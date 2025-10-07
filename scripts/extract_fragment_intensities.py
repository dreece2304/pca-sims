#!/usr/bin/env python3
"""
Extract fragment intensities for PCA analysis results.

This script reads PCA analysis Excel files, matches m/z values with fragment
assignments, and extracts raw TIC-normalized intensities for relevant samples.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_pca_mz_list(excel_path):
    """Load m/z values and PC1 loadings from PCA analysis Excel file."""
    df = pd.read_excel(excel_path, sheet_name='PCA Loadings')
    # The index column contains m/z values
    df = df.rename(columns={'index': 'm/z'})
    return df[['m/z', 'PC1']].copy()


def load_fragment_assignments(csv_path):
    """Load fragment assignments from CSV file."""
    df = pd.read_csv(csv_path)
    return df[['m/z', 'Current Assignment']].copy()


def load_raw_intensities(data_path, ion_mode):
    """Load raw TIC-normalized intensity data."""
    df = pd.read_csv(data_path, sep='\t')
    # First column is 'Mass (u)'
    df = df.rename(columns={'Mass (u)': 'm/z'})
    return df


def match_mz(target_mz, data_df, tolerance=0.001):
    """Find matching m/z in data with tolerance for floating point comparison.

    Uses 0.001 tolerance to handle rounding differences between fragment assignments
    (4 decimal places) and raw data (5+ decimal places).
    """
    matches = data_df[np.abs(data_df['m/z'] - target_mz) < tolerance]
    if len(matches) == 0:
        return None
    return matches.iloc[0]


def get_relevant_columns(analysis_type, dose=None):
    """Determine which sample columns to extract based on analysis type."""
    sq0_cols = ['P1_SQ0', 'P2_SQ0', 'P3_SQ0']

    if analysis_type == 'pairwise':
        # For pairwise: SQ0 + specific dose
        dose_map = {
            2000: ['P1_SQ2', 'P2_SQ2', 'P3_SQ2'],
            5000: ['P1_SQ3', 'P2_SQ3', 'P3_SQ3'],
            10000: ['P1_SQ4', 'P2_SQ4', 'P3_SQ4'],
            15000: ['P1_SQ5', 'P2_SQ5', 'P3_SQ5']
        }
        return sq0_cols + dose_map[dose]

    elif analysis_type == 'dose-dependant':
        # All samples including SQ0
        return sq0_cols + ['P1_SQ2', 'P2_SQ2', 'P3_SQ2',
                           'P1_SQ3', 'P2_SQ3', 'P3_SQ3',
                           'P1_SQ4', 'P2_SQ4', 'P3_SQ4',
                           'P1_SQ5', 'P2_SQ5', 'P3_SQ5']

    elif analysis_type == 'dose-trajectory':
        # E-beam samples only, no SQ0
        return ['P1_SQ2', 'P2_SQ2', 'P3_SQ2',
                'P1_SQ3', 'P2_SQ3', 'P3_SQ3',
                'P1_SQ4', 'P2_SQ4', 'P3_SQ4',
                'P1_SQ5', 'P2_SQ5', 'P3_SQ5']


def extract_fragment_intensities(analysis_folder, ion_mode, analysis_type, dose=None,
                                  raw_data_path=None):
    """
    Extract fragment intensities for a specific PCA analysis.

    Parameters:
    -----------
    analysis_folder : str or Path
        Path to analysis subfolder (e.g., 'outputs/Pairwise/Positive/2000/')
    ion_mode : str
        'positive' or 'negative'
    analysis_type : str
        'pairwise', 'dose-dependant', or 'dose-trajectory'
    dose : int, optional
        Dose level for pairwise analysis (2000, 5000, 10000, 15000)
    raw_data_path : str or Path, optional
        Path to raw data file (auto-detected if None)
    """
    analysis_folder = Path(analysis_folder)

    # Determine raw data path
    if raw_data_path is None:
        base_path = Path('/home/dreece23/pca-sims/data')
        if ion_mode.lower() == 'positive':
            raw_data_path = base_path / 'PositiveIon' / 'PosAllCompoundSearch.txt'
        else:
            raw_data_path = base_path / 'NegativeIon' / 'NegAllCompoundSearch.txt'

    # Load data
    print(f"Processing {analysis_folder}...")
    pca_excel = analysis_folder / 'pca_analysis.xlsx'
    fragment_csv = analysis_folder / 'fragment_assignments.csv'

    # Load fragment assignments (these are the manually assigned fragments)
    fragments = load_fragment_assignments(fragment_csv)

    # Load PCA loadings
    pca_loadings = load_pca_mz_list(pca_excel)

    # Load raw intensity data
    raw_data = load_raw_intensities(raw_data_path, ion_mode)

    # ONLY use fragments that have assignments
    # Merge with tolerance for m/z precision differences
    # Round both to 4 decimal places for matching
    fragments['m/z_rounded'] = fragments['m/z'].round(4)
    pca_loadings['m/z_rounded'] = pca_loadings['m/z'].round(4)

    result = fragments.merge(pca_loadings, on='m/z_rounded', how='inner', suffixes=('_frag', '_pca'))

    # Use the PCA m/z (more precise) for intensity matching
    result['m/z'] = result['m/z_pca']
    result = result.drop(columns=['m/z_frag', 'm/z_pca', 'm/z_rounded'])
    result = result.rename(columns={'PC1': 'PC1_Loading', 'Current Assignment': 'Fragment'})

    # Get relevant sample columns
    sample_cols = get_relevant_columns(analysis_type, dose)

    # Extract intensities for each m/z
    intensity_data = []
    for _, row in result.iterrows():
        mz_val = row['m/z']
        matched_row = match_mz(mz_val, raw_data)

        if matched_row is not None:
            intensities = {col: matched_row[col] for col in sample_cols if col in matched_row.index}
            intensity_data.append(intensities)
        else:
            print(f"Warning: No intensity data found for m/z {mz_val}")
            intensity_data.append({col: np.nan for col in sample_cols})

    # Combine with result
    intensity_df = pd.DataFrame(intensity_data)
    final_result = pd.concat([result, intensity_df], axis=1)

    # Calculate mean and SD for each condition
    # Group sample columns by condition (SQ0, SQ2, SQ3, SQ4, SQ5)
    conditions = {}
    for col in sample_cols:
        # Extract condition (SQ0, SQ2, etc.) from column name
        condition = col.split('_')[1]  # e.g., 'P1_SQ0' -> 'SQ0'
        if condition not in conditions:
            conditions[condition] = []
        conditions[condition].append(col)

    # Calculate mean and SD for each condition
    stats_cols = []
    for condition in sorted(conditions.keys()):
        cols_for_condition = conditions[condition]
        mean_col = f'{condition}_mean'
        sd_col = f'{condition}_sd'

        final_result[mean_col] = final_result[cols_for_condition].mean(axis=1)
        final_result[sd_col] = final_result[cols_for_condition].std(axis=1)

        stats_cols.extend([mean_col, sd_col])

    # Reorder columns: m/z, Fragment, PC1_Loading, individual replicates, then mean/SD
    cols = ['m/z', 'Fragment', 'PC1_Loading'] + sample_cols + stats_cols
    final_result = final_result[cols]

    return final_result


def main():
    """Test function - process Pairwise/Positive/2000 as example."""
    output = extract_fragment_intensities(
        analysis_folder='outputs/Pairwise/Positive/2000',
        ion_mode='positive',
        analysis_type='pairwise',
        dose=2000
    )

    # Show preview
    print("\n" + "="*80)
    print("PREVIEW: Pairwise/Positive/2000 Fragment Intensities")
    print("="*80)

    # Show key columns for preview
    preview_cols = ['m/z', 'Fragment', 'PC1_Loading', 'SQ0_mean', 'SQ0_sd', 'SQ2_mean', 'SQ2_sd']
    print("\nSummary View (mean ± SD):")
    print(output[preview_cols].head(10).to_string(index=False))

    print(f"\n\nFull data with all replicates saved to file.")
    print(f"Total fragments: {len(output)}")
    print(f"Columns: {', '.join(output.columns.tolist())}")

    # Save to file
    output_path = Path('outputs/Pairwise/Positive/2000/fragment_intensities.csv')
    output.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")

    return output


if __name__ == '__main__':
    main()
