#!/usr/bin/env python3
"""
Import matrix-format ToF-SIMS intensities from text files.

Reads fixed-layout intensity matrices with:
  - Column 1: m/z values
  - Columns 2-19: Intensities for SQ0-SQ5 × P1-P3 (18 samples)

Layout: SQ0_P1, SQ0_P2, SQ0_P3, SQ1_P1, ..., SQ5_P3

Rules:
  - SQ0 = as-deposited (dose=0)
  - SQ1 = EXCLUDE entirely
  - SQ2 = 2000 µC/cm²
  - SQ3 = 5000 µC/cm²
  - SQ4 = 10000 µC/cm²
  - SQ5 = 15000 µC/cm²
  - P1/P2/P3 = replicates 1/2/3

Outputs:
  - results/cache/intensities_long.parquet (full dataset)
  - results/cache/intensities_long_head.csv (preview, 200 rows)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Fixed layout: SQ groups and replicates
# Actual column order in files: P1_SQ1, P1_SQ2, ..., P1_SQ5, P2_SQ1, ..., P3_SQ5, P1_SQ0, P2_SQ0, P3_SQ0
# (SQ0 comes LAST in the file)
SQ_GROUPS_ORDERED = ['SQ1', 'SQ2', 'SQ3', 'SQ4', 'SQ5', 'SQ0']  # Order as they appear in file
REPLICATES = ['P1', 'P2', 'P3']

# Dose mapping
DOSE_MAPPING = {
    'SQ0': ('0', 0.0),
    'SQ1': ('EXCLUDE', None),  # Will be dropped
    'SQ2': ('2000', 2000.0),
    'SQ3': ('5000', 5000.0),
    'SQ4': ('10000', 10000.0),
    'SQ5': ('15000', 15000.0)
}

# Expected columns: 1 m/z + 18 intensities (but file has header, so we'll use header=0)
EXPECTED_INTENSITY_COLS = 18


def load_matrix_file(file_path: Path, polarity: str) -> pd.DataFrame:
    """
    Load intensity matrix from whitespace-delimited text file.

    Parameters
    ----------
    file_path : Path
        Path to intensity matrix file
    polarity : str
        'positive' or 'negative'

    Returns
    -------
    pd.DataFrame
        Long-format intensities with columns:
        sample_id, dose_label, dose_uC_cm2, replicate, polarity, mz, intensity
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return pd.DataFrame()

    logger.info(f"Loading {polarity} intensities from {file_path}")

    # Read as tab-delimited with header row
    try:
        df_wide = pd.read_csv(
            file_path,
            sep='\t',
            header=0,
            skip_blank_lines=True,
            comment='#'
        )
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return pd.DataFrame()

    # Validate column count (1 m/z + 18 intensities)
    if df_wide.shape[1] != (EXPECTED_INTENSITY_COLS + 1):
        raise ValueError(
            f"Expected {EXPECTED_INTENSITY_COLS + 1} columns (1 m/z + {EXPECTED_INTENSITY_COLS} intensities), "
            f"got {df_wide.shape[1]} in {file_path}\n"
            f"Expected layout: Mass (u), P1_SQ1, P1_SQ2, ..., P3_SQ0"
        )

    # Rename first column to 'mz' for consistency
    df_wide.columns = ['mz'] + list(df_wide.columns[1:])

    logger.info(f"  Read {len(df_wide)} m/z features × {EXPECTED_INTENSITY_COLS} samples")

    # Convert m/z to float
    df_wide['mz'] = pd.to_numeric(df_wide['mz'], errors='coerce')

    # Drop rows with invalid m/z
    n_before = len(df_wide)
    df_wide = df_wide.dropna(subset=['mz'])
    n_dropped = n_before - len(df_wide)
    if n_dropped > 0:
        logger.warning(f"  Dropped {n_dropped} rows with invalid m/z")

    # Drop SQ1 columns (exclude this group)
    # Columns are P{replicate}_SQ1 format
    sq1_cols = [f'{rep}_SQ1' for rep in REPLICATES]
    df_wide = df_wide.drop(columns=sq1_cols)
    logger.info(f"  Excluded SQ1 group ({len(sq1_cols)} columns)")

    # Reshape to long format
    id_vars = ['mz']
    value_vars = [col for col in df_wide.columns if col != 'mz']

    df_long = df_wide.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='sample_col',
        value_name='intensity'
    )

    # Parse sample_col into replicate and SQ group
    # Format: P1_SQ0 -> P1, SQ0 (replicate first, then SQ group)
    df_long[['replicate_code', 'sq_group']] = df_long['sample_col'].str.split('_', expand=True)

    # Map SQ group to dose_label and dose_uC_cm2
    def map_dose(sq):
        label, dose = DOSE_MAPPING.get(sq, (None, None))
        return pd.Series({'dose_label': label, 'dose_uC_cm2': dose})

    dose_info = df_long['sq_group'].apply(map_dose)
    df_long = pd.concat([df_long, dose_info], axis=1)

    # Map replicate code (P1/P2/P3 -> 1/2/3)
    replicate_map = {'P1': 1, 'P2': 2, 'P3': 3}
    df_long['replicate'] = df_long['replicate_code'].map(replicate_map)

    # Build sample_id: {polarity}_{replicate_code}_{sq_group}
    # e.g., "negative_P1_SQ4" to match the column format
    df_long['sample_id'] = polarity + '_' + df_long['replicate_code'] + '_' + df_long['sq_group']

    # Add polarity
    df_long['polarity'] = polarity

    # Select and order final columns
    df_long = df_long[[
        'sample_id',
        'dose_label',
        'dose_uC_cm2',
        'replicate',
        'polarity',
        'mz',
        'intensity'
    ]]

    # Drop rows with NaN or negative intensities
    n_before = len(df_long)
    df_long = df_long.dropna(subset=['intensity'])
    df_long = df_long[df_long['intensity'] >= 0]
    n_dropped = n_before - len(df_long)
    if n_dropped > 0:
        logger.warning(f"  Dropped {n_dropped} rows with NaN or negative intensities")

    # Convert dtypes
    df_long['dose_label'] = df_long['dose_label'].astype(str)
    df_long['dose_uC_cm2'] = df_long['dose_uC_cm2'].astype(float)
    df_long['replicate'] = df_long['replicate'].astype(int)
    df_long['polarity'] = pd.Categorical(df_long['polarity'], categories=['positive', 'negative'])
    df_long['mz'] = df_long['mz'].astype(float)
    df_long['intensity'] = df_long['intensity'].astype(float)

    logger.info(f"  Reshaped to long format: {len(df_long)} rows")

    return df_long


def validate_and_summarize(df: pd.DataFrame) -> dict:
    """
    Validate intensities data and compute summary statistics.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format intensities

    Returns
    -------
    dict
        Summary statistics
    """
    summary = {}

    # Per-polarity stats
    for polarity in df['polarity'].unique():
        pol_df = df[df['polarity'] == polarity]

        # Unique doses (exclude SQ1)
        doses = sorted(pol_df['dose_label'].unique())

        # Count samples per dose
        replicate_counts = (
            pol_df
            .groupby(['dose_label', 'replicate'], observed=True)
            .size()
            .reset_index(name='count')
        )

        # Get unique SQ groups
        sq_groups = sorted(pol_df['sample_id'].str.extract(r'(SQ\d+)', expand=False).unique())

        summary[polarity] = {
            'n_rows': len(pol_df),
            'n_mz': pol_df['mz'].nunique(),
            'n_samples': pol_df['sample_id'].nunique(),
            'sq_groups': sq_groups,
            'doses': doses,
            'replicate_counts': replicate_counts,
            'mz_range': (pol_df['mz'].min(), pol_df['mz'].max()),
            'intensity_range': (pol_df['intensity'].min(), pol_df['intensity'].max()),
            'intensity_median': pol_df['intensity'].median()
        }

    # Overall stats
    summary['combined'] = {
        'n_rows': len(df),
        'n_mz': df['mz'].nunique(),
        'n_samples': df['sample_id'].nunique(),
        'polarities': df['polarity'].unique().tolist(),
        'doses': sorted(df['dose_label'].unique())
    }

    return summary


def main():
    """Main import workflow."""
    print("=" * 80)
    print("ToF-SIMS Matrix Intensities Import")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Input files
    neg_file = Path('data/NegativeIon/NegAllCompoundSearch.txt')
    pos_file = Path('data/PositiveIon/PosAllCompoundSearch.txt')

    # Output files
    cache_dir = Path('results/cache')
    cache_dir.mkdir(parents=True, exist_ok=True)

    output_parquet = cache_dir / 'intensities_long.parquet'
    output_csv_preview = cache_dir / 'intensities_long_head.csv'

    # Load negative intensities
    df_neg = load_matrix_file(neg_file, 'negative')

    # Load positive intensities
    df_pos = load_matrix_file(pos_file, 'positive')

    # Combine
    dfs = []
    if len(df_neg) > 0:
        dfs.append(df_neg)
    if len(df_pos) > 0:
        dfs.append(df_pos)

    if len(dfs) == 0:
        logger.error("No intensity data loaded! Check file paths.")
        return

    df_combined = pd.concat(dfs, ignore_index=True)

    logger.info(f"\nCombined {len(dfs)} polarity datasets")

    # Validate and summarize
    summary = validate_and_summarize(df_combined)

    # Print summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)

    for polarity in ['negative', 'positive']:
        if polarity in summary:
            s = summary[polarity]
            print(f"\n{polarity.upper()}:")
            print(f"  SQ groups: {', '.join(s['sq_groups'])} (SQ1 excluded)")
            print(f"  Doses: {', '.join(s['doses'])} µC/cm²")
            print(f"  Samples: {s['n_samples']} (3 replicates each)")
            print(f"  m/z features: {s['n_mz']}")
            print(f"  m/z range: {s['mz_range'][0]:.4f} - {s['mz_range'][1]:.4f}")
            print(f"  Intensity range: {s['intensity_range'][0]:.2e} - {s['intensity_range'][1]:.2e}")
            print(f"  Intensity median: {s['intensity_median']:.2e}")
            print(f"  Total rows: {s['n_rows']:,}")

            # Replicate counts
            rep_counts = s['replicate_counts']
            n_expected = len(s['doses']) * 3  # 3 replicates per dose
            n_actual = len(rep_counts)
            if n_actual == n_expected:
                print(f"  Replicate validation: ✓ {n_expected} samples (3 per dose)")
            else:
                print(f"  Replicate validation: ⚠ Expected {n_expected}, found {n_actual}")

    print(f"\nCOMBINED:")
    s = summary['combined']
    print(f"  Polarities: {', '.join(s['polarities'])}")
    print(f"  Doses present: {', '.join(s['doses'])}")
    print(f"  Total samples: {s['n_samples']}")
    print(f"  Total m/z: {s['n_mz']}")
    print(f"  Shape: {s['n_rows']:,} rows × 7 columns")

    # Save parquet
    logger.info(f"\nSaving to {output_parquet}...")
    df_combined.to_parquet(output_parquet, compression='snappy', index=False)
    file_size = output_parquet.stat().st_size / 1024  # KB
    logger.info(f"  ✓ Saved: {output_parquet} ({file_size:.1f} KB)")

    # Save CSV preview (first 200 rows)
    logger.info(f"Saving preview to {output_csv_preview}...")
    df_combined.head(200).to_csv(output_csv_preview, index=False)
    logger.info(f"  ✓ Saved: {output_csv_preview} (200 rows)")

    print("\n" + "=" * 80)
    print("FILES CREATED:")
    print("=" * 80)
    print(f"  {output_parquet} ({file_size:.1f} KB)")
    print(f"  {output_csv_preview} (preview)")

    print("\n" + "=" * 80)
    print(f"✓ Import complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
