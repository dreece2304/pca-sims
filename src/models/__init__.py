"""
Data models for ToF-SIMS PCA analysis.

This package contains pure Python data models with no Qt or UI dependencies.
Models represent application state and data structures.
"""

# PCA Models
from .pca_model import PCAModel, PCAResults

# Sample Models
from .sample_model import (
    Sample,
    SampleGroup,
    SampleSet,
    Polarity
)

# Fragment Models
from .fragment_model import (
    Fragment,
    FragmentAssignment,
    FragmentDatabase,
    AssignmentConfidence
)

# Spectrum Models
from .spectrum_model import (
    MassSpectrum,
    SpectrumData
)

__all__ = [
    # PCA
    'PCAModel',
    'PCAResults',
    # Samples
    'Sample',
    'SampleGroup',
    'SampleSet',
    'Polarity',
    # Fragments
    'Fragment',
    'FragmentAssignment',
    'FragmentDatabase',
    'AssignmentConfidence',
    # Spectra
    'MassSpectrum',
    'SpectrumData',
]
