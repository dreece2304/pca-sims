"""
Data Preview Dialog for ToF-SIMS PCA Application
Shows file structure and content before loading
"""

import os
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QTextEdit, QTabWidget,
    QWidget, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer

class DataPreviewDialog(QDialog):
    """Dialog to preview data file before loading"""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.data = None
        self.accepted_data = False
        
        self.setWindowTitle(f"Data Preview - {file_path.split('/')[-1]}")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_preview()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # File info
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        
        # Data preview tab
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        
        data_layout.addWidget(QLabel("Data Preview (first 10 rows):"))
        self.data_table = QTableWidget()
        data_layout.addWidget(self.data_table)
        
        self.tabs.addTab(self.data_tab, "Data Preview")
        
        # File info tab
        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)
        
        info_layout.addWidget(QLabel("File Analysis:"))
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        self.tabs.addTab(self.info_tab, "File Info")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Load This File")
        self.load_button.clicked.connect(self.accept_data)
        self.load_button.setEnabled(False)
        button_layout.addWidget(self.load_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_preview(self):
        """Load file preview"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # Update info
            file_size = os.path.getsize(self.file_path) / (1024 * 1024)  # MB
            self.info_label.setText(f"File: {self.file_path.split('/')[-1]} ({file_size:.2f} MB)")
            
            # Try to detect file format and load preview
            QTimer.singleShot(100, self._load_data_async)
            
        except Exception as e:
            self.show_error(f"Failed to analyze file: {e}")
    
    def _load_data_async(self):
        """Load data asynchronously"""
        try:
            # Detect delimiter
            delimiter = self.detect_delimiter()
            
            # Read first few rows for preview
            preview_data = pd.read_csv(
                self.file_path, 
                delimiter=delimiter, 
                nrows=10,
                header=0
            )
            
            # Read full header info
            full_data = pd.read_csv(
                self.file_path,
                delimiter=delimiter,
                nrows=0  # Just header
            )
            
            # Store data info
            self.data = {
                'delimiter': delimiter,
                'columns': list(full_data.columns),
                'preview': preview_data
            }
            
            # Update UI
            self.populate_preview_table(preview_data)
            self.generate_file_info()
            
            self.progress_bar.setVisible(False)
            self.load_button.setEnabled(True)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.show_error(f"Failed to load file preview: {e}")
    
    def detect_delimiter(self):
        """Detect file delimiter"""
        try:
            # Read first few lines to detect delimiter
            with open(self.file_path, 'r') as f:
                first_lines = [f.readline() for _ in range(3)]
            
            # Test common delimiters
            delimiters = ['\t', ',', ';', ' ']
            delimiter_counts = {}
            
            for delimiter in delimiters:
                count = sum(line.count(delimiter) for line in first_lines)
                delimiter_counts[delimiter] = count
            
            # Return delimiter with highest count
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            return best_delimiter if delimiter_counts[best_delimiter] > 0 else '\t'
            
        except:
            return '\t'  # Default to tab
    
    def populate_preview_table(self, data):
        """Populate the preview table"""
        self.data_table.setRowCount(len(data))
        self.data_table.setColumnCount(len(data.columns))
        self.data_table.setHorizontalHeaderLabels([str(col) for col in data.columns])
        
        for row in range(len(data)):
            for col in range(len(data.columns)):
                value = data.iloc[row, col]
                # Format numeric values
                if pd.api.types.is_numeric_dtype(type(value)):
                    if isinstance(value, float):
                        item_text = f"{value:.6g}"
                    else:
                        item_text = str(value)
                else:
                    item_text = str(value)
                
                item = QTableWidgetItem(item_text)
                self.data_table.setItem(row, col, item)
        
        # Resize columns to content
        self.data_table.resizeColumnsToContents()
    
    def generate_file_info(self):
        """Generate file information text"""
        try:
            # Get full file info
            full_data = pd.read_csv(self.file_path, delimiter=self.data['delimiter'])
            
            delimiter_display = 'Tab' if self.data['delimiter'] == '\t' else repr(self.data['delimiter'])
            info_text = f"""File Analysis Report
{'=' * 50}

Basic Information:
  • File path: {self.file_path}
  • Delimiter: {delimiter_display}
  • Total rows: {len(full_data):,}
  • Total columns: {len(full_data.columns)}
  • File size: {os.path.getsize(self.file_path) / (1024 * 1024):.2f} MB

Column Analysis:
"""
            
            # Analyze each column
            for i, col in enumerate(full_data.columns):
                col_data = full_data[col]
                
                # Determine column type
                if pd.api.types.is_numeric_dtype(col_data):
                    col_type = "Numeric"
                    stats = f"Range: {col_data.min():.3g} to {col_data.max():.3g}"
                    missing = col_data.isna().sum()
                else:
                    col_type = "Text/Categorical"
                    unique_count = col_data.nunique()
                    stats = f"Unique values: {unique_count}"
                    missing = col_data.isna().sum()
                
                info_text += f"""
  Column {i+1}: {col}
    Type: {col_type}
    {stats}
    Missing values: {missing}"""
            
            # Data structure recommendations
            info_text += f"""

ToF-SIMS Data Structure Assessment:
{'=' * 50}

Expected Structure:
  • First column: Mass values (m/z)
  • Remaining columns: Sample intensities
  • Column names: Sample identifiers

Assessment:
"""
            
            # Check if structure looks like ToF-SIMS data
            first_col = full_data.iloc[:, 0]
            if pd.api.types.is_numeric_dtype(first_col):
                if first_col.min() > 0 and first_col.max() < 1000:
                    info_text += "  ✅ First column appears to be mass values (m/z)\n"
                else:
                    info_text += "  ⚠️  First column is numeric but range seems unusual for m/z\n"
            else:
                info_text += "  ❌ First column is not numeric - may not be standard ToF-SIMS format\n"
            
            # Check sample columns
            numeric_cols = sum(1 for col in full_data.columns[1:] if pd.api.types.is_numeric_dtype(full_data[col]))
            total_sample_cols = len(full_data.columns) - 1
            
            if numeric_cols == total_sample_cols:
                info_text += f"  ✅ All {total_sample_cols} sample columns are numeric\n"
            else:
                info_text += f"  ⚠️  Only {numeric_cols}/{total_sample_cols} sample columns are numeric\n"
            
            # Recommendations
            info_text += f"""
Recommendations:
  • Expected: Mass column + sample intensity columns
  • Found: {len(full_data.columns)} columns ({numeric_cols + (1 if pd.api.types.is_numeric_dtype(full_data.iloc[:, 0]) else 0)} numeric)
  • This {'appears to be' if numeric_cols > 0 else 'may not be'} compatible ToF-SIMS data
"""
            
            self.info_text.setPlainText(info_text)
            
        except Exception as e:
            self.info_text.setPlainText(f"Error analyzing file: {e}")
    
    def accept_data(self):
        """Accept the data and close dialog"""
        self.accepted_data = True
        self.accept()
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Preview Error", message)
        self.reject()
    
    def get_data_info(self):
        """Get data information for loading"""
        return self.data if self.accepted_data else None