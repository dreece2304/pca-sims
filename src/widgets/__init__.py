"""
UI Widgets and Components for ToF-SIMS PCA Analysis.

This package contains reusable UI components organized by type:
- common: Utility widgets (NumericTableWidgetItem, etc.)
- dialogs: Dialog windows
- plotting: Matplotlib-based plotting widgets
- Fragment analysis tab and other major UI components
"""

from .common import NumericTableWidgetItem
from .fragment_analysis_tab import FragmentAnalysisTab

__all__ = [
    'NumericTableWidgetItem',
    'FragmentAnalysisTab',
]
