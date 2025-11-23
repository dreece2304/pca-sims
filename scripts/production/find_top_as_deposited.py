#!/usr/bin/env python3
"""
Find top as-deposited intensities for fragments with assignments.
"""

import pandas as pd
import numpy as np

def find_top_fragments(data_file, fragment_file, ion_mode):
    """Find top as-deposited intensities for assigned fragments."""

    # Load raw intensity data
    data = pd.read_csv(data_file, sep='\t')

    # Get SQ0 columns only
    sq0_cols = [col for col in data.columns if 'SQ0' in col]

    # Calculate mean and SD for SQ0
    data['SQ0_mean'] = data[sq0_cols].mean(axis=1)
    data['SQ0_sd'] = data[sq0_cols].std(axis=1)

    # Sort by mean intensity
    data_sorted = data[['Mass (u)', 'SQ0_mean', 'SQ0_sd']].sort_values('SQ0_mean', ascending=False)

    # Load fragment assignments
    fragments = pd.read_csv(fragment_file)

    # Round m/z for matching
    data_sorted['m/z_rounded'] = data_sorted['Mass (u)'].round(4)
    fragments['m/z_rounded'] = fragments['m/z'].round(4)

    # Merge to get only assigned fragments
    result = data_sorted.merge(
        fragments[['m/z_rounded', 'Current Assignment']],
        on='m/z_rounded',
        how='inner'
    )

    # Sort by intensity
    result = result.sort_values('SQ0_mean', ascending=False)
    result = result.rename(columns={'Current Assignment': 'Fragment'})

    print(f"\n{ion_mode.upper()} IONS - Top As-Deposited Intensities (with fragment assignments)")
    print("=" * 80)
    print(f"{'m/z':>10}  {'Fragment':30}  {'SQ0 Mean':>12}  {'SQ0 SD':>10}")
    print("-" * 80)

    for _, row in result.iterrows():
        print(f"{row['Mass (u)']:10.5f}  {row['Fragment']:30s}  "
              f"{row['SQ0_mean']:12.6f}  {row['SQ0_sd']:10.6f}")

    return result


# Process both ion modes
pos_result = find_top_fragments(
    'data/PositiveIon/PosAllCompoundSearch.txt',
    'outputs/Pairwise/Positive/2000/fragment_assignments.csv',
    'Positive'
)

neg_result = find_top_fragments(
    'data/NegativeIon/NegAllCompoundSearch.txt',
    'outputs/Pairwise/Negative/2000/fragment_assignments.csv',
    'Negative'
)

# Save to files
pos_result.to_csv('outputs/Visualizations/top_as_deposited_positive.csv', index=False)
neg_result.to_csv('outputs/Visualizations/top_as_deposited_negative.csv', index=False)

print("\n" + "=" * 90)
print("Results saved to outputs/Visualizations/")
print("=" * 90)
