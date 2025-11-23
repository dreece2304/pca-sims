#!/usr/bin/env python3
"""
Comprehensive Fragment Database Cleanup
Fixes all identified issues:
1. Removes corrupted unknown polarity entries
2. Merges formula duplicates
3. Reports mass collisions (keeps all - they're valid isobars)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from fragment_mass_calculator import calculate_mass_from_assignment


def comprehensive_cleanup(db_path: str, dry_run: bool = True):
    """
    Comprehensive database cleanup

    Args:
        db_path: Path to fragment database JSON
        dry_run: If True, only report changes without modifying database
    """
    print("🧹 Comprehensive Fragment Database Cleanup")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify database)'}")
    print()

    # Load database
    with open(db_path, 'r') as f:
        db = json.load(f)

    original_count = len(db['fragments'])
    print(f"Original fragment count: {original_count}")
    print()

    # ========== STEP 1: Remove corrupted entries ==========
    print("STEP 1: Removing corrupted entries (polarity=unknown, mass=0)")
    print("-" * 70)

    valid_frags = []
    corrupted_frags = []

    for frag in db['fragments']:
        if frag.get('polarity') == 'unknown':
            corrupted_frags.append(frag)
        else:
            valid_frags.append(frag)

    print(f"  Found {len(corrupted_frags)} corrupted entries")
    print(f"  Keeping {len(valid_frags)} valid entries")
    print()

    # ========== STEP 2: Merge formula duplicates ==========
    print("STEP 2: Merging formula duplicates")
    print("-" * 70)

    # Group by formula and polarity
    formula_groups = defaultdict(list)
    for frag in valid_frags:
        polarity = frag.get('polarity')
        formulas = frag.get('formulas', [])

        for formula in formulas:
            if formula:
                key = (formula.replace('_', ''), polarity)
                formula_groups[key].append(frag)
                break  # Only use first formula

    # Merge duplicates
    cleaned_fragments = []
    duplicates_merged = 0

    for (formula, polarity), frag_list in formula_groups.items():
        if len(frag_list) > 1:
            # Multiple entries - merge
            duplicates_merged += len(frag_list) - 1

            print(f"  Merging {len(frag_list)} entries for {formula} ({polarity}):")
            for frag in frag_list:
                mass = frag.get('mass', 0)
                assignments = frag.get('assignments', ['?'])
                print(f"    m/z {mass:.6f} - {assignments}")

            # Use first entry as base
            base_frag = frag_list[0].copy()

            # Collect all unique assignments
            all_assignments = []
            for frag in frag_list:
                all_assignments.extend(frag.get('assignments', []))

            base_frag['assignments'] = sorted(list(set(all_assignments)))

            # Recalculate exact mass from first assignment
            try:
                exact_mass = calculate_mass_from_assignment(base_frag['assignments'][0])
                base_frag['mass'] = exact_mass
                print(f"    → Merged: exact mass = {exact_mass:.6f}")
            except Exception as e:
                print(f"    ⚠️ Could not calculate exact mass: {e}")

            base_frag['notes'] = f"Cleaned and merged on {datetime.now().strftime('%Y-%m-%d')}"
            cleaned_fragments.append(base_frag)
            print()

        else:
            # Single entry - keep as is
            cleaned_fragments.append(frag_list[0])

    print(f"  Duplicates merged: {duplicates_merged}")
    print()

    # ========== STEP 3: Report mass collisions (isobars) ==========
    print("STEP 3: Checking for mass collisions (isobars)")
    print("-" * 70)

    mass_groups = defaultdict(list)
    for frag in cleaned_fragments:
        mass_key = (round(frag['mass'], 5), frag['polarity'])
        mass_groups[mass_key].append(frag)

    mass_collisions = [(k, v) for k, v in mass_groups.items() if len(v) > 1]

    if mass_collisions:
        print(f"  Found {len(mass_collisions)} mass collisions:")
        for (mass, polarity), frags in mass_collisions:
            formulas = [f.get('formulas', ['?'])[0] for f in frags]
            print(f"    m/z {mass:.5f} ({polarity}): {formulas}")
        print()
        print("  ℹ️ These are valid isobars (different formulas, same mass)")
        print("     Keeping all entries - assignment will depend on context")
    else:
        print("  ✅ No mass collisions found")
    print()

    # Sort by polarity then mass
    cleaned_fragments.sort(key=lambda x: (x['polarity'], x['mass']))

    # ========== Summary ==========
    final_count = len(cleaned_fragments)
    print("=" * 70)
    print("📊 Cleanup Summary:")
    print(f"  Original fragments: {original_count}")
    print(f"  Corrupted removed: {len(corrupted_frags)}")
    print(f"  Duplicates merged: {duplicates_merged}")
    print(f"  Final fragments: {final_count}")
    print(f"  Net reduction: {original_count - final_count} fragments")
    print()

    if not dry_run:
        # Create backup
        backup_dir = Path(db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"before_comprehensive_cleanup_{timestamp}.json"

        shutil.copy2(db_path, backup_path)
        print(f"📦 Backup created: {backup_path}")

        # Update database
        db['fragments'] = cleaned_fragments
        db['metadata']['total_fragments'] = final_count
        db['metadata']['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db['metadata']['comprehensive_cleanup_date'] = datetime.now().strftime("%Y-%m-%d")

        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2)

        print(f"💾 Database saved: {db_path}")
        print(f"\n✅ Comprehensive cleanup complete!")
    else:
        print(f"⚠️ DRY RUN - No changes made")
        print(f"   Run with --apply to apply changes")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python comprehensive_database_cleanup.py <database.json> [--apply]")
        print("\nOptions:")
        print("  --apply    Apply changes to database (default: dry run)")
        sys.exit(1)

    db_path = sys.argv[1]
    apply_changes = "--apply" in sys.argv

    if not Path(db_path).exists():
        print(f"❌ Error: Database not found: {db_path}")
        sys.exit(1)

    comprehensive_cleanup(db_path, dry_run=not apply_changes)


if __name__ == "__main__":
    main()
