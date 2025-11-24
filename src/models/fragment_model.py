"""
Fragment Model - Data structures for fragment assignments and classifications.

Pure Python data models with no Qt or UI dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from .sample_model import Polarity


class AssignmentConfidence(Enum):
    """Confidence level for fragment assignment."""
    HIGH = "high"          # < 10 ppm error
    MEDIUM = "medium"      # 10-50 ppm error
    LOW = "low"            # 50-100 ppm error
    UNCERTAIN = "uncertain"  # > 100 ppm error
    MANUAL = "manual"      # Manually assigned


@dataclass
class Fragment:
    """
    Represents a single fragment ion.

    Attributes:
        formula: Chemical formula (e.g., "C6H5", "CHO")
        exact_mass: Calculated exact m/z
        polarity: Ion polarity
        charge: Ion charge (+1, -1, etc.)
        chemical_family: Classification (e.g., "Aromatic", "Carbonyl")
        is_aromatic: Whether fragment contains aromatic markers
        dbe: Double bond equivalent
        h_c_ratio: H/C ratio
        metadata: Additional fragment metadata
    """
    formula: str
    exact_mass: float
    polarity: Polarity
    charge: int = 1
    chemical_family: str = "Unknown"
    is_aromatic: bool = False
    dbe: float = 0.0
    h_c_ratio: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def display_formula(self) -> str:
        """Get display-friendly formula with charge."""
        charge_str = "+" if self.charge > 0 else "-"
        if abs(self.charge) > 1:
            charge_str = f"{abs(self.charge)}{charge_str}"
        return f"{self.formula}{charge_str}"

    @property
    def mass_label(self) -> str:
        """Get formatted mass label."""
        return f"m/z {self.exact_mass:.4f}"


@dataclass
class FragmentAssignment:
    """
    Represents an assignment of a measured peak to a fragment.

    Attributes:
        measured_mz: Measured m/z value from spectrum
        fragment: Assigned fragment (None if unassigned)
        confidence: Assignment confidence level
        ppm_error: Mass error in ppm
        alternatives: Alternative fragment assignments
        is_assigned: Whether peak has been assigned
        notes: Optional notes about the assignment
    """
    measured_mz: float
    fragment: Optional[Fragment] = None
    confidence: AssignmentConfidence = AssignmentConfidence.UNCERTAIN
    ppm_error: float = 0.0
    alternatives: List[Fragment] = field(default_factory=list)
    is_assigned: bool = False
    notes: str = ""

    def assign(self, fragment: Fragment, ppm_error: float):
        """
        Assign a fragment to this peak.

        Args:
            fragment: Fragment to assign
            ppm_error: Mass error in ppm
        """
        self.fragment = fragment
        self.ppm_error = ppm_error
        self.is_assigned = True
        self._update_confidence()

    def _update_confidence(self):
        """Update confidence based on ppm error."""
        abs_error = abs(self.ppm_error)
        if abs_error < 10:
            self.confidence = AssignmentConfidence.HIGH
        elif abs_error < 50:
            self.confidence = AssignmentConfidence.MEDIUM
        elif abs_error < 100:
            self.confidence = AssignmentConfidence.LOW
        else:
            self.confidence = AssignmentConfidence.UNCERTAIN

    def unassign(self):
        """Remove fragment assignment."""
        self.fragment = None
        self.is_assigned = False
        self.confidence = AssignmentConfidence.UNCERTAIN
        self.ppm_error = 0.0

    def add_alternative(self, fragment: Fragment):
        """Add an alternative fragment assignment."""
        if fragment not in self.alternatives:
            self.alternatives.append(fragment)

    @property
    def has_alternatives(self) -> bool:
        """Whether there are alternative assignments."""
        return len(self.alternatives) > 0

    @property
    def assignment_label(self) -> str:
        """Get label for this assignment."""
        if not self.is_assigned or self.fragment is None:
            return f"m/z {self.measured_mz:.4f} (unassigned)"
        return f"{self.fragment.display_formula} ({self.confidence.value}, {self.ppm_error:+.1f} ppm)"


@dataclass
class FragmentDatabase:
    """
    Database of known fragments for assignment.

    Attributes:
        name: Database name
        fragments: List of known fragments
        polarity: Database polarity (or None for mixed)
        metadata: Database metadata
    """
    name: str
    fragments: List[Fragment] = field(default_factory=list)
    polarity: Optional[Polarity] = None
    metadata: Dict[str, any] = field(default_factory=lambda: {
        "version": "1.0",
        "created": "",
        "total_fragments": 0
    })

    def __post_init__(self):
        """Update metadata after initialization."""
        self.metadata["total_fragments"] = len(self.fragments)

    def add_fragment(self, fragment: Fragment):
        """Add a fragment to the database."""
        if fragment not in self.fragments:
            self.fragments.append(fragment)
            self.metadata["total_fragments"] = len(self.fragments)

    def remove_fragment(self, fragment: Fragment):
        """Remove a fragment from the database."""
        if fragment in self.fragments:
            self.fragments.remove(fragment)
            self.metadata["total_fragments"] = len(self.fragments)

    def find_by_formula(self, formula: str) -> Optional[Fragment]:
        """Find a fragment by exact formula match."""
        normalized = formula.replace("_", "")
        for frag in self.fragments:
            if frag.formula.replace("_", "") == normalized:
                return frag
        return None

    def find_by_mass(self, mz: float, tolerance_ppm: float = 50.0) -> List[Fragment]:
        """
        Find fragments within mass tolerance.

        Args:
            mz: Target m/z value
            tolerance_ppm: Tolerance in ppm

        Returns:
            List of matching fragments sorted by mass error
        """
        matches = []
        for frag in self.fragments:
            error_ppm = abs((frag.exact_mass - mz) / mz * 1e6)
            if error_ppm <= tolerance_ppm:
                matches.append((frag, error_ppm))

        # Sort by error (best match first)
        matches.sort(key=lambda x: x[1])
        return [frag for frag, _ in matches]

    def get_by_family(self, family: str) -> List[Fragment]:
        """Get all fragments of a specific chemical family."""
        return [f for f in self.fragments if f.chemical_family == family]

    @property
    def families(self) -> List[str]:
        """Get list of unique chemical families in database."""
        return sorted(set(f.chemical_family for f in self.fragments))

    @property
    def n_fragments(self) -> int:
        """Number of fragments in database."""
        return len(self.fragments)
