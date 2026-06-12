"""
Fragment Assignment Dialog

Dialog for detailed fragment assignment with peak intensities and candidate matches.
"""

import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QSpinBox, QLineEdit,
    QComboBox, QTextEdit, QFormLayout, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


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

            # Get current polarity from parent app to ensure correct matches
            current_polarity = self.parent_app.multi_ion_manager.active_polarity

            candidates = self.parent_app.find_multiple_fragment_assignments(
                self.mass,
                tolerance_ppm=tolerance_ppm,
                polarity=current_polarity,
                max_matches=10
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
