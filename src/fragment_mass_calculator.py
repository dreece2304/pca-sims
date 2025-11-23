"""
Fragment Mass Calculator
Calculates exact monoisotopic masses from chemical formulas
"""

import re
from typing import Dict, Optional


# Monoisotopic masses (most abundant isotope)
ATOMIC_MASSES = {
    'H': 1.00782503207,
    'C': 12.0000000,
    'N': 14.0030740048,
    'O': 15.99491461956,
    'Al': 26.98153863,
    'Si': 27.9769265325,
    'P': 30.97376163,
    'S': 31.97207100,
    'F': 18.99840322,
    'Cl': 34.96885268,
    'Br': 78.9183371,
    'I': 126.904473,
}

# Electron mass for charge state calculations
ELECTRON_MASS = 0.00054857990907


def parse_formula(formula: str) -> Dict[str, int]:
    """
    Parse chemical formula string into element counts

    Args:
        formula: Chemical formula (e.g., "C6H5", "Al2O3", "C2H5O")

    Returns:
        Dictionary of element: count

    Example:
        >>> parse_formula("C6H5")
        {'C': 6, 'H': 5}
        >>> parse_formula("Al2O3H4")
        {'Al': 2, 'O': 3, 'H': 4}
    """
    # Pattern: Capital letter, optional lowercase, optional number
    pattern = r'([A-Z][a-z]?)(\d*)'
    matches = re.findall(pattern, formula)

    composition = {}
    for element, count in matches:
        if element:  # Skip empty matches
            count = int(count) if count else 1
            composition[element] = composition.get(element, 0) + count

    return composition


def calculate_exact_mass(formula: str, charge: int = 0) -> float:
    """
    Calculate exact monoisotopic mass from chemical formula

    Args:
        formula: Chemical formula (e.g., "C6H5", "Al2O3")
        charge: Charge state (positive = electrons removed, negative = electrons added)

    Returns:
        Exact mass in Daltons

    Example:
        >>> calculate_exact_mass("C6H5", charge=1)  # C6H5+
        77.03912516035
        >>> calculate_exact_mass("C2H5O", charge=1)  # C2H5O+
        45.03349...
    """
    composition = parse_formula(formula)

    mass = 0.0
    for element, count in composition.items():
        if element not in ATOMIC_MASSES:
            raise ValueError(f"Unknown element: {element}")
        mass += ATOMIC_MASSES[element] * count

    # Adjust for charge (positive = remove electrons, negative = add electrons)
    mass -= charge * ELECTRON_MASS

    return mass


def extract_formula_from_assignment(assignment: str) -> tuple[str, int]:
    """
    Extract chemical formula and charge from assignment string

    Args:
        assignment: Fragment assignment (e.g., "C_6H_5+", "Al_2O_3-")

    Returns:
        Tuple of (formula, charge)

    Example:
        >>> extract_formula_from_assignment("C_6H_5+")
        ("C6H5", 1)
        >>> extract_formula_from_assignment("Al_2O_3-")
        ("Al2O3", -1)
    """
    # Remove underscores (subscript notation)
    formula = assignment.replace("_", "")

    # Determine charge
    charge = 0
    if formula.endswith("+"):
        charge = 1
        formula = formula[:-1]
    elif formula.endswith("-"):
        charge = -1
        formula = formula[:-1]
    elif formula.endswith("++"):
        charge = 2
        formula = formula[:-2]
    elif formula.endswith("--"):
        charge = -2
        formula = formula[:-2]

    # Handle multiple charges like +2, -2
    charge_match = re.search(r'([+-])(\d+)$', formula)
    if charge_match:
        sign, num = charge_match.groups()
        charge = int(num) if sign == "+" else -int(num)
        formula = formula[:charge_match.start()]

    return formula, charge


def calculate_mass_from_assignment(assignment: str) -> float:
    """
    Calculate exact mass from fragment assignment string

    Args:
        assignment: Fragment assignment (e.g., "C_6H_5+", "Al_2O_3-")

    Returns:
        Exact mass in Daltons

    Example:
        >>> calculate_mass_from_assignment("C_6H_5+")
        77.03912516035
    """
    formula, charge = extract_formula_from_assignment(assignment)
    return calculate_exact_mass(formula, charge)


def validate_mass_match(measured_mz: float, assignment: str, tolerance_ppm: float = 100) -> dict:
    """
    Validate if measured m/z matches expected mass from assignment

    Args:
        measured_mz: Measured m/z value from instrument
        assignment: Fragment assignment (e.g., "C_6H_5+")
        tolerance_ppm: Mass tolerance in ppm

    Returns:
        Dictionary with validation results

    Example:
        >>> validate_mass_match(77.03938, "C_6H_5+", tolerance_ppm=100)
        {
            'matches': True,
            'exact_mass': 77.039125,
            'measured_mz': 77.03938,
            'error_da': 0.000255,
            'error_ppm': 3.31
        }
    """
    exact_mass = calculate_mass_from_assignment(assignment)
    error_da = measured_mz - exact_mass
    error_ppm = (error_da / exact_mass) * 1e6

    matches = abs(error_ppm) <= tolerance_ppm

    return {
        'matches': matches,
        'exact_mass': exact_mass,
        'measured_mz': measured_mz,
        'error_da': error_da,
        'error_ppm': error_ppm
    }


if __name__ == "__main__":
    # Test examples
    print("Fragment Mass Calculator - Test Examples")
    print("=" * 60)

    test_cases = [
        ("C_6H_5+", 77.03938),   # Phenyl cation
        ("C_2H_5O+", 45.03459),  # Ethoxy cation
        ("Al+", 26.98154),       # Aluminum cation
        ("Al_2O_3+", 101.96089), # Alumina cation
    ]

    for assignment, measured_mz in test_cases:
        result = validate_mass_match(measured_mz, assignment)

        print(f"\n{assignment}:")
        print(f"  Exact mass:    {result['exact_mass']:.6f}")
        print(f"  Measured m/z:  {result['measured_mz']:.6f}")
        print(f"  Error:         {result['error_da']:.6f} Da ({result['error_ppm']:.2f} ppm)")
        print(f"  Match (100ppm): {'✅' if result['matches'] else '❌'}")
