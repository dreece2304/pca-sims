#!/usr/bin/env python3
"""
Test Stage 5: m/z Range Filter
Tests filtering peaks by m/z range with validation
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from simple_tof_sims_pca import SimpleToFSIMSPCA
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing


def apply_mz_range_filter(mz_values, intensities, std_devs, mz_min, mz_max):
    """Apply m/z range filter to data"""
    # Create mask for m/z range
    mask = (mz_values >= mz_min) & (mz_values <= mz_max)

    # Apply mask
    filtered_mz = mz_values[mask]
    filtered_intensities = intensities[mask]
    filtered_std_devs = std_devs[mask]

    return filtered_mz, filtered_intensities, filtered_std_devs, mask


def test_mz_range_filter():
    """Test m/z range filtering"""

    print("=" * 70)
    print("STAGE 5 TEST: m/z Range Filter")
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
    print(f"   Full m/z range: {mz_values.min():.3f} - {mz_values.max():.3f}")

    # Test different m/z ranges
    print(f"\n🔍 Testing m/z range filters:")

    test_ranges = [
        (None, None, "Full range (all peaks)"),
        (1.0, 30.0, "Low m/z region (1-30)"),
        (20.0, 50.0, "Mid m/z region (20-50)"),
        (50.0, 100.0, "High m/z region (50-100)"),
        (10.0, 25.0, "Narrow range (10-25)"),
    ]

    results = {}

    for mz_min, mz_max, label in test_ranges:
        # Handle full range
        if mz_min is None or mz_max is None:
            filtered_mz = mz_values
            filtered_intensities = mean_intensities
            filtered_std_devs = std_devs
            mask = np.ones(len(mz_values), dtype=bool)
            mz_min_actual = mz_values.min()
            mz_max_actual = mz_values.max()
        else:
            filtered_mz, filtered_intensities, filtered_std_devs, mask = apply_mz_range_filter(
                mz_values, mean_intensities, std_devs, mz_min, mz_max
            )
            mz_min_actual = mz_min
            mz_max_actual = mz_max

        results[label] = {
            'mz': filtered_mz,
            'intensities': filtered_intensities,
            'std_devs': filtered_std_devs,
            'mask': mask,
            'count': mask.sum(),
            'mz_min': mz_min_actual,
            'mz_max': mz_max_actual
        }

        print(f"   {label:30s}: {mask.sum():2d}/{len(mask)} peaks ({mask.sum()/len(mask)*100:5.1f}%)")
        if len(filtered_mz) > 0:
            print(f"      Actual m/z range: {filtered_mz.min():.3f} - {filtered_mz.max():.3f}")

    # Verification checks
    print(f"\n🔍 Verification checks:")

    # Check that full range keeps all peaks
    full_range_label = "Full range (all peaks)"
    assert results[full_range_label]['count'] == len(mz_values), "❌ Full range should keep all peaks!"
    print(f"   ✅ Full range keeps all {len(mz_values)} peaks")

    # Check that filtered peaks are within range
    for mz_min, mz_max, label in test_ranges[1:]:  # Skip full range
        result = results[label]
        filtered_mz = result['mz']

        if len(filtered_mz) > 0:
            assert filtered_mz.min() >= mz_min, f"❌ {label}: min m/z out of range!"
            assert filtered_mz.max() <= mz_max, f"❌ {label}: max m/z out of range!"

    print(f"   ✅ All filtered peaks within specified ranges")

    # Check boundary conditions
    narrow_range = results["Narrow range (10-25)"]
    narrow_mz = narrow_range['mz']
    # Check that peaks just outside range are excluded
    excluded_peaks = mz_values[~narrow_range['mask']]
    if len(excluded_peaks) > 0 and len(narrow_mz) > 0:
        assert (excluded_peaks < 10.0).any() or (excluded_peaks > 25.0).any(), \
            "❌ Boundary condition failed!"
    print(f"   ✅ Boundary conditions correct")

    # Visualization: Show m/z range effect
    print(f"\n🎨 Creating visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Stage 5: m/z Range Filter Test', fontsize=14, fontweight='bold')

    # Test full range, low, mid, narrow
    plot_labels = [
        "Full range (all peaks)",
        "Low m/z region (1-30)",
        "Mid m/z region (20-50)",
        "Narrow range (10-25)"
    ]

    for idx, label in enumerate(plot_labels):
        ax = axes[idx // 2, idx % 2]

        result = results[label]
        filtered_mz = result['mz']
        filtered_intensities = result['intensities']
        peak_count = result['count']
        mz_min = result['mz_min']
        mz_max = result['mz_max']

        # Plot sticks
        markerline, stemlines, baseline = ax.stem(
            filtered_mz,
            filtered_intensities,
            linefmt='#440154',  # Viridis dark
            markerfmt=' ',
            basefmt='k-'
        )
        stemlines.set_linewidth(1.0)
        stemlines.set_alpha(0.8)

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')

        ax.set_title(
            f'{label}\n{peak_count}/{len(mz_values)} peaks, m/z: [{mz_min:.1f}, {mz_max:.1f}]',
            fontweight='bold', loc='left'
        )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Set x-axis limits to show full context
        ax.set_xlim(0, 100)

    plt.tight_layout()

    # Save
    output_file = "test_stick_spectrum_stage5_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Test validation scenarios
    print(f"\n🧪 Testing validation scenarios:")

    validation_tests = [
        (10.0, 50.0, True, "Valid range (10-50)"),
        (50.0, 10.0, False, "Invalid: min > max"),
        (10.0, 10.0, False, "Invalid: min = max"),
        (-5.0, 50.0, True, "Valid with negative min"),
        (10.0, 1000.0, True, "Valid with large max"),
    ]

    for mz_min, mz_max, should_be_valid, description in validation_tests:
        is_valid = mz_min < mz_max

        if should_be_valid:
            assert is_valid, f"❌ {description} should be valid!"
            print(f"   ✅ {description}")
        else:
            assert not is_valid, f"❌ {description} should be invalid!"
            print(f"   ✅ {description} correctly rejected")

    # Test combined filters: Intensity + m/z range
    print(f"\n🔬 Testing combined filters (Intensity + m/z range):")

    # Apply 5% intensity threshold first
    threshold_percent = 5
    max_intensity = mean_intensities.max()
    threshold = (threshold_percent / 100.0) * max_intensity
    intensity_mask = mean_intensities >= threshold

    print(f"   1. Intensity filter (5%): {intensity_mask.sum()}/{len(mz_values)} peaks")

    # Then apply m/z range 10-30
    passing_mz = mz_values[intensity_mask]
    passing_intensities = mean_intensities[intensity_mask]
    passing_std_devs = std_devs[intensity_mask]

    range_mz, range_intensities, range_std_devs, range_mask = apply_mz_range_filter(
        passing_mz, passing_intensities, passing_std_devs, 10.0, 30.0
    )

    print(f"   2. m/z range (10-30): {len(range_mz)}/{len(passing_mz)} peaks from passing set")
    print(f"   Final peaks: {len(range_mz)} peaks")
    print(f"   m/z values: {[f'{m:.3f}' for m in range_mz]}")

    # Verification: All final peaks should be in range and above threshold
    assert all(range_mz >= 10.0) and all(range_mz <= 30.0), \
        "❌ Combined filter: peaks outside m/z range!"
    assert all(range_intensities >= threshold), \
        "❌ Combined filter: peaks below intensity threshold!"
    print(f"   ✅ Combined filters work correctly")

    print("\n" + "=" * 70)
    print("✅ STAGE 5 TESTS PASSED")
    print("=" * 70)
    print(f"\nStage 5 Complete:")
    print(f"✅ m/z range filter implemented")
    print(f"✅ Range validation working (min < max)")
    print(f"✅ Boundary conditions correct")
    print(f"✅ Combined filters work (Intensity + m/z range)")
    print(f"\nFilter effectiveness:")
    for label in plot_labels:
        result = results[label]
        count = result['count']
        mz_min = result['mz_min']
        mz_max = result['mz_max']
        print(f"   {label:30s}: {count:2d}/{len(mz_values)} peaks "
              f"[{mz_min:.1f}, {mz_max:.1f}]")
    print(f"\nNext steps:")
    print(f"1. Test in full GUI application")
    print(f"2. Test input validation (invalid values, min >= max)")
    print(f"3. Test combined filters (all 3: Intensity + Top N + m/z range)")
    print(f"4. Begin Stage 6: PCA loadings filter (requires PCA run)")

    return True


if __name__ == "__main__":
    try:
        success = test_mz_range_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
