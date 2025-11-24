"""
Core domain logic for ToF-SIMS analysis.

This package contains pure domain logic with no UI or Qt dependencies.
These modules perform scientific computations and chemical classifications.
"""

from .fragment_classifier import (
    classify_fragment,
    FragmentProperties,
    CrosslinkingMetrics,
    get_fragment_groups,
    AROMATIC_MARKERS
)
from .crosslinking_metrics import CrosslinkingAnalyzer, SampleMetrics
from .fragment_mass_calculator import (
    calculate_mass_from_assignment,
    extract_formula_from_assignment,
    calculate_exact_mass
)

__all__ = [
    # Fragment classification
    'classify_fragment',
    'FragmentProperties',
    'CrosslinkingMetrics',
    'get_fragment_groups',
    'AROMATIC_MARKERS',
    # Crosslinking analysis
    'CrosslinkingAnalyzer',
    'SampleMetrics',
    # Mass calculations
    'calculate_mass_from_assignment',
    'extract_formula_from_assignment',
    'calculate_exact_mass',
]
