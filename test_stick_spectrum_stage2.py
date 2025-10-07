#!/usr/bin/env python3
"""
Test Stage 2: Fragment Assignment Integration
Tests fragment database loading and assignment matching
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


def test_fragment_assignment_integration():
    """Test fragment assignment integration with stick spectrum"""

    print("=" * 70)
    print("STAGE 2 TEST: Fragment Assignment Integration")
    print("=" * 70)

    # Test with negative ion data
    data_file = "data/NegativeIon/NegAllCompoundSearch.txt"

    print(f"\n📁 Loading data: {data_file}")

    # Load data
    pca = SimpleToFSIMSPCA(data_file)
    pca.load_data()

    print(f"✅ Data loaded: {pca.raw_data.shape}")

    # Test dose selection: SQ4 (dose_id = 4)
    test_dose = 4

    print(f"\n🎯 Testing dose selection: SQ{test_dose}")

    # Filter samples for selected dose
    dose_mask = pca.sample_metadata['dose_id'] == test_dose
    dose_samples = pca.sample_metadata[dose_mask]
    sample_names = dose_samples['sample_name'].tolist()
    dose_data = pca.raw_data[sample_names]

    # Calculate statistics
    mean_intensities = dose_data.mean(axis=1).values
    std_devs = dose_data.std(axis=1).values
    mz_values = pca.raw_data.index.values

    print(f"   {len(mz_values)} m/z values")
    print(f"   {len(sample_names)} replicates")

    # Load fragment database
    print(f"\n📚 Loading fragment database...")
    database = load_fragment_database()
    print(f"✅ Loaded {len(database['fragments'])} fragments")
    print(f"   Negative: {database['metadata']['negative_fragments']}")
    print(f"   Positive: {database['metadata']['positive_fragments']}")

    # Find assignments for peaks
    print(f"\n🔍 Finding fragment assignments...")
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
            'error_ppm': matches[0]['error_ppm'] if matches else np.nan
        }
        fragment_assignments.append(assignment_info)

    # Count assignments
    assigned = [a for a in fragment_assignments if a['assignment'] != "Unassigned"]
    unassigned = [a for a in fragment_assignments if a['assignment'] == "Unassigned"]

    print(f"✅ Fragment assignment complete:")
    print(f"   Assigned: {len(assigned)}/{len(mz_values)} ({len(assigned)/len(mz_values)*100:.1f}%)")
    print(f"   Unassigned: {len(unassigned)}/{len(mz_values)} ({len(unassigned)/len(mz_values)*100:.1f}%)")

    # Show top 10 assigned peaks by intensity
    print(f"\n📊 Top 10 assigned peaks (by intensity):")
    assigned_sorted = sorted(assigned, key=lambda x: x['mean_intensity'], reverse=True)[:10]
    for i, a in enumerate(assigned_sorted, 1):
        print(f"   {i}. m/z {a['mz']:.4f} → {a['assignment']:15s} "
              f"(I={a['mean_intensity']:.3e}, CV={a['cv_percent']:.1f}%, "
              f"err={a['error_ppm']:.1f} ppm)")

    # Select top 5 for labeling
    print(f"\n🏷️  Selecting top 5 peaks for labeling...")
    labels = {}
    for a in assigned_sorted[:5]:
        labels[a['mz']] = a['assignment']
        a['show_label'] = True

    print(f"   Labels: {list(labels.values())}")

    # Plot with labels
    print(f"\n🎨 Plotting stick spectrum with fragment labels...")

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

    # Add labels
    for mz, label_text in labels.items():
        idx = np.argmin(np.abs(mz_values - mz))
        intensity = mean_intensities[idx]
        offset = intensity * 0.05

        ax_main.text(
            mz,
            intensity + offset,
            label_text,
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold',
            rotation=0,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                     edgecolor='none', alpha=0.7)
        )

    ax_main.set_xlabel('m/z', fontweight='bold')
    ax_main.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')
    ax_main.set_title(f'Negative Ion - SQ4 (10000 µC/cm²) - With Fragment Labels',
                      fontweight='bold', loc='left')
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

    # Save
    output_file = "test_stick_spectrum_stage2_output.png"
    fig.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ Plot saved to: {output_file}")

    plt.close(fig)

    # Verification checks
    print(f"\n🔍 Verification checks:")

    # Check database loaded
    assert len(database['fragments']) > 0, "❌ Database is empty!"
    print(f"   ✅ Database loaded ({len(database['fragments'])} fragments)")

    # Check assignments found
    assert len(assigned) > 0, "❌ No assignments found!"
    print(f"   ✅ Assignments found ({len(assigned)} peaks)")

    # Check labels added
    assert len(labels) == 5, f"❌ Expected 5 labels, got {len(labels)}"
    print(f"   ✅ Labels added ({len(labels)} peaks)")

    # Check all labeled peaks are assigned
    for mz in labels.keys():
        assignment = next((a for a in fragment_assignments if a['mz'] == mz), None)
        assert assignment is not None and assignment['assignment'] != "Unassigned", \
            f"❌ Labeled peak at m/z {mz} is unassigned!"
    print(f"   ✅ All labeled peaks have assignments")

    # Check mass accuracy
    avg_error = np.mean([a['error_ppm'] for a in assigned])
    print(f"   ✅ Average mass error: {avg_error:.2f} ppm")

    # Export fragment table data (simulated CSV export)
    print(f"\n💾 Simulating CSV export...")
    csv_data = []
    csv_data.append(['m/z', 'Mean Intensity', 'Std Dev', 'CV%',
                    'Assignment', 'Confidence', 'Show Label'])
    for a in fragment_assignments[:10]:  # First 10 rows
        csv_data.append([
            f"{a['mz']:.4f}",
            f"{a['mean_intensity']:.6e}",
            f"{a['std_dev']:.6e}",
            f"{a['cv_percent']:.2f}",
            a['assignment'],
            a['confidence'],
            'Yes' if a.get('show_label', False) else 'No'
        ])

    print(f"   CSV preview (first 5 rows):")
    for row in csv_data[:5]:
        print(f"   {','.join(row)}")

    print("\n" + "=" * 70)
    print("✅ STAGE 2 TESTS PASSED")
    print("=" * 70)
    print(f"\nStage 2 Complete:")
    print(f"✅ Fragment database integration")
    print(f"✅ Assignment matching with ppm tolerance")
    print(f"✅ Label display on stick spectrum")
    print(f"✅ Fragment table data structure")
    print(f"\nNext steps:")
    print(f"1. Test in full GUI application")
    print(f"2. Test fragment table dialog and label toggling")
    print(f"3. Test CSV export functionality")
    print(f"4. Begin Stage 3: Intensity threshold filter")

    return True


if __name__ == "__main__":
    try:
        success = test_fragment_assignment_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
