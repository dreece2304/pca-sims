#!/usr/bin/env python3
"""
Process all PCA analyses to extract fragment intensities.
"""

from extract_fragment_intensities import extract_fragment_intensities
from pathlib import Path


def process_pairwise_positive():
    """Process all pairwise positive ion analyses."""
    print("\n" + "="*80)
    print("PROCESSING PAIRWISE POSITIVE ION ANALYSES")
    print("="*80)

    doses = [2000, 5000, 10000, 15000]

    for dose in doses:
        analysis_folder = f'outputs/Pairwise/Positive/{dose}'
        output_path = Path(analysis_folder) / 'fragment_intensities.csv'

        result = extract_fragment_intensities(
            analysis_folder=analysis_folder,
            ion_mode='positive',
            analysis_type='pairwise',
            dose=dose
        )

        result.to_csv(output_path, index=False)
        print(f"✓ Saved {output_path} ({len(result)} fragments)")


def process_pairwise_negative():
    """Process all pairwise negative ion analyses."""
    print("\n" + "="*80)
    print("PROCESSING PAIRWISE NEGATIVE ION ANALYSES")
    print("="*80)

    doses = [2000, 5000, 10000, 15000]

    for dose in doses:
        analysis_folder = f'outputs/Pairwise/Negative/{dose}'
        output_path = Path(analysis_folder) / 'fragment_intensities.csv'

        result = extract_fragment_intensities(
            analysis_folder=analysis_folder,
            ion_mode='negative',
            analysis_type='pairwise',
            dose=dose
        )

        result.to_csv(output_path, index=False)
        print(f"✓ Saved {output_path} ({len(result)} fragments)")


def process_dose_dependant():
    """Process dose-dependant analyses (all samples including SQ0)."""
    print("\n" + "="*80)
    print("PROCESSING DOSE-DEPENDANT ANALYSES")
    print("="*80)

    for ion_mode in ['Positive', 'Negative']:
        analysis_folder = f'outputs/Dose-Dependant/{ion_mode}'
        output_path = Path(analysis_folder) / 'fragment_intensities.csv'

        result = extract_fragment_intensities(
            analysis_folder=analysis_folder,
            ion_mode=ion_mode.lower(),
            analysis_type='dose-dependant'
        )

        result.to_csv(output_path, index=False)
        print(f"✓ Saved {output_path} ({len(result)} fragments)")


def process_dose_trajectory():
    """Process dose-trajectory analyses (e-beam samples only)."""
    print("\n" + "="*80)
    print("PROCESSING DOSE-TRAJECTORY ANALYSES")
    print("="*80)

    for ion_mode in ['Positive', 'Negative']:
        analysis_folder = f'outputs/Dose-Trajectory/{ion_mode}'
        output_path = Path(analysis_folder) / 'fragment_intensities.csv'

        result = extract_fragment_intensities(
            analysis_folder=analysis_folder,
            ion_mode=ion_mode.lower(),
            analysis_type='dose-trajectory'
        )

        result.to_csv(output_path, index=False)
        print(f"✓ Saved {output_path} ({len(result)} fragments)")


if __name__ == '__main__':
    # Process remaining pairwise positive (5k, 10k, 15k) - 2k already done
    print("\nProcessing remaining Pairwise Positive analyses...")
    for dose in [5000, 10000, 15000]:
        analysis_folder = f'outputs/Pairwise/Positive/{dose}'
        output_path = Path(analysis_folder) / 'fragment_intensities.csv'

        result = extract_fragment_intensities(
            analysis_folder=analysis_folder,
            ion_mode='positive',
            analysis_type='pairwise',
            dose=dose
        )

        result.to_csv(output_path, index=False)
        print(f"✓ Saved {output_path} ({len(result)} fragments)")

    # Process all pairwise negative
    process_pairwise_negative()

    # Process dose-dependant
    process_dose_dependant()

    # Process dose-trajectory
    process_dose_trajectory()

    print("\n" + "="*80)
    print("ALL ANALYSES PROCESSED SUCCESSFULLY!")
    print("="*80)
