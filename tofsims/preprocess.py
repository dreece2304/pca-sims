"""
Preprocessing and merging layer for ToF-SIMS analysis data.

Handles:
- Metadata cleaning and normalization
- Fragment assignment merging with ppm tolerance
- Replicate validation
- Multi-run aggregation
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import json

import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


def clean_meta(
    df: pd.DataFrame,
    analysis_id: str,
    analysis_type: str,
    polarity: str,
    dose_label: Optional[str] = None,
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Clean and normalize metadata columns.

    Operations:
    - Add analysis_id, analysis_type, polarity columns
    - Normalize polarity to lowercase (positive, negative)
    - Set dose_label from path
    - Map dose_label to dose_uC_cm2 using cfg.dose_mapping if available
    - Set categorical dtypes for analysis_type, polarity, dose_label, replicate

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe (scores or loadings)
    analysis_id : str
        Unique analysis identifier
    analysis_type : str
        Analysis type (pairwise, dose_trajectory, dose_dependent)
    polarity : str
        Polarity (Positive/Negative -> normalized to positive/negative)
    dose_label : str, optional
        Dose label (e.g., "10000" for pairwise, "trajectory" for dose_trajectory)
    cfg : dict, optional
        Configuration with dose_mapping

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with metadata columns
    """
    df = df.copy()

    # Add metadata columns
    df['analysis_id'] = analysis_id
    df['analysis_type'] = analysis_type
    df['polarity'] = polarity.lower()  # Normalize to lowercase

    if dose_label:
        df['dose_label'] = dose_label

    # Map dose_label to numeric dose if available
    if cfg and dose_label:
        dose_mapping = cfg.get('dose_mapping', {})
        if dose_label in dose_mapping:
            df['dose_uC_cm2'] = dose_mapping[dose_label]
        elif 'actual_dose' in df.columns:
            # Use actual_dose from scores if available
            if 'dose_uC_cm2' not in df.columns:
                df['dose_uC_cm2'] = df['actual_dose']

    # Set categorical dtypes
    categorical_cols = {
        'analysis_type': ['pairwise', 'dose_trajectory', 'dose_dependent'],
        'polarity': ['positive', 'negative'],
    }

    for col, categories in categorical_cols.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=categories)

    if 'dose_label' in df.columns:
        df['dose_label'] = df['dose_label'].astype('category')

    if 'replicate' in df.columns:
        df['replicate'] = df['replicate'].astype('category')

    logger.debug(f"Cleaned metadata for {analysis_id}: {len(df)} rows")

    return df


def merge_assignments(
    loadings_df: pd.DataFrame,
    assignments_df: pd.DataFrame,
    tol_ppm: float = 10.0
) -> pd.DataFrame:
    """
    Merge fragment assignments with loadings using ppm tolerance.

    Uses nearest-neighbor matching with ppm tolerance. If multiple assignments
    match, keeps all and flags assignment_conflict=True.

    Parameters
    ----------
    loadings_df : pd.DataFrame
        Loadings with 'mz' column
    assignments_df : pd.DataFrame
        Assignments with 'mz', 'assignment', 'formula', etc.
    tol_ppm : float
        ppm tolerance for matching (default: 10.0)

    Returns
    -------
    pd.DataFrame
        Loadings merged with assignments. Columns added:
        - assignment
        - formula (if present)
        - ppm_error (calculated)
        - confidence (if present)
        - assignment_conflict (True if multiple matches)
    """
    if len(assignments_df) == 0:
        logger.warning("No assignments to merge")
        loadings_df['assignment'] = None
        loadings_df['assignment_conflict'] = False
        return loadings_df

    loadings_df = loadings_df.copy()
    assignments_df = assignments_df.copy()

    # Ensure both have 'mz' column
    if 'mz' not in loadings_df.columns or 'mz' not in assignments_df.columns:
        logger.error("Both dataframes must have 'mz' column")
        return loadings_df

    # Perform merge_asof (nearest neighbor within tolerance)
    # Sort both by mz
    loadings_df = loadings_df.sort_values('mz').reset_index(drop=True)
    assignments_df = assignments_df.sort_values('mz').reset_index(drop=True)

    # Calculate absolute ppm tolerance
    def calc_ppm_tol(mz):
        return mz * tol_ppm / 1e6

    merged_rows = []

    for _, loading_row in loadings_df.iterrows():
        mz_target = loading_row['mz']
        ppm_tol_abs = calc_ppm_tol(mz_target)

        # Find all assignments within tolerance
        mz_diff = np.abs(assignments_df['mz'] - mz_target)
        matches = assignments_df[mz_diff <= ppm_tol_abs].copy()

        if len(matches) == 0:
            # No match
            row = loading_row.copy()
            row['assignment'] = None
            row['assignment_conflict'] = False
            merged_rows.append(row)

        elif len(matches) == 1:
            # Single match
            match = matches.iloc[0]
            row = loading_row.copy()
            row['assignment'] = match.get('assignment', None)
            row['formula'] = match.get('formula', None)
            row['confidence'] = match.get('confidence', None)
            row['ppm_error'] = (match['mz'] - mz_target) / mz_target * 1e6
            row['assignment_conflict'] = False
            merged_rows.append(row)

        else:
            # Multiple matches - flag conflict and keep all
            for _, match in matches.iterrows():
                row = loading_row.copy()
                row['assignment'] = match.get('assignment', None)
                row['formula'] = match.get('formula', None)
                row['confidence'] = match.get('confidence', None)
                row['ppm_error'] = (match['mz'] - mz_target) / mz_target * 1e6
                row['assignment_conflict'] = True
                merged_rows.append(row)

    merged_df = pd.DataFrame(merged_rows)

    n_assigned = merged_df['assignment'].notna().sum()
    n_conflicts = merged_df['assignment_conflict'].sum()

    logger.info(
        f"Merged assignments: {n_assigned}/{len(loadings_df)} assigned, "
        f"{n_conflicts} conflicts"
    )

    return merged_df


def validate_replicates(
    scores_df: pd.DataFrame,
    expected_replicates: int = 3,
    group_cols: Optional[list] = None
) -> pd.DataFrame:
    """
    Validate replicate counts per condition.

    Checks that each (analysis_id, polarity, dose_label) group has the expected
    number of replicates.

    Parameters
    ----------
    scores_df : pd.DataFrame
        Scores dataframe with replicate column
    expected_replicates : int
        Expected number of replicates per condition (default: 3)
    group_cols : list, optional
        Grouping columns (default: ['analysis_id', 'polarity', 'dose_label'])

    Returns
    -------
    pd.DataFrame
        Validation report with columns: group, n_replicates, status
    """
    if group_cols is None:
        group_cols = ['analysis_id', 'polarity']
        if 'dose_label' in scores_df.columns:
            group_cols.append('dose_label')

    # Group and count
    replicate_counts = (
        scores_df
        .groupby(group_cols, observed=True)['replicate']
        .nunique()
        .reset_index()
        .rename(columns={'replicate': 'n_replicates'})
    )

    # Check against expected
    replicate_counts['status'] = replicate_counts['n_replicates'].apply(
        lambda x: '✓' if x == expected_replicates else f'⚠ Expected {expected_replicates}, found {x}'
    )

    # Log summary
    n_groups = len(replicate_counts)
    n_ok = (replicate_counts['n_replicates'] == expected_replicates).sum()
    n_issues = n_groups - n_ok

    if n_issues == 0:
        logger.info(f"✓ Replicate validation passed: {n_groups} groups with {expected_replicates} replicates each")
    else:
        logger.warning(f"⚠ Replicate validation: {n_issues}/{n_groups} groups have unexpected replicate counts")
        print("\nReplicate Validation Report:")
        print("=" * 80)
        print(replicate_counts[replicate_counts['n_replicates'] != expected_replicates].to_string(index=False))
        print("=" * 80)

    return replicate_counts


def save_provenance(
    metadata: dict,
    output_path: Path,
    analysis_id: str,
    data_summary: Optional[dict] = None
) -> None:
    """
    Save analysis provenance JSON from Analysis Summary sheet.

    Parameters
    ----------
    metadata : dict
        Metadata from load_summary()
    output_path : Path
        Output directory for provenance.json
    analysis_id : str
        Analysis identifier
    data_summary : dict, optional
        Additional summary statistics (n_samples, n_features, etc.)
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    provenance_file = output_path / f"{analysis_id}_provenance.json"

    provenance = {
        'analysis_id': analysis_id,
        'metadata': metadata,
    }

    if data_summary:
        provenance['data_summary'] = data_summary

    with open(provenance_file, 'w') as f:
        json.dump(provenance, f, indent=2, default=str)

    logger.debug(f"Saved provenance to {provenance_file}")


def aggregate_scores(
    runs_df: pd.DataFrame,
    cfg: dict,
    io_module
) -> pd.DataFrame:
    """
    Load and aggregate all PCA scores across runs.

    Parameters
    ----------
    runs_df : pd.DataFrame
        Output from scan_pca_runs()
    cfg : dict
        Configuration
    io_module : module
        tofsims.io module (for load_scores)

    Returns
    -------
    pd.DataFrame
        Combined scores with metadata
    """
    all_scores = []

    for _, run in runs_df.iterrows():
        try:
            # Load scores
            scores = io_module.load_scores(
                run['path_scores'],
                cfg['sheets']['scores']
            )

            # Clean metadata
            scores = clean_meta(
                scores,
                analysis_id=run['analysis_id'],
                analysis_type=run['analysis_type'],
                polarity=run['polarity'],
                dose_label=run.get('dose_label'),
                cfg=cfg
            )

            all_scores.append(scores)

        except Exception as e:
            logger.error(f"Failed to load scores for {run['analysis_id']}: {e}")

    if not all_scores:
        logger.error("No scores loaded!")
        return pd.DataFrame()

    combined = pd.concat(all_scores, ignore_index=True)
    logger.info(f"Aggregated {len(combined)} scores from {len(all_scores)} runs")

    return combined


def aggregate_loadings(
    runs_df: pd.DataFrame,
    cfg: dict,
    io_module,
    do_merge_assignments: bool = True
) -> pd.DataFrame:
    """
    Load and aggregate all PCA loadings across runs.

    Optionally merges with fragment assignments.

    Parameters
    ----------
    runs_df : pd.DataFrame
        Output from scan_pca_runs()
    cfg : dict
        Configuration
    io_module : module
        tofsims.io module
    do_merge_assignments : bool
        Whether to merge fragment assignments (default: True)

    Returns
    -------
    pd.DataFrame
        Combined loadings with metadata and assignments
    """
    all_loadings = []

    for _, run in runs_df.iterrows():
        try:
            # Load loadings
            loadings = io_module.load_loadings(
                run['path_loadings'],
                cfg['sheets']['loadings']
            )

            # Clean metadata
            loadings = clean_meta(
                loadings,
                analysis_id=run['analysis_id'],
                analysis_type=run['analysis_type'],
                polarity=run['polarity'],
                dose_label=run.get('dose_label'),
                cfg=cfg
            )

            # Merge assignments if available
            if do_merge_assignments and run['path_assignments']:
                assignments = io_module.load_assignments(run['path_assignments'])
                if len(assignments) > 0:
                    tol_ppm = cfg.get('preprocessing', {}).get('assignment_ppm_tolerance', 10.0)
                    loadings = merge_assignments(loadings, assignments, tol_ppm=tol_ppm)

            all_loadings.append(loadings)

        except Exception as e:
            logger.error(f"Failed to load loadings for {run['analysis_id']}: {e}")

    if not all_loadings:
        logger.error("No loadings loaded!")
        return pd.DataFrame()

    combined = pd.concat(all_loadings, ignore_index=True)
    logger.info(f"Aggregated {len(combined)} loadings from {len(all_loadings)} runs")

    return combined


def aggregate_variance(
    runs_df: pd.DataFrame,
    cfg: dict,
    io_module
) -> pd.DataFrame:
    """
    Load and aggregate variance explained across runs.

    Parameters
    ----------
    runs_df : pd.DataFrame
        Output from scan_pca_runs()
    cfg : dict
        Configuration
    io_module : module
        tofsims.io module

    Returns
    -------
    pd.DataFrame
        Combined variance explained with metadata
    """
    all_variance = []

    for _, run in runs_df.iterrows():
        try:
            # Load variance
            variance = io_module.load_explained(
                run['path_explained'],
                cfg['sheets']['explained']
            )

            # Add metadata
            variance['analysis_id'] = run['analysis_id']
            variance['analysis_type'] = run['analysis_type']
            variance['polarity'] = run['polarity']
            if 'dose_label' in run:
                variance['dose_label'] = run['dose_label']

            all_variance.append(variance)

        except Exception as e:
            logger.error(f"Failed to load variance for {run['analysis_id']}: {e}")

    if not all_variance:
        logger.error("No variance loaded!")
        return pd.DataFrame()

    combined = pd.concat(all_variance, ignore_index=True)
    logger.info(f"Aggregated variance from {len(all_variance)} runs")

    return combined


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("ToF-SIMS Preprocessing Demo")
    print("=" * 60)

    # Test ppm matching
    loadings = pd.DataFrame({
        'mz': [77.0383, 41.0408, 29.0397],
        'loading_PC1': [0.568, -0.371, -0.296]
    })

    assignments = pd.DataFrame({
        'mz': [77.0380, 41.0410],  # Slightly different m/z
        'assignment': ['C6H5+', 'C3H5+'],
        'formula': ['C6H5', 'C3H5'],
        'confidence': ['High', 'High']
    })

    print("\nTest: Fragment assignment merge with ppm tolerance")
    print(f"Loadings:\n{loadings}")
    print(f"\nAssignments:\n{assignments}")

    merged = merge_assignments(loadings, assignments, tol_ppm=10.0)
    print(f"\nMerged ({len(merged)} rows):\n{merged[['mz', 'loading_PC1', 'assignment', 'ppm_error']]}")
