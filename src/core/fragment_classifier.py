"""
Fragment Classification and Chemical Metrics Calculator
Based on ToF-SIMS literature best practices (Sjövall et al. 2023, Mei et al. 2022)

Classifies fragments by:
- Saturation (DBE-based)
- Aromaticity (characteristic markers)
- H-deficiency (polyyne/allene patterns)

Calculates crosslinking metrics:
- C6H-/C4H- ratios (for PMMA-type polymers)
- Molecular ion / fragment ion ratios
"""

import re
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


# ===== FRAGMENT CLASSIFICATION CONSTANTS =====

# Aromatic-characteristic markers from literature (Sjövall et al. 2023)
AROMATIC_MARKERS = {
    # Positive ion markers
    'positive': {
        65.0393: 'C5H5+',      # Cyclopentadienyl (aromatic-derived)
        77.0386: 'C6H5+',      # Phenyl cation (strong aromatic marker)
        91.0542: 'C7H7+',      # Tropylium/benzylium (strong aromatic marker)
        78.0464: 'C6H6+',      # Benzene molecular ion
        128.0626: 'C10H8+',    # Naphthalene
        115.0542: 'C9H7+',     # Indene
    },
    # Negative ion markers
    'negative': {
        65.0033: 'C5H-',       # C5H- (highly unsaturated)
        93.0346: 'C6H5O-',     # Phenoxide (aromatic + oxygen)
        105.0346: 'C7H5O-',    # Hydroxytropylium anion
    }
}

# Tolerance for matching aromatic markers (±0.01 Da)
AROMATIC_MARKER_TOLERANCE = 0.01


# ===== DATA CLASSES =====

@dataclass
class FragmentProperties:
    """Chemical properties of a fragment"""
    formula: str
    mass: float
    polarity: str

    # Composition
    c_count: int
    h_count: int
    o_count: int = 0
    n_count: int = 0
    al_count: int = 0
    si_count: int = 0
    other_atoms: Dict[str, int] = None

    # Calculated properties
    dbe: Optional[float] = None
    h_c_ratio: Optional[float] = None

    # Classifications
    saturation_class: str = "Unknown"
    chemical_family: str = "Unknown"
    is_aromatic_marker: bool = False
    aromatic_marker_name: Optional[str] = None


@dataclass
class CrosslinkingMetrics:
    """Crosslinking indicators for polymer samples"""
    sample_name: str

    # Fragment intensity ratios (indicators of crosslinking)
    c6h_to_c4h_ratio: Optional[float] = None  # C6H-/C4H- (PMMA crosslinking indicator)

    # Molecular ion metrics
    molecular_ion_intensity: Optional[float] = None
    fragment_ion_intensity: Optional[float] = None
    mol_to_frag_ratio: Optional[float] = None

    # H-deficiency metrics
    h_deficient_fraction: Optional[float] = None  # From Sjövall eq. 1

    # Notes
    notes: str = ""


# ===== CHEMICAL FORMULA PARSING =====

def parse_formula(formula: str) -> Dict[str, int]:
    """
    Parse chemical formula string into element counts

    Args:
        formula: Chemical formula (e.g., "C6H5", "C2H3O")

    Returns:
        Dictionary of element: count
    """
    # Remove charge indicators and underscores
    formula = formula.replace('+', '').replace('-', '').replace('_', '')

    # Pattern: Capital letter, optional lowercase, optional number
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)

    composition = {}
    for element, count in matches:
        if element:  # Skip empty matches
            count = int(count) if count else 1
            composition[element] = composition.get(element, 0) + count

    return composition


def calculate_dbe(c: int, h: int, n: int = 0, x: int = 0) -> float:
    """
    Calculate Double Bond Equivalents (Degree of Unsaturation)

    DBE = C + 1 - H/2 - X/2 + N/2

    Where:
        C = carbons
        H = hydrogens
        N = nitrogens (trivalent)
        X = halogens (monovalent)

    Args:
        c: Carbon count
        h: Hydrogen count
        n: Nitrogen count (default 0)
        x: Halogen count (default 0)

    Returns:
        DBE value (can be fractional for fragments)
    """
    if c == 0:
        return 0.0

    dbe = c + 1 - h/2 - x/2 + n/2
    return dbe


def calculate_h_c_ratio(h: int, c: int) -> float:
    """Calculate H/C ratio"""
    if c == 0:
        return 0.0
    return h / c


# ===== FRAGMENT CLASSIFICATION =====

def classify_saturation(dbe: float, h_c_ratio: float) -> str:
    """
    Classify fragment by saturation level based on DBE and H/C ratio

    Classification follows literature guidelines:
    - Saturated: DBE = 0, high H/C
    - Unsaturated: DBE = 1-3, moderate H/C
    - Highly unsaturated: DBE ≥ 4 OR very low H/C
    - H-deficient: H/C < 0.8 (polyynes, allenes)

    Args:
        dbe: Double bond equivalents
        h_c_ratio: Hydrogen to carbon ratio

    Returns:
        Classification string
    """
    if dbe == 0:
        return "Saturated"
    elif h_c_ratio < 0.8:
        return "H-deficient"  # Polyynes, allenes (CnH, C2n+1H3)
    elif dbe >= 4:
        return "Highly_unsaturated"  # Could be aromatic (benzene = DBE 4)
    elif 1 <= dbe <= 3:
        return "Unsaturated"
    else:
        return "Unknown"


def is_aromatic_marker(mass: float, polarity: str) -> Tuple[bool, Optional[str]]:
    """
    Check if fragment matches known aromatic markers from literature

    Args:
        mass: Fragment m/z value
        polarity: 'positive' or 'negative'

    Returns:
        (is_marker, marker_name) tuple
    """
    markers = AROMATIC_MARKERS.get(polarity, {})

    for marker_mass, marker_name in markers.items():
        if abs(mass - marker_mass) < AROMATIC_MARKER_TOLERANCE:
            return True, marker_name

    return False, None


def classify_chemical_family(props: FragmentProperties) -> str:
    """
    Assign chemical family based on composition and properties

    Priority order:
    1. Aromatic markers (literature-validated)
    2. Al-based fragments
    3. H-deficiency (polyynes, allenes)
    4. Oxygen-containing organics
    5. Saturation-based classification

    Args:
        props: FragmentProperties object

    Returns:
        Chemical family string
    """
    # Check for aromatic markers first (most specific)
    if props.is_aromatic_marker:
        return "Aromatic"

    # Al-based
    if props.al_count > 0:
        return "Al-based"

    # H-deficient fragments (polyynes, allenes)
    if props.h_c_ratio < 0.8 and props.c_count > 0:
        return "H-deficient_unsaturated"

    # Oxygen-containing organics
    if props.o_count > 0:
        # Distinguish carbonyl vs. hydroxyl
        if props.h_count == 0 or props.o_count > props.h_count:
            return "Carbonyl"
        else:
            return "Organic_oxygen"

    # Saturation-based
    if props.saturation_class == "Saturated":
        return "Saturated_carbon"
    elif props.saturation_class in ["Unsaturated", "Highly_unsaturated"]:
        return "Unsaturated_carbon"

    return "Unknown"


def classify_fragment(formula: str, mass: float, polarity: str) -> FragmentProperties:
    """
    Complete classification of a fragment

    Args:
        formula: Chemical formula (e.g., "C6H5", "C2H3O")
        mass: m/z value
        polarity: 'positive' or 'negative'

    Returns:
        FragmentProperties object with all classifications
    """
    composition = parse_formula(formula)

    # Extract atom counts
    c = composition.get('C', 0)
    h = composition.get('H', 0)
    o = composition.get('O', 0)
    n = composition.get('N', 0)
    al = composition.get('Al', 0)
    si = composition.get('Si', 0)

    # Calculate halogens
    x = sum(composition.get(elem, 0) for elem in ['F', 'Cl', 'Br', 'I'])

    # Other atoms
    other = {k: v for k, v in composition.items()
             if k not in ['C', 'H', 'O', 'N', 'Al', 'Si', 'F', 'Cl', 'Br', 'I']}

    # Calculate properties
    dbe = calculate_dbe(c, h, n, x) if c > 0 else 0
    h_c_ratio = calculate_h_c_ratio(h, c) if c > 0 else 0

    # Check for aromatic markers
    is_aromatic, aromatic_name = is_aromatic_marker(mass, polarity)

    # Classify saturation
    saturation = classify_saturation(dbe, h_c_ratio)

    # Create properties object
    props = FragmentProperties(
        formula=formula,
        mass=mass,
        polarity=polarity,
        c_count=c,
        h_count=h,
        o_count=o,
        n_count=n,
        al_count=al,
        si_count=si,
        other_atoms=other if other else None,
        dbe=dbe,
        h_c_ratio=h_c_ratio,
        saturation_class=saturation,
        is_aromatic_marker=is_aromatic,
        aromatic_marker_name=aromatic_name
    )

    # Assign chemical family
    props.chemical_family = classify_chemical_family(props)

    return props


# ===== CROSSLINKING METRICS =====

def calculate_h_deficient_fraction(fragment_intensities: Dict[str, float]) -> float:
    """
    Calculate fraction of H-deficient fragments (Sjövall et al. 2023, Eq. 1)

    Fraction = (C4H3 + C5H3 + C7H3) / (C4H3 + C5H3 + C7H3 + C4H9 + C5H9 + C7H11)

    This captures H-deficiency while avoiding idiosyncratic responses

    Args:
        fragment_intensities: Dict of {formula: intensity}

    Returns:
        H-deficient fraction (0-1)
    """
    h_deficient = ['C4H3', 'C5H3', 'C7H3']
    h_rich = ['C4H9', 'C5H9', 'C7H11']

    deficient_sum = sum(fragment_intensities.get(f, 0) for f in h_deficient)
    rich_sum = sum(fragment_intensities.get(f, 0) for f in h_rich)

    total = deficient_sum + rich_sum

    if total == 0:
        return 0.0

    return deficient_sum / total


def calculate_crosslinking_metrics(
    sample_name: str,
    fragment_data: Dict[str, Dict],  # {formula: {'intensity': float, 'mass': float}}
    polarity: str = 'negative'
) -> CrosslinkingMetrics:
    """
    Calculate crosslinking indicators for a sample

    Based on literature (Mei et al. 2022):
    - C6H-/C4H- ratio increases with PMMA crosslinking
    - Molecular ion/fragment ratio decreases with crosslinking
    - H-deficient fraction relates to material composition

    Args:
        sample_name: Sample identifier
        fragment_data: Fragment intensities and masses
        polarity: Ion polarity

    Returns:
        CrosslinkingMetrics object
    """
    metrics = CrosslinkingMetrics(sample_name=sample_name)

    # Extract fragment intensities
    intensities = {f: d['intensity'] for f, d in fragment_data.items()}

    # C6H-/C4H- ratio (PMMA crosslinking indicator)
    if polarity == 'negative':
        c6h_int = intensities.get('C6H', 0)
        c4h_int = intensities.get('C4H', 0)

        if c4h_int > 0:
            metrics.c6h_to_c4h_ratio = c6h_int / c4h_int

    # H-deficient fraction
    metrics.h_deficient_fraction = calculate_h_deficient_fraction(intensities)

    # TODO: Molecular ion vs fragment ion requires peak classification
    # This would need integration with PCA high-mass detection

    return metrics


# ===== BATCH PROCESSING =====

def classify_fragment_database(database_path: str) -> List[FragmentProperties]:
    """
    Classify all fragments in a database JSON file

    Args:
        database_path: Path to alucone_fragments_complete.json

    Returns:
        List of FragmentProperties objects
    """
    with open(database_path, 'r') as f:
        db = json.load(f)

    classified = []

    for frag in db['fragments']:
        # Get first formula (primary assignment)
        if not frag['formulas']:
            continue

        formula = frag['formulas'][0]
        mass = frag['mass']
        polarity = frag['polarity']

        props = classify_fragment(formula, mass, polarity)
        classified.append(props)

    return classified


def get_fragment_groups(classified_fragments: List[FragmentProperties]) -> Dict[str, List[FragmentProperties]]:
    """
    Group fragments by chemical family

    Args:
        classified_fragments: List of FragmentProperties

    Returns:
        Dict of {family_name: [fragments]}
    """
    groups = {}

    for frag in classified_fragments:
        family = frag.chemical_family
        if family not in groups:
            groups[family] = []
        groups[family].append(frag)

    return groups


# ===== TESTING =====

if __name__ == "__main__":
    print("Fragment Classifier - Test Examples")
    print("=" * 70)

    # Test cases from literature
    test_fragments = [
        ("C6H5", 77.0386, "positive", "Phenyl (aromatic marker)"),
        ("C7H7", 91.0542, "positive", "Tropylium (aromatic marker)"),
        ("CH2", 14.0156, "negative", "Saturated hydrocarbon"),
        ("C2H3", 27.0235, "negative", "Unsaturated hydrocarbon"),
        ("C4H", 49.0078, "negative", "H-deficient (polyyne)"),
        ("C4HO", 65.0033, "negative", "Highly unsaturated + oxygen"),
        ("C6H5O", 93.0346, "negative", "Phenoxide (aromatic marker)"),
        ("Al2O3", 101.9609, "positive", "Alumina"),
    ]

    for formula, mass, polarity, description in test_fragments:
        props = classify_fragment(formula, mass, polarity)

        print(f"\n{formula} ({description}):")
        print(f"  Mass: {mass:.4f}")
        print(f"  DBE: {props.dbe:.1f}")
        print(f"  H/C ratio: {props.h_c_ratio:.2f}")
        print(f"  Saturation: {props.saturation_class}")
        print(f"  Chemical family: {props.chemical_family}")
        if props.is_aromatic_marker:
            print(f"  ✅ Aromatic marker: {props.aromatic_marker_name}")

    print("\n" + "=" * 70)
    print("✅ Fragment classifier ready for integration!")
