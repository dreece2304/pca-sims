#!/usr/bin/env python3
"""
Visualize fragment trends from statistical analysis.

Creates:
1. Dose-response curves for key fragments
2. Heatmaps showing fold change patterns
3. Summary trend plots
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_dose_trajectory(stats_file, output_dir, ion_mode):
    """Plot dose-response curves for significant linear trends."""
    df = pd.read_csv(stats_file)

    # Filter for significant linear trends
    linear_df = df[df['linear_trend'] == True].copy()

    if len(linear_df) == 0:
        print(f"No linear trends found in {ion_mode}")
        return

    # Get dose means
    doses = [2000, 5000, 10000, 15000]
    dose_labels = ['SQ2\n2k', 'SQ3\n5k', 'SQ4\n10k', 'SQ5\n15k']

    # Create figure with subplots
    n_fragments = min(12, len(linear_df))  # Top 12 by |loading|
    linear_df = linear_df.nlargest(n_fragments, 'PC1_Loading', keep='all')

    fig, axes = plt.subplots(4, 3, figsize=(15, 16))
    axes = axes.flatten()

    for idx, (_, row) in enumerate(linear_df.iterrows()):
        if idx >= 12:
            break

        ax = axes[idx]

        # Get mean values
        means = [row['SQ2_mean'], row['SQ3_mean'], row['SQ4_mean'], row['SQ5_mean']]

        # Plot data points
        ax.plot(doses, means, 'o-', color='#1f77b4', markersize=8, linewidth=2)

        # Plot regression line
        x_fit = np.array(doses)
        y_fit = row['slope'] * x_fit + row['intercept']
        ax.plot(x_fit, y_fit, '--', color='#ff7f0e', linewidth=1.5,
                label=f'R²={row["R_squared"]:.3f}')

        # Format plot
        ax.set_title(f"{row['Fragment']} (m/z {row['m/z']:.4f})", fontsize=10, fontweight='bold')
        ax.set_xlabel('E-beam Dose (µC/cm²)', fontsize=9)
        ax.set_ylabel('Normalized Intensity', fontsize=9)
        ax.set_xticks(doses)
        ax.set_xticklabels(dose_labels, fontsize=8)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        # Add trend label
        trend = 'Increases' if row['slope'] > 0 else 'Decreases'
        ax.text(0.05, 0.95, trend, transform=ax.transAxes,
                verticalalignment='top', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Remove unused subplots
    for idx in range(n_fragments, 12):
        fig.delaxes(axes[idx])

    plt.suptitle(f'{ion_mode} Ion Mode - Dose-Response Curves (Linear Trends)',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = output_dir / f'{ion_mode.lower()}_dose_response_curves.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_pairwise_heatmap(summary_file, output_dir, ion_mode):
    """Create heatmap showing fold change patterns across doses."""
    df = pd.read_csv(summary_file)

    # Get fold change columns
    fc_cols = ['log2fc_2k', 'log2fc_5k', 'log2fc_10k', 'log2fc_15k']
    dose_labels = ['2k', '5k', '10k', '15k']

    # Sort by mean log2fc
    df = df.sort_values('mean_log2fc', ascending=False)

    # Prepare data for heatmap
    heatmap_data = df[fc_cols].values
    fragments = [f"{row['Fragment']}\n{row['m/z']:.4f}" for _, row in df.iterrows()]

    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 12))

    # Use diverging colormap centered at 0
    vmax = max(abs(heatmap_data.min()), abs(heatmap_data.max()))
    im = ax.imshow(heatmap_data, cmap='RdBu_r', aspect='auto',
                   vmin=-vmax, vmax=vmax)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(dose_labels)))
    ax.set_yticks(np.arange(len(fragments)))
    ax.set_xticklabels(dose_labels, fontsize=10)
    ax.set_yticklabels(fragments, fontsize=8)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('log₂(Fold Change) vs As-Deposited', rotation=270, labelpad=20, fontsize=10)

    # Add significance markers
    for i, (_, row) in enumerate(df.iterrows()):
        for j, dose in enumerate(['2k', '5k', '10k', '15k']):
            if row[f'sig_{dose}']:
                ax.text(j, i, '*', ha='center', va='center',
                       color='black', fontsize=12, fontweight='bold')

    ax.set_xlabel('E-beam Dose (µC/cm²)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Fragment', fontsize=11, fontweight='bold')
    ax.set_title(f'{ion_mode} Ion Mode - Pairwise Fold Changes\n(* = FDR q < 0.05)',
                fontsize=13, fontweight='bold', pad=10)

    plt.tight_layout()

    output_file = output_dir / f'{ion_mode.lower()}_pairwise_heatmap.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_trend_summary(pos_stats, neg_stats, output_dir):
    """Create summary plot comparing positive and negative ion trends."""
    pos_df = pd.read_csv(pos_stats)
    neg_df = pd.read_csv(neg_stats)

    # Count trend types
    def count_trends(df):
        return {
            'Linear Increase': (df['trend_type'] == 'linear_increase').sum(),
            'Linear Decrease': (df['trend_type'] == 'linear_decrease').sum(),
            'Non-linear': (df['trend_type'] == 'non_linear').sum(),
            'No Trend': (df['trend_type'] == 'no_trend').sum()
        }

    pos_trends = count_trends(pos_df)
    neg_trends = count_trends(neg_df)

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    categories = list(pos_trends.keys())
    pos_counts = list(pos_trends.values())
    neg_counts = list(neg_trends.values())

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax.bar(x - width/2, pos_counts, width, label='Positive Ions',
                   color='#d62728', alpha=0.8)
    bars2 = ax.bar(x + width/2, neg_counts, width, label='Negative Ions',
                   color='#2ca02c', alpha=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('Trend Type', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Fragments', fontsize=12, fontweight='bold')
    ax.set_title('Dose-Trajectory Trend Classification\n(E-beam samples only, SQ2-SQ5)',
                fontsize=14, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()

    output_file = output_dir / 'trend_summary_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_fragment_categories(pos_stats, neg_stats, output_dir):
    """Plot fragment trends by category."""
    pos_df = pd.read_csv(pos_stats)
    neg_df = pd.read_csv(neg_stats)

    # Add category based on fragment composition
    def categorize_fragment(fragment):
        if 'Al' in fragment:
            return 'Aluminum-based'
        elif 'O' in fragment and 'C' in fragment:
            return 'Organic-oxygen'
        elif 'H' in fragment and 'C' in fragment and 'O' not in fragment:
            return 'Hydrocarbon'
        elif 'O' in fragment and 'C' not in fragment:
            return 'Oxygen-based'
        else:
            return 'Other'

    for df, mode in [(pos_df, 'Positive'), (neg_df, 'Negative')]:
        df['Category'] = df['Fragment'].apply(categorize_fragment)

        # Count trends by category
        category_trends = df.groupby(['Category', 'trend_type']).size().unstack(fill_value=0)

        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(12, 6))

        category_trends.plot(kind='bar', stacked=True, ax=ax,
                            color=['#2ca02c', '#d62728', '#ff7f0e', '#9467bd'])

        ax.set_xlabel('Fragment Category', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Fragments', fontsize=12, fontweight='bold')
        ax.set_title(f'{mode} Ion Mode - Trends by Fragment Category',
                    fontsize=14, fontweight='bold', pad=10)
        ax.legend(title='Trend Type', fontsize=10)
        ax.grid(True, axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        output_file = output_dir / f'{mode.lower()}_trends_by_category.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_file}")
        plt.close()


def main():
    base_dir = Path('/home/dreece23/pca-sims/outputs')

    # Create visualizations directory
    viz_dir = base_dir / 'Visualizations'
    viz_dir.mkdir(exist_ok=True)

    print("Creating visualizations...")
    print("=" * 60)

    # Dose-response curves
    print("\n1. Dose-response curves:")
    plot_dose_trajectory(
        base_dir / 'Dose-Trajectory/Positive/dose_trajectory_statistics.csv',
        viz_dir, 'Positive'
    )
    plot_dose_trajectory(
        base_dir / 'Dose-Trajectory/Negative/dose_trajectory_statistics.csv',
        viz_dir, 'Negative'
    )

    # Pairwise heatmaps
    print("\n2. Pairwise fold change heatmaps:")
    plot_pairwise_heatmap(
        base_dir / 'Pairwise/Positive/pairwise_summary_all_doses.csv',
        viz_dir, 'Positive'
    )
    plot_pairwise_heatmap(
        base_dir / 'Pairwise/Negative/pairwise_summary_all_doses.csv',
        viz_dir, 'Negative'
    )

    # Trend summary
    print("\n3. Trend summary comparison:")
    plot_trend_summary(
        base_dir / 'Dose-Trajectory/Positive/dose_trajectory_statistics.csv',
        base_dir / 'Dose-Trajectory/Negative/dose_trajectory_statistics.csv',
        viz_dir
    )

    # Fragment categories
    print("\n4. Trends by fragment category:")
    plot_fragment_categories(
        base_dir / 'Dose-Trajectory/Positive/dose_trajectory_statistics.csv',
        base_dir / 'Dose-Trajectory/Negative/dose_trajectory_statistics.csv',
        viz_dir
    )

    print("\n" + "=" * 60)
    print(f"All visualizations saved to: {viz_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
