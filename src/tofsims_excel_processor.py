"""
ToF-SIMS Excel Data Processor
Processes Excel files with fragment assignments and intensity data
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ToFSIMSExcelProcessor:
    """
    Process ToF-SIMS Excel files containing fragment assignments and intensities

    Excel Format Expected:
    - Column 0: Fragment assignments (e.g., "H+", "CH_3+", etc.)
    - Column 1: Mass (u) - m/z values
    - Columns 2+: Sample intensities (already TIC-normalized)
    """

    def __init__(self, fragment_database_path: str = "data/FragmentDatabase/alucone_fragments_complete.json"):
        """
        Initialize processor

        Args:
            fragment_database_path: Path to fragment database JSON file
        """
        self.fragment_database_path = fragment_database_path
        self.fragment_database = None
        self.load_fragment_database()

    def load_fragment_database(self) -> None:
        """Load existing fragment database"""
        try:
            with open(self.fragment_database_path, 'r') as f:
                self.fragment_database = json.load(f)
            print(f"✅ Loaded fragment database: {len(self.fragment_database.get('fragments', []))} fragments")
        except FileNotFoundError:
            print(f"⚠️ Fragment database not found at {self.fragment_database_path}")
            print("   Creating new database structure...")
            self.fragment_database = {
                "metadata": {
                    "name": "ToF-SIMS Fragment Database",
                    "version": "1.0",
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "total_fragments": 0
                },
                "fragments": []
            }

    def process_excel_file(self, excel_path: str, polarity: str = "positive") -> Tuple[pd.DataFrame, Dict]:
        """
        Process ToF-SIMS Excel file with fragment assignments

        Args:
            excel_path: Path to Excel file
            polarity: Ion polarity ("positive" or "negative")

        Returns:
            Tuple of (intensity_dataframe, processing_stats)
            - intensity_dataframe: DataFrame with m/z as index, samples as columns
            - processing_stats: Dict with processing statistics
        """
        print(f"\n📊 Processing ToF-SIMS Excel file: {excel_path}")
        print(f"   Polarity: {polarity}")

        # Read Excel file
        df = pd.read_excel(excel_path)
        print(f"   Raw data shape: {df.shape}")
        print(f"   Columns: {list(df.columns)[:5]}...")  # Show first 5 columns

        # Extract fragment column (first column)
        fragment_col = df.columns[0]
        fragments = df[fragment_col].values

        # Extract m/z column (second column, should be "Mass (u)")
        mz_col = df.columns[1]
        mz_values = df[mz_col].values

        # Extract intensity columns (all remaining columns)
        intensity_cols = df.columns[2:]
        intensities = df[intensity_cols]

        print(f"   Found {len(fragments)} fragment assignments")
        print(f"   m/z range: {mz_values.min():.4f} - {mz_values.max():.4f}")
        print(f"   Sample columns: {len(intensity_cols)}")

        # Update fragment database with new fragments
        new_fragments_added = self._update_fragment_database(fragments, mz_values, polarity)

        # Create cleaned intensity DataFrame with duplicate handling
        intensity_df, duplicate_stats = self._create_intensity_dataframe(
            mz_values, intensities, intensity_cols
        )

        # Processing statistics
        stats = {
            "total_rows": len(df),
            "unique_mz_values": len(intensity_df),
            "duplicates_removed": duplicate_stats["duplicates_removed"],
            "duplicate_details": duplicate_stats["duplicate_details"],
            "new_fragments_added": new_fragments_added,
            "sample_columns": len(intensity_cols),
            "mz_range": (float(mz_values.min()), float(mz_values.max()))
        }

        print(f"\n✅ Processing complete:")
        print(f"   Unique m/z values: {stats['unique_mz_values']}")
        print(f"   Duplicates merged: {stats['duplicates_removed']}")
        print(f"   New fragments added to database: {stats['new_fragments_added']}")

        return intensity_df, stats

    def _update_fragment_database(self, fragments: np.ndarray, mz_values: np.ndarray,
                                  polarity: str) -> int:
        """
        Update fragment database with new assignments from Excel

        IMPORTANT: Only adds fragments if the formula doesn't exist in database.
        Uses CALCULATED exact masses from formulas, NOT measured m/z values from Excel.

        Args:
            fragments: Array of fragment strings (e.g., "C_6H_5+", "CH_3+")
            mz_values: Array of measured m/z values (NOT used for database, only for PCA data)
            polarity: Ion polarity

        Returns:
            Number of new fragments added
        """
        from core.fragment_mass_calculator import calculate_mass_from_assignment, extract_formula_from_assignment

        print(f"\n🔍 Checking fragment database for new fragment formulas...")

        # Get existing fragment formulas (not masses!)
        existing_formulas = set()
        for frag in self.fragment_database.get("fragments", []):
            if frag.get("polarity") == polarity:
                # Handle both plural 'formulas' and singular 'formula'
                formulas = frag.get('formulas', [frag.get('formula')]) if frag.get('formula') else frag.get('formulas', [])
                for formula in formulas:
                    if formula:
                        existing_formulas.add(formula.replace("_", ""))  # Normalize

        print(f"   Existing {polarity} fragment formulas in database: {len(existing_formulas)}")

        new_fragments_added = 0

        # Check each fragment assignment
        for fragment in fragments:
            # Skip if fragment is NaN or empty
            if pd.isna(fragment) or fragment == "":
                continue

            try:
                # Extract formula from assignment (e.g., "C_6H_5+" → "C6H5")
                formula, charge = extract_formula_from_assignment(str(fragment))

                # Check if this formula already exists in database
                if formula not in existing_formulas:
                    # Calculate EXACT mass from formula
                    exact_mass = calculate_mass_from_assignment(str(fragment))

                    # Add new fragment with exact calculated mass
                    new_fragment = {
                        "mass": exact_mass,  # CALCULATED, not measured!
                        "assignments": [str(fragment)],
                        "formulas": [formula],
                        "families": ["Unknown"],  # Will be categorized later if needed
                        "polarity": polarity,
                        "confidence": "High",
                        "notes": f"Auto-added from Excel file on {datetime.now().strftime('%Y-%m-%d')} (exact calculated mass)"
                    }

                    self.fragment_database["fragments"].append(new_fragment)
                    existing_formulas.add(formula)
                    new_fragments_added += 1

                    print(f"   ➕ Added {fragment}: exact mass = {exact_mass:.6f}")
                else:
                    # Fragment formula already exists - skip
                    pass

            except Exception as e:
                print(f"   ⚠️ Could not process fragment {fragment}: {e}")
                continue

        if new_fragments_added > 0:
            print(f"   ✅ Added {new_fragments_added} new fragments to database")
            # Update metadata
            self.fragment_database["metadata"]["total_fragments"] = len(self.fragment_database["fragments"])
            self.fragment_database["metadata"]["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save updated database
            self._save_fragment_database()
        else:
            print(f"   ℹ️ No new fragments to add (all already in database)")

        return new_fragments_added

    def _extract_formula(self, fragment: str) -> str:
        """
        Extract chemical formula from fragment string

        Args:
            fragment: Fragment string (e.g., "CH_3+", "H-")

        Returns:
            Chemical formula (e.g., "CH3", "H")
        """
        # Remove charge symbols (+, -)
        formula = fragment.replace("+", "").replace("-", "")
        # Remove underscores (subscript notation)
        formula = formula.replace("_", "")
        return formula

    def _create_intensity_dataframe(self, mz_values: np.ndarray,
                                   intensities: pd.DataFrame,
                                   intensity_cols: pd.Index) -> Tuple[pd.DataFrame, Dict]:
        """
        Create cleaned intensity DataFrame with duplicate m/z handling

        IMPORTANT: Duplicate m/z values have IDENTICAL intensities (multiple fragment
        candidates for same measured peak). We simply remove duplicate rows, keeping
        the first occurrence. DO NOT average - intensities are already identical.

        Args:
            mz_values: Array of measured m/z values
            intensities: DataFrame of intensity values
            intensity_cols: Column names for intensities

        Returns:
            Tuple of (cleaned_dataframe, duplicate_stats)
        """
        print(f"\n🧹 Creating intensity DataFrame with duplicate handling...")

        # Create DataFrame with m/z as index
        df = pd.DataFrame(intensities.values, index=mz_values, columns=intensity_cols)

        # Find duplicates before removing them
        duplicate_mask = df.index.duplicated(keep=False)
        duplicate_mz = df.index[duplicate_mask]
        unique_duplicates = duplicate_mz.unique()

        duplicate_details = []

        if len(unique_duplicates) > 0:
            print(f"   Found {len(unique_duplicates)} m/z values with duplicates")

            # Collect duplicate info for stats
            for mz in unique_duplicates:
                count = (df.index == mz).sum()
                duplicate_details.append({
                    "mz": float(mz),
                    "count": count,
                    "merged_method": "keep_first"
                })

            # Remove duplicate rows (keep first occurrence only)
            # Intensities are identical for true duplicates, so just drop extras
            df = df[~df.index.duplicated(keep='first')]

            print(f"   ✅ Removed {len(duplicate_mask[duplicate_mask]) - len(unique_duplicates)} duplicate rows (kept first occurrence)")
        else:
            print(f"   ℹ️ No duplicate m/z values found")

        # Sort by m/z
        df = df.sort_index()

        duplicate_stats = {
            "duplicates_removed": len(unique_duplicates),
            "duplicate_details": duplicate_details
        }

        return df, duplicate_stats

    def _save_fragment_database(self) -> None:
        """Save updated fragment database to JSON file"""
        try:
            # Create backup of existing database
            if Path(self.fragment_database_path).exists():
                backup_dir = Path(self.fragment_database_path).parent / "backups"
                backup_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"backup_{timestamp}.json"

                import shutil
                shutil.copy2(self.fragment_database_path, backup_path)
                print(f"   📦 Created backup: {backup_path}")

            # Save updated database
            with open(self.fragment_database_path, 'w') as f:
                json.dump(self.fragment_database, f, indent=2)

            print(f"   💾 Saved updated fragment database")

        except Exception as e:
            print(f"   ⚠️ Error saving fragment database: {e}")

    def export_to_tab_delimited(self, intensity_df: pd.DataFrame,
                               output_path: str) -> None:
        """
        Export cleaned intensity data to tab-delimited format (PCA-ready)

        Args:
            intensity_df: DataFrame with m/z as index, samples as columns
            output_path: Path for output file
        """
        print(f"\n💾 Exporting to tab-delimited format: {output_path}")

        # Reset index to make m/z a column
        export_df = intensity_df.reset_index()
        export_df.rename(columns={"index": "Mass"}, inplace=True)

        # Save as tab-delimited
        export_df.to_csv(output_path, sep='\t', index=False)

        print(f"   ✅ Exported {len(intensity_df)} m/z values × {len(intensity_df.columns)} samples")


def process_tofsims_excel(excel_path: str, polarity: str = "positive",
                          output_path: Optional[str] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Convenience function to process ToF-SIMS Excel file

    Args:
        excel_path: Path to Excel file with fragments and intensities
        polarity: Ion polarity ("positive" or "negative")
        output_path: Optional path for tab-delimited output (for PCA)

    Returns:
        Tuple of (intensity_dataframe, processing_stats)
    """
    processor = ToFSIMSExcelProcessor()
    intensity_df, stats = processor.process_excel_file(excel_path, polarity)

    if output_path:
        processor.export_to_tab_delimited(intensity_df, output_path)

    return intensity_df, stats


if __name__ == "__main__":
    # Example usage
    excel_file = "data/PositiveIon/AllPosNewwithFragment.xlsx"
    output_file = "data/PositiveIon/AllPosNew_processed.txt"

    df, stats = process_tofsims_excel(
        excel_file,
        polarity="positive",
        output_path=output_file
    )

    print(f"\n📊 Final DataFrame shape: {df.shape}")
    print(f"   Stats: {stats}")
