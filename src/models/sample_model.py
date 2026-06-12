"""
Sample Model - Data structures for sample metadata and grouping.

Pure Python data models with no Qt or UI dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum


class Polarity(Enum):
    """Ion polarity for ToF-SIMS analysis."""
    POSITIVE = "positive"
    NEGATIVE = "negative"

    @property
    def display_name(self) -> str:
        """Get display-friendly name for polarity."""
        return self.value.capitalize()

    @classmethod
    def from_string(cls, polarity_str: str) -> 'Polarity':
        """
        Convert string to Polarity enum.

        Args:
            polarity_str: String representation ('positive', 'negative', etc.)

        Returns:
            Polarity enum value
        """
        polarity_lower = polarity_str.lower()
        for polarity in cls:
            if polarity.value == polarity_lower:
                return polarity
        raise ValueError(f"Invalid polarity: {polarity_str}")


@dataclass
class Sample:
    """
    Represents a single ToF-SIMS sample.

    Attributes:
        name: Sample identifier
        dose: E-beam dose (µC/cm²), 0 for as-deposited
        replicate: Replicate number (1, 2, 3, ...)
        polarity: Ion polarity (positive/negative)
        group: Optional group name for analysis
        metadata: Additional sample metadata
        is_control: Whether this is a control/reference sample
        notes: Optional notes about the sample
    """
    name: str
    dose: float = 0.0
    replicate: int = 1
    polarity: Polarity = Polarity.NEGATIVE
    group: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    is_control: bool = False
    notes: str = ""

    @property
    def dose_label(self) -> str:
        """Get formatted dose label."""
        if self.dose == 0:
            return "As Deposited"
        elif self.dose >= 1000:
            return f"{int(self.dose)}µC"
        else:
            return f"{self.dose}µC"

    @property
    def display_name(self) -> str:
        """Get display-friendly name."""
        if self.group:
            return f"{self.group}_{self.replicate}"
        return self.name

    def matches_criteria(self, dose: Optional[float] = None,
                        group: Optional[str] = None,
                        replicate: Optional[int] = None) -> bool:
        """
        Check if sample matches given criteria.

        Args:
            dose: Dose to match (None to ignore)
            group: Group to match (None to ignore)
            replicate: Replicate to match (None to ignore)

        Returns:
            True if all provided criteria match
        """
        if dose is not None and self.dose != dose:
            return False
        if group is not None and self.group != group:
            return False
        if replicate is not None and self.replicate != replicate:
            return False
        return True


@dataclass
class SampleGroup:
    """
    Represents a group of related samples (e.g., same dose, different replicates).

    Attributes:
        name: Group identifier
        samples: List of samples in this group
        dose: Common dose for this group (None if mixed)
        polarity: Common polarity (None if mixed)
        description: Optional description
        color: Optional color for visualization
    """
    name: str
    samples: List[Sample] = field(default_factory=list)
    dose: Optional[float] = None
    polarity: Optional[Polarity] = None
    description: str = ""
    color: Optional[str] = None

    def __post_init__(self):
        """Validate group consistency after initialization."""
        if self.samples:
            self._validate_consistency()

    def _validate_consistency(self):
        """Check if samples have consistent dose and polarity."""
        doses = {s.dose for s in self.samples}
        polarities = {s.polarity for s in self.samples}

        if len(doses) == 1:
            self.dose = doses.pop()
        if len(polarities) == 1:
            self.polarity = polarities.pop()

    def add_sample(self, sample: Sample):
        """
        Add a sample to this group.

        Args:
            sample: Sample to add
        """
        self.samples.append(sample)
        sample.group = self.name
        self._validate_consistency()

    def remove_sample(self, sample: Sample):
        """
        Remove a sample from this group.

        Args:
            sample: Sample to remove
        """
        if sample in self.samples:
            self.samples.remove(sample)
            sample.group = None
            self._validate_consistency()

    @property
    def n_samples(self) -> int:
        """Number of samples in the group."""
        return len(self.samples)

    @property
    def sample_names(self) -> List[str]:
        """Get list of sample names in this group."""
        return [s.name for s in self.samples]

    @property
    def replicates(self) -> Set[int]:
        """Get set of replicate numbers in this group."""
        return {s.replicate for s in self.samples}

    def get_samples_by_dose(self, dose: float) -> List[Sample]:
        """Get all samples with a specific dose."""
        return [s for s in self.samples if s.dose == dose]

    def get_samples_by_replicate(self, replicate: int) -> List[Sample]:
        """Get all samples with a specific replicate number."""
        return [s for s in self.samples if s.replicate == replicate]


@dataclass
class SampleSet:
    """
    Collection of sample groups for an analysis.

    Attributes:
        name: Name of the sample set
        groups: Dictionary of group name -> SampleGroup
        polarity: Common polarity for all samples
        description: Optional description
    """
    name: str
    groups: Dict[str, SampleGroup] = field(default_factory=dict)
    polarity: Optional[Polarity] = None
    description: str = ""

    def add_group(self, group: SampleGroup):
        """Add a sample group to this set."""
        self.groups[group.name] = group

    def remove_group(self, group_name: str):
        """Remove a sample group from this set."""
        if group_name in self.groups:
            del self.groups[group_name]

    def get_all_samples(self) -> List[Sample]:
        """Get a flat list of all samples across all groups."""
        samples = []
        for group in self.groups.values():
            samples.extend(group.samples)
        return samples

    def get_sample_by_name(self, name: str) -> Optional[Sample]:
        """Find a sample by name."""
        for sample in self.get_all_samples():
            if sample.name == name:
                return sample
        return None

    @property
    def n_groups(self) -> int:
        """Number of groups in this set."""
        return len(self.groups)

    @property
    def n_total_samples(self) -> int:
        """Total number of samples across all groups."""
        return sum(g.n_samples for g in self.groups.values())

    @property
    def dose_levels(self) -> Set[float]:
        """Get all unique dose levels in this set."""
        return {s.dose for s in self.get_all_samples()}
