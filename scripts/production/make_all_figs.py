#!/usr/bin/env python3
"""
Generate all ToF-SIMS analysis figures with optional Qt interactive display.

Usage:
    python scripts/make_all_figs.py --analysis-type dose_trajectory --polarity positive --topk 20
    python scripts/make_all_figs.py --analysis-type all --polarity all --topk 20 --show
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from datetime import datetime
from typing import List

import pandas as pd

import tofsims.io as io
import tofsims.figures as figs
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
    """
    Filter runs dataframe by analysis type, polarity, and optional ID.

    Parameters
    ----------
    runs_df : pd.DataFrame
        All runs from scan_pca_runs()
    analysis_type : str
        'pairwise', 'dose_trajectory', 'dose_dependent', or 'all'
    polarity : str
        'positive', 'negative', or 'all'
    analysis_id : str, optional
        Specific analysis ID, or None for first match per type/polarity

    Returns
    -------
    pd.DataFrame
        Filtered runs
    """
    filtered = runs_df.copy()

    # Filter by analysis type
    if analysis_type != 'all':
        filtered = filtered[filtered['analysis_type'] == analysis_type]

    # Filter by polarity
    if polarity != 'all':
        filtered = filtered[filtered['polarity'] == polarity]

    # Filter by analysis_id
    if analysis_id:
        filtered = filtered[filtered['analysis_id'] == analysis_id]
    else:
        # Take first per type/polarity combination
        if analysis_type == 'all' and polarity == 'all':
            # Take all
            pass
        else:
            # Group and take first
            filtered = (
                filtered
                .groupby(['analysis_type', 'polarity'], observed=True, as_index=False)
                .first()
            )

    return filtered


def generate_figures_for_run(
    run: pd.Series,
    cfg: dict,
    topk: int,
    show: bool,
    intensities_df: pd.DataFrame = None
) -> List[Path]:
    """
    Generate all figures for a single analysis run.

    Parameters
    ----------
    run : pd.Series
        Single row from runs_df
    cfg : dict
        Configuration
    topk : int
        Number of top features
    show : bool
        Interactive display
    intensities_df : pd.DataFrame, optional
        Intensities for dose-response plots

    Returns
    -------
    list of Path
        Paths to saved figures
    """
    analysis_id = run['analysis_id']
    analysis_type = run['analysis_type']
    polarity = run['polarity']

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Generating figures for: {analysis_id}")
    logger.info(f"{'=' * 80}")

    # Output directory
    fig_dir = Path(cfg['results']['figures_dir']) / analysis_type / polarity / analysis_id
    fig_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    # Load data
    logger.info("Loading PCA data...")
    scores = io.load_scores(run['path_scores'], cfg['sheets']['scores'])
    loadings = io.load_loadings(run['path_loadings'], cfg['sheets']['loadings'])
    variance = io.load_explained(run['path_explained'], cfg['sheets']['explained'])

    # Add metadata to loadings
    if run['path_assignments']:
        assignments = io.load_assignments(run['path_assignments'])
        if len(assignments) > 0:
            # Merge assignments
            loadings = loadings.merge(
                assignments[['mz', 'assignment', 'confidence']],
                on='mz',
                how='left'
            )

    # 1. PCA Scores plot
    logger.info("Plotting PCA scores...")
    scores_path = fig_dir / 'scores.png'
    figs.plot_pca_scores(
        scores,
        pc_x='PC1',
        pc_y='PC2',
        variance_df=variance,
        color_by='dose_label' if 'dose_label' in scores.columns else 'sample_id',
        save_path=scores_path,
        show=show
    )
    saved_files.append(scores_path)

    # 2. Dose trajectory (if multi-dose)
    if analysis_type in ('dose_trajectory', 'dose_dependent'):
        logger.info("Plotting dose trajectory...")
        traj_path = fig_dir / 'trajectory.png'
        figs.plot_dose_trajectory(
            scores,
            pc='PC1',
            variance_df=variance,
            save_path=traj_path,
            show=show
        )
        saved_files.append(traj_path)

    # 3. Loading bars
    logger.info(f"Plotting top {topk} loadings...")
    loading_path = fig_dir / 'loadings_PC1.png'
    figs.plot_loading_bars(
        loadings,
        pc='PC1',
        k=topk,
        include_sign=True,
        save_path=loading_path,
        show=show
    )
    saved_files.append(loading_path)

    # 4. Intensities-based plots (if available)
    if intensities_df is not None and len(intensities_df) > 0:
        logger.info("Generating intensity-based plots...")

        # Filter to this polarity
        intens_pol = intensities_df[intensities_df['polarity'] == polarity].copy()

        if len(intens_pol) > 0:
            # Select key m/z
            mz_list = tstats.select_key_mz(loadings, pc='PC1', k=topk, include_sign=True)

            # Heatmap
            logger.info("Plotting intensity heatmap...")
            heatmap_path = fig_dir / 'heatmap.png'
            figs.plot_heatmap_intensity(
                intens_pol,
                mz_list,
                loadings_df=loadings,
                save_path=heatmap_path,
                show=show
            )
            saved_files.append(heatmap_path)

            # Dose-response for 3 representative m/z
            # Top positive, top negative, one neutral
            loading_col = 'loading_PC1'
            if loading_col in loadings.columns:
                top_pos = loadings.nlargest(1, loading_col)
                top_neg = loadings.nsmallest(1, loading_col)

                # Neutral: closest to zero
                loadings_abs = loadings.copy()
                loadings_abs['abs_load'] = loadings_abs[loading_col].abs()
                top_neut = loadings_abs.nsmallest(1, 'abs_load')

                representative = pd.concat([top_pos, top_neg, top_neut])

                for _, row in representative.iterrows():
                    mz = row['mz']
                    assignment = row.get('assignment', None)

                    logger.info(f"Plotting dose response for m/z {mz:.4f}...")
                    dr_path = fig_dir / f'dose_response_{mz:.4f}.png'
                    figs.plot_dose_response(
                        intens_pol,
                        mz=mz,
                        assignment=assignment,
                        save_path=dr_path,
                        show=show
                    )
                    saved_files.append(dr_path)

    logger.info(f"\n✓ Generated {len(saved_files)} figures for {analysis_id}")
    for f in saved_files:
        logger.info(f"  {f}")

    return saved_files


def main():
    """Main figure generation workflow."""
    parser = argparse.ArgumentParser(
        description='Generate ToF-SIMS analysis figures with optional Qt interactive display'
    )
    parser.add_argument(
        '--analysis-type',
        choices=['pairwise', 'dose_trajectory', 'dose_dependent', 'all'],
        default='all',
        help='Analysis type to plot (default: all)'
    )
    parser.add_argument(
        '--polarity',
        choices=['positive', 'negative', 'all'],
        default='all',
        help='Polarity to plot (default: all)'
    )
    parser.add_argument(
        '--analysis-id',
        type=str,
        default=None,
        help='Specific analysis ID (optional, defaults to first per type/polarity)'
    )
    parser.add_argument(
        '--topk',
        type=int,
        default=20,
        help='Number of top loadings to plot (default: 20)'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Display figures interactively with Qt backend'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("ToF-SIMS Figure Generation")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analysis type: {args.analysis_type}")
    print(f"Polarity: {args.polarity}")
    print(f"Top k features: {args.topk}")
    print(f"Interactive display: {args.show}")
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
        logger.error(f"No runs match criteria: type={args.analysis_type}, polarity={args.polarity}")
        return

    logger.info(f"\nSelected {len(selected_runs)} runs to process:")
    for _, run in selected_runs.iterrows():
        logger.info(f"  {run['analysis_id']}")

    # Load intensities (optional - not required)
    logger.info("\nLoading intensities cache (optional)...")
    try:
        intensities_df = io.load_intensities_cache()
        if len(intensities_df) > 0:
            logger.info(f"  ✓ Loaded {len(intensities_df)} intensity records")
        else:
            logger.info("  No intensities found. Skipping intensity-based plots (optional).")
            intensities_df = pd.DataFrame()
    except Exception as e:
        logger.info(f"  Intensities not available (optional): {e}")
        intensities_df = pd.DataFrame()

    # Generate figures for each run
    all_saved_files = []

    for idx, run in selected_runs.iterrows():
        try:
            saved_files = generate_figures_for_run(
                run,
                cfg,
                topk=args.topk,
                show=args.show,
                intensities_df=intensities_df
            )
            all_saved_files.extend(saved_files)

        except Exception as e:
            logger.error(f"Failed to generate figures for {run['analysis_id']}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("FIGURE GENERATION SUMMARY")
    print("=" * 80)
    print(f"Runs processed: {len(selected_runs)}")
    print(f"Total figures: {len(all_saved_files)}")
    print()
    print("Saved files:")
    for f in all_saved_files[:20]:  # Show first 20
        print(f"  {f}")
    if len(all_saved_files) > 20:
        print(f"  ... and {len(all_saved_files) - 20} more")
    print()

    if args.show:
        print("Interactive display mode: Qt windows should have opened")
        print("(If no windows appeared, Qt backend may not be available)")
    else:
        print("Headless mode: Figures saved to disk only")

    print()
    print("=" * 80)
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Figure generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
