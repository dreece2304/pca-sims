#!/usr/bin/env python3
"""
Process statistical analysis for all pairwise comparisons.
"""

from analyze_fragment_statistics import analyze_pairwise
from pathlib import Path


def process_all_pairwise():
    """Process all pairwise analyses."""

    analyses = [
        ('Positive', 2000),
        ('Positive', 5000),
        ('Positive', 10000),
        ('Positive', 15000),
        ('Negative', 2000),
        ('Negative', 5000),
        ('Negative', 10000),
        ('Negative', 15000),
    ]

    for ion_mode, dose in analyses:
        print(f"\nProcessing {ion_mode} {dose}...")

        intensity_file = f'outputs/Pairwise/{ion_mode}/{dose}/fragment_intensities.csv'
        output_file = f'outputs/Pairwise/{ion_mode}/{dose}/pairwise_statistics.csv'

        result = analyze_pairwise(intensity_file, dose)
        result.to_csv(output_file, index=False)

        n_sig = result['significant'].sum()
        n_total = len(result)
        print(f"  ✓ {n_sig}/{n_total} significant fragments (q < 0.05)")


if __name__ == '__main__':
    print("="*80)
    print("PROCESSING ALL PAIRWISE STATISTICAL ANALYSES")
    print("="*80)

    process_all_pairwise()

    print("\n" + "="*80)
    print("ALL PAIRWISE STATISTICS COMPLETED")
    print("="*80)
