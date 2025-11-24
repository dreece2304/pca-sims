"""
Manual Assignment Dialog

Manual fragment assignment dialog with element composition calculator.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt

class ManualAssignmentDialog(QDialog):
    """Manual fragment assignment dialog with element composition calculator"""

    # Atomic masses for common elements
    ATOMIC_MASSES = {
        'C': 12.0000,
        'H': 1.00783,
        'O': 15.99491,
        'N': 14.00307,
        'Al': 26.98154,
        'Si': 27.97693,
        'Cl': 34.96885,  # Cl-35
        'F': 18.99840,
        'Na': 22.98977,
        'K': 38.96371
    }

    def __init__(self, observed_mz, current_assignment=None, parent=None):
        super().__init__(parent)

        self.observed_mz = observed_mz
        self.current_assignment = current_assignment  # Existing assignment dict or None
        self.element_spinners = {}
        self.assignment_data = None  # Will store result when saved

        self.setWindowTitle(f"Manual Fragment Assignment - m/z {observed_mz:.4f}")
        self.resize(700, 800)

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Header
        header_text = f"Assign Fragment: m/z {self.observed_mz:.4f}"
        if self.current_assignment and self.current_assignment.get('assignment') != "Unassigned":
            header_text += f" (Current: {self.current_assignment['assignment']})"

        header = QLabel(header_text)
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        # Element input section
        element_group = QGroupBox("Element Composition")
        element_layout = QGridLayout(element_group)

        # Common elements (row 1)
        elements_row1 = ['C', 'H', 'O', 'N']
        for col, element in enumerate(elements_row1):
            element_layout.addWidget(QLabel(f"{element}:"), 0, col*2)
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(99)
            spinner.setValue(0)
            spinner.valueChanged.connect(self.update_calculated_values)
            element_layout.addWidget(spinner, 0, col*2+1)
            self.element_spinners[element] = spinner

        # Material elements (row 2)
        elements_row2 = ['Al', 'Si']
        for col, element in enumerate(elements_row2):
            element_layout.addWidget(QLabel(f"{element}:"), 1, col*2)
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(99)
            spinner.setValue(0)
            spinner.valueChanged.connect(self.update_calculated_values)
            element_layout.addWidget(spinner, 1, col*2+1)
            self.element_spinners[element] = spinner

        # Contaminants (row 3)
        elements_row3 = ['Cl', 'F', 'Na', 'K']
        for col, element in enumerate(elements_row3):
            element_layout.addWidget(QLabel(f"{element}:"), 2, col*2)
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(99)
            spinner.setValue(0)
            spinner.valueChanged.connect(self.update_calculated_values)
            element_layout.addWidget(spinner, 2, col*2+1)
            self.element_spinners[element] = spinner

        # Quick set buttons
        quick_set_layout = QHBoxLayout()
        quick_set_layout.addWidget(QLabel("Quick Set:"))

        btn_ch = QPushButton("CH")
        btn_ch.clicked.connect(lambda: self.quick_set_formula({'C': 1, 'H': 1}))
        quick_set_layout.addWidget(btn_ch)

        btn_c2h = QPushButton("C₂H")
        btn_c2h.clicked.connect(lambda: self.quick_set_formula({'C': 2, 'H': 1}))
        quick_set_layout.addWidget(btn_c2h)

        btn_oh = QPushButton("OH")
        btn_oh.clicked.connect(lambda: self.quick_set_formula({'O': 1, 'H': 1}))
        quick_set_layout.addWidget(btn_oh)

        btn_alo = QPushButton("AlO")
        btn_alo.clicked.connect(lambda: self.quick_set_formula({'Al': 1, 'O': 1}))
        quick_set_layout.addWidget(btn_alo)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_all)
        quick_set_layout.addWidget(btn_clear)

        quick_set_layout.addStretch()

        element_layout.addLayout(quick_set_layout, 3, 0, 1, 8)

        layout.addWidget(element_group)

        # Calculated values section
        calc_group = QGroupBox("Calculated Values")
        calc_layout = QGridLayout(calc_group)

        # Formula
        calc_layout.addWidget(QLabel("Formula:"), 0, 0)
        self.formula_label = QLabel("—")
        self.formula_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        calc_layout.addWidget(self.formula_label, 0, 1)

        # Calculated mass
        calc_layout.addWidget(QLabel("Calculated Mass:"), 1, 0)
        self.calc_mass_label = QLabel("—")
        self.calc_mass_label.setStyleSheet("font-weight: bold;")
        calc_layout.addWidget(self.calc_mass_label, 1, 1)

        # Observed m/z
        calc_layout.addWidget(QLabel("Observed m/z:"), 2, 0)
        self.observed_label = QLabel(f"{self.observed_mz:.4f}")
        self.observed_label.setStyleSheet("font-weight: bold;")
        calc_layout.addWidget(self.observed_label, 2, 1)

        # Mass error
        calc_layout.addWidget(QLabel("Mass Error:"), 3, 0)
        self.error_label = QLabel("—")
        calc_layout.addWidget(self.error_label, 3, 1)

        layout.addWidget(calc_group)

        # Assignment details section
        details_group = QGroupBox("Assignment Details")
        details_layout = QVBoxLayout(details_group)

        # Assignment name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Assignment Name:"))
        self.assignment_name = QLineEdit()
        self.assignment_name.setPlaceholderText("e.g., C₂H⁻, AlO⁻, Cl⁻")
        name_layout.addWidget(self.assignment_name)
        details_layout.addLayout(name_layout)

        # Chemical family
        family_layout = QHBoxLayout()
        family_layout.addWidget(QLabel("Chemical Family:"))
        self.family_combo = QComboBox()
        self.family_combo.addItems([
            "Al-based",
            "Saturated_carbon",
            "Unsaturated_carbon",
            "Organic_oxygen",
            "Carbonyl",
            "Hydroxyl",
            "Contamination",
            "Unknown"
        ])
        self.family_combo.setCurrentText("Unknown")
        family_layout.addWidget(self.family_combo)
        details_layout.addLayout(family_layout)

        # Confidence
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Confidence:"))
        self.confidence_combo = QComboBox()
        self.confidence_combo.addItems(["High", "Medium", "Low"])
        self.confidence_combo.setCurrentText("Medium")
        confidence_layout.addWidget(self.confidence_combo)
        details_layout.addLayout(confidence_layout)

        # Notes
        details_layout.addWidget(QLabel("Notes (optional):"))
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Additional notes about this assignment...")
        self.notes_text.setMaximumHeight(80)
        details_layout.addWidget(self.notes_text)

        layout.addWidget(details_group)

        # Validation messages
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("padding: 10px; border: 1px solid #ddd; border-radius: 3px;")
        layout.addWidget(self.validation_label)

        # Buttons
        button_layout = QHBoxLayout()

        button_layout.addStretch()

        save_btn = QPushButton("💾 Save Assignment")
        save_btn.clicked.connect(self.save_assignment)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Initial update
        self.update_calculated_values()

    def quick_set_formula(self, elements):
        """Quick set element counts"""
        # Clear all first
        for spinner in self.element_spinners.values():
            spinner.setValue(0)

        # Set specified elements
        for element, count in elements.items():
            if element in self.element_spinners:
                self.element_spinners[element].setValue(count)

    def clear_all(self):
        """Clear all element counts"""
        for spinner in self.element_spinners.values():
            spinner.setValue(0)

    def update_calculated_values(self):
        """Update calculated mass and formula"""
        # Get element counts
        counts = {elem: spinner.value() for elem, spinner in self.element_spinners.items()}

        # Check if any elements selected
        total_atoms = sum(counts.values())

        if total_atoms == 0:
            self.formula_label.setText("—")
            self.calc_mass_label.setText("—")
            self.error_label.setText("—")
            self.validation_label.setVisible(False)
            return

        # Build formula string
        formula_parts = []
        for element in ['C', 'H', 'O', 'N', 'Al', 'Si', 'Cl', 'F', 'Na', 'K']:
            count = counts[element]
            if count > 0:
                if count == 1:
                    formula_parts.append(element)
                else:
                    formula_parts.append(f"{element}_{count}")

        formula = "".join(formula_parts)
        self.formula_label.setText(formula)

        # Calculate mass
        calc_mass = sum(counts[elem] * self.ATOMIC_MASSES[elem]
                       for elem in counts if counts[elem] > 0)

        self.calc_mass_label.setText(f"{calc_mass:.4f} Da")

        # Calculate error
        error_da = calc_mass - self.observed_mz
        error_ppm = (error_da / self.observed_mz) * 1e6

        # Color code by error magnitude
        if abs(error_ppm) < 50:
            color = "green"
            icon = "✓"
        elif abs(error_ppm) < 100:
            color = "orange"
            icon = "⚠"
        else:
            color = "red"
            icon = "✗"

        error_text = f"{icon} {error_ppm:+.1f} ppm ({error_da:+.4f} Da)"
        self.error_label.setText(error_text)
        self.error_label.setStyleSheet(f"font-weight: bold; color: {color};")

        # Update validation
        self.validate_assignment()

    def validate_assignment(self):
        """Validate the current assignment"""
        messages = []

        # Get counts
        counts = {elem: spinner.value() for elem, spinner in self.element_spinners.items()}
        total_atoms = sum(counts.values())

        if total_atoms == 0:
            return

        # Check mass error
        calc_mass = sum(counts[elem] * self.ATOMIC_MASSES[elem]
                       for elem in counts if counts[elem] > 0)
        error_ppm = abs((calc_mass - self.observed_mz) / self.observed_mz * 1e6)

        if error_ppm > 50:
            messages.append(f"⚠️ <b>Warning:</b> Mass error ({error_ppm:.1f} ppm) exceeds recommended 50 ppm threshold")

        # Check valence (simple rules)
        h_count = counts['H']
        o_count = counts['O']
        c_count = counts['C']

        if h_count > (c_count * 2 + 2 + o_count):
            messages.append("⚠️ <b>Warning:</b> Hydrogen count seems unusually high for this formula")

        # Check for unusual combinations
        if counts['Al'] > 0 and counts['C'] > 3:
            messages.append("💡 <b>Note:</b> Al + high carbon content is unusual for alucone")

        if counts['Na'] > 0 or counts['K'] > 0:
            messages.append("⚠️ <b>Contamination:</b> Na/K detected - likely contamination")

        # Display messages
        if messages:
            self.validation_label.setText("<br>".join(messages))
            self.validation_label.setVisible(True)
        else:
            self.validation_label.setText("✅ <b>Valid:</b> Assignment looks good")
            self.validation_label.setVisible(True)

    def save_assignment(self):
        """Save the assignment and close dialog"""
        counts = {elem: spinner.value() for elem, spinner in self.element_spinners.items()}
        total_atoms = sum(counts.values())

        if total_atoms == 0:
            QMessageBox.warning(self, "Validation Error",
                              "Please specify at least one element.")
            return

        if not self.assignment_name.text().strip():
            QMessageBox.warning(self, "Validation Error",
                              "Please enter an assignment name.")
            return

        # Build formula (for storage, not display)
        formula_parts = []
        for element in ['C', 'H', 'O', 'N', 'Al', 'Si', 'Cl', 'F', 'Na', 'K']:
            count = counts[element]
            if count > 0:
                formula_parts.append(f"{element}{count if count > 1 else ''}")

        formula = "".join(formula_parts)

        # Calculate mass
        calc_mass = sum(counts[elem] * self.ATOMIC_MASSES[elem]
                       for elem in counts if counts[elem] > 0)

        error_ppm = ((calc_mass - self.observed_mz) / self.observed_mz) * 1e6

        # Store assignment data
        self.assignment_data = {
            'assignment': self.assignment_name.text().strip(),
            'formula': formula,
            'chemical_family': self.family_combo.currentText(),
            'confidence': self.confidence_combo.currentText(),
            'calculated_mass': calc_mass,
            'error_ppm': error_ppm,
            'notes': self.notes_text.toPlainText().strip(),
            'element_composition': counts.copy()
        }


        self.accept()
