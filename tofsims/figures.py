"""
Plotting functions for ToF-SIMS analysis with Qt interactive support.

All plotting functions accept a `show` parameter for interactive display.
When show=True, attempts to use Qt backend and call plt.show().
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List, Union
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.axes import Axes


logger = logging.getLogger(__name__)


def _maybe_set_qt_backend(enable_show: bool):
    """
    Attempt to set Qt backend for interactive display.

    Only switches if not already using an interactive backend.
    Falls back gracefully if Qt not available.

    Parameters
    ----------
    enable_show : bool
        Whether to enable interactive backend
    """
    if not enable_show:
        return

    try:
        # Check if already using interactive backend
        current_backend = mpl.get_backend().lower()
        if current_backend in ('qt5agg', 'qtagg', 'tkagg', 'wx', 'gtk3agg'):
            logger.debug(f"Already using interactive backend: {current_backend}")
            return

        # Try to switch to Qt
        mpl.use('QtAgg', force=True)
        logger.info("Switched to QtAgg backend for interactive display")

    except Exception as e:
        logger.warning(f"Qt backend not available: {e}. Proceeding headless.")


def _save_or_show(
    fig: Figure,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    **savefig_kwargs
) -> None:
    """
    Save and/or show a figure.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure
    save_path : str or Path, optional
        Path to save figure
    show : bool
        Whether to display interactively
    **savefig_kwargs
        Additional arguments for savefig
    """
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to use utils.plotting.savefig if available
        try:
            from utils import plotting
            plotting.savefig(fig, save_path, **savefig_kwargs)
            logger.info(f"Saved figure: {save_path}")
        except ImportError:
            # Fallback to matplotlib savefig
            default_kwargs = {'dpi': 300, 'bbox_inches': 'tight'}
            default_kwargs.update(savefig_kwargs)
            fig.savefig(save_path, **default_kwargs)
            logger.info(f"Saved figure: {save_path}")

    if show:
        plt.show()


def plot_pca_scores(
    scores_df: pd.DataFrame,
    pc_x: str = 'PC1',
    pc_y: str = 'PC2',
    variance_df: Optional[pd.DataFrame] = None,
    color_by: str = 'dose_label',
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (8, 6)
) -> Tuple[Figure, Axes]:
    """
    Plot PCA scores with variance explained in axis labels.

    Parameters
    ----------
    scores_df : pd.DataFrame
        Scores dataframe with PC1, PC2, etc.
    pc_x : str
        PC for x-axis (default: PC1)
    pc_y : str
        PC for y-axis (default: PC2)
    variance_df : pd.DataFrame, optional
        Variance explained dataframe
    color_by : str
        Column to color points by (default: dose_label)
    save_path : str or Path, optional
        Path to save figure
    show : bool
        Whether to display interactively
    figsize : tuple
        Figure size in inches

    Returns
    -------
    fig, ax : Figure, Axes
    """
    _maybe_set_qt_backend(show)

    fig, ax = plt.subplots(figsize=figsize)

    # Get variance explained for axis labels
    var_x = None
    var_y = None
    if variance_df is not None:
        pc_x_num = int(pc_x.replace('PC', ''))
        pc_y_num = int(pc_y.replace('PC', ''))
        var_x_row = variance_df[variance_df['component'] == pc_x_num]
        var_y_row = variance_df[variance_df['component'] == pc_y_num]
        if len(var_x_row) > 0:
            var_x = var_x_row['variance_ratio'].iloc[0] * 100
        if len(var_y_row) > 0:
            var_y = var_y_row['variance_ratio'].iloc[0] * 100

    # Scatter plot
    if color_by in scores_df.columns:
        for group in scores_df[color_by].unique():
            mask = scores_df[color_by] == group
            ax.scatter(
                scores_df.loc[mask, pc_x],
                scores_df.loc[mask, pc_y],
                label=str(group),
                s=100,
                alpha=0.7,
                edgecolors='k',
                linewidths=0.5
            )
        ax.legend(title=color_by.replace('_', ' ').title(), frameon=True)
    else:
        ax.scatter(
            scores_df[pc_x],
            scores_df[pc_y],
            s=100,
            alpha=0.7,
            edgecolors='k',
            linewidths=0.5
        )

    # Axis labels with variance
    xlabel = pc_x
    ylabel = pc_y
    if var_x is not None:
        xlabel = f"{pc_x} ({var_x:.1f}%)"
    if var_y is not None:
        ylabel = f"{pc_y} ({var_y:.1f}%)"

    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title('PCA Scores Plot', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(0, color='k', linewidth=0.5, linestyle='-', alpha=0.3)
    ax.axvline(0, color='k', linewidth=0.5, linestyle='-', alpha=0.3)

    plt.tight_layout()

    _save_or_show(fig, save_path, show)

    return fig, ax


def plot_dose_trajectory(
    scores_df: pd.DataFrame,
    pc: str = 'PC1',
    variance_df: Optional[pd.DataFrame] = None,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (10, 6)
) -> Tuple[Figure, Axes]:
    """
    Plot dose trajectory showing PC scores vs dose.

    Parameters
    ----------
    scores_df : pd.DataFrame
        Scores with dose_uC_cm2 and PC columns
    pc : str
        Principal component to plot (default: PC1)
    variance_df : pd.DataFrame, optional
        Variance explained
    save_path : str or Path, optional
        Save path
    show : bool
        Interactive display
    figsize : tuple
        Figure size

    Returns
    -------
    fig, ax : Figure, Axes
    """
    _maybe_set_qt_backend(show)

    fig, ax = plt.subplots(figsize=figsize)

    # Get variance explained
    var_expl = None
    if variance_df is not None:
        pc_num = int(pc.replace('PC', ''))
        var_row = variance_df[variance_df['component'] == pc_num]
        if len(var_row) > 0:
            var_expl = var_row['variance_ratio'].iloc[0] * 100

    # Determine dose column (try dose_uC_cm2, then actual_dose)
    dose_col = None
    for col in ['dose_uC_cm2', 'actual_dose', 'dose']:
        if col in scores_df.columns:
            dose_col = col
            break

    if dose_col is None:
        logger.warning("No dose column found in scores_df")
        dose_col = 'dose_label'  # Fallback

    # Plot each replicate as a line
    if 'replicate' in scores_df.columns and dose_col in scores_df.columns:
        for rep in sorted(scores_df['replicate'].unique()):
            rep_data = scores_df[scores_df['replicate'] == rep].sort_values(dose_col)
            ax.plot(
                rep_data[dose_col],
                rep_data[pc],
                marker='o',
                label=f'Replicate {rep}',
                linewidth=2,
                markersize=8,
                alpha=0.7
            )

    # Mean trajectory
    if dose_col in scores_df.columns:
        mean_traj = scores_df.groupby(dose_col, observed=True)[pc].mean()
        ax.plot(
            mean_traj.index,
            mean_traj.values,
            color='black',
            linewidth=3,
            linestyle='--',
            label='Mean',
            zorder=10
        )

    ax.set_xlabel('Dose (µC/cm²)', fontsize=12, fontweight='bold')
    ylabel = f'{pc} Score'
    if var_expl is not None:
        ylabel += f' ({var_expl:.1f}%)'
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title('Dose Trajectory', fontsize=14, fontweight='bold')
    ax.legend(frameon=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(0, color='k', linewidth=0.5, linestyle='-', alpha=0.3)

    plt.tight_layout()

    _save_or_show(fig, save_path, show)

    return fig, ax


def plot_loading_bars(
    loadings_df: pd.DataFrame,
    pc: str = 'PC1',
    k: int = 20,
    include_sign: bool = True,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (10, 8)
) -> Tuple[Figure, Axes]:
    """
    Plot top k loadings as horizontal bar plot.

    Parameters
    ----------
    loadings_df : pd.DataFrame
        Loadings with mz, loading_PC1, etc., and optional 'assignment'
    pc : str
        Principal component (default: PC1)
    k : int
        Number of top loadings to show
    include_sign : bool
        If True, include both positive and negative (k each direction)
    save_path : str or Path, optional
        Save path
    show : bool
        Interactive display
    figsize : tuple
        Figure size

    Returns
    -------
    fig, ax : Figure, Axes
    """
    _maybe_set_qt_backend(show)

    loading_col = f'loading_{pc}'
    if loading_col not in loadings_df.columns:
        raise ValueError(f"Column {loading_col} not found in loadings_df")

    # Select top k loadings
    if include_sign:
        # Top k positive and top k negative
        pos = loadings_df.nlargest(k, loading_col)
        neg = loadings_df.nsmallest(k, loading_col)
        top = pd.concat([neg, pos]).drop_duplicates(subset=['mz'])
    else:
        # Top k by absolute value
        loadings_df['abs_loading'] = loadings_df[loading_col].abs()
        top = loadings_df.nlargest(k, 'abs_loading')

    top = top.sort_values(loading_col)

    # Build labels with assignment if available
    labels = []
    for _, row in top.iterrows():
        mz = row['mz']
        label = f"{mz:.4f}"
        if 'assignment' in row and pd.notna(row['assignment']):
            assignment = row['assignment']
            label += f"\n{assignment}"
        labels.append(label)

    fig, ax = plt.subplots(figsize=figsize)

    colors = ['red' if x < 0 else 'blue' for x in top[loading_col]]
    ax.barh(range(len(top)), top[loading_col], color=colors, alpha=0.7, edgecolor='k')
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(f'{pc} Loading', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {k} {pc} Loadings', fontsize=14, fontweight='bold')
    ax.axvline(0, color='k', linewidth=1, linestyle='-')
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()

    _save_or_show(fig, save_path, show)

    return fig, ax


def plot_heatmap_intensity(
    intensity_df: pd.DataFrame,
    mz_list: List[float],
    loadings_df: Optional[pd.DataFrame] = None,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (12, 8)
) -> Tuple[Figure, Axes]:
    """
    Plot heatmap of intensities for selected m/z across doses.

    Parameters
    ----------
    intensity_df : pd.DataFrame
        Long-format intensities
    mz_list : list of float
        m/z values to include
    loadings_df : pd.DataFrame, optional
        Loadings with assignments
    save_path : str or Path, optional
        Save path
    show : bool
        Interactive display
    figsize : tuple
        Figure size

    Returns
    -------
    fig, ax : Figure, Axes
    """
    _maybe_set_qt_backend(show)

    # Filter to mz_list
    subset = intensity_df[intensity_df['mz'].isin(mz_list)].copy()

    if len(subset) == 0:
        logger.warning("No intensities found for provided m/z list")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center')
        _save_or_show(fig, save_path, show)
        return fig, ax

    # Pivot: rows = m/z, columns = dose_label, values = mean intensity
    pivot = subset.groupby(['mz', 'dose_label'], observed=True)['intensity'].mean().reset_index()
    heatmap_data = pivot.pivot(index='mz', columns='dose_label', values='intensity')

    # Sort doses numerically
    dose_order = sorted(heatmap_data.columns, key=lambda x: float(x) if x.replace('.', '').isdigit() else 0)
    heatmap_data = heatmap_data[dose_order]

    # Row labels with assignments
    row_labels = []
    for mz in heatmap_data.index:
        label = f"{mz:.4f}"
        if loadings_df is not None:
            match = loadings_df[loadings_df['mz'] == mz]
            if len(match) > 0 and 'assignment' in match.columns:
                assignment = match['assignment'].iloc[0]
                if pd.notna(assignment):
                    label += f" ({assignment})"
        row_labels.append(label)

    fig, ax = plt.subplots(figsize=figsize)

    # Heatmap
    im = ax.imshow(heatmap_data.values, aspect='auto', cmap='viridis', interpolation='nearest')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Mean Intensity', fontsize=12, fontweight='bold')

    ax.set_xticks(range(len(dose_order)))
    ax.set_xticklabels(dose_order, fontsize=10)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)
    ax.set_xlabel('Dose (µC/cm²)', fontsize=12, fontweight='bold')
    ax.set_ylabel('m/z', fontsize=12, fontweight='bold')
    ax.set_title('Intensity Heatmap: Top Features', fontsize=14, fontweight='bold')

    plt.tight_layout()

    _save_or_show(fig, save_path, show)

    return fig, ax


def plot_dose_response(
    intensity_df: pd.DataFrame,
    mz: float,
    assignment: Optional[str] = None,
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (8, 6)
) -> Tuple[Figure, Axes]:
    """
    Plot dose-response curve for a single m/z.

    Shows individual replicates and mean with error bars.

    Parameters
    ----------
    intensity_df : pd.DataFrame
        Long-format intensities
    mz : float
        m/z to plot
    assignment : str, optional
        Fragment assignment for title
    save_path : str or Path, optional
        Save path
    show : bool
        Interactive display
    figsize : tuple
        Figure size

    Returns
    -------
    fig, ax : Figure, Axes
    """
    _maybe_set_qt_backend(show)

    # Filter to this m/z
    subset = intensity_df[intensity_df['mz'] == mz].copy()

    if len(subset) == 0:
        logger.warning(f"No intensity data for m/z {mz}")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f'No data for m/z {mz}', ha='center', va='center')
        _save_or_show(fig, save_path, show)
        return fig, ax

    # Sort by dose
    subset = subset.sort_values('dose_uC_cm2')

    fig, ax = plt.subplots(figsize=figsize)

    # Individual replicates
    for rep in sorted(subset['replicate'].unique()):
        rep_data = subset[subset['replicate'] == rep]
        ax.scatter(
            rep_data['dose_uC_cm2'],
            rep_data['intensity'],
            alpha=0.5,
            s=50,
            label=f'Rep {rep}'
        )

    # Mean with error bars
    summary = subset.groupby('dose_uC_cm2', observed=True)['intensity'].agg(['mean', 'std']).reset_index()
    ax.errorbar(
        summary['dose_uC_cm2'],
        summary['mean'],
        yerr=summary['std'],
        fmt='o-',
        color='black',
        linewidth=2,
        markersize=8,
        capsize=5,
        label='Mean ± SD',
        zorder=10
    )

    ax.set_xlabel('Dose (µC/cm²)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Intensity', fontsize=12, fontweight='bold')

    title = f'Dose Response: m/z {mz:.4f}'
    if assignment:
        title += f' ({assignment})'
    ax.set_title(title, fontsize=14, fontweight='bold')

    ax.legend(frameon=True)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()

    _save_or_show(fig, save_path, show)

    return fig, ax
