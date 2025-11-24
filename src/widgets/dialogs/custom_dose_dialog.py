"""
Custom Dose Dialog

Dialog for setting custom dose values and sample types for dose-response analysis.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QDoubleSpinBox, QPushButton, QMessageBox
)

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

