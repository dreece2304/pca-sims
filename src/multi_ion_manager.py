"""
Multi-Ion Data Manager for ToF-SIMS Analysis

This module manages both positive and negative ion datasets simultaneously,
providing a unified interface for dual-polarity ToF-SIMS analysis.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from simple_tof_sims_pca import SimpleToFSIMSPCA


class MultiIonDataManager:
    """
    Manages both positive and negative ion ToF-SIMS datasets simultaneously

    Features:
    - Automatic detection and loading of companion ion files
    - Unified metadata management across both polarities
    - Individual group analysis capabilities
    - Cross-polarity fragment comparison
    """

    def __init__(self):
        """Initialize the multi-ion data manager"""
        self.negative_analyzer: Optional[SimpleToFSIMSPCA] = None
        self.positive_analyzer: Optional[SimpleToFSIMSPCA] = None
        self.active_polarity: str = "negative"  # Default to negative ion mode
        self.base_filename: Optional[str] = None

        # Track loading status
        self.negative_loaded: bool = False
        self.positive_loaded: bool = False

    def load_data_pair(self, file_path: str) -> Tuple[bool, bool]:
        """
        Load both negative and positive ion data files automatically

        Args:
            file_path: Path to either negative or positive ion data file

        Returns:
            Tuple of (negative_loaded_success, positive_loaded_success)
        """
        file_path = Path(file_path)

        # Detect companion file
        neg_path, pos_path = self._find_companion_files(file_path)

        negative_success = False
        positive_success = False

        # Load negative ion data
        if neg_path and neg_path.exists():
            try:
                print(f"📊 Loading negative ion data: {neg_path}")
                self.negative_analyzer = SimpleToFSIMSPCA(str(neg_path))
                self.negative_analyzer.load_data()
                self.negative_loaded = True
                negative_success = True
                print(f"✅ Negative ion data loaded: {self.negative_analyzer.raw_data.shape}")
            except Exception as e:
                print(f"❌ Failed to load negative ion data: {e}")

        # Load positive ion data
        if pos_path and pos_path.exists():
            try:
                print(f"📊 Loading positive ion data: {pos_path}")
                self.positive_analyzer = SimpleToFSIMSPCA(str(pos_path))
                self.positive_analyzer.load_data()
                self.positive_loaded = True
                positive_success = True
                print(f"✅ Positive ion data loaded: {self.positive_analyzer.raw_data.shape}")
            except Exception as e:
                print(f"❌ Failed to load positive ion data: {e}")

        # Set base filename for metadata coordination
        if negative_success or positive_success:
            self.base_filename = self._extract_base_filename(file_path)

        return negative_success, positive_success

    def _find_companion_files(self, file_path: Path) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Find both negative and positive ion files based on input file

        Args:
            file_path: Path to either ion file

        Returns:
            Tuple of (negative_path, positive_path)
        """
        parent_dir = file_path.parent

        # Common naming patterns
        neg_patterns = ["NegAllCompoundSearch.txt", "NegIonTIC.txt", "*Neg*.txt"]
        pos_patterns = ["PosAllCompoundSearch.txt", "PosIonTIC.txt", "*Pos*.txt"]

        neg_path = None
        pos_path = None

        # If input file is negative, find positive companion
        if any(pattern.replace("*", "").replace(".txt", "").lower() in file_path.name.lower()
               for pattern in ["neg", "negative"]):
            neg_path = file_path
            # Look for positive companion
            for pattern in pos_patterns:
                if "*" in pattern:
                    # Use glob for wildcard patterns
                    matches = list(parent_dir.glob(pattern))
                    if matches:
                        pos_path = matches[0]
                        break
                else:
                    potential_pos = parent_dir / pattern
                    if potential_pos.exists():
                        pos_path = potential_pos
                        break

        # If input file is positive, find negative companion
        elif any(pattern.replace("*", "").replace(".txt", "").lower() in file_path.name.lower()
                 for pattern in ["pos", "positive"]):
            pos_path = file_path
            # Look for negative companion
            for pattern in neg_patterns:
                if "*" in pattern:
                    matches = list(parent_dir.glob(pattern))
                    if matches:
                        neg_path = matches[0]
                        break
                else:
                    potential_neg = parent_dir / pattern
                    if potential_neg.exists():
                        neg_path = potential_neg
                        break

        # If neither pattern matches, try to detect by location
        else:
            # Check if we're in a NegativeIon or PositiveIon directory
            if "negative" in str(parent_dir).lower():
                neg_path = file_path
                # Look for positive in sibling directory
                pos_dir = parent_dir.parent / "PositiveIon"
                if pos_dir.exists():
                    for pattern in pos_patterns:
                        potential_pos = pos_dir / pattern
                        if potential_pos.exists():
                            pos_path = potential_pos
                            break
            elif "positive" in str(parent_dir).lower():
                pos_path = file_path
                # Look for negative in sibling directory
                neg_dir = parent_dir.parent / "NegativeIon"
                if neg_dir.exists():
                    for pattern in neg_patterns:
                        potential_neg = neg_dir / pattern
                        if potential_neg.exists():
                            neg_path = potential_neg
                            break

        return neg_path, pos_path

    def _extract_base_filename(self, file_path: Path) -> str:
        """Extract base filename without polarity indicators"""
        name = file_path.stem
        # Remove common polarity indicators
        for indicator in ["Neg", "Pos", "Negative", "Positive", "negative", "positive"]:
            name = name.replace(indicator, "")
        # Clean up any remaining artifacts
        name = name.replace("AllCompoundSearch", "CompoundSearch")
        return name.strip("_")

    def get_active_analyzer(self) -> Optional[SimpleToFSIMSPCA]:
        """Get the currently active analyzer based on polarity setting"""
        if self.active_polarity == "negative":
            return self.negative_analyzer
        else:
            return self.positive_analyzer

    def set_active_polarity(self, polarity: str) -> bool:
        """
        Set the active polarity mode

        Args:
            polarity: "negative" or "positive"

        Returns:
            True if successfully set, False if data not available
        """
        if polarity == "negative" and self.negative_loaded:
            self.active_polarity = "negative"
            return True
        elif polarity == "positive" and self.positive_loaded:
            self.active_polarity = "positive"
            return True
        else:
            return False

    def get_available_polarities(self) -> List[str]:
        """Get list of available polarities based on loaded data"""
        available = []
        if self.negative_loaded:
            available.append("negative")
        if self.positive_loaded:
            available.append("positive")
        return available

    def get_sample_groups(self) -> List[str]:
        """
        Get available sample groups from the active analyzer

        Returns:
            List of group names (e.g., ["As-Deposited", "2000 μC/cm²", ...])
        """
        analyzer = self.get_active_analyzer()
        if not analyzer or not hasattr(analyzer, 'sample_metadata'):
            return []

        groups = []

        # Check if we have sample_type metadata
        if 'sample_type' in analyzer.sample_metadata.columns:
            # Group by sample type and actual dose
            for _, row in analyzer.sample_metadata.iterrows():
                sample_type = row.get('sample_type', 'Unknown')
                if sample_type == 'As-Deposited':
                    if 'As-Deposited' not in groups:
                        groups.append('As-Deposited')
                elif sample_type == 'E-Beam Exposed':
                    dose = row.get('actual_dose', row.get('dose', 'Unknown'))
                    dose_label = f"{dose} μC/cm²"
                    if dose_label not in groups:
                        groups.append(dose_label)
                elif sample_type != 'Excluded':
                    if sample_type not in groups:
                        groups.append(sample_type)
        else:
            # Fallback to dose_id grouping
            dose_ids = sorted(analyzer.sample_metadata['dose_id'].unique())
            for dose_id in dose_ids:
                if dose_id == 0:
                    groups.append('As-Deposited (SQ0)')
                else:
                    groups.append(f'Dose Level {dose_id}')

        return groups

    def get_group_intensity_data(self, group_name: str, polarity: str = None) -> Optional[pd.DataFrame]:
        """
        Get intensity data for a specific sample group

        Args:
            group_name: Name of the sample group
            polarity: "negative", "positive", or None for active polarity

        Returns:
            DataFrame with columns: mass, mean_intensity, std_intensity, assignment
        """
        if polarity is None:
            polarity = self.active_polarity

        analyzer = self.negative_analyzer if polarity == "negative" else self.positive_analyzer
        if not analyzer:
            return None

        # Get samples belonging to this group
        group_samples = self._get_group_samples(group_name, analyzer)
        if not group_samples:
            return None

        # Extract intensity data for these samples
        data = analyzer.raw_data[group_samples]

        # Calculate statistics
        intensity_stats = pd.DataFrame({
            'mass': data.index,
            'mean_intensity': data.mean(axis=1),
            'std_intensity': data.std(axis=1),
            'max_intensity': data.max(axis=1),
            'min_intensity': data.min(axis=1),
            'n_samples': len(group_samples)
        })

        # Add assignment information from fragment database
        intensity_stats['assignment'] = intensity_stats['mass'].apply(
            lambda m: self._get_fragment_assignment(m, polarity)
        )

        # Sort by mean intensity (descending)
        intensity_stats = intensity_stats.sort_values('mean_intensity', ascending=False)

        return intensity_stats

    def _get_group_samples(self, group_name: str, analyzer: SimpleToFSIMSPCA) -> List[str]:
        """Get list of sample names belonging to a specific group"""
        if not hasattr(analyzer, 'sample_metadata'):
            return []

        samples = []

        if group_name == 'As-Deposited':
            # Find As-Deposited samples
            if 'sample_type' in analyzer.sample_metadata.columns:
                mask = analyzer.sample_metadata['sample_type'] == 'As-Deposited'
            else:
                # Fallback to dose_id = 0
                mask = analyzer.sample_metadata['dose_id'] == 0
            samples = analyzer.sample_metadata.loc[mask, 'sample_name'].tolist()

        elif 'μC/cm²' in group_name:
            # Extract dose value from group name
            try:
                dose_val = float(group_name.split()[0])
                if 'actual_dose' in analyzer.sample_metadata.columns:
                    mask = analyzer.sample_metadata['actual_dose'] == dose_val
                else:
                    # Try to match by dose_id
                    dose_mapping = {0: 0, 1: 1000, 2: 2000, 3: 5000, 4: 10000, 5: 15000}
                    dose_id = None
                    for did, dval in dose_mapping.items():
                        if dval == dose_val:
                            dose_id = did
                            break
                    if dose_id is not None:
                        mask = analyzer.sample_metadata['dose_id'] == dose_id
                    else:
                        mask = pd.Series([False] * len(analyzer.sample_metadata))
                samples = analyzer.sample_metadata.loc[mask, 'sample_name'].tolist()
            except (ValueError, IndexError):
                pass

        # Filter out excluded samples
        if 'include' in analyzer.sample_metadata.columns:
            included_samples = analyzer.sample_metadata.loc[
                analyzer.sample_metadata['include'] == True, 'sample_name'
            ].tolist()
            samples = [s for s in samples if s in included_samples]

        return samples

    def _get_fragment_assignment(self, mass: float, polarity: str) -> str:
        """Get fragment assignment from database for a given mass"""
        # This would integrate with the existing fragment database
        # For now, return placeholder
        return "Unknown"

    def apply_metadata_to_both(self, metadata_dict: dict):
        """Apply metadata to both analyzers"""
        if self.negative_analyzer:
            metadata = {'metadata': metadata_dict}
            self.negative_analyzer.apply_metadata(metadata)

        if self.positive_analyzer:
            metadata = {'metadata': metadata_dict}
            self.positive_analyzer.apply_metadata(metadata)

    def get_comparison_summary(self, group_name: str) -> Dict:
        """
        Get comparison summary between negative and positive ions for a group

        Returns:
            Dictionary with comparative statistics
        """
        summary = {
            'group_name': group_name,
            'negative_peaks': 0,
            'positive_peaks': 0,
            'total_negative_intensity': 0.0,
            'total_positive_intensity': 0.0,
            'top_negative_peaks': [],
            'top_positive_peaks': []
        }

        # Get data for both polarities
        neg_data = self.get_group_intensity_data(group_name, "negative")
        pos_data = self.get_group_intensity_data(group_name, "positive")

        if neg_data is not None:
            summary['negative_peaks'] = len(neg_data)
            summary['total_negative_intensity'] = neg_data['mean_intensity'].sum()
            summary['top_negative_peaks'] = neg_data.head(10)[['mass', 'mean_intensity', 'assignment']].to_dict('records')

        if pos_data is not None:
            summary['positive_peaks'] = len(pos_data)
            summary['total_positive_intensity'] = pos_data['mean_intensity'].sum()
            summary['top_positive_peaks'] = pos_data.head(10)[['mass', 'mean_intensity', 'assignment']].to_dict('records')

        return summary