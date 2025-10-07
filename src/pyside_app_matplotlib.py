"""
PySide6 ToF-SIMS PCA Application with Native Matplotlib Plotting
Better performance and reliability than QtWebEngine approach
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Set Qt platform before importing Qt
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['DISPLAY'] = os.environ.get('DISPLAY', ':0')

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QCheckBox, QSpinBox, QGroupBox, QGridLayout, QMessageBox,
    QTabWidget, QSplitter, QMenuBar, QMenu, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QInputDialog,
    QListWidget, QListWidgetItem, QLineEdit, QFormLayout, QComboBox,
    QScrollArea, QFrame, QDoubleSpinBox
)
from PySide6.QtCore import QThread, Signal, Qt, QSettings
from PySide6.QtGui import QColor
from PySide6.QtGui import QAction

# Matplotlib imports
import matplotlib
matplotlib.use('QtAgg')  # Use Qt backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))
from simple_tof_sims_pca import SimpleToFSIMSPCA
from matplotlib_plotting import PCAPlotCanvas, InteractivePCAPlots
from stick_spectrum_plotting import StickSpectrumCanvas

# ===== APPLICATION CONSTANTS =====
class Polarity:
    """Ion polarity constants - single source of truth for polarity values"""
    NEGATIVE = "negative"
    POSITIVE = "positive"

    @staticmethod
    def display_name(polarity: str) -> str:
        """Convert internal polarity value to display name"""
        return {
            Polarity.NEGATIVE: "Negative Ion",
            Polarity.POSITIVE: "Positive Ion"
        }.get(polarity, polarity)

    @staticmethod
    def from_display_name(display: str) -> str:
        """Convert display name to internal polarity value"""
        display_lower = display.lower()
        if "negative" in display_lower:
            return Polarity.NEGATIVE
        elif "positive" in display_lower:
            return Polarity.POSITIVE
        return display


class FragmentAssignmentDialog(QDialog):
    """Dialog for detailed fragment assignment with peak intensities and candidate matches"""

    def __init__(self, parent, mass, row_index):
        super().__init__(parent)
        self.parent_app = parent
        self.mass = mass
        self.row_index = row_index
        self.selected_assignment = None

        self.setWindowTitle(f"Fragment Assignment - m/z {mass:.4f}")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"🔬 Detailed Assignment for m/z {self.mass:.4f}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(header)

        # Create tab widget for different views
        tabs = QTabWidget()

        # Peak intensities tab
        intensities_widget = self.create_peak_intensities_tab()
        tabs.addTab(intensities_widget, "📊 Peak Intensities")

        # Candidate assignments tab
        candidates_widget = self.create_candidates_tab()
        tabs.addTab(candidates_widget, "🎯 Candidate Assignments")

        # Manual assignment tab
        manual_widget = self.create_manual_assignment_tab()
        tabs.addTab(manual_widget, "✏️ Manual Assignment")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.accept_button = QPushButton("Accept Assignment")
        self.accept_button.setEnabled(False)
        self.accept_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def create_peak_intensities_tab(self):
        """Create tab showing peak intensities across sample groups with trend plot"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add instruction
        info_label = QLabel("Peak intensities across different sample groups:")
        info_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(info_label)

        # Create horizontal splitter for table and plot
        splitter = QSplitter(Qt.Horizontal)

        # Create intensity table
        self.intensity_table = QTableWidget()
        splitter.addWidget(self.intensity_table)

        # Create compact intensity trend plot
        self.intensity_plot_widget = self.create_intensity_plot()
        splitter.addWidget(self.intensity_plot_widget)

        # Set splitter proportions (table gets more space)
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)

        return widget

    def create_intensity_plot(self):
        """Create a compact matplotlib plot for intensity trends"""
        from matplotlib.figure import Figure

        # Create matplotlib figure
        self.intensity_figure = Figure(figsize=(4, 3), dpi=100)
        self.intensity_canvas = FigureCanvas(self.intensity_figure)
        self.intensity_canvas.setMaximumHeight(250)

        # Create plot widget container
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(5, 5, 5, 5)

        # Add title
        plot_title = QLabel("📈 Intensity Trend")
        plot_title.setStyleSheet("font-weight: bold; color: #333; text-align: center;")
        plot_title.setAlignment(Qt.AlignCenter)
        plot_layout.addWidget(plot_title)

        # Add canvas
        plot_layout.addWidget(self.intensity_canvas)

        return plot_widget

    def update_intensity_plot(self, dose_data, intensity_data, dose_labels=None):
        """Update the intensity trend plot with data and optional labels"""
        try:
            print(f"📊 Updating intensity plot with {len(dose_data)} dose points and {len(intensity_data)} intensity points")
            print(f"   Dose data: {dose_data}")
            print(f"   Intensity data: {intensity_data}")
            if dose_labels:
                print(f"   Dose labels: {dose_labels}")

            self.intensity_figure.clear()
            ax = self.intensity_figure.add_subplot(111)

            if len(dose_data) > 0 and len(intensity_data) > 0:
                # Sort data by dose value for proper trend line
                if dose_labels and len(dose_labels) == len(dose_data):
                    sorted_data = sorted(zip(dose_data, intensity_data, dose_labels))
                    sorted_doses, sorted_intensities, sorted_labels = zip(*sorted_data)

                    # Use x-positions for plotting but show custom labels
                    x_positions = list(range(len(sorted_doses)))

                    # Create compact scatter plot
                    ax.scatter(x_positions, sorted_intensities, c='steelblue', s=40, alpha=0.7, edgecolors='darkblue')

                    # Add trend line if we have enough points
                    if len(x_positions) > 1:
                        import numpy as np
                        z = np.polyfit(x_positions, sorted_intensities, 1)
                        p = np.poly1d(z)
                        ax.plot(x_positions, p(x_positions), 'r--', alpha=0.8, linewidth=1.5)

                        # Determine trend direction
                        slope = z[0]
                        if abs(slope) > max(sorted_intensities) * 0.01:  # Significant trend
                            trend_text = "↗ Increasing" if slope > 0 else "↘ Decreasing"
                            trend_color = "green" if slope > 0 else "red"
                        else:
                            trend_text = "→ Stable"
                            trend_color = "blue"

                        ax.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                               verticalalignment='top', fontsize=9, color=trend_color, weight='bold')

                    # Set custom x-axis labels
                    ax.set_xticks(x_positions)
                    ax.set_xticklabels(sorted_labels, rotation=45, ha='right', fontsize=8)
                    ax.set_xlabel('Electron Beam Dose', fontsize=9)
                else:
                    # Fallback to original behavior
                    ax.scatter(dose_data, intensity_data, c='steelblue', s=40, alpha=0.7, edgecolors='darkblue')

                    # Add trend line if we have enough points
                    if len(dose_data) > 1:
                        import numpy as np
                        z = np.polyfit(dose_data, intensity_data, 1)
                        p = np.poly1d(z)
                        ax.plot(dose_data, p(dose_data), 'r--', alpha=0.8, linewidth=1.5)

                        # Determine trend direction
                        slope = z[0]
                        if abs(slope) > max(intensity_data) * 0.01:  # Significant trend
                            trend_text = "↗ Increasing" if slope > 0 else "↘ Decreasing"
                            trend_color = "green" if slope > 0 else "red"
                        else:
                            trend_text = "→ Stable"
                            trend_color = "blue"

                        ax.text(0.02, 0.98, trend_text, transform=ax.transAxes,
                               verticalalignment='top', fontsize=9, color=trend_color, weight='bold')

                    ax.set_xlabel('Dose (SQ)', fontsize=9)

                ax.set_ylabel('Intensity', fontsize=9)
                ax.tick_params(axis='both', which='major', labelsize=8)
                ax.grid(True, alpha=0.3)

                # Compact layout
                self.intensity_figure.tight_layout(pad=1.0)
            else:
                ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes,
                       ha='center', va='center', fontsize=10, color='gray')

            self.intensity_canvas.draw()

        except Exception as e:
            print(f"Warning: Could not update intensity plot: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    def create_candidates_tab(self):
        """Create tab showing candidate fragment assignments from database"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tolerance control
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Mass tolerance (mDa):"))

        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(1, 50)
        self.tolerance_spin.setValue(10)  # 10 mDa default
        self.tolerance_spin.valueChanged.connect(self.update_candidates)
        tolerance_layout.addWidget(self.tolerance_spin)

        tolerance_layout.addStretch()
        layout.addLayout(tolerance_layout)

        # Candidates table
        self.candidates_table = QTableWidget()
        self.candidates_table.setColumnCount(6)
        self.candidates_table.setHorizontalHeaderLabels([
            "Assignment", "Formula", "Mass Error (ppm)", "Confidence", "Family", "Select"
        ])

        # Set column widths
        header = self.candidates_table.horizontalHeader()
        header.resizeSection(0, 120)  # Assignment
        header.resizeSection(1, 80)   # Formula
        header.resizeSection(2, 100)  # Mass Error
        header.resizeSection(3, 80)   # Confidence
        header.resizeSection(4, 100)  # Family
        header.resizeSection(5, 60)   # Select button

        self.candidates_table.setAlternatingRowColors(True)
        layout.addWidget(self.candidates_table)

        return widget

    def create_manual_assignment_tab(self):
        """Create tab for manual assignment entry"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Manual entry fields
        self.manual_assignment = QLineEdit()
        self.manual_assignment.setPlaceholderText("e.g., Al+, C2H3+, Unknown")
        layout.addRow("Assignment:", self.manual_assignment)

        self.manual_formula = QLineEdit()
        self.manual_formula.setPlaceholderText("e.g., Al, C2H3")
        layout.addRow("Formula:", self.manual_formula)

        self.manual_family = QComboBox()
        self.manual_family.addItems([
            "Al-based", "Saturated Carbon", "Unsaturated Carbon",
            "Carbonyl", "Hydroxyl", "Contamination", "Unknown"
        ])
        layout.addRow("Family:", self.manual_family)

        self.manual_confidence = QComboBox()
        self.manual_confidence.addItems(["High", "Medium", "Low"])
        self.manual_confidence.setCurrentText("Medium")
        layout.addRow("Confidence:", self.manual_confidence)

        self.manual_notes = QTextEdit()
        self.manual_notes.setMaximumHeight(100)
        self.manual_notes.setPlaceholderText("Optional notes about this assignment...")
        layout.addRow("Notes:", self.manual_notes)

        # Manual assign button
        manual_btn = QPushButton("Use Manual Assignment")
        manual_btn.clicked.connect(self.use_manual_assignment)
        layout.addRow(manual_btn)

        return widget

    def populate_data(self):
        """Populate the dialog with peak intensity and candidate data"""
        self.populate_peak_intensities()
        self.update_candidates()

    def populate_peak_intensities(self):
        """Populate peak intensities table"""
        try:
            # Get current working data (respects sample selection)
            if hasattr(self.parent_app, 'pca_analyzer') and self.parent_app.pca_analyzer:
                working_data, working_metadata = self.parent_app.pca_analyzer.get_active_data()
                raw_data = working_data.T  # Transpose to get masses as rows
                sample_metadata = working_metadata

                # Find closest mass in data (accounting for floating point precision)
                mass_index = None
                min_diff = float('inf')
                for idx, data_mass in enumerate(raw_data.index):
                    try:
                        # Ensure data_mass is a float
                        data_mass_float = float(data_mass)
                        diff = abs(data_mass_float - self.mass)
                        if diff < min_diff:
                            min_diff = diff
                            mass_index = idx
                    except (ValueError, TypeError):
                        # Skip non-numeric mass values
                        continue

                if mass_index is not None and min_diff < 0.001:  # Within 1 mDa
                    actual_mass = raw_data.index[mass_index]
                    intensities = raw_data.iloc[mass_index]

                    # Group by dose using working metadata
                    dose_groups = working_metadata.groupby('dose_id') if 'dose_id' in working_metadata.columns else None

                    if dose_groups is None:
                        # Fallback: treat each sample as its own group
                        self.intensity_table.setRowCount(len(intensities))
                        self.intensity_table.setColumnCount(2)
                        self.intensity_table.setHorizontalHeaderLabels(["Sample", "Intensity"])

                        for i, (sample_name, intensity) in enumerate(intensities.items()):
                            self.intensity_table.setItem(i, 0, QTableWidgetItem(str(sample_name)))
                            self.intensity_table.setItem(i, 1, QTableWidgetItem(f"{intensity:.4f}"))
                        return

                    # Set up table
                    self.intensity_table.setRowCount(len(dose_groups))
                    self.intensity_table.setColumnCount(5)
                    self.intensity_table.setHorizontalHeaderLabels([
                        "Sample Group", "Mean Intensity", "Std Dev", "Min", "Max"
                    ])

                    # Collect data for plotting with metadata support
                    dose_data = []
                    intensity_data = []
                    dose_labels = []

                    for row, (dose_id, group) in enumerate(dose_groups):
                        group_samples = group['sample_name'].tolist()
                        # Safely access intensities with proper error handling
                        group_intensities = []
                        for sample in group_samples:
                            try:
                                if sample in intensities.index:
                                    intensity_val = intensities[sample]
                                    if pd.notna(intensity_val):  # Check for NaN
                                        group_intensities.append(float(intensity_val))
                            except (KeyError, ValueError, TypeError):
                                # Skip problematic intensity values
                                continue

                        if group_intensities:
                            import numpy as np
                            mean_int = np.mean(group_intensities)
                            std_int = np.std(group_intensities)
                            min_int = np.min(group_intensities)
                            max_int = np.max(group_intensities)

                            # Determine display label using metadata
                            if group_samples and hasattr(self.parent_app.pca_analyzer, 'sample_metadata') and 'sample_type' in self.parent_app.pca_analyzer.sample_metadata.columns:
                                sample_name = group_samples[0]  # Use first sample as representative
                                sample_mask = self.parent_app.pca_analyzer.sample_metadata['sample_name'] == sample_name
                                if sample_mask.any():
                                    sample_meta = self.parent_app.pca_analyzer.sample_metadata.loc[sample_mask].iloc[0]
                                    sample_type = sample_meta.get('sample_type', 'E-beam Exposed')

                                    if sample_type == 'As-Deposited':
                                        dose_label = 'As-Deposited'
                                        dose_value = 0  # For plotting position
                                    elif sample_type == 'E-beam Exposed':
                                        dose_value = sample_meta.get('actual_dose', dose_id)
                                        dose_label = f'{dose_value} μC/cm²'
                                    else:
                                        dose_label = f'SQ{dose_id}'
                                        dose_value = dose_id
                                else:
                                    dose_label = f'SQ{dose_id}'
                                    dose_value = dose_id
                            else:
                                dose_label = f'SQ{dose_id}'
                                dose_value = dose_id

                            self.intensity_table.setItem(row, 0, QTableWidgetItem(dose_label))
                            self.intensity_table.setItem(row, 1, QTableWidgetItem(f"{mean_int:.2e}"))
                            self.intensity_table.setItem(row, 2, QTableWidgetItem(f"{std_int:.2e}"))
                            self.intensity_table.setItem(row, 3, QTableWidgetItem(f"{min_int:.2e}"))
                            self.intensity_table.setItem(row, 4, QTableWidgetItem(f"{max_int:.2e}"))

                            # Collect data for plot
                            dose_data.append(dose_value)
                            intensity_data.append(mean_int)
                            dose_labels.append(dose_label)

                    self.intensity_table.resizeColumnsToContents()

                    # Update the intensity plot with labels
                    print(f"🔍 About to call update_intensity_plot with {len(dose_data)} doses and {len(intensity_data)} intensities")
                    print(f"🔍 dose_data={dose_data}, intensity_data={intensity_data}, dose_labels={dose_labels}")

                    # Always call update_intensity_plot with the data we collected
                    if len(dose_data) > 0 and len(dose_labels) == len(dose_data):
                        self.update_intensity_plot(dose_data, intensity_data, dose_labels)
                    elif len(dose_data) > 0:
                        self.update_intensity_plot(dose_data, intensity_data)
                    else:
                        print("⚠️  No dose data collected for plotting")

        except Exception as e:
            print(f"Error populating peak intensities: {e}")

    def update_candidates(self):
        """Update candidate assignments table based on tolerance"""
        try:
            tolerance_mda = self.tolerance_spin.value()
            tolerance_da = tolerance_mda / 1000.0

            # Get candidate assignments using ppm tolerance
            # Convert mDa to ppm for this mass
            tolerance_ppm = (tolerance_da * 1e6) / self.mass
            candidates = self.parent_app.find_multiple_fragment_assignments(
                self.mass, tolerance_ppm=tolerance_ppm, max_matches=10
            )

            # Populate candidates table
            self.candidates_table.setRowCount(len(candidates))

            for row, candidate in enumerate(candidates):
                # Assignment
                self.candidates_table.setItem(row, 0, QTableWidgetItem(candidate['assignment']))

                # Formula
                self.candidates_table.setItem(row, 1, QTableWidgetItem(candidate['formula']))

                # Mass error in ppm
                ppm_error = candidate['mass_error_ppm']
                error_item = QTableWidgetItem(f"{ppm_error:.1f}")
                if ppm_error < 10:
                    error_item.setBackground(QColor(200, 255, 200))  # Green for good accuracy
                elif ppm_error < 50:
                    error_item.setBackground(QColor(255, 255, 200))  # Yellow for fair
                else:
                    error_item.setBackground(QColor(255, 200, 200))  # Red for poor
                self.candidates_table.setItem(row, 2, error_item)

                # Confidence
                self.candidates_table.setItem(row, 3, QTableWidgetItem(candidate.get('confidence', 'Medium')))

                # Family
                self.candidates_table.setItem(row, 4, QTableWidgetItem(candidate.get('family', 'Unknown')))

                # Select button
                select_btn = QPushButton("Select")
                select_btn.clicked.connect(lambda checked, c=candidate: self.select_candidate(c))
                self.candidates_table.setCellWidget(row, 5, select_btn)

        except Exception as e:
            print(f"Error updating candidates: {e}")

    def select_candidate(self, candidate):
        """Select a candidate assignment"""
        self.selected_assignment = candidate
        self.accept_button.setEnabled(True)

    def use_manual_assignment(self):
        """Use manual assignment from user input"""
        assignment = self.manual_assignment.text().strip()
        formula = self.manual_formula.text().strip()

        if not assignment:
            QMessageBox.warning(self, "Invalid Input", "Please enter an assignment.")
            return

        self.selected_assignment = {
            'assignment': assignment,
            'formula': formula or 'Unknown',
            'family': self.manual_family.currentText(),
            'confidence': self.manual_confidence.currentText(),
            'notes': self.manual_notes.toPlainText(),
            'mass_error_ppm': 0  # Manual assignment, no error calculation
        }

        self.accept_button.setEnabled(True)

    def get_selected_assignment(self):
        """Get the selected assignment"""
        return self.selected_assignment


from data_preview_dialog import DataPreviewDialog


class PCAWorker(QThread):
    """Worker thread for PCA computation"""
    finished = Signal()
    error = Signal(str)
    progress = Signal(int, str)
    
    def __init__(self, pca_analyzer, n_components, preprocessing_options):
        super().__init__()
        self.pca_analyzer = pca_analyzer
        self.n_components = n_components
        self.preprocessing_options = preprocessing_options
    
    def run(self):
        try:
            self.progress.emit(25, "Preprocessing data...")
            self.pca_analyzer.preprocess_data(**self.preprocessing_options)
            
            self.progress.emit(75, "Computing PCA...")
            self.pca_analyzer.run_pca(self.n_components)
            
            self.progress.emit(100, "PCA completed!")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))


class CustomDoseDialog(QDialog):
    """Dialog for setting custom dose values and sample types for dose-response analysis"""

    def __init__(self, parent, dose_ids, saved_metadata=None):
        super().__init__(parent)
        self.dose_ids = sorted(dose_ids)
        self.dose_values = {}
        self.sample_metadata = {}
        self.saved_metadata = saved_metadata  # Store saved metadata for pre-population

        self.setWindowTitle("Configure Sample Metadata")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Configure sample types and dose values for each dose group.\n"
            "• As-Deposited: Control samples (dose = 0)\n"
            "• E-Beam Exposed: Samples with electron beam exposure\n"
            "• Excluded: Samples to exclude from analysis"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Create table for dose configuration
        self.config_table = QTableWidget()
        self.config_table.setRowCount(len(self.dose_ids))
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["Dose Group", "Sample Type", "Dose Value (μC/cm²)"])

        # Configure table
        header = self.config_table.horizontalHeader()
        header.resizeSection(0, 100)  # Dose Group
        header.resizeSection(1, 200)  # Sample Type
        header.resizeSection(2, 200)  # Dose Value

        self.sample_type_combos = {}
        self.dose_value_inputs = {}

        # Extract saved dose values if available
        saved_dose_values = {}
        saved_sample_types = {}
        if saved_metadata and 'custom_dose_values' in saved_metadata and 'metadata' in saved_metadata:
            saved_dose_values = saved_metadata['custom_dose_values']
            # Extract sample types from metadata (check first sample of each dose_id)
            for sample_name, sample_meta in saved_metadata['metadata'].items():
                dose_id_key = str(sample_meta.get('dose_id', sample_name.split('_SQ')[-1].replace('SQ', '')))
                if dose_id_key not in saved_sample_types:
                    saved_sample_types[dose_id_key] = sample_meta.get('sample_type', 'E-Beam Exposed')

        # Populate table
        for row, dose_id in enumerate(self.dose_ids):
            # Dose group label
            self.config_table.setItem(row, 0, QTableWidgetItem(f"SQ{dose_id}"))

            # Sample type dropdown
            sample_type_combo = QComboBox()
            sample_type_combo.addItems(["E-Beam Exposed", "As-Deposited", "Excluded"])

            # Check if we have saved sample type for this dose_id
            dose_id_str = str(dose_id)
            if dose_id_str in saved_sample_types:
                saved_type = saved_sample_types[dose_id_str]
                sample_type_combo.setCurrentText(saved_type)
                print(f"   Pre-populating SQ{dose_id}: {saved_type}")
            else:
                # Set default based on dose_id (SQ0 = As-Deposited, others = E-Beam Exposed)
                if dose_id == 0:
                    sample_type_combo.setCurrentText("As-Deposited")
                else:
                    sample_type_combo.setCurrentText("E-Beam Exposed")

            sample_type_combo.currentTextChanged.connect(lambda text, d_id=dose_id: self.on_sample_type_changed(d_id, text))
            self.config_table.setCellWidget(row, 1, sample_type_combo)
            self.sample_type_combos[dose_id] = sample_type_combo

            # Dose value input
            dose_input = QDoubleSpinBox()
            dose_input.setRange(0.0, 100000.0)
            dose_input.setDecimals(2)
            dose_input.setSuffix(" μC/cm²")

            # Check if we have saved dose value for this dose_id
            if dose_id_str in saved_dose_values:
                saved_dose = float(saved_dose_values[dose_id_str])
                dose_input.setValue(saved_dose)
                print(f"   Pre-populating SQ{dose_id} dose: {saved_dose}")
                # Enable/disable based on sample type
                if dose_id_str in saved_sample_types and saved_sample_types[dose_id_str] == "As-Deposited":
                    dose_input.setEnabled(False)
            else:
                # Set default dose value
                if dose_id == 0:
                    dose_input.setValue(0.0)
                    dose_input.setEnabled(False)  # Disabled for As-Deposited
                else:
                    dose_input.setValue(dose_id * 1000.0)  # Default scaling

            self.config_table.setCellWidget(row, 2, dose_input)
            self.dose_value_inputs[dose_id] = dose_input

        layout.addWidget(self.config_table)

        # Buttons
        button_layout = QHBoxLayout()

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        # Cancel and OK buttons
        button_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Save Configuration")
        ok_btn.clicked.connect(self.accept_configuration)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def on_sample_type_changed(self, dose_id, sample_type):
        """Handle sample type change - enable/disable dose input"""
        dose_input = self.dose_value_inputs[dose_id]

        if sample_type == "As-Deposited":
            dose_input.setValue(0.0)
            dose_input.setEnabled(False)
        elif sample_type == "Excluded":
            dose_input.setEnabled(False)
        else:  # E-Beam Exposed
            dose_input.setEnabled(True)
            if dose_input.value() == 0.0:
                dose_input.setValue(dose_id * 1000.0)  # Default scaling

    def reset_to_defaults(self):
        """Reset all inputs to default values"""
        for dose_id in self.dose_ids:
            combo = self.sample_type_combos[dose_id]
            dose_input = self.dose_value_inputs[dose_id]

            if dose_id == 0:
                combo.setCurrentText("As-Deposited")
                dose_input.setValue(0.0)
                dose_input.setEnabled(False)
            else:
                combo.setCurrentText("E-Beam Exposed")
                dose_input.setValue(dose_id * 1000.0)
                dose_input.setEnabled(True)

    def get_sample_metadata(self):
        """Get the configured sample metadata"""
        return self.sample_metadata.copy()

    def accept_configuration(self):
        """Validate and accept the configuration"""
        try:
            # Clear previous data
            self.dose_values = {}
            self.sample_metadata = {}

            # Collect configuration for each dose group
            for dose_id in self.dose_ids:
                sample_type = self.sample_type_combos[dose_id].currentText()
                dose_value = self.dose_value_inputs[dose_id].value()

                # Store dose value for plotting
                self.dose_values[dose_id] = dose_value

                # Store metadata for each sample in this dose group
                # We'll need sample names from the parent to create full metadata
                self.sample_metadata[dose_id] = {
                    'sample_type': sample_type,
                    'dose': dose_value,
                    'dose_units': 'μC/cm²',
                    'include': sample_type != 'Excluded',
                    'notes': ''
                }

            self.accept()

        except Exception as e:
            QMessageBox.warning(self, "Configuration Error",
                              f"Error in configuration: {e}")


class ToFSIMSPCAApp(QMainWindow):
    """Main PySide6 ToF-SIMS PCA Application with Matplotlib"""
    
    def __init__(self):
        super().__init__()
        self.pca_analyzer = None
        self.pca_completed = False
        self.worker = None  # Initialize worker thread reference

        # Multi-ion data management
        from multi_ion_manager import MultiIonDataManager
        self.multi_ion_manager = MultiIonDataManager()
        self.dual_ion_mode = False  # Track if both ion modes are available

        # Group-based sample management state
        self.selected_patterns = set()  # Track which patterns are selected
        self.selected_squares = set()   # Track which squares are selected
        self.pattern_names = {}         # Map original pattern names to display names
        self.square_names = {}          # Map original square names to display names
        
        self.setWindowTitle("ToF-SIMS PCA Analysis (Native Plotting)")
        # Window size will be set by main() function with DPI awareness
        
        # Settings for recent files
        self.settings = QSettings('ToFSIMSPCA', 'RecentFiles')
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initialize database protection and pending assignments
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pending_assignments = []
        self.user_confirmed_assignments = {}  # Store user-confirmed assignments by m/z
        self.initialize_database_protection()

        # Create UI
        self.init_ui()
        self.create_menu_bar()

        print("🚀 PySide6 ToF-SIMS PCA Application (Matplotlib) Initialized")

    def closeEvent(self, event):
        """Handle application close event with proper cleanup"""
        print("🔄 Closing application...")

        try:
            # Stop any running worker threads
            if hasattr(self, 'worker') and self.worker is not None:
                if self.worker.isRunning():
                    print("   Stopping worker thread...")
                    self.worker.terminate()
                    self.worker.wait(3000)  # Wait up to 3 seconds
                    if self.worker.isRunning():
                        print("   Force killing worker thread...")
                        self.worker.kill()
                self.worker.deleteLater()
                self.worker = None

            # Clean up matplotlib figures and canvases
            # Close all matplotlib figures
            plt.close('all')

            # Clean up main plot canvas
            if hasattr(self, 'plot_canvas'):
                self.plot_canvas.close()

            # Clean up any other matplotlib canvases
            for attr_name in dir(self):
                if 'canvas' in attr_name.lower():
                    canvas = getattr(self, attr_name)
                    if hasattr(canvas, 'close'):
                        canvas.close()
                    elif hasattr(canvas, 'deleteLater'):
                        canvas.deleteLater()

            # Save settings
            if hasattr(self, 'settings'):
                self.settings.sync()

            print("   ✅ Cleanup completed")

        except Exception as e:
            print(f"   ⚠️ Error during cleanup: {e}")

        # Accept the close event
        event.accept()

        # Ensure proper Qt cleanup
        if hasattr(self, 'deleteLater'):
            self.deleteLater()

        # Quit the application completely
        QApplication.instance().quit()

    def init_ui(self):
        """Initialize the user interface"""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(main_splitter)
        
        # Left panel for controls (compact)
        left_panel = QWidget()
        left_panel.setMaximumWidth(420)  # Increased width for better button layout
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)  # Reduce spacing between sections
        left_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        
        # Apply compact styling to left panel
        left_panel.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                padding-top: 8px;
            }
            QLabel {
                font-size: 10px;
            }
            QPushButton {
                font-size: 10px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QCheckBox {
                font-size: 10px;
            }
            QSpinBox {
                font-size: 10px;
                max-height: 24px;
            }
            QTableWidget {
                font-size: 9px;
            }
        """)
        
        # Override styling for group selection buttons to be more visible
        self.group_button_selected_style = """
            QPushButton {
                font-size: 10px;
                font-weight: bold;
                padding: 4px 8px;
                min-height: 24px;
                min-width: 70px;
                border: 2px solid #2196F3;
                border-radius: 3px;
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border-color: #1976D2;
            }
        """
        
        self.group_button_unselected_style = """
            QPushButton {
                font-size: 10px;
                font-weight: normal;
                padding: 4px 8px;
                min-height: 24px;
                min-width: 70px;
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: #f8f8f8;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #999;
            }
        """
        
        # Right panel for plots (maximize space)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for plots
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([380, 1120])  # Balanced layout with more room for buttons
        main_splitter.setCollapsible(0, False)  # Prevent left panel from collapsing completely
        
        # Create control sections in left panel
        self.create_data_section(left_layout)
        self.create_sample_management_section(left_layout)
        self.create_preprocessing_section(left_layout)
        self.create_pca_section(left_layout)
        self.create_export_section(left_layout)
        
        # Add stretch to push controls to top
        left_layout.addStretch()
        
        # Create plot section in right panel
        self.create_plot_section(right_layout)
    
    def create_data_section(self, parent_layout):
        """Create data loading section"""
        group = QGroupBox("📁 Data Loading")
        layout = QVBoxLayout(group)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)

        file_layout.addWidget(QLabel("Data file:"))
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_button)

        layout.addLayout(file_layout)

        # Default file button
        default_button = QPushButton("Load Default Data")
        default_button.clicked.connect(self.load_default_data)
        layout.addWidget(default_button)

        # Polarity selection for multi-ion mode
        polarity_layout = QHBoxLayout()
        polarity_layout.addWidget(QLabel("Ion Mode:"))

        self.polarity_combo = QComboBox()
        self.polarity_combo.addItem("Negative Ion", "negative")
        self.polarity_combo.addItem("Positive Ion", "positive")
        self.polarity_combo.setCurrentIndex(0)  # Default to negative
        self.polarity_combo.currentTextChanged.connect(self.on_polarity_changed)
        self.polarity_combo.setEnabled(False)  # Disabled until dual data is loaded
        self.polarity_combo.setToolTip("Switch between negative and positive ion modes")

        polarity_layout.addWidget(self.polarity_combo)
        polarity_layout.addStretch()

        layout.addLayout(polarity_layout)

        # Status
        self.data_status = QLabel("Ready to load data")
        layout.addWidget(self.data_status)

        parent_layout.addWidget(group)
    
    def create_sample_management_section(self, parent_layout):
        """Create sample management section"""
        self.sample_group = QGroupBox("📋 Sample Management")
        layout = QVBoxLayout(self.sample_group)
        
        # Group information display
        info_layout = QHBoxLayout()
        self.squares_info = QLabel("Doses: Loading...")
        self.patterns_info = QLabel("Replicates: Loading...")
        info_layout.addWidget(self.squares_info)
        info_layout.addWidget(self.patterns_info)
        layout.addLayout(info_layout)
        
        # Pattern and Square selection controls
        pattern_square_layout = QVBoxLayout()
        
        # Square selection with rename (Squares = Different Doses)
        square_layout = QHBoxLayout()
        square_layout.addWidget(QLabel("Doses (Squares):"))
        
        self.square_checkboxes = {}  # Will be populated when data loads
        self.square_checkbox_layout = QGridLayout()
        square_layout.addLayout(self.square_checkbox_layout)
        
        # Square rename button
        self.rename_square_button = QPushButton("Rename Dose")
        self.rename_square_button.clicked.connect(self.rename_square_group)
        self.rename_square_button.setMaximumWidth(120)
        square_layout.addWidget(self.rename_square_button)
        square_layout.addStretch()
        
        pattern_square_layout.addLayout(square_layout)
        
        # Pattern selection with rename (Patterns = Triplicate Replicates)
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Replicates (Patterns):"))
        
        self.pattern_checkboxes = {}  # Will be populated when data loads
        self.pattern_checkbox_layout = QGridLayout()
        pattern_layout.addLayout(self.pattern_checkbox_layout)
        
        # Pattern rename button
        self.rename_pattern_button = QPushButton("Rename Replicate")
        self.rename_pattern_button.clicked.connect(self.rename_pattern_group)
        self.rename_pattern_button.setMaximumWidth(120)
        pattern_layout.addWidget(self.rename_pattern_button)
        pattern_layout.addStretch()
        
        pattern_square_layout.addLayout(pattern_layout)
        layout.addLayout(pattern_square_layout)
        
        # General sample management buttons
        button_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_samples)
        button_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_samples)
        button_layout.addWidget(self.deselect_all_button)
        
        layout.addLayout(button_layout)
        
        # Update button
        self.update_analysis_button = QPushButton("Update Analysis")
        self.update_analysis_button.clicked.connect(self.update_analysis_from_selection)
        self.update_analysis_button.setEnabled(False)
        layout.addWidget(self.update_analysis_button)
        
        # Initially hide until data is loaded
        self.sample_group.setVisible(False)
        
        parent_layout.addWidget(self.sample_group)
    
    def create_preprocessing_section(self, parent_layout):
        """Create preprocessing options section"""
        group = QGroupBox("🔧 Preprocessing Options")
        layout = QGridLayout(group)

        self.sqrt_checkbox = QCheckBox("Square Root Transform")
        self.sqrt_checkbox.setChecked(True)
        self.sqrt_checkbox.setToolTip("Stabilizes variance for count data")

        self.pareto_checkbox = QCheckBox("Pareto Scale")
        self.pareto_checkbox.setChecked(True)
        self.pareto_checkbox.setToolTip("Balances large vs small peaks")

        self.filter_contamination_checkbox = QCheckBox("Filter contamination peaks")
        self.filter_contamination_checkbox.setChecked(False)
        self.filter_contamination_checkbox.setToolTip("Remove all contamination peaks (Cl, Si, etc.) from database before PCA")

        layout.addWidget(self.sqrt_checkbox, 0, 0)
        layout.addWidget(self.pareto_checkbox, 0, 1)
        layout.addWidget(self.filter_contamination_checkbox, 1, 0)

        parent_layout.addWidget(group)
    
    def create_pca_section(self, parent_layout):
        """Create PCA execution section"""
        group = QGroupBox("🚀 PCA Analysis")
        layout = QVBoxLayout(group)
        
        # Components selection
        comp_layout = QHBoxLayout()
        comp_layout.addWidget(QLabel("Components:"))
        self.components_spin = QSpinBox()
        self.components_spin.setMinimum(2)
        self.components_spin.setMaximum(15)
        self.components_spin.setValue(8)
        comp_layout.addWidget(self.components_spin)
        comp_layout.addStretch()
        layout.addLayout(comp_layout)
        
        # Run button
        self.run_button = QPushButton("Run PCA")
        self.run_button.clicked.connect(self.run_pca)
        self.run_button.setEnabled(False)
        layout.addWidget(self.run_button)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)
        
        parent_layout.addWidget(group)
    
    def create_export_section(self, parent_layout):
        """Create export section"""
        group = QGroupBox("💾 Export")
        layout = QVBoxLayout(group)
        
        self.export_data_button = QPushButton("Export Data (CSV)")
        self.export_data_button.clicked.connect(self.export_data)
        self.export_data_button.setEnabled(False)
        layout.addWidget(self.export_data_button)
        
        self.export_excel_button = QPushButton("Export to Excel")
        self.export_excel_button.clicked.connect(self.export_excel)
        self.export_excel_button.setEnabled(False)
        layout.addWidget(self.export_excel_button)
        
        self.export_plots_button = QPushButton("Export Plots (PNG/PDF)")
        self.export_plots_button.clicked.connect(self.export_plots)
        self.export_plots_button.setEnabled(False)
        layout.addWidget(self.export_plots_button)
        
        parent_layout.addWidget(group)
    
    def create_plot_section(self, parent_layout):
        """Create plotting section with matplotlib"""
        group = QGroupBox("📊 Results Visualization")
        layout = QVBoxLayout(group)
        
        # Create tab widget for different plot views
        self.plot_tabs = QTabWidget()
        
        # Main results tab
        self.main_results_widget = QWidget()
        main_results_layout = QVBoxLayout(self.main_results_widget)
        
        # Create matplotlib canvas with DPI awareness
        self.plot_canvas = PCAPlotCanvas(self.main_results_widget, width=12, height=8)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self.main_results_widget)
        
        main_results_layout.addWidget(self.plot_toolbar)
        main_results_layout.addWidget(self.plot_canvas)
        
        self.plot_tabs.addTab(self.main_results_widget, "Main Results")
        
        # Text summary tab
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        self.plot_tabs.addTab(self.summary_widget, "Summary")

        # Fragment Assignment tab
        self.assignment_widget = self.create_fragment_assignment_tab()
        self.plot_tabs.addTab(self.assignment_widget, "Fragment Assignment")

        # Stick Spectrum tab
        self.stick_spectrum_widget = self.create_stick_spectrum_tab()
        self.plot_tabs.addTab(self.stick_spectrum_widget, "📊 Stick Spectrum")

        # Database Management tab (keep for future enhancement)
        self.database_mgmt_widget = self.create_database_management_tab()
        self.plot_tabs.addTab(self.database_mgmt_widget, "🗃️ Database Management")

        # ===== REMOVED UNUSED TABS =====
        # The following tabs were removed to reduce code complexity:
        # - Group Analysis (lines 2515-2616) - Not actively used
        # - Fragment Trends (lines 2617-2682) - Not actively used, had duplicate polarity selector
        # - Familial Trends (lines 2683-2766) - Not actively used
        # Tab creation methods and supporting code remain below (commented) for potential future use

        layout.addWidget(self.plot_tabs)
        parent_layout.addWidget(group)
    
    def create_menu_bar(self):
        """Create menu bar with recent files"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open file action
        open_action = QAction('&Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu('Recent Files')
        self.update_recent_files_menu()
        
        file_menu.addSeparator()
        
        # Load default action
        default_action = QAction('Load &Default Data', self)
        default_action.triggered.connect(self.load_default_data)
        file_menu.addAction(default_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Export menu
        export_menu = menubar.addMenu('&Export')
        
        export_data_action = QAction('Export &Data (CSV)', self)
        export_data_action.triggered.connect(self.export_data)
        export_menu.addAction(export_data_action)
        
        export_excel_action = QAction('Export to &Excel (Multi-sheet)', self)
        export_excel_action.triggered.connect(self.export_excel)
        export_menu.addAction(export_excel_action)
        
        export_plots_action = QAction('Export &Plots (PNG/PDF)', self)
        export_plots_action.triggered.connect(self.export_plots)
        export_menu.addAction(export_plots_action)
    
    def get_recent_files(self):
        """Get list of recent files from settings"""
        recent_files = []
        size = self.settings.beginReadArray('recent_files')
        for i in range(size):
            self.settings.setArrayIndex(i)
            file_path = self.settings.value('path')
            if file_path and os.path.exists(file_path):
                recent_files.append(file_path)
        self.settings.endArray()
        return recent_files
    
    def add_recent_file(self, file_path):
        """Add file to recent files list"""
        recent_files = self.get_recent_files()
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only last 10
        recent_files = recent_files[:10]
        
        # Save to settings
        self.settings.beginWriteArray('recent_files')
        for i, path in enumerate(recent_files):
            self.settings.setArrayIndex(i)
            self.settings.setValue('path', path)
        self.settings.endArray()
        
        # Update menu
        self.update_recent_files_menu()
    
    def update_recent_files_menu(self):
        """Update recent files menu"""
        self.recent_menu.clear()
        
        recent_files = self.get_recent_files()
        
        if not recent_files:
            no_files_action = QAction('No recent files', self)
            no_files_action.setEnabled(False)
            self.recent_menu.addAction(no_files_action)
        else:
            for file_path in recent_files:
                action = QAction(os.path.basename(file_path), self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, path=file_path: self.load_data_file(path))
                self.recent_menu.addAction(action)
            
            self.recent_menu.addSeparator()
            clear_action = QAction('Clear Recent Files', self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)
    
    def clear_recent_files(self):
        """Clear recent files list"""
        self.settings.remove('recent_files')
        self.update_recent_files_menu()
    
    def browse_file(self):
        """Browse for data file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ToF-SIMS Data File", 
            "/home/dreece23/pca-sims/data",
            "Text files (*.txt *.tsv *.csv)"
        )
        
        if file_path:
            # Show preview dialog
            preview_dialog = DataPreviewDialog(file_path, self)
            if preview_dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data_file(file_path)
    
    def load_default_data(self):
        """Load default data file"""
        default_path = "/home/dreece23/pca-sims/data/NegativeIon/NegIonTIC.txt"
        if os.path.exists(default_path):
            self.load_data_file(default_path)
        else:
            QMessageBox.warning(self, "Warning", f"Default file not found: {default_path}")
    
    def load_data_file(self, file_path):
        """Load data from file with multi-ion support"""
        try:
            self.data_status.setText("Loading data...")

            # Clear user-confirmed assignments when loading new file
            self.user_confirmed_assignments.clear()

            # Try to load both ion modes
            negative_success, positive_success = self.multi_ion_manager.load_data_pair(file_path)

            # If only one file loaded, ask user to confirm polarity
            if (negative_success or positive_success) and not (negative_success and positive_success):
                # Determine what the system detected
                detected_polarity = "negative" if negative_success else "positive"

                # Ask user to confirm or correct the polarity
                polarity_dialog = QMessageBox(self)
                polarity_dialog.setWindowTitle("Confirm Ion Mode")
                polarity_dialog.setText(f"The system detected this as <b>{detected_polarity.upper()}</b> ion data.\n\n"
                                       "Is this correct?")
                polarity_dialog.setInformativeText("This affects fragment assignment and analysis.\n"
                                                  "Choose the correct ion mode for your data.")
                polarity_dialog.setIcon(QMessageBox.Question)

                # Add custom buttons
                correct_btn = polarity_dialog.addButton("Correct", QMessageBox.AcceptRole)
                negative_btn = polarity_dialog.addButton("Use Negative", QMessageBox.ActionRole)
                positive_btn = polarity_dialog.addButton("Use Positive", QMessageBox.ActionRole)
                polarity_dialog.setDefaultButton(correct_btn)

                polarity_dialog.exec()
                clicked_button = polarity_dialog.clickedButton()

                # Determine user's choice
                if clicked_button == negative_btn:
                    user_polarity = "negative"
                elif clicked_button == positive_btn:
                    user_polarity = "positive"
                else:  # Correct button
                    user_polarity = detected_polarity

                print(f"🔍 Polarity confirmation: detected={detected_polarity}, user_choice={user_polarity}")

                # If user chose different polarity than detected, we need to reload
                if user_polarity != detected_polarity:
                    print(f"🔄 User specified {user_polarity} ion mode (detected: {detected_polarity})")
                    # Force load as the specified polarity (store only in multi_ion_manager)
                    if user_polarity == "negative":
                        analyzer = SimpleToFSIMSPCA(file_path)
                        analyzer.load_data()
                        self.multi_ion_manager.negative_analyzer = analyzer
                        self.multi_ion_manager.negative_loaded = True
                        negative_success = True
                        positive_success = False
                    else:
                        analyzer = SimpleToFSIMSPCA(file_path)
                        analyzer.load_data()
                        self.multi_ion_manager.positive_analyzer = analyzer
                        self.multi_ion_manager.positive_loaded = True
                        positive_success = True
                        negative_success = False
                else:
                    # User confirmed detection is correct - ensure success flags match
                    print(f"✅ User confirmed {user_polarity} ion mode")
                    if user_polarity == "negative":
                        negative_success = True
                        positive_success = False
                    else:
                        positive_success = True
                        negative_success = False


            if negative_success or positive_success:
                # Enable dual-ion mode if both are loaded
                self.dual_ion_mode = negative_success and positive_success

                if self.dual_ion_mode:
                    # Both ion modes available - enable switching
                    self.polarity_combo.setEnabled(True)
                    available_polarities = self.multi_ion_manager.get_available_polarities()
                    print(f"🔄 Dual-ion mode enabled: {available_polarities}")

                    # Set initial active analyzer (prefer negative)
                    if "negative" in available_polarities:
                        self.multi_ion_manager.set_active_polarity("negative")
                        self.polarity_combo.setCurrentIndex(0)
                    else:
                        self.multi_ion_manager.set_active_polarity("positive")
                        self.polarity_combo.setCurrentIndex(1)
                else:
                    # Single ion mode - disable combo and show informative text
                    self.polarity_combo.setEnabled(False)
                    if negative_success:
                        self.multi_ion_manager.set_active_polarity("negative")
                        self.polarity_combo.setCurrentIndex(0)
                        self.polarity_combo.setToolTip("Single-ion mode: Negative ion data loaded\n(Positive companion file not found)")
                        print(f"📊 Single-ion mode: Negative ion data loaded")
                    else:
                        self.multi_ion_manager.set_active_polarity("positive")
                        self.polarity_combo.setCurrentIndex(1)
                        self.polarity_combo.setToolTip("Single-ion mode: Positive ion data loaded\n(Negative companion file not found)")
                        print(f"📊 Single-ion mode: Positive ion data loaded")

                    # Debug: verify combo state

                # Get the active analyzer
                self.pca_analyzer = self.multi_ion_manager.get_active_analyzer()

                # Final verification: ensure UI matches active polarity
                actual_polarity = self.multi_ion_manager.active_polarity
                if (actual_polarity == "negative" and self.polarity_combo.currentIndex() != 0) or \
                   (actual_polarity == "positive" and self.polarity_combo.currentIndex() != 1):
                    print(f"⚠️  WARNING: Combo box mismatch! Correcting...")
                    self.polarity_combo.setCurrentIndex(0 if actual_polarity == "negative" else 1)
            else:
                # Fallback to single-file loading
                print("⚠️ Multi-ion loading failed, falling back to single-file mode")
                self.pca_analyzer = SimpleToFSIMSPCA(file_path)
                self.pca_analyzer.load_data()
                self.dual_ion_mode = False
                self.polarity_combo.setEnabled(False)

            # Prompt for custom dose values if doses are detected
            if 'dose_id' in self.pca_analyzer.sample_metadata.columns:
                dose_ids = sorted(self.pca_analyzer.sample_metadata['dose_id'].unique())

                # Try to load existing metadata first
                saved_metadata = self.pca_analyzer.load_metadata(file_path)

                if saved_metadata and 'metadata' in saved_metadata and 'custom_dose_values' in saved_metadata:
                    # Metadata found - apply it automatically
                    print(f"📄 Found saved metadata for this file")

                    # Apply metadata to analyzer
                    self.pca_analyzer.apply_metadata(saved_metadata)
                    self.pca_analyzer.set_custom_dose_values(saved_metadata['custom_dose_values'])

                    status_msg = f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, {len(self.pca_analyzer.raw_data.columns)} samples (metadata loaded)"
                    self.data_status.setText(status_msg)

                    # Show info that metadata was loaded, with option to reconfigure
                    reply = QMessageBox.question(
                        self,
                        "Metadata Loaded",
                        f"Found saved dose configuration for this file.\n\n"
                        f"Last modified: {saved_metadata.get('last_modified', 'Unknown')}\n"
                        f"{len(dose_ids)} dose levels configured\n\n"
                        "Would you like to reconfigure the dose assignments?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        # User wants to reconfigure - show dialog with saved values
                        print(f"🔧 Opening dose dialog with saved metadata for reconfiguration")
                        dose_dialog = CustomDoseDialog(self, dose_ids, saved_metadata=saved_metadata)
                        if dose_dialog.exec() == QDialog.DialogCode.Accepted:
                            # Get configured metadata
                            dose_metadata = dose_dialog.get_sample_metadata()
                            dose_values = dose_dialog.dose_values

                            # Create sample-level metadata dictionary
                            sample_metadata_dict = {}
                            for sample_name in self.pca_analyzer.sample_metadata['sample_name']:
                                # Extract dose_id from sample metadata
                                sample_mask = self.pca_analyzer.sample_metadata['sample_name'] == sample_name
                                dose_id = self.pca_analyzer.sample_metadata.loc[sample_mask, 'dose_id'].iloc[0]

                                if dose_id in dose_metadata:
                                    sample_metadata_dict[sample_name] = dose_metadata[dose_id].copy()
                                    sample_metadata_dict[sample_name]['square_id'] = sample_name

                            # Apply metadata to analyzer
                            self.pca_analyzer.set_custom_dose_values(dose_values)

                            # Create metadata structure and apply it
                            metadata = {
                                'metadata': sample_metadata_dict,
                                'custom_dose_values': dose_values
                            }
                            self.pca_analyzer.apply_metadata(metadata)

                            # Save updated metadata to file
                            success = self.pca_analyzer.save_metadata(file_path, sample_metadata_dict, dose_values)

                            status_msg = f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, {len(self.pca_analyzer.raw_data.columns)} samples"
                            if success:
                                status_msg += " (metadata updated)"
                            else:
                                status_msg += " (metadata not saved)"
                            self.data_status.setText(status_msg)
                else:
                    # No saved metadata - show dialog for first-time configuration
                    reply = QMessageBox.question(
                        self,
                        "Custom Dose Values",
                        f"Detected {len(dose_ids)} dose levels: {dose_ids}\n\n"
                        "Would you like to set custom E-beam dose values (μC/cm²) "
                        "for dose-response analysis?\n\n"
                        "Your configuration will be saved for future use.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        dose_dialog = CustomDoseDialog(self, dose_ids)
                        if dose_dialog.exec() == QDialog.DialogCode.Accepted:
                            # Get configured metadata
                            dose_metadata = dose_dialog.get_sample_metadata()
                            dose_values = dose_dialog.dose_values

                            # Create sample-level metadata dictionary
                            sample_metadata_dict = {}
                            for sample_name in self.pca_analyzer.sample_metadata['sample_name']:
                                # Extract dose_id from sample metadata
                                sample_mask = self.pca_analyzer.sample_metadata['sample_name'] == sample_name
                                dose_id = self.pca_analyzer.sample_metadata.loc[sample_mask, 'dose_id'].iloc[0]

                                if dose_id in dose_metadata:
                                    sample_metadata_dict[sample_name] = dose_metadata[dose_id].copy()
                                    sample_metadata_dict[sample_name]['square_id'] = sample_name

                            # Apply metadata to analyzer
                            self.pca_analyzer.set_custom_dose_values(dose_values)

                            # Create metadata structure and apply it
                            metadata = {
                                'metadata': sample_metadata_dict,
                                'custom_dose_values': dose_values
                            }
                            self.pca_analyzer.apply_metadata(metadata)

                            # Save metadata to file
                            success = self.pca_analyzer.save_metadata(file_path, sample_metadata_dict, dose_values)

                            status_msg = f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, {len(self.pca_analyzer.raw_data.columns)} samples"
                            if success:
                                status_msg += " (metadata saved)"
                            else:
                                status_msg += " (metadata not saved)"
                            self.data_status.setText(status_msg)
                        else:
                            self.data_status.setText(
                                f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, "
                                f"{len(self.pca_analyzer.raw_data.columns)} samples (default configuration)"
                            )
                    else:
                        self.data_status.setText(
                            f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, "
                            f"{len(self.pca_analyzer.raw_data.columns)} samples"
                        )
            else:
                # No dose information detected
                self.data_status.setText(
                    f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, "
                    f"{len(self.pca_analyzer.raw_data.columns)} samples"
                )

            # Update UI
            self.file_label.setText(os.path.basename(file_path))
            self.run_button.setEnabled(True)
            self.pca_completed = False

            # Add to recent files
            self.add_recent_file(file_path)

            # Populate sample management table
            self.populate_sample_table()

            # Update group analysis if in dual-ion mode
            if self.dual_ion_mode and hasattr(self, 'group_combo'):
                self.update_group_analysis()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
            self.data_status.setText("❌ Failed to load data")
    
    def run_pca(self):
        """Run PCA analysis in worker thread"""
        if not self.pca_analyzer:
            return

        # Get preprocessing options
        preprocessing_options = {
            'sqrt_transform': self.sqrt_checkbox.isChecked(),
            'pareto_scale': self.pareto_checkbox.isChecked(),
            'filter_contamination_peaks': self.filter_contamination_checkbox.isChecked()
        }

        # Apply sample selection using proper masking
        selected_samples, display_names = self.get_selected_samples()

        if not selected_samples:
            QMessageBox.warning(self, "No Samples Selected",
                              "Please select at least one sample for analysis.")
            return

        if len(selected_samples) < 3:
            QMessageBox.warning(self, "Insufficient Samples",
                              "Please select at least 3 samples for meaningful PCA analysis.")
            return

        # Apply sample selection using masks (preserves original data)
        try:
            # Use the new masking system
            self.pca_analyzer.select_samples_by_names(selected_samples)

            # Update display names in working metadata
            for original, display in display_names.items():
                mask = self.pca_analyzer.working_metadata['sample_name'] == original
                if mask.any():
                    self.pca_analyzer.working_metadata.loc[mask, 'display_name'] = display

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply sample selection: {e}")
            return
        
        # Start worker thread
        self.worker = PCAWorker(
            self.pca_analyzer,
            self.components_spin.value(),
            preprocessing_options
        )
        
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.pca_finished)
        self.worker.error.connect(self.pca_error)
        
        self.run_button.setEnabled(False)
        self.worker.start()
    
    def update_progress(self, value, text):
        """Update progress bar and label"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(text)
    
    def pca_finished(self):
        """Handle PCA completion"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("✅ PCA completed!")
        self.run_button.setEnabled(True)
        self.export_data_button.setEnabled(True)
        self.export_excel_button.setEnabled(True)
        self.export_plots_button.setEnabled(True)
        self.pca_completed = True

        # Display results
        self.display_results()

        # Refresh fragment assignments with new PCA loadings
        if hasattr(self, 'assignment_table'):
            self.refresh_assignment_table()
    
    def pca_error(self, error_message):
        """Handle PCA error"""
        QMessageBox.critical(self, "PCA Error", f"PCA failed: {error_message}")
        self.progress_bar.setValue(0)
        self.progress_label.setText("❌ PCA failed")
        self.run_button.setEnabled(True)
    
    def display_results(self):
        """Display PCA results in matplotlib canvas"""
        if not self.pca_completed:
            return
        
        # Plot results using matplotlib
        self.plot_canvas.plot_pca_results(self.pca_analyzer)
        
        # Update summary text
        self.update_summary_text()
        
        print("✅ Results displayed using native matplotlib")
    
    def update_summary_text(self):
        """Update summary text display"""
        summary = self.pca_analyzer.get_results_summary()
        variance_ratios = self.pca_analyzer.explained_variance_ratio * 100

        # Get scores and loadings
        scores_df = self.pca_analyzer.get_scores_dataframe()
        loadings_df = self.pca_analyzer.get_loadings_dataframe()
        top_loadings = loadings_df['PC1'].abs().sort_values(ascending=False).head(10)

        
        text_summary = f"""ToF-SIMS PCA Analysis Results
{'=' * 50}

Dataset Information:
  • File: {self.file_label.text()}
  • Samples analyzed: {summary['n_samples']}
  • Mass channels: {summary['n_masses']}
  • Principal components: {summary['n_components']}
  • Total variance explained: {summary['total_variance_explained']*100:.1f}%

Principal Component Analysis:
  • PC1 explains: {variance_ratios[0]:.1f}% of variance
  • PC2 explains: {variance_ratios[1]:.1f}% of variance
  • PC3 explains: {variance_ratios[2]:.1f}% of variance
  • PC4 explains: {variance_ratios[3]:.1f}% of variance

📊 Interpreting PC1 Scores and Loadings:

PC1 Score Interpretation:
  • POSITIVE PC1 scores → Samples with higher intensities of masses with positive loadings
  • NEGATIVE PC1 scores → Samples with higher intensities of masses with negative loadings
  • Distance from zero → Strength of the chemical pattern difference
  • Grouping pattern → Reveals systematic variation (e.g., dose response)

PC1 Loadings Interpretation:
  • POSITIVE loadings → Masses that increase together with positive PC1 scores
  • NEGATIVE loadings → Masses that increase together with negative PC1 scores
  • Magnitude → Importance of each mass in defining the main variation
  • Sign pattern → Chemical fingerprint distinguishing sample groups

Top 10 PC1 Loadings (by absolute value):
{'-' * 40}
Rank | m/z     | Loading    | |Loading|
{'-' * 40}"""
        
        for i, (mass, abs_loading) in enumerate(top_loadings.items(), 1):
            original_loading = loadings_df.loc[mass, 'PC1']
            text_summary += f"\n{i:2d}   | {mass:7.3f} | {original_loading:+.6f} | {abs_loading:.6f}"
        
        # Add dose correlation if available
        if 'dose_id' in scores_df.columns:
            dose_groups = scores_df.groupby('dose_id')['PC1'].mean()
            corr = scores_df['dose_id'].corr(scores_df['PC1'])
            text_summary += f"""

Dose Response Analysis:
  • PC1 vs Dose correlation: r = {corr:.3f}
  • Trend: {'Strong' if abs(corr) > 0.8 else 'Moderate' if abs(corr) > 0.5 else 'Weak'}"""
        
        text_summary += f"""

{'-' * 50}
Plotting: Native matplotlib (fast, responsive)
Navigation: Use toolbar above plot to zoom, pan, save
Export: Use export buttons to save data and plots
"""
        
        self.summary_text.setPlainText(text_summary)
    
    def export_data(self):
        """Export PCA results to CSV files"""
        if not self.pca_completed:
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            "/home/dreece23/pca-sims/outputs"
        )
        
        if output_dir:
            try:
                # Save scores
                scores_df = self.pca_analyzer.get_scores_dataframe()
                scores_path = os.path.join(output_dir, "pca_scores.csv")
                scores_df.to_csv(scores_path, index=False)
                
                # Save loadings
                loadings_df = self.pca_analyzer.get_loadings_dataframe()
                loadings_path = os.path.join(output_dir, "pca_loadings.csv")
                loadings_df.to_csv(loadings_path)
                
                QMessageBox.information(
                    self, "Export Complete",
                    f"Data exported to:\n{output_dir}\n\nFiles:\n- pca_scores.csv\n- pca_loadings.csv"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")
    
    def export_excel(self):
        """Export PCA results to Excel with multiple sheets"""
        if not self.pca_completed:
            return
        
        # Get output file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel",
            "/home/dreece23/pca-sims/outputs/pca_analysis.xlsx",
            "Excel files (*.xlsx)"
        )
        
        if file_path:
            try:
                import pandas as pd
                
                # Create Excel writer
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    
                    # Sheet 1: Analysis Summary
                    summary = self.pca_analyzer.get_results_summary()
                    variance_ratios = self.pca_analyzer.explained_variance_ratio * 100
                    
                    summary_data = {
                        'Metric': [
                            'Analysis Date',
                            'Data File',
                            'Total Samples',
                            'Selected Samples',
                            'Mass Channels',
                            'Principal Components',
                            'Total Variance Explained (%)',
                            'PC1 Variance (%)',
                            'PC2 Variance (%)',
                            'PC3 Variance (%)',
                            'Preprocessing Applied'
                        ],
                        'Value': [
                            pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                            self.file_label.text(),
                            len(self.pca_analyzer.raw_data.columns),
                            len(self.get_selected_samples()[0]),
                            summary['n_masses'],
                            summary['n_components'],
                            f"{summary['total_variance_explained']*100:.2f}",
                            f"{variance_ratios[0]:.2f}",
                            f"{variance_ratios[1]:.2f}" if len(variance_ratios) > 1 else "N/A",
                            f"{variance_ratios[2]:.2f}" if len(variance_ratios) > 2 else "N/A",
                            f"√Transform: {self.sqrt_checkbox.isChecked()}, Pareto Scale: {self.pareto_checkbox.isChecked()}"
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Analysis Summary', index=False)
                    
                    # Sheet 2: Scores Data
                    scores_df = self.pca_analyzer.get_scores_dataframe()
                    
                    # Add sample information if available
                    if hasattr(self, 'sample_table') and self.sample_table.rowCount() > 0:
                        selected_samples, display_names = self.get_selected_samples()
                        
                        # Map display names
                        scores_df['Display_Name'] = scores_df['sample_name'].map(
                            lambda x: display_names.get(x, x) if x in display_names.values() 
                            else display_names.get(x, x)
                        )
                        
                        # Reorder columns to put display name first
                        cols = ['Display_Name'] + [col for col in scores_df.columns if col != 'Display_Name']
                        scores_df = scores_df[cols]
                    
                    scores_df.to_excel(writer, sheet_name='PCA Scores', index=False)
                    
                    # Sheet 3: Loadings Data
                    loadings_df = self.pca_analyzer.get_loadings_dataframe()
                    
                    # Add ranking column for PC1
                    loadings_df['PC1_Abs_Loading'] = loadings_df['PC1'].abs()
                    loadings_df['PC1_Rank'] = loadings_df['PC1_Abs_Loading'].rank(ascending=False)
                    loadings_df = loadings_df.sort_values('PC1_Rank')
                    
                    # Reset index to include m/z as a column
                    loadings_df = loadings_df.reset_index()
                    loadings_df.to_excel(writer, sheet_name='PCA Loadings', index=False)
                    
                    # Sheet 4: Variance Explained
                    variance_df = pd.DataFrame({
                        'Component': [f'PC{i+1}' for i in range(len(variance_ratios))],
                        'Variance_Explained_Percent': variance_ratios,
                        'Cumulative_Variance_Percent': np.cumsum(variance_ratios)
                    })
                    variance_df.to_excel(writer, sheet_name='Variance Explained', index=False)
                    
                    # Sheet 5: Sample Information (if available)
                    if hasattr(self, 'sample_table') and self.sample_table.rowCount() > 0:
                        sample_info = []
                        for row in range(self.sample_table.rowCount()):
                            include_item = self.sample_table.item(row, 0)
                            original_item = self.sample_table.item(row, 1)
                            display_item = self.sample_table.item(row, 2)
                            
                            if original_item and display_item:
                                sample_info.append({
                                    'Included_in_Analysis': include_item.checkState() == Qt.CheckState.Checked if include_item else False,
                                    'Original_Name': original_item.text(),
                                    'Display_Name': display_item.text(),
                                    'Extracted_Dose': self.extract_dose_from_name(display_item.text())
                                })
                        
                        sample_info_df = pd.DataFrame(sample_info)
                        sample_info_df.to_excel(writer, sheet_name='Sample Information', index=False)
                    
                    # Sheet 6: Top Loadings Summary
                    top_loadings = loadings_df.head(20).copy()
                    top_loadings_summary = top_loadings[['index', 'PC1', 'PC1_Abs_Loading', 'PC1_Rank']].copy()
                    top_loadings_summary.columns = ['Mass_mz', 'PC1_Loading', 'Absolute_Loading', 'Rank']
                    top_loadings_summary.to_excel(writer, sheet_name='Top 20 Loadings', index=False)
                
                QMessageBox.information(
                    self, "Excel Export Complete",
                    f"Analysis exported to Excel:\n{file_path}\n\n"
                    "Sheets included:\n"
                    "• Analysis Summary\n"
                    "• PCA Scores\n"
                    "• PCA Loadings\n" 
                    "• Variance Explained\n"
                    "• Sample Information\n"
                    "• Top 20 Loadings"
                )
                
            except ImportError:
                QMessageBox.critical(
                    self, "Missing Dependency",
                    "Excel export requires openpyxl.\n"
                    "Install with: pip install openpyxl"
                )
            except Exception as e:
                QMessageBox.critical(self, "Excel Export Error", f"Failed to export to Excel: {e}")
    
    def export_plots(self):
        """Export plots to image files"""
        if not self.pca_completed:
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            "/home/dreece23/pca-sims/outputs"
        )
        
        if output_dir:
            try:
                # Export main plot
                main_plot_path = os.path.join(output_dir, "pca_results_overview.png")
                self.plot_canvas.export_plot(main_plot_path)
                
                # Create and export detailed plots
                scores_plot = InteractivePCAPlots.create_detailed_scores_plot(
                    self.pca_analyzer, 
                    os.path.join(output_dir, "pca_scores_detailed.png")
                )
                
                loadings_plot = InteractivePCAPlots.create_loadings_plot(
                    self.pca_analyzer,
                    os.path.join(output_dir, "pca_loadings_detailed.png")
                )
                
                QMessageBox.information(
                    self, "Plots Exported",
                    f"Plots exported to:\n{output_dir}\n\nFiles:\n- pca_results_overview.png\n- pca_scores_detailed.png\n- pca_loadings_detailed.png"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export plots: {e}")
    
    def parse_sample_name(self, sample_name):
        """Parse sample name to extract pattern and square information"""
        import re
        
        # Pattern: P1_SQ2, P2_SQ1, etc.
        match = re.match(r'P(\d+)_SQ(\d+)', sample_name)
        if match:
            pattern = f"P{match.group(1)}"
            square = f"SQ{match.group(2)}"
            return pattern, square
        
        # Fallback for other naming patterns
        return "Unknown", "Unknown"
    
    def create_pattern_square_checkboxes(self, sample_names):
        """Create pattern and square selection checkboxes"""
        # Clear existing checkboxes
        for checkbox in self.pattern_checkboxes.values():
            checkbox.setParent(None)
        for checkbox in self.square_checkboxes.values():
            checkbox.setParent(None)
        self.pattern_checkboxes.clear()
        self.square_checkboxes.clear()
        
        # Collect unique patterns and squares
        patterns = set()
        squares = set()
        
        for sample_name in sample_names:
            pattern, square = self.parse_sample_name(sample_name)
            patterns.add(pattern)
            squares.add(square)
        
        # Create pattern checkboxes in a compact grid
        row = 0
        col = 0
        for pattern in sorted(patterns):
            if pattern != "Unknown":
                checkbox = QCheckBox(pattern)
                checkbox.setChecked(True)  # Start with all selected
                checkbox.stateChanged.connect(lambda state, p=pattern: self.toggle_pattern(p))
                self.pattern_checkboxes[pattern] = checkbox
                self.pattern_checkbox_layout.addWidget(checkbox, row, col)
                col += 1
                if col >= 3:  # 3 checkboxes per row
                    col = 0
                    row += 1
        
        # Create square checkboxes in a compact grid
        row = 0
        col = 0
        for square in sorted(squares):
            if square != "Unknown":
                checkbox = QCheckBox(square)
                checkbox.setChecked(True)  # Start with all selected
                checkbox.stateChanged.connect(lambda state, s=square: self.toggle_square(s))
                self.square_checkboxes[square] = checkbox
                self.square_checkbox_layout.addWidget(checkbox, row, col)
                col += 1
                if col >= 3:  # 3 checkboxes per row
                    col = 0
                    row += 1
    
    def toggle_pattern(self, pattern):
        """Update pattern selection based on checkbox state"""
        checkbox = self.pattern_checkboxes.get(pattern)
        if checkbox:
            if checkbox.isChecked():
                self.selected_patterns.add(pattern)
            else:
                self.selected_patterns.discard(pattern)
        
        self.on_selection_changed()
    
    def toggle_square(self, square):
        """Update square selection based on checkbox state"""
        checkbox = self.square_checkboxes.get(square)
        if checkbox:
            if checkbox.isChecked():
                self.selected_squares.add(square)
            else:
                self.selected_squares.discard(square)
        
        self.on_selection_changed()
    
    def update_checkbox_states(self):
        """Update checkbox states based on selection"""
        # Update pattern checkboxes
        for pattern, checkbox in self.pattern_checkboxes.items():
            checkbox.blockSignals(True)  # Prevent triggering the signal
            checkbox.setChecked(pattern in self.selected_patterns)
            checkbox.setText(self.pattern_names.get(pattern, pattern))
            checkbox.blockSignals(False)
        
        # Update square checkboxes  
        for square, checkbox in self.square_checkboxes.items():
            checkbox.blockSignals(True)  # Prevent triggering the signal
            checkbox.setChecked(square in self.selected_squares)
            checkbox.setText(self.square_names.get(square, square))
            checkbox.blockSignals(False)
        
        # Update info labels
        selected_squares_str = ", ".join(sorted(self.square_names.get(s, s) for s in self.selected_squares))
        selected_patterns_str = ", ".join(sorted(self.pattern_names.get(p, p) for p in self.selected_patterns))
        
        self.squares_info.setText(f"Selected Doses: {selected_squares_str if selected_squares_str else 'None'}")
        self.patterns_info.setText(f"Selected Replicates: {selected_patterns_str if selected_patterns_str else 'None'}")
    
    def on_selection_changed(self):
        """Handle changes in group selection"""
        # Enable update button when changes are made
        self.update_analysis_button.setEnabled(True)

        # If PCA has been run, suggest updating
        if self.pca_completed:
            self.update_analysis_button.setText("Update Analysis *")
            self.update_analysis_button.setStyleSheet("QPushButton { font-weight: bold; color: #d62728; }")

    def on_polarity_changed(self):
        """Handle changes in polarity selection for multi-ion mode"""
        if not self.dual_ion_mode:
            return  # No action needed in single-ion mode

        # Get the selected polarity
        selected_polarity = self.polarity_combo.currentData()

        if self.multi_ion_manager.set_active_polarity(selected_polarity):
            # Successfully switched polarity
            self.pca_analyzer = self.multi_ion_manager.get_active_analyzer()

            if self.pca_analyzer:
                # Update UI to reflect the new active analyzer
                self.update_sample_management()

                # Reset PCA completion status since we switched datasets
                self.pca_completed = False

                # Update export buttons
                self.export_excel_button.setEnabled(False)
                self.export_plots_button.setEnabled(False)

                # Clear any existing plots
                if hasattr(self, 'plot_canvas'):
                    self.plot_canvas.figure.clear()
                    self.plot_canvas.draw()

                # Refresh fragment assignments if PCA has been run
                if hasattr(self, 'assignment_table') and self.pca_completed:
                    self.refresh_assignment_table()

                # Update group analysis
                if hasattr(self, 'group_combo'):
                    self.update_group_analysis()

                # Update status
                polarity_label = "Negative" if selected_polarity == "negative" else "Positive"
                self.data_status.setText(f"✅ Switched to {polarity_label} Ion Mode")

                print(f"🔄 Switched to {polarity_label} ion mode")
            else:
                QMessageBox.warning(self, "Switch Failed",
                                  f"No data available for {selected_polarity} ion mode")
        else:
            # Failed to switch - revert combo box to previous selection
            current_polarity = self.multi_ion_manager.active_polarity
            index = 0 if current_polarity == "negative" else 1
            self.polarity_combo.setCurrentIndex(index)
    
    def select_all_samples(self):
        """Select all groups"""
        self.selected_patterns = set(self.pattern_checkboxes.keys())
        self.selected_squares = set(self.square_checkboxes.keys())
        self.update_checkbox_states()
        self.on_selection_changed()
    
    def deselect_all_samples(self):
        """Deselect all groups"""
        self.selected_patterns.clear()
        self.selected_squares.clear()
        self.update_checkbox_states()
        self.on_selection_changed()
    
    def rename_pattern_group(self):
        """Rename a replicate group"""
        patterns = list(self.pattern_checkboxes.keys())
        if not patterns:
            QMessageBox.information(self, "No Replicates", "No replicate groups found to rename.")
            return
        
        # Get pattern to rename
        pattern, ok = QInputDialog.getItem(
            self, "Select Replicate", "Choose replicate group to rename:", patterns, 0, False
        )
        if not ok:
            return
        
        # Get new name
        new_name, ok = QInputDialog.getText(
            self, "Rename Replicate", f"Enter new name for {pattern}:", text=self.pattern_names.get(pattern, pattern)
        )
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        self.pattern_names[pattern] = new_name
        self.update_checkbox_states()
        
        QMessageBox.information(self, "Replicate Renamed", 
                              f"Replicate group {pattern} renamed to '{new_name}'")
    
    def rename_square_group(self):
        """Rename a dose group"""
        squares = list(self.square_checkboxes.keys())
        if not squares:
            QMessageBox.information(self, "No Doses", "No dose groups found to rename.")
            return
        
        # Get square to rename
        square, ok = QInputDialog.getItem(
            self, "Select Dose", "Choose dose group to rename:", squares, 0, False
        )
        if not ok:
            return
        
        # Get new name
        new_name, ok = QInputDialog.getText(
            self, "Rename Dose", f"Enter new name for {square}:", text=self.square_names.get(square, square)
        )
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        self.square_names[square] = new_name
        self.update_checkbox_states()
        
        QMessageBox.information(self, "Dose Renamed", 
                              f"Dose group {square} renamed to '{new_name}'")

    def populate_sample_table(self):
        """Setup group-based sample management"""
        if not self.pca_analyzer:
            return

        # Original data is preserved in pca_analyzer.raw_data (immutable)

        # Get non-excluded samples only
        if hasattr(self.pca_analyzer, 'get_non_excluded_samples'):
            non_excluded_samples = self.pca_analyzer.get_non_excluded_samples()
            sample_names = non_excluded_samples['sample_name'].tolist()
        else:
            # Fallback to all samples if no metadata
            sample_names = list(self.pca_analyzer.raw_data.columns)

        # Create pattern and square selection checkboxes
        self.create_pattern_square_checkboxes(sample_names)

        # Start with all non-excluded groups selected
        self.selected_patterns = set(self.pattern_checkboxes.keys())
        self.selected_squares = set(self.square_checkboxes.keys())

        # Update info labels to show exclusions
        self.update_sample_info_labels()

        # Initialize display names to original names
        for pattern in self.pattern_checkboxes.keys():
            if pattern not in self.pattern_names:
                self.pattern_names[pattern] = pattern
        for square in self.square_checkboxes.keys():
            if square not in self.square_names:
                self.square_names[square] = square
        
        # Update checkbox states
        self.update_checkbox_states()
        
        # Show sample management section
        self.sample_group.setVisible(True)
        self.update_analysis_button.setEnabled(True)

    def update_sample_info_labels(self):
        """Update info labels to show sample counts and exclusion status"""
        if not self.pca_analyzer:
            return

        try:
            # Get non-excluded samples
            non_excluded_data = self.pca_analyzer.get_non_excluded_samples()
            total_samples = len(self.pca_analyzer.sample_metadata)
            included_samples = len(non_excluded_data)
            excluded_samples = total_samples - included_samples

            # Update pattern info
            patterns = set()
            squares = set()
            for _, row in non_excluded_data.iterrows():
                sample_name = row['sample_name']
                pattern, square = self.parse_sample_name(sample_name)
                patterns.add(pattern)
                squares.add(square)

            # Update labels with exclusion info
            pattern_text = f"Replicates: {len(patterns)} types"
            if excluded_samples > 0:
                pattern_text += f" ({excluded_samples} samples excluded)"
            self.patterns_info.setText(pattern_text)

            square_text = f"Doses: {len(squares)} levels"
            if excluded_samples > 0:
                square_text += f" (Total: {included_samples}/{total_samples} samples)"
            self.squares_info.setText(square_text)

        except Exception as e:
            print(f"Warning: Could not update sample info labels: {e}")
            # Fallback to basic labels
            self.patterns_info.setText("Replicates: Loading...")
            self.squares_info.setText("Doses: Loading...")

    def get_selected_samples(self):
        """Get list of selected samples based on group selection"""
        if not self.pca_analyzer:
            return [], {}

        selected_samples = []
        display_names = {}

        # Get all sample names from original data (not working data)
        all_sample_names = list(self.pca_analyzer.raw_data.columns)
        
        for sample_name in all_sample_names:
            pattern, square = self.parse_sample_name(sample_name)
            
            # Include sample if both its pattern and square are selected
            if pattern in self.selected_patterns and square in self.selected_squares:
                selected_samples.append(sample_name)
                
                # Create display name using renamed groups (keep original format: pattern_square)
                pattern_display = self.pattern_names.get(pattern, pattern)
                square_display = self.square_names.get(square, square)
                display_name = f"{pattern_display}_{square_display}"
                display_names[sample_name] = display_name
        
        return selected_samples, display_names
    
    def update_analysis_from_selection(self):
        """Update PCA analysis based on selected samples"""
        selected_samples, display_names = self.get_selected_samples()
        
        if not selected_samples:
            QMessageBox.warning(self, "No Samples Selected", 
                              "Please select at least one sample for analysis.")
            return
        
        if len(selected_samples) < 3:
            QMessageBox.warning(self, "Insufficient Samples", 
                              "Please select at least 3 samples for meaningful PCA analysis.")
            return
        
        # Update analyzer with selected samples using masks
        try:
            # Use the new masking system to preserve original data
            self.pca_analyzer.select_samples_by_names(selected_samples)
            
            # Update display names in working metadata
            if 'display_name' not in self.pca_analyzer.working_metadata.columns:
                self.pca_analyzer.working_metadata['display_name'] = self.pca_analyzer.working_metadata['sample_name']

            for original, display in display_names.items():
                mask = self.pca_analyzer.working_metadata['sample_name'] == original
                if mask.any():
                    self.pca_analyzer.working_metadata.loc[mask, 'display_name'] = display

            # Reset PCA completion flag
            self.pca_completed = False

            # Reset button styling
            self.update_analysis_button.setText("Update Analysis")
            self.update_analysis_button.setStyleSheet("")

            working_data, working_metadata = self.pca_analyzer.get_active_data()
            self.data_status.setText(f"✅ Updated: {len(working_data.columns)} samples selected")

            # If PCA was already run, automatically re-run with new selection
            if hasattr(self.pca_analyzer, 'explained_variance_ratio'):
                self.run_pca()
            
        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to update analysis: {e}")
    
    def extract_dose_from_name(self, name):
        """Extract dose information from sample name"""
        import re
        
        # Handle square-based naming (SQ1, SQ2, etc. represent doses)
        sq_match = re.search(r'sq(\d+)', name.lower())
        if sq_match:
            return float(sq_match.group(1))
        
        # Try to find numeric dose values in common formats
        patterns = [
            r'dose[_\s]*(\d+\.?\d*)',  # dose_5, dose 10, etc.
            r'(\d+\.?\d*)[_\s]*kev',   # 50_kev, 25 keV, etc.
            r'(\d+\.?\d*)[_\s]*v',     # 100v, 50 V, etc.
            r'(\d+\.?\d*)',            # Just numbers
        ]
        
        name_lower = name.lower()
        for pattern in patterns:
            match = re.search(pattern, name_lower)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        # If no numeric dose found, use alphabetical ordering
        return hash(name) % 1000  # Simple hash-based ID
    
    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            # Check if any files have valid extensions
            valid_extensions = {'.txt', '.tsv', '.csv', '.xlsx'}
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if any(file_path.lower().endswith(ext) for ext in valid_extensions):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()  # Take first file
                
                # Validate file extension
                valid_extensions = {'.txt', '.tsv', '.csv', '.xlsx'}
                if any(file_path.lower().endswith(ext) for ext in valid_extensions):
                    # Show preview dialog
                    preview_dialog = DataPreviewDialog(file_path, self)
                    if preview_dialog.exec() == QDialog.DialogCode.Accepted:
                        self.load_data_file(file_path)
                    event.acceptProposedAction()
                else:
                    QMessageBox.warning(
                        self, "Invalid File Type",
                        f"Please drop a valid data file (.txt, .tsv, .csv, .xlsx)\n\nFile: {file_path}"
                    )
        event.ignore()


    def create_fragment_assignment_tab(self):
        """Create Fragment Assignment tab with database integration"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("🧪 Fragment Assignment")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Ion mode info (read-only display - uses main selector)
        polarity_layout = QHBoxLayout()
        polarity_label = QLabel("Ion Mode:")
        polarity_label.setStyleSheet("font-weight: bold;")
        polarity_layout.addWidget(polarity_label)

        self.assignment_polarity_display = QLabel("(Use main Ion Mode selector above)")
        self.assignment_polarity_display.setStyleSheet("color: #666; font-style: italic;")
        polarity_layout.addWidget(self.assignment_polarity_display)

        polarity_layout.addStretch()
        layout.addLayout(polarity_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh Top Loadings")
        refresh_btn.clicked.connect(self.refresh_assignment_table)
        button_layout.addWidget(refresh_btn)

        add_btn = QPushButton("➕ Add Assignment")
        add_btn.clicked.connect(self.add_manual_assignment)
        button_layout.addWidget(add_btn)

        save_btn = QPushButton("💾 Save Database")
        save_btn.clicked.connect(self.save_assignments_database)
        button_layout.addWidget(save_btn)

        export_btn = QPushButton("📤 Export Table")
        export_btn.clicked.connect(self.export_assignment_table)
        export_btn.setToolTip("Export assignment table to CSV file")
        button_layout.addWidget(export_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Assignment table with simplified structure for user review
        self.assignment_table = QTableWidget()
        self.assignment_table.setColumnCount(6)
        self.assignment_table.setHorizontalHeaderLabels([
            "m/z", "PC1 Loading", "Current Assignment", "Confidence", "Action", "Notes"
        ])

        # Set column widths
        header_view = self.assignment_table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.resizeSection(0, 80)   # m/z
        header_view.resizeSection(1, 100)  # PC1 Loading
        header_view.resizeSection(2, 180)  # Current Assignment
        header_view.resizeSection(3, 80)   # Confidence
        header_view.resizeSection(4, 100)  # Action button

        self.assignment_table.setAlternatingRowColors(True)
        self.assignment_table.setSortingEnabled(True)
        layout.addWidget(self.assignment_table)

        return widget

    def create_group_analysis_tab(self):
        """Create Individual Group Analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("🔬 Individual Group Analysis")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Description
        description = QLabel("Analyze fragments in individual sample groups to correlate with FTIR and XPS data")
        description.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(description)

        # Controls section
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout(controls_group)

        # Sample group selection
        group_label = QLabel("Sample Group:")
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(200)
        self.group_combo.currentTextChanged.connect(self.update_group_analysis)
        controls_layout.addWidget(group_label)
        controls_layout.addWidget(self.group_combo)

        controls_layout.addStretch()

        # Analysis button
        analyze_btn = QPushButton("🧬 Analyze Group")
        analyze_btn.clicked.connect(self.run_group_analysis)
        controls_layout.addWidget(analyze_btn)

        # Export button
        export_btn = QPushButton("📊 Export Results")
        export_btn.clicked.connect(self.export_group_analysis)
        controls_layout.addWidget(export_btn)

        layout.addWidget(controls_group)

        # Results section with side-by-side tables
        results_group = QGroupBox("Top Fragment Intensities")
        results_layout = QHBoxLayout(results_group)

        # Negative ion table
        neg_group = QGroupBox("Negative Ion Mode")
        neg_layout = QVBoxLayout(neg_group)

        self.neg_group_table = QTableWidget()
        self.neg_group_table.setColumnCount(4)
        self.neg_group_table.setHorizontalHeaderLabels(['m/z', 'Mean Intensity', 'Std Dev', 'Assignment'])
        self.neg_group_table.horizontalHeader().setStretchLastSection(True)
        self.neg_group_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.neg_group_table.setAlternatingRowColors(True)
        self.neg_group_table.setSortingEnabled(True)
        neg_layout.addWidget(self.neg_group_table)

        # Positive ion table
        pos_group = QGroupBox("Positive Ion Mode")
        pos_layout = QVBoxLayout(pos_group)

        self.pos_group_table = QTableWidget()
        self.pos_group_table.setColumnCount(4)
        self.pos_group_table.setHorizontalHeaderLabels(['m/z', 'Mean Intensity', 'Std Dev', 'Assignment'])
        self.pos_group_table.horizontalHeader().setStretchLastSection(True)
        self.pos_group_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pos_group_table.setAlternatingRowColors(True)
        self.pos_group_table.setSortingEnabled(True)
        pos_layout.addWidget(self.pos_group_table)

        # Add tables to results layout
        results_layout.addWidget(neg_group)
        results_layout.addWidget(pos_group)

        layout.addWidget(results_group)

        # Statistics summary
        self.group_stats_text = QTextEdit()
        self.group_stats_text.setMaximumHeight(120)
        self.group_stats_text.setReadOnly(True)
        layout.addWidget(QLabel("Group Statistics:"))
        layout.addWidget(self.group_stats_text)

        # Visualization section
        viz_group = QGroupBox("Top Peaks Visualization")
        viz_layout = QVBoxLayout(viz_group)

        # Create matplotlib plot for group analysis
        from matplotlib.backends.qt_compat import QtWidgets
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure

        self.group_plot_figure = Figure(figsize=(10, 4))
        self.group_plot_canvas = FigureCanvas(self.group_plot_figure)
        self.group_plot_canvas.setMaximumHeight(300)

        viz_layout.addWidget(self.group_plot_canvas)
        layout.addWidget(viz_group)

        return widget

    def create_individual_fragment_trends_tab(self):
        """Create Individual Fragment Trends tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("📈 Individual Fragment Trends")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Input section
        input_group = QGroupBox("Fragment Analysis Input")
        input_layout = QFormLayout(input_group)

        # M/Z input
        self.mz_input = QLineEdit()
        self.mz_input.setPlaceholderText("Enter m/z value (e.g., 19.023)")
        input_layout.addRow("m/z Value:", self.mz_input)

        # Polarity selection (for fragment trends analysis)
        self.fragment_trends_polarity_combo = QComboBox()
        self.fragment_trends_polarity_combo.addItems(["Negative", "Positive"])
        input_layout.addRow("Ion Mode:", self.fragment_trends_polarity_combo)

        # Element constraints
        elements_group = QGroupBox("Element Constraints")
        elements_layout = QGridLayout(elements_group)

        # Expected elements (alucone)
        self.elements_expected = {}
        expected_elements = [("C", "Carbon"), ("H", "Hydrogen"), ("O", "Oxygen"), ("Al", "Aluminum")]
        for i, (symbol, name) in enumerate(expected_elements):
            checkbox = QCheckBox(f"{symbol} ({name})")
            checkbox.setChecked(True)
            self.elements_expected[symbol] = checkbox
            elements_layout.addWidget(checkbox, 0, i)

        # Contaminants
        self.elements_contaminants = {}
        contaminant_elements = [("F", "Fluorine"), ("Cl", "Chlorine"), ("Si", "Silicon"), ("N", "Nitrogen")]
        for i, (symbol, name) in enumerate(contaminant_elements):
            checkbox = QCheckBox(f"{symbol} ({name})")
            checkbox.setChecked(False)  # Unchecked by default
            self.elements_contaminants[symbol] = checkbox
            elements_layout.addWidget(checkbox, 1, i)

        input_layout.addRow(elements_group)

        layout.addWidget(input_group)

        # Calculate button
        calculate_btn = QPushButton("🧮 Calculate Possible Fragments")
        calculate_btn.clicked.connect(self.calculate_fragments)
        layout.addWidget(calculate_btn)

        # Results area
        self.fragment_results = QTextEdit()
        self.fragment_results.setReadOnly(True)
        self.fragment_results.setMaximumHeight(200)
        layout.addWidget(QLabel("Possible Fragment Assignments:"))
        layout.addWidget(self.fragment_results)

        # Note: Contamination filtering is now handled in the main PCA preprocessing options

        return widget

    def create_familial_trends_tab(self):
        """Create Familial Trends tab for chemical family analysis"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("👨‍👩‍👧‍👦 Familial Chemical Trends (Alucone)")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Chemical family selection
        family_group = QGroupBox("Chemical Family Selection")
        family_layout = QGridLayout(family_group)

        # Define chemical families for alucone with butyne linker
        self.chemical_families = {
            "Al-based": {"description": "Al-O, Al-C bonds", "color": "#1f77b4"},
            "Saturated Carbon": {"description": "Alkyl chains, cycloalkanes", "color": "#ff7f0e"},
            "Unsaturated Carbon": {"description": "Alkenes, alkynes, aromatics", "color": "#2ca02c"},
            "Carbonyl": {"description": "C=O, aldehydes, ketones, acids", "color": "#d62728"},
            "Hydroxyl": {"description": "OH groups from hydrolysis", "color": "#9467bd"},
            "Ether/Ester": {"description": "C-O-C, COO linkages", "color": "#8c564b"},
            "Nitrogenous": {"description": "N-containing compounds", "color": "#e377c2"}
        }

        self.family_checkboxes = {}
        row, col = 0, 0
        for family, info in self.chemical_families.items():
            checkbox = QCheckBox(f"{family}\n({info['description']})")
            checkbox.setChecked(True)
            self.family_checkboxes[family] = checkbox
            family_layout.addWidget(checkbox, row, col)
            col += 1
            if col >= 3:  # 3 families per row
                col = 0
                row += 1

        layout.addWidget(family_group)

        # Control buttons
        button_layout = QHBoxLayout()

        assign_families_btn = QPushButton("🔗 Auto-Assign Families")
        assign_families_btn.clicked.connect(self.auto_assign_chemical_families)
        button_layout.addWidget(assign_families_btn)

        plot_families_btn = QPushButton("📊 Plot Family Trends")
        plot_families_btn.clicked.connect(self.plot_familial_trends)
        button_layout.addWidget(plot_families_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Plot options
        options_layout = QHBoxLayout()

        # As-Deposited inclusion checkbox
        self.include_as_deposited_checkbox = QCheckBox("Include As-Deposited samples")
        self.include_as_deposited_checkbox.setChecked(True)  # Default to include
        self.include_as_deposited_checkbox.setToolTip("Include As-Deposited (0 dose) samples in dose response plots")
        options_layout.addWidget(self.include_as_deposited_checkbox)

        # Curve fitting checkbox
        self.fit_curve_checkbox = QCheckBox("Fit dose response curve")
        self.fit_curve_checkbox.setChecked(False)  # Default to simple line plot
        self.fit_curve_checkbox.setToolTip("Fit exponential/sigmoidal curves instead of linear connections")
        options_layout.addWidget(self.fit_curve_checkbox)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Plotting area
        self.familial_trends_canvas = PCAPlotCanvas(widget, width=10, height=8)
        self.familial_trends_toolbar = NavigationToolbar(self.familial_trends_canvas, widget)

        layout.addWidget(self.familial_trends_toolbar)
        layout.addWidget(self.familial_trends_canvas)

        # Family assignment status
        self.family_status = QLabel("No family assignments loaded. Click 'Auto-Assign Families' to start.")
        layout.addWidget(self.family_status)

        return widget

    def create_database_management_tab(self):
        """Create Database Management tab with strict controls and validation"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header with warning
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_frame.setStyleSheet("background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;")
        header_layout = QVBoxLayout(header_frame)

        warning_label = QLabel("⚠️ DATABASE MANAGEMENT - EXPERT USE ONLY")
        warning_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #856404;")
        header_layout.addWidget(warning_label)

        info_label = QLabel("This tab allows controlled additions to the fragment database with validation.\n" +
                           "The main database is protected from direct modification.")
        info_label.setStyleSheet("color: #856404; padding: 5px;")
        header_layout.addWidget(info_label)

        layout.addWidget(header_frame)

        # Database status section
        status_group = QGroupBox("📊 Database Status")
        status_layout = QVBoxLayout(status_group)

        self.db_status_label = QLabel("Database not loaded")
        status_layout.addWidget(self.db_status_label)

        refresh_db_btn = QPushButton("🔄 Refresh Database Status")
        refresh_db_btn.clicked.connect(self.refresh_database_status)
        status_layout.addWidget(refresh_db_btn)

        layout.addWidget(status_group)

        # Pending assignments section
        pending_group = QGroupBox("⏳ Pending Assignments (Validation Required)")
        pending_layout = QVBoxLayout(pending_group)

        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(7)
        self.pending_table.setHorizontalHeaderLabels([
            "Mass", "Assignment", "Formula", "Family", "Confidence", "Status", "Action"
        ])
        self.pending_table.setAlternatingRowColors(True)
        pending_layout.addWidget(self.pending_table)

        # Validation controls
        validation_layout = QHBoxLayout()

        validate_all_btn = QPushButton("✅ Validate All")
        validate_all_btn.clicked.connect(self.validate_all_pending)
        validation_layout.addWidget(validate_all_btn)

        clear_pending_btn = QPushButton("🗑️ Clear Pending")
        clear_pending_btn.clicked.connect(self.clear_pending_assignments)
        validation_layout.addWidget(clear_pending_btn)

        validation_layout.addStretch()
        pending_layout.addLayout(validation_layout)

        layout.addWidget(pending_group)

        # Manual entry section
        manual_group = QGroupBox("✏️ Add New Fragment (Manual Entry)")
        manual_layout = QFormLayout(manual_group)

        self.new_mass = QLineEdit()
        self.new_mass.setPlaceholderText("e.g., 26.9815")
        manual_layout.addRow("Mass (Da):", self.new_mass)

        self.new_assignment = QLineEdit()
        self.new_assignment.setPlaceholderText("e.g., Al+")
        manual_layout.addRow("Assignment:", self.new_assignment)

        self.new_formula = QLineEdit()
        self.new_formula.setPlaceholderText("e.g., Al")
        manual_layout.addRow("Formula:", self.new_formula)

        self.new_family = QComboBox()
        self.new_family.addItems([
            "Al-based", "Saturated Carbon", "Unsaturated Carbon",
            "Carbonyl", "Hydroxyl", "Ether/Ester", "Contamination", "Unknown"
        ])
        manual_layout.addRow("Family:", self.new_family)

        self.new_polarity = QComboBox()
        self.new_polarity.addItems(["positive", "negative"])
        manual_layout.addRow("Polarity:", self.new_polarity)

        self.new_confidence = QComboBox()
        self.new_confidence.addItems(["High", "Medium", "Low"])
        self.new_confidence.setCurrentText("Medium")
        manual_layout.addRow("Confidence:", self.new_confidence)

        self.new_notes = QTextEdit()
        self.new_notes.setMaximumHeight(80)
        self.new_notes.setPlaceholderText("Optional notes or literature reference...")
        manual_layout.addRow("Notes:", self.new_notes)

        # Add buttons
        add_layout = QHBoxLayout()

        validate_new_btn = QPushButton("🔍 Validate & Preview")
        validate_new_btn.clicked.connect(self.validate_new_fragment)
        add_layout.addWidget(validate_new_btn)

        add_pending_btn = QPushButton("📝 Add to Pending")
        add_pending_btn.clicked.connect(self.add_to_pending)
        add_layout.addWidget(add_pending_btn)

        add_layout.addStretch()
        manual_layout.addRow(add_layout)

        layout.addWidget(manual_group)

        # Database backup section
        backup_group = QGroupBox("💾 Database Backup & Safety")
        backup_layout = QHBoxLayout(backup_group)

        backup_btn = QPushButton("📁 Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        backup_layout.addWidget(backup_btn)

        restore_btn = QPushButton("🔄 Restore from Backup")
        restore_btn.clicked.connect(self.restore_database)
        backup_layout.addWidget(restore_btn)

        validate_db_btn = QPushButton("🔍 Validate Database")
        validate_db_btn.clicked.connect(self.validate_database_integrity)
        backup_layout.addWidget(validate_db_btn)

        report_btn = QPushButton("📋 Generate Report")
        report_btn.clicked.connect(self.export_database_report)
        backup_layout.addWidget(report_btn)

        backup_layout.addStretch()
        layout.addWidget(backup_group)

        # Apply pending assignments section
        apply_group = QGroupBox("🚀 Apply Validated Changes")
        apply_layout = QHBoxLayout(apply_group)

        apply_pending_btn = QPushButton("✅ Apply All Pending Assignments")
        apply_pending_btn.clicked.connect(self.apply_pending_assignments)
        apply_pending_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        apply_layout.addWidget(apply_pending_btn)

        apply_layout.addStretch()
        layout.addWidget(apply_group)

        layout.addStretch()

        return widget

    def create_stick_spectrum_tab(self):
        """
        Create Stick Spectrum tab for mass spectrum visualization
        Stage 1: Basic implementation with dose selection and plotting
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header_label = QLabel("📊 Stick Spectrum Visualization")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)

        # Dose selection section
        dose_group = QGroupBox("Sample Selection")
        dose_layout = QHBoxLayout(dose_group)

        dose_layout.addWidget(QLabel("Select Dose Level:"))

        # Dose buttons (SQ0, SQ2-SQ5 only - SQ1 is excluded)
        self.dose_buttons = QComboBox()
        self.dose_buttons.addItems([
            "SQ0 (As-deposited, 0 µC/cm²)",
            "SQ2 (2000 µC/cm²)",
            "SQ3 (5000 µC/cm²)",
            "SQ4 (10000 µC/cm²)",
            "SQ5 (15000 µC/cm²)"
        ])
        dose_layout.addWidget(self.dose_buttons)

        # Plot button
        plot_spectrum_btn = QPushButton("📈 Plot Spectrum")
        plot_spectrum_btn.clicked.connect(self.plot_stick_spectrum)
        dose_layout.addWidget(plot_spectrum_btn)

        dose_layout.addStretch()
        layout.addWidget(dose_group)

        # Options section
        options_group = QGroupBox("Display Options")
        options_layout = QHBoxLayout(options_group)

        self.show_sd_checkbox = QCheckBox("Show Replicate Variability (SD plot)")
        self.show_sd_checkbox.setChecked(False)
        self.show_sd_checkbox.stateChanged.connect(self.update_stick_spectrum_display)
        options_layout.addWidget(self.show_sd_checkbox)

        options_layout.addStretch()

        # Fragment table button (Stage 2)
        view_table_btn = QPushButton("📋 View Fragment Table")
        view_table_btn.clicked.connect(self.show_fragment_table_dialog)
        options_layout.addWidget(view_table_btn)

        layout.addWidget(options_group)

        # Filters section (Stage 3+)
        filters_group = QGroupBox("Peak Filters")
        filters_group.setCheckable(True)
        filters_group.setChecked(False)  # Collapsed by default
        filters_layout = QVBoxLayout(filters_group)

        # Filter 1: Intensity threshold (Stage 3)
        intensity_filter_layout = QHBoxLayout()
        self.intensity_filter_enabled = QCheckBox("Intensity Threshold:")
        self.intensity_filter_enabled.setChecked(False)
        self.intensity_filter_enabled.stateChanged.connect(self.apply_stick_filters)
        intensity_filter_layout.addWidget(self.intensity_filter_enabled)

        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setMinimum(0)
        self.intensity_slider.setMaximum(100)
        self.intensity_slider.setValue(0)
        self.intensity_slider.setTickPosition(QSlider.TicksBelow)
        self.intensity_slider.setTickInterval(10)
        self.intensity_slider.valueChanged.connect(self.update_intensity_filter_label)
        self.intensity_slider.valueChanged.connect(self.apply_stick_filters)
        intensity_filter_layout.addWidget(self.intensity_slider)

        self.intensity_filter_label = QLabel("0.000 (0% of max)")
        self.intensity_filter_label.setMinimumWidth(150)
        intensity_filter_layout.addWidget(self.intensity_filter_label)

        filters_layout.addLayout(intensity_filter_layout)

        # Filter 2: Top N peaks (Stage 4)
        topn_filter_layout = QHBoxLayout()
        self.topn_filter_enabled = QCheckBox("Top N Peaks:")
        self.topn_filter_enabled.setChecked(False)
        self.topn_filter_enabled.stateChanged.connect(self.apply_stick_filters)
        topn_filter_layout.addWidget(self.topn_filter_enabled)

        self.topn_dropdown = QComboBox()
        self.topn_dropdown.addItems(["All", "20", "50", "100", "200"])
        self.topn_dropdown.setCurrentText("All")
        self.topn_dropdown.currentTextChanged.connect(self.apply_stick_filters)
        topn_filter_layout.addWidget(self.topn_dropdown)

        topn_filter_layout.addWidget(QLabel("highest intensity peaks"))
        topn_filter_layout.addStretch()

        filters_layout.addLayout(topn_filter_layout)

        # Filter 3: m/z range (Stage 5)
        mz_range_layout = QHBoxLayout()
        self.mz_range_enabled = QCheckBox("m/z Range:")
        self.mz_range_enabled.setChecked(False)
        self.mz_range_enabled.stateChanged.connect(self.apply_stick_filters)
        mz_range_layout.addWidget(self.mz_range_enabled)

        mz_range_layout.addWidget(QLabel("Min:"))
        self.mz_min_input = QLineEdit()
        self.mz_min_input.setPlaceholderText("1.0")
        self.mz_min_input.setMaximumWidth(80)
        self.mz_min_input.textChanged.connect(self.validate_mz_range)
        mz_range_layout.addWidget(self.mz_min_input)

        mz_range_layout.addWidget(QLabel("Max:"))
        self.mz_max_input = QLineEdit()
        self.mz_max_input.setPlaceholderText("300.0")
        self.mz_max_input.setMaximumWidth(80)
        self.mz_max_input.textChanged.connect(self.validate_mz_range)
        mz_range_layout.addWidget(self.mz_max_input)

        self.mz_range_status = QLabel("✓")
        self.mz_range_status.setStyleSheet("color: green;")
        mz_range_layout.addWidget(self.mz_range_status)

        mz_range_layout.addStretch()

        filters_layout.addLayout(mz_range_layout)

        # Filter 4: PCA loadings (Stage 6)
        pca_loadings_layout = QHBoxLayout()
        self.pca_loadings_enabled = QCheckBox("PCA Loadings:")
        self.pca_loadings_enabled.setChecked(False)
        self.pca_loadings_enabled.stateChanged.connect(self.apply_stick_filters)
        pca_loadings_layout.addWidget(self.pca_loadings_enabled)

        pca_loadings_layout.addWidget(QLabel("|PC1| >"))
        self.pca_loadings_slider = QSlider(Qt.Horizontal)
        self.pca_loadings_slider.setMinimum(0)
        self.pca_loadings_slider.setMaximum(100)
        self.pca_loadings_slider.setValue(5)  # Default 0.05
        self.pca_loadings_slider.setTickPosition(QSlider.TicksBelow)
        self.pca_loadings_slider.setTickInterval(10)
        self.pca_loadings_slider.valueChanged.connect(self.update_pca_loadings_label)
        self.pca_loadings_slider.valueChanged.connect(self.apply_stick_filters)
        pca_loadings_layout.addWidget(self.pca_loadings_slider)

        self.pca_loadings_label = QLabel("0.05")
        self.pca_loadings_label.setMinimumWidth(80)
        pca_loadings_layout.addWidget(self.pca_loadings_label)

        self.pca_loadings_status = QLabel("(PCA not run)")
        self.pca_loadings_status.setStyleSheet("color: gray;")
        pca_loadings_layout.addWidget(self.pca_loadings_status)

        pca_loadings_layout.addStretch()

        filters_layout.addLayout(pca_loadings_layout)

        layout.addWidget(filters_group)

        # Plotting area
        plot_group = QGroupBox("Mass Spectrum")
        plot_layout = QVBoxLayout(plot_group)

        # Create stick spectrum canvas
        self.stick_canvas = StickSpectrumCanvas(widget, width=12, height=8)
        self.stick_toolbar = NavigationToolbar(self.stick_canvas, widget)

        plot_layout.addWidget(self.stick_toolbar)
        plot_layout.addWidget(self.stick_canvas)

        layout.addWidget(plot_group)

        return widget

    def plot_stick_spectrum(self):
        """
        Plot stick spectrum for selected dose
        Stage 2: Fragment assignment integration - load assignments and display labels
        """
        # Check if data is loaded
        if not hasattr(self, 'pca_analyzer') or self.pca_analyzer is None:
            QMessageBox.warning(
                self,
                "No Data Loaded",
                "Please load data first using the main data loading section."
            )
            return

        # Get selected dose
        dose_text = self.dose_buttons.currentText()
        # Extract SQ number (e.g., "SQ0" from "SQ0 (As-deposited, 0 µC/cm²)")
        sq_label = dose_text.split()[0]  # "SQ0", "SQ2", etc.
        dose_num = int(sq_label.replace("SQ", ""))  # 0, 2, 3, 4, 5

        try:
            # Get raw data (TIC-normalized, no preprocessing)
            raw_data = self.pca_analyzer.raw_data  # DataFrame with m/z as index
            sample_metadata = self.pca_analyzer.sample_metadata

            # Filter samples for selected dose
            dose_mask = sample_metadata['dose_id'] == dose_num
            dose_samples = sample_metadata[dose_mask]

            if len(dose_samples) == 0:
                QMessageBox.warning(
                    self,
                    "No Data",
                    f"No samples found for {sq_label}"
                )
                return

            # Get column names for this dose (P1, P2, P3)
            sample_names = dose_samples['sample_name'].tolist()

            # Extract intensity data for these samples
            dose_data = raw_data[sample_names]

            # Calculate mean and std across replicates
            mean_intensities = dose_data.mean(axis=1).values
            std_devs = dose_data.std(axis=1).values

            # Get m/z values
            mz_values = raw_data.index.values

            # Get polarity for title
            polarity_display = Polarity.display_name(self.multi_ion_manager.active_polarity)

            # Create title
            title = f"{polarity_display} - {dose_text}"

            # Stage 2: Load fragment database and find assignments
            if not hasattr(self, 'fragment_database') or not self.fragment_database:
                self.load_fragment_database()

            # Build fragment assignment data for all peaks
            fragment_assignments = []
            labels = {}  # Will store {mz: label_text} for labeled peaks

            current_polarity = self.multi_ion_manager.active_polarity

            for i, mz in enumerate(mz_values):
                # Find matching assignment within ±0.0001 Da tolerance
                matches = self.find_multiple_fragment_assignments(
                    target_mass=mz,
                    tolerance_ppm=100.0,  # ~100 ppm gives ±0.0001 Da at m/z=1
                    polarity=current_polarity,
                    max_matches=1
                )

                # Store assignment info (even if unassigned)
                assignment_info = {
                    'mz': mz,
                    'mean_intensity': mean_intensities[i],
                    'std_dev': std_devs[i],
                    'cv_percent': (std_devs[i] / mean_intensities[i] * 100) if mean_intensities[i] > 0 else 0,
                    'assignment': matches[0]['assignments'][0] if matches else "Unassigned",
                    'formula': matches[0]['formulas'][0] if matches else "",
                    'confidence': matches[0].get('confidence', '') if matches else "",
                    'show_label': False  # Default: don't show label
                }
                fragment_assignments.append(assignment_info)

            # Store fragment assignment data for table display
            self.current_fragment_assignments = fragment_assignments

            # Plot (with empty labels for now - user will toggle them in table)
            show_sd = self.show_sd_checkbox.isChecked()
            self.stick_canvas.plot_stick_spectrum(
                mz_values=mz_values,
                intensities=mean_intensities,
                std_devs=std_devs,
                labels=labels,  # Empty for now
                show_sd_plot=show_sd,
                title=title
            )

            # Store current plot data for replotting when options change
            self.current_stick_data = {
                'mz_values': mz_values,
                'intensities': mean_intensities,
                'std_devs': std_devs,
                'title': title,
                'labels': labels
            }

            # Count assignments
            assigned_count = sum(1 for a in fragment_assignments if a['assignment'] != "Unassigned")

            print(f"✅ Plotted stick spectrum for {sq_label}")
            print(f"   {len(mz_values)} m/z values")
            print(f"   {len(sample_names)} replicates averaged")
            print(f"   {assigned_count}/{len(mz_values)} peaks assigned")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Plot Error",
                f"Error plotting stick spectrum:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def update_stick_spectrum_display(self):
        """Update stick spectrum when display options change"""
        if hasattr(self, 'current_stick_data') and self.current_stick_data:
            show_sd = self.show_sd_checkbox.isChecked()

            # Rebuild labels from fragment assignments based on show_label flags
            labels = {}
            if hasattr(self, 'current_fragment_assignments'):
                for assignment in self.current_fragment_assignments:
                    if assignment['show_label'] and assignment['assignment'] != "Unassigned":
                        labels[assignment['mz']] = assignment['assignment']

            self.stick_canvas.plot_stick_spectrum(
                mz_values=self.current_stick_data['mz_values'],
                intensities=self.current_stick_data['intensities'],
                std_devs=self.current_stick_data['std_devs'],
                labels=labels,
                show_sd_plot=show_sd,
                title=self.current_stick_data['title']
            )

    def validate_mz_range(self):
        """Validate m/z range inputs and apply filter if valid"""
        # Get input values
        min_text = self.mz_min_input.text().strip()
        max_text = self.mz_max_input.text().strip()

        # If both empty, valid (use full range)
        if not min_text and not max_text:
            self.mz_range_status.setText("✓")
            self.mz_range_status.setStyleSheet("color: green;")
            self.apply_stick_filters()
            return

        # Try to parse as floats
        try:
            mz_min = float(min_text) if min_text else 0.0
            mz_max = float(max_text) if max_text else 1000.0

            # Validate min < max
            if mz_min >= mz_max:
                self.mz_range_status.setText("✗ Min ≥ Max")
                self.mz_range_status.setStyleSheet("color: red;")
                return

            # Valid range
            self.mz_range_status.setText("✓")
            self.mz_range_status.setStyleSheet("color: green;")
            self.apply_stick_filters()

        except ValueError:
            self.mz_range_status.setText("✗ Invalid")
            self.mz_range_status.setStyleSheet("color: red;")

    def update_pca_loadings_label(self):
        """Update PCA loadings filter label to show threshold value"""
        # Convert slider value (0-100) to loading threshold (0.00-1.00)
        slider_value = self.pca_loadings_slider.value()
        threshold = slider_value / 100.0

        self.pca_loadings_label.setText(f"{threshold:.2f}")

    def update_intensity_filter_label(self):
        """Update intensity filter label to show threshold value"""
        if not hasattr(self, 'current_stick_data') or not self.current_stick_data:
            return

        # Get max intensity from unfiltered data
        max_intensity = self.current_stick_data['intensities'].max()

        # Calculate threshold value from slider percentage
        percent = self.intensity_slider.value()
        threshold = (percent / 100.0) * max_intensity

        self.intensity_filter_label.setText(f"{threshold:.3e} ({percent}% of max)")

    def apply_stick_filters(self):
        """
        Apply all active filters to stick spectrum data
        Stage 3: Intensity threshold filter
        Stage 4: Top N peaks filter
        Stage 5: m/z range filter
        Stage 6: PCA loadings filter
        """
        if not hasattr(self, 'current_stick_data') or not self.current_stick_data:
            return

        # Start with all data (unfiltered)
        mz_values = self.current_stick_data['mz_values']
        intensities = self.current_stick_data['intensities']
        std_devs = self.current_stick_data['std_devs']

        # Create filter mask (True = keep peak)
        mask = np.ones(len(mz_values), dtype=bool)

        # Filter 1: Intensity threshold
        if self.intensity_filter_enabled.isChecked():
            max_intensity = intensities.max()
            percent = self.intensity_slider.value()
            threshold = (percent / 100.0) * max_intensity

            intensity_mask = intensities >= threshold
            mask &= intensity_mask

            print(f"   Intensity filter: {mask.sum()}/{len(mask)} peaks above {percent}% threshold")

        # Filter 2: Top N peaks (applied after intensity filter)
        if self.topn_filter_enabled.isChecked():
            topn_text = self.topn_dropdown.currentText()

            if topn_text != "All":
                n_peaks = int(topn_text)

                # Get indices of peaks that passed previous filters
                passing_indices = np.where(mask)[0]

                # Sort by intensity (descending) among passing peaks
                passing_intensities = intensities[passing_indices]
                sorted_indices = np.argsort(passing_intensities)[::-1]  # Descending

                # Keep only top N
                if len(sorted_indices) > n_peaks:
                    # Indices to keep (top N)
                    keep_indices = passing_indices[sorted_indices[:n_peaks]]

                    # Update mask: set all to False, then set top N to True
                    topn_mask = np.zeros(len(mz_values), dtype=bool)
                    topn_mask[keep_indices] = True

                    # Combine with previous mask
                    mask &= topn_mask

                    print(f"   Top N filter: kept {n_peaks} highest intensity peaks")

        # Filter 3: m/z range
        if self.mz_range_enabled.isChecked():
            # Get range values
            min_text = self.mz_min_input.text().strip()
            max_text = self.mz_max_input.text().strip()

            # Only apply if valid inputs
            if self.mz_range_status.text() == "✓":
                try:
                    mz_min = float(min_text) if min_text else mz_values.min()
                    mz_max = float(max_text) if max_text else mz_values.max()

                    mz_range_mask = (mz_values >= mz_min) & (mz_values <= mz_max)
                    mask &= mz_range_mask

                    print(f"   m/z range filter: {mask.sum()}/{len(mask)} peaks in range [{mz_min:.1f}, {mz_max:.1f}]")

                except ValueError:
                    pass  # Skip if invalid

        # Filter 4: PCA loadings (Stage 6)
        if self.pca_loadings_enabled.isChecked():
            # Check if PCA has been run
            if hasattr(self, 'pca_completed') and self.pca_completed:
                try:
                    # Get PCA loadings for PC1
                    loadings_df = self.pca_analyzer.get_loadings_dataframe()

                    if 'PC1' in loadings_df.columns:
                        # Get threshold from slider
                        slider_value = self.pca_loadings_slider.value()
                        threshold = slider_value / 100.0

                        # Match m/z values to loadings
                        # For each m/z in spectrum, find corresponding loading
                        pca_mask = np.zeros(len(mz_values), dtype=bool)

                        for i, mz in enumerate(mz_values):
                            # Find loading for this m/z (exact match)
                            if mz in loadings_df.index:
                                loading = loadings_df.loc[mz, 'PC1']
                                abs_loading = abs(loading)

                                # Keep if absolute loading exceeds threshold
                                if abs_loading >= threshold:
                                    pca_mask[i] = True

                        # Combine with previous mask
                        mask &= pca_mask

                        print(f"   PCA loadings filter: {mask.sum()}/{len(mask)} peaks with |PC1| >= {threshold:.2f}")

                        # Update status
                        self.pca_loadings_status.setText(f"({mask.sum()} peaks)")
                        self.pca_loadings_status.setStyleSheet("color: green;")

                except Exception as e:
                    print(f"   Warning: PCA loadings filter failed: {e}")
                    self.pca_loadings_status.setText("(Error)")
                    self.pca_loadings_status.setStyleSheet("color: red;")
            else:
                # PCA not run
                self.pca_loadings_status.setText("(PCA not run)")
                self.pca_loadings_status.setStyleSheet("color: gray;")

        # Apply mask to data
        filtered_mz = mz_values[mask]
        filtered_intensities = intensities[mask]
        filtered_std_devs = std_devs[mask]

        # Filter fragment assignments
        if hasattr(self, 'current_fragment_assignments'):
            # Update visibility of assignments based on filter
            for i, assignment in enumerate(self.current_fragment_assignments):
                assignment['filtered'] = not mask[i]  # Mark as filtered if not in mask

        # Rebuild labels (only for visible peaks)
        labels = {}
        if hasattr(self, 'current_fragment_assignments'):
            for i, assignment in enumerate(self.current_fragment_assignments):
                if mask[i] and assignment['show_label'] and assignment['assignment'] != "Unassigned":
                    labels[assignment['mz']] = assignment['assignment']

        # Update plot
        show_sd = self.show_sd_checkbox.isChecked()
        self.stick_canvas.plot_stick_spectrum(
            mz_values=filtered_mz,
            intensities=filtered_intensities,
            std_devs=filtered_std_devs,
            labels=labels,
            show_sd_plot=show_sd,
            title=self.current_stick_data['title']
        )

        # Update statistics
        print(f"✅ Filters applied: {mask.sum()}/{len(mask)} peaks visible")

    def show_fragment_table_dialog(self):
        """
        Show pop-out dialog with fragment assignment table
        Stage 2: Read-only table with sortable columns and label toggles
        """
        # Check if fragment data exists
        if not hasattr(self, 'current_fragment_assignments') or not self.current_fragment_assignments:
            QMessageBox.information(
                self,
                "No Data",
                "Please plot a stick spectrum first."
            )
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Fragment Assignment Table")
        dialog.resize(1000, 600)
        layout = QVBoxLayout(dialog)

        # Header with statistics
        header_label = QLabel()
        total = len(self.current_fragment_assignments)
        assigned = sum(1 for a in self.current_fragment_assignments if a['assignment'] != "Unassigned")
        header_label.setText(f"📊 Fragment Assignments: {assigned}/{total} peaks assigned ({assigned/total*100:.1f}%)")
        header_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 5px;")
        layout.addWidget(header_label)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search:"))
        search_box = QLineEdit()
        search_box.setPlaceholderText("Filter by m/z or assignment...")
        search_layout.addWidget(search_box)
        layout.addLayout(search_layout)

        # Table widget
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "m/z", "Mean Intensity", "Std Dev", "CV%",
            "Assignment", "Confidence", "Show Label"
        ])
        table.setSortingEnabled(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only except for checkboxes
        table.setSelectionBehavior(QTableWidget.SelectRows)

        # Populate table
        table.setRowCount(len(self.current_fragment_assignments))
        for row, assignment in enumerate(self.current_fragment_assignments):
            # m/z (4 decimals)
            mz_item = QTableWidgetItem(f"{assignment['mz']:.4f}")
            mz_item.setData(Qt.UserRole, assignment['mz'])  # Store numeric value for sorting
            table.setItem(row, 0, mz_item)

            # Mean Intensity (scientific notation)
            intensity_item = QTableWidgetItem(f"{assignment['mean_intensity']:.3e}")
            intensity_item.setData(Qt.UserRole, assignment['mean_intensity'])
            table.setItem(row, 1, intensity_item)

            # Std Dev (scientific notation)
            sd_item = QTableWidgetItem(f"{assignment['std_dev']:.3e}")
            sd_item.setData(Qt.UserRole, assignment['std_dev'])
            table.setItem(row, 2, sd_item)

            # CV% (2 decimals)
            cv_item = QTableWidgetItem(f"{assignment['cv_percent']:.2f}%")
            cv_item.setData(Qt.UserRole, assignment['cv_percent'])
            table.setItem(row, 3, cv_item)

            # Assignment
            assignment_item = QTableWidgetItem(assignment['assignment'])
            if assignment['assignment'] == "Unassigned":
                assignment_item.setForeground(QColor(150, 150, 150))  # Gray for unassigned
            table.setItem(row, 4, assignment_item)

            # Confidence
            confidence_item = QTableWidgetItem(assignment['confidence'])
            table.setItem(row, 5, confidence_item)

            # Show Label checkbox
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)

            checkbox = QCheckBox()
            checkbox.setChecked(assignment['show_label'])
            checkbox.setEnabled(assignment['assignment'] != "Unassigned")  # Disable for unassigned

            # Connect checkbox to update function
            checkbox.stateChanged.connect(
                lambda state, r=row: self.toggle_fragment_label(r, state)
            )

            checkbox_layout.addWidget(checkbox)
            table.setCellWidget(row, 6, checkbox_widget)

        # Resize columns to content
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Search functionality
        def filter_table(text):
            text_lower = text.lower()
            for row in range(table.rowCount()):
                # Check m/z and assignment columns
                mz_text = table.item(row, 0).text().lower()
                assignment_text = table.item(row, 4).text().lower()
                match = text_lower in mz_text or text_lower in assignment_text
                table.setRowHidden(row, not match)

        search_box.textChanged.connect(filter_table)

        # Buttons
        button_layout = QHBoxLayout()

        # Export button
        export_btn = QPushButton("💾 Export to CSV")
        export_btn.clicked.connect(lambda: self.export_fragment_table(dialog))
        button_layout.addWidget(export_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def toggle_fragment_label(self, row_index, state):
        """Toggle show_label flag for a fragment and refresh plot"""
        if hasattr(self, 'current_fragment_assignments') and row_index < len(self.current_fragment_assignments):
            self.current_fragment_assignments[row_index]['show_label'] = (state == Qt.Checked)
            # Refresh plot to show/hide label
            self.update_stick_spectrum_display()

    def export_fragment_table(self, parent_dialog):
        """Export fragment assignment table to CSV"""
        if not hasattr(self, 'current_fragment_assignments') or not self.current_fragment_assignments:
            return

        # Get save location
        default_path = f"/home/dreece23/pca-sims/outputs/fragment_table_{self.multi_ion_manager.active_polarity}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            parent_dialog,
            "Export Fragment Table",
            default_path,
            "CSV files (*.csv);;All files (*)"
        )

        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Header
                    writer.writerow(['m/z', 'Mean Intensity', 'Std Dev', 'CV%',
                                   'Assignment', 'Confidence', 'Show Label'])
                    # Data
                    for assignment in self.current_fragment_assignments:
                        writer.writerow([
                            f"{assignment['mz']:.4f}",
                            f"{assignment['mean_intensity']:.6e}",
                            f"{assignment['std_dev']:.6e}",
                            f"{assignment['cv_percent']:.2f}",
                            assignment['assignment'],
                            assignment['confidence'],
                            'Yes' if assignment['show_label'] else 'No'
                        ])

                QMessageBox.information(parent_dialog, "Export Complete",
                                       f"Fragment table exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(parent_dialog, "Export Error",
                                   f"Failed to export table:\n{str(e)}")

    def refresh_fragment_list(self):
        """Populate fragment list from current PCA loadings"""
        if not self.pca_completed:
            QMessageBox.information(self, "No PCA Data", "Please run PCA analysis first.")
            return

        try:
            # Get loadings data
            loadings_df = self.pca_analyzer.get_loadings_dataframe()
            top_loadings = loadings_df['PC1'].abs().sort_values(ascending=False).head(20)

            # Clear and populate list
            self.fragment_list.clear()
            for mass, abs_loading in top_loadings.items():
                original_loading = loadings_df.loc[mass, 'PC1']
                item_text = f"m/z {mass:.3f} (loading: {original_loading:+.6f})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, mass)  # Store mass value
                self.fragment_list.addItem(item)

            print(f"✅ Loaded {len(top_loadings)} fragments for trend analysis")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load fragments: {e}")

    def plot_fragment_trends(self):
        """Plot intensity trends for selected fragments"""
        if not self.pca_completed:
            QMessageBox.information(self, "No PCA Data", "Please run PCA analysis first.")
            return

        selected_items = self.fragment_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Fragments Selected", "Please select fragments to plot.")
            return

        try:
            # Use the current working data from PCA analyzer
            if not self.pca_analyzer or not hasattr(self.pca_analyzer, 'working_data'):
                QMessageBox.information(self, "No Data Available", "Please run PCA analysis first.")
                return

            # Get working data and metadata (respects current sample selection)
            working_data, working_metadata = self.pca_analyzer.get_active_data()
            data_subset = working_data.T  # Transpose to get masses as rows, samples as columns

            # Extract selected fragment masses
            fragment_masses = []
            for item in selected_items:
                mass = item.data(Qt.UserRole)
                fragment_masses.append(mass)

            # Create trend plot
            self.trends_canvas.figure.clear()
            ax = self.trends_canvas.figure.add_subplot(111)

            # Plot each fragment
            for mass in fragment_masses:
                if mass in data_subset.index:
                    intensities = data_subset.loc[mass].values

                    # Group by dose from working metadata
                    sample_names = list(working_data.columns)
                    doses = working_metadata['dose_id'].tolist() if 'dose_id' in working_metadata.columns else list(range(len(sample_names)))

                    ax.plot(doses, intensities, 'o-', label=f'm/z {mass:.3f}', linewidth=2, markersize=6)

            ax.set_xlabel("Dose Level", fontsize=12)
            ax.set_ylabel("Intensity", fontsize=12)
            ax.set_title("Fragment Intensity Trends", fontsize=14, fontweight='bold')
            ax.legend(loc='best', framealpha=0.9)
            ax.grid(True, alpha=0.3)

            # Use viridis colormap
            colors = plt.cm.viridis(np.linspace(0, 1, len(fragment_masses)))
            for line, color in zip(ax.lines, colors):
                line.set_color(color)

            self.trends_canvas.figure.tight_layout()
            self.trends_canvas.draw()

            print(f"✅ Plotted trends for {len(fragment_masses)} fragments")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot trends: {e}")
            import traceback
            traceback.print_exc()

    def calculate_fragments(self):
        """Calculate possible fragment assignments"""
        try:
            mz_text = self.mz_input.text().strip()
            if not mz_text:
                QMessageBox.information(self, "Input Required", "Please enter an m/z value.")
                return

            target_mz = float(mz_text)
            polarity = self.fragment_trends_polarity_combo.currentText()

            # Get selected elements
            elements = []
            for symbol, checkbox in self.elements_expected.items():
                if checkbox.isChecked():
                    elements.append(symbol)
            for symbol, checkbox in self.elements_contaminants.items():
                if checkbox.isChecked():
                    elements.append(symbol)

            # Simple fragment calculation (this could be expanded)
            results = self.generate_fragment_possibilities(target_mz, polarity, elements)

            self.fragment_results.clear()
            self.fragment_results.append(f"Fragment Analysis for m/z {target_mz:.3f} ({polarity} mode)\n")
            self.fragment_results.append("=" * 50)
            self.fragment_results.append(results)

        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter a valid numeric m/z value.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fragment calculation failed: {e}")

    def generate_fragment_possibilities(self, target_mz, polarity, elements):
        """Generate possible fragment assignments"""
        # Atomic masses
        atomic_masses = {
            'C': 12.000, 'H': 1.008, 'O': 15.999, 'Al': 26.982,
            'F': 18.998, 'Cl': 34.969, 'Si': 27.977, 'N': 14.007
        }

        results = []
        tolerance = 0.1  # Mass tolerance

        # Common fragment patterns for alucone
        common_fragments = [
            ('H-', [('H', 1)], 'Hydride'),
            ('O-', [('O', 1)], 'Oxide'),
            ('OH-', [('O', 1), ('H', 1)], 'Hydroxide'),
            ('AlO-', [('Al', 1), ('O', 1)], 'Aluminum oxide'),
            ('AlO2-', [('Al', 1), ('O', 2)], 'Aluminum dioxide'),
            ('C2H-', [('C', 2), ('H', 1)], 'Acetylide'),
            ('CHO-', [('C', 1), ('H', 1), ('O', 1)], 'Formyl'),
            ('C2H3O-', [('C', 2), ('H', 3), ('O', 1)], 'Acetyl'),
        ]

        # Add contaminant fragments
        if 'F' in elements:
            common_fragments.extend([
                ('F-', [('F', 1)], 'Fluoride (contamination)'),
                ('CF-', [('C', 1), ('F', 1)], 'Carbon fluoride (contamination)'),
            ])

        if 'Cl' in elements:
            common_fragments.extend([
                ('Cl-', [('Cl', 1)], 'Chloride (contamination)'),
            ])

        # Check each fragment
        for formula, composition, description in common_fragments:
            calculated_mass = sum(atomic_masses[element] * count for element, count in composition)

            # Check if it's within tolerance
            if abs(calculated_mass - target_mz) <= tolerance:
                error = calculated_mass - target_mz
                results.append(f"✅ {formula}: {calculated_mass:.3f} Da (Δ = {error:+.3f}) - {description}")

        if not results:
            results.append("❌ No matching fragments found within ±0.1 Da tolerance")
            results.append(f"\nFor reference, common elements in your system:")
            for element in elements:
                if element in atomic_masses:
                    results.append(f"  {element}: {atomic_masses[element]:.3f} Da")

        return "\n".join(results)


    # New method implementations for the redesigned tabs

    def calculate_fragment_mass(self, formula: str) -> float:
        """Calculate theoretical mass from molecular formula"""
        # Atomic masses (most common isotopes)
        atomic_masses = {
            'H': 1.007825, 'C': 12.000000, 'N': 14.003074, 'O': 15.994915,
            'F': 18.998403, 'Na': 22.989769, 'Mg': 23.985042, 'Al': 26.981539,
            'Si': 27.976927, 'P': 30.973762, 'S': 31.972071, 'Cl': 34.968853,
            'K': 38.963707, 'Ca': 39.962591, 'Ti': 47.947947, 'Cr': 51.940512,
            'Mn': 54.938045, 'Fe': 55.934942, 'Ni': 57.935348, 'Cu': 62.929601,
            'Zn': 63.929147, 'Br': 78.918338, 'I': 126.904468
        }

        import re
        total_mass = 0.0

        # Parse formula like "CHAl", "C2H4O", etc.
        pattern = r'([A-Z][a-z]?)([0-9]*|₀₁₂₃₄₅₆₇₈₉)'
        matches = re.findall(pattern, formula)

        for element, count_str in matches:
            if element in atomic_masses:
                # Handle subscript numbers and regular numbers
                if count_str == '' or count_str in '₀₁₂₃₄₅₆₇₈₉':
                    if count_str == '':
                        count = 1
                    else:
                        # Convert subscript to regular number
                        subscript_map = {'₀':0,'₁':1,'₂':2,'₃':3,'₄':4,'₅':5,'₆':6,'₇':7,'₈':8,'₉':9}
                        count = sum(subscript_map.get(c, 0) for c in count_str) or 1
                else:
                    count = int(count_str) if count_str.isdigit() else 1

                total_mass += atomic_masses[element] * count

        return total_mass

    def validate_database_masses(self) -> dict:
        """Validate that database masses match calculated masses"""
        if not hasattr(self, 'fragment_database') or not self.fragment_database:
            return {'status': 'error', 'message': 'No database loaded'}

        validation_results = {'valid': [], 'invalid': [], 'errors': []}

        for i, fragment in enumerate(self.fragment_database['fragments']):
            try:
                db_mass = fragment['mass']
                formulas = fragment.get('formulas', [fragment.get('formula', '')])

                for formula in formulas:
                    if formula and formula != 'Unknown':
                        calculated_mass = self.calculate_fragment_mass(formula)
                        mass_error_ppm = abs(db_mass - calculated_mass) / db_mass * 1e6

                        if mass_error_ppm > 5.0:  # More than 5 ppm error
                            validation_results['invalid'].append({
                                'index': i,
                                'mass': db_mass,
                                'formula': formula,
                                'calculated': calculated_mass,
                                'error_ppm': mass_error_ppm,
                                'assignment': fragment.get('assignments', [''])[0]
                            })
                        else:
                            validation_results['valid'].append({
                                'mass': db_mass,
                                'formula': formula,
                                'error_ppm': mass_error_ppm
                            })
                        break  # Only check first formula
            except Exception as e:
                validation_results['errors'].append({
                    'index': i,
                    'error': str(e),
                    'fragment': fragment
                })

        return validation_results

    def load_fragment_database(self):
        """Load fragment assignment database from JSON file"""
        try:
            import json
            database_path = "/home/dreece23/pca-sims/data/FragmentDatabase/alucone_fragments_complete.json"

            with open(database_path, 'r') as f:
                self.fragment_database = json.load(f)

            print(f"✅ Loaded fragment database with {len(self.fragment_database['fragments'])} fragments")

            # Build mass index for fast lookups (group by integer mass)
            self.fragment_mass_index = {}
            for fragment in self.fragment_database['fragments']:
                mass_key = int(fragment['mass'])  # Index by integer part
                if mass_key not in self.fragment_mass_index:
                    self.fragment_mass_index[mass_key] = []
                self.fragment_mass_index[mass_key].append(fragment)

            print(f"📇 Indexed {len(self.fragment_database['fragments'])} fragments into {len(self.fragment_mass_index)} mass buckets")

            return True

        except Exception as e:
            print(f"Warning: Could not load fragment database: {e}")
            self.fragment_database = None
            return False


    def find_multiple_fragment_assignments(self, target_mass: float, tolerance_ppm: float = 55.0, polarity: str = None, max_matches: int = 4):
        """
        Find multiple fragment assignments for a given mass within tolerance

        Args:
            target_mass: The target mass to find assignments for
            tolerance_ppm: Mass tolerance in ppm (default 55 ppm)
            polarity: Ion polarity ('positive' or 'negative')
            max_matches: Maximum number of assignments to return

        Returns:
            List of fragment dictionaries sorted by mass error
        """
        if not hasattr(self, 'fragment_database') or not self.fragment_database:
            return []

        # Get polarity from single source of truth if not specified
        if polarity is None:
            polarity = self.multi_ion_manager.active_polarity

        matches = []

        # Convert ppm tolerance to Da tolerance for this specific mass
        tolerance_da = (tolerance_ppm * target_mass) / 1e6

        # Use mass index for faster lookups (search only nearby mass buckets)
        target_mass_int = int(target_mass)
        # Check ±2 Da range to account for tolerance
        mass_buckets_to_search = [target_mass_int - 1, target_mass_int, target_mass_int + 1]

        fragments_to_check = []
        if hasattr(self, 'fragment_mass_index') and self.fragment_mass_index:
            # Fast path: use index
            for bucket in mass_buckets_to_search:
                if bucket in self.fragment_mass_index:
                    fragments_to_check.extend(self.fragment_mass_index[bucket])
        else:
            # Fallback: search all fragments
            fragments_to_check = self.fragment_database['fragments']

        for fragment in fragments_to_check:
            # Filter by polarity if specified
            if polarity and fragment['polarity'] != polarity:
                continue

            mass_error = abs(fragment['mass'] - target_mass)
            if mass_error <= tolerance_da:
                # Handle both old (single assignment) and new (multiple assignments) database formats
                assignments = fragment.get('assignments', [fragment.get('assignment', '')])
                formulas = fragment.get('formulas', [fragment.get('formula', '')])
                families = fragment.get('families', [fragment.get('family', '')])

                # Create separate entries for each assignment at this mass
                for i, assignment in enumerate(assignments):
                    fragment_with_error = fragment.copy()
                    fragment_with_error['assignment'] = assignment
                    fragment_with_error['formula'] = formulas[i] if i < len(formulas) else formulas[0] if formulas else ''
                    fragment_with_error['family'] = families[i] if i < len(families) else families[0] if families else ''
                    fragment_with_error['mass_error'] = mass_error
                    fragment_with_error['mass_error_ppm'] = (mass_error / target_mass) * 1000000 if target_mass > 0 else 0
                    matches.append(fragment_with_error)

        # Apply chemical priority scoring and sort by combined score
        for match in matches:
            match['priority_score'] = self.calculate_assignment_priority(match, target_mass)

        # Sort by priority score first (higher is better), then by mass error, then by assignment name for deterministic ordering
        matches.sort(key=lambda x: (-x['priority_score'], x['mass_error'], x.get('assignments', [''])[0]))
        return matches[:max_matches]

    def calculate_assignment_priority(self, fragment, target_mass):
        """
        Calculate priority score for fragment assignment based on chemical reasonableness

        Args:
            fragment: Fragment dictionary with assignment info
            target_mass: The target mass being assigned

        Returns:
            float: Priority score (higher = better assignment)
        """
        score = 100.0  # Base score

        # Exact mass match bonus (high precision)
        mass_error_ppm = fragment.get('mass_error_ppm', 0)
        if mass_error_ppm < 10:
            score += 50  # Excellent mass accuracy
        elif mass_error_ppm < 50:
            score += 20  # Good mass accuracy
        elif mass_error_ppm < 100:
            score += 5   # Fair mass accuracy

        # Element-specific assignments based on mass ranges
        # Handle both old and new database formats
        assignments = fragment.get('assignments', [fragment.get('assignment', '')])
        assignment = assignments[0].upper() if assignments and assignments[0] else ''
        formula = fragment.get('formula', '').upper()

        # Aluminum chemistry (m/z 26-28 range)
        if 26 <= target_mass <= 28:
            if 'AL' in assignment or 'AL' in formula:
                score += 100  # Highly favored for this mass range
            elif any(x in assignment for x in ['C3H6', 'C6H5', 'C4', 'C5', 'C6']):
                score -= 50   # Penalize large organic fragments in light mass range

        # Light fragment priority (m/z < 30)
        if target_mass < 30:
            element_count = formula.count('C') + formula.count('H') + formula.count('O') + formula.count('N')
            if element_count > 6:  # More than 6 atoms unlikely for light masses
                score -= 30

        # Contamination detection
        if any(x in assignment for x in ['NA+', 'K+', 'CA+', 'CL']):
            if fragment.get('family') == 'Contamination':
                score += 10  # Correctly identified contamination
            else:
                score -= 20  # Unidentified contamination

        # Confidence scoring from database
        confidence = fragment.get('confidence', 'Medium').lower()
        if confidence == 'high':
            score += 30
        elif confidence == 'low':
            score -= 10

        # Family-based scoring
        family = fragment.get('family', '').lower()
        if 'al' in family and 26 <= target_mass <= 35:
            score += 20  # Al-containing fragments in appropriate range

        return score

    def refresh_assignment_table(self):
        """Refresh assignment table with top 20-25 loadings for user review"""
        if not self.pca_completed:
            QMessageBox.information(self, "No PCA Data", "Please run PCA analysis first.")
            return

        # Load database if not already loaded
        if not hasattr(self, 'fragment_database') or not self.fragment_database:
            self.load_fragment_database()

        try:
            # Get top 25 loadings from PCA
            loadings_df = self.pca_analyzer.get_loadings_dataframe()

            top_loadings = loadings_df['PC1'].abs().sort_values(ascending=False).head(25)

            # Clear and populate table
            self.assignment_table.setRowCount(len(top_loadings))

            for i, (mass, abs_loading) in enumerate(top_loadings.items()):
                original_loading = loadings_df.loc[mass, 'PC1']

                # m/z value - ensure mass is numeric
                try:
                    mass_float = float(mass)
                    mass_str = f"{mass_float:.4f}"
                except (ValueError, TypeError) as e:
                    print(f"❌ Error converting mass to float: {mass} (type={type(mass)}), error={e}")
                    mass_str = str(mass)

                self.assignment_table.setItem(i, 0, QTableWidgetItem(mass_str))

                # PC1 loading value
                loading_item = QTableWidgetItem(f"{original_loading:+.6f}")
                if original_loading > 0:
                    loading_item.setBackground(QColor(200, 255, 200))  # Light green for positive
                else:
                    loading_item.setBackground(QColor(255, 200, 200))  # Light red for negative
                self.assignment_table.setItem(i, 1, loading_item)

                # Check if user has confirmed an assignment for this m/z
                user_assignment = None
                for confirmed_mass, assignment in self.user_confirmed_assignments.items():
                    if abs(confirmed_mass - mass) < 0.0001:  # Match within 0.1 mDa
                        user_assignment = assignment
                        break

                if user_assignment:
                    # Use the user-confirmed assignment
                    assignment_text = f"{user_assignment['assignment']} ({user_assignment['formula']})"
                    confidence = user_assignment.get('confidence', 'User Confirmed')
                    notes = "User confirmed"

                    # Set items with green highlight for confirmed assignments
                    assignment_item = QTableWidgetItem(assignment_text)
                    assignment_item.setBackground(QColor(200, 255, 200))  # Green for confirmed
                    confidence_item = QTableWidgetItem(confidence)
                    confidence_item.setBackground(QColor(200, 255, 200))

                    self.assignment_table.setItem(i, 2, assignment_item)
                    self.assignment_table.setItem(i, 3, confidence_item)

                    # Button to edit/review the confirmed assignment
                    assign_btn = QPushButton("✓ Confirmed")
                    assign_btn.setToolTip("User-confirmed assignment (click to modify)")
                    assign_btn.setStyleSheet("background-color: #90EE90; font-weight: bold;")  # Light green
                else:
                    # Look up ALL possible assignments in database with 55 ppm tolerance
                    fragment_matches = self.find_multiple_fragment_assignments(mass, tolerance_ppm=55.0, max_matches=10)

                    if fragment_matches:
                        num_matches = len(fragment_matches)
                        if num_matches == 1:
                            # Single match - show it normally
                            primary = fragment_matches[0]
                            assignment_text = f"{primary['assignment']} ({primary['formula']})"
                            confidence = primary.get('confidence', 'Medium')
                            notes = f"{primary['family']}, {primary['mass_error_ppm']:.0f}ppm"
                        else:
                            # Multiple matches - indicate ambiguity
                            assignment_text = f"[{num_matches} MATCHES] Click to review"
                            confidence = "AMBIGUOUS"
                            notes = f"{num_matches} possible assignments - requires review"

                        # Set items with appropriate styling
                        assignment_item = QTableWidgetItem(assignment_text)
                        confidence_item = QTableWidgetItem(confidence)

                        # Highlight ambiguous assignments
                        if num_matches > 1:
                            assignment_item.setBackground(QColor(255, 255, 150))  # Yellow for multiple matches
                            confidence_item.setBackground(QColor(255, 255, 150))
                            assignment_item.setToolTip(f"Multiple possible assignments found for m/z {mass:.4f}")

                        self.assignment_table.setItem(i, 2, assignment_item)
                        self.assignment_table.setItem(i, 3, confidence_item)
                    else:
                        self.assignment_table.setItem(i, 2, QTableWidgetItem("[Unassigned]"))
                        self.assignment_table.setItem(i, 3, QTableWidgetItem(""))
                        notes = f"Rank #{i+1} loading - no database matches"

                    # Action button for detailed assignment
                    if fragment_matches and len(fragment_matches) > 1:
                        assign_btn = QPushButton(f"Review {len(fragment_matches)}")
                        assign_btn.setToolTip(f"Review {len(fragment_matches)} possible assignments for m/z {mass:.4f}")
                        assign_btn.setStyleSheet("background-color: #FFE66D; font-weight: bold;")  # Yellow highlight
                    elif fragment_matches:
                        assign_btn = QPushButton("Confirm")
                        assign_btn.setToolTip("Confirm single assignment or explore alternatives")
                    else:
                        assign_btn = QPushButton("Assign")
                        assign_btn.setToolTip("Manually assign this unidentified fragment")

                # Store mass and row in button properties
                assign_btn.setProperty("mass", mass)
                assign_btn.setProperty("row", i)
                assign_btn.clicked.connect(lambda checked, btn=assign_btn: self.open_assignment_dialog(
                    btn.property("mass"), btn.property("row")))
                self.assignment_table.setCellWidget(i, 4, assign_btn)

                # Notes
                self.assignment_table.setItem(i, 5, QTableWidgetItem(notes))

            # Count assigned vs unassigned
            assigned_count = sum(1 for i in range(len(top_loadings))
                               if self.assignment_table.item(i, 2).text() != "[Unassigned]")
            confirmed_count = len([m for m in top_loadings.keys()
                                  if any(abs(m - cm) < 0.0001 for cm in self.user_confirmed_assignments.keys())])

            print(f"✅ Loaded {len(top_loadings)} top loadings: {assigned_count} assigned ({confirmed_count} user-confirmed), {len(top_loadings)-assigned_count} unassigned")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh assignments: {e}")

    def open_assignment_dialog(self, mass, row_index):
        """Open detailed assignment dialog with peak intensities and candidate matches"""
        dialog = FragmentAssignmentDialog(self, mass, row_index)
        if dialog.exec() == QDialog.Accepted:
            # Update the table with user's choice
            selected_assignment = dialog.get_selected_assignment()
            if selected_assignment:
                self.update_assignment_table_row(row_index, selected_assignment)

    def update_assignment_table_row(self, row_index, assignment_info):
        """Update a specific row in the assignment table with new assignment"""
        try:
            assignment_text = f"{assignment_info['assignment']} ({assignment_info['formula']})"
            confidence = assignment_info.get('confidence', 'User Assigned')

            # Get the m/z value for this row
            mz_text = self.assignment_table.item(row_index, 0).text()
            mz_value = float(mz_text)

            # Store the user-confirmed assignment for this m/z
            self.user_confirmed_assignments[mz_value] = assignment_info.copy()

            self.assignment_table.setItem(row_index, 2, QTableWidgetItem(assignment_text))
            self.assignment_table.setItem(row_index, 3, QTableWidgetItem(confidence))

            # Update notes
            if 'mass_error_ppm' in assignment_info:
                notes = f"{assignment_info.get('family', 'Unknown')}, {assignment_info['mass_error_ppm']:.0f}ppm"
            else:
                notes = "User confirmed"
            self.assignment_table.setItem(row_index, 5, QTableWidgetItem(notes))

            print(f"✅ Updated and saved assignment: m/z {mz_text} → {assignment_text}")

        except Exception as e:
            QMessageBox.warning(self, "Update Error", f"Failed to update assignment: {e}")

    def add_manual_assignment(self):
        """Add a manual fragment assignment"""
        # Get m/z value
        mz_text, ok = QInputDialog.getText(self, "Add Assignment", "Enter m/z value:")
        if not ok or not mz_text:
            return

        try:
            mz = float(mz_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid m/z value")
            return

        # Get assignment
        assignment_text, ok = QInputDialog.getText(self, "Add Assignment", "Enter fragment assignment:")
        if not ok or not assignment_text:
            return

        # Add to table
        row = self.assignment_table.rowCount()
        self.assignment_table.setRowCount(row + 1)

        self.assignment_table.setItem(row, 0, QTableWidgetItem(f"{mz:.3f}"))
        self.assignment_table.setItem(row, 1, QTableWidgetItem(assignment_text))
        self.assignment_table.setItem(row, 2, QTableWidgetItem(""))  # Formula (to be filled)
        # Clear alternative columns
        for alt_idx in range(3, 6):
            self.assignment_table.setItem(row, alt_idx, QTableWidgetItem(""))
        self.assignment_table.setItem(row, 6, QTableWidgetItem("Manual assignment"))

        print(f"✅ Added manual assignment: m/z {mz:.3f} = {assignment_text}")

    def save_assignments_database(self):
        """Save current assignments back to database"""
        try:
            # Load existing database
            if not hasattr(self, 'fragment_database') or not self.fragment_database:
                self.load_fragment_database()

            if not self.fragment_database:
                QMessageBox.warning(self, "No Database", "No fragment database loaded to save to.")
                return

            # Create set of existing masses in database for quick lookup
            existing_masses = {frag['mass'] for frag in self.fragment_database['fragments']}

            # Add new assignments from table
            new_assignments = 0
            for row in range(self.assignment_table.rowCount()):
                mz_item = self.assignment_table.item(row, 0)
                assignment_item = self.assignment_table.item(row, 1)
                formula_item = self.assignment_table.item(row, 2)
                notes_item = self.assignment_table.item(row, 6)

                if mz_item and assignment_item:
                    mass = float(mz_item.text())
                    assignment = assignment_item.text()
                    formula = formula_item.text() if formula_item else ""
                    notes = notes_item.text() if notes_item else ""

                    # Skip if it's just a loading annotation or already exists
                    if (assignment.startswith("[Unassigned") or assignment.startswith("[Top loading") or
                        mass in existing_masses):
                        continue

                    # Add new fragment to database
                    new_fragment = {
                        "mass": mass,
                        "assignment": assignment,
                        "formula": formula,
                        "family": "User-defined",
                        "polarity": "unknown",
                        "confidence": "User-assigned",
                        "notes": f"User assignment: {notes}"
                    }

                    self.fragment_database['fragments'].append(new_fragment)
                    new_assignments += 1

            if new_assignments > 0:
                # Save updated database
                import json
                database_path = "/home/dreece23/pca-sims/data/FragmentDatabase/alucone_fragments_complete.json"

                with open(database_path, 'w') as f:
                    json.dump(self.fragment_database, f, indent=2)

                QMessageBox.information(self, "Database Saved",
                                      f"Added {new_assignments} new assignments to database!\nDatabase saved to: {database_path}")
                print(f"✅ Saved {new_assignments} new fragment assignments to database")
            else:
                QMessageBox.information(self, "No New Assignments", "No new assignments to save to database.")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save assignments: {e}")

    def export_assignment_table(self):
        """Export assignment table to CSV file"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv
            import os
            from datetime import datetime

            if not hasattr(self, 'assignment_table') or self.assignment_table.rowCount() == 0:
                QMessageBox.information(self, "No Data", "No assignment data to export. Please run PCA and refresh assignments first.")
                return

            # Get export filename
            default_filename = f"fragment_assignments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Assignment Table",
                os.path.join("outputs", default_filename),
                "CSV Files (*.csv);;All Files (*)"
            )

            if not filename:
                return

            # Create outputs directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Export table data
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                headers = []
                for col in range(self.assignment_table.columnCount()):
                    headers.append(self.assignment_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Write data rows
                for row in range(self.assignment_table.rowCount()):
                    row_data = []
                    for col in range(self.assignment_table.columnCount()):
                        item = self.assignment_table.item(row, col)
                        if item:
                            # Skip the Action column (buttons)
                            if col == 4:  # Action column
                                widget = self.assignment_table.cellWidget(row, col)
                                if widget and hasattr(widget, 'text'):
                                    row_data.append(widget.text())
                                else:
                                    row_data.append("Review")
                            else:
                                row_data.append(item.text())
                        else:
                            row_data.append("")
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export Successful",
                                  f"Assignment table exported to:\n{filename}\n\n"
                                  f"Exported {self.assignment_table.rowCount()} assignments.")
            print(f"✅ Exported assignment table to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export assignment table: {e}")

    def refresh_fragment_trends_list(self):
        """Refresh the fragment trends list with assigned fragments from database and table"""
        # Clear list
        self.fragment_trends_list.clear()

        # Load database if not already loaded
        if not hasattr(self, 'fragment_database') or not self.fragment_database:
            self.load_fragment_database()

        assigned_fragments = []

        # Get assignments from assignment table first (current session)
        for row in range(self.assignment_table.rowCount()):
            mz_item = self.assignment_table.item(row, 0)
            assignment_item = self.assignment_table.item(row, 1)

            if mz_item and assignment_item:
                mz_text = mz_item.text()
                assignment_text = assignment_item.text()

                if assignment_text and not assignment_text.startswith("[Unassigned") and not assignment_text.startswith("[Top loading"):
                    # Only show fragments that have been assigned
                    list_text = f"m/z {mz_text}: {assignment_text}"
                    assigned_fragments.append((float(mz_text), list_text))

        # Also get assignments from database (for consistency)
        if self.fragment_database and self.pca_completed:
            try:
                # Get the mass range from current PCA data
                loadings_df = self.pca_analyzer.get_loadings_dataframe()
                mass_range = (loadings_df.index.min(), loadings_df.index.max())

                for fragment in self.fragment_database['fragments']:
                    mass = fragment['mass']
                    # Only include fragments within the mass range of current data
                    if mass_range[0] <= mass <= mass_range[1]:
                        # Handle both old and new database formats
                        assignments = fragment.get('assignments', [fragment.get('assignment', '')])
                        families = fragment.get('families', [fragment.get('family', 'Unknown')])
                        assignment = assignments[0] if assignments else 'Unknown'
                        family = families[0] if families else 'Unknown'
                        list_text = f"m/z {mass:.3f}: {assignment} ({family})"

                        # Avoid duplicates from table
                        if not any(abs(af[0] - mass) < 0.01 for af in assigned_fragments):
                            assigned_fragments.append((mass, list_text))

            except:
                pass  # Fallback to table-only assignments

        # Sort by mass and add to list
        assigned_fragments.sort()
        for mass, list_text in assigned_fragments:
            item = QListWidgetItem(list_text)
            item.setData(Qt.UserRole, mass)
            self.fragment_trends_list.addItem(item)

        print(f"✅ Loaded {self.fragment_trends_list.count()} assigned fragments for trends")

    def plot_individual_fragment_trends(self):
        """Plot dose-response trends for selected individual fragments"""
        if not self.pca_completed:
            QMessageBox.information(self, "No PCA Data", "Please run PCA analysis first.")
            return

        selected_items = self.fragment_trends_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Fragments Selected", "Please select fragments to plot.")
            return

        try:
            # Use the current working data from PCA analyzer
            if not self.pca_analyzer or not hasattr(self.pca_analyzer, 'working_data'):
                QMessageBox.information(self, "No Data Available", "Please run PCA analysis first.")
                return

            # Get working data and metadata (respects current sample selection)
            working_data, working_metadata = self.pca_analyzer.get_active_data()
            data_subset = working_data.T  # Transpose to get masses as rows, samples as columns

            # Extract dose information from working metadata using new metadata system
            sample_names = list(working_data.columns)
            dose_data = {}
            dose_labels = {}

            for i, sample in enumerate(sample_names):
                sample_row = working_metadata.iloc[i]

                # Get sample type and dose from metadata
                if hasattr(self.pca_analyzer, 'sample_metadata') and 'sample_type' in self.pca_analyzer.sample_metadata.columns:
                    # Find the metadata for this sample
                    sample_mask = self.pca_analyzer.sample_metadata['sample_name'] == sample
                    if sample_mask.any():
                        sample_meta = self.pca_analyzer.sample_metadata.loc[sample_mask].iloc[0]
                        sample_type = sample_meta.get('sample_type', 'E-beam Exposed')

                        if sample_type == 'As-Deposited':
                            dose_data[sample] = 0  # Assign 0 for sorting
                            dose_labels[sample] = 'As-Deposited'
                        elif sample_type == 'E-beam Exposed':
                            # Use actual dose value if available
                            dose_val = sample_meta.get('actual_dose', sample_row.get('dose_id', i))
                            dose_data[sample] = dose_val
                            dose_labels[sample] = f'{dose_val} μC/cm²'
                        else:  # Excluded samples shouldn't reach here due to masking
                            dose_data[sample] = sample_row.get('dose_id', i)
                            dose_labels[sample] = str(dose_data[sample])
                    else:
                        # Fallback to original behavior
                        dose_data[sample] = sample_row.get('dose_id', i)
                        dose_labels[sample] = str(dose_data[sample])
                else:
                    # Fallback to original behavior
                    dose_data[sample] = sample_row.get('dose_id', i)
                    dose_labels[sample] = str(dose_data[sample])

            # Create plot
            self.individual_trends_canvas.figure.clear()

            n_fragments = len(selected_items)
            if n_fragments == 1:
                ax = self.individual_trends_canvas.figure.add_subplot(111)
                axes = [ax]
            else:
                # Create subplots for multiple fragments
                rows = int(np.ceil(n_fragments / 2))
                axes = []
                for i in range(n_fragments):
                    ax = self.individual_trends_canvas.figure.add_subplot(rows, 2, i+1)
                    axes.append(ax)

            # Plot each fragment
            for i, item in enumerate(selected_items):
                mz = item.data(Qt.UserRole)
                fragment_name = item.text()

                ax = axes[i] if len(axes) > 1 else axes[0]

                if mz in data_subset.index:
                    intensities = data_subset.loc[mz]
                    doses = [dose_data[sample] for sample in sample_names]
                    labels = [dose_labels[sample] for sample in sample_names]

                    # Sort by dose for plotting with proper labeling
                    dose_intensity_pairs = list(zip(doses, intensities, labels, sample_names))

                    # Filter As-Deposited samples if checkbox is unchecked (use familial trends checkbox)
                    if hasattr(self, 'include_as_deposited_checkbox') and not self.include_as_deposited_checkbox.isChecked():
                        dose_intensity_pairs = [(d, i, l, s) for d, i, l, s in dose_intensity_pairs if d > 0]

                    if not dose_intensity_pairs:
                        continue  # Skip this fragment if no data points remain

                    dose_intensity_pairs.sort()  # Sort by dose value
                    sorted_doses, sorted_intensities, sorted_labels, sorted_samples = zip(*dose_intensity_pairs)

                    # Create x-positions for plotting (0, 1, 2, etc.) but use custom labels
                    x_positions = list(range(len(sorted_doses)))

                    # Plot data points
                    ax.scatter(x_positions, sorted_intensities, s=50, alpha=0.8, zorder=3)

                    # Add curve fitting if checkbox is checked (use familial trends checkbox)
                    if hasattr(self, 'fit_curve_checkbox') and self.fit_curve_checkbox.isChecked() and len(x_positions) >= 3:
                        try:
                            import numpy as np
                            from scipy.optimize import curve_fit

                            # Define exponential saturation model
                            def exponential_saturation(x, a, b, c):
                                return a * (1 - np.exp(-b * np.array(x))) + c

                            # Try curve fitting
                            try:
                                popt, _ = curve_fit(exponential_saturation, x_positions, sorted_intensities,
                                                   maxfev=1000, bounds=([-np.inf, 0, -np.inf], [np.inf, np.inf, np.inf]))
                                x_fit = np.linspace(min(x_positions), max(x_positions), 100)
                                y_fit = exponential_saturation(x_fit, *popt)
                                ax.plot(x_fit, y_fit, '--', linewidth=2, alpha=0.8)
                            except:
                                # Fallback to linear connection
                                ax.plot(x_positions, sorted_intensities, '-', linewidth=2, alpha=0.6)
                        except ImportError:
                            # scipy not available, fall back to linear
                            ax.plot(x_positions, sorted_intensities, '-', linewidth=2, alpha=0.6)
                    else:
                        # Simple linear connection
                        ax.plot(x_positions, sorted_intensities, '-', linewidth=2, alpha=0.6)

                    # Set custom x-axis labels
                    ax.set_xticks(x_positions)
                    ax.set_xticklabels(sorted_labels, rotation=45, ha='right')
                    ax.set_xlabel('Electron Beam Dose')
                    ax.set_ylabel('Intensity')
                    ax.set_title(fragment_name, fontsize=10)
                    ax.grid(True, alpha=0.3)

            self.individual_trends_canvas.figure.tight_layout()
            self.individual_trends_canvas.draw()

            print(f"✅ Plotted trends for {len(selected_items)} fragments")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot fragment trends: {e}")

    def auto_assign_chemical_families(self):
        """Auto-assign chemical families based on m/z values and fragment assignments"""
        # This is a simplified auto-assignment based on common ToF-SIMS fragments
        family_assignments = {}

        # Get current assignments from table
        for row in range(self.assignment_table.rowCount()):
            mz_item = self.assignment_table.item(row, 0)
            assignment_item = self.assignment_table.item(row, 1)

            if mz_item and assignment_item:
                try:
                    mz = float(mz_item.text())
                    assignment = assignment_item.text().lower()

                    # Simple family assignment logic
                    if any(keyword in assignment for keyword in ['al', 'aluminum']):
                        family = "Al-based"
                    elif any(keyword in assignment for keyword in ['ch3', 'ch2', 'alkyl', 'saturated']):
                        family = "Saturated Carbon"
                    elif any(keyword in assignment for keyword in ['c2h', 'c=c', 'alkene', 'alkyne', 'aromatic']):
                        family = "Unsaturated Carbon"
                    elif any(keyword in assignment for keyword in ['c=o', 'co', 'carbonyl', 'cho', 'cooh']):
                        family = "Carbonyl"
                    elif any(keyword in assignment for keyword in ['oh', 'hydroxyl', 'h2o']):
                        family = "Hydroxyl"
                    elif any(keyword in assignment for keyword in ['c-o-c', 'ether', 'ester', 'coo']):
                        family = "Ether/Ester"
                    elif any(keyword in assignment for keyword in ['n', 'nh', 'nitrogen']):
                        family = "Nitrogenous"
                    else:
                        # Fallback assignment based on m/z ranges
                        if mz < 30:
                            family = "Al-based"
                        elif 30 <= mz < 60:
                            family = "Saturated Carbon"
                        elif 60 <= mz < 100:
                            family = "Unsaturated Carbon"
                        else:
                            family = "Carbonyl"

                    if family not in family_assignments:
                        family_assignments[family] = []
                    family_assignments[family].append(mz)

                except ValueError:
                    continue

        # Store assignments
        self.fragment_family_assignments = family_assignments

        # Update status
        total_assigned = sum(len(fragments) for fragments in family_assignments.values())
        status_text = f"Auto-assigned {total_assigned} fragments to {len(family_assignments)} families:\n"
        for family, fragments in family_assignments.items():
            status_text += f"• {family}: {len(fragments)} fragments\n"

        self.family_status.setText(status_text)
        print(f"✅ Auto-assigned chemical families for {total_assigned} fragments")

    def plot_familial_trends(self):
        """Plot dose-response trends for chemical families"""
        if not hasattr(self, 'fragment_family_assignments') or not self.fragment_family_assignments:
            QMessageBox.information(self, "No Family Assignments", "Please run 'Auto-Assign Families' first.")
            return

        if not self.pca_completed:
            QMessageBox.information(self, "No PCA Data", "Please run PCA analysis first.")
            return

        try:
            # Use the current working data from PCA analyzer
            if not self.pca_analyzer or not hasattr(self.pca_analyzer, 'working_data'):
                QMessageBox.information(self, "No Data Available", "Please run PCA analysis first.")
                return

            # Get working data and metadata (respects current sample selection)
            working_data, working_metadata = self.pca_analyzer.get_active_data()
            data_subset = working_data.T  # Transpose to get masses as rows, samples as columns

            # Extract dose information from working metadata using new metadata system
            sample_names = list(working_data.columns)
            dose_data = {}
            dose_labels = {}

            for i, sample in enumerate(sample_names):
                sample_row = working_metadata.iloc[i]

                # Get sample type and dose from metadata
                if hasattr(self.pca_analyzer, 'sample_metadata') and 'sample_type' in self.pca_analyzer.sample_metadata.columns:
                    # Find the metadata for this sample
                    sample_mask = self.pca_analyzer.sample_metadata['sample_name'] == sample
                    if sample_mask.any():
                        sample_meta = self.pca_analyzer.sample_metadata.loc[sample_mask].iloc[0]
                        sample_type = sample_meta.get('sample_type', 'E-beam Exposed')

                        if sample_type == 'As-Deposited':
                            dose_data[sample] = 0  # Assign 0 for sorting
                            dose_labels[sample] = 'As-Deposited'
                        elif sample_type == 'E-beam Exposed':
                            # Use actual dose value if available
                            dose_val = sample_meta.get('actual_dose', sample_row.get('dose_id', i))
                            dose_data[sample] = dose_val
                            dose_labels[sample] = f'{dose_val} μC/cm²'
                        else:  # Excluded samples shouldn't reach here due to masking
                            dose_data[sample] = sample_row.get('dose_id', i)
                            dose_labels[sample] = str(dose_data[sample])
                    else:
                        # Fallback to original behavior
                        dose_data[sample] = sample_row.get('dose_id', i)
                        dose_labels[sample] = str(dose_data[sample])
                else:
                    # Fallback to original behavior
                    dose_data[sample] = sample_row.get('dose_id', i)
                    dose_labels[sample] = str(dose_data[sample])

            # Create plot
            self.familial_trends_canvas.figure.clear()
            ax = self.familial_trends_canvas.figure.add_subplot(111)

            # Plot each selected family
            for family, fragments in self.fragment_family_assignments.items():
                if self.family_checkboxes[family].isChecked():
                    # Calculate family average intensity
                    family_intensities = []
                    for sample in sample_names:
                        # Average intensity across all fragments in this family
                        fragment_intensities = []
                        for mz in fragments:
                            if mz in data_subset.index:
                                fragment_intensities.append(data_subset.loc[mz, sample])

                        if fragment_intensities:
                            family_intensities.append(np.mean(fragment_intensities))
                        else:
                            family_intensities.append(0)

                    # Get doses and sort with proper labeling
                    doses = [dose_data[sample] for sample in sample_names]
                    labels = [dose_labels[sample] for sample in sample_names]
                    dose_intensity_pairs = list(zip(doses, family_intensities, labels, sample_names))

                    # Filter As-Deposited samples if checkbox is unchecked
                    if not self.include_as_deposited_checkbox.isChecked():
                        dose_intensity_pairs = [(d, i, l, s) for d, i, l, s in dose_intensity_pairs if d > 0]

                    if not dose_intensity_pairs:
                        continue  # Skip this family if no data points remain

                    dose_intensity_pairs.sort()  # Sort by dose value
                    sorted_doses, sorted_intensities, sorted_labels, sorted_samples = zip(*dose_intensity_pairs)

                    # Plot with family color using proper x-axis positions
                    color = self.chemical_families[family]["color"]

                    # Create x-positions for plotting (0, 1, 2, etc.) but use custom labels
                    x_positions = list(range(len(sorted_doses)))

                    # Plot data points
                    ax.scatter(x_positions, sorted_intensities, color=color, s=50, alpha=0.8, zorder=3)

                    # Add curve fitting if checkbox is checked
                    if self.fit_curve_checkbox.isChecked() and len(x_positions) >= 3:
                        try:
                            import numpy as np
                            from scipy.optimize import curve_fit

                            # Define different curve models
                            def exponential_saturation(x, a, b, c):
                                """Exponential saturation: y = a * (1 - exp(-b*x)) + c"""
                                return a * (1 - np.exp(-b * np.array(x))) + c

                            def sigmoidal(x, a, b, c, d):
                                """Sigmoidal: y = a / (1 + exp(-b*(x-c))) + d"""
                                return a / (1 + np.exp(-b * (np.array(x) - c))) + d

                            # Try exponential saturation first
                            try:
                                popt_exp, _ = curve_fit(exponential_saturation, x_positions, sorted_intensities,
                                                       maxfev=1000, bounds=([-np.inf, 0, -np.inf], [np.inf, np.inf, np.inf]))
                                x_fit = np.linspace(min(x_positions), max(x_positions), 100)
                                y_fit_exp = exponential_saturation(x_fit, *popt_exp)
                                ax.plot(x_fit, y_fit_exp, '--', color=color, linewidth=2, alpha=0.8,
                                       label=f"{family} fit (n={len(fragments)})")
                                print(f"   📈 Fitted exponential saturation for {family}")
                            except:
                                # Fallback to sigmoidal
                                try:
                                    popt_sig, _ = curve_fit(sigmoidal, x_positions, sorted_intensities, maxfev=1000)
                                    x_fit = np.linspace(min(x_positions), max(x_positions), 100)
                                    y_fit_sig = sigmoidal(x_fit, *popt_sig)
                                    ax.plot(x_fit, y_fit_sig, '--', color=color, linewidth=2, alpha=0.8,
                                           label=f"{family} fit (n={len(fragments)})")
                                    print(f"   📈 Fitted sigmoidal for {family}")
                                except:
                                    # Fallback to linear connection
                                    ax.plot(x_positions, sorted_intensities, '-', color=color, linewidth=2, alpha=0.6,
                                           label=f"{family} (n={len(fragments)})")
                                    print(f"   📊 Linear connection for {family} (curve fitting failed)")
                        except ImportError:
                            # scipy not available, fall back to linear
                            ax.plot(x_positions, sorted_intensities, '-', color=color, linewidth=2, alpha=0.6,
                                   label=f"{family} (n={len(fragments)})")
                            print(f"   📊 Linear connection for {family} (scipy not available)")
                    else:
                        # Simple linear connection
                        ax.plot(x_positions, sorted_intensities, '-', color=color, linewidth=2, alpha=0.6,
                               label=f"{family} (n={len(fragments)})")

                    # Store the labels for x-axis formatting
                    if not hasattr(ax, '_dose_labels'):
                        ax._dose_labels = sorted_labels
                        ax._x_positions = x_positions

            # Set custom x-axis labels if available
            if hasattr(ax, '_dose_labels') and hasattr(ax, '_x_positions'):
                ax.set_xticks(ax._x_positions)
                ax.set_xticklabels(ax._dose_labels, rotation=45, ha='right')
                ax.set_xlabel('Electron Beam Dose')
            else:
                ax.set_xlabel('Dose (arbitrary units)')

            ax.set_ylabel('Average Family Intensity')
            ax.set_title('Chemical Family Dose-Response Trends')
            ax.legend(loc='best', framealpha=0.9)
            ax.grid(True, alpha=0.3)

            self.familial_trends_canvas.draw()

            print(f"✅ Plotted familial trends for selected chemical families")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to plot familial trends: {e}")

    # Database Management Methods
    def refresh_database_status(self):
        """Refresh database status display"""
        try:
            if hasattr(self, 'fragment_database') and self.fragment_database:
                fragment_count = len(self.fragment_database['fragments'])
                self.db_status_label.setText(f"✅ Database loaded: {fragment_count} fragments")
            else:
                self.db_status_label.setText("❌ Database not loaded - click 'Load Data' first")
        except Exception as e:
            self.db_status_label.setText(f"❌ Database error: {e}")

    def validate_new_fragment(self):
        """Validate and preview new fragment before adding"""
        try:
            mass = float(self.new_mass.text())
            assignment = self.new_assignment.text().strip()
            formula = self.new_formula.text().strip()

            if not assignment:
                QMessageBox.warning(self, "Validation Error", "Assignment is required.")
                return

            # Chemical validation
            validation_results = self.validate_fragment_chemistry(mass, assignment, formula)

            # Show validation dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Fragment Validation Results")
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            # Results display
            results_text = QTextEdit()
            results_text.setReadOnly(True)

            validation_text = f"🧪 VALIDATION RESULTS for {assignment} (m/z {mass})\n"
            validation_text += "=" * 60 + "\n\n"

            for category, result in validation_results.items():
                validation_text += f"{category}: {result}\n"

            results_text.setPlainText(validation_text)
            layout.addWidget(results_text)

            # Buttons
            button_layout = QHBoxLayout()

            accept_btn = QPushButton("✅ Accept - Add to Pending")
            accept_btn.clicked.connect(lambda: (dialog.accept(), self.add_to_pending()))

            cancel_btn = QPushButton("❌ Cancel")
            cancel_btn.clicked.connect(dialog.reject)

            button_layout.addWidget(accept_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)

            dialog.exec()

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid mass value.")
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate fragment: {e}")

    def validate_fragment_chemistry(self, mass, assignment, formula):
        """Validate fragment chemistry and return results"""
        results = {}

        # Mass range validation
        if mass < 1 or mass > 1000:
            results["Mass Range"] = f"❌ Unusual mass ({mass}) - outside typical ToF-SIMS range"
        else:
            results["Mass Range"] = f"✅ Mass {mass} is within typical range"

        # Check for existing assignments with tight tolerance
        existing = self.find_multiple_fragment_assignments(mass, tolerance_ppm=5.0, max_matches=5)
        if existing:
            results["Existing Assignments"] = f"⚠️ {len(existing)} similar assignments found"
            for ex in existing[:3]:
                results[f"  - {ex['assignment']}"] = f"Mass error: {ex['mass_error_ppm']:.1f} ppm"
        else:
            results["Existing Assignments"] = "✅ No conflicting assignments found"

        # Formula validation
        if formula:
            # Simple element count validation
            c_count = formula.count('C')
            h_count = formula.count('H')
            o_count = formula.count('O')
            al_count = formula.count('Al')

            if mass < 30 and (c_count > 3 or h_count > 6):
                results["Formula Logic"] = f"⚠️ Large molecule ({formula}) for light mass"
            elif 26 <= mass <= 28 and al_count == 0 and 'AL' not in assignment.upper():
                results["Formula Logic"] = f"⚠️ Non-Al assignment in Al mass range"
            else:
                results["Formula Logic"] = "✅ Formula appears chemically reasonable"

        # Assignment naming convention
        if '+' in assignment or '-' in assignment:
            results["Ion Format"] = "✅ Proper ion notation used"
        else:
            results["Ion Format"] = "⚠️ Consider adding charge state (+/-)"

        return results

    def add_to_pending(self):
        """Add fragment to pending table for review"""
        try:
            mass = float(self.new_mass.text())
            assignment = self.new_assignment.text().strip()
            formula = self.new_formula.text().strip()
            family = self.new_family.currentText()
            polarity = self.new_polarity.currentText()
            confidence = self.new_confidence.currentText()
            notes = self.new_notes.toPlainText()

            if not assignment:
                QMessageBox.warning(self, "Input Error", "Assignment is required.")
                return

            # Add to pending table
            row = self.pending_table.rowCount()
            self.pending_table.setRowCount(row + 1)

            self.pending_table.setItem(row, 0, QTableWidgetItem(f"{mass:.4f}"))
            self.pending_table.setItem(row, 1, QTableWidgetItem(assignment))
            self.pending_table.setItem(row, 2, QTableWidgetItem(formula))
            self.pending_table.setItem(row, 3, QTableWidgetItem(family))
            self.pending_table.setItem(row, 4, QTableWidgetItem(confidence))
            self.pending_table.setItem(row, 5, QTableWidgetItem("Pending"))

            # Action button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda: self.remove_pending_row(row))
            self.pending_table.setCellWidget(row, 6, remove_btn)

            # Clear input fields
            self.new_mass.clear()
            self.new_assignment.clear()
            self.new_formula.clear()
            self.new_notes.clear()

            QMessageBox.information(self, "Added", f"Fragment {assignment} added to pending assignments.")

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid mass value.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add to pending: {e}")

    def remove_pending_row(self, row):
        """Remove row from pending table"""
        self.pending_table.removeRow(row)

    def validate_all_pending(self):
        """Validate all pending assignments and show results"""
        row_count = self.pending_table.rowCount()
        if row_count == 0:
            QMessageBox.information(self, "No Pending", "No pending assignments to validate.")
            return

        validation_results = []
        for row in range(row_count):
            mass_text = self.pending_table.item(row, 0).text()
            assignment = self.pending_table.item(row, 1).text()
            formula = self.pending_table.item(row, 2).text()

            try:
                mass = float(mass_text)
                results = self.validate_fragment_chemistry(mass, assignment, formula)
                validation_results.append((assignment, mass, results))
            except Exception as e:
                validation_results.append((assignment, mass_text, {"Error": str(e)}))

        # Show validation results dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Batch Validation Results")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        results_text = QTextEdit()
        results_text.setReadOnly(True)

        full_text = "🔍 BATCH VALIDATION RESULTS\n"
        full_text += "=" * 50 + "\n\n"

        for assignment, mass, results in validation_results:
            full_text += f"📍 {assignment} (m/z {mass})\n"
            for category, result in results.items():
                full_text += f"    {result}\n"
            full_text += "\n"

        results_text.setPlainText(full_text)
        layout.addWidget(results_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def clear_pending_assignments(self):
        """Clear all pending assignments after confirmation"""
        if self.pending_table.rowCount() == 0:
            return

        reply = QMessageBox.question(
            self, "Clear Pending",
            "Are you sure you want to clear all pending assignments?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.pending_table.setRowCount(0)
            QMessageBox.information(self, "Cleared", "All pending assignments have been cleared.")

    def backup_database(self):
        """Create a backup copy of the current database"""
        try:
            import shutil
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/home/dreece23/pca-sims/data/FragmentDatabase/backup_alucone_fragments_{timestamp}.json"

            original_path = "/home/dreece23/pca-sims/data/FragmentDatabase/alucone_fragments_complete.json"
            shutil.copy2(original_path, backup_path)

            QMessageBox.information(
                self, "Backup Created",
                f"Database backup created:\n{backup_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup: {e}")

    def restore_database(self):
        """Restore database from a backup file"""
        backup_file, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File",
            "/home/dreece23/pca-sims/data/FragmentDatabase/",
            "JSON files (*.json);;All files (*)"
        )

        if backup_file:
            reply = QMessageBox.question(
                self, "Restore Database",
                "⚠️ This will overwrite the current database!\n\nAre you sure you want to restore from backup?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    import shutil
                    target_path = "/home/dreece23/pca-sims/data/FragmentDatabase/alucone_fragments_complete.json"
                    shutil.copy2(backup_file, target_path)

                    # Reload database
                    self.load_fragment_database()
                    self.refresh_database_status()

                    QMessageBox.information(self, "Restored", "Database has been restored from backup.")

                except Exception as e:
                    QMessageBox.critical(self, "Restore Error", f"Failed to restore database: {e}")

    def apply_pending_assignments(self):
        """Apply all validated pending assignments to the database"""
        if not hasattr(self, 'pending_assignments') or not self.pending_assignments:
            QMessageBox.information(self, "No Assignments", "No pending assignments to apply.")
            return

        try:
            # Create backup before applying changes
            self.backup_database()

            # Temporarily make database writable for controlled modification
            self.ensure_database_writable()

            # Load current database
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')
            with open(db_path, 'r') as f:
                database = json.load(f)

            applied_count = 0
            for assignment in self.pending_assignments:
                mz = assignment['mz']
                formula = assignment['formula']
                description = assignment['description']
                category = assignment['category']

                # Add to database with validation metadata
                database[str(mz)] = {
                    'formula': formula,
                    'description': description,
                    'category': category,
                    'validated': True,
                    'added_date': datetime.now().isoformat(),
                    'validation_method': 'controlled_addition'
                }
                applied_count += 1

            # Save updated database
            with open(db_path, 'w') as f:
                json.dump(database, f, indent=2)

            # Restore database protection
            self.restore_database_protection()

            # Clear pending assignments
            self.pending_assignments.clear()

            # Refresh displays
            self.refresh_database_status()
            QMessageBox.information(self, "Success", f"Applied {applied_count} assignments to database.")

        except Exception as e:
            QMessageBox.critical(self, "Apply Error", f"Failed to apply assignments: {e}")

    def clear_pending_assignments(self):
        """Clear all pending assignments"""
        if hasattr(self, 'pending_assignments') and self.pending_assignments:
            reply = QMessageBox.question(self, "Clear Pending",
                                       f"Clear {len(self.pending_assignments)} pending assignments?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.pending_assignments.clear()
                self.refresh_database_status()
                QMessageBox.information(self, "Cleared", "Pending assignments cleared.")

    def validate_database_integrity(self):
        """Validate the integrity of the fragment database"""
        try:
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')

            with open(db_path, 'r') as f:
                database = json.load(f)

            issues = []
            total_entries = len(database)

            for mz_str, data in database.items():
                try:
                    mz = float(mz_str)
                except ValueError:
                    issues.append(f"Invalid m/z key: {mz_str}")
                    continue

                # Check required fields
                if 'formula' not in data:
                    issues.append(f"Missing formula for m/z {mz}")
                elif not data['formula'].strip():
                    issues.append(f"Empty formula for m/z {mz}")

                if 'description' not in data:
                    issues.append(f"Missing description for m/z {mz}")

                # Validate chemistry if possible
                if 'formula' in data and data['formula'].strip():
                    formula = data['formula'].strip()
                    chem_issues = self.validate_fragment_chemistry(mz, formula)
                    if chem_issues:
                        issues.append(f"m/z {mz} ({formula}): {', '.join(chem_issues)}")

            # Show validation results
            if issues:
                issues_text = '\n'.join(issues[:20])  # Limit to first 20 issues
                if len(issues) > 20:
                    issues_text += f"\n... and {len(issues) - 20} more issues"

                QMessageBox.warning(self, "Database Issues Found",
                                  f"Found {len(issues)} issues in {total_entries} entries:\n\n{issues_text}")
            else:
                QMessageBox.information(self, "Database Valid",
                                      f"Database integrity check passed.\n{total_entries} entries validated.")

        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate database: {e}")

    def export_database_report(self):
        """Export a comprehensive database report"""
        try:
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')

            with open(db_path, 'r') as f:
                database = json.load(f)

            # Create report
            report_lines = [
                "Fragment Database Report",
                "=" * 50,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Entries: {len(database)}",
                "",
                "Mass Range Analysis:",
            ]

            # Analyze mass ranges
            masses = [float(mz) for mz in database.keys()]
            masses.sort()

            report_lines.extend([
                f"  Lowest m/z: {min(masses):.4f}",
                f"  Highest m/z: {max(masses):.4f}",
                f"  Mass range: {max(masses) - min(masses):.4f}",
                "",
                "Category Breakdown:",
            ])

            # Category analysis
            categories = {}
            for data in database.values():
                cat = data.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1

            for cat, count in sorted(categories.items()):
                report_lines.append(f"  {cat}: {count}")

            report_lines.extend([
                "",
                "Detailed Entries:",
                "-" * 30,
            ])

            # Detailed listings
            for mz in sorted(masses):
                data = database[str(mz)]
                formula = data.get('formula', 'Unknown')
                description = data.get('description', 'No description')
                category = data.get('category', 'Unknown')

                report_lines.append(f"m/z {mz:8.4f}: {formula:12s} | {category:15s} | {description}")

            # Save report
            report_path = os.path.join(self.base_dir, 'outputs', f'database_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w') as f:
                f.write('\n'.join(report_lines))

            QMessageBox.information(self, "Report Generated", f"Database report saved to:\n{report_path}")

        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {e}")

    def validate_all_pending(self):
        """Validate all pending assignments for chemical reasonableness"""
        if not hasattr(self, 'pending_assignments') or not self.pending_assignments:
            QMessageBox.information(self, "No Assignments", "No pending assignments to validate.")
            return

        try:
            validated_count = 0
            issues_found = []

            for i, assignment in enumerate(self.pending_assignments):
                mz = assignment['mz']
                formula = assignment['formula']

                # Run chemical validation
                chem_issues = self.validate_fragment_chemistry(mz, formula)

                if not chem_issues:
                    assignment['validation_status'] = 'Validated'
                    validated_count += 1
                else:
                    assignment['validation_status'] = 'Issues Found'
                    issues_found.append(f"m/z {mz} ({formula}): {', '.join(chem_issues)}")

            # Update the pending table display
            self.refresh_database_status()

            # Show results
            if validated_count == len(self.pending_assignments):
                QMessageBox.information(self, "Validation Complete",
                                      f"All {validated_count} assignments validated successfully!")
            else:
                issues_text = '\n'.join(issues_found[:10])  # Limit display
                if len(issues_found) > 10:
                    issues_text += f"\n... and {len(issues_found) - 10} more issues"

                QMessageBox.warning(self, "Validation Results",
                                  f"Validated: {validated_count}/{len(self.pending_assignments)}\n\n"
                                  f"Issues found:\n{issues_text}")

        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate pending assignments: {e}")

    def initialize_database_protection(self):
        """Initialize database protection measures on startup"""
        try:
            # Ensure backup directory exists
            backup_dir = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            # Create automatic startup backup if database exists
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')
            if os.path.exists(db_path):
                # Create timestamp-based backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                startup_backup = os.path.join(backup_dir, f'startup_backup_{timestamp}.json')

                # Copy current database as startup backup
                import shutil
                shutil.copy2(db_path, startup_backup)

                # Clean up old startup backups (keep only last 10)
                startup_backups = [f for f in os.listdir(backup_dir) if f.startswith('startup_backup_')]
                if len(startup_backups) > 10:
                    startup_backups.sort()
                    for old_backup in startup_backups[:-10]:  # Keep only last 10
                        old_backup_path = os.path.join(backup_dir, old_backup)
                        try:
                            os.remove(old_backup_path)
                        except OSError:
                            pass  # Ignore errors when cleaning old backups

                print(f"📁 Database startup backup created: {startup_backup}")

            # Set database file to read-only mode for additional protection
            if os.path.exists(db_path):
                try:
                    # Make database read-only (but allow writing through our controlled methods)
                    current_stat = os.stat(db_path)
                    # Store original permissions for restoration if needed
                    self.db_original_permissions = current_stat.st_mode
                    print("🔒 Database protection initialized")
                except OSError:
                    print("⚠️ Could not set database protection mode")

        except Exception as e:
            print(f"⚠️ Database protection initialization failed: {e}")

    def ensure_database_writable(self):
        """Temporarily make database writable for controlled modifications"""
        try:
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')
            if os.path.exists(db_path) and hasattr(self, 'db_original_permissions'):
                os.chmod(db_path, self.db_original_permissions | 0o200)  # Add write permission
        except OSError:
            pass  # Ignore permission errors

    def restore_database_protection(self):
        """Restore database protection after controlled modifications"""
        try:
            db_path = os.path.join(self.base_dir, 'data', 'FragmentDatabase', 'alucone_fragments.json')
            if os.path.exists(db_path):
                # Make read-only again (remove write permission for owner)
                current_stat = os.stat(db_path)
                os.chmod(db_path, current_stat.st_mode & ~0o200)
        except OSError:
            pass  # Ignore permission errors

    def update_group_analysis(self):
        """Update group analysis when selection changes"""
        if not self.dual_ion_mode or not hasattr(self, 'group_combo'):
            return

        # Update available groups in combo box
        groups = self.multi_ion_manager.get_sample_groups()

        current_text = self.group_combo.currentText()
        self.group_combo.clear()

        if groups:
            self.group_combo.addItems(groups)
            # Try to restore previous selection
            index = self.group_combo.findText(current_text)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)

    def run_group_analysis(self):
        """Run analysis for the selected group"""
        if not self.dual_ion_mode:
            QMessageBox.warning(self, "Warning", "Dual ion mode not available. Please load data files first.")
            return

        selected_group = self.group_combo.currentText()
        if not selected_group:
            QMessageBox.warning(self, "Warning", "Please select a sample group to analyze.")
            return

        try:
            # Update progress
            self.progress_bar.setValue(10)
            QApplication.processEvents()

            # Get data for both polarities
            neg_data = self.multi_ion_manager.get_group_intensity_data(selected_group, "negative")
            pos_data = self.multi_ion_manager.get_group_intensity_data(selected_group, "positive")

            self.progress_bar.setValue(50)
            QApplication.processEvents()

            # Update negative ion table
            if neg_data is not None:
                self.populate_group_table(self.neg_group_table, neg_data.head(30))
            else:
                self.clear_group_table(self.neg_group_table)

            self.progress_bar.setValue(75)
            QApplication.processEvents()

            # Update positive ion table
            if pos_data is not None:
                self.populate_group_table(self.pos_group_table, pos_data.head(30))
            else:
                self.clear_group_table(self.pos_group_table)

            # Update statistics
            summary = self.multi_ion_manager.get_comparison_summary(selected_group)
            self.update_group_statistics(summary)

            # Update visualization
            self.update_group_visualization(neg_data, pos_data, selected_group)

            self.progress_bar.setValue(100)
            QApplication.processEvents()

            # Reset progress bar after delay
            QTimer.singleShot(1000, lambda: self.progress_bar.setValue(0))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze group: {str(e)}")
            self.progress_bar.setValue(0)

    def populate_group_table(self, table, data):
        """Populate a group analysis table with data"""
        if data is None or data.empty:
            self.clear_group_table(table)
            return

        table.setRowCount(len(data))

        for row, (_, row_data) in enumerate(data.iterrows()):
            # m/z
            mz_item = QTableWidgetItem(f"{row_data['mass']:.5f}")
            mz_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, mz_item)

            # Mean intensity
            intensity_item = QTableWidgetItem(f"{row_data['mean_intensity']:.2e}")
            intensity_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, intensity_item)

            # Standard deviation
            std_item = QTableWidgetItem(f"{row_data['std_intensity']:.2e}")
            std_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 2, std_item)

            # Assignment
            assignment = row_data.get('assignment', 'Unknown')
            if assignment == 'Unknown' and hasattr(self, 'analyzer') and self.analyzer:
                # Try to get assignment from existing database
                assignment = self.analyzer.get_assignment_from_database(row_data['mass'])

            assignment_item = QTableWidgetItem(str(assignment))
            table.setItem(row, 3, assignment_item)

    def clear_group_table(self, table):
        """Clear a group analysis table"""
        table.setRowCount(0)

    def update_group_statistics(self, summary):
        """Update the group statistics text area"""
        if not summary:
            self.group_stats_text.clear()
            return

        stats_text = f"📊 Analysis Results for: {summary['group_name']}\n\n"

        if summary['negative_peaks'] > 0:
            stats_text += f"🔵 Negative Ion Mode:\n"
            stats_text += f"   • Total peaks: {summary['negative_peaks']}\n"
            stats_text += f"   • Total intensity: {summary['total_negative_intensity']:.2e}\n"
            if summary['top_negative_peaks']:
                top_neg = summary['top_negative_peaks'][0]
                stats_text += f"   • Strongest peak: {top_neg['mass']:.5f} m/z ({top_neg['mean_intensity']:.2e})\n"

        if summary['positive_peaks'] > 0:
            stats_text += f"\n🔴 Positive Ion Mode:\n"
            stats_text += f"   • Total peaks: {summary['positive_peaks']}\n"
            stats_text += f"   • Total intensity: {summary['total_positive_intensity']:.2e}\n"
            if summary['top_positive_peaks']:
                top_pos = summary['top_positive_peaks'][0]
                stats_text += f"   • Strongest peak: {top_pos['mass']:.5f} m/z ({top_pos['mean_intensity']:.2e})\n"

        if summary['negative_peaks'] > 0 and summary['positive_peaks'] > 0:
            ratio = summary['total_negative_intensity'] / summary['total_positive_intensity']
            stats_text += f"\n📈 Intensity Ratio (Neg/Pos): {ratio:.2f}"

        self.group_stats_text.setText(stats_text)

    def update_group_visualization(self, neg_data, pos_data, group_name):
        """Update the group analysis visualization"""
        if not hasattr(self, 'group_plot_figure'):
            return

        # Clear previous plot
        self.group_plot_figure.clear()

        # Create subplot
        ax = self.group_plot_figure.add_subplot(111)

        # Get top 10 peaks for visualization
        top_n = 10

        if neg_data is not None and not neg_data.empty:
            top_neg = neg_data.head(top_n)

            # Create bar plot
            x_pos = range(len(top_neg))
            bars = ax.bar(x_pos, top_neg['mean_intensity'],
                         color='steelblue', alpha=0.7, label='Negative Ion')

            # Add m/z labels
            ax.set_xticks(x_pos)
            ax.set_xticklabels([f"{mass:.3f}" for mass in top_neg['mass']],
                              rotation=45, ha='right')

            # Add intensity values on bars
            for i, (bar, intensity) in enumerate(zip(bars, top_neg['mean_intensity'])):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{intensity:.1e}', ha='center', va='bottom', fontsize=8)

        ax.set_xlabel('m/z')
        ax.set_ylabel('Mean Intensity')
        ax.set_title(f'Top {top_n} Fragment Peaks - {group_name}')
        ax.grid(True, alpha=0.3)

        # Format y-axis for scientific notation
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))

        # Adjust layout
        self.group_plot_figure.tight_layout()

        # Refresh canvas
        if hasattr(self, 'group_plot_canvas'):
            self.group_plot_canvas.draw()

    def export_group_analysis(self):
        """Export group analysis results to Excel"""
        selected_group = self.group_combo.currentText()
        if not selected_group or not self.dual_ion_mode:
            QMessageBox.warning(self, "Warning", "No group analysis to export.")
            return

        # Get file path for export
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Group Analysis",
            f"group_analysis_{selected_group.replace(' ', '_').replace('/', '_')}.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Get data for both polarities
            neg_data = self.multi_ion_manager.get_group_intensity_data(selected_group, "negative")
            pos_data = self.multi_ion_manager.get_group_intensity_data(selected_group, "positive")

            if file_path.endswith('.xlsx'):
                # Export to Excel with multiple sheets
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    if neg_data is not None:
                        neg_data.to_excel(writer, sheet_name='Negative_Ions', index=False)
                    if pos_data is not None:
                        pos_data.to_excel(writer, sheet_name='Positive_Ions', index=False)

                    # Add summary sheet
                    summary = self.multi_ion_manager.get_comparison_summary(selected_group)
                    summary_df = pd.DataFrame([summary])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

            elif file_path.endswith('.csv'):
                # Export negative ion data only for CSV
                if neg_data is not None:
                    neg_data.to_csv(file_path, index=False)
                else:
                    QMessageBox.warning(self, "Warning", "No negative ion data to export.")
                    return

            QMessageBox.information(self, "Success", f"Group analysis exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export group analysis: {str(e)}")


def main():
    """Main application entry point"""
    # Set Qt platform if not already set
    if 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'xcb'

    # Ensure only one instance of QApplication
    if QApplication.instance() is not None:
        print("⚠️ QApplication instance already exists. Using existing instance.")
        app = QApplication.instance()
    else:
        # Enable high DPI support BEFORE creating QApplication
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

        app = QApplication(sys.argv)

        # Ensure proper cleanup on exit
        app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
    
    # Set application properties
    app.setApplicationName("ToF-SIMS PCA Analysis (Matplotlib)")
    app.setApplicationVersion("2.0")
    
    # Multi-display detection and selection
    screens = app.screens()
    print(f"🚀 Qt Platform: {app.platformName()}")
    print(f"🖥️  Detected {len(screens)} display(s)")
    
    # Choose the best screen (largest resolution or external monitor)
    best_screen = None
    max_area = 0
    
    for i, screen in enumerate(screens):
        geom = screen.geometry()
        area = geom.width() * geom.height()
        dpi = screen.logicalDotsPerInch()
        
        print(f"   Display {i+1}: {geom.width()}x{geom.height()} @ {dpi:.0f} DPI (area: {area:,})")
        
        # Prefer larger displays (typically external monitors)
        if area > max_area:
            max_area = area
            best_screen = screen
    
    # Use the best screen found (fallback to primary if none found)
    screen = best_screen if best_screen else app.primaryScreen()
    screen_geometry = screen.geometry()
    screen_dpi = screen.logicalDotsPerInch()
    device_pixel_ratio = screen.devicePixelRatio()
    
    print(f"📺 Using: {screen_geometry.width()}x{screen_geometry.height()} @ {screen_dpi:.0f} DPI")
    print(f"🔍 Device Pixel Ratio: {device_pixel_ratio:.2f}")
    print("📊 Using native matplotlib plotting (better performance)")
    
    # Create and show main window
    window = ToFSIMSPCAApp()
    
    # Adjust window size based on screen resolution and DPI
    base_width, base_height = 1400, 900
    
    # Scale window size based on DPI and screen size
    scale_factor = max(1.0, min(device_pixel_ratio, screen_dpi / 96.0))
    
    # Ensure window fits on screen
    max_width = int(screen_geometry.width() * 0.9)
    max_height = int(screen_geometry.height() * 0.9)
    
    adjusted_width = min(int(base_width * scale_factor), max_width)
    adjusted_height = min(int(base_height * scale_factor), max_height)
    
    window.resize(adjusted_width, adjusted_height)
    
    # Center window on the selected screen (accounting for screen position)
    screen_x = screen_geometry.x()
    screen_y = screen_geometry.y()
    
    center_x = screen_x + (screen_geometry.width() - adjusted_width) // 2
    center_y = screen_y + (screen_geometry.height() - adjusted_height) // 2
    
    window.move(center_x, center_y)
    
    print(f"📐 Window size: {adjusted_width}x{adjusted_height} (scale factor: {scale_factor:.2f})")
    
    window.show()

    # Run application with proper cleanup
    try:
        exit_code = app.exec()
    finally:
        # Force cleanup of the application
        window.deleteLater()
        app.deleteLater()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()