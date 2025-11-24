"""
Unit tests for FragmentService

Tests fragment database operations including loading, searching,
and saving assignments.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.append('src')

from services import FragmentService


class TestFragmentService:
    """Test suite for FragmentService"""

    @pytest.fixture
    def temp_database(self):
        """Create a temporary test database"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_fragments.json"

        # Create minimal test database
        test_data = {
            "metadata": {
                "version": "1.0",
                "total_fragments": 3,
                "negative_fragments": 2,
                "positive_fragments": 1,
                "last_modified": "2025-11-23 12:00:00"
            },
            "fragments": [
                {
                    "mass": 25.0078,
                    "assignments": ["C_2H-"],
                    "formulas": ["C2H"],
                    "families": ["Unsaturated_carbon"],
                    "polarity": "negative",
                    "confidence": "High"
                },
                {
                    "mass": 65.0031,
                    "assignments": ["C_4HO-"],
                    "formulas": ["C4HO"],
                    "families": ["Unsaturated_carbon"],
                    "polarity": "negative",
                    "confidence": "High"
                },
                {
                    "mass": 15.0235,
                    "assignments": ["CH_3+", "NH+"],
                    "formulas": ["CH3", "NH"],
                    "families": ["Saturated_carbon", "Unknown"],
                    "polarity": "positive",
                    "confidence": "Medium"
                }
            ]
        }

        with open(db_path, 'w') as f:
            json.dump(test_data, f, indent=2)

        yield db_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_service_initialization(self, temp_database):
        """Test service initialization"""
        service = FragmentService(temp_database)
        assert service.database_path == temp_database
        assert service.fragment_database is None
        assert len(service.fragment_mass_index) == 0

    def test_load_database_success(self, temp_database):
        """Test successful database loading"""
        service = FragmentService(temp_database)
        result = service.load_database()

        assert result is True
        assert service.fragment_database is not None
        assert len(service.fragment_database['fragments']) == 3
        assert len(service.fragment_mass_index) > 0

    def test_load_database_with_indexing(self, temp_database):
        """Test that database loading creates proper mass index"""
        service = FragmentService(temp_database)
        service.load_database()

        # Check index structure
        assert 25 in service.fragment_mass_index  # C2H- at 25.0078
        assert 65 in service.fragment_mass_index  # C4HO- at 65.0031
        assert 15 in service.fragment_mass_index  # CH3+/NH+ at 15.0235

        # Check fragments in buckets
        assert len(service.fragment_mass_index[65]) == 1
        assert service.fragment_mass_index[65][0]['mass'] == 65.0031

    def test_load_database_invalid_path(self):
        """Test loading from non-existent path"""
        service = FragmentService(Path("/nonexistent/path.json"))
        result = service.load_database()

        assert result is False
        assert service.fragment_database is None

    def test_get_database(self, temp_database):
        """Test get_database method with lazy loading"""
        service = FragmentService(temp_database)

        # First call should load database
        db = service.get_database()
        assert db is not None
        assert len(db['fragments']) == 3

    def test_get_fragment_count(self, temp_database):
        """Test fragment count retrieval"""
        service = FragmentService(temp_database)

        # Before loading
        assert service.get_fragment_count() == 0

        # After loading
        service.load_database()
        assert service.get_fragment_count() == 3

    def test_find_candidates_exact_match(self, temp_database):
        """Test finding exact matching candidates"""
        service = FragmentService(temp_database)
        service.load_database()

        # Search for C4HO- at 65.0031
        candidates = service.find_candidates(65.0031, 'negative', ppm_tolerance=50.0)

        assert len(candidates) == 1
        assert candidates[0]['assignments'][0] == "C_4HO-"
        assert abs(candidates[0]['ppm_error']) < 1.0  # Near exact match

    def test_find_candidates_with_tolerance(self, temp_database):
        """Test finding candidates within PPM tolerance"""
        service = FragmentService(temp_database)
        service.load_database()

        # Search near C4HO- with small offset
        candidates = service.find_candidates(65.0050, 'negative', ppm_tolerance=50.0)

        assert len(candidates) == 1
        assert abs(candidates[0]['ppm_error']) < 50.0

    def test_find_candidates_wrong_polarity(self, temp_database):
        """Test that wrong polarity returns no results"""
        service = FragmentService(temp_database)
        service.load_database()

        # Search for negative fragment with positive polarity
        candidates = service.find_candidates(65.0031, 'positive', ppm_tolerance=50.0)

        assert len(candidates) == 0

    def test_find_candidates_outside_tolerance(self, temp_database):
        """Test that fragments outside tolerance are not returned"""
        service = FragmentService(temp_database)
        service.load_database()

        # Search far from any fragment with tight tolerance
        candidates = service.find_candidates(100.0, 'negative', ppm_tolerance=10.0)

        assert len(candidates) == 0

    def test_find_candidates_sorted_by_error(self, temp_database):
        """Test that candidates are sorted by PPM error"""
        service = FragmentService(temp_database)
        service.load_database()

        # If we had multiple candidates, they should be sorted
        candidates = service.find_candidates(65.0031, 'negative', ppm_tolerance=100.0)

        # Check that results are sorted by absolute ppm error
        if len(candidates) > 1:
            for i in range(len(candidates) - 1):
                assert abs(candidates[i]['ppm_error']) <= abs(candidates[i+1]['ppm_error'])

    def test_get_all_fragments_no_filter(self, temp_database):
        """Test retrieving all fragments"""
        service = FragmentService(temp_database)
        service.load_database()

        fragments = service.get_all_fragments()
        assert len(fragments) == 3

    def test_get_all_fragments_with_polarity_filter(self, temp_database):
        """Test retrieving fragments filtered by polarity"""
        service = FragmentService(temp_database)
        service.load_database()

        negative_frags = service.get_all_fragments(polarity='negative')
        positive_frags = service.get_all_fragments(polarity='positive')

        assert len(negative_frags) == 2
        assert len(positive_frags) == 1
        assert all(f['polarity'] == 'negative' for f in negative_frags)
        assert all(f['polarity'] == 'positive' for f in positive_frags)

    def test_get_metadata(self, temp_database):
        """Test retrieving database metadata"""
        service = FragmentService(temp_database)
        service.load_database()

        metadata = service.get_metadata()
        assert metadata is not None
        assert metadata['total_fragments'] == 3
        assert metadata['negative_fragments'] == 2
        assert metadata['positive_fragments'] == 1

    def test_save_manual_assignment_new_fragment(self, temp_database):
        """Test saving a new manual assignment"""
        service = FragmentService(temp_database)
        service.load_database()

        # Create backup directory
        backup_dir = temp_database.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        assignment_data = {
            'assignment': 'C_3H_3-',
            'formula': 'C3H3',
            'calculated_mass': 39.0235,
            'error_ppm': 5.0,
            'chemical_family': 'Unsaturated_carbon',
            'confidence': 'High',
            'notes': 'Test assignment'
        }

        success, message = service.save_manual_assignment(
            39.0235, assignment_data, 'negative'
        )

        assert success is True
        assert 'saved' in message.lower() or 'assignment' in message.lower()

        # Verify fragment was added
        fragments = service.get_all_fragments(polarity='negative')
        new_fragment = [f for f in fragments if f['mass'] == 39.0235]
        assert len(new_fragment) == 1
        assert new_fragment[0]['assignments'][0] == 'C_3H_3-'

    def test_save_manual_assignment_creates_backup(self, temp_database):
        """Test that saving creates a backup file"""
        service = FragmentService(temp_database)
        service.load_database()

        backup_dir = temp_database.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        assignment_data = {
            'assignment': 'Test',
            'formula': 'C1H1',
            'calculated_mass': 13.0078,
            'error_ppm': 1.0,
            'chemical_family': 'Test',
            'confidence': 'Low',
            'notes': 'Test'
        }

        # Count backups before
        backups_before = len(list(backup_dir.glob("*.json")))

        service.save_manual_assignment(13.0078, assignment_data, 'negative')

        # Count backups after
        backups_after = len(list(backup_dir.glob("*.json")))

        assert backups_after == backups_before + 1

    def test_ppm_calculation_accuracy(self, temp_database):
        """Test that PPM error calculation is accurate"""
        service = FragmentService(temp_database)
        service.load_database()

        # Known fragment at 65.0031
        # Test with small offset: 65.0035
        # Expected PPM error: (0.0004 / 65.0031) * 1e6 ≈ 6.15 ppm

        candidates = service.find_candidates(65.0035, 'negative', ppm_tolerance=50.0)

        assert len(candidates) == 1
        expected_ppm = ((65.0031 - 65.0035) / 65.0035) * 1e6
        assert abs(candidates[0]['ppm_error'] - expected_ppm) < 0.1  # Within 0.1 ppm


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
