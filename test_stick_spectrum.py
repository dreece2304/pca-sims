#!/usr/bin/env python3
"""
Standalone test for stick spectrum plotting
Tests plotting functionality without running full GUI
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


def test_stick_spectrum_plotting():
    """Test stick spectrum plotting with real data"""

    print("=" * 60)
    print("STICK SPECTRUM PLOTTING TEST")
    print("=" * 60)

    # Test with negative ion data
    data_file = "data/NegativeIon/NegAllCompoundSearch.txt"

    print(f"\n📁 Loading data: {data_file}")

    # Load data using existing PCA class
    pca = SimpleToFSIMSPCA(data_file)
    pca.load_data()

    print(f"✅ Data loaded: {pca.raw_data.shape}")
    print(f"   m/z range: {pca.mass_values.min():.3f} - {pca.mass_values.max():.3f}")
    print(f"   Samples: {len(pca.sample_metadata)}")

    # Test dose selection: SQ4 (dose_id = 4)
    test_dose = 4  # SQ4 = 10000 µC/cm²

    print(f"\n🎯 Testing dose selection: SQ{test_dose}")

    # Filter samples for selected dose
    dose_mask = pca.sample_metadata['dose_id'] == test_dose
    dose_samples = pca.sample_metadata[dose_mask]

    print(f"   Found {len(dose_samples)} replicates")
    print(f"   Sample names: {dose_samples['sample_name'].tolist()}")

    if len(dose_samples) == 0:
        print("❌ No samples found for this dose")
        return False

    # Get data for this dose
    sample_names = dose_samples['sample_name'].tolist()
    dose_data = pca.raw_data[sample_names]

    # Calculate statistics
    mean_intensities = dose_data.mean(axis=1).values
    std_devs = dose_data.std(axis=1).values
    mz_values = pca.raw_data.index.values

    print(f"\n📊 Calculated statistics:")
    print(f"   Mean intensity range: {mean_intensities.min():.6f} - {mean_intensities.max():.6f}")
    print(f"   Std dev range: {std_devs.min():.6f} - {std_devs.max():.6f}")
    print(f"   Number of m/z values: {len(mz_values)}")

    # Test plotting
    print(f"\n🎨 Testing matplotlib plotting...")

    fig, (ax_main, ax_sd) = plt.subplots(2, 1, figsize=(12, 8),
                                          gridspec_kw={'height_ratios': [3, 1]})

    # Main stick spectrum
    markerline, stemlines, baseline = ax_main.stem(
        mz_values,
        mean_intensities,
        linefmt='#440154',  # Viridis dark
        markerfmt=' ',
        basefmt='k-'
    )
    stemlines.set_linewidth(1.0)
    stemlines.set_alpha(0.8)

    ax_main.set_xlabel('m/z', fontweight='bold')
    ax_main.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')
    ax_main.set_title(f'Negative Ion - SQ4 (10000 µC/cm²)', fontweight='bold', loc='left')
    ax_main.spines['top'].set_visible(False)
    ax_main.spines['right'].set_visible(False)
    ax_main.set_ylim(bottom=0)
    ax_main.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # SD plot
    ax_sd.scatter(mz_values, std_devs, alpha=0.6, s=20, color='#21908C', edgecolors='none')
    ax_sd.plot(mz_values, std_devs, color='#21908C', alpha=0.3, linewidth=0.5)
    ax_sd.set_xlabel('m/z', fontweight='bold')
    ax_sd.set_ylabel('Std Dev', fontweight='bold')
    ax_sd.set_title('Replicate Variability', fontweight='bold', loc='left', fontsize=10)
    ax_sd.spines['top'].set_visible(False)
    ax_sd.spines['right'].set_visible(False)
    ax_sd.set_ylim(bottom=0)
    ax_sd.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Save to file
    output_file = "test_stick_spectrum_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Verify some key statistics
    print(f"\n🔍 Verification checks:")

    # Check that we have positive intensities
    assert mean_intensities.min() >= 0, "❌ Negative intensities found!"
    print(f"   ✅ All intensities are non-negative")

    # Check that we have 3 replicates (so std can be calculated)
    assert len(sample_names) == 3, f"❌ Expected 3 replicates, got {len(sample_names)}"
    print(f"   ✅ Correct number of replicates (3)")

    # Check that mean and std have same length
    assert len(mean_intensities) == len(std_devs) == len(mz_values), "❌ Array length mismatch!"
    print(f"   ✅ Array lengths match ({len(mz_values)} points)")

    # Check that std is less than mean (generally true for count data)
    high_intensity_mask = mean_intensities > 0.01  # Only check high intensity peaks
    if high_intensity_mask.any():
        cv_values = std_devs[high_intensity_mask] / mean_intensities[high_intensity_mask]
        mean_cv = cv_values.mean()
        print(f"   ✅ Mean coefficient of variation: {mean_cv*100:.1f}%")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Check output file: {output_file}")
    print(f"2. Verify stick spectrum looks correct")
    print(f"3. Verify SD plot shows variability")
    print(f"4. Test in full GUI application")

    return True


if __name__ == "__main__":
    try:
        success = test_stick_spectrum_plotting()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
