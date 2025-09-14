"""
Web-based Interactive GUI for ToF-SIMS PCA Data Selection
Runs in browser - works perfectly in WSL environments
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import sys
from pathlib import Path
import io
import tempfile
import zipfile

# Import our existing PCA classes
from tof_sims_pca import ToFSIMSPCA
from tof_sims_plotting import ToFSIMSPlotter
from fragment_database import AluconeFragmentDatabase
from positive_fragment_database import AluconePositiveFragmentDatabase


def main():
    st.set_page_config(
        page_title="ToF-SIMS PCA Data Selector",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔬 ToF-SIMS PCA Data Selector")
    st.markdown("Interactive web-based tool for ToF-SIMS Principal Component Analysis")
    
    # Initialize session state
    if 'pca_analysis' not in st.session_state:
        st.session_state.pca_analysis = None
    if 'sample_info' not in st.session_state:
        st.session_state.sample_info = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'fragment_db' not in st.session_state:
        st.session_state.fragment_db = AluconeFragmentDatabase()
    if 'positive_fragment_db' not in st.session_state:
        st.session_state.positive_fragment_db = AluconePositiveFragmentDatabase()
    if 'ion_type' not in st.session_state:
        st.session_state.ion_type = "Negative Ions"
    
    # Sidebar for controls
    with st.sidebar:
        st.header("📁 Data Files")
        
        # File upload
        data_file = st.file_uploader(
            "Upload ToF-SIMS Data File",
            type=['txt', 'xlsx'],
            help="Select your ToF-SIMS data file"
        )
        
        # Output directory
        output_dir = st.text_input(
            "Output Directory",
            value=str(Path.cwd() / "outputs"),
            help="Directory where results will be saved"
        )
        
        # Create output directory button
        if st.button("📁 Create Output Directory"):
            try:
                os.makedirs(output_dir, exist_ok=True)
                st.success(f"Created directory: {output_dir}")
            except Exception as e:
                st.error(f"Error creating directory: {e}")
        
        st.header("⚙️ Analysis Options")
        
        # Ion type
        ion_type = st.radio(
            "Ion Type",
            ["Negative Ions", "Positive Ions"],
            index=0 if st.session_state.ion_type == "Negative Ions" else 1
        )
        
        # Update session state
        st.session_state.ion_type = ion_type
        
        # Show ion-specific information
        if ion_type == "Positive Ions":
            st.info("🔬 **Positive Ion Mode**\nExpected major fragments: Al+, AlO+, CH3+, C6H+, Si+")
        else:
            st.info("🔬 **Negative Ion Mode**\nVerified fragments: H-, Cl-, C6H-, COOH-, C4HO-")
        
        # Load data button
        if st.button("📊 Load Data", type="primary"):
            if data_file is not None:
                load_data(data_file, output_dir, ion_type == "Positive Ions")
            else:
                st.error("Please upload a data file first")
    
    # Main content area
    if st.session_state.data_loaded:
        show_data_selection()
        
        if st.session_state.analysis_complete:
            show_results()
    else:
        show_welcome()


def show_welcome():
    """Show welcome screen"""
    st.markdown("""
    ## Welcome to ToF-SIMS PCA Analysis Tool
    
    This interactive web application allows you to:
    
    ### 🎯 **Select Your Data**
    - Choose specific patterns and squares to include in your analysis
    - Filter out unwanted data points (e.g., omit data from specific squares)
    - Preview your selection before running analysis
    
    ### 🔬 **Configure Analysis**
    - Set preprocessing options (square root transform, mean centering, scaling)
    - Choose number of principal components
    - Customize analysis parameters
    
    ### 📊 **Interactive Results**
    - View PC1 scores and loadings in sortable tables
    - Explore interactive Plotly visualizations
    - Download publication-quality plots
    - Export results as CSV files
    
    ### 🚀 **Get Started**
    1. **Upload your data file** in the sidebar (txt or xlsx format)
    2. **Set output directory** where results will be saved
    3. **Click "Load Data"** to begin
    
    ---
    *This tool works perfectly in WSL, remote servers, and any browser!*
    """)


def load_data(data_file, output_dir, positive_ions):
    """Load and process data file"""
    with st.spinner("Loading data..."):
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt' if data_file.name.endswith('.txt') else '.xlsx') as tmp_file:
                tmp_file.write(data_file.getvalue())
                tmp_path = tmp_file.name
            
            # Create PCA analysis object
            pca_analysis = ToFSIMSPCA(tmp_path, output_dir, positive_ions)
            
            # Load the data
            pca_analysis.load_data()
            
            # Store in session state
            st.session_state.pca_analysis = pca_analysis
            st.session_state.sample_info = pca_analysis.sample_info
            st.session_state.data_loaded = True
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            st.success(f"✅ Data loaded successfully! Found {len(pca_analysis.sample_info)} samples")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")


def show_data_selection():
    """Show data selection interface"""
    sample_info = st.session_state.sample_info
    
    st.header("🎯 Sample Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Pattern Selection")
        
        available_patterns = sorted(sample_info['pattern_num'].unique())
        
        # Select all/none buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Select All Patterns"):
                st.session_state.selected_patterns = available_patterns
        with col_b:
            if st.button("Deselect All Patterns"):
                st.session_state.selected_patterns = []
        
        # Initialize selected patterns if not exists
        if 'selected_patterns' not in st.session_state:
            st.session_state.selected_patterns = available_patterns.copy()
        
        # Pattern checkboxes
        selected_patterns = []
        for pattern in available_patterns:
            sample_count = len(sample_info[sample_info['pattern_num'] == pattern])
            checked = pattern in st.session_state.selected_patterns
            
            if st.checkbox(f"Pattern {pattern} ({sample_count} samples)", value=checked, key=f"pattern_{pattern}"):
                selected_patterns.append(pattern)
        
        st.session_state.selected_patterns = selected_patterns
    
    with col2:
        st.subheader("🔲 Square Selection")
        
        available_squares = sorted(sample_info['square_num'].unique())
        
        # Select all/none buttons
        col_c, col_d = st.columns(2)
        with col_c:
            if st.button("Select All Squares"):
                st.session_state.selected_squares = available_squares
        with col_d:
            if st.button("Deselect All Squares"):
                st.session_state.selected_squares = []
        
        # Initialize selected squares if not exists
        if 'selected_squares' not in st.session_state:
            st.session_state.selected_squares = available_squares.copy()
        
        # Square checkboxes
        selected_squares = []
        for square in available_squares:
            sample_count = len(sample_info[sample_info['square_num'] == square])
            checked = square in st.session_state.selected_squares
            
            if st.checkbox(f"Square {square} ({sample_count} samples)", value=checked, key=f"square_{square}"):
                selected_squares.append(square)
        
        st.session_state.selected_squares = selected_squares
    
    # Show selection summary
    selected_samples = get_selected_samples()
    if selected_samples:
        st.success(f"✅ Selected {len(selected_samples)} samples for analysis")
    else:
        st.warning("⚠️ No samples selected. Please select at least one pattern and square.")
    
    # Preprocessing options
    st.header("🔧 Preprocessing Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sqrt_transform = st.checkbox("Square Root Transform", help="Apply square root transformation for variance stabilization")
    with col2:
        mean_center = st.checkbox("Mean Center", help="Center data around the mean")
    with col3:
        scale_data = st.checkbox("Scale Data", help="Standardize data (z-score normalization)")
    
    # PCA options
    st.header("🎛️ PCA Options")
    n_components = st.slider("Number of Components", min_value=2, max_value=20, value=8)
    
    # Run analysis button
    if st.button("🚀 Run PCA Analysis", type="primary", disabled=len(selected_samples)==0):
        run_pca_analysis(selected_samples, sqrt_transform, mean_center, scale_data, n_components)


def get_selected_samples():
    """Get list of selected sample names"""
    if 'selected_patterns' not in st.session_state or 'selected_squares' not in st.session_state:
        return []
    
    sample_info = st.session_state.sample_info
    selected_patterns = st.session_state.selected_patterns
    selected_squares = st.session_state.selected_squares
    
    if not selected_patterns or not selected_squares:
        return []
    
    mask = (
        sample_info['pattern_num'].isin(selected_patterns) & 
        sample_info['square_num'].isin(selected_squares)
    )
    
    return sample_info[mask]['sample_name'].tolist()


def run_pca_analysis(selected_samples, sqrt_transform, mean_center, scale_data, n_components):
    """Run PCA analysis"""
    with st.spinner("Running PCA analysis..."):
        try:
            pca_analysis = st.session_state.pca_analysis
            
            # Filter samples
            selected_mask = pca_analysis.sample_info['sample_name'].isin(selected_samples)
            pca_analysis.raw_data = pca_analysis.raw_data[selected_samples]
            pca_analysis.sample_info = pca_analysis.sample_info[selected_mask].reset_index(drop=True)
            
            # Preprocess data
            pca_analysis.preprocess_data(
                sqrt_transform=sqrt_transform,
                mean_center=mean_center,
                scale_data=scale_data
            )
            
            # Run PCA
            pca_analysis.run_pca(n_components=n_components)
            
            # Export results
            pca_analysis.export_results()
            
            st.session_state.pca_analysis = pca_analysis
            st.session_state.analysis_complete = True
            
            st.success(f"✅ PCA analysis completed! Analyzed {len(selected_samples)} samples with {n_components} components.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ PCA analysis failed: {str(e)}")


def show_results():
    """Show PCA results"""
    pca_analysis = st.session_state.pca_analysis
    
    st.header("📊 PCA Results")
    
    # Results summary
    pc1_variance = pca_analysis.variance_explained[0]
    n_samples = len(pca_analysis.scores_df)
    
    st.info(f"🎯 **PC1 explains {pc1_variance:.1f}% of variance** ({n_samples} samples analyzed)")
    
    # Show crosslinking analysis summary at top
    # Use appropriate fragment database based on ion type
    if st.session_state.ion_type == "Positive Ions":
        current_fragment_db = st.session_state.positive_fragment_db
    else:
        current_fragment_db = st.session_state.fragment_db
        
    if hasattr(current_fragment_db, 'calculate_crosslinking_ratio'):
        try:
            crosslinking_ratios = current_fragment_db.calculate_crosslinking_ratio(pca_analysis.loadings_df)
            if crosslinking_ratios:
                with st.container():
                    st.markdown("#### 🔗 Quick Chemical Analysis")
                    cols = st.columns(len(crosslinking_ratios) + 1)
                    
                    cols[0].metric("PC1 Variance", f"{pc1_variance:.1f}%")
                    
                    for i, (ratio_name, ratio_value) in enumerate(crosslinking_ratios.items()):
                        cols[i+1].metric(ratio_name, f"{ratio_value:.3f}")
                    
                    st.markdown("---")
        except:
            pass
    
    # Tabs for different views
    if st.session_state.ion_type == "Positive Ions":
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📈 PC1 Scores", 
            "🎯 Fragment Assignment", 
            "🔬 Chemical Analysis", 
            "📊 Interactive Plots", 
            "📈 Dose Response",
            "🔬 Individual Fragments",
            "🔗 Cross-Correlation",
            "📁 Download Results"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 PC1 Scores", 
            "🎯 Fragment Assignment", 
            "🔬 Chemical Analysis", 
            "📊 Interactive Plots", 
            "📈 Dose Response",
            "🔬 Individual Fragments",
            "📁 Download Results"
        ])
    
    with tab1:
        show_scores_table()
    
    with tab2:
        show_fragment_assignment()
    
    with tab3:
        show_chemical_analysis()
    
    with tab4:
        show_interactive_plots()
    
    with tab5:
        show_dose_response_analysis()
    
    with tab6:
        show_individual_fragment_analysis()
    
    with tab7:
        if st.session_state.ion_type == "Positive Ions":
            show_cross_correlation_analysis()
        else:
            show_download_options()
    
    if st.session_state.ion_type == "Positive Ions":
        with tab8:
            show_download_options()


def show_scores_table():
    """Show PC1 scores table"""
    pca_analysis = st.session_state.pca_analysis
    scores_df = pca_analysis.scores_df.sort_values('PC1', ascending=False).copy()
    
    # Add square information for better display
    scores_df['Square'] = scores_df['sample_name'].apply(extract_square_from_name)
    
    # Select columns to display
    display_cols = ['sample_name', 'pattern', 'Square', 'PC1']
    display_df = scores_df[display_cols].copy()
    display_df.columns = ['Sample Name', 'Pattern', 'Square', 'PC1 Score']
    
    st.subheader("🏆 PC1 Scores (Sorted by Score)")
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download PC1 Scores CSV",
        data=csv,
        file_name="pc1_scores.csv",
        mime="text/csv"
    )


def show_loadings_table():
    """Show PC1 loadings table"""
    pca_analysis = st.session_state.pca_analysis
    
    # Get PC1 loadings
    pc1_loadings = pca_analysis.loadings_df['PC1']
    masses = pca_analysis.loadings_df.index.values
    
    # Sort by absolute loading values
    abs_loadings = np.abs(pc1_loadings.values)
    sorted_indices = np.argsort(abs_loadings)[::-1]
    
    # Create display dataframe
    top_indices = sorted_indices[:20]  # Top 20
    
    loadings_display = pd.DataFrame({
        'Rank': range(1, 21),
        'm/z': [f"{masses[idx]:.3f}" for idx in top_indices],
        'PC1 Loading': [f"{pc1_loadings.iloc[idx]:.6f}" for idx in top_indices],
        '|Loading|': [f"{abs_loadings[idx]:.6f}" for idx in top_indices]
    })
    
    st.subheader("🎯 Top 20 Contributing Masses (PC1)")
    st.dataframe(
        loadings_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = loadings_display.to_csv(index=False)
    st.download_button(
        label="📥 Download PC1 Loadings CSV",
        data=csv,
        file_name="pc1_loadings.csv",
        mime="text/csv"
    )


def show_interactive_plots():
    """Show interactive Plotly visualizations"""
    pca_analysis = st.session_state.pca_analysis
    
    plot_type = st.selectbox(
        "Select Plot Type",
        ["Scores Plot", "Loadings Plot", "Scree Plot"],
        index=0
    )
    
    if plot_type == "Scores Plot":
        create_scores_plot(pca_analysis)
    elif plot_type == "Loadings Plot":
        create_loadings_plot(pca_analysis)
    elif plot_type == "Scree Plot":
        create_scree_plot(pca_analysis)


def create_scores_plot(pca_analysis):
    """Create interactive scores plot"""
    scores_df = pca_analysis.scores_df
    
    # Add square info for hover
    scores_df['Square'] = scores_df['sample_name'].apply(extract_square_from_name)
    
    # Determine y-axis (PC2 if available, else PC1)
    y_col = 'PC2' if 'PC2' in scores_df.columns else 'PC1'
    
    fig = px.scatter(
        scores_df,
        x='PC1',
        y=y_col,
        color='pattern' if 'pattern' in scores_df.columns else None,
        hover_data=['sample_name', 'Square'],
        title=f"PCA Scores Plot: PC1 vs {y_col}",
        labels={'PC1': f'PC1 ({pca_analysis.variance_explained[0]:.1f}%)'}
    )
    
    if y_col == 'PC2' and len(pca_analysis.variance_explained) > 1:
        fig.update_yaxes(title=f'PC2 ({pca_analysis.variance_explained[1]:.1f}%)')
    
    fig.update_layout(
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_loadings_plot(pca_analysis):
    """Create interactive loadings plot"""
    loadings_df = pca_analysis.loadings_df
    masses = loadings_df.index.values
    pc1_loadings = loadings_df['PC1'].values
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=masses,
        y=pc1_loadings,
        name='PC1 Loadings',
        hovertemplate='m/z: %{x:.3f}<br>Loading: %{y:.6f}<extra></extra>',
        marker_color=px.colors.sequential.Viridis
    ))
    
    fig.update_layout(
        title="PC1 Loadings",
        xaxis_title="m/z",
        yaxis_title="PC1 Loading",
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_scree_plot(pca_analysis):
    """Create interactive scree plot"""
    variance_explained = pca_analysis.variance_explained
    components = [f'PC{i+1}' for i in range(len(variance_explained))]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=components,
        y=variance_explained,
        name='Variance Explained',
        hovertemplate='%{x}: %{y:.1f}%<extra></extra>',
        marker_color=px.colors.sequential.Plasma
    ))
    
    fig.update_layout(
        title="Scree Plot - Variance Explained by Principal Components",
        xaxis_title="Principal Component",
        yaxis_title="Variance Explained (%)",
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_download_options():
    """Show download options for results"""
    pca_analysis = st.session_state.pca_analysis
    
    st.subheader("📁 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Data Files")
        
        # Scores CSV
        scores_csv = pca_analysis.scores_df.to_csv()
        st.download_button(
            label="📥 Download All Scores (CSV)",
            data=scores_csv,
            file_name="pca_scores.csv",
            mime="text/csv"
        )
        
        # Loadings CSV
        loadings_csv = pca_analysis.loadings_df.to_csv()
        st.download_button(
            label="📥 Download All Loadings (CSV)",
            data=loadings_csv,
            file_name="pca_loadings.csv",
            mime="text/csv"
        )
        
        # Variance explained CSV
        variance_df = pd.DataFrame({
            'PC': [f'PC{i+1}' for i in range(len(pca_analysis.variance_explained))],
            'Variance_Explained_%': pca_analysis.variance_explained,
            'Cumulative_%': np.cumsum(pca_analysis.variance_explained)
        })
        variance_csv = variance_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Variance Explained (CSV)",
            data=variance_csv,
            file_name="variance_explained.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("### 🎨 Generate Publication Plots")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🎨 Generate All Publication Plots"):
                generate_publication_plots()
        with col_b:
            if st.button("📊 Generate Fragment Report"):
                generate_fragment_analysis_report()


def generate_publication_plots():
    """Generate all publication-quality plots"""
    with st.spinner("Generating publication-quality plots..."):
        try:
            pca_analysis = st.session_state.pca_analysis
            output_dir = pca_analysis.output_dir
            
            # Create plotter
            plotter = ToFSIMSPlotter(output_dir)
            
            # Generate all plots
            plot_files = plotter.create_all_plots(
                scores_df=pca_analysis.scores_df,
                loadings_df=pca_analysis.loadings_df,
                variance_explained=pca_analysis.variance_explained,
                max_components=min(5, len(pca_analysis.variance_explained))
            )
            
            total_plots = sum(len(files) for files in plot_files.values())
            
            st.success(f"✅ Generated {total_plots} publication-quality plots!")
            st.info(f"📁 Plots saved to: {output_dir}")
            
            # List generated files
            with st.expander("📋 View Generated Files"):
                for category, files in plot_files.items():
                    if files:
                        st.write(f"**{category.title()}:**")
                        for file_path in files:
                            st.write(f"- {os.path.basename(file_path)}")
            
        except Exception as e:
            st.error(f"❌ Error generating plots: {str(e)}")


def show_fragment_assignment():
    """Show automated fragment assignment for PC1 loadings"""
    pca_analysis = st.session_state.pca_analysis
    
    # Use appropriate fragment database based on ion type
    if st.session_state.ion_type == "Positive Ions":
        fragment_db = st.session_state.positive_fragment_db
        st.subheader("🎯 Positive Ion Fragment Assignment")
        st.info("🔬 Using positive ion fragment database with 39 expected fragments")
    else:
        fragment_db = st.session_state.fragment_db
        st.subheader("🎯 Negative Ion Fragment Assignment")
        st.info("🔬 Using negative ion fragment database with verified assignments")
    
    # Settings
    col1, col2 = st.columns(2)
    with col1:
        tolerance = st.slider("Mass Tolerance (Da)", 0.005, 0.05, 0.02, 0.005)
    with col2:
        top_n = st.slider("Number of fragments to show", 10, 50, 25)
    
    # Generate fragment assignment report
    try:
        # Check if method exists
        if not hasattr(fragment_db, 'generate_fragment_report'):
            st.error("❌ Fragment database missing generate_fragment_report method. Please restart Streamlit.")
            st.info("💡 Tip: Stop the server (Ctrl+C) and run 'streamlit run src/pca_gui_web.py' again")
            return
            
        fragment_report = fragment_db.generate_fragment_report(pca_analysis.loadings_df, top_n=top_n)
        
        # Separate assigned and unassigned
        assigned_fragments = fragment_report[fragment_report['Fragment'] != 'Unknown']
        unassigned_fragments = fragment_report[fragment_report['Fragment'] == 'Unknown']
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Fragments", len(fragment_report))
        with col2:
            st.metric("Assigned", len(assigned_fragments))
        with col3:
            st.metric("Unassigned", len(unassigned_fragments))
        
        # Show assigned fragments
        st.markdown("### ✅ Assigned Fragments")
        if len(assigned_fragments) > 0:
            # Add color coding based on expected trend
            def get_trend_color(trend):
                if 'increase_with_dose' in trend or 'strong_increase' in trend:
                    return '🔴'  # Red for increasing
                elif 'decrease_with_dose' in trend:
                    return '🔵'  # Blue for decreasing
                elif 'stable' in trend:
                    return '🟢'  # Green for stable
                else:
                    return '🟡'  # Yellow for variable
            
            assigned_display = assigned_fragments.copy()
            assigned_display['Trend'] = assigned_display['Expected_Trend'].apply(get_trend_color) + ' ' + assigned_display['Expected_Trend']
            
            st.dataframe(
                assigned_display[['m/z', 'PC1_Loading', '|Loading|', 'Fragment', 'Formula', 'Category', 'Description', 'Trend']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No fragments could be assigned automatically. Consider adjusting the mass tolerance.")
        
        # Show unassigned fragments with emphasis
        if len(unassigned_fragments) > 0:
            st.markdown("### ⚠️ Unassigned Fragments - Need Further Investigation")
            st.error(f"Found {len(unassigned_fragments)} unassigned fragments with significant loadings. These may represent:")
            st.markdown("""
            - Novel degradation products
            - Unexpected crosslinking fragments
            - Substrate interference
            - Contamination peaks
            - Database gaps requiring manual identification
            """)
            
            st.dataframe(
                unassigned_fragments[['m/z', 'PC1_Loading', '|Loading|']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("🎉 All top contributing fragments have been successfully assigned!")
        
        # Download button
        csv = fragment_report.to_csv(index=False)
        st.download_button(
            label="📥 Download Fragment Assignment Report",
            data=csv,
            file_name="fragment_assignment_report.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error generating fragment assignment: {str(e)}")


def show_chemical_analysis():
    """Show quantitative chemical analysis tools"""
    pca_analysis = st.session_state.pca_analysis
    
    # Use appropriate fragment database based on ion type
    if st.session_state.ion_type == "Positive Ions":
        fragment_db = st.session_state.positive_fragment_db
    else:
        fragment_db = st.session_state.fragment_db
    
    st.subheader("🔬 Quantitative Chemical Analysis")
    
    try:
        # Calculate crosslinking ratios
        crosslinking_ratios = fragment_db.calculate_crosslinking_ratio(pca_analysis.loadings_df)
        
        # Display key metrics
        st.markdown("### 📊 Key Chemical Indicators")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'C6H/C4H' in crosslinking_ratios:
                st.metric(
                    "C6H⁻/C4H⁻ Ratio (ρ)", 
                    f"{crosslinking_ratios['C6H/C4H']:.3f}",
                    help="Primary crosslinking indicator from literature. Higher values = more crosslinking"
                )
            
            if 'High_C/Low_C' in crosslinking_ratios:
                st.metric(
                    "High-C/Low-C Ratio",
                    f"{crosslinking_ratios['High_C/Low_C']:.3f}",
                    help="(C8H⁻+C9H⁻+C10H⁻)/(C2H⁻+C3H⁻). Indicates advanced crosslinking/carbonization"
                )
        
        with col2:
            # PC1 variance as carbon density indicator
            pc1_variance = pca_analysis.variance_explained[0]
            st.metric(
                "PC1 Variance (%)",
                f"{pc1_variance:.1f}%",
                help="Higher PC1 variance often correlates with carbon density changes"
            )
        
        # Show fragment categories breakdown
        st.markdown("### 🧪 Fragment Categories Analysis")
        
        categories = fragment_db.get_categories()
        category_data = []
        
        for category in categories:
            cat_fragments = fragment_db.get_fragments_by_category(category)
            assigned_count = 0
            total_loading = 0.0
            
            for frag_name, frag_data in cat_fragments.items():
                fragment_match = fragment_db.get_fragment_by_mz(frag_data['mz'], tolerance=0.02)
                if fragment_match:
                    # Find this fragment in loadings
                    mz_matches = pca_analysis.loadings_df.index[
                        abs(pca_analysis.loadings_df.index - frag_data['mz']) < 0.02
                    ]
                    if len(mz_matches) > 0:
                        assigned_count += 1
                        total_loading += abs(pca_analysis.loadings_df.loc[mz_matches[0], 'PC1'])
            
            category_data.append({
                'Category': category,
                'Assigned_Fragments': assigned_count,
                'Total_|Loading|': f"{total_loading:.6f}",
                'Avg_|Loading|': f"{total_loading/max(assigned_count, 1):.6f}"
            })
        
        category_df = pd.DataFrame(category_data)
        st.dataframe(category_df, use_container_width=True, hide_index=True)
        
        # Methods for quantifying chemical changes
        st.markdown("### 📚 Methods for Quantifying Chemical Changes")
        
        with st.expander("🔗 Crosslinking Quantification Methods"):
            st.markdown("""
            **1. C6H⁻/C4H⁻ Ratio (ρ) - Primary Method**
            - C4H⁻ as stable reference ion (literature validated)
            - C6H⁻ increases with crosslinking degree
            - Higher ρ values = more crosslinking
            
            **2. Higher Carbon Chain Ratios**
            - (C8H⁻ + C9H⁻ + C10H⁻) / (C2H⁻ + C3H⁻)
            - Indicates advanced crosslinking/carbonization
            
            **3. PC1 Score Progression**
            - Track PC1 scores vs. electron beam dose
            - Should show systematic progression with crosslinking
            """)
        
        with st.expander("🔥 Carbonization/Graphitization Methods"):
            st.markdown("""
            **1. Long Carbon Chain Detection**
            - Monitor C7H⁻, C8H⁻, C9H⁻, C10H⁻ intensities
            - Higher intensities = more carbonization
            
            **2. Hydrogen Loss Indicators**
            - OH⁻ decrease (hydroxyl loss)
            - CHO⁻ increase (aldehyde formation)
            
            **3. Aromatic/Graphitic Structure Formation**
            - C6H⁻ strong increase at high doses
            - Formation of extended carbon networks
            """)
        
        with st.expander("🧬 Polymer Degradation Methods"):
            st.markdown("""
            **1. Organic Linker Loss**
            - C4H6O2⁻ decrease (intact diol linker loss)
            - C4H4O⁻ changes (dehydrated linker)
            
            **2. Metal-Organic Bond Breaking**
            - AlC⁻ decrease (aluminum-carbon bond loss)
            - Al⁻/AlO⁻ ratio changes
            
            **3. Oxidation Indicators**
            - CO⁻, CO2⁻ increase
            - AlO⁻/Al⁻ ratio increase
            """)
        
    except Exception as e:
        st.error(f"Error in chemical analysis: {str(e)}")


def show_dose_response_analysis():
    """Show dose-response analysis for electron beam effects"""
    pca_analysis = st.session_state.pca_analysis
    
    # Use appropriate fragment database based on ion type
    if st.session_state.ion_type == "Positive Ions":
        fragment_db = st.session_state.positive_fragment_db
    else:
        fragment_db = st.session_state.fragment_db
    
    st.subheader("📈 Dose-Response Analysis")
    
    try:
        # Extract dose information from sample names
        scores_df = pca_analysis.scores_df.copy()
        
        # Add dose mapping
        dose_mapping = {1: 500, 2: 2000, 3: 5000, 4: 10000, 5: 15000}
        scores_df['square_num'] = scores_df['sample_name'].apply(lambda x: int(x.split('_SQ')[1].split('_')[0]) if '_SQ' in x else 0)
        scores_df['dose_uC_cm2'] = scores_df['square_num'].map(dose_mapping)
        
        if scores_df['dose_uC_cm2'].notna().sum() > 0:
            # Analyze dose trends
            dose_trends = fragment_db.identify_dose_trends(scores_df)
            
            # Show trend analysis
            col1, col2 = st.columns(2)
            
            with col1:
                if 'PC1_vs_dose' in dose_trends:
                    trend_desc = dose_trends['PC1_vs_dose'].replace('_', ' ').title()
                    correlation = dose_trends.get('correlation_coefficient', 'N/A')
                    st.metric(
                        "PC1 vs Dose Trend",
                        trend_desc,
                        f"r = {correlation}"
                    )
                
            with col2:
                avg_by_dose = scores_df.groupby('dose_uC_cm2')['PC1'].agg(['mean', 'std']).reset_index()
                if len(avg_by_dose) > 1:
                    st.metric(
                        "Dose Range",
                        f"{avg_by_dose['dose_uC_cm2'].min():.0f} - {avg_by_dose['dose_uC_cm2'].max():.0f} μC/cm²",
                        f"{len(avg_by_dose)} dose levels"
                    )
            
            # Create dose response plot
            fig = px.scatter(
                scores_df,
                x='dose_uC_cm2',
                y='PC1',
                color='pattern' if 'pattern' in scores_df.columns else None,
                title="PC1 Score vs. Electron Beam Dose",
                labels={
                    'dose_uC_cm2': 'Electron Beam Dose (μC/cm²)',
                    'PC1': f'PC1 Score ({pca_analysis.variance_explained[0]:.1f}% variance)'
                },
                hover_data=['sample_name']
            )
            
            # Add trendline
            fig.add_trace(px.scatter(
                avg_by_dose, x='dose_uC_cm2', y='mean'
            ).update_traces(
                mode='lines+markers',
                name='Average Trend',
                line=dict(color='red', width=3)
            ).data[0])
            
            fig.update_layout(
                template="plotly_white",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show dose progression table
            st.markdown("### 📊 Dose Progression Summary")
            
            dose_summary = scores_df.groupby('dose_uC_cm2').agg({
                'PC1': ['mean', 'std', 'count'],
                'pattern': 'nunique'
            }).round(4)
            
            dose_summary.columns = ['PC1_Mean', 'PC1_Std', 'Sample_Count', 'Patterns']
            dose_summary = dose_summary.reset_index()
            dose_summary['Expected_Effect'] = dose_summary['dose_uC_cm2'].apply(get_expected_dose_effect)
            
            st.dataframe(dose_summary, use_container_width=True, hide_index=True)
            
        else:
            st.warning("⚠️ Could not extract dose information from sample names. Ensure samples follow P#_SQ# naming convention.")
            
    except Exception as e:
        st.error(f"Error in dose-response analysis: {str(e)}")


def get_expected_dose_effect(dose):
    """Get expected chemical effect for given dose"""
    if dose <= 2000:
        return "Minimal crosslinking, intact linkers"
    elif dose <= 10000:
        return "Increased crosslinking, H-loss"
    else:
        return "Carbonization/graphitization"


def show_individual_fragment_analysis():
    """Interactive individual fragment dose plotting"""
    pca_analysis = st.session_state.pca_analysis
    
    # Use appropriate fragment database and data files based on ion type
    if st.session_state.ion_type == "Positive Ions":
        fragment_db = st.session_state.positive_fragment_db
        st.subheader("🔬 Individual Positive Ion Fragment Analysis")
        data_file_patterns = ["PosIonTIC.txt", "PosDataNorm.txt", "PosPeakList.txt"]
    else:
        fragment_db = st.session_state.fragment_db
        st.subheader("🔬 Individual Negative Ion Fragment Analysis")
        data_file_patterns = ["NegIonTIC.txt", "NegDataNorm.txt", "NegPeakList.txt"]
    
    try:
        # Try multiple possible data file locations
        possible_paths = []
        for pattern in data_file_patterns:
            possible_paths.extend([
                f"data/{pattern}",
                f"/home/dreece23/pca-sims/data/{pattern}",
                pattern
            ])
        
        # Also check if PCA analysis object has a data file path
        if hasattr(pca_analysis, 'data_file'):
            possible_paths.insert(0, pca_analysis.data_file)
        
        # Try each path until one works
        data_file_path = None
        lines = None
        
        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                    data_file_path = path
                    break
            except:
                continue
        
        if lines is None:
            # Dynamic error message based on ion type
            if st.session_state.ion_type == "Positive Ions":
                expected_file = "PosIonTIC.txt"
                file_type = "positive ion"
            else:
                expected_file = "NegIonTIC.txt" 
                file_type = "negative ion"
                
            st.error(f"Cannot locate raw ToF-SIMS data file. Please ensure {expected_file} is in the data/ directory.")
            st.info("Tried these locations:")
            for path in possible_paths:
                st.write(f"- {path}")
            
            # Add file uploader as backup
            st.markdown("### 📁 Upload Raw Data File")
            uploaded_file = st.file_uploader(
                f"Upload {expected_file} file",
                type=['txt'],
                help=f"Upload your raw {file_type} ToF-SIMS data file"
            )
            
            if uploaded_file is not None:
                lines = uploaded_file.getvalue().decode().splitlines()
                lines = [line + '\n' for line in lines]  # Add back newlines
                data_file_path = uploaded_file.name
            else:
                return
        
        # Parse header to get sample names
        header = lines[0].strip().split('\t')
        sample_names = header[1:]  # Skip 'Mass (u)' column
        
        # Filter out SQ1 columns and create dose mapping
        dose_mapping = {1: 500, 2: 2000, 3: 5000, 4: 10000, 5: 15000}
        valid_samples = []
        
        for i, sample_name in enumerate(sample_names):
            if '_SQ1' not in sample_name:  # Omit SQ1 as discussed
                try:
                    sq_num = int(sample_name.split('_SQ')[1])
                    dose = dose_mapping.get(sq_num)
                    if dose:
                        valid_samples.append({
                            'index': i + 1,  # +1 because mass is column 0
                            'name': sample_name,
                            'pattern': sample_name.split('_')[0],
                            'square': sq_num,
                            'dose': dose
                        })
                except:
                    continue
        
        if not valid_samples:
            st.error("No valid samples found in data")
            return
        
        # Fragment selection interface
        st.markdown("### 🎯 Fragment Selection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Select fragments to plot:**")
            
            # Get critical fragments from our analysis
            critical_fragments = [
                (1.0085, "H⁻ - Hydrogen anion (CRITICAL)"),
                (41.0036, "C₂HO⁻/AlCH₂⁻ - MYSTERY FRAGMENT"),
                (44.9981, "COOH⁻ - Carboxyl group"),
                (34.9699, "³⁵Cl⁻ - Chlorine from HCl development"),
                (36.9669, "³⁷Cl⁻ - Chlorine isotope"),  
                (65.0031, "C₄HO⁻ - Four-carbon carbonyl"),
                (53.0032, "C₃HO⁻ - Three-carbon carbonyl"),
                (18.9991, "F⁻ - Fluorine"),
                (12.0006, "C⁻ - Carbon anion"),
                (68.9984, "Unknown - increases with dose"),
                (66.9811, "¹³CC₃HO⁻ - Isotope of m/z 65"),
                (26.9815, "Al⁻ - Aluminum (may not be in data)"),
                (42.9765, "AlO⁻ - Aluminum oxide (check if present)"),
            ]
            
            selected_fragments = []
            for mz, description in critical_fragments:
                if st.checkbox(f"m/z {mz:.4f} - {description}", key=f"frag_{mz}"):
                    selected_fragments.append(mz)
        
        with col2:
            st.markdown("**Plot options:**")
            
            # Plotting options
            plot_type = st.radio(
                "Plot style",
                ["Individual traces", "Average by dose", "Both"],
                index=1
            )
            
            normalize_data = st.checkbox("Normalize intensities", value=False)
            
            error_bars = st.checkbox("Show error bars (avg mode)", value=True)
            
            log_scale = st.checkbox("Log scale Y-axis", value=False)
        
        if selected_fragments:
            st.markdown("### 📊 Dose Response Plots")
            
            # Extract data for selected fragments
            fragment_data = {}
            missing_fragments = []
            
            for target_mz in selected_fragments:
                # Find closest mass in data
                best_match = None
                best_diff = float('inf')
                
                for line in lines[1:]:
                    parts = line.strip().split('\t')
                    if len(parts) > 1:
                        try:
                            mz = float(parts[0])
                            diff = abs(mz - target_mz)
                            if diff < best_diff and diff < 0.05:  # Increased tolerance
                                best_match = (mz, parts)
                                best_diff = diff
                        except:
                            continue
                
                if best_match and best_diff < 0.02:  # Accept reasonable matches
                    actual_mz, data_parts = best_match
                    
                    # Extract intensities for valid samples
                    sample_data = []
                    for sample_info in valid_samples:
                        try:
                            intensity = float(data_parts[sample_info['index']])
                            sample_data.append({
                                'sample': sample_info['name'],
                                'pattern': sample_info['pattern'], 
                                'dose': sample_info['dose'],
                                'intensity': intensity
                            })
                        except:
                            continue
                    
                    if sample_data:
                        fragment_data[f"{target_mz:.4f} (actual: {actual_mz:.4f})"] = sample_data
                else:
                    missing_fragments.append(target_mz)
            
            # Show missing fragments
            if missing_fragments:
                st.warning(f"⚠️ Could not find these fragments in data: {', '.join([f'm/z {mz:.4f}' for mz in missing_fragments])}")
                st.info("This may be because they have very low intensities or weren't detected in your analysis.")
            
            # Plot options for multiple fragments
            plot_individual = st.checkbox("Plot each fragment separately", value=True)
            plot_overlay = st.checkbox("Overlay all fragments on one plot", value=False)
            
            if plot_overlay and len(fragment_data) > 1:
                st.markdown("#### 📊 Combined Fragment Trends")
                
                # Automatic quantification analysis
                st.markdown("#### 🔬 Automatic Chemical Quantification")
                
                # Calculate chemical transformation metrics
                transformation_metrics = calculate_transformation_metrics(fragment_data)
                
                if transformation_metrics:
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        if 'carbonyl_formation' in transformation_metrics:
                            st.metric(
                                "Carbonyl Formation",
                                f"{transformation_metrics['carbonyl_formation']:.3f}",
                                help="Ratio of carbonyl fragments (C=O formation)"
                            )
                    
                    with col_m2:
                        if 'hydrogen_loss' in transformation_metrics:
                            st.metric(
                                "Hydrogen Loss", 
                                f"{transformation_metrics['hydrogen_loss']:.3f}",
                                help="H⁻ depletion indicating radical chemistry"
                            )
                    
                    with col_m3:
                        if 'aromatic_formation' in transformation_metrics:
                            st.metric(
                                "Aromatic Formation",
                                f"{transformation_metrics['aromatic_formation']:.3f}",
                                help="Formation of aromatic/conjugated species"
                            )
                    
                    with col_m4:
                        if 'transformation_index' in transformation_metrics:
                            st.metric(
                                "Transformation Index",
                                f"{transformation_metrics['transformation_index']:.3f}",
                                help="Overall e-beam transformation degree"
                            )
                
                # Create overlay plot
                fig_overlay = go.Figure()
                
                colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
                
                for i, (frag_label, data) in enumerate(fragment_data.items()):
                    df = pd.DataFrame(data)
                    
                    if normalize_data:
                        max_intensity = df['intensity'].max()
                        if max_intensity > 0:
                            df['intensity'] = df['intensity'] / max_intensity
                    
                    # Calculate averages by dose
                    avg_data = df.groupby('dose').agg({
                        'intensity': ['mean', 'std', 'count']
                    }).round(6)
                    
                    avg_data.columns = ['mean', 'std', 'count']
                    avg_data = avg_data.reset_index()
                    avg_data['stderr'] = avg_data['std'] / np.sqrt(avg_data['count'])
                    
                    color = colors[i % len(colors)]
                    
                    if error_bars:
                        error_y = dict(type='data', array=avg_data['stderr'], visible=True)
                    else:
                        error_y = None
                    
                    fig_overlay.add_trace(go.Scatter(
                        x=avg_data['dose'],
                        y=avg_data['mean'],
                        mode='lines+markers',
                        name=frag_label.split('(')[0].strip(),  # Clean name
                        error_y=error_y,
                        line=dict(width=3, color=color),
                        marker=dict(size=8)
                    ))
                
                # Customize overlay plot
                y_label = "Normalized Intensity" if normalize_data else "Intensity"
                if log_scale:
                    fig_overlay.update_yaxes(type="log")
                    y_label += " (log scale)"
                
                fig_overlay.update_layout(
                    title="Multiple Fragment Dose Response Comparison",
                    xaxis_title="Electron Beam Dose (μC/cm²)",
                    yaxis_title=y_label,
                    template="plotly_white",
                    height=500,
                    showlegend=True,
                    legend=dict(x=1, y=1)
                )
                
                st.plotly_chart(fig_overlay, use_container_width=True)
            
            # Individual plots (if enabled)
            if plot_individual:
                for frag_label, data in fragment_data.items():
                    st.markdown(f"#### {frag_label}")
                    
                    # Convert to DataFrame for easier plotting
                    import pandas as pd
                    df = pd.DataFrame(data)
                    
                    if normalize_data:
                        max_intensity = df['intensity'].max()
                        if max_intensity > 0:
                            df['intensity'] = df['intensity'] / max_intensity
                    
                    # Create plot
                    fig = go.Figure()
                
                    if plot_type in ["Individual traces", "Both"]:
                        # Plot individual sample traces
                        for pattern in df['pattern'].unique():
                            pattern_data = df[df['pattern'] == pattern].sort_values('dose')
                            
                            fig.add_trace(go.Scatter(
                                x=pattern_data['dose'],
                                y=pattern_data['intensity'],
                                mode='lines+markers',
                                name=f'{pattern} individual',
                                opacity=0.6,
                                line=dict(width=1)
                            ))
                    
                    # Always calculate avg_data for trend analysis
                    avg_data = df.groupby('dose').agg({
                        'intensity': ['mean', 'std', 'count']
                    }).round(6)
                    
                    avg_data.columns = ['mean', 'std', 'count']
                    avg_data = avg_data.reset_index()
                    avg_data['stderr'] = avg_data['std'] / np.sqrt(avg_data['count'])
                    
                    if plot_type in ["Average by dose", "Both"]:
                        if error_bars:
                            error_y = dict(
                                type='data',
                                array=avg_data['stderr'],
                                visible=True
                            )
                        else:
                            error_y = None
                        
                        fig.add_trace(go.Scatter(
                            x=avg_data['dose'],
                            y=avg_data['mean'],
                            mode='lines+markers',
                            name='Average ± SEM',
                            error_y=error_y,
                            line=dict(width=3, color='red'),
                            marker=dict(size=8)
                        ))
                
                    # Customize plot
                    y_label = "Normalized Intensity" if normalize_data else "Intensity"
                    if log_scale:
                        fig.update_yaxes(type="log")
                        y_label += " (log scale)"
                    
                    fig.update_layout(
                        title=f"{frag_label} vs Electron Beam Dose",
                        xaxis_title="Electron Beam Dose (μC/cm²)",
                        yaxis_title=y_label,
                        template="plotly_white",
                        height=400,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show trend analysis
                    if len(avg_data) > 2:
                        correlation = np.corrcoef(avg_data['dose'], avg_data['mean'])[0, 1]
                        trend = "increases" if correlation > 0.3 else "decreases" if correlation < -0.3 else "shows no clear trend"
                        
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Correlation (r)", f"{correlation:.3f}")
                        col_b.metric("Trend", trend.title())
                        
                        # Show dose range values
                        min_val = avg_data['mean'].iloc[0]
                        max_val = avg_data['mean'].iloc[-1]
                        change = ((max_val - min_val) / min_val * 100) if min_val > 0 else 0
                        col_c.metric("Change SQ2→SQ5", f"{change:+.1f}%")
        
        else:
            st.info("👆 Select fragments above to see dose-response plots")
            
        # Quick fragment identification helper
        with st.expander("🔍 E-beam Chemical Transformation Analysis"):
            st.markdown("""
            **⚡ E-BEAM TRANSFORMATION MECHANISM:**
            ```
            HO-CH₂-C≡C-CH₂-OH + e⁻ → [Radicals] → Thermodynamically stable products
            ```
            
            **🎯 TRANSFORMATION PRINCIPLES:**
            - **Carbonyls (C=O) > Saturated C-H**: Thermodynamic stabilization
            - **Aromatic/Conjugated > Linear**: Conjugation stabilization  
            - **Crosslinked networks > Chains**: Entropic stabilization
            
            **✅ CONFIRMED TRANSFORMATIONS:**
            - **↗️ Carbonyl Formation**: C₄HO⁻ (+119%), C₃HO⁻, C₂HO⁻, COOH⁻
            - **↘️ Hydrogen Loss**: H⁻ depletion during radical stabilization
            - **↘️ Process Chemistry**: Cl⁻ removal (HCl development validation)
            - **↗️ Conjugated Systems**: Formation of more stable species
            
            **🧪 CHEMICAL TRANSFORMATION SERIES:**
            ```
            C₄H₆O₂ (diol) → C₄HO⁻ → C₃HO⁻ → C₂HO⁻ (carbonyl cascade)
                            ↓
            Thermodynamic stabilization + crosslinking network formation
            ```
            
            **📊 QUANTIFICATION METHODS:**
            1. **Carbonyl Formation Index**: (ΣCarbonyls) / (ΣTotal changes)
            2. **Hydrogen Loss Ratio**: (H⁻ᵢₙᵢₜᵢₐₗ - H⁻ₑᵢₙₐₗ) / H⁻ᵢₙᵢₜᵢₐₗ
            3. **Aromatic Formation**: Conjugated species increase
            4. **Transformation Index**: Overall chemical stabilization degree
            
            **🎮 INTERACTIVE ANALYSIS:**
            - Select multiple fragments → Enable "Overlay" → View transformation cascade!
            """)
    
    
    
    except Exception as e:
        st.error(f"Error in individual fragment analysis: {str(e)}")


def calculate_transformation_metrics(fragment_data):
    """Calculate automatic chemical transformation metrics"""
    
    metrics = {}
    
    # Define fragment categories based on chemical identity
    carbonyl_fragments = ['41.0036', '44.9981', '53.0032', '65.0031']  # C2HO-, COOH-, C3HO-, C4HO-
    aromatic_fragments = ['73.0078', '65.0031', '77.0078', '91.0078']  # C6H-, potential aromatics
    hydrogen_fragments = ['1.0085']  # H-
    saturated_fragments = ['25.0080', '37.0078', '49.0078']  # C2H-, C3H-, C4H-
    
    try:
        # Calculate carbonyl formation index
        carbonyl_intensities = []
        total_intensities = []
        
        for frag_label, data in fragment_data.items():
            # Extract actual m/z from label
            mz_str = frag_label.split('(')[0].strip()
            
            df = pd.DataFrame(data)
            
            # Get dose progression (SQ2 vs SQ5)
            sq2_data = df[df['dose'] == 2000]['intensity']
            sq5_data = df[df['dose'] == 15000]['intensity']
            
            if len(sq2_data) > 0 and len(sq5_data) > 0:
                sq2_avg = sq2_data.mean()
                sq5_avg = sq5_data.mean()
                intensity_change = sq5_avg - sq2_avg
                
                # Check if this is a carbonyl fragment
                is_carbonyl = any(carbonyl_frag in mz_str for carbonyl_frag in carbonyl_fragments)
                
                if is_carbonyl:
                    carbonyl_intensities.append(max(0, intensity_change))  # Only positive changes
                
                total_intensities.append(abs(intensity_change))
        
        # Carbonyl formation metric
        if carbonyl_intensities and total_intensities:
            metrics['carbonyl_formation'] = sum(carbonyl_intensities) / sum(total_intensities)
        
        # Hydrogen loss metric (should be negative change)
        for frag_label, data in fragment_data.items():
            if '1.0085' in frag_label:  # H-
                df = pd.DataFrame(data)
                sq2_data = df[df['dose'] == 2000]['intensity']
                sq5_data = df[df['dose'] == 15000]['intensity']
                
                if len(sq2_data) > 0 and len(sq5_data) > 0:
                    sq2_avg = sq2_data.mean()
                    sq5_avg = sq5_data.mean()
                    h_loss = (sq2_avg - sq5_avg) / sq2_avg if sq2_avg > 0 else 0
                    metrics['hydrogen_loss'] = max(0, h_loss)  # Positive value = more loss
        
        # Aromatic formation (look for aromatic-like fragments increasing)
        aromatic_changes = []
        for frag_label, data in fragment_data.items():
            mz_str = frag_label.split('(')[0].strip()
            
            # Check for potential aromatic fragments (unsaturated, 6-ring like)
            is_aromatic = any(arom_frag in mz_str for arom_frag in aromatic_fragments)
            
            if is_aromatic:
                df = pd.DataFrame(data)
                sq2_data = df[df['dose'] == 2000]['intensity']
                sq5_data = df[df['dose'] == 15000]['intensity']
                
                if len(sq2_data) > 0 and len(sq5_data) > 0:
                    sq2_avg = sq2_data.mean()
                    sq5_avg = sq5_data.mean()
                    change = (sq5_avg - sq2_avg) / sq2_avg if sq2_avg > 0 else 0
                    aromatic_changes.append(max(0, change))
        
        if aromatic_changes:
            metrics['aromatic_formation'] = sum(aromatic_changes) / len(aromatic_changes)
        
        # Overall transformation index
        # Combination of carbonyl formation, hydrogen loss, and aromatic formation
        transformation_components = []
        if 'carbonyl_formation' in metrics:
            transformation_components.append(metrics['carbonyl_formation'])
        if 'hydrogen_loss' in metrics:
            transformation_components.append(metrics['hydrogen_loss'])
        if 'aromatic_formation' in metrics:
            transformation_components.append(metrics['aromatic_formation'])
        
        if transformation_components:
            metrics['transformation_index'] = sum(transformation_components) / len(transformation_components)
        
        return metrics
    
    except Exception as e:
        st.warning(f"Could not calculate transformation metrics: {e}")
        return {}


def generate_fragment_analysis_report():
    """Generate comprehensive fragment analysis report"""
    with st.spinner("Generating comprehensive fragment analysis report..."):
        try:
            pca_analysis = st.session_state.pca_analysis
            
            # Use appropriate fragment database based on ion type
            if st.session_state.ion_type == "Positive Ions":
                fragment_db = st.session_state.positive_fragment_db
            else:
                fragment_db = st.session_state.fragment_db
                
            output_dir = pca_analysis.output_dir
            
            # Generate fragment assignment report
            fragment_report = fragment_db.generate_fragment_report(pca_analysis.loadings_df, top_n=50)
            
            # Calculate crosslinking ratios
            crosslinking_ratios = fragment_db.calculate_crosslinking_ratio(pca_analysis.loadings_df)
            
            # Analyze dose trends if possible
            scores_df = pca_analysis.scores_df.copy()
            dose_mapping = {1: 500, 2: 2000, 3: 5000, 4: 10000, 5: 15000}
            try:
                scores_df['square_num'] = scores_df['sample_name'].apply(lambda x: int(x.split('_SQ')[1].split('_')[0]) if '_SQ' in x else 0)
                scores_df['dose_uC_cm2'] = scores_df['square_num'].map(dose_mapping)
                dose_trends = fragment_db.identify_dose_trends(scores_df)
            except:
                dose_trends = {}
            
            # Create comprehensive report
            report_lines = [
                "# ToF-SIMS Alucone Resist Fragment Analysis Report",
                "## Generated with Automated Fragment Assignment Tool",
                "",
                "## Analysis Summary",
                f"- **Total samples analyzed**: {len(pca_analysis.scores_df)}",
                f"- **PC1 variance explained**: {pca_analysis.variance_explained[0]:.1f}%",
                f"- **Total fragments in top loadings**: {len(fragment_report)}",
                f"- **Assigned fragments**: {len(fragment_report[fragment_report['Fragment'] != 'Unknown'])}",
                f"- **Unassigned fragments**: {len(fragment_report[fragment_report['Fragment'] == 'Unknown'])}",
                "",
                "## Key Chemical Indicators"
            ]
            
            for ratio_name, ratio_value in crosslinking_ratios.items():
                report_lines.append(f"- **{ratio_name}**: {ratio_value:.4f}")
            
            if dose_trends:
                report_lines.extend([
                    "",
                    "## Dose-Response Analysis",
                    f"- **PC1 vs Dose Trend**: {dose_trends.get('PC1_vs_dose', 'Unknown')}",
                    f"- **Correlation Coefficient**: {dose_trends.get('correlation_coefficient', 'N/A')}"
                ])
            
            report_lines.extend([
                "",
                "## Fragment Assignment Details",
                "",
                "### Assigned Fragments (Chemical Identity Confirmed)"
            ])
            
            assigned_fragments = fragment_report[fragment_report['Fragment'] != 'Unknown']
            for _, row in assigned_fragments.iterrows():
                report_lines.append(
                    f"- **{row['Fragment']}** ({row['Formula']}): m/z {row['m/z']}, Loading {row['PC1_Loading']} - {row['Description']}"
                )
            
            unassigned_fragments = fragment_report[fragment_report['Fragment'] == 'Unknown']
            if len(unassigned_fragments) > 0:
                report_lines.extend([
                    "",
                    "### Unassigned Fragments (Require Further Investigation)"
                ])
                for _, row in unassigned_fragments.iterrows():
                    report_lines.append(
                        f"- **Unknown**: m/z {row['m/z']}, Loading {row['PC1_Loading']} - Significant contributor requiring manual identification"
                    )
            
            report_content = "\n".join(report_lines)
            
            # Save report
            report_path = os.path.join(output_dir, "fragment_analysis_report.md")
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            # Save detailed CSV
            csv_path = os.path.join(output_dir, "detailed_fragment_assignment.csv")
            fragment_report.to_csv(csv_path, index=False)
            
            st.success(f"✅ Fragment analysis report generated!")
            st.info(f"📁 Files saved:\n- Report: {os.path.basename(report_path)}\n- Data: {os.path.basename(csv_path)}")
            
            # Show preview of report
            with st.expander("📋 Preview Report"):
                st.markdown(report_content)
                
        except Exception as e:
            st.error(f"❌ Error generating fragment analysis report: {str(e)}")


def show_cross_correlation_analysis():
    """Show cross-correlation analysis between positive and negative ion modes"""
    st.subheader("🔗 Positive-Negative Ion Cross-Correlation")
    
    pca_analysis = st.session_state.pca_analysis
    pos_fragment_db = st.session_state.positive_fragment_db
    neg_fragment_db = st.session_state.fragment_db
    
    st.markdown("""
    **Cross-validation strategy for mechanism confirmation:**
    Compare positive ion findings with verified negative ion assignments to validate chemical mechanisms.
    """)
    
    # Key validation targets
    st.markdown("### 🎯 Critical Validation Targets")
    
    validation_targets = [
        {
            "mechanism": "Aluminum Chemistry",
            "positive_ions": "Al+ (m/z 26.9815), AlO+ (m/z 42.9765), AlCH3+ (m/z 41.0049)",
            "negative_correlation": "Absence of Al- validates C2HO- assignment over AlCH2-",
            "validation": "Strong Al+ signal confirms aluminum presence"
        },
        {
            "mechanism": "Aromatic Formation", 
            "positive_ions": "C6H+ (m/z 73.0078)",
            "negative_correlation": "C6H- increases +154% (maximum thermodynamic stability)",
            "validation": "C6H+ should show similar strong dose increase"
        },
        {
            "mechanism": "Carbonyl Cascade",
            "positive_ions": "CHO+ (m/z 29.0027), COOH+ (m/z 44.9982), C2HO+ (m/z 41.0027)",
            "negative_correlation": "COOH- (+98%), C4HO- (+119%), C3HO- (+69%), C2HO- (+52%)",
            "validation": "Positive carbonyls should show similar increases"
        },
        {
            "mechanism": "Radical Chemistry",
            "positive_ions": "H+ (m/z 1.0078)",
            "negative_correlation": "H- decreases -28% (consumed in stabilization)",
            "validation": "H+ should show complementary behavior"
        }
    ]
    
    for i, target in enumerate(validation_targets, 1):
        with st.expander(f"{i}. {target['mechanism']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Positive Ion Targets:**")
                st.code(target["positive_ions"])
            with col2:
                st.markdown("**Negative Ion Evidence:**")
                st.info(target["negative_correlation"])
            st.markdown(f"**Validation Logic:** {target['validation']}")
    
    # Cross-correlation matrix
    st.markdown("### 🔄 Expected Ion Pair Correlations")
    
    # Get counterparts from positive database
    counterparts = pos_fragment_db.get_negative_ion_counterparts()
    
    if counterparts:
        correlation_data = []
        for pos_ion, neg_ion in counterparts.items():
            if pos_ion in pos_fragment_db.fragments:
                pos_frag = pos_fragment_db.fragments[pos_ion]
                correlation_data.append({
                    "Positive Ion": f"{pos_frag['formula']} (m/z {pos_frag['mz']:.4f})",
                    "Negative Ion": f"{neg_ion}",
                    "Expected Correlation": pos_frag.get("expected_trend", "varies"),
                    "Chemical Significance": pos_frag["description"]
                })
        
        if correlation_data:
            import pandas as pd
            corr_df = pd.DataFrame(correlation_data)
            st.dataframe(corr_df, use_container_width=True, hide_index=True)
    
    # Fragment assignment export for correlation
    st.markdown("### 📊 Export Fragment Assignments")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Positive Ion Assignments", type="primary"):
            try:
                # Check if method exists
                if not hasattr(pos_fragment_db, 'generate_fragment_report'):
                    st.error("❌ Positive fragment database missing method. Please restart Streamlit.")
                    return
                    
                pos_report = pos_fragment_db.generate_fragment_report(pca_analysis.loadings_df, top_n=50)
                csv_data = pos_report.to_csv(index=False)
                st.download_button(
                    "📥 Download Positive Assignments CSV",
                    csv_data,
                    "positive_ion_assignments.csv",
                    "text/csv"
                )
                st.success("✅ Positive ion assignments ready for download!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.markdown("**Next Steps:**")
        st.markdown("""
        1. Export positive ion fragment assignments
        2. Compare with negative ion verified fragments  
        3. Validate key mechanisms (aromatic formation, carbonyl cascade)
        4. Resolve unknown fragments (e.g., m/z 68.9984)
        5. Generate comprehensive correlation report
        """)
    
    # Specific unknown fragment analysis
    st.markdown("### ❓ Unknown Fragment Resolution")
    
    unknown_validation = {
        "m/z 68.9984 (Unknown)": {
            "candidates": ["CF2H-", "C3HO2-", "Al13C-", "C5H-"],
            "positive_checks": [
                "CF2H+ at m/z 68.9950",
                "C3HO2+ at m/z 69.0027", 
                "Al+ presence confirms Al-carbon possible",
                "C5H+ at m/z 61.0078"
            ]
        }
    }
    
    for unknown, info in unknown_validation.items():
        with st.expander(f"Resolve: {unknown}", expanded=False):
            st.markdown("**Candidate Identities:**")
            for i, (candidate, check) in enumerate(zip(info["candidates"], info["positive_checks"])):
                st.markdown(f"{i+1}. **{candidate}** → Check: {check}")


def extract_square_from_name(sample_name):
    """Extract square information from sample name"""
    if '_SQ' in sample_name:
        try:
            square = sample_name.split('_SQ')[1].split('_')[0]
            return f"SQ{square}"
        except:
            return 'N/A'
    return 'N/A'


if __name__ == "__main__":
    main()