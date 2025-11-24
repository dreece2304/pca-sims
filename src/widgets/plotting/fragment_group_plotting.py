"""
Fragment Group Plotting with PCA Loadings Overlay
Visualizes ToF-SIMS fragments grouped by chemical classification
Highlights high-loading fragments that drive PC separation
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.fragment_classifier import (
    classify_fragment,
    FragmentProperties,
    get_fragment_groups
)


@dataclass
class FragmentDataPoint:
    """Single fragment for plotting"""
    mass: float
    formula: str
    intensity: float
    loading: float  # PCA loading value
    chemical_family: str
    properties: FragmentProperties


class FragmentGroupPlotCanvas(FigureCanvas):
    """
    Canvas for plotting fragments grouped by chemical family
    with PCA loadings overlay
    """

    # Color scheme for chemical families
    FAMILY_COLORS = {
        'Aromatic': '#E74C3C',              # Red - aromatic markers
        'H-deficient_unsaturated': '#9B59B6',  # Purple - polyynes/allenes
        'Unsaturated_carbon': '#3498DB',    # Blue - unsaturated
        'Saturated_carbon': '#2ECC71',      # Green - saturated
        'Organic_oxygen': '#F39C12',        # Orange - oxygen-containing
        'Carbonyl': '#E67E22',              # Dark orange
        'Al-based': '#95A5A6',              # Gray - aluminum
        'Contamination': '#7F8C8D',         # Dark gray
        'Unknown': '#BDC3C7',               # Light gray
    }

    def __init__(self, parent=None, width=12, height=8, dpi=None):
        """Initialize canvas"""
        if dpi is None:
            try:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                    dpi = screen.logicalDotsPerInch()
                else:
                    dpi = 100
            except:
                dpi = 100

        dpi = max(72, min(dpi, 300))

        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

        self.plot_dpi = dpi
        self.fragment_data = []

    def plot_fragment_groups(
        self,
        fragments: List[Dict],  # [{mass, formula, intensity, polarity}]
        loadings: np.ndarray,   # PCA loadings for this PC
        pc_number: int = 1,
        polarity: str = 'negative',
        loading_threshold: float = 0.1,  # Highlight fragments with |loading| > threshold
        title: Optional[str] = None
    ):
        """
        Plot fragments grouped by chemical family with loadings overlay

        Args:
            fragments: List of fragment dicts with mass, formula, intensity, polarity
            loadings: PCA loading values for each fragment
            pc_number: Which PC these loadings are from
            polarity: Ion polarity
            loading_threshold: Threshold for highlighting high-loading fragments
            title: Optional plot title
        """
        self.fig.clear()

        # Classify all fragments
        classified_data = []
        for i, frag in enumerate(fragments):
            props = classify_fragment(
                frag['formula'],
                frag['mass'],
                polarity
            )

            data_point = FragmentDataPoint(
                mass=frag['mass'],
                formula=frag['formula'],
                intensity=frag.get('intensity', 0),
                loading=loadings[i] if i < len(loadings) else 0,
                chemical_family=props.chemical_family,
                properties=props
            )
            classified_data.append(data_point)

        self.fragment_data = classified_data

        # Create subplot grid
        gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.3)

        # Main plot: Intensity by chemical family
        ax_main = self.fig.add_subplot(gs[0])

        # Loadings plot: Show which fragments drive PC separation
        ax_loadings = self.fig.add_subplot(gs[1], sharex=ax_main)

        # Group fragments by chemical family
        family_groups = {}
        for dp in classified_data:
            family = dp.chemical_family
            if family not in family_groups:
                family_groups[family] = []
            family_groups[family].append(dp)

        # Plot intensity sticks colored by family
        self._plot_intensity_by_family(ax_main, family_groups, loading_threshold)

        # Plot loadings
        self._plot_loadings(ax_loadings, classified_data, loading_threshold, pc_number)

        # Set title
        if title:
            ax_main.set_title(title, fontsize=12, fontweight='bold')
        else:
            ax_main.set_title(
                f'Fragment Groups - PC{pc_number} Loadings ({polarity.capitalize()} Ion)',
                fontsize=12, fontweight='bold'
            )

        self.draw()

    def _plot_intensity_by_family(
        self,
        ax,
        family_groups: Dict[str, List[FragmentDataPoint]],
        loading_threshold: float
    ):
        """Plot intensity sticks colored by chemical family"""

        # Plot each family
        for family, data_points in sorted(family_groups.items()):
            masses = [dp.mass for dp in data_points]
            intensities = [dp.intensity for dp in data_points]
            loadings = [dp.loading for dp in data_points]

            color = self.FAMILY_COLORS.get(family, '#BDC3C7')

            # Regular fragments
            regular_mask = np.abs(loadings) < loading_threshold
            if np.any(regular_mask):
                masses_reg = np.array(masses)[regular_mask]
                intensities_reg = np.array(intensities)[regular_mask]
                ax.vlines(masses_reg, 0, intensities_reg,
                         colors=color, linewidth=1.5, alpha=0.6,
                         label=family if family != 'Unknown' else None)

            # High-loading fragments (emphasized)
            high_mask = np.abs(loadings) >= loading_threshold
            if np.any(high_mask):
                masses_high = np.array(masses)[high_mask]
                intensities_high = np.array(intensities)[high_mask]
                ax.vlines(masses_high, 0, intensities_high,
                         colors=color, linewidth=3, alpha=1.0)

                # Add markers at top of high-loading sticks
                ax.scatter(masses_high, intensities_high,
                          c=color, s=50, marker='o', edgecolors='black',
                          linewidths=1, zorder=10)

        ax.set_ylabel('Normalized Intensity', fontsize=10, fontweight='bold')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--')

        # Legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            # Add custom legend entry for high loadings
            from matplotlib.lines import Line2D
            high_loading_line = Line2D([0], [0], color='black', linewidth=3,
                                      label=f'|Loading| ≥ {loading_threshold:.2f}')
            handles.append(high_loading_line)
            labels.append(f'|Loading| ≥ {loading_threshold:.2f}')

            ax.legend(handles, labels, loc='upper right', fontsize=8,
                     framealpha=0.9, ncol=2)

    def _plot_loadings(
        self,
        ax,
        data_points: List[FragmentDataPoint],
        loading_threshold: float,
        pc_number: int
    ):
        """Plot PCA loadings as bar chart"""

        masses = [dp.mass for dp in data_points]
        loadings = [dp.loading for dp in data_points]
        families = [dp.chemical_family for dp in data_points]

        # Color bars by chemical family
        colors = [self.FAMILY_COLORS.get(f, '#BDC3C7') for f in families]

        # Plot loadings as stem plot
        markerline, stemlines, baseline = ax.stem(
            masses, loadings,
            linefmt='gray', markerfmt='o', basefmt='k-'
        )

        # Color stems by family (matplotlib 3.1+ uses LineCollection)
        # Set colors and linewidths for all stems at once
        stemlines.set_colors(colors)

        # Set linewidths - emphasize high loadings
        linewidths = [3 if abs(loadings[i]) >= loading_threshold else 1.5
                      for i in range(len(loadings))]
        stemlines.set_linewidths(linewidths)

        # Color markers
        markerline.set_markerfacecolor('none')
        markerline.set_markeredgecolor('black')
        markerline.set_markersize(4)

        # Add threshold lines
        ax.axhline(loading_threshold, color='red', linestyle='--',
                  linewidth=1, alpha=0.5, label=f'±{loading_threshold:.2f}')
        ax.axhline(-loading_threshold, color='red', linestyle='--',
                  linewidth=1, alpha=0.5)

        ax.set_xlabel('m/z', fontsize=10, fontweight='bold')
        ax.set_ylabel(f'PC{pc_number} Loading', fontsize=10, fontweight='bold')
        ax.set_xlim(left=0)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.legend(loc='upper right', fontsize=8)

    def plot_family_summary(
        self,
        fragments: List[Dict],
        polarity: str = 'negative',
        title: Optional[str] = None
    ):
        """
        Plot summary statistics by chemical family (no PCA loadings needed)

        Useful for initial data exploration before PCA

        Args:
            fragments: List of fragment dicts
            polarity: Ion polarity
            title: Optional title
        """
        self.fig.clear()

        # Classify fragments
        classified = []
        for frag in fragments:
            props = classify_fragment(frag['formula'], frag['mass'], polarity)
            classified.append((props, frag.get('intensity', 0)))

        # Group by family
        family_groups = {}
        for props, intensity in classified:
            family = props.chemical_family
            if family not in family_groups:
                family_groups[family] = {
                    'count': 0,
                    'total_intensity': 0,
                    'fragments': []
                }
            family_groups[family]['count'] += 1
            family_groups[family]['total_intensity'] += intensity
            family_groups[family]['fragments'].append(props)

        # Create pie chart and bar chart
        ax1 = self.fig.add_subplot(1, 2, 1)
        ax2 = self.fig.add_subplot(1, 2, 2)

        # Pie chart: Fragment count by family
        families = list(family_groups.keys())
        counts = [family_groups[f]['count'] for f in families]
        colors = [self.FAMILY_COLORS.get(f, '#BDC3C7') for f in families]

        ax1.pie(counts, labels=families, colors=colors, autopct='%1.1f%%',
               startangle=90)
        ax1.set_title('Fragment Count by Family', fontweight='bold')

        # Bar chart: Total intensity by family
        intensities = [family_groups[f]['total_intensity'] for f in families]
        ax2.barh(families, intensities, color=colors)
        ax2.set_xlabel('Total Intensity', fontweight='bold')
        ax2.set_title('Intensity Distribution', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')

        if title:
            self.fig.suptitle(title, fontsize=14, fontweight='bold')

        self.draw()


# ===== TESTING =====

if __name__ == "__main__":
    print("Fragment Group Plotting - Test")
    print("=" * 60)

    # Create test data
    test_fragments = [
        {'mass': 77.0386, 'formula': 'C6H5', 'intensity': 0.8, 'polarity': 'positive'},
        {'mass': 91.0542, 'formula': 'C7H7', 'intensity': 0.6, 'polarity': 'positive'},
        {'mass': 27.0235, 'formula': 'C2H3', 'intensity': 0.4, 'polarity': 'negative'},
        {'mass': 49.0078, 'formula': 'C4H', 'intensity': 0.3, 'polarity': 'negative'},
        {'mass': 93.0346, 'formula': 'C6H5O', 'intensity': 0.7, 'polarity': 'negative'},
        {'mass': 65.0033, 'formula': 'C4HO', 'intensity': 0.5, 'polarity': 'negative'},
    ]

    # Simulated PCA loadings
    test_loadings = np.array([0.35, 0.25, 0.05, 0.15, 0.40, 0.08])

    print("✅ Test data created")
    print(f"   {len(test_fragments)} fragments")
    print(f"   {len(test_loadings)} loadings")
    print("\n🎨 Fragment group plotting module ready for GUI integration!")
