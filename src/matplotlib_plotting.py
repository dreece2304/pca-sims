"""
Scientific Publication Quality Matplotlib Plotting for ToF-SIMS PCA
Optimized for journal submission and high-quality figures
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.style as mplstyle
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
from scipy import stats

def setup_matplotlib_for_screen():
    """Setup matplotlib with screen-appropriate settings"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            screen_dpi = screen.logicalDotsPerInch()
            device_ratio = screen.devicePixelRatio()
        else:
            screen_dpi = 96
            device_ratio = 1.0
    except:
        screen_dpi = 96
        device_ratio = 1.0
    
    # Scale font sizes based on DPI
    base_font_size = 10
    font_scale = max(1.0, screen_dpi / 96.0)
    scaled_font_size = int(base_font_size * font_scale)
    
    # Set publication-quality style with DPI awareness
    plt.rcParams.update({
        'font.size': scaled_font_size,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
        'axes.linewidth': 1.0 * font_scale,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'xtick.major.size': 4 * font_scale,
        'xtick.minor.size': 2 * font_scale,
        'ytick.major.size': 4 * font_scale,
        'ytick.minor.size': 2 * font_scale,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'lines.linewidth': 1.5 * font_scale,
        'grid.alpha': 0.3,
        'legend.frameon': False,
        'figure.dpi': max(100, screen_dpi),
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1
    })
    
    return screen_dpi, font_scale

# Initialize with screen-appropriate settings
screen_dpi, font_scale = setup_matplotlib_for_screen()

def calculate_confidence_ellipse(x, y, confidence=0.95):
    """
    Calculate confidence ellipse for 2D data with small sample correction
    
    Parameters:
    x, y: array-like, data points
    confidence: float, confidence level (0.95 for 95%)
    
    Returns:
    center, width, height, angle, sample_info
    
    What the ellipse represents:
    - For n >= 30: Shows region containing ~95% of future data points (prediction ellipse)
    - For n < 30: Shows region with small-sample correction using Hotelling's T²
    - For n < 5: Shows approximate data spread (use with caution)
    
    Mathematical basis:
    - Large samples: Chi-square distribution (χ² with df=2)
    - Small samples: Hotelling's T² distribution with finite sample correction
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 points for confidence ellipse")
    
    # Calculate mean (center of ellipse)
    center = (np.mean(x), np.mean(y))
    
    # Center the data
    x_centered = x - center[0]
    y_centered = y - center[1]
    
    # Calculate sample covariance matrix (with n-1 denominator)
    cov = np.cov(x_centered, y_centered, ddof=1)
    
    # Handle edge case of zero variance
    if np.any(np.diag(cov) <= 0):
        # Fallback: create small circular ellipse
        width = height = 0.1
        angle = 0
        sample_info = f"n={n} (zero variance - using fallback)"
        return center, width, height, angle, sample_info
    
    # Calculate eigenvalues and eigenvectors
    eigenvals, eigenvecs = np.linalg.eigh(cov)
    
    # Sort by eigenvalue (largest first)
    idx = eigenvals.argsort()[::-1]
    eigenvals = eigenvals[idx]
    eigenvecs = eigenvecs[:, idx]
    
    # Calculate the angle of the ellipse (angle of largest eigenvector)
    angle = np.degrees(np.arctan2(eigenvecs[1, 0], eigenvecs[0, 0]))
    
    # Choose appropriate distribution based on sample size
    if n >= 30:
        # Large sample: use chi-square
        critical_val = stats.chi2.ppf(confidence, df=2)
        scale_factor = 1.0
        method = "χ² (large sample)"
    elif n >= 5:
        # Small sample: use Hotelling's T² with finite sample correction
        # T² = (n-1) * 2 / (n-2) * F(α, 2, n-2)
        f_val = stats.f.ppf(confidence, 2, n-2)
        critical_val = (n-1) * 2 * f_val / (n-2)
        scale_factor = 1.0
        method = f"Hotelling T² (n={n})"
    else:
        # Very small sample: use chi-square with warning
        critical_val = stats.chi2.ppf(confidence, df=2)
        scale_factor = 1.0
        method = f"χ² (n={n}, use with caution)"
    
    # Calculate ellipse semi-axes
    semi_major = np.sqrt(critical_val * eigenvals[0])
    semi_minor = np.sqrt(critical_val * eigenvals[1])
    
    # Full width and height (diameter = 2 * radius)
    width = 2 * semi_major
    height = 2 * semi_minor
    
    sample_info = f"n={n}, {method}"
    
    return center, width, height, angle, sample_info

class PCAPlotCanvas(FigureCanvas):
    """Matplotlib canvas for PCA plots integrated with Qt"""
    
    def __init__(self, parent=None, width=8, height=6, dpi=None):
        # Auto-detect DPI from screen if not specified
        if dpi is None:
            try:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    screen = app.primaryScreen()
                    dpi = screen.logicalDotsPerInch()
                else:
                    dpi = 100
            except:
                dpi = 100
        
        # Ensure reasonable DPI bounds
        dpi = max(72, min(dpi, 300))
        
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Store DPI for export
        self.plot_dpi = dpi
        
        # Enable navigation toolbar
        self.axes = None
        
        # Store data for tooltips
        self.scores_data = None
        self.tooltip_annotations = []
        self.current_tooltip = None
        
        # Connect hover events
        self.mpl_connect('motion_notify_event', self.on_hover)
        
    def plot_pca_results(self, pca_analyzer):
        """Create comprehensive PCA results plot"""
        self.fig.clear()
        
        # Create 2x2 subplot layout
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Variance explained (scree plot) - Publication style
        ax1 = self.fig.add_subplot(gs[0, 0])
        variance_ratios = pca_analyzer.explained_variance_ratio * 100
        components = range(1, len(variance_ratios) + 1)
        
        # Use viridis colors for consistency
        bars = ax1.bar(components, variance_ratios, alpha=0.8, color='#440154',
                      edgecolor='black', linewidth=0.8)
        ax1.set_xlabel('Principal Component', fontweight='bold')
        ax1.set_ylabel('Variance Explained (%)', fontweight='bold')
        ax1.set_title('A) Scree Plot', fontweight='bold', loc='left')
        
        # Remove top and right spines for clean look
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # Add percentage labels on bars (publication style)
        for bar, pct in zip(bars, variance_ratios):
            if pct > 5:  # Only label significant components
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{pct:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Set reasonable y-axis limits
        ax1.set_ylim(0, max(variance_ratios) * 1.15)
        
        # 2. PC1 vs PC2 scores - Publication style
        ax2 = self.fig.add_subplot(gs[0, 1])
        scores_df = pca_analyzer.get_scores_dataframe()
        
        # Store scores data for tooltips
        self.scores_data = scores_df
        self.scores_ax = ax2
        
        # Publication-quality color scheme with discrete legend
        if 'dose_id' in scores_df.columns:
            # Use discrete viridis colors for discrete dose levels
            unique_doses = sorted(scores_df['dose_id'].unique())
            colors = ['#440154', '#3B528B', '#21908C', '#5DC863', '#FDE725',
                     '#DCE319', '#B8DE29', '#73D055', '#1F968B', '#414487']
            
            for i, dose in enumerate(unique_doses):
                mask = scores_df['dose_id'] == dose
                color = colors[i % len(colors)]
                
                # Plot data points
                dose_data = scores_df.loc[mask]
                ax2.scatter(dose_data['PC1'], dose_data['PC2'], 
                           alpha=0.8, s=60, color=color, edgecolors='black', linewidth=0.5,
                           label=f'Dose {dose}')
                
                # Add 95% confidence ellipse if we have enough points
                if len(dose_data) >= 3:
                    try:
                        center, width, height, angle, sample_info = calculate_confidence_ellipse(
                            dose_data['PC1'], dose_data['PC2'], confidence=0.95)
                        
                        ellipse = Ellipse(center, width, height, angle=angle,
                                        facecolor='none', edgecolor=color, 
                                        linestyle='--', linewidth=1.5, alpha=0.6)
                        ax2.add_patch(ellipse)
                        
                        # Add ellipse info to legend only for first dose
                        if i == 0:
                            # Create invisible line for legend entry
                            ax2.plot([], [], color='gray', linestyle='--', linewidth=1.5, 
                                   label=f'95% CI per dose ({sample_info})')
                    except Exception as e:
                        # Skip ellipse if calculation fails
                        print(f"Warning: Could not calculate ellipse for dose {dose}: {e}")
                        pass
            
            # Add legend instead of colorbar
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        else:
            # No dose information available - use viridis mid-tone
            ax2.scatter(scores_df['PC1'], scores_df['PC2'], alpha=0.8, s=60,
                       color='#21908C', edgecolors='black', linewidth=0.5)
            
            # Note: No confidence ellipse here because mixed samples from different 
            # chemical conditions would not be scientifically meaningful
        
        ax2.set_xlabel(f'PC1 ({variance_ratios[0]:.1f}%)', fontweight='bold')
        ax2.set_ylabel(f'PC2 ({variance_ratios[1]:.1f}%)', fontweight='bold')
        ax2.set_title('B) Scores Plot', fontweight='bold', loc='left')
        
        # Clean up spines
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # Add origin lines for reference
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        # 3. PC1 loadings (highest at top)
        ax3 = self.fig.add_subplot(gs[1, 0])
        loadings_df = pca_analyzer.get_loadings_dataframe()
        pc1_loadings = loadings_df['PC1'].abs().sort_values(ascending=True).head(15)  # ascending=True puts highest at top

        y_pos = np.arange(len(pc1_loadings))
        bars = ax3.barh(y_pos, pc1_loadings.values, alpha=0.8, color='#21908C')  # viridis mid-tone
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels([f'{idx:.3f}' for idx in pc1_loadings.index], fontsize=8)
        ax3.set_xlabel('|PC1 Loading|', fontweight='bold')
        ax3.set_title('C) Top PC1 Loadings', fontweight='bold', loc='left')
        ax3.grid(True, alpha=0.3, axis='x')

        # Clean up spines
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        
        # 4. Dose response (if available)
        ax4 = self.fig.add_subplot(gs[1, 1])
        
        if 'dose_id' in scores_df.columns:
            # PC1 vs dose correlation with viridis styling
            dose_groups = scores_df.groupby('dose_id')['PC1'].mean()
            ax4.plot(dose_groups.index, dose_groups.values, 'o-', linewidth=2.5, markersize=8,
                    color='#440154', markerfacecolor='#FDE725', markeredgecolor='#440154')
            ax4.set_xlabel('Dose ID', fontweight='bold')
            ax4.set_ylabel('PC1 Score', fontweight='bold')
            ax4.set_title('D) Dose Response', fontweight='bold', loc='left')
            ax4.grid(True, alpha=0.3)

            # Clean up spines
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)

            # Calculate correlation
            corr = np.corrcoef(dose_groups.index, dose_groups.values)[0, 1]
            ax4.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax4.transAxes,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontweight='bold')
        else:
            # Summary statistics table
            summary = pca_analyzer.get_results_summary()
            ax4.axis('off')
            
            table_data = [
                ['Samples', f"{summary['n_samples']}"],
                ['Masses', f"{summary['n_masses']}"],
                ['Components', f"{summary['n_components']}"],
                ['Total Var.', f"{summary['total_variance_explained']*100:.1f}%"]
            ]
            
            table = ax4.table(cellText=table_data, 
                            colLabels=['Metric', 'Value'],
                            cellLoc='center',
                            loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            ax4.set_title('D) Summary Statistics', fontweight='bold', loc='left')
        
        # Refresh canvas
        self.draw()
    
    def on_hover(self, event):
        """Handle mouse hover events to show tooltips"""
        if event.inaxes != getattr(self, 'scores_ax', None) or self.scores_data is None:
            # Remove tooltip if not over scores plot
            if self.current_tooltip:
                self.current_tooltip.remove()
                self.current_tooltip = None
                self.draw_idle()
            return
        
        # Find closest point
        if event.xdata is None or event.ydata is None:
            return
        
        try:
            distances = ((self.scores_data['PC1'] - event.xdata)**2 + 
                        (self.scores_data['PC2'] - event.ydata)**2)**0.5
            
            min_distance = distances.min()
            if min_distance < 0.5:  # Threshold for proximity
                closest_idx = distances.idxmin()
                sample_data = self.scores_data.loc[closest_idx]
                
                # Create tooltip text
                sample_name = sample_data.get('sample_name', f'Sample {closest_idx}')
                pc1_val = sample_data['PC1']
                pc2_val = sample_data['PC2']
                dose_id = sample_data.get('dose_id', 'N/A')
                
                tooltip_text = f"{sample_name}\nPC1: {pc1_val:.3f}\nPC2: {pc2_val:.3f}\nDose: {dose_id}"
                
                # Remove old tooltip
                if self.current_tooltip:
                    self.current_tooltip.remove()
                
                # Add new tooltip
                self.current_tooltip = self.scores_ax.annotate(
                    tooltip_text,
                    xy=(pc1_val, pc2_val),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                    fontsize=9,
                    ha='left'
                )
                
                self.draw_idle()
            else:
                # Remove tooltip if not close to any point
                if self.current_tooltip:
                    self.current_tooltip.remove()
                    self.current_tooltip = None
                    self.draw_idle()
        except Exception:
            # Silently handle any errors in tooltip display
            pass
    
    def export_plot(self, filename):
        """Export plot to file with appropriate DPI"""
        # Use high DPI for exports (at least 300 for publications)
        export_dpi = max(300, self.plot_dpi)
        self.fig.savefig(filename, dpi=export_dpi, bbox_inches='tight')


class InteractivePCAPlots:
    """Create interactive matplotlib plots with navigation"""
    
    @staticmethod
    def create_detailed_scores_plot(pca_analyzer, save_path=None):
        """Create detailed scores plot with annotations"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        scores_df = pca_analyzer.get_scores_dataframe()
        variance_ratios = pca_analyzer.explained_variance_ratio * 100
        
        # Create scatter plot
        if 'dose_id' in scores_df.columns:
            scatter = ax.scatter(scores_df['PC1'], scores_df['PC2'], 
                               c=scores_df['dose_id'], cmap='viridis', 
                               alpha=0.7, s=60, edgecolors='black', linewidth=0.5)
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Dose ID', fontsize=12)
        else:
            ax.scatter(scores_df['PC1'], scores_df['PC2'], alpha=0.7, s=60)
        
        # Add sample labels (optional, for small datasets)
        if len(scores_df) <= 20 and 'sample_name' in scores_df.columns:
            for idx, row in scores_df.iterrows():
                ax.annotate(row['sample_name'], (row['PC1'], row['PC2']),
                          xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax.set_xlabel(f'PC1 ({variance_ratios[0]:.1f}%)', fontsize=12)
        ax.set_ylabel(f'PC2 ({variance_ratios[1]:.1f}%)', fontsize=12)
        ax.set_title('PCA Scores Plot - ToF-SIMS Data', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add zero lines
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax.axvline(x=0, color='k', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    @staticmethod  
    def create_loadings_plot(pca_analyzer, save_path=None, top_n=20):
        """Create detailed loadings plot"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        loadings_df = pca_analyzer.get_loadings_dataframe()
        
        # PC1 loadings spectrum
        masses = loadings_df.index.values
        pc1_loadings = loadings_df['PC1'].values
        
        ax1.stem(masses, pc1_loadings, linefmt='b-', markerfmt='bo', basefmt=' ')
        ax1.set_xlabel('m/z', fontsize=12)
        ax1.set_ylabel('PC1 Loading', fontsize=12)
        ax1.set_title('PC1 Loadings Spectrum', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Top loadings bar chart (highest at top)
        top_loadings = loadings_df['PC1'].abs().sort_values(ascending=True).head(top_n)  # ascending=True puts highest at top
        y_pos = np.arange(len(top_loadings))

        bars = ax2.barh(y_pos, top_loadings.values, alpha=0.8)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels([f'{idx:.3f}' for idx in top_loadings.index])
        ax2.set_xlabel('|PC1 Loading|', fontsize=12)
        ax2.set_title(f'Top {top_n} PC1 Loadings', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')

        # Color bars using viridis colors for positive/negative
        original_loadings = loadings_df.loc[top_loadings.index, 'PC1']
        for bar, loading in zip(bars, original_loadings):
            bar.set_color('#FDE725' if loading < 0 else '#440154')  # viridis yellow/purple
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig