"""
Stick Spectrum Plotting for ToF-SIMS Mass Spectra
Follows PCAPlotCanvas pattern for consistency
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class StickSpectrumCanvas(FigureCanvas):
    """
    Matplotlib canvas for stick spectrum visualization
    Follows the same pattern as PCAPlotCanvas for consistency
    """

    def __init__(self, parent=None, width=10, height=6, dpi=None):
        """
        Initialize stick spectrum canvas

        Args:
            parent: Qt parent widget
            width: Figure width in inches
            height: Figure height in inches
            dpi: Dots per inch (auto-detected if None)
        """
        # Auto-detect DPI from screen if not specified (same as PCAPlotCanvas)
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

        # Ensure reasonable DPI bounds
        dpi = max(72, min(dpi, 300))

        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

        # Store DPI for export
        self.plot_dpi = dpi

        # Initialize axes (will be created in plot methods)
        self.main_ax = None
        self.sd_ax = None

        # Store data for interaction
        self.mz_values = None
        self.intensities = None
        self.std_devs = None
        self.labels = None

    def plot_stick_spectrum(self, mz_values, intensities, std_devs=None,
                           labels=None, show_sd_plot=False, title=None):
        """
        Plot stick spectrum with optional SD subplot

        Args:
            mz_values: Array of m/z values
            intensities: Array of mean intensities
            std_devs: Array of standard deviations (optional)
            labels: Dict mapping m/z -> label text for selected peaks
            show_sd_plot: Whether to show SD subplot
            title: Plot title (e.g., "Negative Ion - SQ4 (10000 µC/cm²)")
        """
        self.fig.clear()

        # Store data
        self.mz_values = mz_values
        self.intensities = intensities
        self.std_devs = std_devs
        self.labels = labels if labels else {}

        # Determine subplot layout
        if show_sd_plot and std_devs is not None:
            # Stacked: main spectrum on top, SD plot below
            gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.3)
            self.main_ax = self.fig.add_subplot(gs[0])
            self.sd_ax = self.fig.add_subplot(gs[1], sharex=self.main_ax)
        else:
            # Single plot
            self.main_ax = self.fig.add_subplot(111)
            self.sd_ax = None

        # Plot main stick spectrum
        self._plot_main_spectrum(self.main_ax, mz_values, intensities, title)

        # Plot SD subplot if requested
        if show_sd_plot and std_devs is not None and self.sd_ax is not None:
            self._plot_sd_spectrum(self.sd_ax, mz_values, std_devs)

        self.draw()

    def _plot_main_spectrum(self, ax, mz_values, intensities, title):
        """
        Plot the main stick spectrum

        Args:
            ax: Matplotlib axes
            mz_values: Array of m/z values
            intensities: Array of intensities
            title: Plot title
        """
        # Use viridis dark blue for consistency with PCA plots
        stick_color = '#440154'  # Viridis dark

        # Create stick plot (markerline, stemlines, baseline)
        markerline, stemlines, baseline = ax.stem(
            mz_values,
            intensities,
            linefmt=stick_color,
            markerfmt=' ',  # No markers on top
            basefmt='k-'    # Black baseline
        )

        # Style the stems
        stemlines.set_linewidth(1.0)
        stemlines.set_alpha(0.8)
        baseline.set_linewidth(0.5)

        # Add fragment labels for selected peaks
        if self.labels:
            self._add_labels(ax, mz_values, intensities)

        # Styling (match PCA plots)
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Intensity (TIC-normalized)', fontweight='bold')

        if title:
            ax.set_title(title, fontweight='bold', loc='left')

        # Clean publication style (remove top and right spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Set y-axis to start at 0
        ax.set_ylim(bottom=0)

        # Grid for readability
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    def _plot_sd_spectrum(self, ax, mz_values, std_devs):
        """
        Plot standard deviation vs m/z

        Args:
            ax: Matplotlib axes
            mz_values: Array of m/z values
            std_devs: Array of standard deviations
        """
        # Use viridis mid-tone for SD plot
        sd_color = '#21908C'  # Viridis teal

        # Plot as scatter to show variability distribution
        ax.scatter(mz_values, std_devs, alpha=0.6, s=20, color=sd_color, edgecolors='none')

        # Optional: add line connecting points for continuity
        ax.plot(mz_values, std_devs, color=sd_color, alpha=0.3, linewidth=0.5)

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Std Dev', fontweight='bold')
        ax.set_title('Replicate Variability', fontweight='bold', loc='left', fontsize=10)

        # Clean style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    def _add_labels(self, ax, mz_values, intensities):
        """
        Add fragment labels to selected peaks with smart positioning

        Args:
            ax: Matplotlib axes
            mz_values: Array of m/z values
            intensities: Array of intensities
        """
        # For now, use simple positioning (will enhance in later stages)
        # Labels go above their respective sticks

        for mz, label_text in self.labels.items():
            # Find the index of this m/z value
            idx = np.argmin(np.abs(mz_values - mz))

            if idx < len(intensities):
                intensity = intensities[idx]

                # Place label above stick with small offset
                offset = intensity * 0.05  # 5% offset above peak

                ax.text(
                    mz,
                    intensity + offset,
                    label_text,
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold',
                    rotation=0,  # Horizontal for now (can rotate if crowded)
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                             edgecolor='none', alpha=0.7)
                )

    def export_plot(self, filepath, dpi=300):
        """
        Export plot to file

        Args:
            filepath: Output file path
            dpi: Resolution (default 300 for publication quality)
        """
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
