#!/usr/bin/env python3
"""
Run statistical analyses on ToF-SIMS PCA outputs.

Analyzes:
- PCA scores (dose group differences, trajectories)
- PCA loadings (significance, fragment families)
- Fragment chemistry patterns

Usage:
    python scripts/run_stats.py --analysis-type pairwise --polarity positive --topk 30
    python scripts/run_stats.py --analysis-type dose_trajectory --polarity all
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from datetime import datetime

import pandas as pd
import numpy as np

import tofsims.io as io
import tofsims.stats as tstats


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def select_runs(
    runs_df: pd.DataFrame,
    analysis_type: str,
    polarity: str,
    analysis_id: str = None
) -> pd.DataFrame:
    """Filter runs by criteria."""
    filtered = runs_df.copy()

    if analysis_type != 'all':
        filtered = filtered[filtered['analysis_type'] == analysis_type]

    if polarity != 'all':
        filtered = filtered[filtered['polarity'] == polarity]

    if analysis_id:
        filtered = filtered[filtered['analysis_id'] == analysis_id]
    else:
        # Take first per type/polarity if not specified
        if analysis_type == 'all' and polarity == 'all':
            pass  # Take all
        else:
            filtered = (
                filtered
                .groupby(['analysis_type', 'polarity'], observed=True, as_index=False)
                .first()
            )

    return filtered


def run_pca_stats(
    run: pd.Series,
    cfg: dict,
    topk: int,
    alpha: float
) -> dict:
    """
    Run statistical analysis on PCA outputs for one analysis.

    Parameters
    ----------
    run : pd.Series
        Single run metadata
    cfg : dict
        Configuration
    topk : int
        Number of top loadings to analyze
    alpha : float
        Significance level

    Returns
    -------
    dict
        Summary statistics
    """
    analysis_id = run['analysis_id']
    analysis_type = run['analysis_type']
    polarity = run['polarity']

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Analyzing PCA outputs: {analysis_id}")
    logger.info(f"{'=' * 80}")

    # Output directory
    tables_dir = Path(cfg['results']['tables_dir']) / analysis_type / polarity / analysis_id
    tables_dir.mkdir(parents=True, exist_ok=True)

    # Load PCA outputs
    logger.info("Loading PCA data...")
    scores = io.load_scores(run['path_scores'], cfg['sheets']['scores'])
    loadings = io.load_loadings(run['path_loadings'], cfg['sheets']['loadings'])
    variance = io.load_explained(run['path_explained'], cfg['sheets']['explained'])

    # Load assignments
    if run['path_assignments']:
        assignments = io.load_assignments(run['path_assignments'])
        if len(assignments) > 0:
            loadings = loadings.merge(
                assignments[['mz', 'assignment', 'confidence']],
                on='mz',
                how='left'
            )

    # ==== 1. SCORES STATISTICS ====
    logger.info("\n--- PCA Scores Analysis ---")

    # Test for dose group differences
    if 'dose_label' in scores.columns:
        scores_result = tstats.scores_anova(
            scores,
            pc='PC1',
            grouping_col='dose_label',
            test='kruskal',
            alpha=alpha
        )

        # Save scores statistics
        if scores_result:
            scores_stats = pd.DataFrame([scores_result])
            scores_path = tables_dir / 'scores_anova.csv'
            scores_stats.to_csv(scores_path, index=False)
            logger.info(f"  ✓ Saved: {scores_path}")

    # Dose trajectory (if applicable)
    if analysis_type in ('dose_trajectory', 'dose_dependent'):
        if 'actual_dose' in scores.columns:
            traj_result = tstats.scores_trajectory(
                scores,
                pc='PC1',
                dose_col='actual_dose'
            )

            if traj_result:
                traj_stats = pd.DataFrame([traj_result])
                traj_path = tables_dir / 'trajectory_stats.csv'
                traj_stats.to_csv(traj_path, index=False)
                logger.info(f"  ✓ Saved: {traj_path}")

    # ==== 2. LOADINGS STATISTICS ====
    logger.info("\n--- PCA Loadings Analysis ---")

    # Add fragment families
    loadings = tstats.group_by_fragment_family(loadings)

    # Mark significant loadings
    loadings = tstats.loadings_significance(
        loadings,
        pc='PC1',
        threshold=0.1,
        top_k=topk
    )

    # Save loadings with significance
    loadings_path = tables_dir / 'loadings_analysis.csv'
    loadings.to_csv(loadings_path, index=False)
    logger.info(f"  ✓ Saved: {loadings_path}")

    # ==== 3. FRAGMENT FAMILY SUMMARY ====
    logger.info("\n--- Fragment Family Analysis ---")

    family_summary = tstats.fragment_family_summary(loadings, pc='PC1')

    if len(family_summary) > 0:
        family_path = tables_dir / 'fragment_families.csv'
        family_summary.to_csv(family_path, index=False)
        logger.info(f"  ✓ Saved: {family_path}")

    # ==== SUMMARY ====
    n_significant = loadings['significant'].sum()
    n_assigned = loadings['assignment'].notna().sum()

    summary = {
        'analysis_id': analysis_id,
        'analysis_type': analysis_type,
        'polarity': polarity,
        'n_features': len(loadings),
        'n_significant': n_significant,
        'n_assigned': n_assigned,
        'pct_assigned': n_assigned / len(loadings) * 100 if len(loadings) > 0 else 0,
        'n_families': family_summary['fragment_family'].nunique() if len(family_summary) > 0 else 0
    }

    logger.info(f"\n✓ Analysis complete for {analysis_id}")

    return summary


def main():
    """Main statistics workflow."""
    parser = argparse.ArgumentParser(
        description='Statistical analysis of ToF-SIMS PCA outputs'
    )
    parser.add_argument(
        '--analysis-type',
        choices=['pairwise', 'dose_trajectory', 'dose_dependent', 'all'],
        default='all',
        help='Analysis type (default: all)'
    )
    parser.add_argument(
        '--polarity',
        choices=['positive', 'negative', 'all'],
        default='all',
        help='Polarity (default: all)'
    )
    parser.add_argument(
        '--analysis-id',
        type=str,
        default=None,
        help='Specific analysis ID (optional)'
    )
    parser.add_argument(
        '--topk',
        type=int,
        default=30,
        help='Number of top loadings to analyze (default: 30)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("ToF-SIMS PCA Statistical Analysis")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analysis type: {args.analysis_type}")
    print(f"Polarity: {args.polarity}")
    print(f"Top k loadings: {args.topk}")
    print(f"Significance level: {args.alpha}")
    print()

    # Load config
    logger.info("Loading configuration...")
    cfg = io.load_config('config/tofsims.yaml')

    # Scan runs
    logger.info("Scanning PCA runs...")
    runs_df = io.scan_pca_runs(cfg)

    if len(runs_df) == 0:
        logger.error("No PCA runs found!")
        return

    # Select runs
    selected_runs = select_runs(runs_df, args.analysis_type, args.polarity, args.analysis_id)

    if len(selected_runs) == 0:
        logger.error(f"No runs match criteria")
        return

    logger.info(f"\nSelected {len(selected_runs)} runs to process:")
    for _, run in selected_runs.iterrows():
        logger.info(f"  {run['analysis_id']}")

    # Run statistics for each
    all_summaries = []

    for idx, run in selected_runs.iterrows():
        try:
            summary = run_pca_stats(
                run,
                cfg,
                topk=args.topk,
                alpha=args.alpha
            )
            all_summaries.append(summary)

        except Exception as e:
            logger.error(f"Failed for {run['analysis_id']}: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Runs processed: {len(all_summaries)}")
    print()

    for summary in all_summaries:
        print(f"{summary['polarity']}/{summary['analysis_type']}/{summary['analysis_id']}")
        print(f"  Features: {summary['n_features']}")
        print(f"  Significant: {summary['n_significant']} (top {args.topk})")
        print(f"  Assigned: {summary['n_assigned']} ({summary['pct_assigned']:.1f}%)")
        print(f"  Fragment families: {summary['n_families']}")
        print()

    print("=" * 80)
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
