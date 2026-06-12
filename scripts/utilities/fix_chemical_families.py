#!/usr/bin/env python3
"""
Fix Chemical Family Classifications in Fragment Database

Properly classifies fragments based on chemical rules:
- Aromatic: C6H3-C6H7, C7H5-C7H9 and similar aromatic markers
- Saturated carbon: CxHy where H/C ≥ 2 and no O
- Unsaturated carbon: CxHy where H/C < 2 and no O
- Keep existing Al-based, Organic_oxygen, Hydroxyl, Carbonyl, Contamination
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# Aromatic markers (C6 and C7 benzene-like fragments)
AROMATIC_FORMULAS = [
    'C6H3', 'C6H4', 'C6H5', 'C6H6', 'C6H7',
    'C7H3', 'C7H4', 'C7H5', 'C7H6', 'C7H7', 'C7H8', 'C7H9',
    'C8H5', 'C8H6', 'C8H7', 'C8H8', 'C8H9', 'C8H10'
]

def classify_chemical_family(formula_clean: str, current_family: str) -> str:
    """
    Classify fragment into chemical family

    Args:
        formula_clean: Formula without charge (e.g., 'C7H7')
        current_family: Current family assignment

    Returns:
        Proper chemical family
    """
    # Keep specific families that are already correct
    keep_as_is = [
        'Al-based', 'Organic_oxygen', 'Hydroxyl',
        'Carbonyl', 'Contamination'
    ]

    if current_family in keep_as_is:
        return current_family

    # Check for aromatic markers
    if formula_clean in AROMATIC_FORMULAS:
        return 'Aromatic'

    # Parse formula for carbon/hydrogen content
    # Simple parser for CxHy fragments
    c_count = 0
    h_count = 0
    has_o = 'O' in formula_clean
    has_al = 'Al' in formula_clean

    # Extract C count
    if 'C' in formula_clean:
        c_part = formula_clean.split('C')[1]
        if c_part and c_part[0].isdigit():
            num_str = ''
            for char in c_part:
                if char.isdigit():
                    num_str += char
                else:
                    break
            c_count = int(num_str) if num_str else 1
        else:
            c_count = 1

    # Extract H count
    if 'H' in formula_clean:
        h_parts = formula_clean.split('H')
        if len(h_parts) > 1:
            h_part = h_parts[1]
            if h_part and h_part[0].isdigit():
                num_str = ''
                for char in h_part:
                    if char.isdigit():
                        num_str += char
                    else:
                        break
                h_count = int(num_str) if num_str else 1
            else:
                h_count = 1

    # Classification rules
    if has_al:
        return 'Al-based'
    elif has_o:
        return 'Organic_oxygen'
    elif c_count > 0 and h_count > 0:
        h_c_ratio = h_count / c_count
        if h_c_ratio >= 2.0:
            return 'Saturated_carbon'
        elif h_c_ratio < 2.0:
            return 'Unsaturated_carbon'

    # Default to Unknown for everything else
    return 'Unknown'


def fix_database_families(database_path: Path, backup: bool = True):
    """
    Fix chemical family classifications in database

    Args:
        database_path: Path to fragment database JSON
        backup: Whether to create backup before modifying
    """
    # Load database
    print(f"Loading database: {database_path}")
    with open(database_path, 'r') as f:
        db = json.load(f)

    # Create backup if requested
    if backup:
        backup_dir = database_path.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"before_family_fix_{timestamp}.json"
        shutil.copy(database_path, backup_path)
        print(f"✅ Created backup: {backup_path}")

    # Track changes
    changes_by_polarity = {'negative': {}, 'positive': {}}
    total_changes = 0

    # Fix each fragment
    for frag in db['fragments']:
        polarity = frag['polarity']
        formulas = frag.get('formulas', [])
        families = frag.get('families', [])

        # Process each formula/family pair
        new_families = []
        for i, formula in enumerate(formulas):
            # Get current family
            current_family = families[i] if i < len(families) else 'Unknown'

            # Clean formula (remove charge)
            formula_clean = formula.replace('+', '').replace('-', '').strip()

            # Get new family
            new_family = classify_chemical_family(formula_clean, current_family)
            new_families.append(new_family)

            # Track changes
            if new_family != current_family:
                change_key = f"{current_family} → {new_family}"
                if change_key not in changes_by_polarity[polarity]:
                    changes_by_polarity[polarity][change_key] = []
                changes_by_polarity[polarity][change_key].append(
                    f"m/z {frag['mass']:.4f} ({formula})"
                )
                total_changes += 1

        # Update families
        frag['families'] = new_families

    # Update metadata
    db['metadata']['last_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db['metadata']['family_fix_date'] = datetime.now().strftime('%Y-%m-%d')

    # Save updated database
    with open(database_path, 'w') as f:
        json.dump(db, f, indent=2)

    print(f"\n✅ Updated database: {database_path}")
    print(f"   Total changes: {total_changes}")

    # Print summary
    print("\n" + "="*70)
    print("CHANGES SUMMARY")
    print("="*70)

    for polarity in ['negative', 'positive']:
        if changes_by_polarity[polarity]:
            print(f"\n{polarity.upper()} IONS:")
            for change, examples in sorted(changes_by_polarity[polarity].items()):
                print(f"\n  {change}: {len(examples)} fragments")
                for ex in examples[:3]:
                    print(f"    - {ex}")
                if len(examples) > 3:
                    print(f"    ... and {len(examples) - 3} more")

    print("\n" + "="*70)

    # Print final distribution
    print("\nFINAL FAMILY DISTRIBUTION:")
    print("="*70)

    for polarity in ['negative', 'positive']:
        family_counts = {}
        for frag in db['fragments']:
            if frag['polarity'] == polarity:
                for family in frag.get('families', []):
                    family_counts[family] = family_counts.get(family, 0) + 1

        print(f"\n{polarity.upper()} ions:")
        for family, count in sorted(family_counts.items(), key=lambda x: -x[1]):
            print(f"  {family:25s}: {count:3d} fragments")


if __name__ == '__main__':
    # Use relative path from project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    database_path = project_root / 'data' / 'FragmentDatabase' / 'alucone_fragments_complete.json'
    fix_database_families(database_path, backup=True)
    print("\n✅ Chemical family classification complete!")
