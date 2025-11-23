#!/usr/bin/env python3
"""
Create combined pairwise summary showing all doses side-by-side.
"""

import pandas as pd
from pathlib import Path


def create_pairwise_summary(ion_mode):
    """
    Create summary combining all 4 pairwise comparisons for one ion mode.

    Parameters:
    -----------
    ion_mode : str
        'Positive' or 'Negative'
    """
    doses = [2000, 5000, 10000, 15000]
    dose_labels = ['2k', '5k', '10k', '15k']

    # Load all pairwise results
    dfs = {}
    for dose, label in zip(doses, dose_labels):
        csv_path = f'outputs/Pairwise/{ion_mode}/{dose}/pairwise_statistics.csv'
        dfs[label] = pd.read_csv(csv_path)

    # Start with m/z and Fragment from first file
    base_df = dfs['2k'][['m/z', 'Fragment']].copy()

    # Add data from each dose
    for label in dose_labels:
        df = dfs[label]

        # Add key columns with dose suffix
        base_df[f'log2fc_{label}'] = df['log2fc']
        base_df[f'fc_{label}'] = df['fold_change']
        base_df[f'pval_{label}'] = df['p_value']
        base_df[f'qval_{label}'] = df['q_value']
        base_df[f'sig_{label}'] = df['significant']

    # Calculate summary metrics
    fc_cols = [f'log2fc_{label}' for label in dose_labels]
    base_df['mean_log2fc'] = base_df[fc_cols].mean(axis=1)
    base_df['std_log2fc'] = base_df[fc_cols].std(axis=1)

    # Check consistency
    sig_cols = [f'sig_{label}' for label in dose_labels]
    base_df['n_significant'] = base_df[sig_cols].sum(axis=1)
    base_df['always_significant'] = base_df['n_significant'] == 4

    # Check if direction is consistent (all positive or all negative log2fc)
    def check_consistent_direction(row):
        values = [row[f'log2fc_{label}'] for label in dose_labels]
        values = [v for v in values if not pd.isna(v)]
        if len(values) == 0:
            return False
        all_positive = all(v > 0 for v in values)
        all_negative = all(v < 0 for v in values)
        return all_positive or all_negative

    base_df['consistent_direction'] = base_df.apply(check_consistent_direction, axis=1)

    # Determine trend (does effect size increase/decrease with dose?)
    def determine_trend(row):
        values = [row[f'log2fc_{label}'] for label in dose_labels]
        if any(pd.isna(v) for v in values):
            return 'unknown'

        # Check if monotonic
        increasing = all(values[i] <= values[i+1] for i in range(len(values)-1))
        decreasing = all(values[i] >= values[i+1] for i in range(len(values)-1))

        if increasing:
            return 'increasing_effect'
        elif decreasing:
            return 'decreasing_effect'
        else:
            return 'variable_effect'

    base_df['effect_trend'] = base_df.apply(determine_trend, axis=1)

    # Reorder columns for clarity
    info_cols = ['m/z', 'Fragment']
    summary_cols = ['mean_log2fc', 'std_log2fc', 'n_significant', 'always_significant',
                    'consistent_direction', 'effect_trend']

    detail_cols = []
    for label in dose_labels:
        detail_cols.extend([f'log2fc_{label}', f'fc_{label}', f'qval_{label}', f'sig_{label}'])

    base_df = base_df[info_cols + summary_cols + detail_cols]

    # Sort by mean absolute log2fc
    base_df['abs_mean_log2fc'] = base_df['mean_log2fc'].abs()
    base_df = base_df.sort_values('abs_mean_log2fc', ascending=False).drop('abs_mean_log2fc', axis=1)

    return base_df


if __name__ == '__main__':
    print("="*80)
    print("CREATING PAIRWISE SUMMARY FILES")
    print("="*80)

    for ion_mode in ['Positive', 'Negative']:
        print(f"\nProcessing {ion_mode} ion mode...")

        summary = create_pairwise_summary(ion_mode)

        # Save
        output_path = Path(f'outputs/Pairwise/{ion_mode}/pairwise_summary_all_doses.csv')
        summary.to_csv(output_path, index=False)

        print(f"  ✓ Saved: {output_path}")
        print(f"  Total fragments: {len(summary)}")
        print(f"  Always significant: {summary['always_significant'].sum()}")
        print(f"  Consistent direction: {summary['consistent_direction'].sum()}")

        # Show top 5
        print(f"\n  Top 5 fragments by |mean log2fc|:")
        print(summary[['m/z', 'Fragment', 'mean_log2fc', 'always_significant', 'effect_trend']].head(5).to_string(index=False))

    print("\n" + "="*80)
    print("PAIRWISE SUMMARIES COMPLETED")
    print("="*80)
