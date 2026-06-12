"""
Fragment Database Service

Service for managing fragment assignment database operations including:
- Loading and caching fragment database
- Saving manual assignments
- Finding fragment candidates for observed m/z values
- Database backup management
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from paths import FRAGMENT_DATABASE_PATH


class FragmentService:
    """Service for fragment database operations"""

    DEFAULT_DATABASE_PATH = FRAGMENT_DATABASE_PATH
    DEFAULT_PPM_TOLERANCE = 50.0
    MANUAL_ASSIGNMENT_TOLERANCE = 10.0

    def __init__(self, database_path: Optional[Path] = None):
        """Initialize fragment service

        Args:
            database_path: Path to fragment database JSON file (default: standard location)
        """
        self.database_path = database_path or self.DEFAULT_DATABASE_PATH
        self.fragment_database: Optional[Dict] = None
        self.fragment_mass_index: Dict[int, List[Dict]] = {}

    def load_database(self) -> bool:
        """Load fragment assignment database from JSON file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.database_path, 'r') as f:
                self.fragment_database = json.load(f)

            print(f"✅ Loaded fragment database with {len(self.fragment_database['fragments'])} fragments")

            # Build mass index for fast lookups (group by integer mass)
            self.fragment_mass_index = {}
            for fragment in self.fragment_database['fragments']:
                mass_key = int(fragment['mass'])  # Index by integer part
                if mass_key not in self.fragment_mass_index:
                    self.fragment_mass_index[mass_key] = []
                self.fragment_mass_index[mass_key].append(fragment)

            print(f"📇 Indexed {len(self.fragment_database['fragments'])} fragments into {len(self.fragment_mass_index)} mass buckets")

            return True

        except Exception as e:
            print(f"Warning: Could not load fragment database: {e}")
            self.fragment_database = None
            self.fragment_mass_index = {}
            return False

    def get_database(self) -> Optional[Dict]:
        """Get the loaded database, loading if necessary

        Returns:
            Optional[Dict]: The fragment database or None if not loaded
        """
        if self.fragment_database is None:
            self.load_database()
        return self.fragment_database

    def get_fragment_count(self) -> int:
        """Get total number of fragments in database

        Returns:
            int: Number of fragments, or 0 if database not loaded
        """
        if self.fragment_database is None:
            return 0
        return len(self.fragment_database.get('fragments', []))

    def find_candidates(self, mz_value: float, polarity: str,
                       ppm_tolerance: Optional[float] = None) -> List[Dict]:
        """Find fragment candidates for an observed m/z value

        Args:
            mz_value: Observed m/z value
            polarity: 'positive' or 'negative'
            ppm_tolerance: PPM tolerance for matching (default: 50 ppm)

        Returns:
            List[Dict]: List of matching fragment candidates
        """
        if self.fragment_database is None:
            self.load_database()

        if self.fragment_database is None:
            return []

        tolerance = ppm_tolerance or self.DEFAULT_PPM_TOLERANCE
        candidates = []

        # Check integer mass buckets around the target
        mass_key = int(mz_value)
        for key in [mass_key - 1, mass_key, mass_key + 1]:
            if key in self.fragment_mass_index:
                for fragment in self.fragment_mass_index[key]:
                    if fragment['polarity'] != polarity:
                        continue

                    # Calculate ppm error
                    ppm_error = ((fragment['mass'] - mz_value) / mz_value) * 1e6

                    if abs(ppm_error) <= tolerance:
                        candidate = fragment.copy()
                        candidate['ppm_error'] = ppm_error
                        candidates.append(candidate)

        # Sort by absolute ppm error (best matches first)
        candidates.sort(key=lambda x: abs(x['ppm_error']))

        return candidates

    def save_manual_assignment(self, mz_value: float, assignment_data: Dict[str, Any],
                              polarity: str) -> Tuple[bool, str]:
        """Save a manual fragment assignment to the database

        Args:
            mz_value: Observed m/z value
            assignment_data: Dict with assignment, formula, confidence, calculated_mass, error_ppm, notes
            polarity: 'positive' or 'negative'

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Step 1: Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.database_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_path = backup_dir / f"before_manual_assignment_{timestamp}.json"
            shutil.copy2(self.database_path, backup_path)
            print(f"📦 Created backup: {backup_path.name}")

            # Step 2: Load current database
            with open(self.database_path, 'r') as f:
                database = json.load(f)

            # Step 3: Check if fragment exists at this mass (within 10 ppm tolerance)
            existing_fragment = None
            existing_index = None

            for i, fragment in enumerate(database['fragments']):
                if fragment['polarity'] != polarity:
                    continue

                # Calculate mass error in ppm
                mass_error_ppm = abs((fragment['mass'] - mz_value) / mz_value * 1e6)

                if mass_error_ppm <= self.MANUAL_ASSIGNMENT_TOLERANCE:
                    existing_fragment = fragment
                    existing_index = i
                    break

            # Step 4: Create fragment entry
            fragment_entry = {
                "mass": assignment_data['calculated_mass'],
                "assignments": [assignment_data['assignment']],
                "formulas": [assignment_data['formula']],
                "families": [assignment_data['chemical_family']],
                "polarity": polarity,
                "confidence": assignment_data['confidence'],
                "notes": f"Manual assignment - {assignment_data.get('notes', 'User-assigned')}"
            }

            if existing_fragment:
                # Update existing fragment
                print(f"📝 Updating existing fragment at m/z {existing_fragment['mass']:.4f}")

                # Preserve existing assignments if they're different
                if assignment_data['assignment'] not in existing_fragment['assignments']:
                    existing_fragment['assignments'].insert(0, assignment_data['assignment'])
                    existing_fragment['formulas'].insert(0, assignment_data['formula'])
                    existing_fragment['families'].insert(0, assignment_data['chemical_family'])
                else:
                    # Replace if it already exists
                    idx = existing_fragment['assignments'].index(assignment_data['assignment'])
                    existing_fragment['assignments'][idx] = assignment_data['assignment']
                    existing_fragment['formulas'][idx] = assignment_data['formula']
                    existing_fragment['families'][idx] = assignment_data['chemical_family']

                # Update confidence and notes
                existing_fragment['confidence'] = assignment_data['confidence']
                existing_fragment['notes'] = fragment_entry['notes']

                # Update mass to calculated value
                existing_fragment['mass'] = assignment_data['calculated_mass']

            else:
                # Add new fragment
                print(f"➕ Adding new fragment at m/z {mz_value:.4f}")
                database['fragments'].append(fragment_entry)

                # Keep fragments sorted by mass
                database['fragments'].sort(key=lambda x: x['mass'])

            # Step 5: Update metadata
            total_fragments = len(database['fragments'])
            negative_count = sum(1 for f in database['fragments'] if f['polarity'] == 'negative')
            positive_count = sum(1 for f in database['fragments'] if f['polarity'] == 'positive')

            database['metadata']['total_fragments'] = total_fragments
            database['metadata']['negative_fragments'] = negative_count
            database['metadata']['positive_fragments'] = positive_count
            database['metadata']['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Step 6: Write updated database
            with open(self.database_path, 'w') as f:
                json.dump(database, f, indent=2)

            print(f"✅ Database updated successfully")
            print(f"   Total fragments: {total_fragments} ({negative_count} negative, {positive_count} positive)")

            # Step 7: Reload database and rebuild index
            self.load_database()

            success_msg = (
                f"Assignment saved to database:\n\n"
                f"m/z {mz_value:.4f} → {assignment_data['assignment']}\n"
                f"Formula: {assignment_data['formula']}\n"
                f"Error: {assignment_data['error_ppm']:.1f} ppm\n\n"
                f"Backup created: {backup_path.name}"
            )

            return True, success_msg

        except Exception as e:
            error_msg = f"Error saving assignment: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def get_all_fragments(self, polarity: Optional[str] = None) -> List[Dict]:
        """Get all fragments, optionally filtered by polarity

        Args:
            polarity: Optional polarity filter ('positive' or 'negative')

        Returns:
            List[Dict]: List of fragment entries
        """
        if self.fragment_database is None:
            self.load_database()

        if self.fragment_database is None:
            return []

        fragments = self.fragment_database.get('fragments', [])

        if polarity:
            fragments = [f for f in fragments if f.get('polarity') == polarity]

        return fragments

    def get_metadata(self) -> Optional[Dict]:
        """Get database metadata

        Returns:
            Optional[Dict]: Metadata dictionary or None if not loaded
        """
        if self.fragment_database is None:
            self.load_database()

        if self.fragment_database is None:
            return None

        return self.fragment_database.get('metadata', {})
