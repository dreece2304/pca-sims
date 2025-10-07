#!/usr/bin/env python3
"""
Test Stage 6: PCA Loadings Filter
Tests filtering peaks by PCA loading values
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


def apply_pca_loadings_filter(mz_values, intensities, std_devs, loadings_df, threshold, pc='PC1'):
    """Apply PCA loadings filter to data"""
    # Create mask for PCA loadings
    mask = np.zeros(len(mz_values), dtype=bool)

    for i, mz in enumerate(mz_values):
        # Find loading for this m/z (exact match)
        if mz in loadings_df.index:
            loading = loadings_df.loc[mz, pc]
            abs_loading = abs(loading)

            # Keep if absolute loading exceeds threshold
            if abs_loading >= threshold:
                mask[i] = True

    # Apply mask
    filtered_mz = mz_values[mask]
    filtered_intensities = intensities[mask]
    filtered_std_devs = std_devs[mask]

    return filtered_mz, filtered_intensities, filtered_std_devs, mask


def test_pca_loadings_filter():
    """Test PCA loadings filtering"""

    print("=" * 70)
    print("STAGE 6 TEST: PCA Loadings Filter")
    print("=" * 70)

    # Test with negative ion data
    data_file = "data/NegativeIon/NegAllCompoundSearch.txt"

    print(f"\n📁 Loading data: {data_file}")

    # Load data
    pca = SimpleToFSIMSPCA(data_file)
    pca.load_data()

    print(f"✅ Data loaded: {pca.raw_data.shape}")

    # Run PCA first (required for loadings filter)
    print(f"\n🔬 Running PCA analysis...")
    pca.preprocess_data()
    pca.run_pca(n_components=5)

    print(f"✅ PCA complete")
    print(f"   PC1 variance explained: {pca.explained_variance_ratio[0]*100:.1f}%")

    # Get PCA loadings
    loadings_df = pca.get_loadings_dataframe()

    print(f"\n📊 PCA Loadings:")
    print(f"   Loadings shape: {loadings_df.shape}")
    print(f"   m/z range: {loadings_df.index.min():.3f} - {loadings_df.index.max():.3f}")
    print(f"   PC1 loading range: {loadings_df['PC1'].min():.6f} - {loadings_df['PC1'].max():.6f}")

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

    # Test different PCA loading thresholds
    print(f"\n🔍 Testing PCA loadings filters:")

    test_thresholds = [0.00, 0.05, 0.10, 0.20, 0.50]
    results = {}

    for threshold in test_thresholds:
        filtered_mz, filtered_intensities, filtered_std_devs, mask = apply_pca_loadings_filter(
            mz_values, mean_intensities, std_devs, loadings_df, threshold
        )

        results[threshold] = {
            'mz': filtered_mz,
            'intensities': filtered_intensities,
            'std_devs': filtered_std_devs,
            'mask': mask,
            'count': mask.sum()
        }

        print(f"   |PC1| >= {threshold:.2f}: {mask.sum():2d}/{len(mask)} peaks ({mask.sum()/len(mask)*100:5.1f}%)")

        # Show highest loading peaks
        if len(filtered_mz) > 0:
            # Get loadings for filtered peaks
            filtered_loadings = []
            for mz in filtered_mz:
                if mz in loadings_df.index:
                    filtered_loadings.append(abs(loadings_df.loc[mz, 'PC1']))

            if filtered_loadings:
                print(f"      Loading range: {min(filtered_loadings):.6f} - {max(filtered_loadings):.6f}")

    # Verification checks
    print(f"\n🔍 Verification checks:")

    # Check that 0.00 threshold keeps all peaks
    assert results[0.00]['count'] == len(mz_values), "❌ 0.00 threshold should keep all peaks!"
    print(f"   ✅ 0.00 threshold keeps all {len(mz_values)} peaks")

    # Check that higher thresholds remove more peaks
    for i in range(len(test_thresholds) - 1):
        current = test_thresholds[i]
        next_thresh = test_thresholds[i + 1]
        assert results[current]['count'] >= results[next_thresh]['count'], \
            f"❌ {current:.2f} threshold should have >= peaks than {next_thresh:.2f}!"
    print(f"   ✅ Higher thresholds progressively filter more peaks")

    # Check that filtered peaks actually have high loadings
    threshold = 0.10
    result = results[threshold]
    for mz in result['mz']:
        if mz in loadings_df.index:
            abs_loading = abs(loadings_df.loc[mz, 'PC1'])
            assert abs_loading >= threshold, \
                f"❌ Peak at m/z {mz:.3f} has |loading|={abs_loading:.6f} < {threshold:.2f}!"
    print(f"   ✅ Filtering correctly selects high-loading peaks")

    # Visualization: Show PCA loadings effect
    print(f"\n🎨 Creating visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Stage 6: PCA Loadings Filter Test', fontsize=14, fontweight='bold')

    # Test 0.00, 0.05, 0.10, 0.20
    plot_thresholds = [0.00, 0.05, 0.10, 0.20]

    for idx, threshold in enumerate(plot_thresholds):
        ax = axes[idx // 2, idx % 2]

        result = results[threshold]
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
            f'|PC1| >= {threshold:.2f}\n{peak_count}/{len(mz_values)} peaks visible',
            fontweight='bold', loc='left'
        )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    plt.tight_layout()

    # Save
    output_file = "test_stick_spectrum_stage6_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Show top peaks by loading
    print(f"\n📊 Top 10 peaks by |PC1| loading:")
    top_loadings = loadings_df['PC1'].abs().sort_values(ascending=False).head(10)
    for rank, (mz, abs_loading) in enumerate(top_loadings.items(), 1):
        original_loading = loadings_df.loc[mz, 'PC1']
        # Get intensity for this m/z
        idx = np.argmin(np.abs(mz_values - mz))
        intensity = mean_intensities[idx]

        print(f"   {rank:2d}. m/z {mz:.4f}: loading={original_loading:+.6f}, "
              f"|loading|={abs_loading:.6f}, intensity={intensity:.3e}")

    # Test combined filters: Intensity + PCA loadings
    print(f"\n🔬 Testing combined filters (5% Intensity + |PC1| >= 0.05):")

    # Apply 5% intensity threshold first
    threshold_percent = 5
    max_intensity = mean_intensities.max()
    threshold_intensity = (threshold_percent / 100.0) * max_intensity
    intensity_mask = mean_intensities >= threshold_intensity

    print(f"   1. Intensity filter (5%): {intensity_mask.sum()}/{len(mz_values)} peaks")

    # Then apply PCA loadings filter
    passing_mz = mz_values[intensity_mask]
    passing_intensities = mean_intensities[intensity_mask]
    passing_std_devs = std_devs[intensity_mask]

    pca_filtered_mz, pca_filtered_intensities, pca_filtered_std_devs, pca_mask = apply_pca_loadings_filter(
        passing_mz, passing_intensities, passing_std_devs, loadings_df, 0.05
    )

    print(f"   2. PCA loadings (|PC1| >= 0.05): {len(pca_filtered_mz)}/{len(passing_mz)} peaks")
    print(f"   Final peaks: {len(pca_filtered_mz)} peaks")

    # Verification: All final peaks should be above intensity threshold and loading threshold
    for mz in pca_filtered_mz:
        idx = np.argmin(np.abs(mz_values - mz))
        intensity = mean_intensities[idx]
        assert intensity >= threshold_intensity, \
            "❌ Combined filter: peaks below intensity threshold!"

        if mz in loadings_df.index:
            abs_loading = abs(loadings_df.loc[mz, 'PC1'])
            assert abs_loading >= 0.05, \
                "❌ Combined filter: peaks below loading threshold!"

    print(f"   ✅ Combined filters work correctly")

    print("\n" + "=" * 70)
    print("✅ STAGE 6 TESTS PASSED")
    print("=" * 70)
    print(f"\nStage 6 Complete:")
    print(f"✅ PCA loadings filter implemented")
    print(f"✅ Filters based on |PC1| loading value")
    print(f"✅ Higher thresholds progressively filter more peaks")
    print(f"✅ Combined filters work (Intensity + PCA loadings)")
    print(f"\nFilter effectiveness:")
    for threshold in plot_thresholds:
        count = results[threshold]['count']
        print(f"   |PC1| >= {threshold:.2f}: {count:2d}/{len(mz_values)} peaks "
              f"({count/len(mz_values)*100:5.1f}% retained)")
    print(f"\nNext steps:")
    print(f"1. Test in full GUI application (requires running PCA first)")
    print(f"2. Test PCA loading filter with different components (PC2, PC3)")
    print(f"3. Test combined filters (all 4: Intensity + Top N + m/z + PCA)")
    print(f"4. Begin Stage 7: Statistical and Assignment filters")

    return True


if __name__ == "__main__":
    try:
        success = test_pca_loadings_filter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
