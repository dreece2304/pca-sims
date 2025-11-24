#!/usr/bin/env python3
"""
Fragment Database Management Tool
Consolidated utility for database validation, cleanup, backup, and statistics

Usage:
    python manage_fragment_database.py validate [--db PATH]
    python manage_fragment_database.py cleanup [--db PATH] [--live]
    python manage_fragment_database.py backup [--db PATH]
    python manage_fragment_database.py stats [--db PATH]
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from core.fragment_mass_calculator import calculate_mass_from_assignment


DEFAULT_DB_PATH = "data/FragmentDatabase/alucone_fragments_complete.json"


def get_database_path(args_db_path: str = None) -> Path:
    """Resolve database path"""
    if args_db_path:
        return Path(args_db_path)

    # Try to find from script location
    script_dir = Path(__file__).parent.parent.parent
    db_path = script_dir / DEFAULT_DB_PATH

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    return db_path


def create_backup(db_path: Path, prefix: str = "backup") -> Path:
    """Create timestamped backup of database"""
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{prefix}_{timestamp}.json"

    shutil.copy2(db_path, backup_path)
    return backup_path


def load_database(db_path: Path) -> dict:
    """Load database JSON"""
    with open(db_path, 'r') as f:
        return json.load(f)


def save_database(db_path: Path, db: dict):
    """Save database JSON with pretty formatting"""
    with open(db_path, 'w') as f:
        json.dump(db, f, indent=2)


# ============================================================================
# VALIDATE command
# ============================================================================

def cmd_validate(args):
    """Validate database integrity"""
    db_path = get_database_path(args.db)
    print("🔍 Fragment Database Validation")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    db = load_database(db_path)
    fragments = db.get('fragments', [])
    metadata = db.get('metadata', {})

    print("📊 Metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    print()

    # Validation checks
    issues = []

    # Check 1: Missing required fields
    print("CHECK 1: Required fields")
    print("-" * 70)
    required_fields = ['mass', 'polarity', 'assignments', 'formulas']
    fragments_with_missing = 0

    for i, frag in enumerate(fragments):
        missing = [field for field in required_fields if field not in frag]
        if missing:
            fragments_with_missing += 1
            if fragments_with_missing <= 5:  # Only show first 5
                print(f"  Fragment #{i}: Missing {missing}")
                issues.append(f"Fragment #{i} missing: {missing}")

    if fragments_with_missing == 0:
        print("  ✅ All fragments have required fields")
    else:
        print(f"  ⚠️  {fragments_with_missing} fragments missing required fields")
    print()

    # Check 2: Corrupted entries
    print("CHECK 2: Corrupted entries")
    print("-" * 70)
    corrupted = []

    for i, frag in enumerate(fragments):
        polarity = frag.get('polarity')
        mass = frag.get('mass', 0)

        if polarity == 'unknown' or polarity is None:
            corrupted.append((i, 'unknown polarity', frag))
        elif mass == 0 or mass is None:
            corrupted.append((i, 'zero mass', frag))

    if not corrupted:
        print("  ✅ No corrupted entries found")
    else:
        print(f"  ⚠️  {len(corrupted)} corrupted entries:")
        for idx, reason, frag in corrupted[:5]:
            assignments = frag.get('assignments', ['?'])
            print(f"    Fragment #{idx}: {reason} - {assignments}")
        if len(corrupted) > 5:
            print(f"    ... and {len(corrupted) - 5} more")
        issues.extend([f"Fragment #{idx}: {reason}" for idx, reason, _ in corrupted])
    print()

    # Check 3: Formula duplicates
    print("CHECK 3: Formula duplicates")
    print("-" * 70)
    formula_groups = defaultdict(list)

    for i, frag in enumerate(fragments):
        polarity = frag.get('polarity')
        formulas = frag.get('formulas', [])

        for formula in formulas:
            if formula:
                key = (formula.replace('_', ''), polarity)
                formula_groups[key].append((i, frag))
                break

    duplicates = {k: v for k, v in formula_groups.items() if len(v) > 1}

    if not duplicates:
        print("  ✅ No formula duplicates found")
    else:
        print(f"  ⚠️  {len(duplicates)} formulas with multiple entries:")
        for (formula, polarity), frag_list in list(duplicates.items())[:5]:
            print(f"    {formula} ({polarity}): {len(frag_list)} entries")
            for idx, frag in frag_list:
                mass = frag.get('mass', 0)
                print(f"      #{idx} m/z {mass:.6f}")
        if len(duplicates) > 5:
            print(f"    ... and {len(duplicates) - 5} more")
        issues.append(f"{len(duplicates)} formulas have duplicates")
    print()

    # Check 4: Mass collisions (isobars - valid)
    print("CHECK 4: Mass collisions (isobars)")
    print("-" * 70)
    mass_groups = defaultdict(list)

    for i, frag in enumerate(fragments):
        mass = frag.get('mass', 0)
        polarity = frag.get('polarity')

        if mass > 0:
            # Group by mass (±0.01 Da tolerance)
            mass_key = (round(mass, 2), polarity)
            mass_groups[mass_key].append((i, frag))

    collisions = {k: v for k, v in mass_groups.items() if len(v) > 1}

    if not collisions:
        print("  ℹ️  No mass collisions (no isobars)")
    else:
        print(f"  ℹ️  {len(collisions)} mass collisions (valid isobars):")
        for (mass, polarity), frag_list in list(collisions.items())[:5]:
            print(f"    m/z ~{mass:.2f} ({polarity}): {len(frag_list)} fragments")
            for idx, frag in frag_list:
                formulas = frag.get('formulas', ['?'])
                exact_mass = frag.get('mass', 0)
                print(f"      #{idx} {formulas[0]} ({exact_mass:.6f} Da)")
        if len(collisions) > 5:
            print(f"    ... and {len(collisions) - 5} more")
    print()

    # Check 5: Mass accuracy (formula vs. database)
    print("CHECK 5: Mass accuracy")
    print("-" * 70)
    mass_errors = []

    for i, frag in enumerate(fragments):
        assignments = frag.get('assignments', [])
        db_mass = frag.get('mass', 0)

        if assignments and db_mass > 0:
            try:
                calc_mass = calculate_mass_from_assignment(assignments[0])
                error = abs(db_mass - calc_mass)

                if error > 0.001:  # > 1 mDa
                    mass_errors.append((i, assignments[0], db_mass, calc_mass, error))
            except:
                pass

    if not mass_errors:
        print("  ✅ All masses accurate (within 1 mDa)")
    else:
        print(f"  ⚠️  {len(mass_errors)} fragments with mass errors > 1 mDa:")
        for idx, assignment, db_mass, calc_mass, error in mass_errors[:5]:
            print(f"    #{idx} {assignment}: {db_mass:.6f} Da (should be {calc_mass:.6f}, Δ={error*1000:.2f} mDa)")
        if len(mass_errors) > 5:
            print(f"    ... and {len(mass_errors) - 5} more")
        issues.append(f"{len(mass_errors)} fragments have mass errors")
    print()

    # Summary
    print("=" * 70)
    if not issues:
        print("✅ DATABASE VALID - No issues found")
        return 0
    else:
        print(f"⚠️  DATABASE HAS ISSUES - {len(issues)} problems detected:")
        for issue in issues[:10]:
            print(f"   • {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
        print()
        print("Run 'cleanup' command to fix these issues")
        return 1


# ============================================================================
# CLEANUP command
# ============================================================================

def cmd_cleanup(args):
    """Clean up database by merging duplicates and fixing masses"""
    db_path = get_database_path(args.db)
    dry_run = not args.live

    print("🧹 Fragment Database Cleanup")
    print("=" * 70)
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify database)'}")
    print()

    db = load_database(db_path)
    original_count = len(db['fragments'])
    print(f"Original fragment count: {original_count}")
    print()

    # STEP 1: Remove corrupted entries
    print("STEP 1: Remove corrupted entries")
    print("-" * 70)

    valid_frags = []
    corrupted_count = 0

    for frag in db['fragments']:
        polarity = frag.get('polarity')
        mass = frag.get('mass', 0)

        if polarity == 'unknown' or polarity is None or mass == 0:
            corrupted_count += 1
        else:
            valid_frags.append(frag)

    print(f"  Removed {corrupted_count} corrupted entries")
    print(f"  Keeping {len(valid_frags)} valid entries")
    print()

    # STEP 2: Merge formula duplicates
    print("STEP 2: Merge formula duplicates")
    print("-" * 70)

    formula_groups = defaultdict(list)
    for frag in valid_frags:
        polarity = frag.get('polarity')
        formulas = frag.get('formulas', [])

        for formula in formulas:
            if formula:
                key = (formula.replace('_', ''), polarity)
                formula_groups[key].append(frag)
                break

    cleaned_fragments = []
    duplicates_merged = 0

    for (formula, polarity), frag_list in formula_groups.items():
        if len(frag_list) > 1:
            # Merge duplicates
            duplicates_merged += len(frag_list) - 1

            print(f"  Merging {len(frag_list)} entries for {formula} ({polarity})")

            # Use first as base, collect all unique data
            base_frag = frag_list[0].copy()

            all_assignments = []
            all_formulas = []
            all_families = []

            for frag in frag_list:
                all_assignments.extend(frag.get('assignments', []))
                all_formulas.extend(frag.get('formulas', []))
                all_families.extend(frag.get('families', []))

            base_frag['assignments'] = sorted(list(set(all_assignments)))
            base_frag['formulas'] = sorted(list(set(all_formulas)))
            base_frag['families'] = sorted(list(set(all_families)))

            # Recalculate mass from first assignment
            try:
                exact_mass = calculate_mass_from_assignment(base_frag['assignments'][0])
                base_frag['mass'] = exact_mass
                base_frag['notes'] = f"Merged and recalculated on {datetime.now().strftime('%Y-%m-%d')}"
            except:
                pass

            cleaned_fragments.append(base_frag)
        else:
            # Single entry - keep as-is
            cleaned_fragments.append(frag_list[0])

    print(f"  Merged {duplicates_merged} duplicate entries")
    print()

    # STEP 3: Recalculate masses
    print("STEP 3: Recalculate masses from formulas")
    print("-" * 70)

    mass_fixed_count = 0
    for frag in cleaned_fragments:
        assignments = frag.get('assignments', [])
        if assignments:
            try:
                exact_mass = calculate_mass_from_assignment(assignments[0])
                old_mass = frag.get('mass', 0)

                if abs(old_mass - exact_mass) > 0.001:
                    print(f"  Fixed: {assignments[0]}: {old_mass:.6f} → {exact_mass:.6f} Da")
                    frag['mass'] = exact_mass
                    frag['notes'] = f"Mass recalculated on {datetime.now().strftime('%Y-%m-%d')}"
                    mass_fixed_count += 1
            except:
                pass

    print(f"  Recalculated {mass_fixed_count} masses")
    print()

    # Sort by polarity and mass
    cleaned_fragments.sort(key=lambda x: (x.get('polarity', ''), x.get('mass', 0)))

    final_count = len(cleaned_fragments)

    # Summary
    print("=" * 70)
    print("📊 Cleanup Summary:")
    print(f"   Original fragments: {original_count}")
    print(f"   Corrupted removed: {corrupted_count}")
    print(f"   Duplicates merged: {duplicates_merged}")
    print(f"   Masses fixed: {mass_fixed_count}")
    print(f"   Final fragments: {final_count}")
    print(f"   Net reduction: {original_count - final_count} fragments")
    print()

    if not dry_run:
        # Create backup
        backup_path = create_backup(db_path, "before_cleanup")
        print(f"📦 Backup created: {backup_path}")

        # Update database
        db['fragments'] = cleaned_fragments
        db['metadata']['total_fragments'] = final_count
        db['metadata']['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db['metadata']['comprehensive_cleanup_date'] = datetime.now().strftime("%Y-%m-%d")

        save_database(db_path, db)
        print(f"✅ Database updated: {db_path}")
    else:
        print("🔒 DRY RUN - No changes made. Use --live to apply changes.")

    return 0


# ============================================================================
# BACKUP command
# ============================================================================

def cmd_backup(args):
    """Create manual backup of database"""
    db_path = get_database_path(args.db)

    print("📦 Creating Database Backup")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    backup_path = create_backup(db_path, "manual_backup")

    print(f"✅ Backup created: {backup_path}")
    print(f"   Size: {backup_path.stat().st_size / 1024:.1f} KB")

    return 0


# ============================================================================
# STATS command
# ============================================================================

def cmd_stats(args):
    """Show database statistics"""
    db_path = get_database_path(args.db)

    print("📊 Fragment Database Statistics")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    db = load_database(db_path)
    fragments = db.get('fragments', [])
    metadata = db.get('metadata', {})

    # Basic stats
    print("Metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    print()

    # Count by polarity
    polarity_counts = defaultdict(int)
    for frag in fragments:
        polarity = frag.get('polarity', 'unknown')
        polarity_counts[polarity] += 1

    print("Fragments by Polarity:")
    for polarity, count in sorted(polarity_counts.items()):
        print(f"   {polarity}: {count}")
    print()

    # Count by family
    family_counts = defaultdict(int)
    for frag in fragments:
        families = frag.get('families', [])
        for family in families:
            if family:
                family_counts[family] += 1

    print("Fragments by Chemical Family:")
    for family, count in sorted(family_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"   {family}: {count}")
    if len(family_counts) > 10:
        print(f"   ... and {len(family_counts) - 10} more families")
    print()

    # Confidence levels
    confidence_counts = defaultdict(int)
    for frag in fragments:
        confidence = frag.get('confidence', 'Unknown')
        confidence_counts[confidence] += 1

    print("Fragments by Confidence:")
    for confidence, count in sorted(confidence_counts.items()):
        print(f"   {confidence}: {count}")
    print()

    # Mass range
    masses = [frag.get('mass', 0) for frag in fragments if frag.get('mass', 0) > 0]
    if masses:
        print("Mass Range:")
        print(f"   Minimum: {min(masses):.4f} Da")
        print(f"   Maximum: {max(masses):.4f} Da")
        print(f"   Mean: {sum(masses) / len(masses):.4f} Da")

    return 0


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fragment Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Validate database:
    python manage_fragment_database.py validate

  Cleanup (dry run):
    python manage_fragment_database.py cleanup

  Cleanup (apply changes):
    python manage_fragment_database.py cleanup --live

  Create backup:
    python manage_fragment_database.py backup

  Show statistics:
    python manage_fragment_database.py stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate database integrity')
    validate_parser.add_argument('--db', help='Path to database file')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up database')
    cleanup_parser.add_argument('--db', help='Path to database file')
    cleanup_parser.add_argument('--live', action='store_true', help='Apply changes (default is dry run)')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create manual backup')
    backup_parser.add_argument('--db', help='Path to database file')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--db', help='Path to database file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    commands = {
        'validate': cmd_validate,
        'cleanup': cmd_cleanup,
        'backup': cmd_backup,
        'stats': cmd_stats,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
