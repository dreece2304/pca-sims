"""
Multi-Ion Data Manager - Minimal Version
Simplified polarity tracking without dual-loading complexity
"""

from typing import Optional, List
from simple_tof_sims_pca import SimpleToFSIMSPCA


class MultiIonDataManager:
    """
    Minimal polarity manager - tracks current ion mode

    Note: Dual-polarity loading removed - complexity not needed.
    Just tracks which polarity is active for fragment assignment.
    """

    def __init__(self):
        """Initialize with single polarity tracking"""
        self.negative_analyzer: Optional[SimpleToFSIMSPCA] = None
        self.positive_analyzer: Optional[SimpleToFSIMSPCA] = None
        self.active_polarity: str = "negative"
        self.negative_loaded: bool = False
        self.positive_loaded: bool = False

    def load_data_pair(self, file_path: str):
        """
        Minimal stub - just returns False, False
        Actual loading happens in main GUI
        """
        return False, False

    def get_active_analyzer(self) -> Optional[SimpleToFSIMSPCA]:
        """Get the currently active analyzer"""
        if self.active_polarity == "negative":
            return self.negative_analyzer
        else:
            return self.positive_analyzer

    def set_active_polarity(self, polarity: str) -> bool:
        """Set active polarity"""
        if polarity in ["negative", "positive"]:
            self.active_polarity = polarity
            return True
        return False

    def get_available_polarities(self) -> List[str]:
        """Get list of loaded polarities"""
        polarities = []
        if self.negative_loaded:
            polarities.append("negative")
        if self.positive_loaded:
            polarities.append("positive")
        return polarities

    def get_sample_groups(self) -> List[str]:
        """Stub - returns empty list"""
        return []

    def get_group_intensity_data(self, group_name: str, polarity: str = None):
        """Stub - returns None"""
        return None

    def get_comparison_summary(self, group_name: str):
        """Stub - returns empty dict"""
        return {}
