"""
Spectrum Model - Data structures for mass spectrum data.

Pure Python data models with no Qt or UI dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import numpy as np
import pandas as pd
from .sample_model import Sample, Polarity
from .fragment_model import FragmentAssignment


@dataclass
class MassSpectrum:
    """
    Represents a single ToF-SIMS mass spectrum.

    Attributes:
        sample: Associated sample
        mass_values: m/z values
        intensities: Intensity values (TIC-normalized)
        raw_intensities: Raw intensity values (optional)
        assignments: Fragment assignments for peaks
        polarity: Ion polarity
        tic_value: Total ion count (optional)
        metadata: Additional spectrum metadata
    """
    sample: Sample
    mass_values: np.ndarray
    intensities: np.ndarray
    raw_intensities: Optional[np.ndarray] = None
    assignments: Dict[float, FragmentAssignment] = field(default_factory=dict)
    polarity: Polarity = Polarity.NEGATIVE
    tic_value: Optional[float] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate spectrum after initialization."""
        if len(self.mass_values) != len(self.intensities):
            raise ValueError(
                f"mass_values ({len(self.mass_values)}) and intensities "
                f"({len(self.intensities)}) must have same length"
            )

        if self.raw_intensities is not None:
            if len(self.raw_intensities) != len(self.intensities):
                raise ValueError(
                    f"raw_intensities length ({len(self.raw_intensities)}) must match "
                    f"intensities length ({len(self.intensities)})"
                )

    @property
    def n_peaks(self) -> int:
        """Number of peaks in spectrum."""
        return len(self.mass_values)

    @property
    def n_assigned(self) -> int:
        """Number of assigned peaks."""
        return sum(1 for a in self.assignments.values() if a.is_assigned)

    @property
    def assignment_rate(self) -> float:
        """Fraction of peaks that are assigned (0.0 to 1.0)."""
        if not self.assignments:
            return 0.0
        return self.n_assigned / len(self.assignments)

    def get_peak_at_mz(self, mz: float, tolerance_da: float = 0.01) -> Optional[tuple]:
        """
        Find peak closest to target m/z within tolerance.

        Args:
            mz: Target m/z value
            tolerance_da: Tolerance in Daltons

        Returns:
            (mz, intensity) tuple or None if no peak found
        """
        idx = np.argmin(np.abs(self.mass_values - mz))
        if abs(self.mass_values[idx] - mz) <= tolerance_da:
            return (self.mass_values[idx], self.intensities[idx])
        return None

    def get_assignment(self, mz: float) -> Optional[FragmentAssignment]:
        """Get fragment assignment for a specific m/z value."""
        return self.assignments.get(mz)

    def add_assignment(self, mz: float, assignment: FragmentAssignment):
        """Add or update fragment assignment."""
        self.assignments[mz] = assignment

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert spectrum to DataFrame.

        Returns:
            DataFrame with columns: mz, intensity, [raw_intensity], [assignment], [formula]
        """
        data = {
            'mz': self.mass_values,
            'intensity': self.intensities
        }

        if self.raw_intensities is not None:
            data['raw_intensity'] = self.raw_intensities

        # Add assignments if available
        if self.assignments:
            formulas = []
            assignment_labels = []
            for mz in self.mass_values:
                assignment = self.assignments.get(mz)
                if assignment and assignment.is_assigned:
                    formulas.append(assignment.fragment.formula)
                    assignment_labels.append(assignment.assignment_label)
                else:
                    formulas.append("")
                    assignment_labels.append("unassigned")

            data['formula'] = formulas
            data['assignment'] = assignment_labels

        return pd.DataFrame(data)


@dataclass
class SpectrumData:
    """
    Collection of mass spectra for multiple samples.

    Attributes:
        name: Dataset name
        spectra: Dictionary mapping sample name -> spectrum
        polarity: Common polarity for all spectra
        is_normalized: Whether intensities are TIC-normalized
        mass_range: (min_mz, max_mz) tuple
        description: Optional description
    """
    name: str
    spectra: Dict[str, MassSpectrum] = field(default_factory=dict)
    polarity: Optional[Polarity] = None
    is_normalized: bool = True
    mass_range: Optional[tuple] = None
    description: str = ""

    def add_spectrum(self, spectrum: MassSpectrum):
        """Add a spectrum to the dataset."""
        self.spectra[spectrum.sample.name] = spectrum
        self._update_mass_range(spectrum)

    def remove_spectrum(self, sample_name: str):
        """Remove a spectrum from the dataset."""
        if sample_name in self.spectra:
            del self.spectra[sample_name]

    def get_spectrum(self, sample_name: str) -> Optional[MassSpectrum]:
        """Get spectrum for a specific sample."""
        return self.spectra.get(sample_name)

    def _update_mass_range(self, spectrum: MassSpectrum):
        """Update mass range based on added spectrum."""
        mz_min = spectrum.mass_values.min()
        mz_max = spectrum.mass_values.max()

        if self.mass_range is None:
            self.mass_range = (mz_min, mz_max)
        else:
            self.mass_range = (
                min(self.mass_range[0], mz_min),
                max(self.mass_range[1], mz_max)
            )

    def to_intensity_matrix(self) -> pd.DataFrame:
        """
        Convert all spectra to intensity matrix.

        Returns:
            DataFrame with m/z as index, sample names as columns
        """
        # Get all unique m/z values
        all_mz = set()
        for spectrum in self.spectra.values():
            all_mz.update(spectrum.mass_values)

        mz_sorted = sorted(all_mz)

        # Build intensity matrix
        data = {}
        for sample_name, spectrum in self.spectra.items():
            # Create lookup for this spectrum
            mz_to_intensity = dict(zip(spectrum.mass_values, spectrum.intensities))
            # Map to sorted m/z list (0 for missing values)
            data[sample_name] = [mz_to_intensity.get(mz, 0.0) for mz in mz_sorted]

        return pd.DataFrame(data, index=mz_sorted)

    @property
    def n_spectra(self) -> int:
        """Number of spectra in dataset."""
        return len(self.spectra)

    @property
    def sample_names(self) -> List[str]:
        """Get list of all sample names."""
        return list(self.spectra.keys())

    @property
    def average_assignment_rate(self) -> float:
        """Average assignment rate across all spectra."""
        if not self.spectra:
            return 0.0
        rates = [s.assignment_rate for s in self.spectra.values()]
        return np.mean(rates)
