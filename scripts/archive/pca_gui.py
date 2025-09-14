"""
Interactive GUI for ToF-SIMS PCA Data Selection
Allows users to select which patterns/squares to include in PCA analysis
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import os
import sys
from typing import List, Dict, Optional
import threading
import queue

# Import our existing PCA classes
from tof_sims_pca import ToFSIMSPCA
from tof_sims_plotting import ToFSIMSPlotter


class PCADataSelectorGUI:
    """
    GUI for selecting ToF-SIMS data for PCA analysis
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("ToF-SIMS PCA Data Selector")
        self.root.geometry("800x900")
        
        # Data storage
        self.data_file = None
        self.output_dir = None
        self.pca_analysis = None
        self.sample_info = None
        self.available_patterns = []
        self.available_squares = []
        
        # GUI state
        self.pattern_vars = {}
        self.square_vars = {}
        self.preprocessing_vars = {}
        
        # Progress tracking
        self.progress_queue = queue.Queue()
        self.progress_var = tk.StringVar(value="Ready to load data...")
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        
        # Main container with scrollable frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        current_row = 0
        
        # File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text="Data Files", padding="10")
        file_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        current_row += 1
        
        # Data file selection
        ttk.Label(file_frame, text="Data File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.data_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.data_file_var, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(file_frame, text="Browse", command=self.browse_data_file).grid(
            row=0, column=2, sticky=tk.W
        )
        
        # Output directory selection
        ttk.Label(file_frame, text="Output Dir:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.output_dir_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.output_dir_var, state="readonly").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        
        # Output directory buttons frame
        output_buttons_frame = ttk.Frame(file_frame)
        output_buttons_frame.grid(row=1, column=2, sticky=tk.W)
        
        ttk.Button(output_buttons_frame, text="Browse", command=self.browse_output_dir).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(output_buttons_frame, text="New Folder", command=self.create_new_output_dir).grid(
            row=0, column=1
        )
        
        # Load data button
        ttk.Button(file_frame, text="Load Data", command=self.load_data).grid(
            row=2, column=0, columnspan=3, pady=(10, 0)
        )
        
        # Ion type selection
        ion_frame = ttk.LabelFrame(main_frame, text="Ion Type", padding="10")
        ion_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        self.ion_type_var = tk.StringVar(value="negative")
        ttk.Radiobutton(ion_frame, text="Positive Ions", variable=self.ion_type_var, 
                       value="positive").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Radiobutton(ion_frame, text="Negative Ions", variable=self.ion_type_var, 
                       value="negative").grid(row=0, column=1, sticky=tk.W)
        
        # Pattern Selection Section
        self.pattern_frame = ttk.LabelFrame(main_frame, text="Pattern Selection", padding="10")
        self.pattern_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Square Selection Section  
        self.square_frame = ttk.LabelFrame(main_frame, text="Square Selection", padding="10")
        self.square_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Preprocessing Options
        preproc_frame = ttk.LabelFrame(main_frame, text="Preprocessing Options", padding="10")
        preproc_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        self.preprocessing_vars = {
            'sqrt_transform': tk.BooleanVar(value=False),
            'mean_center': tk.BooleanVar(value=False),
            'scale_data': tk.BooleanVar(value=False)
        }
        
        ttk.Checkbutton(preproc_frame, text="Square Root Transform", 
                       variable=self.preprocessing_vars['sqrt_transform']).grid(
                           row=0, column=0, sticky=tk.W, pady=2
                       )
        ttk.Checkbutton(preproc_frame, text="Mean Center", 
                       variable=self.preprocessing_vars['mean_center']).grid(
                           row=1, column=0, sticky=tk.W, pady=2
                       )
        ttk.Checkbutton(preproc_frame, text="Scale Data", 
                       variable=self.preprocessing_vars['scale_data']).grid(
                           row=2, column=0, sticky=tk.W, pady=2
                       )
        
        # PCA Options
        pca_frame = ttk.LabelFrame(main_frame, text="PCA Options", padding="10")
        pca_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        ttk.Label(pca_frame, text="Number of Components:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.n_components_var = tk.IntVar(value=8)
        ttk.Spinbox(pca_frame, from_=2, to=20, textvariable=self.n_components_var, width=5).grid(
            row=0, column=1, sticky=tk.W
        )
        
        # Analysis Controls
        control_frame = ttk.LabelFrame(main_frame, text="Analysis", padding="10")
        control_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        ttk.Button(control_frame, text="Run PCA Analysis", 
                  command=self.run_pca_analysis, style="Accent.TButton").grid(
                      row=0, column=0, padx=(0, 10)
                  )
        ttk.Button(control_frame, text="Generate Plots", 
                  command=self.generate_plots).grid(row=0, column=1)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        progress_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        current_row += 1
        
        ttk.Label(progress_frame, textvariable=self.progress_var, wraplength=750).grid(
            row=0, column=0, sticky=(tk.W, tk.E)
        )
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Results Display Section (initially hidden)
        self.results_frame = ttk.LabelFrame(main_frame, text="PCA Results", padding="10")
        self.results_frame.grid(row=current_row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=1)  # Make tables expandable
        current_row += 1
        
        # Configure main frame to allow results section to expand
        main_frame.rowconfigure(current_row-1, weight=1)
        
        # Results summary
        self.results_summary_var = tk.StringVar()
        ttk.Label(self.results_frame, textvariable=self.results_summary_var, 
                 font=('TkDefaultFont', 9, 'bold')).grid(
            row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        
        # Create notebook for tabbed results display
        self.results_notebook = ttk.Notebook(self.results_frame)
        self.results_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # PC1 Scores Tab
        self.scores_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.scores_frame, text="PC1 Scores")
        self._create_scores_table()
        
        # PC1 Loadings Tab  
        self.loadings_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.loadings_frame, text="PC1 Loadings (Top 20)")
        self._create_loadings_table()
        
        # Initially hide results
        self.results_frame.grid_remove()
        
        # Initially disable selection frames
        self._set_selection_state("disabled")
        
    def _create_scores_table(self):
        """Create table for displaying PC1 scores"""
        # Create treeview for scores
        columns = ('Sample', 'Pattern', 'Square', 'PC1 Score')
        self.scores_tree = ttk.Treeview(self.scores_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        self.scores_tree.heading('Sample', text='Sample Name')
        self.scores_tree.heading('Pattern', text='Pattern')  
        self.scores_tree.heading('Square', text='Square')
        self.scores_tree.heading('PC1 Score', text='PC1 Score')
        
        self.scores_tree.column('Sample', width=150)
        self.scores_tree.column('Pattern', width=80)
        self.scores_tree.column('Square', width=80)
        self.scores_tree.column('PC1 Score', width=100)
        
        # Add scrollbars
        scores_v_scrollbar = ttk.Scrollbar(self.scores_frame, orient="vertical", command=self.scores_tree.yview)
        scores_h_scrollbar = ttk.Scrollbar(self.scores_frame, orient="horizontal", command=self.scores_tree.xview)
        self.scores_tree.configure(yscrollcommand=scores_v_scrollbar.set, xscrollcommand=scores_h_scrollbar.set)
        
        # Grid layout
        self.scores_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scores_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scores_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        self.scores_frame.columnconfigure(0, weight=1)
        self.scores_frame.rowconfigure(0, weight=1)
        
    def _create_loadings_table(self):
        """Create table for displaying PC1 top loadings"""
        # Create treeview for loadings
        columns = ('Rank', 'Mass', 'Loading', 'Abs Loading')
        self.loadings_tree = ttk.Treeview(self.loadings_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        self.loadings_tree.heading('Rank', text='Rank')
        self.loadings_tree.heading('Mass', text='m/z')
        self.loadings_tree.heading('Loading', text='PC1 Loading')
        self.loadings_tree.heading('Abs Loading', text='|Loading|')
        
        self.loadings_tree.column('Rank', width=60)
        self.loadings_tree.column('Mass', width=100)
        self.loadings_tree.column('Loading', width=120)
        self.loadings_tree.column('Abs Loading', width=100)
        
        # Add scrollbars
        loadings_v_scrollbar = ttk.Scrollbar(self.loadings_frame, orient="vertical", command=self.loadings_tree.yview)
        loadings_h_scrollbar = ttk.Scrollbar(self.loadings_frame, orient="horizontal", command=self.loadings_tree.xview)
        self.loadings_tree.configure(yscrollcommand=loadings_v_scrollbar.set, xscrollcommand=loadings_h_scrollbar.set)
        
        # Grid layout
        self.loadings_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        loadings_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        loadings_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        self.loadings_frame.columnconfigure(0, weight=1)
        self.loadings_frame.rowconfigure(0, weight=1)

    def browse_data_file(self):
        """Browse for data file"""
        filename = filedialog.askopenfilename(
            title="Select ToF-SIMS Data File",
            filetypes=[("Text files", "*.txt"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.data_file_var.set(filename)
            self.data_file = filename
            
    def browse_output_dir(self):
        """Browse for output directory"""
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_dir_var.set(dirname)
            self.output_dir = dirname
            
    def create_new_output_dir(self):
        """Create a new output directory"""
        # First, let user select parent directory
        parent_dir = filedialog.askdirectory(title="Select Parent Directory for New Folder")
        if not parent_dir:
            return
            
        # Dialog to get new folder name
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Output Folder")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content frame
        content_frame = ttk.Frame(dialog, padding="20")
        content_frame.pack(fill="both", expand=True)
        
        ttk.Label(content_frame, text="Enter folder name:").pack(pady=(0, 10))
        
        folder_name_var = tk.StringVar(value="pca_output")
        entry = ttk.Entry(content_frame, textvariable=folder_name_var, width=30)
        entry.pack(pady=(0, 20))
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        # Button frame
        button_frame = ttk.Frame(content_frame)
        button_frame.pack()
        
        def create_folder():
            folder_name = folder_name_var.get().strip()
            if not folder_name:
                messagebox.showerror("Error", "Please enter a folder name")
                return
                
            # Remove invalid characters
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                folder_name = folder_name.replace(char, '_')
                
            new_dir = os.path.join(parent_dir, folder_name)
            
            try:
                os.makedirs(new_dir, exist_ok=True)
                self.output_dir_var.set(new_dir)
                self.output_dir = new_dir
                dialog.destroy()
                messagebox.showinfo("Success", f"Created output directory:\n{new_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create directory:\n{str(e)}")
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Create", command=create_folder).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side="left")
        
        # Bind Enter key to create folder
        entry.bind('<Return>', lambda e: create_folder())
            
    def load_data(self):
        """Load data file and populate selection options"""
        if not self.data_file or not self.output_dir:
            messagebox.showerror("Error", "Please select both data file and output directory")
            return
            
        try:
            self.progress_var.set("Loading data file...")
            self.progress_bar.start()
            
            # Create PCA analysis object
            positive_ions = self.ion_type_var.get() == "positive"
            self.pca_analysis = ToFSIMSPCA(self.data_file, self.output_dir, positive_ions)
            
            # Load the data
            self.pca_analysis.load_data()
            self.sample_info = self.pca_analysis.sample_info
            
            # Extract available patterns and squares
            self.available_patterns = sorted(self.sample_info['pattern_num'].unique())
            self.available_squares = sorted(self.sample_info['square_num'].unique())
            
            # Populate selection widgets
            self._populate_pattern_selection()
            self._populate_square_selection()
            
            # Enable selection frames
            self._set_selection_state("normal")
            
            self.progress_var.set(f"Data loaded successfully! Found {len(self.sample_info)} samples with "
                                f"{len(self.available_patterns)} patterns and {len(self.available_squares)} squares.")
            self.progress_bar.stop()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_var.set(f"Error loading data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            
    def _populate_pattern_selection(self):
        """Populate pattern selection checkboxes"""
        # Clear existing widgets
        for widget in self.pattern_frame.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.destroy()
                
        # Add "Select All" / "Deselect All" buttons
        button_frame = ttk.Frame(self.pattern_frame)
        button_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="Select All Patterns", 
                  command=self._select_all_patterns).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Deselect All Patterns", 
                  command=self._deselect_all_patterns).grid(row=0, column=1)
        
        # Create checkboxes for each pattern
        self.pattern_vars = {}
        row, col = 1, 0
        for i, pattern in enumerate(self.available_patterns):
            var = tk.BooleanVar(value=True)  # Default to selected
            self.pattern_vars[pattern] = var
            
            # Get sample count for this pattern
            sample_count = len(self.sample_info[self.sample_info['pattern_num'] == pattern])
            
            ttk.Checkbutton(self.pattern_frame, 
                           text=f"Pattern {pattern} ({sample_count} samples)", 
                           variable=var).grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            
            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1
                
    def _populate_square_selection(self):
        """Populate square selection checkboxes"""
        # Clear existing widgets
        for widget in self.square_frame.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.destroy()
                
        # Add "Select All" / "Deselect All" buttons
        button_frame = ttk.Frame(self.square_frame)
        button_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="Select All Squares", 
                  command=self._select_all_squares).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Deselect All Squares", 
                  command=self._deselect_all_squares).grid(row=0, column=1)
        
        # Create checkboxes for each square
        self.square_vars = {}
        row, col = 1, 0
        for i, square in enumerate(self.available_squares):
            var = tk.BooleanVar(value=True)  # Default to selected
            self.square_vars[square] = var
            
            # Get sample count for this square
            sample_count = len(self.sample_info[self.sample_info['square_num'] == square])
            
            ttk.Checkbutton(self.square_frame, 
                           text=f"Square {square} ({sample_count} samples)", 
                           variable=var).grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
                
    def _select_all_patterns(self):
        """Select all patterns"""
        for var in self.pattern_vars.values():
            var.set(True)
            
    def _deselect_all_patterns(self):
        """Deselect all patterns"""
        for var in self.pattern_vars.values():
            var.set(False)
            
    def _select_all_squares(self):
        """Select all squares"""
        for var in self.square_vars.values():
            var.set(True)
            
    def _deselect_all_squares(self):
        """Deselect all squares"""
        for var in self.square_vars.values():
            var.set(False)
            
    def _set_selection_state(self, state):
        """Enable/disable selection frames"""
        for frame in [self.pattern_frame, self.square_frame]:
            for child in frame.winfo_children():
                if hasattr(child, 'configure'):
                    try:
                        child.configure(state=state)
                    except tk.TclError:
                        pass  # Some widgets don't support state
                        
    def _get_selected_samples(self) -> List[str]:
        """Get list of selected sample names based on pattern/square selection"""
        if not self.sample_info is not None:
            return []
            
        # Get selected patterns and squares
        selected_patterns = [p for p, var in self.pattern_vars.items() if var.get()]
        selected_squares = [s for s, var in self.square_vars.items() if var.get()]
        
        if not selected_patterns or not selected_squares:
            return []
            
        # Filter samples based on selections
        mask = (self.sample_info['pattern_num'].isin(selected_patterns) & 
                self.sample_info['square_num'].isin(selected_squares))
        
        return self.sample_info[mask]['sample_name'].tolist()
        
    def run_pca_analysis(self):
        """Run PCA analysis with selected parameters"""
        if self.pca_analysis is None:
            messagebox.showerror("Error", "Please load data first")
            return
            
        selected_samples = self._get_selected_samples()
        if not selected_samples:
            messagebox.showerror("Error", "No samples selected. Please select at least one pattern and square.")
            return
            
        # Run analysis in separate thread to prevent GUI freezing
        threading.Thread(target=self._run_pca_thread, args=(selected_samples,), daemon=True).start()
        
    def _run_pca_thread(self, selected_samples: List[str]):
        """Run PCA analysis in separate thread"""
        try:
            # Update progress
            self.progress_var.set("Filtering selected samples...")
            self.progress_bar.start()
            
            # Filter samples in the PCA analysis object
            # We need to manually filter since the existing select_samples method works with patterns
            selected_mask = self.pca_analysis.sample_info['sample_name'].isin(selected_samples)
            self.pca_analysis.raw_data = self.pca_analysis.raw_data[selected_samples]
            self.pca_analysis.sample_info = self.pca_analysis.sample_info[selected_mask].reset_index(drop=True)
            
            self.progress_var.set(f"Selected {len(selected_samples)} samples for analysis...")
            
            # Preprocess data
            self.progress_var.set("Preprocessing data...")
            self.pca_analysis.preprocess_data(
                sqrt_transform=self.preprocessing_vars['sqrt_transform'].get(),
                mean_center=self.preprocessing_vars['mean_center'].get(),
                scale_data=self.preprocessing_vars['scale_data'].get()
            )
            
            # Run PCA
            self.progress_var.set("Running PCA analysis...")
            n_components = self.n_components_var.get()
            self.pca_analysis.run_pca(n_components=n_components)
            
            # Export results
            self.progress_var.set("Exporting results...")
            self.pca_analysis.export_results()
            
            self.progress_bar.stop()
            self.progress_var.set(f"PCA analysis completed successfully! Results saved to {self.output_dir}")
            
            # Update results display
            self.root.after(0, self._update_results_display)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"PCA analysis completed!\n\nResults saved to:\n{self.output_dir}\n\n"
                f"Analyzed {len(selected_samples)} samples\n"
                f"Computed {n_components} principal components"))
            
        except Exception as e:
            self.progress_bar.stop()
            error_msg = f"PCA analysis failed: {str(e)}"
            self.progress_var.set(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
    def generate_plots(self):
        """Generate all PCA plots"""
        if self.pca_analysis is None or not hasattr(self.pca_analysis, 'scores_df'):
            messagebox.showerror("Error", "Please run PCA analysis first")
            return
            
        threading.Thread(target=self._generate_plots_thread, daemon=True).start()
        
    def _generate_plots_thread(self):
        """Generate plots in separate thread"""
        try:
            self.progress_var.set("Generating publication-quality plots...")
            self.progress_bar.start()
            
            # Create plotter
            plotter = ToFSIMSPlotter(self.output_dir)
            
            # Generate all plots
            plot_files = plotter.create_all_plots(
                scores_df=self.pca_analysis.scores_df,
                loadings_df=self.pca_analysis.loadings_df,
                variance_explained=self.pca_analysis.variance_explained,
                max_components=min(5, self.n_components_var.get())
            )
            
            self.progress_bar.stop()
            self.progress_var.set(f"All plots generated successfully! Saved to {self.output_dir}")
            
            # Count total plots
            total_plots = sum(len(files) for files in plot_files.values())
            
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"Generated {total_plots} publication-quality plots!\n\n"
                f"Plots saved to:\n{self.output_dir}\n\n"
                f"Includes: scree plots, scores plots, loadings plots, and biplots"))
            
        except Exception as e:
            self.progress_bar.stop()
            error_msg = f"Plot generation failed: {str(e)}"
            self.progress_var.set(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
    def _update_results_display(self):
        """Update the results display with PC1 scores and loadings"""
        if not hasattr(self.pca_analysis, 'scores_df') or not hasattr(self.pca_analysis, 'loadings_df'):
            return
            
        try:
            # Show results frame
            self.results_frame.grid()
            
            # Update summary
            pc1_variance = self.pca_analysis.variance_explained[0] if len(self.pca_analysis.variance_explained) > 0 else 0
            n_samples = len(self.pca_analysis.scores_df)
            summary_text = f"PCA Results Summary - PC1 explains {pc1_variance:.1f}% of variance ({n_samples} samples)"
            self.results_summary_var.set(summary_text)
            
            # Update scores table
            self._populate_scores_table()
            
            # Update loadings table
            self._populate_loadings_table()
            
        except Exception as e:
            print(f"Error updating results display: {e}")
            
    def _populate_scores_table(self):
        """Populate the scores table with PC1 data"""
        # Clear existing data
        for item in self.scores_tree.get_children():
            self.scores_tree.delete(item)
            
        if not hasattr(self.pca_analysis, 'scores_df'):
            return
            
        # Sort by PC1 score (highest to lowest)
        scores_data = self.pca_analysis.scores_df.copy()
        scores_data = scores_data.sort_values('PC1', ascending=False)
        
        # Insert data into table
        for idx, row in scores_data.iterrows():
            sample_name = row['sample_name'] if 'sample_name' in row else str(idx)
            pattern = row['pattern'] if 'pattern' in row else 'N/A'
            
            # Extract square from sample name if available
            square = 'N/A'
            if 'square' in row:
                square = row['square']
            elif '_SQ' in sample_name:
                try:
                    square = sample_name.split('_SQ')[1].split('_')[0]
                    square = f"SQ{square}"
                except:
                    pass
            
            pc1_score = f"{row['PC1']:.4f}"
            
            self.scores_tree.insert('', 'end', values=(
                sample_name, pattern, square, pc1_score
            ))
            
    def _populate_loadings_table(self):
        """Populate the loadings table with PC1 top contributing masses"""
        # Clear existing data
        for item in self.loadings_tree.get_children():
            self.loadings_tree.delete(item)
            
        if not hasattr(self.pca_analysis, 'loadings_df'):
            return
            
        # Get PC1 loadings
        pc1_loadings = self.pca_analysis.loadings_df['PC1']
        masses = self.pca_analysis.loadings_df.index.values
        
        # Sort by absolute loading values (highest to lowest)
        abs_loadings = np.abs(pc1_loadings.values)
        sorted_indices = np.argsort(abs_loadings)[::-1]
        
        # Take top 20
        top_indices = sorted_indices[:20]
        
        # Insert data into table
        for rank, idx in enumerate(top_indices, 1):
            mass = f"{masses[idx]:.3f}"
            loading = f"{pc1_loadings.iloc[idx]:.6f}"
            abs_loading = f"{abs_loadings[idx]:.6f}"
            
            self.loadings_tree.insert('', 'end', values=(
                rank, mass, loading, abs_loading
            ))


def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    
    # Configure ttk style
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme
    
    # Create custom style for accent button
    style.configure("Accent.TButton", foreground="white", background="#0078d4")
    
    app = PCADataSelectorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()