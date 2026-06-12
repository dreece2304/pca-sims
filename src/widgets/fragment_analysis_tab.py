"""
Fragment Analysis Tab - Chemical Classification and Metrics
Separate tab that activates after PCA completion
Shows fragment groups and chemical metrics across all samples
Enhanced with top loading fragments table and dose trajectory analysis
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QComboBox, QSlider, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QSpinBox, QFormLayout, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import numpy as np
import pandas as pd
from pathlib import Path
import json

from widgets.plotting import FragmentGroupPlotCanvas
from widgets.common import NumericTableWidgetItem
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from core.fragment_classifier import classify_fragment, AROMATIC_MARKERS
from core.crosslinking_metrics import CrosslinkingAnalyzer, SampleMetrics


class TopLoadingFragmentsWidget(QWidget):
    """
    Widget for displaying top loading fragments with dose trajectories
    Shows table of fragments sorted by loading magnitude and their trends across doses
    """

    fragment_selected = Signal(int)  # Emit fragment index when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fragment_data = None
        self.pca_results = None
        self.sample_info = None  # Stores dose/sample mapping
        self.current_polarity = 'negative'

        self.init_ui()

    def init_ui(self):
        # Use splitter for resizable table/plot layout
        splitter = QSplitter(Qt.Vertical)
        layout = QVBoxLayout(self)

        # Controls section
        controls_group = QGroupBox("Display Controls")
        controls_layout = QGridLayout()

        # PC selector
        controls_layout.addWidget(QLabel("Principal Component:"), 0, 0)
        self.pc_combo = QComboBox()
        self.pc_combo.currentIndexChanged.connect(self.update_display)
        controls_layout.addWidget(self.pc_combo, 0, 1)

        # Top N selector
        controls_layout.addWidget(QLabel("Show Top:"), 0, 2)
        self.top_n_spin = QSpinBox()
        self.top_n_spin.setMinimum(5)
        self.top_n_spin.setMaximum(100)
        self.top_n_spin.setValue(20)
        self.top_n_spin.setSuffix(" fragments")
        self.top_n_spin.valueChanged.connect(self.update_display)
        controls_layout.addWidget(self.top_n_spin, 0, 3)

        # Chemical family filter
        controls_layout.addWidget(QLabel("Filter by Group:"), 1, 0)
        self.family_filter = QComboBox()
        self.family_filter.addItem("All Families")
        self.family_filter.currentIndexChanged.connect(self.update_display)
        controls_layout.addWidget(self.family_filter, 1, 1, 1, 3)

        # Sort options
        controls_layout.addWidget(QLabel("Sort by:"), 2, 0)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Loading Magnitude", "Variance Contribution", "Positive Loading", "Negative Loading", "Dose Change"])
        self.sort_combo.currentIndexChanged.connect(self.update_display)
        controls_layout.addWidget(self.sort_combo, 2, 1, 1, 3)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Table section
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Top Loading Fragments")
        table_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        table_layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(False)  # We handle sorting manually
        self.table.itemSelectionChanged.connect(self.on_fragment_selected)
        table_layout.addWidget(self.table)

        splitter.addWidget(table_widget)

        # Plot section
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        plot_label = QLabel("Dose Trajectory (select fragment above)")
        plot_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        plot_layout.addWidget(plot_label)

        self.plot_canvas = FigureCanvas(Figure(figsize=(10, 4)))
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, plot_widget)
        plot_layout.addWidget(self.plot_toolbar)
        plot_layout.addWidget(self.plot_canvas)

        splitter.addWidget(plot_widget)

        # Set initial sizes (60% table, 40% plot)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter)

        # Export button
        export_btn = QPushButton("Export Top Loading Fragments")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)

        # Info label
        self.info_label = QLabel("Load data and run PCA to view top loading fragments")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)

    def set_data(self, fragment_data, pca_results, sample_info, polarity='negative'):
        """
        Populate widget with fragment data and PCA results

        Args:
            fragment_data: Dict with masses, formulas, intensities per sample
            pca_results: Dict with PCA loadings, scores, variance
            sample_info: List of dicts with sample metadata (name, dose, etc.)
            polarity: 'negative' or 'positive'
        """
        self.fragment_data = fragment_data
        self.pca_results = pca_results
        self.sample_info = sample_info
        self.current_polarity = polarity

        # Store dose values if available (for averaged data)
        self.dose_values = fragment_data.get('dose_values', None)
        self.n_replicates = fragment_data.get('n_replicates', 0)

        # Populate PC selector
        self.pc_combo.clear()
        n_components = pca_results['loadings'].shape[1]
        for i in range(n_components):
            variance = pca_results['variance_explained'][i]
            self.pc_combo.addItem(f"PC{i+1} ({variance:.1f}%)")

        # Populate chemical family filter
        self.family_filter.clear()
        self.family_filter.addItem("All Families")

        # Use curated families from database (not recalculated)
        if 'families' in fragment_data:
            families = set(fragment_data['families'])
        else:
            # Fallback: calculate if not provided (backward compatibility)
            families = set()
            for formula, mass in zip(fragment_data['formulas'], fragment_data['masses']):
                props = classify_fragment(formula, mass, polarity)
                families.add(props.chemical_family)

        for family in sorted(families):
            self.family_filter.addItem(family)

        self.info_label.setText(
            f"{len(fragment_data['masses'])} fragments | "
            f"{len(sample_info)} samples | "
            f"{n_components} PCs"
        )

        self.update_display()

    def update_display(self):
        """Update table with top loading fragments"""
        if self.fragment_data is None or self.pca_results is None:
            return

        pc_idx = self.pc_combo.currentIndex()
        if pc_idx < 0:
            return

        # Get loadings for selected PC
        loadings = self.pca_results['loadings'].iloc[:, pc_idx].values

        # Calculate total sum of squared loadings for this PC (for variance contribution)
        total_squared_loading = np.sum(loadings ** 2)

        # Build fragment info list
        fragments_info = []
        family_filter = self.family_filter.currentText()

        for i in range(len(self.fragment_data['masses'])):
            mass = self.fragment_data['masses'][i]
            formula = self.fragment_data['formulas'][i]
            loading = loadings[i]

            # Calculate variance contribution as percentage
            # (squared loading / sum of squared loadings) * 100
            variance_contribution = (loading ** 2 / total_squared_loading) * 100 if total_squared_loading > 0 else 0.0

            # Get chemical family from database (or calculate if not provided)
            if 'families' in self.fragment_data and i < len(self.fragment_data['families']):
                chemical_family = self.fragment_data['families'][i]
                # Still classify for other properties (DBE, H/C ratio, etc.)
                props = classify_fragment(formula, mass, self.current_polarity)
                # Override the chemical family with database value
                props.chemical_family = chemical_family
            else:
                # Fallback: calculate if not provided (backward compatibility)
                props = classify_fragment(formula, mass, self.current_polarity)

            # Apply family filter
            if family_filter != "All Families" and props.chemical_family != family_filter:
                continue

            # Calculate dose trajectory metrics
            intensities = np.array([
                self.fragment_data['intensities'][j][i]
                for j in range(len(self.fragment_data['intensities']))
            ])

            # Get standard deviations if available
            if 'intensities_std' in self.fragment_data:
                intensities_std = np.array([
                    self.fragment_data['intensities_std'][j][i]
                    for j in range(len(self.fragment_data['intensities_std']))
                ])
            else:
                intensities_std = None

            # Calculate change (ratio of max to min, or percent change)
            if intensities.min() > 0:
                dose_change = (intensities.max() - intensities.min()) / intensities.min() * 100
            else:
                dose_change = 0.0

            fragments_info.append({
                'index': i,
                'mass': mass,
                'formula': formula,
                'loading': loading,
                'loading_abs': abs(loading),
                'variance_contribution': variance_contribution,
                'chemical_family': props.chemical_family,
                'dbe': props.dbe,
                'h_c_ratio': props.h_c_ratio,
                'saturation': props.saturation_class,
                'aromatic': 'Yes' if props.is_aromatic_marker else 'No',
                'dose_change': dose_change,
                'intensities': intensities,
                'intensities_std': intensities_std,
                'n_replicates': self.n_replicates
            })

        # Sort based on selection
        sort_option = self.sort_combo.currentText()
        if sort_option == "Loading Magnitude":
            fragments_info.sort(key=lambda x: x['loading_abs'], reverse=True)
        elif sort_option == "Variance Contribution":
            fragments_info.sort(key=lambda x: x['variance_contribution'], reverse=True)
        elif sort_option == "Positive Loading":
            fragments_info.sort(key=lambda x: x['loading'], reverse=True)
        elif sort_option == "Negative Loading":
            fragments_info.sort(key=lambda x: x['loading'], reverse=False)
        elif sort_option == "Dose Change":
            fragments_info.sort(key=lambda x: abs(x['dose_change']), reverse=True)

        # Take top N
        top_n = self.top_n_spin.value()
        fragments_info = fragments_info[:top_n]

        # Update table
        self._populate_table(fragments_info, pc_idx)

        # Store current fragments for selection
        self.current_fragments = fragments_info

    def _populate_table(self, fragments_info, pc_idx):
        """Populate table with fragment information"""
        # Define columns
        columns = [
            'Rank', 'm/z', 'Formula', f'PC{pc_idx+1} Loading',
            '% Variance', 'Chemical Family', 'DBE', 'H/C', 'Saturation',
            'Aromatic', 'Dose Change (%)'
        ]

        self.table.setRowCount(len(fragments_info))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        for i, frag in enumerate(fragments_info):
            # Rank
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # m/z (numeric for sorting)
            self.table.setItem(i, 1, NumericTableWidgetItem(f"{frag['mass']:.4f}"))

            # Formula
            formula_item = QTableWidgetItem(frag['formula'])
            self.table.setItem(i, 2, formula_item)

            # Loading (color-coded)
            loading_item = NumericTableWidgetItem(f"{frag['loading']:.4f}")
            if frag['loading'] > 0:
                loading_item.setBackground(QColor(255, 200, 200))  # Light red
            else:
                loading_item.setBackground(QColor(200, 200, 255))  # Light blue
            self.table.setItem(i, 3, loading_item)

            # % Variance (contribution to PC)
            variance_pct_item = NumericTableWidgetItem(f"{frag['variance_contribution']:.2f}")
            self.table.setItem(i, 4, variance_pct_item)

            # Chemical family
            self.table.setItem(i, 5, QTableWidgetItem(frag['chemical_family']))

            # DBE
            if frag['dbe'] is not None:
                self.table.setItem(i, 6, NumericTableWidgetItem(f"{frag['dbe']:.1f}"))
            else:
                self.table.setItem(i, 6, QTableWidgetItem("N/A"))

            # H/C ratio
            if frag['h_c_ratio'] is not None:
                self.table.setItem(i, 7, NumericTableWidgetItem(f"{frag['h_c_ratio']:.2f}"))
            else:
                self.table.setItem(i, 7, QTableWidgetItem("N/A"))

            # Saturation
            self.table.setItem(i, 8, QTableWidgetItem(frag['saturation']))

            # Aromatic
            self.table.setItem(i, 9, QTableWidgetItem(frag['aromatic']))

            # Dose change
            change_item = NumericTableWidgetItem(f"{frag['dose_change']:.1f}")
            if abs(frag['dose_change']) > 50:  # Highlight large changes
                change_item.setBackground(QColor(255, 255, 200))  # Light yellow
            self.table.setItem(i, 10, change_item)

        # Resize columns to content
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def on_fragment_selected(self):
        """Handle fragment selection in table"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_fragments):
            return

        # Plot dose trajectory for selected fragment
        frag = self.current_fragments[row]
        self._plot_dose_trajectory(frag)

    def _plot_dose_trajectory(self, frag):
        """Plot intensity trajectory across doses for a fragment with error bars"""
        self.plot_canvas.figure.clear()
        ax = self.plot_canvas.figure.add_subplot(111)

        # Get dose values - check if dose_values available (averaged data)
        if hasattr(self, 'dose_values') and self.dose_values:
            doses = self.dose_values
            sample_names = [f"Dose {i}" for i in range(len(doses))]
        elif self.sample_info:
            doses = [s.get('dose', i) for i, s in enumerate(self.sample_info)]
            sample_names = [s.get('name', f"S{i}") for i, s in enumerate(self.sample_info)]
        else:
            doses = list(range(len(frag['intensities'])))
            sample_names = [f"Sample {i}" for i in range(len(frag['intensities']))]

        intensities = frag['intensities']

        # Get standard deviations if available
        stds = frag.get('intensities_std', None)

        # Plot line with markers and error bars
        if stds is not None:
            ax.errorbar(doses, intensities, yerr=stds,
                       fmt='o-', linewidth=2, markersize=8,
                       color='#440154', ecolor='#999999', capsize=5, capthick=2,
                       label=frag['formula'])

            # Add n_replicates info to title if available
            n_reps = frag.get('n_replicates', 0)
            rep_text = f" (n={n_reps})" if n_reps > 0 else ""
        else:
            ax.plot(doses, intensities, 'o-', linewidth=2, markersize=8,
                   color='#440154', label=frag['formula'])
            rep_text = ""

        # Add value labels
        for dose, intensity in zip(doses, intensities):
            ax.text(dose, intensity, f'{intensity:.2e}',
                   fontsize=8, ha='center', va='bottom')

        # Styling
        ax.set_xlabel('Dose (µC/cm²)', fontweight='bold')
        ax.set_ylabel('Intensity (mean ± std)', fontweight='bold') if stds is not None else ax.set_ylabel('Intensity', fontweight='bold')
        ax.set_title(
            f"{frag['formula']} (m/z {frag['mass']:.4f}) - {frag['chemical_family']}{rep_text}\n"
            f"Loading: {frag['loading']:.4f} | Change: {frag['dose_change']:.1f}%",
            fontweight='bold', fontsize=10
        )
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')

        # Set x-axis ticks to dose values
        ax.set_xticks(doses)

        self.plot_canvas.figure.tight_layout()
        self.plot_canvas.draw()

    def export_data(self):
        """Export top loading fragments data"""
        if not hasattr(self, 'current_fragments') or not self.current_fragments:
            QMessageBox.warning(self, "No Data", "No fragment data to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Top Loading Fragments",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Build DataFrame
            export_data = []
            for rank, frag in enumerate(self.current_fragments, 1):
                row = {
                    'Rank': rank,
                    'm/z': frag['mass'],
                    'Formula': frag['formula'],
                    'Loading': frag['loading'],
                    'Loading_Abs': frag['loading_abs'],
                    'Variance_Contribution_Percent': frag['variance_contribution'],
                    'Chemical_Family': frag['chemical_family'],
                    'DBE': frag['dbe'],
                    'H_C_Ratio': frag['h_c_ratio'],
                    'Saturation': frag['saturation'],
                    'Aromatic': frag['aromatic'],
                    'Dose_Change_Percent': frag['dose_change']
                }

                # Add intensity columns for each sample
                for i, intensity in enumerate(frag['intensities']):
                    if self.sample_info and i < len(self.sample_info):
                        sample_name = self.sample_info[i].get('name', f'Sample_{i}')
                    else:
                        sample_name = f'Sample_{i}'
                    row[sample_name] = intensity

                export_data.append(row)

            df = pd.DataFrame(export_data)

            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False)

            QMessageBox.information(
                self,
                "Export Success",
                f"Top loading fragments exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n{str(e)}"
            )


class FragmentGroupsWidget(QWidget):
    """
    Widget for visualizing fragments grouped by chemical family
    with PCA loadings overlay
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fragment_data = None
        self.pca_results = None
        self.current_polarity = 'negative'

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Controls section
        controls_group = QGroupBox("Display Controls")
        controls_layout = QGridLayout()

        # PC selector
        controls_layout.addWidget(QLabel("Principal Component:"), 0, 0)
        self.pc_combo = QComboBox()
        self.pc_combo.currentIndexChanged.connect(self.update_plot)
        controls_layout.addWidget(self.pc_combo, 0, 1)

        # Loading threshold slider
        controls_layout.addWidget(QLabel("Loading Threshold:"), 1, 0)
        threshold_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(5)  # 0.05
        self.threshold_slider.setMaximum(30)  # 0.30
        self.threshold_slider.setValue(10)  # 0.10 default
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(5)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        threshold_layout.addWidget(self.threshold_slider)

        self.threshold_label = QLabel("0.10")
        self.threshold_label.setMinimumWidth(50)
        threshold_layout.addWidget(self.threshold_label)
        controls_layout.addLayout(threshold_layout, 1, 1)

        # Show only high-loading checkbox
        self.high_loading_only = QCheckBox("Show only high-loading fragments")
        self.high_loading_only.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.high_loading_only, 2, 0, 1, 2)

        # Sample selector
        controls_layout.addWidget(QLabel("Sample:"), 3, 0)
        self.sample_combo = QComboBox()
        self.sample_combo.currentIndexChanged.connect(self.update_plot)
        controls_layout.addWidget(self.sample_combo, 3, 1)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Plot canvas
        self.canvas = FragmentGroupPlotCanvas(self, width=12, height=8)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Export button
        export_btn = QPushButton("Export Fragment Groups")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)

        # Info label
        self.info_label = QLabel("Load data and run PCA to view fragment groups")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)

    def on_threshold_changed(self):
        """Update threshold label when slider moves"""
        value = self.threshold_slider.value() / 100.0
        self.threshold_label.setText(f"{value:.2f}")
        self.update_plot()

    def set_data(self, fragment_data, pca_results, polarity='negative'):
        """
        Populate widget with fragment data and PCA results

        Args:
            fragment_data: Dict with fragment info from all samples
            pca_results: Dict with PCA loadings, scores, variance
            polarity: 'negative' or 'positive'
        """
        self.fragment_data = fragment_data
        self.pca_results = pca_results
        self.current_polarity = polarity

        # Populate PC selector
        self.pc_combo.clear()
        n_components = pca_results['loadings'].shape[1]
        for i in range(n_components):
            variance = pca_results['variance_explained'][i]
            self.pc_combo.addItem(f"PC{i+1} ({variance:.1f}%)")

        # Populate sample selector
        self.sample_combo.clear()
        if 'sample_names' in fragment_data:
            for name in fragment_data['sample_names']:
                self.sample_combo.addItem(name)

        self.info_label.setText(
            f"{len(fragment_data.get('masses', []))} fragments classified | "
            f"{n_components} PCs available"
        )

        self.update_plot()

    def update_plot(self):
        """Update the fragment groups plot"""
        if self.fragment_data is None or self.pca_results is None:
            return

        # Get current selections
        pc_idx = self.pc_combo.currentIndex()
        if pc_idx < 0:
            return

        sample_idx = self.sample_combo.currentIndex()
        if sample_idx < 0:
            sample_idx = 0

        threshold = self.threshold_slider.value() / 100.0

        # Get loadings for selected PC
        loadings = self.pca_results['loadings'].iloc[:, pc_idx]

        # Filter for high-loading only if checkbox is checked
        if self.high_loading_only.isChecked():
            high_loading_mask = (np.abs(loadings) >= threshold).values
            if not np.any(high_loading_mask):
                self.info_label.setText("No fragments above threshold")
                return

            # Filter data
            fragments = [
                {
                    'mass': self.fragment_data['masses'][i],
                    'formula': self.fragment_data['formulas'][i],
                    'intensity': self.fragment_data['intensities'][sample_idx][i],
                    'polarity': self.current_polarity
                }
                for i in range(len(self.fragment_data['masses']))
                if high_loading_mask[i]
            ]
            loadings_filtered = loadings[high_loading_mask].values
        else:
            # All fragments
            fragments = [
                {
                    'mass': self.fragment_data['masses'][i],
                    'formula': self.fragment_data['formulas'][i],
                    'intensity': self.fragment_data['intensities'][sample_idx][i],
                    'polarity': self.current_polarity
                }
                for i in range(len(self.fragment_data['masses']))
            ]
            loadings_filtered = loadings.values

        # Get sample name
        sample_name = self.sample_combo.currentText() if self.sample_combo.count() > 0 else "Sample"

        # Plot
        pc_num = pc_idx + 1
        title = f"{sample_name} - Fragment Groups (PC{pc_num})"

        self.canvas.plot_fragment_groups(
            fragments,
            loadings_filtered,
            pc_number=pc_num,
            polarity=self.current_polarity,
            loading_threshold=threshold,
            title=title
        )

    def export_data(self):
        """Export fragment classification data with options"""
        if self.fragment_data is None:
            QMessageBox.warning(self, "No Data", "No fragment data to export")
            return

        # Show export options dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Options")
        dialog.setModal(True)
        dialog_layout = QVBoxLayout(dialog)

        # Export scope options
        scope_group = QGroupBox("Export Scope")
        scope_layout = QVBoxLayout()

        scope_all = QRadioButton("All fragments")
        scope_top_n = QRadioButton("Top N fragments by loading")
        scope_variance = QRadioButton("Top fragments explaining X% cumulative variance")
        scope_all.setChecked(True)

        scope_layout.addWidget(scope_all)
        scope_layout.addWidget(scope_top_n)
        scope_layout.addWidget(scope_variance)

        # Top N input
        top_n_layout = QHBoxLayout()
        top_n_layout.addWidget(QLabel("  N ="))
        top_n_spin = QSpinBox()
        top_n_spin.setMinimum(1)
        top_n_spin.setMaximum(1000)
        top_n_spin.setValue(self.top_n_spin.value())
        top_n_spin.setEnabled(False)
        top_n_layout.addWidget(top_n_spin)
        top_n_layout.addStretch()
        scope_layout.addLayout(top_n_layout)

        # Variance % input
        variance_layout = QHBoxLayout()
        variance_layout.addWidget(QLabel("  Variance % ="))
        variance_spin = QSpinBox()
        variance_spin.setMinimum(1)
        variance_spin.setMaximum(100)
        variance_spin.setValue(80)
        variance_spin.setSuffix("%")
        variance_spin.setEnabled(False)
        variance_layout.addWidget(variance_spin)
        variance_layout.addStretch()
        scope_layout.addLayout(variance_layout)

        scope_group.setLayout(scope_layout)
        dialog_layout.addWidget(scope_group)

        # Enable/disable inputs based on radio selection
        def update_inputs():
            top_n_spin.setEnabled(scope_top_n.isChecked())
            variance_spin.setEnabled(scope_variance.isChecked())

        scope_all.toggled.connect(update_inputs)
        scope_top_n.toggled.connect(update_inputs)
        scope_variance.toggled.connect(update_inputs)

        # PC selection
        pc_group = QGroupBox("Principal Component")
        pc_layout = QHBoxLayout()
        pc_combo = QComboBox()
        for i in range(self.pca_results['loadings'].shape[1]):
            variance = self.pca_results['variance_explained'][i]
            pc_combo.addItem(f"PC{i+1} ({variance:.1f}%)")
        pc_combo.setCurrentIndex(self.pc_combo.currentIndex())
        pc_layout.addWidget(QLabel("Select PC:"))
        pc_layout.addWidget(pc_combo)
        pc_group.setLayout(pc_layout)
        dialog_layout.addWidget(pc_group)

        # Include intensities option
        include_intensities = QCheckBox("Include sample/dose intensities")
        include_intensities.setChecked(True)
        dialog_layout.addWidget(include_intensities)

        # Buttons
        button_box = QHBoxLayout()
        ok_btn = QPushButton("Export")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        button_box.addStretch()
        button_box.addWidget(ok_btn)
        button_box.addWidget(cancel_btn)
        dialog_layout.addLayout(button_box)

        if dialog.exec() != QDialog.Accepted:
            return

        # Get export options
        export_options = {
            'scope': 'all' if scope_all.isChecked() else ('top_n' if scope_top_n.isChecked() else 'variance'),
            'top_n': top_n_spin.value(),
            'variance_percent': variance_spin.value(),
            'pc_index': pc_combo.currentIndex(),
            'include_intensities': include_intensities.isChecked()
        }

        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Top Loading Fragments",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                self._export_json(file_path, export_options)
            elif file_path.endswith('.xlsx'):
                self._export_excel(file_path, export_options)
            else:
                self._export_csv(file_path, export_options)

            QMessageBox.information(
                self,
                "Export Success",
                f"Top loading fragments exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n{str(e)}"
            )

    def _get_fragments_to_export(self, export_options):
        """
        Get list of fragment indices to export based on options

        Returns:
            List of (fragment_index, loading_value) tuples
        """
        pc_idx = export_options['pc_index']
        loadings = self.pca_results['loadings'].iloc[:, pc_idx].values

        # Create list of (index, loading_magnitude) sorted by magnitude
        fragments = [(i, abs(loadings[i])) for i in range(len(loadings))]
        fragments.sort(key=lambda x: x[1], reverse=True)

        if export_options['scope'] == 'all':
            return [(i, loadings[i]) for i, _ in fragments]

        elif export_options['scope'] == 'top_n':
            n = min(export_options['top_n'], len(fragments))
            return [(i, loadings[i]) for i, _ in fragments[:n]]

        elif export_options['scope'] == 'variance':
            # Calculate cumulative explained variance from top loadings
            target_variance = export_options['variance_percent']

            # Get total sum of squared loadings for this PC
            total_ss = np.sum(loadings ** 2)

            cumulative_ss = 0
            selected = []
            for i, mag in fragments:
                selected.append((i, loadings[i]))
                cumulative_ss += loadings[i] ** 2
                cumulative_variance = (cumulative_ss / total_ss) * 100
                if cumulative_variance >= target_variance:
                    break

            return selected

        return []

    def _export_csv(self, file_path, export_options=None):
        """Export to CSV with optional filtering and intensities"""
        if export_options is None:
            export_options = {'scope': 'all', 'include_intensities': False, 'pc_index': 0}

        # Get fragments to export
        fragments_to_export = self._get_fragments_to_export(export_options)

        data = []
        for frag_idx, loading in fragments_to_export:
            mass = self.fragment_data['masses'][frag_idx]
            formula = self.fragment_data['formulas'][frag_idx]

            # Get chemical family from database (or calculate if not provided)
            if 'families' in self.fragment_data and frag_idx < len(self.fragment_data['families']):
                chemical_family = self.fragment_data['families'][frag_idx]
                # Still classify for other properties (DBE, H/C ratio, etc.)
                props = classify_fragment(formula, mass, self.current_polarity)
                # Override the chemical family with database value
                props.chemical_family = chemical_family
            else:
                # Fallback: calculate if not provided (backward compatibility)
                props = classify_fragment(formula, mass, self.current_polarity)

            row = {
                'mass': mass,
                'formula': formula,
                'chemical_family': props.chemical_family,
                'dbe': props.dbe,
                'h_c_ratio': props.h_c_ratio,
                'saturation': props.saturation_class,
                'aromatic_marker': props.is_aromatic_marker
            }

            # Add loading for selected PC
            pc_idx = export_options['pc_index']
            row[f'PC{pc_idx+1}_loading'] = loading

            # Add loadings for all other PCs
            for other_pc_idx in range(self.pca_results['loadings'].shape[1]):
                if other_pc_idx != pc_idx:
                    row[f'PC{other_pc_idx+1}_loading'] = self.pca_results['loadings'].iloc[frag_idx, other_pc_idx]

            # Add intensities if requested
            if export_options['include_intensities']:
                for j, sample_name in enumerate(self.fragment_data['sample_names']):
                    row[f'intensity_{sample_name}'] = self.fragment_data['intensities'][j][frag_idx]

                    # Add standard deviation if available
                    if 'intensities_std' in self.fragment_data:
                        row[f'std_{sample_name}'] = self.fragment_data['intensities_std'][j][frag_idx]

            data.append(row)

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

    def _export_json(self, file_path, export_options=None):
        """Export to JSON with optional filtering and intensities"""
        if export_options is None:
            export_options = {'scope': 'all', 'include_intensities': False, 'pc_index': 0}

        # Get fragments to export
        fragments_to_export = self._get_fragments_to_export(export_options)

        data = {
            'metadata': {
                'polarity': self.current_polarity,
                'n_fragments_total': len(self.fragment_data['masses']),
                'n_fragments_exported': len(fragments_to_export),
                'n_components': self.pca_results['loadings'].shape[1],
                'export_scope': export_options['scope'],
                'selected_pc': f"PC{export_options['pc_index'] + 1}",
                'include_intensities': export_options['include_intensities']
            },
            'fragments': []
        }

        for frag_idx, loading in fragments_to_export:
            mass = self.fragment_data['masses'][frag_idx]
            formula = self.fragment_data['formulas'][frag_idx]

            # Get chemical family from database (or calculate if not provided)
            if 'families' in self.fragment_data and frag_idx < len(self.fragment_data['families']):
                chemical_family = self.fragment_data['families'][frag_idx]
                # Still classify for other properties (DBE, H/C ratio, etc.)
                props = classify_fragment(formula, mass, self.current_polarity)
                # Override the chemical family with database value
                props.chemical_family = chemical_family
            else:
                # Fallback: calculate if not provided (backward compatibility)
                props = classify_fragment(formula, mass, self.current_polarity)

            frag_data = {
                'mass': mass,
                'formula': formula,
                'chemical_family': props.chemical_family,
                'properties': {
                    'dbe': props.dbe,
                    'h_c_ratio': props.h_c_ratio,
                    'saturation': props.saturation_class,
                    'c_count': props.c_count,
                    'h_count': props.h_count,
                    'o_count': props.o_count,
                    'aromatic_marker': props.is_aromatic_marker,
                    'aromatic_marker_name': props.aromatic_marker_name
                },
                'pca_loadings': {}
            }

            # Add loadings
            for pc_idx in range(self.pca_results['loadings'].shape[1]):
                frag_data['pca_loadings'][f'PC{pc_idx+1}'] = float(
                    self.pca_results['loadings'].iloc[frag_idx, pc_idx]
                )

            # Add intensities if requested
            if export_options['include_intensities']:
                frag_data['intensities'] = {}
                for j, sample_name in enumerate(self.fragment_data['sample_names']):
                    intensity_data = {
                        'mean': float(self.fragment_data['intensities'][j][frag_idx])
                    }
                    # Add standard deviation if available
                    if 'intensities_std' in self.fragment_data:
                        intensity_data['std'] = float(self.fragment_data['intensities_std'][j][frag_idx])
                    frag_data['intensities'][sample_name] = intensity_data

            data['fragments'].append(frag_data)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _export_excel(self, file_path, export_options=None):
        """Export to Excel with multiple sheets"""
        if export_options is None:
            export_options = {'scope': 'all', 'include_intensities': False, 'pc_index': 0}

        # Get fragments to export
        fragments_to_export = self._get_fragments_to_export(export_options)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Sheet 1: Fragment Properties and Loadings
            props_data = []
            for frag_idx, loading in fragments_to_export:
                mass = self.fragment_data['masses'][frag_idx]
                formula = self.fragment_data['formulas'][frag_idx]

                # Get chemical family from database
                if 'families' in self.fragment_data and frag_idx < len(self.fragment_data['families']):
                    chemical_family = self.fragment_data['families'][frag_idx]
                    props = classify_fragment(formula, mass, self.current_polarity)
                    props.chemical_family = chemical_family
                else:
                    props = classify_fragment(formula, mass, self.current_polarity)

                row = {
                    'mass': mass,
                    'formula': formula,
                    'chemical_family': props.chemical_family,
                    'dbe': props.dbe,
                    'h_c_ratio': props.h_c_ratio,
                    'saturation': props.saturation_class,
                    'aromatic_marker': 'Yes' if props.is_aromatic_marker else 'No',
                }

                # Add loadings for all PCs
                for pc_idx in range(self.pca_results['loadings'].shape[1]):
                    row[f'PC{pc_idx+1}_loading'] = self.pca_results['loadings'].iloc[frag_idx, pc_idx]

                props_data.append(row)

            props_df = pd.DataFrame(props_data)
            props_df.to_excel(writer, sheet_name='Fragment_Properties', index=False)

            # Sheet 2: Intensities (if requested)
            if export_options['include_intensities']:
                intensity_data = []
                for frag_idx, loading in fragments_to_export:
                    mass = self.fragment_data['masses'][frag_idx]
                    formula = self.fragment_data['formulas'][frag_idx]

                    row = {
                        'mass': mass,
                        'formula': formula
                    }

                    # Add intensities for each sample/dose
                    for j, sample_name in enumerate(self.fragment_data['sample_names']):
                        row[f'{sample_name}_intensity'] = self.fragment_data['intensities'][j][frag_idx]

                        # Add standard deviation if available
                        if 'intensities_std' in self.fragment_data:
                            row[f'{sample_name}_std'] = self.fragment_data['intensities_std'][j][frag_idx]

                    intensity_data.append(row)

                intensity_df = pd.DataFrame(intensity_data)
                intensity_df.to_excel(writer, sheet_name='Intensities', index=False)

            # Sheet 3: Export metadata
            metadata_data = {
                'Parameter': [
                    'Polarity',
                    'Total Fragments',
                    'Exported Fragments',
                    'Export Scope',
                    'Selected PC',
                    'Include Intensities',
                    'Number of PCs',
                    'Number of Samples/Doses'
                ],
                'Value': [
                    self.current_polarity,
                    len(self.fragment_data['masses']),
                    len(fragments_to_export),
                    export_options['scope'],
                    f"PC{export_options['pc_index'] + 1}",
                    'Yes' if export_options['include_intensities'] else 'No',
                    self.pca_results['loadings'].shape[1],
                    len(self.fragment_data['sample_names'])
                ]
            }
            metadata_df = pd.DataFrame(metadata_data)
            metadata_df.to_excel(writer, sheet_name='Export_Metadata', index=False)


class ChemicalMetricsWidget(QWidget):
    """
    Widget for displaying chemical metrics across all samples
    Shows C6H-/C4H- ratios, H-deficient fractions, etc.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.metrics_data = None
        self.analyzer = CrosslinkingAnalyzer()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create sub-tabs for table and plot views
        self.sub_tabs = QTabWidget()

        # Table view
        self.table_widget = self._create_table_view()
        self.sub_tabs.addTab(self.table_widget, "Metrics Table")

        # Plot view
        self.plot_widget = self._create_plot_view()
        self.sub_tabs.addTab(self.plot_widget, "Trends Plot")

        layout.addWidget(self.sub_tabs)

        # Export buttons
        export_layout = QHBoxLayout()

        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(csv_btn)

        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(json_btn)

        plot_btn = QPushButton("Export Plot")
        plot_btn.clicked.connect(self.export_plot)
        export_layout.addWidget(plot_btn)

        export_layout.addStretch()
        layout.addLayout(export_layout)

        # Info label
        self.info_label = QLabel("Load data and run PCA to view chemical metrics")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)

    def _create_table_view(self):
        """Create table widget for metrics"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        return widget

    def _create_plot_view(self):
        """Create plot widget for trends"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Create matplotlib canvas
        self.plot_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, widget)

        layout.addWidget(self.plot_toolbar)
        layout.addWidget(self.plot_canvas)

        return widget

    def set_data(self, fragment_data, sample_names, polarity='negative'):
        """
        Calculate and display metrics for all samples

        Args:
            fragment_data: Dict with fragment masses, formulas, intensities per sample
            sample_names: List of sample names
            polarity: Ion polarity
        """
        self.analyzer = CrosslinkingAnalyzer()

        # Calculate metrics for each sample (or dose group if averaged)
        n_data_points = len(fragment_data['intensities'])
        for i in range(min(len(sample_names), n_data_points)):
            sample_name = sample_names[i] if i < len(sample_names) else f"Sample {i}"

            # Build fragment data dict for this sample/dose
            sample_frag_data = {}
            for j, formula in enumerate(fragment_data['formulas']):
                sample_frag_data[formula] = {
                    'mass': fragment_data['masses'][j],
                    'intensity': fragment_data['intensities'][i][j]
                }

            # Calculate metrics
            metrics = self.analyzer.calculate_sample_metrics(
                sample_name,
                sample_frag_data,
                polarity
            )
            self.analyzer.add_sample(metrics)

        # Update displays
        self._update_table()
        self._update_plot()

        self.info_label.setText(f"{len(sample_names)} samples analyzed")

    def _update_table(self):
        """Update metrics table"""
        df = self.analyzer.get_trends()

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        for i, row in df.iterrows():
            for j, col in enumerate(df.columns):
                value = row[col]
                if isinstance(value, float):
                    item = QTableWidgetItem(f"{value:.4f}")
                else:
                    item = QTableWidgetItem(str(value))
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def _update_plot(self):
        """Update trends plot"""
        df = self.analyzer.get_trends()

        self.plot_canvas.figure.clear()

        # Create subplots
        ax1 = self.plot_canvas.figure.add_subplot(2, 1, 1)
        ax2 = self.plot_canvas.figure.add_subplot(2, 1, 2)

        # Plot C6H-/C4H- ratio
        if 'c6h_to_c4h_ratio' in df.columns and df['c6h_to_c4h_ratio'].notna().any():
            ax1.plot(df.index, df['c6h_to_c4h_ratio'], 'o-', linewidth=2, markersize=8)
            ax1.set_ylabel('C6H⁻/C4H⁻ Ratio', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.set_xticks(df.index)
            ax1.set_xticklabels(df['sample_name'], rotation=45, ha='right')

        # Plot H-deficient fraction
        if 'h_deficient_fraction' in df.columns and df['h_deficient_fraction'].notna().any():
            ax2.plot(df.index, df['h_deficient_fraction'], 's-', linewidth=2, markersize=8, color='purple')
            ax2.set_ylabel('H-deficient Fraction', fontweight='bold')
            ax2.set_xlabel('Sample', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.set_xticks(df.index)
            ax2.set_xticklabels(df['sample_name'], rotation=45, ha='right')

        self.plot_canvas.figure.tight_layout()
        self.plot_canvas.draw()

    def export_csv(self):
        """Export metrics to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metrics CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            try:
                self.analyzer.export_to_csv(file_path)
                QMessageBox.information(self, "Success", f"Exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")

    def export_json(self):
        """Export metrics to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metrics JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.analyzer.export_to_json(file_path)
                QMessageBox.information(self, "Success", f"Exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")

    def export_plot(self):
        """Export trends plot"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Plot", "", "PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if file_path:
            try:
                self.plot_canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", f"Plot saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")


class FragmentAnalysisTab(QWidget):
    """
    Main Fragment Analysis tab with sub-tabs for
    Fragment Groups and Chemical Metrics
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Fragment Analysis - Chemical Classification & Metrics")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Sub-tabs
        self.tabs = QTabWidget()

        # Top Loading Fragments tab (NEW - most useful, so first)
        self.top_loading = TopLoadingFragmentsWidget()
        self.tabs.addTab(self.top_loading, "Top Loading Fragments")

        # Fragment Groups tab
        self.fragment_groups = FragmentGroupsWidget()
        self.tabs.addTab(self.fragment_groups, "Fragment Groups")

        # Chemical Metrics tab
        self.chemical_metrics = ChemicalMetricsWidget()
        self.tabs.addTab(self.chemical_metrics, "Chemical Metrics")

        layout.addWidget(self.tabs)

    def set_data(self, fragment_data, pca_results, sample_names, polarity='negative', sample_info=None):
        """
        Populate all sub-tabs with data

        Args:
            fragment_data: Dict with masses, formulas, intensities
            pca_results: Dict with PCA loadings, scores, variance
            sample_names: List of sample names (should match intensities length)
            polarity: Ion polarity
            sample_info: List of dicts with sample metadata (name, dose, etc.)
        """
        # Use sample_names from fragment_data if available (more reliable for dose-averaged data)
        actual_sample_names = fragment_data.get('sample_names', sample_names)

        # Ensure fragment_data has correct sample_names
        fragment_data['sample_names'] = actual_sample_names

        # Build sample_info if not provided - use dose_values if available
        if sample_info is None:
            dose_values = fragment_data.get('dose_values', None)
            if dose_values:
                # Dose-averaged data: use dose values
                sample_info = [
                    {'name': name, 'dose': dose}
                    for name, dose in zip(actual_sample_names, dose_values)
                ]
            else:
                # Individual samples: use index as dose
                sample_info = [
                    {'name': name, 'dose': i}
                    for i, name in enumerate(actual_sample_names)
                ]

        # Populate all sub-tabs
        self.top_loading.set_data(fragment_data, pca_results, sample_info, polarity)
        self.fragment_groups.set_data(fragment_data, pca_results, polarity)
        self.chemical_metrics.set_data(fragment_data, actual_sample_names, polarity)
