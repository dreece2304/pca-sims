"""
PySide6 ToF-SIMS PCA Application with Native Matplotlib Plotting
Better performance and reliability than QtWebEngine approach
"""

import sys
import os
from pathlib import Path

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
    QScrollArea, QFrame
)
from PySide6.QtCore import QThread, Signal, Qt, QSettings
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


class ToFSIMSPCAApp(QMainWindow):
    """Main PySide6 ToF-SIMS PCA Application with Matplotlib"""
    
    def __init__(self):
        super().__init__()
        self.pca_analyzer = None
        self.pca_completed = False
        
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
        
        # Create UI
        self.init_ui()
        self.create_menu_bar()
        
        print("🚀 PySide6 ToF-SIMS PCA Application (Matplotlib) Initialized")
    
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
        
        self.mean_checkbox = QCheckBox("Mean Center")
        self.mean_checkbox.setChecked(True)
        self.mean_checkbox.setToolTip("Required for covariance-based PCA")
        
        self.pareto_checkbox = QCheckBox("Pareto Scale")
        self.pareto_checkbox.setChecked(True)
        self.pareto_checkbox.setToolTip("Balances large vs small peaks")
        
        layout.addWidget(self.sqrt_checkbox, 0, 0)
        layout.addWidget(self.mean_checkbox, 0, 1)
        layout.addWidget(self.pareto_checkbox, 1, 0, 1, 2)
        
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

        # Fragment Trends tab
        self.trends_widget = self.create_fragment_trends_tab()
        self.plot_tabs.addTab(self.trends_widget, "Fragment Trends")

        # Molecular Calculator tab
        self.calculator_widget = self.create_molecular_calculator_tab()
        self.plot_tabs.addTab(self.calculator_widget, "MW Calculator")

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
        """Load data from file"""
        try:
            self.data_status.setText("Loading data...")
            
            # Initialize PCA analyzer
            self.pca_analyzer = SimpleToFSIMSPCA(file_path)
            self.pca_analyzer.load_data()
            
            # Update UI
            self.file_label.setText(os.path.basename(file_path))
            self.data_status.setText(f"✅ Loaded: {len(self.pca_analyzer.mass_values)} masses, {len(self.pca_analyzer.raw_data.columns)} samples")
            self.run_button.setEnabled(True)
            self.pca_completed = False
            
            # Add to recent files
            self.add_recent_file(file_path)
            
            # Populate sample management table
            self.populate_sample_table()
            
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
            'mean_center': self.mean_checkbox.isChecked(),
            'pareto_scale': self.pareto_checkbox.isChecked()
        }

        # Apply sample selection based on checkboxes
        selected_samples, display_names = self.get_selected_samples()

        if not selected_samples:
            QMessageBox.warning(self, "No Samples Selected",
                              "Please select at least one sample for analysis.")
            return

        if len(selected_samples) < 3:
            QMessageBox.warning(self, "Insufficient Samples",
                              "Please select at least 3 samples for meaningful PCA analysis.")
            return

        # Filter data to selected samples before PCA
        try:
            # Store original data for potential restoration
            if not hasattr(self, 'original_raw_data'):
                self.original_raw_data = self.pca_analyzer.raw_data.copy()

            # Filter data to selected samples
            selected_data = self.original_raw_data[selected_samples]

            # Rename columns to display names
            column_rename_map = {original: display_names[original] for original in selected_samples}
            selected_data_renamed = selected_data.rename(columns=column_rename_map)

            self.pca_analyzer.raw_data = selected_data_renamed

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
                            f"√Transform: {self.sqrt_checkbox.isChecked()}, Mean Center: {self.mean_checkbox.isChecked()}, Pareto Scale: {self.pareto_checkbox.isChecked()}"
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

        # Backup original data for sample selection operations
        self.original_raw_data = self.pca_analyzer.raw_data.copy()

        # Get sample names from data columns (excluding first column which is masses)
        sample_names = list(self.pca_analyzer.raw_data.columns)
        
        # Create pattern and square selection checkboxes
        self.create_pattern_square_checkboxes(sample_names)
        
        # Start with all groups selected
        self.selected_patterns = set(self.pattern_checkboxes.keys())
        self.selected_squares = set(self.square_checkboxes.keys())
        
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
    
    def get_selected_samples(self):
        """Get list of selected samples based on group selection"""
        if not self.pca_analyzer:
            return [], {}
        
        selected_samples = []
        display_names = {}
        
        # Get all sample names
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
        
        # Update analyzer with selected samples and display names
        try:
            # Use original data for consistent filtering
            if not hasattr(self, 'original_raw_data'):
                self.original_raw_data = self.pca_analyzer.raw_data.copy()

            # Filter data to selected samples from original data
            selected_data = self.original_raw_data[selected_samples]
            
            # Create a copy of the analyzer with filtered data
            # Rename columns to display names
            column_rename_map = {original: display_names[original] for original in selected_samples}
            selected_data_renamed = selected_data.rename(columns=column_rename_map)
            
            self.pca_analyzer.raw_data = selected_data_renamed
            
            # Update sample metadata with display names
            sample_metadata = []
            for original_name in selected_samples:
                display_name = display_names[original_name]
                
                # Try to extract dose information from name
                dose_id = self.extract_dose_from_name(display_name)
                
                sample_metadata.append({
                    'sample_name': display_name,
                    'original_name': original_name,
                    'dose_id': dose_id
                })
            
            # Update analyzer metadata
            import pandas as pd
            self.pca_analyzer.sample_metadata = pd.DataFrame(sample_metadata)
            
            # Reset PCA completion flag
            self.pca_completed = False
            
            # Reset button styling
            self.update_analysis_button.setText("Update Analysis")
            self.update_analysis_button.setStyleSheet("")
            
            self.data_status.setText(f"✅ Updated: {len(selected_samples)} samples selected")
            
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


    def create_fragment_trends_tab(self):
        """Create Fragment Trends analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("📈 Fragment Intensity Trends")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Fragment selection area
        selection_group = QGroupBox("Fragment Selection")
        selection_layout = QHBoxLayout(selection_group)

        # Fragment list (will be populated from PCA loadings)
        self.fragment_list = QListWidget()
        self.fragment_list.setMaximumHeight(150)
        selection_layout.addWidget(QLabel("Select Fragments:"))
        selection_layout.addWidget(self.fragment_list)

        # Refresh button to sync with PCA tab
        refresh_btn = QPushButton("🔄 Sync with PCA")
        refresh_btn.clicked.connect(self.refresh_fragment_list)
        selection_layout.addWidget(refresh_btn)

        layout.addWidget(selection_group)

        # Plotting area
        self.trends_canvas = PCAPlotCanvas(widget, width=10, height=6)
        self.trends_toolbar = NavigationToolbar(self.trends_canvas, widget)

        layout.addWidget(self.trends_toolbar)
        layout.addWidget(self.trends_canvas)

        # Plot button
        plot_trends_btn = QPushButton("📊 Plot Selected Fragments")
        plot_trends_btn.clicked.connect(self.plot_fragment_trends)
        layout.addWidget(plot_trends_btn)

        return widget

    def create_molecular_calculator_tab(self):
        """Create Molecular Weight Calculator tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("⚛️ Molecular Weight Calculator & Fragment Assignment")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Input section
        input_group = QGroupBox("Fragment Analysis Input")
        input_layout = QFormLayout(input_group)

        # M/Z input
        self.mz_input = QLineEdit()
        self.mz_input.setPlaceholderText("Enter m/z value (e.g., 19.023)")
        input_layout.addRow("m/z Value:", self.mz_input)

        # Polarity selection
        self.polarity_combo = QComboBox()
        self.polarity_combo.addItems(["Negative", "Positive"])
        input_layout.addRow("Ion Mode:", self.polarity_combo)

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

        # Contamination filter section
        filter_group = QGroupBox("🚫 Contamination Filtering for PCA")
        filter_layout = QVBoxLayout(filter_group)

        filter_info = QLabel("Exclude contamination peaks from PCA analysis:")
        filter_layout.addWidget(filter_info)

        # Contamination checkboxes
        contam_layout = QHBoxLayout()
        self.filter_F = QCheckBox("Exclude F- (m/z 19)")
        self.filter_Cl = QCheckBox("Exclude Cl- (m/z 35)")
        self.filter_Si = QCheckBox("Exclude Si+ (m/z 28)")

        contam_layout.addWidget(self.filter_F)
        contam_layout.addWidget(self.filter_Cl)
        contam_layout.addWidget(self.filter_Si)
        filter_layout.addLayout(contam_layout)

        # Apply filters button
        apply_filter_btn = QPushButton("🔄 Re-run PCA with Filters")
        apply_filter_btn.clicked.connect(self.apply_contamination_filters)
        filter_layout.addWidget(apply_filter_btn)

        layout.addWidget(filter_group)

        return widget

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
                item_text = f"m/z {mass:.3f} (loading: {original_loading:+.3f})"
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
            # Get current sample selection (same as PCA tab)
            selected_samples, display_names = self.get_selected_samples()
            if not selected_samples:
                QMessageBox.information(self, "No Samples Selected", "No samples selected in PCA tab.")
                return

            # Get raw data for selected samples
            data_subset = self.original_raw_data[selected_samples]

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

                    # Group by dose if available
                    sample_names = selected_samples
                    doses = []
                    for sample in sample_names:
                        pattern, square = self.parse_sample_name(sample)
                        # Extract dose number from square (e.g., SQ1 -> 1)
                        dose_num = int(square[2:]) if square.startswith('SQ') and square[2:].isdigit() else 0
                        doses.append(dose_num)

                    ax.plot(doses, intensities, 'o-', label=f'm/z {mass:.3f}', linewidth=2, markersize=6)

            ax.set_xlabel("Dose Level", fontsize=12)
            ax.set_ylabel("Intensity", fontsize=12)
            ax.set_title("Fragment Intensity Trends", fontsize=14, fontweight='bold')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
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
            polarity = self.polarity_combo.currentText()

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

    def apply_contamination_filters(self):
        """Apply contamination filters and re-run PCA"""
        if self.original_raw_data is None:
            QMessageBox.information(self, "No Data", "Please load data first.")
            return

        try:
            # Get filter settings
            filters = []
            if self.filter_F.isChecked():
                filters.append(19.0)  # F- mass
            if self.filter_Cl.isChecked():
                filters.append(35.0)  # Cl- mass
            if self.filter_Si.isChecked():
                filters.append(28.0)  # Si+ mass

            if not filters:
                QMessageBox.information(self, "No Filters", "Please select contamination peaks to filter.")
                return

            # Filter data
            filtered_data = self.original_raw_data.copy()
            masses_to_remove = []

            for filter_mass in filters:
                # Find closest mass within 0.5 Da
                closest_masses = []
                for mass in filtered_data.index:
                    if abs(mass - filter_mass) <= 0.5:
                        closest_masses.append(mass)
                masses_to_remove.extend(closest_masses)

            # Remove contamination peaks
            if masses_to_remove:
                filtered_data = filtered_data.drop(masses_to_remove)
                self.pca_analyzer.raw_data = filtered_data

                QMessageBox.information(self, "Filters Applied",
                    f"Removed {len(masses_to_remove)} contamination peaks.\nPlease re-run PCA analysis.")

                # Reset PCA completion status
                self.pca_completed = False
                self.run_button.setEnabled(True)

                print(f"🚫 Filtered out masses: {[f'{m:.3f}' for m in masses_to_remove]}")
            else:
                QMessageBox.information(self, "No Peaks Found", "No contamination peaks found to filter.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply filters: {e}")


def main():
    """Main application entry point"""
    # Set Qt platform if not already set
    if 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    # Enable high DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    app = QApplication(sys.argv)
    
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
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()