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
        self.fragment_assignments = None  # Store fragment assignments for hover

        # Hover annotation and highlighting
        self.hover_annotation = None
        self.hover_connection = None
        self.stemlines = None  # Store stemlines for highlighting
        self.highlight_line = None  # Highlighted stick overlay

    def plot_stick_spectrum(self, mz_values, intensities, std_devs=None,
                           labels=None, show_sd_plot=False, title=None, fragment_assignments=None):
        """
        Plot stick spectrum with optional SD subplot

        Args:
            mz_values: Array of m/z values
            intensities: Array of mean intensities
            std_devs: Array of standard deviations (optional)
            labels: Dict mapping m/z -> label text for selected peaks
            show_sd_plot: Whether to show SD subplot
            title: Plot title (e.g., "Negative Ion - SQ4 (10000 µC/cm²)")
            fragment_assignments: List of dicts with fragment data for hover tooltips
        """
        self.fig.clear()

        # Store data
        self.mz_values = mz_values
        self.intensities = intensities
        self.std_devs = std_devs
        self.labels = labels if labels else {}
        self.fragment_assignments = fragment_assignments  # For hover tooltips

        print(f"📊 plot_stick_spectrum received {len(self.labels)} labels: {self.labels}")

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
            self._plot_sd_spectrum(self.sd_ax, mz_values, intensities, std_devs)

        # Set up hover tooltips
        self._setup_hover_tooltips()

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

        # Store stemlines for hover highlighting
        self.stemlines = stemlines

        # Add fragment labels for selected peaks
        if self.labels:
            self._add_labels(ax, mz_values, intensities)

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('Intensity', fontweight='bold')

        if title:
            ax.set_title(title, fontweight='bold', loc='left')

        # Add box frame (all spines visible)
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_linewidth(1.0)
            ax.spines[spine].set_color('black')

        # Set y-axis to start at 0
        ax.set_ylim(bottom=0)

        # Grid for readability
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    def _plot_sd_spectrum(self, ax, mz_values, intensities, std_devs):
        """
        Plot coefficient of variation (CV%) vs m/z as stick spectrum

        Args:
            ax: Matplotlib axes
            mz_values: Array of m/z values
            intensities: Array of mean intensities
            std_devs: Array of standard deviations
        """
        # Calculate CV% = (std_dev / intensity) * 100
        # Avoid division by zero
        cv_percent = np.where(intensities > 0, (std_devs / intensities) * 100, 0)

        # Use viridis mid-tone for CV% plot
        cv_color = '#21908C'  # Viridis teal

        # Create stick plot (matching main spectrum style)
        markerline, stemlines, baseline = ax.stem(
            mz_values,
            cv_percent,
            linefmt=cv_color,
            markerfmt=' ',  # No markers on top
            basefmt='k-'    # Black baseline
        )

        # Style the stems
        stemlines.set_linewidth(0.8)
        stemlines.set_alpha(0.7)
        baseline.set_linewidth(0.5)

        # Styling
        ax.set_xlabel('m/z', fontweight='bold')
        ax.set_ylabel('CV%', fontweight='bold')
        ax.set_title('Replicate Variability', fontweight='bold', loc='left', fontsize=10)

        # Add box frame (all spines visible)
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_linewidth(1.0)
            ax.spines[spine].set_color('black')

        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    def _add_labels(self, ax, mz_values, intensities):
        """
        Add fragment labels to selected peaks with smart positioning and collision avoidance

        Args:
            ax: Matplotlib axes
            mz_values: Array of m/z values
            intensities: Array of intensities
        """
        print(f"🏷️  _add_labels called with {len(self.labels)} labels to add")

        if not self.labels:
            return

        # Store label positions for collision detection
        placed_labels = []  # (x_min, x_max, y_min, y_max, label_obj)

        # Sort labels by intensity (descending) to place tallest peaks first
        label_items = []
        for mz, label_text in self.labels.items():
            idx = np.argmin(np.abs(mz_values - mz))
            if idx < len(intensities):
                label_items.append((mz, label_text, idx, intensities[idx]))

        label_items.sort(key=lambda x: x[3], reverse=True)  # Sort by intensity

        # Get plot dimensions for collision calculations
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]

        for mz, label_text, idx, intensity in label_items:
            print(f"   Adding label '{label_text}' at m/z {mz:.4f} (intensity: {intensity:.4e})")

            # Convert to LaTeX format for proper chemical notation
            latex_label = self._convert_to_latex(label_text)

            # Try multiple vertical positions to avoid collisions
            base_offset = intensity * 0.08  # Start 8% above peak
            offsets_to_try = [
                base_offset,
                base_offset + y_range * 0.05,
                base_offset + y_range * 0.10,
                base_offset + y_range * 0.15,
                base_offset + y_range * 0.20
            ]

            label_placed = False
            for offset in offsets_to_try:
                y_pos = intensity + offset

                # Estimate label bounds (rough approximation)
                # Each character is ~0.015 of x_range wide, height is ~0.03 of y_range
                label_width = len(label_text) * 0.012 * x_range
                label_height = 0.035 * y_range

                x_min = mz - label_width / 2
                x_max = mz + label_width / 2
                y_min = y_pos
                y_max = y_pos + label_height

                # Check for collisions with existing labels
                collision = False
                for prev_x_min, prev_x_max, prev_y_min, prev_y_max, _ in placed_labels:
                    if not (x_max < prev_x_min or x_min > prev_x_max or
                            y_max < prev_y_min or y_min > prev_y_max):
                        collision = True
                        break

                if not collision:
                    # No collision - place label here
                    # Use annotate for connection line if offset is large
                    if offset > base_offset + y_range * 0.02:
                        # Add connection line for elevated labels
                        label_obj = ax.annotate(
                            latex_label,
                            xy=(mz, intensity),  # Point to peak
                            xytext=(mz, y_pos),  # Label position
                            ha='center',
                            va='bottom',
                            fontsize=9,
                            color='#440154',  # Match stick color
                            arrowprops=dict(
                                arrowstyle='-',
                                color='#440154',
                                linewidth=0.8,
                                alpha=0.6
                            )
                        )
                    else:
                        # Simple text without connection line
                        label_obj = ax.text(
                            mz,
                            y_pos,
                            latex_label,
                            ha='center',
                            va='bottom',
                            fontsize=9,
                            color='#440154'  # Match stick color
                        )

                    # Store bounds for future collision checks
                    placed_labels.append((x_min, x_max, y_min, y_max, label_obj))
                    label_placed = True
                    print(f"   ✓ Label placed at offset {offset:.4e} (collision-free)")
                    break

            if not label_placed:
                # If all positions collide, place at highest position anyway
                y_pos = intensity + offsets_to_try[-1]
                label_obj = ax.annotate(
                    latex_label,
                    xy=(mz, intensity),
                    xytext=(mz, y_pos),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    color='#440154',
                    arrowprops=dict(
                        arrowstyle='-',
                        color='#440154',
                        linewidth=0.8,
                        alpha=0.6
                    )
                )
                print(f"   ⚠️  Label placed with possible overlap (no collision-free position found)")

    def _convert_to_latex(self, formula):
        """
        Convert chemical formula to LaTeX format for proper rendering

        Examples:
            "C_2H^-" -> "$\\mathrm{C_2H^-}$"
            "AlO^-" -> "$\\mathrm{AlO^-}$"
            "C_6H_5^+" -> "$\\mathrm{C_6H_5^+}$"

        Args:
            formula: Chemical formula string (may contain _, ^, -, +)

        Returns:
            LaTeX formatted string
        """
        # Already has subscript/superscript markers - wrap in LaTeX
        # Use \mathrm{} for upright (non-italic) math text
        return f"$\\mathrm{{{formula}}}$"

    def _setup_hover_tooltips(self):
        """Set up interactive hover tooltips for stick spectrum"""
        if self.main_ax is None:
            return

        # Disconnect previous hover connection if it exists
        if self.hover_connection is not None:
            self.mpl_disconnect(self.hover_connection)

        # Create simple text annotation (no box, no arrow) for overlay display
        self.hover_annotation = self.main_ax.text(
            0, 0, '',
            fontsize=10,
            fontweight='bold',
            color='#440154',  # Viridis dark (matches sticks)
            ha='left',
            va='bottom',
            visible=False,
            zorder=1000,  # High z-order to appear on top
            bbox=dict(facecolor='white', alpha=0.85, edgecolor='#440154', linewidth=1.5, pad=3)
        )

        # Connect hover event
        self.hover_connection = self.mpl_connect('motion_notify_event', self._on_hover)

    def _on_hover(self, event):
        """Handle mouse hover events to show tooltips"""
        if event.inaxes != self.main_ax or self.mz_values is None:
            if self.hover_annotation is not None:
                self.hover_annotation.set_visible(False)
                self.draw_idle()
            return

        # Find closest stick to mouse position
        x_data = event.xdata
        y_data = event.ydata

        if x_data is None or y_data is None:
            return

        # Find the closest m/z value
        distances = np.abs(self.mz_values - x_data)
        closest_idx = np.argmin(distances)
        closest_mz = self.mz_values[closest_idx]
        closest_intensity = self.intensities[closest_idx]

        # Much larger hover area for thin sticks (10% of x-range)
        x_tolerance = (self.main_ax.get_xlim()[1] - self.main_ax.get_xlim()[0]) * 0.10
        # Allow hovering anywhere in the vertical height of the stick plus extra space
        y_tolerance_bottom = -closest_intensity * 0.1  # Below baseline
        y_tolerance_top = closest_intensity * 0.2  # 20% above peak

        if (distances[closest_idx] < x_tolerance and
            y_data >= y_tolerance_bottom and
            y_data <= closest_intensity + y_tolerance_top):

            # Build simple tooltip: m/z and assignment only
            tooltip_text = f"m/z {closest_mz:.4f}"

            # Add fragment assignment if available (just the chemical formula)
            if self.fragment_assignments is not None:
                for assignment in self.fragment_assignments:
                    if abs(assignment['mz'] - closest_mz) < 1e-6:
                        if assignment['assignment'] != "Unassigned":
                            tooltip_text = f"m/z {closest_mz:.4f}\n{assignment['assignment']}"
                        break

            # Position tooltip near mouse, but ensure it stays in plot bounds
            xlim = self.main_ax.get_xlim()
            ylim = self.main_ax.get_ylim()

            # Position slightly offset from mouse
            x_pos = min(x_data + (xlim[1] - xlim[0]) * 0.02, xlim[1] * 0.95)
            y_pos = min(y_data + (ylim[1] - ylim[0]) * 0.03, ylim[1] * 0.95)

            # Update annotation position and text
            self.hover_annotation.set_position((x_pos, y_pos))
            self.hover_annotation.set_text(tooltip_text)
            self.hover_annotation.set_visible(True)

            # Highlight the hovered stick with a prominent outline
            self._highlight_stick(closest_idx, closest_mz, closest_intensity)

            self.draw_idle()
        else:
            # Hide tooltip and remove highlight if not hovering over a stick
            if self.hover_annotation is not None:
                self.hover_annotation.set_visible(False)
            self._remove_highlight()
            self.draw_idle()

    def _highlight_stick(self, stick_idx, mz, intensity):
        """Highlight a stick by adding a prominent outline"""
        # Remove previous highlight if it exists
        self._remove_highlight()

        # Draw a thicker, semi-transparent line over the stick
        self.highlight_line = self.main_ax.plot(
            [mz, mz],
            [0, intensity],
            color='#FDB462',  # Orange highlight color
            linewidth=4.0,
            alpha=0.7,
            zorder=999  # Just below tooltip
        )[0]

    def _remove_highlight(self):
        """Remove stick highlight"""
        if self.highlight_line is not None:
            try:
                self.highlight_line.remove()
            except:
                pass  # Ignore if already removed
            self.highlight_line = None

    def export_plot(self, filepath, dpi=300):
        """
        Export plot to file

        Args:
            filepath: Output file path
            dpi: Resolution (default 300 for publication quality)
        """
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
