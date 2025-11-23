#!/usr/bin/env python3
"""
Statistical analysis of fragment intensities.

Stage 1: Pairwise t-tests (AD vs each dose)
Stage 2: Dose-trajectory ANOVA and regression
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection


def load_fragment_intensities(csv_path):
    """Load fragment intensities from CSV file."""
    return pd.read_csv(csv_path)


def ttest_two_groups(group1_samples, group2_samples):
    """
    Perform two-sample t-test.

    Parameters:
    -----------
    group1_samples : list of column names for group 1
    group2_samples : list of column names for group 2
    df : DataFrame with intensity data

    Returns:
    --------
    dict with t-statistic, p-value
    """
    # Will be called on row-by-row basis
    pass


def calculate_fold_change(mean1, mean2):
    """Calculate fold change with handling of zero/near-zero values."""
    if mean1 == 0 or np.isnan(mean1):
        return np.nan
    fc = mean2 / mean1
    return fc


def analyze_pairwise(intensity_file, dose):
    """
    Analyze one pairwise comparison (AD vs specific dose).

    Parameters:
    -----------
    intensity_file : str or Path
        Path to fragment_intensities.csv
    dose : int
        Dose level (2000, 5000, 10000, or 15000)

    Returns:
    --------
    DataFrame with statistics for each fragment
    """
    df = load_fragment_intensities(intensity_file)

    # Identify sample columns
    sq0_cols = ['P1_SQ0', 'P2_SQ0', 'P3_SQ0']
    dose_map = {
        2000: 'SQ2',
        5000: 'SQ3',
        10000: 'SQ4',
        15000: 'SQ5'
    }
    dose_label = dose_map[dose]
    dose_cols = [f'P1_{dose_label}', f'P2_{dose_label}', f'P3_{dose_label}']

    # Initialize results
    results = []

    for idx, row in df.iterrows():
        # Get intensity values
        sq0_vals = row[sq0_cols].values.astype(float)
        dose_vals = row[dose_cols].values.astype(float)

        # Skip if any NaN values
        if np.any(np.isnan(sq0_vals)) or np.any(np.isnan(dose_vals)):
            results.append({
                't_stat': np.nan,
                'p_value': np.nan,
                'fold_change': np.nan,
                'log2fc': np.nan,
                'cohens_d': np.nan
            })
            continue

        # T-test
        t_stat, p_value = stats.ttest_ind(sq0_vals, dose_vals)

        # Fold change
        mean_sq0 = np.mean(sq0_vals)
        mean_dose = np.mean(dose_vals)
        fc = calculate_fold_change(mean_sq0, mean_dose)
        log2fc = np.log2(fc) if not np.isnan(fc) and fc > 0 else np.nan

        # Cohen's d (effect size)
        pooled_std = np.sqrt((np.std(sq0_vals, ddof=1)**2 + np.std(dose_vals, ddof=1)**2) / 2)
        cohens_d = (mean_dose - mean_sq0) / pooled_std if pooled_std > 0 else np.nan

        results.append({
            't_stat': t_stat,
            'p_value': p_value,
            'fold_change': fc,
            'log2fc': log2fc,
            'cohens_d': cohens_d
        })

    # Convert to DataFrame
    stats_df = pd.DataFrame(results)

    # FDR correction
    valid_pvals = ~stats_df['p_value'].isna()
    if valid_pvals.sum() > 0:
        reject, q_values = fdrcorrection(stats_df.loc[valid_pvals, 'p_value'].values)
        stats_df.loc[valid_pvals, 'q_value'] = q_values
        stats_df.loc[valid_pvals, 'significant'] = q_values < 0.05
    else:
        stats_df['q_value'] = np.nan
        stats_df['significant'] = False

    # Combine with original data
    result = pd.concat([
        df[['m/z', 'Fragment', 'PC1_Loading', 'SQ0_mean', f'{dose_label}_mean', 'SQ0_sd', f'{dose_label}_sd']],
        stats_df
    ], axis=1)

    return result


def analyze_dose_trajectory(intensity_file, ion_mode):
    """
    Analyze dose-trajectory (ANOVA and regression across doses).

    Parameters:
    -----------
    intensity_file : str or Path
        Path to fragment_intensities.csv for dose-trajectory analysis
    ion_mode : str
        'positive' or 'negative'

    Returns:
    --------
    DataFrame with ANOVA and regression statistics
    """
    df = load_fragment_intensities(intensity_file)

    # Dose columns (no SQ0 in trajectory)
    doses = [2000, 5000, 10000, 15000]
    dose_labels = ['SQ2', 'SQ3', 'SQ4', 'SQ5']

    results = []

    for idx, row in df.iterrows():
        # Collect all intensity values organized by dose
        dose_groups = []
        dose_means = []

        for dose_label in dose_labels:
            cols = [f'P1_{dose_label}', f'P2_{dose_label}', f'P3_{dose_label}']
            vals = row[cols].values.astype(float)

            if np.any(np.isnan(vals)):
                dose_groups.append([np.nan, np.nan, np.nan])
                dose_means.append(np.nan)
            else:
                dose_groups.append(vals)
                dose_means.append(np.mean(vals))

        # Skip if any NaN values
        if any(np.isnan(dose_means)):
            results.append({
                'anova_F': np.nan,
                'anova_p': np.nan,
                'slope': np.nan,
                'intercept': np.nan,
                'R_squared': np.nan,
                'regression_p': np.nan
            })
            continue

        # One-way ANOVA
        F_stat, anova_p = stats.f_oneway(*dose_groups)

        # Linear regression
        # X = dose values, Y = mean intensities
        X = np.array(doses)
        Y = np.array(dose_means)

        # Simple linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
        R_squared = r_value ** 2

        results.append({
            'anova_F': F_stat,
            'anova_p': anova_p,
            'slope': slope,
            'intercept': intercept,
            'R_squared': R_squared,
            'regression_p': p_value
        })

    # Convert to DataFrame
    stats_df = pd.DataFrame(results)

    # FDR correction for ANOVA
    valid_pvals = ~stats_df['anova_p'].isna()
    if valid_pvals.sum() > 0:
        reject, q_values = fdrcorrection(stats_df.loc[valid_pvals, 'anova_p'].values)
        stats_df.loc[valid_pvals, 'anova_q'] = q_values
        stats_df.loc[valid_pvals, 'anova_significant'] = q_values < 0.05
    else:
        stats_df['anova_q'] = np.nan
        stats_df['anova_significant'] = False

    # Classify trends
    def classify_trend(row):
        if np.isnan(row['anova_p']) or np.isnan(row['R_squared']):
            return 'unknown'
        if row['anova_q'] >= 0.05:
            return 'no_trend'
        if row['R_squared'] > 0.8 and row['regression_p'] < 0.05:
            if row['slope'] > 0:
                return 'linear_increase'
            else:
                return 'linear_decrease'
        else:
            return 'non_linear'

    stats_df['trend_type'] = stats_df.apply(classify_trend, axis=1)

    # Linear trend flag
    stats_df['linear_trend'] = (stats_df['R_squared'] > 0.8) & (stats_df['regression_p'] < 0.05)

    # Combine with original data
    dose_mean_cols = [f'{label}_mean' for label in dose_labels]
    result = pd.concat([
        df[['m/z', 'Fragment', 'PC1_Loading'] + dose_mean_cols],
        stats_df
    ], axis=1)

    return result


def main():
    """Test function - analyze Pairwise/Positive/2000."""
    print("="*80)
    print("TESTING: Pairwise/Positive/2000 Statistical Analysis")
    print("="*80)

    result = analyze_pairwise(
        intensity_file='outputs/Pairwise/Positive/2000/fragment_intensities.csv',
        dose=2000
    )

    # Show top significant results
    print("\nTop 10 fragments by |log2 fold change|:")
    print(result.nlargest(10, 'log2fc', keep='all')[
        ['m/z', 'Fragment', 'log2fc', 'fold_change', 'p_value', 'q_value', 'significant']
    ].to_string(index=False))

    print("\n\nTop 10 most significant (by q-value):")
    print(result.nsmallest(10, 'q_value')[
        ['m/z', 'Fragment', 'log2fc', 'p_value', 'q_value', 'cohens_d']
    ].to_string(index=False))

    # Save output
    output_path = Path('outputs/Pairwise/Positive/2000/pairwise_statistics.csv')
    result.to_csv(output_path, index=False)
    print(f"\n✓ Saved to: {output_path}")

    # Summary statistics
    n_significant = result['significant'].sum()
    n_total = len(result)
    print(f"\nSummary: {n_significant}/{n_total} fragments significant (q < 0.05)")

    return result


if __name__ == '__main__':
    main()
