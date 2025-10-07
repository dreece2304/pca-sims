"""
IO layer for ToF-SIMS multi-ion analysis.

Handles loading of:
- PCA outputs (scores, loadings, variance explained)
- Fragment assignments
- Analysis metadata
- Raw intensities (optional, with mapping)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import glob as glob_module

import pandas as pd
import yaml


# Configure logging
logger = logging.getLogger(__name__)


def load_config(config_path: Union[str, Path] = "config/tofsims.yaml") -> dict:
    """
    Load YAML configuration file.

    Parameters
    ----------
    config_path : str or Path
        Path to tofsims.yaml configuration file

    Returns
    -------
    dict
        Parsed configuration dictionary
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)

    logger.info(f"Loaded config from {config_path}")
    return cfg


def scan_pca_runs(cfg: dict) -> pd.DataFrame:
    """
    Scan all PCA analysis runs based on config glob patterns.

    Discovers all analysis files and extracts metadata from paths:
    - analysis_type (pairwise, dose_trajectory, dose_dependent)
    - polarity (positive, negative)
    - dose_label (for pairwise: "2000", "5000", etc.; else "trajectory"/"dependant")

    Parameters
    ----------
    cfg : dict
        Configuration dictionary from load_config()

    Returns
    -------
    pd.DataFrame
        Columns: analysis_id, analysis_type, polarity, dose_label,
                 path_scores, path_loadings, path_explained, path_summary,
                 path_toplist, path_assignments
    """
    runs = []

    analyses = cfg.get('analyses', {})

    for analysis_type, polarities in analyses.items():
        for polarity, patterns in polarities.items():
            # All patterns point to same Excel file for each run
            scores_glob = patterns.get('scores_glob', '')
            assignments_glob = patterns.get('assignments_glob', '')

            # Expand glob pattern for scores (one file per run)
            matched_files = glob_module.glob(scores_glob)

            if not matched_files:
                logger.warning(f"No files found for {analysis_type}/{polarity}: {scores_glob}")
                continue

            for path in matched_files:
                path = Path(path)

                # Extract dose_label from path for pairwise
                if analysis_type == 'pairwise':
                    # Path format: outputs/Pairwise/Positive/10000/pca_analysis.xlsx
                    dose_label = path.parent.name  # "10000"
                elif analysis_type == 'dose_trajectory':
                    dose_label = 'trajectory'
                elif analysis_type == 'dose_dependent':
                    dose_label = 'dependant'
                else:
                    dose_label = 'unknown'

                # Generate analysis_id
                analysis_id = f"{analysis_type}_{polarity}_{dose_label}"

                # Assignments file is sibling to pca_analysis.xlsx
                assignments_path = path.parent / "fragment_assignments.csv"

                run = {
                    'analysis_id': analysis_id,
                    'analysis_type': analysis_type,
                    'polarity': polarity,
                    'dose_label': dose_label,
                    'path_scores': str(path),        # All sheets in same Excel
                    'path_loadings': str(path),
                    'path_explained': str(path),
                    'path_summary': str(path),
                    'path_toplist': str(path),
                    'path_assignments': str(assignments_path) if assignments_path.exists() else None
                }

                runs.append(run)

    runs_df = pd.DataFrame(runs)

    if len(runs_df) == 0:
        logger.warning("No PCA runs found!")
    else:
        logger.info(f"Found {len(runs_df)} PCA runs: "
                   f"{runs_df['analysis_type'].value_counts().to_dict()}")

    return runs_df


def load_scores(
    path: Union[str, Path],
    sheet: str = "PCA Scores",
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load PCA scores from Excel sheet.

    Parameters
    ----------
    path : str or Path
        Path to pca_analysis.xlsx
    sheet : str
        Sheet name (default: "PCA Scores")
    cfg : dict, optional
        Configuration for validation

    Returns
    -------
    pd.DataFrame
        Scores with columns: sample_id (from sample_name), replicate, PC1-PC5, etc.
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet)

        # Rename sample_name to sample_id for consistency
        if 'sample_name' in df.columns:
            df = df.rename(columns={'sample_name': 'sample_id'})

        # Rename replicate_id to replicate for consistency
        if 'replicate_id' in df.columns:
            df = df.rename(columns={'replicate_id': 'replicate'})

        logger.debug(f"Loaded {len(df)} scores from {path}")
        return df

    except Exception as e:
        logger.error(f"Failed to load scores from {path}: {e}")
        raise


def load_loadings(
    path: Union[str, Path],
    sheet: str = "PCA Loadings",
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load PCA loadings from Excel sheet.

    Parameters
    ----------
    path : str or Path
        Path to pca_analysis.xlsx
    sheet : str
        Sheet name (default: "PCA Loadings")
    cfg : dict, optional
        Configuration for validation

    Returns
    -------
    pd.DataFrame
        Loadings with columns: mz (from index), loading_PC1-PC5, rank
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet)

        # Rename 'index' to 'mz' for clarity
        if 'index' in df.columns:
            df = df.rename(columns={'index': 'mz'})

        # Rename PC columns to loading_PC1, loading_PC2, etc.
        rename_map = {}
        for col in df.columns:
            if col.startswith('PC') and col[2:].isdigit():
                pc_num = col[2:]
                rename_map[col] = f'loading_PC{pc_num}'

        df = df.rename(columns=rename_map)

        # Rename ranking column
        if 'PC1_Rank' in df.columns:
            df = df.rename(columns={'PC1_Rank': 'rank'})

        logger.debug(f"Loaded {len(df)} loadings from {path}")
        return df

    except Exception as e:
        logger.error(f"Failed to load loadings from {path}: {e}")
        raise


def load_explained(
    path: Union[str, Path],
    sheet: str = "Variance Explained",
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load variance explained from Excel sheet.

    Parameters
    ----------
    path : str or Path
        Path to pca_analysis.xlsx
    sheet : str
        Sheet name (default: "Variance Explained")
    cfg : dict, optional
        Configuration for validation

    Returns
    -------
    pd.DataFrame
        Variance with columns: component (int), variance_ratio, cumulative_variance
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet)

        # Rename columns for consistency
        rename_map = {
            'Component': 'component',
            'Variance_Explained_Percent': 'variance_pct',
            'Cumulative_Variance_Percent': 'cumulative_pct'
        }
        df = df.rename(columns=rename_map)

        # Convert variance to ratio (0-1 instead of 0-100)
        if 'variance_pct' in df.columns:
            df['variance_ratio'] = df['variance_pct'] / 100.0
        if 'cumulative_pct' in df.columns:
            df['cumulative_variance'] = df['cumulative_pct'] / 100.0

        # Extract PC number from component string (e.g., "PC1" -> 1)
        if 'component' in df.columns and df['component'].dtype == object:
            df['component'] = df['component'].str.replace('PC', '').astype(int)

        logger.debug(f"Loaded {len(df)} variance components from {path}")
        return df

    except Exception as e:
        logger.error(f"Failed to load variance from {path}: {e}")
        raise


def load_summary(
    path: Union[str, Path],
    sheet: str = "Analysis Summary",
    cfg: Optional[dict] = None
) -> dict:
    """
    Load analysis summary metadata from Excel sheet.

    Extracts key metadata for provenance tracking.

    Parameters
    ----------
    path : str or Path
        Path to pca_analysis.xlsx
    sheet : str
        Sheet name (default: "Analysis Summary")
    cfg : dict, optional
        Configuration

    Returns
    -------
    dict
        Metadata dictionary with keys: analysis_id, analysis_type, polarity,
        doses_included, scaling, centering, n_components, date, notes
    """
    try:
        # Read as DataFrame (structure varies, so be flexible)
        df = pd.read_excel(path, sheet_name=sheet, header=None)

        # Try to parse key-value pairs (common format)
        metadata = {}

        for _, row in df.iterrows():
            if len(row) >= 2:
                key = str(row[0]).strip().lower().replace(' ', '_')
                value = row[1]
                metadata[key] = value

        logger.debug(f"Loaded summary metadata from {path}: {list(metadata.keys())}")
        return metadata

    except Exception as e:
        logger.warning(f"Could not load summary from {path}: {e}")
        return {}


def load_toplist(
    path: Union[str, Path],
    sheet: str = "Top 20 Loadings",
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load top loadings list from Excel sheet.

    Parameters
    ----------
    path : str or Path
        Path to pca_analysis.xlsx
    sheet : str
        Sheet name (default: "Top 20 Loadings")
    cfg : dict, optional
        Configuration

    Returns
    -------
    pd.DataFrame
        Top loadings (typically top 20 by PC1)
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet)
        logger.debug(f"Loaded {len(df)} top loadings from {path}")
        return df

    except Exception as e:
        logger.warning(f"Could not load top loadings from {path}: {e}")
        return pd.DataFrame()


def load_assignments(
    csv_path: Union[str, Path],
    cfg: Optional[dict] = None
) -> pd.DataFrame:
    """
    Load fragment assignments from CSV.

    Parameters
    ----------
    csv_path : str or Path
        Path to fragment_assignments.csv
    cfg : dict, optional
        Configuration for validation

    Returns
    -------
    pd.DataFrame
        Assignments with columns: mz, assignment, formula, ppm_error, confidence, etc.
        Returns empty DataFrame if file doesn't exist.
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.warning(f"Assignments file not found: {csv_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_path)

        # Rename 'm/z' to 'mz' for consistency
        if 'm/z' in df.columns:
            df = df.rename(columns={'m/z': 'mz'})

        # Rename 'PC1 Loading' to 'loading_PC1'
        if 'PC1 Loading' in df.columns:
            df = df.rename(columns={'PC1 Loading': 'loading_PC1'})

        # Rename 'Current Assignment' to 'assignment'
        if 'Current Assignment' in df.columns:
            df = df.rename(columns={'Current Assignment': 'assignment'})

        # Rename 'Confidence' to 'confidence'
        if 'Confidence' in df.columns:
            df = df.rename(columns={'Confidence': 'confidence'})

        # Lowercase column names for consistency
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        logger.debug(f"Loaded {len(df)} assignments from {csv_path}")
        return df

    except Exception as e:
        logger.error(f"Failed to load assignments from {csv_path}: {e}")
        return pd.DataFrame()


def scan_intensities(cfg: dict) -> pd.DataFrame:
    """
    Scan raw intensity files (optional, requires mapping).

    This is a placeholder that checks if intensities are enabled and provides
    guidance on required inputs.

    Parameters
    ----------
    cfg : dict
        Configuration dictionary

    Returns
    -------
    pd.DataFrame
        Empty DataFrame with expected schema if mapping not provided.
        Will be implemented when user provides file patterns and mapping.
    """
    intensities_cfg = cfg.get('intensities', {})

    if not intensities_cfg.get('enabled', False):
        logger.info("Intensities loading disabled in config")
        return pd.DataFrame()

    mapping_csv = intensities_cfg.get('mapping_csv', '')

    if not mapping_csv:
        logger.warning(
            "Intensities enabled but mapping_csv not provided. "
            "Please provide:\n"
            "  1. intensities.file_glob pattern (e.g., '*.csv' or '*.parquet')\n"
            "  2. intensities.mapping_csv path (filename -> metadata mapping)\n"
            "Expected columns: sample_id, dose_label, dose_uC_cm2, replicate, polarity, mz, intensity"
        )
        return pd.DataFrame()

    # TODO: Implement when user provides mapping
    logger.info("Intensities loading will be implemented when mapping is provided")
    return pd.DataFrame()


def load_intensities_cache(path: Union[str, Path] = 'results/cache/intensities_long.parquet') -> pd.DataFrame:
    """
    Load cached intensities from parquet file.

    This loads the pre-processed long-format intensities generated by
    scripts/import_matrix_intensities.py.

    Parameters
    ----------
    path : str or Path
        Path to intensities parquet cache (default: results/cache/intensities_long.parquet)

    Returns
    -------
    pd.DataFrame
        Long-format intensities with columns:
        sample_id, dose_label, dose_uC_cm2, replicate, polarity, mz, intensity

        Returns empty DataFrame with correct columns if file doesn't exist.
    """
    path = Path(path)

    if not path.exists():
        logger.debug(f"Intensities cache not found: {path} (optional)")
        # Return empty DataFrame with correct schema
        return pd.DataFrame(columns=[
            'sample_id',
            'dose_label',
            'dose_uC_cm2',
            'replicate',
            'polarity',
            'mz',
            'intensity'
        ])

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded intensities cache: {len(df):,} rows from {path}")
        return df

    except Exception as e:
        logger.error(f"Failed to load intensities from {path}: {e}")
        return pd.DataFrame(columns=[
            'sample_id',
            'dose_label',
            'dose_uC_cm2',
            'replicate',
            'polarity',
            'mz',
            'intensity'
        ])


if __name__ == "__main__":
    # Quick demo/test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("ToF-SIMS IO Layer Demo")
    print("=" * 60)

    # Load config
    cfg = load_config("config/tofsims.yaml")
    print(f"\n✓ Config loaded: {len(cfg)} top-level keys")
    print(f"  Sheet names: {cfg['sheets']}")

    # Scan runs
    runs_df = scan_pca_runs(cfg)
    print(f"\n✓ Found {len(runs_df)} PCA runs")
    print(f"\n{runs_df[['analysis_id', 'analysis_type', 'polarity', 'dose_label']].to_string()}")

    # Load first run as example
    if len(runs_df) > 0:
        first_run = runs_df.iloc[0]
        print(f"\n{'=' * 60}")
        print(f"Loading example run: {first_run['analysis_id']}")
        print(f"{'=' * 60}")

        # Scores
        scores = load_scores(first_run['path_scores'], cfg['sheets']['scores'])
        print(f"\n✓ Scores: {scores.shape}")
        print(f"  Columns: {list(scores.columns)}")

        # Loadings
        loadings = load_loadings(first_run['path_loadings'], cfg['sheets']['loadings'])
        print(f"\n✓ Loadings: {loadings.shape}")
        print(f"  Columns: {list(loadings.columns)}")

        # Variance
        variance = load_explained(first_run['path_explained'], cfg['sheets']['explained'])
        print(f"\n✓ Variance: {variance.shape}")
        print(variance)

        # Summary
        summary = load_summary(first_run['path_summary'], cfg['sheets']['summary'])
        print(f"\n✓ Summary: {len(summary)} metadata fields")

        # Assignments
        if first_run['path_assignments']:
            assignments = load_assignments(first_run['path_assignments'])
            print(f"\n✓ Assignments: {assignments.shape}")
            print(f"  Columns: {list(assignments.columns)}")
