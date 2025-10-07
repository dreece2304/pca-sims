"""
ToF-SIMS Multi-Ion Analysis Package

Unified IO and preprocessing layer for PCA outputs, fragment assignments,
and raw intensities across multiple analysis types and polarities.
"""

__version__ = "0.1.0"

from . import io
from . import preprocess

__all__ = ["io", "preprocess"]
