#!/usr/bin/env python3
"""
Test Stage 4: Top N Peaks Filter
Tests filtering to show only highest intensity peaks
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


def apply_topn_filter(mz_values, intensities, std_devs, n_peaks):
    """Apply Top N peaks filter to data"""
    if n_peaks is None or n_peaks >= len(intensities):
        # Keep all peaks
        return mz_values, intensities, std_devs, np.ones(len(mz_values), dtype=bool)

    # Sort by intensity (descending)
    sorted_indices = np.argsort(intensities)[::-1]

    # Keep only top N
    keep_indices = sorted_indices[:n_peaks]
    keep_indices = np.sort(keep_indices)  # Re-sort by original order (m/z)

    # Create mask
    mask = np.zeros(len(mz_values), dtype=bool)
    mask[keep_indices] = True

    # Apply mask
    filtered_mz = mz_values[mask]
    filtered_intensities = intensities[mask]
    filtered_std_devs = std_devs[mask]

    return filtered_mz, filtered_intensities, filtered_std_devs, mask


def test_topn_filter():
    """Test Top N peaks filtering"""

    print("=" * 70)
    print("STAGE 4 TEST: Top N Peaks Filter")
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
    print(f"   Intensity range: {mean_intensities.min():.3e} - {mean_intensities.max():.3e}")

    # Test different Top N values
    print(f"\n🔍 Testing Top N filters:")

    test_n_values = [None, 20, 50, 100, 200]  # None = All
    results = {}

    for n_peaks in test_n_values:
        filtered_mz, filtered_intensities, filtered_std_devs, mask = apply_topn_filter(
            mz_values, mean_intensities, std_devs, n_peaks
        )

        label = "All" if n_peaks is None else str(n_peaks)
        results[label] = {
            'mz': filtered_mz,
            'intensities': filtered_intensities,
            'std_devs': filtered_std_devs,
            'mask': mask,
            'count': mask.sum()
        }

        print(f"   Top {label:3s}: {mask.sum():2d}/{len(mask)} peaks "
              f"({mask.sum()/len(mask)*100:5.1f}%)")

        # Show intensity range of kept peaks
        if len(filtered_intensities) > 0:
            print(f"         Intensity range: {filtered_intensities.min():.3e} - "
                  f"{filtered_intensities.max():.3e}")

    # Verification checks
    print(f"\n🔍 Verification checks:")

    # Check that "All" keeps all peaks
    assert results["All"]['count'] == len(mz_values), "❌ 'All' should keep all peaks!"
    print(f"   ✅ 'All' option keeps all {len(mz_values)} peaks")

    # Check that Top N keeps exactly N peaks (or fewer if N > total)
    for n_peaks in [20, 50, 100, 200]:
        label = str(n_peaks)
        expected = min(n_peaks, len(mz_values))
        actual = results[label]['count']
        assert actual == expected, f"❌ Top {n_peaks} should keep {expected} peaks, got {actual}!"
    print(f"   ✅ Top N filters keep correct number of peaks")

    # Check that kept peaks are highest intensity
    for n_peaks in [20, 50]:
        label = str(n_peaks)
        kept_intensities = results[label]['intensities']
        all_intensities = mean_intensities

        # Sort all intensities and check kept ones match top N
        top_n_intensities = np.sort(all_intensities)[::-1][:n_peaks]
        kept_sorted = np.sort(kept_intensities)[::-1]

        assert np.allclose(kept_sorted, top_n_intensities), \
            f"❌ Top {n_peaks} doesn't match highest intensity peaks!"

    print(f"   ✅ Filtering correctly selects highest intensity peaks")

    # Visualization: Show Top N effect
    print(f"\n🎨 Creating visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Stage 4: Top N Peaks Filter Test', fontsize=14, fontweight='bold')

    # Test All, 20, 50, 100
    plot_n_values = ["All", "20", "50", "100"]

    for idx, label in enumerate(plot_n_values):
        ax = axes[idx // 2, idx % 2]

        result = results[label]
        filtered_mz = result['mz']
        filtered_intensities = result['intensities']
        peak_count = result['count']

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
            f'Top {label} peaks\n{peak_count}/{len(mz_values)} peaks visible',
            fontweight='bold', loc='left'
        )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    plt.tight_layout()

    # Save
    output_file = "test_stick_spectrum_stage4_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Test combined filters: Intensity threshold + Top N
    print(f"\n🔬 Testing combined filters (Intensity + Top N):")

    # Apply 5% intensity threshold first
    threshold_percent = 5
    max_intensity = mean_intensities.max()
    threshold = (threshold_percent / 100.0) * max_intensity
    intensity_mask = mean_intensities >= threshold

    print(f"   1. Intensity filter (5%): {intensity_mask.sum()}/{len(mz_values)} peaks")

    # Then apply Top 5 from those
    passing_mz = mz_values[intensity_mask]
    passing_intensities = mean_intensities[intensity_mask]
    passing_std_devs = std_devs[intensity_mask]

    top5_mz, top5_intensities, top5_std_devs, _ = apply_topn_filter(
        passing_mz, passing_intensities, passing_std_devs, 5
    )

    print(f"   2. Top 5 from passing: {len(top5_mz)} peaks")
    print(f"   Final peaks: {list(top5_mz)}")

    # Verification: Final peaks should be top 5 by intensity
    expected_top5 = np.sort(passing_intensities)[::-1][:5]
    actual_top5 = np.sort(top5_intensities)[::-1]
    assert np.allclose(actual_top5, expected_top5), \
        "❌ Combined filter doesn't produce correct top 5!"
    print(f"   ✅ Combined filters work correctly")

    print("\n" + "=" * 70)
    print("✅ STAGE 4 TESTS PASSED")
    print("=" * 70)
    print(f"\nStage 4 Complete:")
    print(f"✅ Top N peaks filter implemented")
    print(f"✅ Correct peak selection verified (All, 20, 50, 100, 200)")
    print(f"✅ Highest intensity peaks correctly identified")
    print(f"✅ Combined filters work correctly (Intensity + Top N)")
    print(f"\nFilter effectiveness:")
    for label in ["All", "20", "50", "100", "200"]:
        count = results[label]['count']
        print(f"   Top {label:3s}: {count:2d}/{len(mz_values)} peaks "
              f"({count/len(mz_values)*100:5.1f}% retained)")
    print(f"\nNext steps:")
    print(f"1. Test in full GUI application")
    print(f"2. Test filter combinations (Intensity + Top N)")
    print(f"3. Test interaction with fragment labels")
    print(f"4. Begin Stage 5: m/z range filter")

    return True


if __name__ == "__main__":
    try:
        success = test_topn_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
