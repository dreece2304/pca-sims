"""
PyQt5-based Interactive GUI for ToF-SIMS PCA Data Selection
Superior performance with integrated Plotly visualizations
"""

import sys
import os
import threading
import traceback
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        HAS_WEBENGINE = True
    except ImportError:
        HAS_WEBENGINE = False
        print("Warning: QtWebEngineWidgets not available. Interactive plots will be disabled.")
    PYQT_VERSION = 5
except ImportError:
    try:
        from PySide2.QtWidgets import *
        from PySide2.QtCore import *
        from PySide2.QtGui import *
        try:
            from PySide2.QtWebEngineWidgets import QWebEngineView
            HAS_WEBENGINE = True
        except ImportError:
            HAS_WEBENGINE = False
            print("Warning: QtWebEngineWidgets not available. Interactive plots will be disabled.")
        PYQT_VERSION = 'PySide2'
    except ImportError:
        print("Error: Neither PyQt5 nor PySide2 found. Please install one of them:")
        print("pip install PyQt5")
        print("or") 
        print("pip install PySide2")
        sys.exit(1)

# Import our existing PCA classes
from tof_sims_pca import ToFSIMSPCA
from tof_sims_plotting import ToFSIMSPlotter


class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = pyqtSignal() if PYQT_VERSION == 5 else Signal()
    error = pyqtSignal(str) if PYQT_VERSION == 5 else Signal(str)
    result = pyqtSignal(object) if PYQT_VERSION == 5 else Signal(object)
    progress = pyqtSignal(str) if PYQT_VERSION == 5 else Signal(str)


class PCAWorker(QRunnable):
    """Worker thread for PCA analysis"""
    
    def __init__(self, pca_analysis, selected_samples, preprocessing_options, n_components):
        super().__init__()
        self.pca_analysis = pca_analysis
        self.selected_samples = selected_samples
        self.preprocessing_options = preprocessing_options
        self.n_components = n_components
        self.signals = WorkerSignals()
        
    def run(self):
        try:
            # Filter samples
            self.signals.progress.emit("Filtering selected samples...")
            selected_mask = self.pca_analysis.sample_info['sample_name'].isin(self.selected_samples)
            self.pca_analysis.raw_data = self.pca_analysis.raw_data[self.selected_samples]
            self.pca_analysis.sample_info = self.pca_analysis.sample_info[selected_mask].reset_index(drop=True)
            
            # Preprocess data
            self.signals.progress.emit("Preprocessing data...")
            self.pca_analysis.preprocess_data(**self.preprocessing_options)
            
            # Run PCA
            self.signals.progress.emit("Running PCA analysis...")
            self.pca_analysis.run_pca(n_components=self.n_components)
            
            # Export results
            self.signals.progress.emit("Exporting results...")
            self.pca_analysis.export_results()
            
            self.signals.result.emit(self.pca_analysis)
            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.error.emit(f"PCA analysis failed: {str(e)}")


class PlotWorker(QRunnable):
    """Worker thread for plot generation"""
    
    def __init__(self, pca_analysis, output_dir):
        super().__init__()
        self.pca_analysis = pca_analysis
        self.output_dir = output_dir
        self.signals = WorkerSignals()
        
    def run(self):
        try:
            self.signals.progress.emit("Generating publication-quality plots...")
            
            plotter = ToFSIMSPlotter(self.output_dir)
            plot_files = plotter.create_all_plots(
                scores_df=self.pca_analysis.scores_df,
                loadings_df=self.pca_analysis.loadings_df,
                variance_explained=self.pca_analysis.variance_explained,
                max_components=min(5, len(self.pca_analysis.variance_explained))
            )
            
            self.signals.result.emit(plot_files)
            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.error.emit(f"Plot generation failed: {str(e)}")


class PCADataSelectorGUI(QMainWindow):
    """
    PyQt5-based GUI for ToF-SIMS PCA data selection and analysis
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToF-SIMS PCA Data Selector")
        self.setMinimumSize(1200, 900)
        
        # Data storage
        self.data_file = None
        self.output_dir = None
        self.pca_analysis = None
        self.sample_info = None
        self.available_patterns = []
        self.available_squares = []
        
        # Thread pool for background tasks
        self.thread_pool = QThreadPool()
        
        self.init_ui()
        self.center_window()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        main_layout = QVBoxLayout(scroll_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # File Selection Section
        self.create_file_selection_section(main_layout)
        
        # Ion Type Selection
        self.create_ion_type_section(main_layout)
        
        # Sample Selection Sections (initially disabled)
        self.create_sample_selection_sections(main_layout)
        
        # Preprocessing Options
        self.create_preprocessing_section(main_layout)
        
        # PCA Options
        self.create_pca_options_section(main_layout)
        
        # Analysis Controls
        self.create_analysis_controls_section(main_layout)
        
        # Results Display
        self.create_results_section(main_layout)
        
        # Status Section
        self.create_status_section(main_layout)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # Main window layout
        window_layout = QVBoxLayout(central_widget)
        window_layout.addWidget(scroll_area)
        
        # Initially disable sample selection
        self.set_selection_enabled(False)
        
    def create_file_selection_section(self, parent_layout):
        """Create file selection section"""
        group = QGroupBox("Data Files")
        layout = QGridLayout(group)
        
        # Data file selection
        layout.addWidget(QLabel("Data File:"), 0, 0)
        self.data_file_edit = QLineEdit()
        self.data_file_edit.setReadOnly(True)
        layout.addWidget(self.data_file_edit, 0, 1)
        
        browse_data_btn = QPushButton("Browse")
        browse_data_btn.clicked.connect(self.browse_data_file)
        layout.addWidget(browse_data_btn, 0, 2)
        
        # Output directory selection
        layout.addWidget(QLabel("Output Directory:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        layout.addWidget(self.output_dir_edit, 1, 1)
        
        # Output directory buttons
        output_btn_layout = QHBoxLayout()
        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self.browse_output_dir)
        output_btn_layout.addWidget(browse_output_btn)
        
        new_folder_btn = QPushButton("New Folder")
        new_folder_btn.clicked.connect(self.create_new_output_dir)
        output_btn_layout.addWidget(new_folder_btn)
        
        output_btn_widget = QWidget()
        output_btn_widget.setLayout(output_btn_layout)
        layout.addWidget(output_btn_widget, 1, 2)
        
        # Load data button
        self.load_data_btn = QPushButton("Load Data")
        self.load_data_btn.clicked.connect(self.load_data)
        self.load_data_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        layout.addWidget(self.load_data_btn, 2, 0, 1, 3)
        
        parent_layout.addWidget(group)
        
    def create_ion_type_section(self, parent_layout):
        """Create ion type selection section"""
        group = QGroupBox("Ion Type")
        layout = QHBoxLayout(group)
        
        self.ion_type_group = QButtonGroup()
        
        self.positive_radio = QRadioButton("Positive Ions")
        self.negative_radio = QRadioButton("Negative Ions")
        self.negative_radio.setChecked(True)
        
        self.ion_type_group.addButton(self.positive_radio, 0)
        self.ion_type_group.addButton(self.negative_radio, 1)
        
        layout.addWidget(self.positive_radio)
        layout.addWidget(self.negative_radio)
        layout.addStretch()
        
        parent_layout.addWidget(group)
        
    def create_sample_selection_sections(self, parent_layout):
        """Create pattern and square selection sections"""
        # Pattern selection
        self.pattern_group = QGroupBox("Pattern Selection")
        self.pattern_layout = QVBoxLayout(self.pattern_group)
        
        # Pattern control buttons
        pattern_btn_layout = QHBoxLayout()
        self.select_all_patterns_btn = QPushButton("Select All Patterns")
        self.select_all_patterns_btn.clicked.connect(self.select_all_patterns)
        pattern_btn_layout.addWidget(self.select_all_patterns_btn)
        
        self.deselect_all_patterns_btn = QPushButton("Deselect All Patterns") 
        self.deselect_all_patterns_btn.clicked.connect(self.deselect_all_patterns)
        pattern_btn_layout.addWidget(self.deselect_all_patterns_btn)
        pattern_btn_layout.addStretch()
        
        self.pattern_layout.addLayout(pattern_btn_layout)
        
        # Pattern checkboxes container
        self.pattern_checkboxes_widget = QWidget()
        self.pattern_checkboxes_layout = QGridLayout(self.pattern_checkboxes_widget)
        self.pattern_layout.addWidget(self.pattern_checkboxes_widget)
        
        parent_layout.addWidget(self.pattern_group)
        
        # Square selection
        self.square_group = QGroupBox("Square Selection")
        self.square_layout = QVBoxLayout(self.square_group)
        
        # Square control buttons
        square_btn_layout = QHBoxLayout()
        self.select_all_squares_btn = QPushButton("Select All Squares")
        self.select_all_squares_btn.clicked.connect(self.select_all_squares)
        square_btn_layout.addWidget(self.select_all_squares_btn)
        
        self.deselect_all_squares_btn = QPushButton("Deselect All Squares")
        self.deselect_all_squares_btn.clicked.connect(self.deselect_all_squares)
        square_btn_layout.addWidget(self.deselect_all_squares_btn)
        square_btn_layout.addStretch()
        
        self.square_layout.addLayout(square_btn_layout)
        
        # Square checkboxes container
        self.square_checkboxes_widget = QWidget()
        self.square_checkboxes_layout = QGridLayout(self.square_checkboxes_widget)
        self.square_layout.addWidget(self.square_checkboxes_widget)
        
        parent_layout.addWidget(self.square_group)
        
    def create_preprocessing_section(self, parent_layout):
        """Create preprocessing options section"""
        group = QGroupBox("Preprocessing Options")
        layout = QVBoxLayout(group)
        
        self.sqrt_transform_cb = QCheckBox("Square Root Transform")
        self.mean_center_cb = QCheckBox("Mean Center")
        self.scale_data_cb = QCheckBox("Scale Data")
        
        layout.addWidget(self.sqrt_transform_cb)
        layout.addWidget(self.mean_center_cb)
        layout.addWidget(self.scale_data_cb)
        
        parent_layout.addWidget(group)
        
    def create_pca_options_section(self, parent_layout):
        """Create PCA options section"""
        group = QGroupBox("PCA Options")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("Number of Components:"))
        
        self.n_components_spinbox = QSpinBox()
        self.n_components_spinbox.setRange(2, 20)
        self.n_components_spinbox.setValue(8)
        layout.addWidget(self.n_components_spinbox)
        
        layout.addStretch()
        
        parent_layout.addWidget(group)
        
    def create_analysis_controls_section(self, parent_layout):
        """Create analysis control buttons"""
        group = QGroupBox("Analysis")
        layout = QHBoxLayout(group)
        
        self.run_pca_btn = QPushButton("Run PCA Analysis")
        self.run_pca_btn.clicked.connect(self.run_pca_analysis)
        self.run_pca_btn.setStyleSheet("""
            QPushButton { 
                background-color: #0078d4; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
            }
            QPushButton:hover { 
                background-color: #106ebe; 
            }
            QPushButton:disabled { 
                background-color: #cccccc; 
                color: #666666; 
            }
        """)
        layout.addWidget(self.run_pca_btn)
        
        self.generate_plots_btn = QPushButton("Generate Plots")
        self.generate_plots_btn.clicked.connect(self.generate_plots)
        self.generate_plots_btn.setEnabled(False)
        layout.addWidget(self.generate_plots_btn)
        
        layout.addStretch()
        
        parent_layout.addWidget(group)
        
    def create_results_section(self, parent_layout):
        """Create results display section"""
        self.results_group = QGroupBox("PCA Results")
        layout = QVBoxLayout(self.results_group)
        
        # Results summary
        self.results_summary_label = QLabel()
        self.results_summary_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.results_summary_label)
        
        # Tabbed results
        self.results_tabs = QTabWidget()
        
        # PC1 Scores tab
        self.scores_tab = QWidget()
        scores_layout = QVBoxLayout(self.scores_tab)
        
        self.scores_table = QTableWidget()
        self.scores_table.setColumnCount(4)
        self.scores_table.setHorizontalHeaderLabels(['Sample Name', 'Pattern', 'Square', 'PC1 Score'])
        self.scores_table.horizontalHeader().setStretchLastSection(True)
        self.scores_table.setAlternatingRowColors(True)
        scores_layout.addWidget(self.scores_table)
        
        self.results_tabs.addTab(self.scores_tab, "PC1 Scores")
        
        # PC1 Loadings tab
        self.loadings_tab = QWidget()
        loadings_layout = QVBoxLayout(self.loadings_tab)
        
        self.loadings_table = QTableWidget()
        self.loadings_table.setColumnCount(4)
        self.loadings_table.setHorizontalHeaderLabels(['Rank', 'm/z', 'PC1 Loading', '|Loading|'])
        self.loadings_table.horizontalHeader().setStretchLastSection(True)
        self.loadings_table.setAlternatingRowColors(True)
        loadings_layout.addWidget(self.loadings_table)
        
        self.results_tabs.addTab(self.loadings_tab, "PC1 Loadings (Top 20)")
        
        # Interactive Plots tab
        self.plots_tab = QWidget()
        plots_layout = QVBoxLayout(self.plots_tab)
        
        # Plot controls
        plot_controls_layout = QHBoxLayout()
        plot_controls_layout.addWidget(QLabel("Plot Type:"))
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Scores Plot", "Loadings Plot", "Scree Plot"])
        self.plot_type_combo.currentTextChanged.connect(self.update_interactive_plot)
        plot_controls_layout.addWidget(self.plot_type_combo)
        
        plot_controls_layout.addStretch()
        plots_layout.addLayout(plot_controls_layout)
        
        # Web view for Plotly plots (or fallback)
        if HAS_WEBENGINE:
            self.plot_view = QWebEngineView()
            plots_layout.addWidget(self.plot_view)
        else:
            # Fallback: show message about missing WebEngine
            fallback_label = QLabel("Interactive plots require QtWebEngineWidgets.\n"
                                  "Install with: pip install PyQtWebEngine\n"
                                  "Static plots are still available via 'Generate Plots'.")
            fallback_label.setAlignment(Qt.AlignCenter)
            fallback_label.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
            plots_layout.addWidget(fallback_label)
            self.plot_view = None
        
        self.results_tabs.addTab(self.plots_tab, "Interactive Plots")
        
        layout.addWidget(self.results_tabs)
        
        # Initially hide results
        self.results_group.hide()
        
        parent_layout.addWidget(self.results_group)
        
    def create_status_section(self, parent_layout):
        """Create status section"""
        group = QGroupBox("Status")
        layout = QVBoxLayout(group)
        
        self.status_label = QLabel("Ready to load data...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(group)
        
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def browse_data_file(self):
        """Browse for data file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select ToF-SIMS Data File",
            "",
            "Text files (*.txt);;Excel files (*.xlsx);;All files (*.*)"
        )
        if file_path:
            self.data_file_edit.setText(file_path)
            self.data_file = file_path
            
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.output_dir = dir_path
            
    def create_new_output_dir(self):
        """Create a new output directory"""
        # First select parent directory
        parent_dir = QFileDialog.getExistingDirectory(
            self, "Select Parent Directory for New Folder"
        )
        if not parent_dir:
            return
            
        # Get folder name from user
        folder_name, ok = QInputDialog.getText(
            self, 
            "Create New Output Folder",
            "Enter folder name:",
            text="pca_output"
        )
        
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            
            # Remove invalid characters
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                folder_name = folder_name.replace(char, '_')
                
            new_dir = os.path.join(parent_dir, folder_name)
            
            try:
                os.makedirs(new_dir, exist_ok=True)
                self.output_dir_edit.setText(new_dir)
                self.output_dir = new_dir
                QMessageBox.information(
                    self, "Success", f"Created output directory:\n{new_dir}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to create directory:\n{str(e)}"
                )
                
    def load_data(self):
        """Load data file and populate selection options"""
        if not self.data_file or not self.output_dir:
            QMessageBox.critical(
                self, "Error", "Please select both data file and output directory"
            )
            return
            
        try:
            self.status_label.setText("Loading data file...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # Create PCA analysis object
            positive_ions = self.positive_radio.isChecked()
            self.pca_analysis = ToFSIMSPCA(self.data_file, self.output_dir, positive_ions)
            
            # Load the data
            self.pca_analysis.load_data()
            self.sample_info = self.pca_analysis.sample_info
            
            # Extract available patterns and squares
            self.available_patterns = sorted(self.sample_info['pattern_num'].unique())
            self.available_squares = sorted(self.sample_info['square_num'].unique())
            
            # Populate selection widgets
            self.populate_pattern_selection()
            self.populate_square_selection()
            
            # Enable selection sections
            self.set_selection_enabled(True)
            
            self.progress_bar.setVisible(False)
            self.status_label.setText(
                f"Data loaded successfully! Found {len(self.sample_info)} samples with "
                f"{len(self.available_patterns)} patterns and {len(self.available_squares)} squares."
            )
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
            
    def populate_pattern_selection(self):
        """Populate pattern selection checkboxes"""
        # Clear existing checkboxes
        self.clear_layout(self.pattern_checkboxes_layout)
        
        self.pattern_checkboxes = {}
        row, col = 0, 0
        
        for pattern in self.available_patterns:
            sample_count = len(self.sample_info[self.sample_info['pattern_num'] == pattern])
            
            checkbox = QCheckBox(f"Pattern {pattern} ({sample_count} samples)")
            checkbox.setChecked(True)  # Default to selected
            self.pattern_checkboxes[pattern] = checkbox
            
            self.pattern_checkboxes_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1
                
    def populate_square_selection(self):
        """Populate square selection checkboxes"""
        # Clear existing checkboxes
        self.clear_layout(self.square_checkboxes_layout)
        
        self.square_checkboxes = {}
        row, col = 0, 0
        
        for square in self.available_squares:
            sample_count = len(self.sample_info[self.sample_info['square_num'] == square])
            
            checkbox = QCheckBox(f"Square {square} ({sample_count} samples)")
            checkbox.setChecked(True)  # Default to selected
            self.square_checkboxes[square] = checkbox
            
            self.square_checkboxes_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
                
    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def set_selection_enabled(self, enabled):
        """Enable/disable selection sections"""
        self.pattern_group.setEnabled(enabled)
        self.square_group.setEnabled(enabled)
        
    def select_all_patterns(self):
        """Select all patterns"""
        for checkbox in self.pattern_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_patterns(self):
        """Deselect all patterns"""
        for checkbox in self.pattern_checkboxes.values():
            checkbox.setChecked(False)
            
    def select_all_squares(self):
        """Select all squares"""
        for checkbox in self.square_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_squares(self):
        """Deselect all squares"""
        for checkbox in self.square_checkboxes.values():
            checkbox.setChecked(False)
            
    def get_selected_samples(self) -> List[str]:
        """Get list of selected sample names"""
        if self.sample_info is None:
            return []
            
        selected_patterns = [
            p for p, cb in self.pattern_checkboxes.items() if cb.isChecked()
        ]
        selected_squares = [
            s for s, cb in self.square_checkboxes.items() if cb.isChecked()
        ]
        
        if not selected_patterns or not selected_squares:
            return []
            
        mask = (
            self.sample_info['pattern_num'].isin(selected_patterns) & 
            self.sample_info['square_num'].isin(selected_squares)
        )
        
        return self.sample_info[mask]['sample_name'].tolist()
        
    def run_pca_analysis(self):
        """Run PCA analysis with selected parameters"""
        if self.pca_analysis is None:
            QMessageBox.critical(self, "Error", "Please load data first")
            return
            
        selected_samples = self.get_selected_samples()
        if not selected_samples:
            QMessageBox.critical(
                self, "Error", 
                "No samples selected. Please select at least one pattern and square."
            )
            return
            
        # Disable buttons during analysis
        self.run_pca_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Prepare parameters
        preprocessing_options = {
            'sqrt_transform': self.sqrt_transform_cb.isChecked(),
            'mean_center': self.mean_center_cb.isChecked(),
            'scale_data': self.scale_data_cb.isChecked()
        }
        n_components = self.n_components_spinbox.value()
        
        # Create and run worker
        worker = PCAWorker(
            self.pca_analysis.copy() if hasattr(self.pca_analysis, 'copy') else self.pca_analysis,
            selected_samples, 
            preprocessing_options, 
            n_components
        )
        worker.signals.progress.connect(self.update_status)
        worker.signals.result.connect(self.on_pca_completed)
        worker.signals.error.connect(self.on_pca_error)
        worker.signals.finished.connect(self.on_pca_finished)
        
        self.thread_pool.start(worker)
        
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
        
    def on_pca_completed(self, pca_analysis):
        """Handle PCA completion"""
        self.pca_analysis = pca_analysis
        
        # Update results display
        self.update_results_display()
        
        # Show success message
        n_samples = len(self.pca_analysis.scores_df)
        n_components = len(self.pca_analysis.variance_explained)
        
        QMessageBox.information(
            self, "Success",
            f"PCA analysis completed!\n\n"
            f"Results saved to:\n{self.output_dir}\n\n"
            f"Analyzed {n_samples} samples\n"
            f"Computed {n_components} principal components"
        )
        
    def on_pca_error(self, error_message):
        """Handle PCA error"""
        QMessageBox.critical(self, "Error", error_message)
        
    def on_pca_finished(self):
        """Handle PCA thread completion"""
        self.run_pca_btn.setEnabled(True)
        self.generate_plots_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def update_results_display(self):
        """Update results display with PCA results"""
        if not hasattr(self.pca_analysis, 'scores_df'):
            return
            
        # Show results section
        self.results_group.show()
        
        # Update summary
        pc1_variance = self.pca_analysis.variance_explained[0]
        n_samples = len(self.pca_analysis.scores_df)
        self.results_summary_label.setText(
            f"PCA Results Summary - PC1 explains {pc1_variance:.1f}% of variance ({n_samples} samples)"
        )
        
        # Update tables
        self.populate_scores_table()
        self.populate_loadings_table()
        
        # Update interactive plots
        self.update_interactive_plot()
        
    def populate_scores_table(self):
        """Populate scores table"""
        scores_data = self.pca_analysis.scores_df.sort_values('PC1', ascending=False)
        
        self.scores_table.setRowCount(len(scores_data))
        
        for row, (idx, data) in enumerate(scores_data.iterrows()):
            sample_name = data.get('sample_name', str(idx))
            pattern = data.get('pattern', 'N/A')
            
            # Extract square info
            square = 'N/A'
            if 'square' in data:
                square = data['square']
            elif '_SQ' in sample_name:
                try:
                    square = sample_name.split('_SQ')[1].split('_')[0]
                    square = f"SQ{square}"
                except:
                    pass
                    
            pc1_score = f"{data['PC1']:.4f}"
            
            self.scores_table.setItem(row, 0, QTableWidgetItem(sample_name))
            self.scores_table.setItem(row, 1, QTableWidgetItem(str(pattern)))
            self.scores_table.setItem(row, 2, QTableWidgetItem(square))
            self.scores_table.setItem(row, 3, QTableWidgetItem(pc1_score))
            
    def populate_loadings_table(self):
        """Populate loadings table"""
        pc1_loadings = self.pca_analysis.loadings_df['PC1']
        masses = self.pca_analysis.loadings_df.index.values
        
        abs_loadings = np.abs(pc1_loadings.values)
        sorted_indices = np.argsort(abs_loadings)[::-1]
        top_indices = sorted_indices[:20]
        
        self.loadings_table.setRowCount(20)
        
        for rank, idx in enumerate(top_indices, 1):
            mass = f"{masses[idx]:.3f}"
            loading = f"{pc1_loadings.iloc[idx]:.6f}"
            abs_loading = f"{abs_loadings[idx]:.6f}"
            
            self.loadings_table.setItem(rank-1, 0, QTableWidgetItem(str(rank)))
            self.loadings_table.setItem(rank-1, 1, QTableWidgetItem(mass))
            self.loadings_table.setItem(rank-1, 2, QTableWidgetItem(loading))
            self.loadings_table.setItem(rank-1, 3, QTableWidgetItem(abs_loading))
            
    def update_interactive_plot(self):
        """Update interactive Plotly visualization"""
        if not hasattr(self.pca_analysis, 'scores_df') or not HAS_WEBENGINE or not self.plot_view:
            return
            
        plot_type = self.plot_type_combo.currentText()
        
        if plot_type == "Scores Plot":
            self.create_scores_plot()
        elif plot_type == "Loadings Plot":
            self.create_loadings_plot()
        elif plot_type == "Scree Plot":
            self.create_scree_plot()
            
    def create_scores_plot(self):
        """Create interactive scores plot"""
        scores_df = self.pca_analysis.scores_df
        
        fig = px.scatter(
            scores_df, 
            x='PC1', 
            y='PC2' if 'PC2' in scores_df.columns else 'PC1',
            color='pattern' if 'pattern' in scores_df.columns else None,
            hover_data=['sample_name'] if 'sample_name' in scores_df.columns else None,
            title="PCA Scores Plot"
        )
        
        fig.update_layout(
            width=800, 
            height=600,
            template="plotly_white"
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
        
    def create_loadings_plot(self):
        """Create interactive loadings plot"""
        loadings_df = self.pca_analysis.loadings_df
        masses = loadings_df.index.values
        pc1_loadings = loadings_df['PC1'].values
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=masses,
            y=pc1_loadings,
            name='PC1 Loadings',
            hovertemplate='m/z: %{x:.3f}<br>Loading: %{y:.6f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="PC1 Loadings",
            xaxis_title="m/z",
            yaxis_title="PC1 Loading",
            width=800,
            height=600,
            template="plotly_white"
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
        
    def create_scree_plot(self):
        """Create interactive scree plot"""
        variance_explained = self.pca_analysis.variance_explained
        components = [f'PC{i+1}' for i in range(len(variance_explained))]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=components,
            y=variance_explained,
            name='Variance Explained',
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="Scree Plot - Variance Explained by Principal Components",
            xaxis_title="Principal Component",
            yaxis_title="Variance Explained (%)",
            width=800,
            height=600,
            template="plotly_white"
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
        
    def generate_plots(self):
        """Generate all publication-quality plots"""
        if not hasattr(self.pca_analysis, 'scores_df'):
            QMessageBox.critical(self, "Error", "Please run PCA analysis first")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        worker = PlotWorker(self.pca_analysis, self.output_dir)
        worker.signals.progress.connect(self.update_status)
        worker.signals.result.connect(self.on_plots_completed)
        worker.signals.error.connect(self.on_plots_error)
        worker.signals.finished.connect(lambda: self.progress_bar.setVisible(False))
        
        self.thread_pool.start(worker)
        
    def on_plots_completed(self, plot_files):
        """Handle plot generation completion"""
        total_plots = sum(len(files) for files in plot_files.values())
        
        QMessageBox.information(
            self, "Success",
            f"Generated {total_plots} publication-quality plots!\n\n"
            f"Plots saved to:\n{self.output_dir}\n\n"
            f"Includes: scree plots, scores plots, loadings plots, and biplots"
        )
        
    def on_plots_error(self, error_message):
        """Handle plot generation error"""
        QMessageBox.critical(self, "Error", error_message)


def main():
    """Main function to run the GUI"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Set application properties
    app.setApplicationName("ToF-SIMS PCA Data Selector")
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = PCADataSelectorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()