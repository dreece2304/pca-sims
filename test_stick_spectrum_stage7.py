#!/usr/bin/env python3
"""
Test Stage 7: Statistical and Assignment Filters
Tests filtering by statistical significance (mean > N×SD) and assignment status
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from simple_tof_sims_pca import SimpleToFSIMSPCA
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing


def load_fragment_database():
    """Load fragment database from JSON"""
    database_path = "data/FragmentDatabase/alucone_fragments_complete.json"
    with open(database_path, 'r') as f:
        return json.load(f)


def find_fragment_assignment(target_mass, database, tolerance_ppm=100.0, polarity='negative'):
    """Find fragment assignment for a given mass"""
    matches = []

    for fragment in database['fragments']:
        if fragment['polarity'] != polarity:
            continue

        # Calculate mass error in ppm
        mass_error_ppm = abs((fragment['mass'] - target_mass) / target_mass * 1e6)

        if mass_error_ppm <= tolerance_ppm:
            matches.append({
                'mass': fragment['mass'],
                'assignments': fragment['assignments'],
                'formulas': fragment['formulas'],
                'confidence': fragment.get('confidence', ''),
                'error_ppm': mass_error_ppm
            })

    # Sort by mass error
    matches.sort(key=lambda x: x['error_ppm'])

    return matches


def apply_statistical_filter(mz_values, intensities, std_devs, multiplier):
    """Apply statistical significance filter"""
    mask = intensities > (multiplier * std_devs)

    filtered_mz = mz_values[mask]
    filtered_intensities = intensities[mask]
    filtered_std_devs = std_devs[mask]

    return filtered_mz, filtered_intensities, filtered_std_devs, mask


def apply_assignment_filter(mz_values, intensities, std_devs, assignments, filter_type):
    """Apply assignment status filter"""
    mask = np.ones(len(mz_values), dtype=bool)

    if filter_type == "assigned":
        for i, assignment in enumerate(assignments):
            if assignment['assignment'] == "Unassigned":
                mask[i] = False
    elif filter_type == "unassigned":
        for i, assignment in enumerate(assignments):
            if assignment['assignment'] != "Unassigned":
                mask[i] = False
    # "all" keeps everything

    filtered_mz = mz_values[mask]
    filtered_intensities = intensities[mask]
    filtered_std_devs = std_devs[mask]

    return filtered_mz, filtered_intensities, filtered_std_devs, mask


def test_statistical_and_assignment_filters():
    """Test statistical significance and assignment filters"""

    print("=" * 70)
    print("STAGE 7 TEST: Statistical & Assignment Filters")
    print("=" * 70)

    # Test with negative ion data
    data_file = "data/NegativeIon/NegAllCompoundSearch.txt"

    print(f"\n📁 Loading data: {data_file}")

    # Load data
    pca = SimpleToFSIMSPCA(data_file)
    pca.load_data()

    # Test dose: SQ4
    test_dose = 4

    print(f"\n🎯 Testing dose selection: SQ{test_dose}")

    # Get data
    dose_mask = pca.sample_metadata['dose_id'] == test_dose
    dose_samples = pca.sample_metadata[dose_mask]
    sample_names = dose_samples['sample_name'].tolist()
    dose_data = pca.raw_data[sample_names]

    # Calculate statistics
    mean_intensities = dose_data.mean(axis=1).values
    std_devs = dose_data.std(axis=1).values
    mz_values = pca.raw_data.index.values

    print(f"   {len(mz_values)} m/z values (unfiltered)")

    # Load fragment database and create assignments
    print(f"\n📚 Loading fragment database...")
    database = load_fragment_database()

    fragment_assignments = []
    polarity = 'negative'

    for i, mz in enumerate(mz_values):
        matches = find_fragment_assignment(mz, database, tolerance_ppm=100.0, polarity=polarity)

        assignment_info = {
            'mz': mz,
            'mean_intensity': mean_intensities[i],
            'std_dev': std_devs[i],
            'cv_percent': (std_devs[i] / mean_intensities[i] * 100) if mean_intensities[i] > 0 else 0,
            'assignment': matches[0]['assignments'][0] if matches else "Unassigned",
            'formula': matches[0]['formulas'][0] if matches else "",
            'confidence': matches[0].get('confidence', '') if matches else "",
        }
        fragment_assignments.append(assignment_info)

    assigned_count = sum(1 for a in fragment_assignments if a['assignment'] != "Unassigned")
    unassigned_count = len(fragment_assignments) - assigned_count

    print(f"   Assigned: {assigned_count}/{len(mz_values)} peaks")
    print(f"   Unassigned: {unassigned_count}/{len(mz_values)} peaks")

    # Test statistical filters
    print(f"\n🔍 Testing statistical filters:")

    test_multipliers = [1, 2, 3]
    stat_results = {}

    for multiplier in test_multipliers:
        filtered_mz, filtered_intensities, filtered_std_devs, mask = apply_statistical_filter(
            mz_values, mean_intensities, std_devs, multiplier
        )

        stat_results[multiplier] = {
            'mz': filtered_mz,
            'intensities': filtered_intensities,
            'std_devs': filtered_std_devs,
            'mask': mask,
            'count': mask.sum()
        }

        print(f"   Mean > {multiplier}×SD: {mask.sum():2d}/{len(mask)} peaks ({mask.sum()/len(mask)*100:5.1f}%)")

    # Test assignment filters
    print(f"\n🔍 Testing assignment filters:")

    assignment_results = {}
    test_filters = ["all", "assigned", "unassigned"]

    for filter_type in test_filters:
        filtered_mz, filtered_intensities, filtered_std_devs, mask = apply_assignment_filter(
            mz_values, mean_intensities, std_devs, fragment_assignments, filter_type
        )

        assignment_results[filter_type] = {
            'mz': filtered_mz,
            'intensities': filtered_intensities,
            'std_devs': filtered_std_devs,
            'mask': mask,
            'count': mask.sum()
        }

        print(f"   {filter_type.capitalize():12s}: {mask.sum():2d}/{len(mask)} peaks ({mask.sum()/len(mask)*100:5.1f}%)")

    # Verification checks
    print(f"\n🔍 Verification checks:")

    # Statistical filter checks
    # Higher multipliers should filter more peaks
    for i in range(len(test_multipliers) - 1):
        current = test_multipliers[i]
        next_mult = test_multipliers[i + 1]
        assert stat_results[current]['count'] >= stat_results[next_mult]['count'], \
            f"❌ {current}×SD should have >= peaks than {next_mult}×SD!"
    print(f"   ✅ Statistical filter: higher thresholds remove more peaks")

    # Verify filtered peaks actually meet criterion
    multiplier = 3
    result = stat_results[multiplier]
    for mz in result['mz']:
        idx = np.argmin(np.abs(mz_values - mz))
        mean_val = mean_intensities[idx]
        std_val = std_devs[idx]
        assert mean_val > multiplier * std_val, \
            f"❌ Peak at m/z {mz:.3f} doesn't meet mean > {multiplier}×SD criterion!"
    print(f"   ✅ Statistical filter: peaks meet mean > 3×SD criterion")

    # Assignment filter checks
    assert assignment_results['all']['count'] == len(mz_values), \
        "❌ 'All' filter should keep all peaks!"
    print(f"   ✅ Assignment filter: 'All' keeps all peaks")

    assert assignment_results['assigned']['count'] == assigned_count, \
        f"❌ 'Assigned' filter should keep {assigned_count} peaks!"
    print(f"   ✅ Assignment filter: 'Assigned Only' keeps correct count")

    assert assignment_results['unassigned']['count'] == unassigned_count, \
        f"❌ 'Unassigned' filter should keep {unassigned_count} peaks!"
    print(f"   ✅ Assignment filter: 'Unassigned Only' keeps correct count")

    # Visualization: Statistical filters
    print(f"\n🎨 Creating visualization...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Stage 7: Statistical & Assignment Filters Test', fontsize=14, fontweight='bold')

    # Row 1: Statistical filters (1×SD, 2×SD, 3×SD)
    for idx, multiplier in enumerate([1, 2, 3]):
        ax = axes[0, idx]

        result = stat_results[multiplier]
        filtered_mz = result['mz']
        filtered_intensities = result['intensities']
        peak_count = result['count']

        # Plot sticks (only if data exists)
        if len(filtered_mz) > 0:
            markerline, stemlines, baseline = ax.stem(
                filtered_mz,
                filtered_intensities,
                linefmt='#440154',  # Viridis dark
                markerfmt=' ',
                basefmt='k-'
            )
            stemlines.set_linewidth(1.0)
            stemlines.set_alpha(0.8)
        else:
            # Empty plot with message
            ax.text(0.5, 0.5, 'No peaks match filter',
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')

        ax.set_title(
            f'Mean > {multiplier}×SD\n{peak_count}/{len(mz_values)} peaks visible',
            fontweight='bold', loc='left'
        )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Row 2: Assignment filters (All, Assigned, Unassigned)
    for idx, (filter_type, label) in enumerate([("all", "All"), ("assigned", "Assigned Only"), ("unassigned", "Unassigned Only")]):
        ax = axes[1, idx]

        result = assignment_results[filter_type]
        filtered_mz = result['mz']
        filtered_intensities = result['intensities']
        peak_count = result['count']

        # Plot sticks (only if data exists)
        if len(filtered_mz) > 0:
            markerline, stemlines, baseline = ax.stem(
                filtered_mz,
                filtered_intensities,
                linefmt='#440154',  # Viridis dark
                markerfmt=' ',
                basefmt='k-'
            )
            stemlines.set_linewidth(1.0)
            stemlines.set_alpha(0.8)
        else:
            # Empty plot with message
            ax.text(0.5, 0.5, 'No peaks match filter',
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')

        ax.set_title(
            f'{label}\n{peak_count}/{len(mz_values)} peaks visible',
            fontweight='bold', loc='left'
        )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    plt.tight_layout()

    # Save
    output_file = "test_stick_spectrum_stage7_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Test combined filters: Statistical + Assignment
    print(f"\n🔬 Testing combined filters (Mean > 3×SD + Assigned Only):")

    # Apply statistical filter first
    stat_mz, stat_intensities, stat_std_devs, stat_mask = apply_statistical_filter(
        mz_values, mean_intensities, std_devs, 3
    )

    print(f"   1. Statistical (mean > 3×SD): {len(stat_mz)}/{len(mz_values)} peaks")

    # Build assignments for passing peaks
    passing_assignments = [fragment_assignments[i] for i in range(len(mz_values)) if stat_mask[i]]

    # Apply assignment filter
    final_mz, final_intensities, final_std_devs, assignment_mask = apply_assignment_filter(
        stat_mz, stat_intensities, stat_std_devs, passing_assignments, "assigned"
    )

    print(f"   2. Assignment (assigned only): {len(final_mz)}/{len(stat_mz)} peaks")
    print(f"   Final peaks: {len(final_mz)} peaks")

    # Verification
    for mz in final_mz:
        idx = np.argmin(np.abs(mz_values - mz))
        mean_val = mean_intensities[idx]
        std_val = std_devs[idx]
        assert mean_val > 3 * std_val, "❌ Combined filter: peaks don't meet statistical criterion!"

        assignment = fragment_assignments[idx]
        assert assignment['assignment'] != "Unassigned", "❌ Combined filter: unassigned peak found!"

    print(f"   ✅ Combined filters work correctly")

    print("\n" + "=" * 70)
    print("✅ STAGE 7 TESTS PASSED")
    print("=" * 70)
    print(f"\nStage 7 Complete:")
    print(f"✅ Statistical filter implemented (mean > N×SD)")
    print(f"✅ Assignment filter implemented (All/Assigned/Unassigned)")
    print(f"✅ Filters work independently and in combination")
    print(f"\nFilter effectiveness:")
    print(f"  Statistical:")
    for multiplier in test_multipliers:
        count = stat_results[multiplier]['count']
        print(f"   Mean > {multiplier}×SD: {count:2d}/{len(mz_values)} peaks ({count/len(mz_values)*100:5.1f}% retained)")
    print(f"  Assignment:")
    for filter_type in test_filters:
        count = assignment_results[filter_type]['count']
        print(f"   {filter_type.capitalize():12s}: {count:2d}/{len(mz_values)} peaks ({count/len(mz_values)*100:5.1f}% retained)")
    print(f"\nNext steps:")
    print(f"1. Test in full GUI application")
    print(f"2. Test combined filters (all 6 filters together)")
    print(f"3. Begin Stage 8: Manual assignment dialog")

    return True


if __name__ == "__main__":
    try:
        success = test_statistical_and_assignment_filters()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
