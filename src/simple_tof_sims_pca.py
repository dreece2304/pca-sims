"""
Simple ToF-SIMS PCA Analysis with Clear Mathematical Steps
Educational implementation with detailed mathematical explanations
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class SimpleToFSIMSPCA:
    """
    Simple ToF-SIMS PCA analysis with clear mathematical steps and explanations
    """
    
    def __init__(self, data_file: str):
        """
        Initialize PCA analysis
        
        Args:
            data_file: Path to tab-delimited ToF-SIMS data file
        """
        self.data_file = data_file
        
        # Raw data containers
        self.raw_data = None
        self.mass_values = None
        self.sample_metadata = None
        
        # Preprocessed data containers
        self.preprocessed_data = None
        self.preprocessing_steps = []
        
        # PCA results
        self.pca_model = None
        self.scores = None
        self.loadings = None
        self.explained_variance_ratio = None
        self.explained_variance = None
        
        print("🔬 Simple ToF-SIMS PCA Analysis Initialized")
        print("=" * 50)
    
    def load_data(self) -> None:
        """
        Load ToF-SIMS data and parse P#_SQ# format
        """
        print("📁 Loading ToF-SIMS data...")
        
        try:
            # Read tab-delimited file
            df = pd.read_csv(self.data_file, sep='\t')
            print(f"   Raw data shape: {df.shape}")
            
            # Extract mass values (first column)
            mass_column = df.columns[0]
            self.mass_values = df[mass_column].values
            print(f"   Mass range: {self.mass_values.min():.3f} - {self.mass_values.max():.3f} Da")
            print(f"   Number of masses: {len(self.mass_values)}")
            
            # Set mass as index and extract sample data
            df.set_index(mass_column, inplace=True)
            self.raw_data = df.copy()
            
            # Parse sample names (P#_SQ# format)
            self._parse_sample_metadata()
            
            print(f"   Successfully parsed {len(self.raw_data.columns)} samples")
            print("   ✅ Data loading complete")
            
        except Exception as e:
            raise ValueError(f"Error loading data: {e}")
    
    def _parse_sample_metadata(self) -> None:
        """
        Parse P#_SQ# format sample names into metadata
        
        Mathematical Note:
        - P1, P2, P3 = Triplicates (experimental replicates)  
        - SQ0, SQ1, SQ2, etc. = Doses (electron beam doses)
        - Each dose should appear 3 times (once per triplicate)
        """
        print("🔍 Parsing sample metadata...")
        
        metadata = []
        for sample_name in self.raw_data.columns:
            if '_' in sample_name:
                try:
                    pattern, square = sample_name.split('_')
                    pattern_num = int(pattern.replace('P', ''))
                    dose_num = int(square.replace('SQ', ''))
                    
                    metadata.append({
                        'sample_name': sample_name,
                        'pattern': pattern_num,
                        'dose': dose_num,
                        'replicate_id': pattern_num,
                        'dose_id': dose_num
                    })
                except:
                    # Fallback for non-standard names
                    metadata.append({
                        'sample_name': sample_name,
                        'pattern': 1,
                        'dose': 0,
                        'replicate_id': 1,
                        'dose_id': 0
                    })
            else:
                # Fallback for formats without underscore
                metadata.append({
                    'sample_name': sample_name,
                    'pattern': 1,
                    'dose': 0,
                    'replicate_id': 1,
                    'dose_id': 0
                })
        
        self.sample_metadata = pd.DataFrame(metadata)
        
        # Print experimental design summary
        print("   Experimental Design Summary:")
        dose_counts = self.sample_metadata.groupby('dose_id').size()
        for dose, count in dose_counts.items():
            print(f"   - SQ{dose}: {count} replicates")
        
        total_doses = len(dose_counts)
        expected_replicates = 3
        if all(count == expected_replicates for count in dose_counts):
            print(f"   ✅ Balanced design: {total_doses} doses × {expected_replicates} replicates")
        else:
            print(f"   ⚠️  Unbalanced design detected")
    
    def select_doses(self, dose_ids: List[int]) -> None:
        """
        Select which doses to include in analysis
        
        Args:
            dose_ids: List of dose IDs (e.g., [0, 1, 2, 3, 4, 5])
        """
        print(f"🎯 Selecting doses: {dose_ids}")
        
        # Filter samples based on selected doses
        selected_mask = self.sample_metadata['dose_id'].isin(dose_ids)
        selected_samples = self.sample_metadata[selected_mask]['sample_name'].tolist()
        
        # Update data and metadata
        self.raw_data = self.raw_data[selected_samples]
        self.sample_metadata = self.sample_metadata[selected_mask].reset_index(drop=True)
        
        print(f"   Selected {len(selected_samples)} samples")
        print(f"   Doses included: {sorted(dose_ids)}")
    
    def preprocess_data(self,
                       sqrt_transform: bool = True,
                       mean_center: bool = True,
                       pareto_scale: bool = True,
                       filter_cl_peaks: bool = False,
                       filter_si_peaks: bool = False) -> None:
        """
        Preprocess data for PCA with clear mathematical explanations

        Args:
            sqrt_transform: Apply √(x) transformation
            mean_center: Subtract column means
            pareto_scale: Divide by √(std) per mass
            filter_cl_peaks: Remove Cl- peaks (m/z 34.971 and 36.968) before analysis
            filter_si_peaks: Remove Si+ peaks (m/z 27.984 and related) before analysis

        Mathematical Steps:
        0. Contamination filtering: Remove contamination peaks from dataset
           - Cl peaks: m/z 34.971 (³⁵Cl⁻) and 36.968 (³⁷Cl⁻)
           - Si peaks: m/z 27.984 (²⁸Si⁺) and related silicon fragments

        1. √ transform: Stabilizes variance for count data (Poisson-like)
           X_new = √(X_old)

        2. Mean centering: Required for covariance-based PCA
           X_centered = X - mean(X) for each mass

        3. Pareto scaling: Compromise between no scaling and unit variance
           X_pareto = X_centered / √(std(X)) for each mass
        """
        print("⚙️ Preprocessing data with mathematical transformations...")
        self.preprocessing_steps = []

        # Always start with raw data
        data = self.raw_data.copy()
        print(f"   Starting data shape: {data.shape} (masses × samples)")

        # Step 0: Cl peak filtering (if requested) - use masking instead of permanent removal
        mask_indices = None
        if filter_cl_peaks:
            print("   🧹 Step 0: Cl peak filtering")
            print("      Purpose: Mask contamination peaks during analysis")
            print("      Targets: m/z 34.971 (³⁵Cl⁻) and 36.968 (³⁷Cl⁻)")

            # Define Cl peak masses with tolerance
            cl35_mass = 34.971
            cl37_mass = 36.968
            tolerance = 0.01  # 10 mDa tolerance

            # Create mask for peaks to exclude
            mass_indices = data.index
            cl_mask = np.ones(len(mass_indices), dtype=bool)  # Start with all True (keep all)
            cl_peaks_found = 0

            for i, mass in enumerate(mass_indices):
                if (abs(mass - cl35_mass) <= tolerance or
                    abs(mass - cl37_mass) <= tolerance):
                    cl_mask[i] = False  # Mark for exclusion
                    cl_peaks_found += 1
                    print(f"      Found Cl peak at m/z {mass:.6f} (masked)")

            if cl_peaks_found > 0:
                # Apply mask to data
                data = data.iloc[cl_mask]
                mask_indices = cl_mask
                print(f"      Masked {cl_peaks_found} Cl peaks")
                print(f"      New data shape: {data.shape} (masses × samples)")
                self.preprocessing_steps.append("filter_cl_peaks")
            else:
                print("      No Cl peaks found in current dataset")

        # Step 0b: Si peak filtering (if requested) - use masking
        if filter_si_peaks:
            print("   🧹 Step 0b: Si peak filtering")
            print("      Purpose: Mask silicon contamination peaks during analysis")
            print("      Targets: m/z 27.984 (²⁸Si⁺) and related silicon fragments")

            # Define Si peak masses with tolerance
            si28_mass = 27.984  # ²⁸Si⁺
            si29_mass = 28.976  # ²⁹Si⁺
            si30_mass = 29.974  # ³⁰Si⁺
            sih_mass = 28.991   # SiH⁺
            tolerance = 0.01    # 10 mDa tolerance

            # Create mask for peaks to exclude
            mass_indices = data.index
            si_mask = np.ones(len(mass_indices), dtype=bool)  # Start with all True (keep all)
            si_peaks_found = 0

            for i, mass in enumerate(mass_indices):
                if (abs(mass - si28_mass) <= tolerance or
                    abs(mass - si29_mass) <= tolerance or
                    abs(mass - si30_mass) <= tolerance or
                    abs(mass - sih_mass) <= tolerance):
                    si_mask[i] = False  # Mark for exclusion
                    si_peaks_found += 1
                    print(f"      Found Si peak at m/z {mass:.6f} (masked)")

            if si_peaks_found > 0:
                # Apply mask to data
                data = data.iloc[si_mask]
                print(f"      Masked {si_peaks_found} Si peaks")
                print(f"      New data shape: {data.shape} (masses × samples)")
                self.preprocessing_steps.append("filter_si_peaks")
            else:
                print("      No Si peaks found in current dataset")

        # Step 1: Square root transformation
        if sqrt_transform:
            print("   📊 Step 1: Square root transformation")
            print("      Mathematical purpose: Variance stabilization for count data")
            print("      Formula: X_new = √(X_old)")
            
            # Check for negative values
            if (data < 0).any().any():
                print("      ⚠️  Warning: Negative values detected - will be set to 0 before √")
                data = data.clip(lower=0)
            
            data = np.sqrt(data)
            self.preprocessing_steps.append("sqrt_transform")
            print("      ✅ Square root transformation applied")
        
        # Transpose for PCA computation (samples as rows, masses as columns)
        data = data.T
        print(f"   Transposed data shape: {data.shape} (samples × masses)")
        
        # Step 2: Mean centering
        if mean_center:
            print("   📊 Step 2: Mean centering")
            print("      Mathematical purpose: Required for covariance-based PCA")
            print("      Formula: X_centered = X - mean(X) for each mass")
            
            column_means = data.mean(axis=0)
            print(f"      Mean range: {column_means.min():.6f} to {column_means.max():.6f}")
            
            data = data - column_means
            self.preprocessing_steps.append("mean_center")
            print("      ✅ Mean centering applied")
        
        # Step 3: Pareto scaling
        if pareto_scale:
            print("   📊 Step 3: Pareto scaling")
            print("      Mathematical purpose: Balance large vs small peaks")
            print("      Formula: X_pareto = X_centered / √(std(X)) for each mass")
            
            column_stds = data.std(axis=0)
            print(f"      Std dev range: {column_stds.min():.6f} to {column_stds.max():.6f}")
            
            # Avoid division by zero
            column_stds = np.where(column_stds == 0, 1, column_stds)
            data = data / np.sqrt(column_stds)
            self.preprocessing_steps.append("pareto_scale")
            print("      ✅ Pareto scaling applied")
        
        self.preprocessed_data = data

        # Store the mask information for consistent mass indexing
        if mask_indices is not None:
            self.current_mass_mask = mask_indices
            self.current_mass_values = self.mass_values[mask_indices]
        else:
            self.current_mass_mask = np.ones(len(self.mass_values), dtype=bool)
            self.current_mass_values = self.mass_values.copy()

        # Debug: Ensure current_mass_values matches preprocessed data shape
        expected_masses = self.preprocessed_data.shape[1]  # number of columns (masses)
        actual_masses = len(self.current_mass_values)
        if expected_masses != actual_masses:
            print(f"   ⚠️  Mass index adjustment: Expected {expected_masses}, got {actual_masses}")
            # Create sequential index if sizes don't match
            self.current_mass_values = np.arange(expected_masses)

        print(f"   Final preprocessed data shape: {data.shape}")
        print(f"   Data range: {data.values.min():.6f} to {data.values.max():.6f}")
        print(f"   Active masses: {len(self.current_mass_values)}/{len(self.mass_values)}")
        print("   ✅ Preprocessing complete")
    
    def run_pca(self, n_components: int = 10) -> None:
        """
        Run PCA analysis with mathematical verification
        
        Args:
            n_components: Number of principal components to compute
            
        Mathematical Background:
        PCA finds the directions of maximum variance in the data.
        
        For data matrix X (samples × masses):
        1. Covariance matrix: C = (1/(n-1)) * X^T * X
        2. Eigendecomposition: C * v = λ * v
           - λ (eigenvalues) = variance explained by each PC
           - v (eigenvectors) = loadings (mass contributions)
        3. Scores = X * loadings (sample positions in PC space)
        
        sklearn uses SVD for numerical stability: X = U * S * V^T
        - V^T = loadings
        - U * S = scores  
        - S² / (n-1) = eigenvalues
        """
        print("🧮 Running PCA with mathematical verification...")
        
        if self.preprocessed_data is None:
            raise ValueError("Data must be preprocessed first")
        
        n_samples, n_masses = self.preprocessed_data.shape
        print(f"   Input data: {n_samples} samples × {n_masses} masses")
        
        # Fit PCA model
        print("   Computing principal components using SVD...")
        self.pca_model = PCA(n_components=min(n_components, n_samples-1))
        
        # Fit and transform
        self.scores = self.pca_model.fit_transform(self.preprocessed_data)
        self.loadings = self.pca_model.components_.T  # Transpose to get masses × PCs
        self.explained_variance_ratio = self.pca_model.explained_variance_ratio_
        self.explained_variance = self.pca_model.explained_variance_
        
        # Mathematical verification
        print("   🔍 Mathematical Verification:")
        print(f"      - Scores shape: {self.scores.shape}")
        print(f"      - Loadings shape: {self.loadings.shape}")
        print(f"      - Sum of variance ratios: {self.explained_variance_ratio.sum():.4f}")
        
        # Check orthogonality of loadings
        if n_components > 1:
            loading_correlation = np.corrcoef(self.loadings[:, 0], self.loadings[:, 1])[0, 1]
            print(f"      - PC1-PC2 loading correlation: {loading_correlation:.6f} (should be ~0)")
        
        # Reconstruction error
        reconstructed = self.scores @ self.loadings.T
        reconstruction_error = np.mean((self.preprocessed_data - reconstructed) ** 2)
        print(f"      - Reconstruction error: {reconstruction_error:.6f}")
        
        print("   📈 Variance Explained:")
        for i in range(min(5, len(self.explained_variance_ratio))):
            print(f"      - PC{i+1}: {self.explained_variance_ratio[i]:.3f} ({self.explained_variance_ratio[i]*100:.1f}%)")
        
        if len(self.explained_variance_ratio) > 5:
            cumsum = np.cumsum(self.explained_variance_ratio)
            print(f"      - Total (first {len(self.explained_variance_ratio)} PCs): {cumsum[-1]:.3f} ({cumsum[-1]*100:.1f}%)")
        
        print("   ✅ PCA analysis complete")
    
    def get_results_summary(self) -> Dict:
        """
        Get summary of PCA results for display
        """
        if self.pca_model is None:
            raise ValueError("PCA must be run first")
        
        return {
            'n_samples': self.scores.shape[0],
            'n_masses': self.loadings.shape[0], 
            'n_components': self.scores.shape[1],
            'total_variance_explained': self.explained_variance_ratio.sum(),
            'preprocessing_steps': self.preprocessing_steps,
            'dose_ids': sorted(self.sample_metadata['dose_id'].unique()),
            'replicates_per_dose': self.sample_metadata.groupby('dose_id').size().to_dict()
        }
    
    def get_scores_dataframe(self) -> pd.DataFrame:
        """
        Get PCA scores as DataFrame with sample metadata
        """
        if self.scores is None:
            raise ValueError("PCA must be run first")
        
        # Create scores DataFrame
        pc_labels = [f'PC{i+1}' for i in range(self.scores.shape[1])]
        scores_df = pd.DataFrame(self.scores, columns=pc_labels)
        
        # Add sample metadata
        scores_df = pd.concat([self.sample_metadata.reset_index(drop=True), scores_df], axis=1)
        
        return scores_df
    
    def get_loadings_dataframe(self) -> pd.DataFrame:
        """
        Get PCA loadings as DataFrame with proper mass indexing for filtered data
        """
        if self.loadings is None:
            raise ValueError("PCA must be run first")

        pc_labels = [f'PC{i+1}' for i in range(self.loadings.shape[1])]

        # Use current_mass_values if available (filtered data), otherwise use mass_values
        mass_index = getattr(self, 'current_mass_values', self.mass_values)

        # Verify shapes match
        if len(mass_index) != self.loadings.shape[0]:
            # Fallback: create a simple integer index if sizes don't match
            print(f"⚠️  Warning: Mass index size ({len(mass_index)}) doesn't match loadings size ({self.loadings.shape[0]})")
            print(f"   Using sequential mass index instead")
            mass_index = np.arange(self.loadings.shape[0])

        loadings_df = pd.DataFrame(
            self.loadings,
            columns=pc_labels,
            index=mass_index
        )

        return loadings_df
    
    def filter_loadings_by_importance(self, 
                                    pc_components: List[str] = None,
                                    variance_threshold: float = 0.01) -> pd.DataFrame:
        """
        Filter loadings to show only important contributors
        
        Args:
            pc_components: PCs to consider (e.g., ['PC1', 'PC2'])
            variance_threshold: Minimum variance threshold (0.01 = top 1%)
        """
        loadings_df = self.get_loadings_dataframe()
        
        if pc_components is None:
            pc_components = loadings_df.columns[:3]  # First 3 PCs
        
        # Calculate importance metric (sum of squared loadings)
        importance = (loadings_df[pc_components] ** 2).sum(axis=1)
        
        # Normalize and filter
        normalized_importance = importance / importance.max()
        significant_masses = normalized_importance >= variance_threshold
        
        filtered_loadings = loadings_df[significant_masses]
        
        print(f"🔍 Filtered loadings: {len(filtered_loadings)} / {len(loadings_df)} masses")
        print(f"   Retention rate: {len(filtered_loadings)/len(loadings_df)*100:.1f}%")
        
        return filtered_loadings


if __name__ == "__main__":
    # Test with your data
    pca = SimpleToFSIMSPCA("/home/dreece23/pca-sims/data/NegativeIon/NegIonTIC.txt")
    pca.load_data()
    pca.select_doses([1, 2, 3, 4, 5])  # Exclude SQ0 for now
    pca.preprocess_data(sqrt_transform=True, mean_center=True, pareto_scale=True)
    pca.run_pca(n_components=8)
    
    print("\n" + "="*50)
    print("🎉 TEST COMPLETE - Results Summary:")
    summary = pca.get_results_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")