#!/usr/bin/env python3
"""
Cache PCA results to unified parquet files.

Workflow:
1. Scan all PCA runs from outputs/
2. Load scores, loadings, variance for each run
3. Clean metadata and merge assignments
4. Validate replicates
5. Save to results/cache/ as parquet
6. Generate provenance JSONs
7. Print summary statistics

Usage:
    python scripts/cache_pca.py [--config config/tofsims.yaml]
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from datetime import datetime

import pandas as pd

import tofsims.io as io
import tofsims.preprocess as preprocess


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main(config_path: str = "config/tofsims.yaml"):
    """
    Main cache generation workflow.

    Parameters
    ----------
    config_path : str
        Path to YAML configuration file
    """
    print("=" * 80)
    print("ToF-SIMS PCA Cache Generation")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Config: {config_path}")
    print()

    # ===== 1. Load Config =====
    logger.info("Loading configuration...")
    cfg = io.load_config(config_path)

    # Create results directories
    results_dirs = [
        cfg['results']['cache_dir'],
        cfg['results']['tables_dir'],
        cfg['results']['figures_dir']
    ]

    for d in results_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"  Ensured directory exists: {d}")

    # ===== 2. Scan Runs =====
    logger.info("\nScanning PCA runs...")
    runs_df = io.scan_pca_runs(cfg)

    if len(runs_df) == 0:
        logger.error("No PCA runs found! Check glob patterns in config.")
        return

    print()
    print("=" * 80)
    print(f"Found {len(runs_df)} PCA runs:")
    print("=" * 80)
    print(runs_df[['analysis_id', 'analysis_type', 'polarity', 'dose_label']].to_string(index=False))
    print()

    # Summary by analysis type and polarity
    summary = runs_df.groupby(['analysis_type', 'polarity'], observed=True).size().reset_index(name='n_runs')
    print("Summary by analysis type and polarity:")
    print(summary.to_string(index=False))
    print()

    # ===== 3. Aggregate Scores =====
    logger.info("\nAggregating PCA scores...")
    scores_df = preprocess.aggregate_scores(runs_df, cfg, io)

    print(f"  Total scores: {len(scores_df)}")
    print(f"  Columns: {list(scores_df.columns)}")

    # ===== 4. Aggregate Loadings =====
    logger.info("\nAggregating PCA loadings (with assignments)...")
    loadings_df = preprocess.aggregate_loadings(runs_df, cfg, io, do_merge_assignments=True)

    print(f"  Total loadings: {len(loadings_df)}")
    print(f"  Columns: {list(loadings_df.columns)}")

    if 'assignment' in loadings_df.columns:
        n_assigned = loadings_df['assignment'].notna().sum()
        pct_assigned = n_assigned / len(loadings_df) * 100
        print(f"  Assignments: {n_assigned}/{len(loadings_df)} ({pct_assigned:.1f}%)")

        if 'assignment_conflict' in loadings_df.columns:
            n_conflicts = loadings_df['assignment_conflict'].sum()
            print(f"  Conflicts: {n_conflicts}")

    # ===== 5. Aggregate Variance =====
    logger.info("\nAggregating variance explained...")
    variance_df = preprocess.aggregate_variance(runs_df, cfg, io)

    print(f"  Total variance records: {len(variance_df)}")
    print(f"  Columns: {list(variance_df.columns)}")

    # ===== 6. Validate Replicates =====
    logger.info("\nValidating replicates...")
    expected_replicates = cfg.get('preprocessing', {}).get('expected_replicates', 3)
    replicate_validation = preprocess.validate_replicates(scores_df, expected_replicates)

    # ===== 7. Save Cache Files =====
    cache_dir = Path(cfg['results']['cache_dir'])

    logger.info(f"\nSaving cache files to {cache_dir}...")

    # Scores
    scores_file = cache_dir / "scores_merged.parquet"
    scores_df.to_parquet(scores_file, compression='snappy', index=False)
    logger.info(f"  ✓ Saved: {scores_file} ({scores_df.shape[0]} rows)")

    # Loadings
    loadings_file = cache_dir / "loadings_merged.parquet"
    loadings_df.to_parquet(loadings_file, compression='snappy', index=False)
    logger.info(f"  ✓ Saved: {loadings_file} ({loadings_df.shape[0]} rows)")

    # Variance
    variance_file = cache_dir / "variance_explained.parquet"
    variance_df.to_parquet(variance_file, compression='snappy', index=False)
    logger.info(f"  ✓ Saved: {variance_file} ({variance_df.shape[0]} rows)")

    # Replicate validation
    replicate_file = cache_dir / "replicate_validation.csv"
    replicate_validation.to_csv(replicate_file, index=False)
    logger.info(f"  ✓ Saved: {replicate_file}")

    # ===== 8. Save Provenance =====
    logger.info("\nSaving provenance metadata...")

    for _, run in runs_df.iterrows():
        try:
            # Load summary metadata
            metadata = io.load_summary(
                run['path_summary'],
                cfg['sheets']['summary']
            )

            # Add data summary
            run_scores = scores_df[scores_df['analysis_id'] == run['analysis_id']]
            run_loadings = loadings_df[loadings_df['analysis_id'] == run['analysis_id']]

            pc_pattern = r'^PC\d+$'
            data_summary = {
                'n_samples': len(run_scores),
                'n_features': len(run_loadings['mz'].unique()) if 'mz' in run_loadings.columns else 0,
                'n_components': run_scores.filter(regex=pc_pattern).shape[1],
                'cache_date': datetime.now().isoformat()
            }

            # Save provenance JSON
            tables_dir = Path(cfg['results']['tables_dir'])
            analysis_dir = tables_dir / run['analysis_type'] / run['polarity']

            preprocess.save_provenance(
                metadata=metadata,
                output_path=analysis_dir,
                analysis_id=run['analysis_id'],
                data_summary=data_summary
            )

        except Exception as e:
            logger.warning(f"Could not save provenance for {run['analysis_id']}: {e}")

    # ===== 9. Summary Statistics =====
    print()
    print("=" * 80)
    print("CACHE GENERATION SUMMARY")
    print("=" * 80)
    print()

    print(f"Runs processed: {len(runs_df)}")
    print(f"  by analysis_type:")
    for analysis_type, count in runs_df['analysis_type'].value_counts().items():
        print(f"    {analysis_type}: {count}")
    print(f"  by polarity:")
    for polarity, count in runs_df['polarity'].value_counts().items():
        print(f"    {polarity}: {count}")
    print()

    print(f"Scores: {len(scores_df)} rows")
    print(f"  Unique samples: {scores_df['sample_id'].nunique() if 'sample_id' in scores_df.columns else 'N/A'}")
    pc_cols = scores_df.filter(regex=r'^PC\d+$').shape[1]
    print(f"  PCs captured: {pc_cols}")
    print()

    print(f"Loadings: {len(loadings_df)} rows")
    print(f"  Unique m/z: {loadings_df['mz'].nunique() if 'mz' in loadings_df.columns else 'N/A'}")
    if 'assignment' in loadings_df.columns:
        n_assigned = loadings_df['assignment'].notna().sum()
        pct = n_assigned / len(loadings_df) * 100
        print(f"  Assigned: {n_assigned}/{len(loadings_df)} ({pct:.1f}%)")
    print()

    print(f"Variance: {len(variance_df)} records")
    print()

    print("Files saved:")
    print(f"  {scores_file}")
    print(f"  {loadings_file}")
    print(f"  {variance_file}")
    print(f"  {replicate_file}")
    print()

    # Replicate validation summary
    n_groups = len(replicate_validation)
    n_ok = (replicate_validation['n_replicates'] == expected_replicates).sum()
    n_issues = n_groups - n_ok

    print(f"Replicate validation: {n_ok}/{n_groups} groups OK")
    if n_issues > 0:
        print(f"  ⚠ {n_issues} groups with unexpected replicate counts")
        print(f"  See: {replicate_file}")

    print()
    print("=" * 80)
    print(f"✓ Cache generation complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cache ToF-SIMS PCA results to unified parquet files"
    )
    parser.add_argument(
        '--config',
        default='config/tofsims.yaml',
        help='Path to configuration YAML (default: config/tofsims.yaml)'
    )

    args = parser.parse_args()

    try:
        main(args.config)
    except Exception as e:
        logger.error(f"Cache generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
