#!/usr/bin/env python3
"""
Fragment Database Cleanup Utility
Merges duplicate fragments and recalculates exact masses from formulas
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


def cleanup_fragment_database(db_path: str, dry_run: bool = True):
    """
    Clean up fragment database by merging duplicates and fixing masses

    Args:
        db_path: Path to fragment database JSON
        dry_run: If True, only report changes without modifying database
    """
    print("🧹 Fragment Database Cleanup Utility")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify database)'}")
    print()

    # Load database
    with open(db_path, 'r') as f:
        db = json.load(f)

    original_count = len(db['fragments'])
    print(f"Original fragment count: {original_count}")

    # Group by formula and polarity
    formula_groups = defaultdict(list)
    for frag in db['fragments']:
        # Handle both singular 'assignment' and plural 'assignments'
        assignments = frag.get('assignments', [frag.get('assignment')]) if frag.get('assignment') else frag.get('assignments', [])

        if not assignments:
            print(f"⚠️ Skipping fragment with no assignment: {frag}")
            continue

        for assignment in assignments:
            # Use first assignment as canonical
            formula = assignment.replace("_", "")  # Remove subscripts
            key = (formula, frag['polarity'])
            formula_groups[key].append((assignment, frag))
            break  # Only use first assignment

    print(f"Unique formula-polarity combinations: {len(formula_groups)}")

    # Process each group
    cleaned_fragments = []
    duplicate_count = 0
    mass_fixed_count = 0

    for (formula, polarity), frag_list in formula_groups.items():
        if len(frag_list) > 1:
            # Multiple entries for same formula - merge them
            duplicate_count += len(frag_list) - 1

            print(f"\n🔍 Duplicate found: {formula} ({polarity})")
            print(f"   {len(frag_list)} entries with masses:")
            for assignment, frag in frag_list:
                print(f"     {frag['mass']:.6f} - {assignment}")

            # Use first entry as base, collect all unique data
            base_assignment = frag_list[0][0]
            base_frag = frag_list[0][1].copy()

            # Collect all unique assignments and formulas (handle both singular and plural)
            all_assignments = []
            all_formulas = []
            for assignment, frag in frag_list:
                # Handle 'assignments' (plural) or 'assignment' (singular)
                if 'assignments' in frag:
                    all_assignments.extend(frag['assignments'])
                elif 'assignment' in frag:
                    all_assignments.append(frag['assignment'])

                # Handle 'formulas' (plural) or 'formula' (singular)
                if 'formulas' in frag:
                    all_formulas.extend(frag['formulas'])
                elif 'formula' in frag:
                    all_formulas.append(frag['formula'])

            base_frag['assignments'] = sorted(list(set(all_assignments)))
            base_frag['formulas'] = sorted(list(set(all_formulas)))

            # Normalize to plural forms
            if 'assignment' in base_frag:
                del base_frag['assignment']
            if 'formula' in base_frag:
                del base_frag['formula']
            if 'family' in base_frag:
                if 'families' not in base_frag:
                    base_frag['families'] = [base_frag['family']]
                del base_frag['family']

            # Calculate exact mass from first assignment
            try:
                exact_mass = calculate_mass_from_assignment(base_assignment)
                old_mass = base_frag['mass']
                base_frag['mass'] = exact_mass

                print(f"   ✅ Merged into single entry:")
                print(f"      Mass: {old_mass:.6f} → {exact_mass:.6f} (exact from formula)")
                print(f"      Assignments: {base_frag['assignments']}")

                mass_fixed_count += 1
            except Exception as e:
                print(f"   ⚠️ Could not calculate exact mass: {e}")
                print(f"      Keeping mass: {base_frag['mass']:.6f}")

            # Update notes
            base_frag['notes'] = f"Cleaned and recalculated on {datetime.now().strftime('%Y-%m-%d')}"
            cleaned_fragments.append(base_frag)

        else:
            # Single entry - just recalculate mass
            assignment, frag = frag_list[0]
            frag_copy = frag.copy()

            try:
                exact_mass = calculate_mass_from_assignment(assignment)
                old_mass = frag_copy['mass']

                if abs(old_mass - exact_mass) > 0.001:  # More than 1 mDa difference
                    print(f"\n🔧 Mass fix: {assignment}")
                    print(f"   {old_mass:.6f} → {exact_mass:.6f} Da (Δ = {exact_mass - old_mass:.6f})")
                    frag_copy['mass'] = exact_mass
                    frag_copy['notes'] = f"Mass recalculated on {datetime.now().strftime('%Y-%m-%d')}"
                    mass_fixed_count += 1
                else:
                    # Mass is already correct
                    pass

            except Exception as e:
                print(f"\n⚠️ Could not calculate exact mass for {assignment}: {e}")

            cleaned_fragments.append(frag_copy)

    # Sort by mass
    cleaned_fragments.sort(key=lambda x: (x['polarity'], x['mass']))

    # Statistics
    final_count = len(cleaned_fragments)
    print(f"\n" + "=" * 60)
    print(f"📊 Cleanup Summary:")
    print(f"   Original fragments: {original_count}")
    print(f"   Final fragments: {final_count}")
    print(f"   Duplicates merged: {duplicate_count}")
    print(f"   Masses recalculated: {mass_fixed_count}")
    print(f"   Net reduction: {original_count - final_count} fragments")

    if not dry_run:
        # Create backup
        backup_dir = Path(db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"before_cleanup_{timestamp}.json"

        shutil.copy2(db_path, backup_path)
        print(f"\n📦 Backup created: {backup_path}")

        # Update database
        db['fragments'] = cleaned_fragments
        db['metadata']['total_fragments'] = final_count
        db['metadata']['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db['metadata']['cleanup_date'] = datetime.now().strftime("%Y-%m-%d")

        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2)

        print(f"💾 Database saved: {db_path}")
        print(f"\n✅ Cleanup complete!")
    else:
        print(f"\n⚠️ DRY RUN - No changes made")
        print(f"   Run with --apply to apply changes")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python cleanup_fragment_database.py <database.json> [--apply]")
        print("\nOptions:")
        print("  --apply    Apply changes to database (default: dry run)")
        sys.exit(1)

    db_path = sys.argv[1]
    apply_changes = "--apply" in sys.argv

    if not Path(db_path).exists():
        print(f"❌ Error: Database not found: {db_path}")
        sys.exit(1)

    cleanup_fragment_database(db_path, dry_run=not apply_changes)


if __name__ == "__main__":
    main()
