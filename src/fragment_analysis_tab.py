"""
Fragment Analysis Tab - Chemical Classification and Metrics
Separate tab that activates after PCA completion
Shows fragment groups and chemical metrics across all samples
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QComboBox, QSlider, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QSpinBox, QFormLayout, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import numpy as np
import pandas as pd
from pathlib import Path
import json

from fragment_group_plotting import FragmentGroupPlotCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from fragment_classifier import classify_fragment, AROMATIC_MARKERS
from crosslinking_metrics import CrosslinkingAnalyzer, SampleMetrics


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
        loadings = self.pca_results['loadings'][:, pc_idx]

        # Filter for high-loading only if checkbox is checked
        if self.high_loading_only.isChecked():
            high_loading_mask = np.abs(loadings) >= threshold
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
            loadings_filtered = loadings[high_loading_mask]
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
            loadings_filtered = loadings

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
        """Export fragment classification data"""
        if self.fragment_data is None:
            QMessageBox.warning(self, "No Data", "No fragment data to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Fragment Groups",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                self._export_json(file_path)
            else:
                self._export_csv(file_path)

            QMessageBox.information(
                self,
                "Export Success",
                f"Fragment data exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n{str(e)}"
            )

    def _export_csv(self, file_path):
        """Export to CSV"""
        data = []
        for i, mass in enumerate(self.fragment_data['masses']):
            formula = self.fragment_data['formulas'][i]
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

            # Add loadings for each PC
            for pc_idx in range(self.pca_results['loadings'].shape[1]):
                row[f'PC{pc_idx+1}_loading'] = self.pca_results['loadings'][i, pc_idx]

            data.append(row)

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

    def _export_json(self, file_path):
        """Export to JSON"""
        data = {
            'metadata': {
                'polarity': self.current_polarity,
                'n_fragments': len(self.fragment_data['masses']),
                'n_components': self.pca_results['loadings'].shape[1]
            },
            'fragments': []
        }

        for i, mass in enumerate(self.fragment_data['masses']):
            formula = self.fragment_data['formulas'][i]
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
                    self.pca_results['loadings'][i, pc_idx]
                )

            data['fragments'].append(frag_data)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


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

        # Calculate metrics for each sample
        for i, sample_name in enumerate(sample_names):
            # Build fragment data dict for this sample
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

        # Fragment Groups tab
        self.fragment_groups = FragmentGroupsWidget()
        self.tabs.addTab(self.fragment_groups, "Fragment Groups")

        # Chemical Metrics tab
        self.chemical_metrics = ChemicalMetricsWidget()
        self.tabs.addTab(self.chemical_metrics, "Chemical Metrics")

        layout.addWidget(self.tabs)

    def set_data(self, fragment_data, pca_results, sample_names, polarity='negative'):
        """
        Populate all sub-tabs with data

        Args:
            fragment_data: Dict with masses, formulas, intensities
            pca_results: Dict with PCA loadings, scores, variance
            sample_names: List of sample names
            polarity: Ion polarity
        """
        # Add sample names to fragment data
        fragment_data['sample_names'] = sample_names

        # Populate both sub-tabs
        self.fragment_groups.set_data(fragment_data, pca_results, polarity)
        self.chemical_metrics.set_data(fragment_data, sample_names, polarity)
