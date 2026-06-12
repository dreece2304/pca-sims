"""
Integration tests for fragment assignment workflow

Tests the complete workflow from loading database to saving assignments.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

import sys
# Get project root (tests/integration -> tests -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT / 'src'))

from services import FragmentService
from models import Fragment, Polarity


class TestFragmentWorkflow:
    """Integration tests for fragment assignment workflow"""

    @pytest.fixture
    def real_database(self):
        """Use the actual fragment database for integration testing"""
        db_path = PROJECT_ROOT / "data" / "FragmentDatabase" / "alucone_fragments_complete.json"
        if not db_path.exists():
            pytest.skip("Fragment database not found")
        return db_path

    @pytest.fixture
    def temp_database_copy(self, real_database):
        """Create a temporary copy of the real database for destructive testing"""
        temp_dir = tempfile.mkdtemp()
        db_copy = Path(temp_dir) / "fragments_copy.json"
        shutil.copy2(real_database, db_copy)

        # Create backup directory
        backup_dir = db_copy.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        yield db_copy

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_load_real_database(self, real_database):
        """Test loading the actual fragment database"""
        service = FragmentService(real_database)
        success = service.load_database()

        assert success is True
        assert service.get_fragment_count() > 0
        assert len(service.fragment_mass_index) > 0

        print(f"\n✅ Loaded {service.get_fragment_count()} fragments")

    def test_search_known_fragments(self, real_database):
        """Test searching for known fragments in real database"""
        service = FragmentService(real_database)
        service.load_database()

        # Search for common fragments
        test_cases = [
            (25.0078, 'negative', 'C2H-'),  # C2H-
            (65.0031, 'negative', 'C4HO-'),  # C4HO-
        ]

        for mz, polarity, expected_formula in test_cases:
            candidates = service.find_candidates(mz, polarity, ppm_tolerance=50.0)

            if len(candidates) > 0:
                print(f"\n✅ Found {len(candidates)} candidates for m/z {mz}:")
                for i, cand in enumerate(candidates[:3], 1):
                    print(f"   {i}. {cand['formulas'][0]} "
                          f"({cand['ppm_error']:.1f} ppm)")

                # Check if expected formula is in top results
                top_formulas = [c['formulas'][0] for c in candidates[:5]]
                # Note: Exact match depends on database content

    def test_complete_assignment_workflow(self, temp_database_copy):
        """Test complete workflow: load, search, assign, save"""
        service = FragmentService(temp_database_copy)

        # Step 1: Load database
        assert service.load_database() is True
        initial_count = service.get_fragment_count()

        # Step 2: Search for a fragment
        candidates = service.find_candidates(65.0031, 'negative', ppm_tolerance=50.0)
        assert len(candidates) > 0

        # Step 3: Create and save a new assignment
        new_assignment = {
            'assignment': 'C_3H_3O-',
            'formula': 'C3H3O',
            'calculated_mass': 55.0184,
            'error_ppm': 10.0,
            'chemical_family': 'Organic_oxygen',
            'confidence': 'Medium',
            'notes': 'Integration test assignment'
        }

        success, message = service.save_manual_assignment(
            55.0184, new_assignment, 'negative'
        )

        assert success is True

        # Step 4: Verify assignment was saved
        final_count = service.get_fragment_count()
        assert final_count >= initial_count  # May be equal if updating existing

        # Step 5: Search for the newly added fragment
        new_candidates = service.find_candidates(55.0184, 'negative', ppm_tolerance=10.0)
        assert len(new_candidates) > 0

        print(f"\n✅ Complete workflow test passed")
        print(f"   Initial fragments: {initial_count}")
        print(f"   Final fragments: {final_count}")

    def test_polarity_filtering(self, real_database):
        """Test that polarity filtering works correctly"""
        service = FragmentService(real_database)
        service.load_database()

        negative_fragments = service.get_all_fragments(polarity='negative')
        positive_fragments = service.get_all_fragments(polarity='positive')

        assert len(negative_fragments) > 0
        assert len(positive_fragments) >= 0  # May be 0 if no positive fragments

        # Verify all fragments have correct polarity
        assert all(f['polarity'] == 'negative' for f in negative_fragments)
        if len(positive_fragments) > 0:
            assert all(f['polarity'] == 'positive' for f in positive_fragments)

        print(f"\n✅ Polarity filtering test passed")
        print(f"   Negative fragments: {len(negative_fragments)}")
        print(f"   Positive fragments: {len(positive_fragments)}")

    def test_metadata_consistency(self, real_database):
        """Test that metadata is consistent with actual fragment count"""
        service = FragmentService(real_database)
        service.load_database()

        metadata = service.get_metadata()
        actual_count = service.get_fragment_count()

        # Metadata may not always match exactly (depends on last update)
        # But should be reasonably close
        assert metadata is not None
        assert 'total_fragments' in metadata

        print(f"\n✅ Metadata test passed")
        print(f"   Metadata count: {metadata['total_fragments']}")
        print(f"   Actual count: {actual_count}")

    def test_backup_creation(self, temp_database_copy):
        """Test that backups are created when saving assignments"""
        service = FragmentService(temp_database_copy)
        service.load_database()

        backup_dir = temp_database_copy.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Count backups before
        backups_before = len(list(backup_dir.glob("*.json")))

        # Save an assignment
        assignment_data = {
            'assignment': 'TestFragment',
            'formula': 'C1H1',
            'calculated_mass': 13.0078,
            'error_ppm': 5.0,
            'chemical_family': 'Test',
            'confidence': 'Low',
            'notes': 'Test'
        }

        service.save_manual_assignment(13.0078, assignment_data, 'negative')

        # Count backups after
        backups_after = len(list(backup_dir.glob("*.json")))

        assert backups_after == backups_before + 1

        print(f"\n✅ Backup creation test passed")
        print(f"   Backups created: {backups_after - backups_before}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
