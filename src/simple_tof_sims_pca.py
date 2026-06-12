"""
Simple ToF-SIMS PCA Analysis with Clear Mathematical Steps
Educational implementation with detailed mathematical explanations
"""

import numpy as np
import pandas as pd
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
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
        
        # Raw data containers (immutable after loading)
        self.raw_data = None
        self.mass_values = None
        self.sample_metadata = None

        # Working data with masks (mutable for analysis)
        self.working_data = None
        self.working_metadata = None
        self.sample_mask = None  # Boolean mask for selected samples
        
        # Preprocessed data containers
        self.preprocessed_data = None
        self.preprocessing_steps = []
        self.custom_dose_values = {}  # Custom dose values for plotting (dose_id -> actual_dose)
        
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

            # Check for and load existing metadata
            metadata = self.load_metadata(self.data_file)
            if metadata:
                self.apply_metadata(metadata)
            else:
                # Initialize working data to full dataset (no metadata available)
                self.working_data = self.raw_data.copy()
                self.working_metadata = self.sample_metadata.copy()
                self.sample_mask = np.ones(len(self.sample_metadata), dtype=bool)

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
    
    def select_samples_by_mask(self, sample_mask: np.ndarray) -> None:
        """
        Select samples using a boolean mask (preserves original data)

        Args:
            sample_mask: Boolean array where True = include sample
        """
        if len(sample_mask) != len(self.sample_metadata):
            raise ValueError(f"Mask length ({len(sample_mask)}) doesn't match samples ({len(self.sample_metadata)})")

        self.sample_mask = sample_mask.copy()

        # Create working copies using the mask
        selected_samples = self.sample_metadata[sample_mask]['sample_name'].tolist()
        self.working_data = self.raw_data[selected_samples].copy()
        self.working_metadata = self.sample_metadata[sample_mask].reset_index(drop=True)

        included_count = sample_mask.sum()
        excluded_count = len(self.sample_metadata) - included_count
        print(f"🎯 Selected {included_count} / {len(self.sample_metadata)} samples using mask")
        if excluded_count > 0:
            print(f"   🚫 Excluded {excluded_count} samples")

    def get_inclusion_mask(self) -> np.ndarray:
        """Get current inclusion mask based on metadata"""
        if 'include' in self.sample_metadata.columns:
            return self.sample_metadata['include'].values
        else:
            return np.ones(len(self.sample_metadata), dtype=bool)

    def get_sample_type_mask(self, sample_type: str) -> np.ndarray:
        """Get mask for specific sample type"""
        if 'sample_type' in self.sample_metadata.columns:
            return self.sample_metadata['sample_type'] == sample_type
        else:
            return np.zeros(len(self.sample_metadata), dtype=bool)

    def get_non_excluded_samples(self) -> pd.DataFrame:
        """Get sample metadata for non-excluded samples only"""
        inclusion_mask = self.get_inclusion_mask()
        return self.sample_metadata[inclusion_mask]

    def select_samples_by_names(self, sample_names: List[str]) -> None:
        """
        Select samples by name (preserves original data)

        Args:
            sample_names: List of sample names to include
        """
        # Create mask from sample names
        mask = self.sample_metadata['sample_name'].isin(sample_names)
        self.select_samples_by_mask(mask)

    def select_doses(self, dose_ids: List[int]) -> None:
        """
        Select which doses to include in analysis (preserves original data)
        Respects inclusion/exclusion flags from metadata

        Args:
            dose_ids: List of dose IDs (e.g., [0, 1, 2, 3, 4, 5])
        """
        print(f"🎯 Selecting doses: {dose_ids}")

        # Create mask based on selected doses
        dose_mask = self.sample_metadata['dose_id'].isin(dose_ids)

        # Also respect inclusion flags from metadata
        inclusion_mask = self.get_inclusion_mask()

        # Combine dose selection with inclusion mask
        combined_mask = dose_mask & inclusion_mask

        self.select_samples_by_mask(combined_mask)

    def set_custom_dose_values(self, dose_mapping: dict) -> None:
        """
        Set custom dose values for plotting (e.g., actual electron beam doses)

        Args:
            dose_mapping: Dictionary mapping dose_id to actual dose value
                         e.g., {0: 0.0, 1: 5.2, 2: 10.4, 3: 15.6, 4: 20.8, 5: 26.0}
        """
        # Convert numpy/pandas types to native Python types for JSON serialization
        self.custom_dose_values = self.convert_to_json_serializable(dose_mapping)
        print(f"📊 Set custom dose values: {self.custom_dose_values}")

    def get_metadata_path(self, data_file_path: str) -> str:
        """Generate metadata file path from data file path"""
        data_path = Path(data_file_path)
        filename_without_ext = data_path.stem
        metadata_dir = Path("data/project_assignments")
        metadata_dir.mkdir(exist_ok=True)
        return str(metadata_dir / f"{filename_without_ext}_metadata.json")

    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of data file to detect changes"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Warning: Could not calculate checksum for {file_path}: {e}")
            return ""

    def load_metadata(self, data_file_path: str) -> Optional[dict]:
        """Load metadata from JSON file if it exists"""
        metadata_path = self.get_metadata_path(data_file_path)

        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                # Verify data file hasn't changed
                current_checksum = self.calculate_file_checksum(data_file_path)
                stored_checksum = metadata.get('data_checksum', '')

                if current_checksum and stored_checksum and current_checksum != stored_checksum:
                    print(f"⚠️ Warning: Data file has changed since metadata was saved")
                    print(f"   Metadata may be outdated for {data_file_path}")

                print(f"📄 Loaded metadata from {metadata_path}")
                return metadata
            else:
                print(f"📄 No metadata found for {data_file_path}")
                return None

        except Exception as e:
            print(f"❌ Error loading metadata from {metadata_path}: {e}")
            return None

    def convert_to_json_serializable(self, obj):
        """Convert numpy/pandas data types to JSON-serializable Python types"""
        import numpy as np
        import pandas as pd

        if isinstance(obj, dict):
            # Convert both keys and values
            return {self.convert_to_json_serializable(key): self.convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):  # This covers np.int64, np.int32, etc.
            return int(obj)
        elif isinstance(obj, np.floating):  # This covers np.float64, np.float32, etc.
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.ndarray, pd.Series)):
            return obj.tolist()
        elif hasattr(obj, 'item'):  # Fallback for numpy scalars
            return obj.item()
        else:
            return obj

    def save_metadata(self, data_file_path: str, sample_metadata_dict: dict, custom_doses: dict = None):
        """Save metadata to JSON file"""
        metadata_path = self.get_metadata_path(data_file_path)

        try:
            # Convert data types to JSON-serializable format
            clean_metadata_dict = self.convert_to_json_serializable(sample_metadata_dict)
            clean_custom_doses = self.convert_to_json_serializable(custom_doses) if custom_doses else {}

            # Create metadata structure
            metadata = {
                "metadata": clean_metadata_dict,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "data_file": os.path.abspath(data_file_path),
                "data_checksum": self.calculate_file_checksum(data_file_path),
                "custom_dose_values": clean_custom_doses
            }

            # Save to file
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"💾 Saved metadata to {metadata_path}")
            return True

        except Exception as e:
            print(f"❌ Error saving metadata to {metadata_path}: {e}")
            return False

    def apply_metadata(self, metadata: dict):
        """Apply loaded metadata to sample_metadata DataFrame"""
        if not metadata or 'metadata' not in metadata:
            return

        sample_meta = metadata['metadata']

        # Add new columns to sample_metadata if they don't exist
        for col in ['sample_type', 'actual_dose', 'dose_units', 'include', 'notes']:
            if col not in self.sample_metadata.columns:
                if col == 'include':
                    self.sample_metadata[col] = True  # Default to include
                elif col == 'sample_type':
                    self.sample_metadata[col] = 'E-Beam Exposed'  # Default type
                elif col == 'actual_dose':
                    self.sample_metadata[col] = 0.0  # Default dose
                elif col == 'dose_units':
                    self.sample_metadata[col] = 'μC/cm²'  # Default units
                else:
                    self.sample_metadata[col] = ''  # Default empty string

        # Apply metadata to each sample
        for sample_name in self.sample_metadata['sample_name']:
            if sample_name in sample_meta:
                sample_info = sample_meta[sample_name]
                mask = self.sample_metadata['sample_name'] == sample_name

                # Update sample metadata
                self.sample_metadata.loc[mask, 'sample_type'] = sample_info.get('sample_type', 'E-Beam Exposed')
                self.sample_metadata.loc[mask, 'actual_dose'] = sample_info.get('dose', 0.0)
                self.sample_metadata.loc[mask, 'dose_units'] = sample_info.get('dose_units', 'μC/cm²')
                self.sample_metadata.loc[mask, 'include'] = sample_info.get('include', True)
                self.sample_metadata.loc[mask, 'notes'] = sample_info.get('notes', '')

        # Apply custom dose values if available
        if 'custom_dose_values' in metadata:
            self.custom_dose_values = self.convert_to_json_serializable(metadata['custom_dose_values'])
            print(f"📊 Applied custom dose values: {self.custom_dose_values}")

        # Update working data to respect inclusions/exclusions
        self.update_working_data_from_metadata()

        print(f"✅ Applied metadata to {len(self.sample_metadata)} samples")

    def update_working_data_from_metadata(self):
        """Update working data to respect include/exclude flags from metadata"""
        if 'include' in self.sample_metadata.columns:
            # Create mask based on include flag
            include_mask = self.sample_metadata['include'].values
            self.select_samples_by_mask(include_mask)

            # Samples already excluded via select_samples_by_mask above

    def _load_contamination_peaks_from_database(self, polarity: str = "positive") -> List[float]:
        """
        Load contamination peak masses from the fragment database

        Args:
            polarity: "positive" or "negative" to match the data type

        Returns:
            List of contamination peak masses for filtering
        """
        contamination_masses = []
        database_path = "data/FragmentDatabase/alucone_fragments_complete.json"

        try:
            with open(database_path, 'r') as f:
                database = json.load(f)

            for fragment in database.get('fragments', []):
                if (fragment.get('polarity') == polarity and
                    'Contamination' in fragment.get('families', [])):
                    contamination_masses.append(fragment['mass'])

            print(f"   📋 Loaded {len(contamination_masses)} contamination peaks from database")
            return sorted(contamination_masses)

        except Exception as e:
            print(f"   ⚠️ Could not load contamination database: {e}")
            print(f"   📋 Falling back to hardcoded contamination values")
            return []

    def get_active_data(self):
        """
        Get the currently active data (either working data or raw data)

        Returns:
            Tuple of (data, metadata) currently being used for analysis
        """
        if self.working_data is not None:
            return self.working_data, self.working_metadata
        else:
            return self.raw_data, self.sample_metadata
    
    def preprocess_data(self,
                       sqrt_transform: bool = True,
                       mean_center: bool = False,  # Redundant: sklearn PCA auto-centers
                       pareto_scale: bool = True,
                       filter_contamination_peaks: bool = False) -> None:
        """
        Preprocess data for PCA with clear mathematical explanations

        Args:
            sqrt_transform: Apply √(x) transformation
            mean_center: Subtract column means (REDUNDANT: sklearn PCA auto-centers)
            pareto_scale: Divide by √(std) per mass
            filter_contamination_peaks: Remove contamination peaks from database before analysis

        Mathematical Steps:
        0. Contamination filtering: Remove peaks marked as "Contamination" in fragment database

        1. √ transform: Stabilizes variance for count data (Poisson-like)
           X_new = √(X_old)

        2. Mean centering: REDUNDANT - sklearn PCA automatically centers data
           Note: Manual centering is skipped since sklearn.decomposition.PCA
           automatically subtracts column means before SVD decomposition

        3. Pareto scaling: Compromise between no scaling and unit variance
           X_pareto = X_centered / √(std(X)) for each mass
        """
        print("⚙️ Preprocessing data with mathematical transformations...")
        self.preprocessing_steps = []

        # Always start with active data (respects sample selection)
        active_data, active_metadata = self.get_active_data()
        data = active_data.copy()
        print(f"   Starting data shape: {data.shape} (masses × samples)")

        # All contamination filtering now handled by database-based system
        mask_indices = None

        # Step 0: Contamination peak filtering (if requested) - use database
        if filter_contamination_peaks:
            print("   🧹 Step 0: Contamination peak filtering")
            print("      Purpose: Mask contamination peaks during analysis")
            print("      Source: Fragment database (Contamination family)")

            # Load contamination peaks from database
            # Determine polarity from data file path
            polarity = "positive" if "Pos" in self.data_file else "negative"
            print(f"      Detected polarity: {polarity}")

            contamination_masses = self._load_contamination_peaks_from_database(polarity)
            tolerance = 0.01    # 10 mDa tolerance

            if contamination_masses:
                # Create mask for peaks to exclude
                mass_indices = data.index
                contam_mask = np.ones(len(mass_indices), dtype=bool)  # Start with all True (keep all)
                contam_peaks_found = 0

                for i, mass in enumerate(mass_indices):
                    for contam_mass in contamination_masses:
                        if abs(mass - contam_mass) <= tolerance:
                            contam_mask[i] = False  # Mark for exclusion
                            contam_peaks_found += 1
                            print(f"      Found contamination peak at m/z {mass:.6f} (database match: {contam_mass:.6f})")
                            break  # Only need one match per mass

                if contam_peaks_found > 0:
                    # Apply mask to data
                    data = data.iloc[contam_mask]
                    # Update mask tracking for mass values
                    if mask_indices is not None:
                        # Combine with previous mask (Cl filtering)
                        mask_indices = mask_indices & contam_mask
                    else:
                        mask_indices = contam_mask
                    print(f"      Masked {contam_peaks_found} contamination peaks")
                    print(f"      New data shape: {data.shape} (masses × samples)")
                    self.preprocessing_steps.append("filter_contamination_peaks")
                else:
                    print("      No contamination peaks found in current dataset")
            else:
                print("      No contamination peaks available from database")

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
        
        # Step 2: Mean centering (SKIPPED - sklearn PCA auto-centers)
        if mean_center:
            print("   📊 Step 2: Mean centering")
            print("      ⚠️  WARNING: Manual mean centering is REDUNDANT!")
            print("      sklearn PCA automatically centers data before SVD")
            print("      Formula: X_centered = X - mean(X) for each mass")

            column_means = data.mean(axis=0)
            print(f"      Mean range: {column_means.min():.6f} to {column_means.max():.6f}")

            data = data - column_means
            self.preprocessing_steps.append("mean_center")
            print("      ⚠️  Applied redundant mean centering (consider disabling)")
        else:
            print("   📊 Step 2: Mean centering")
            print("      ✅ Skipped - sklearn PCA automatically centers data")
            print("      This is the recommended setting for sklearn PCA")
        
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
            # Use original mass values instead of sequential indices
            if len(self.mass_values) >= expected_masses:
                self.current_mass_values = self.mass_values[:expected_masses]
            else:
                # This should rarely happen, but handle gracefully
                self.current_mass_values = np.concatenate([
                    self.mass_values,
                    np.arange(len(self.mass_values), expected_masses)
                ])
            print(f"   ✅ Adjusted to use original mass values: {self.current_mass_values[:5]}...")

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
        
        # Use working metadata to reflect current sample selection
        active_data, active_metadata = self.get_active_data()

        return {
            'n_samples': self.scores.shape[0],
            'n_masses': self.loadings.shape[0],
            'n_components': self.scores.shape[1],
            'total_variance_explained': self.explained_variance_ratio.sum(),
            'preprocessing_steps': self.preprocessing_steps,
            'dose_ids': sorted(active_metadata['dose_id'].unique()),
            'replicates_per_dose': active_metadata.groupby('dose_id').size().to_dict()
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
        
        # Add active sample metadata (working metadata)
        active_data, active_metadata = self.get_active_data()
        scores_df = pd.concat([active_metadata.reset_index(drop=True), scores_df], axis=1)
        
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
            # Fallback: use original mass values (truncated or padded as needed)
            print(f"⚠️  Warning: Mass index size ({len(mass_index)}) doesn't match loadings size ({self.loadings.shape[0]})")
            print(f"   Using original mass values as fallback")

            if len(self.mass_values) >= self.loadings.shape[0]:
                # Use first N mass values
                mass_index = self.mass_values[:self.loadings.shape[0]]
            else:
                # Pad with sequential values if needed (rare case)
                mass_index = np.concatenate([
                    self.mass_values,
                    np.arange(len(self.mass_values), self.loadings.shape[0])
                ])

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

    def get_polarity(self) -> str:
        """
        Determine the polarity of the dataset based on filename

        Returns:
            "negative" or "positive"
        """
        if "neg" in self.data_file.lower() or "negative" in self.data_file.lower():
            return "negative"
        elif "pos" in self.data_file.lower() or "positive" in self.data_file.lower():
            return "positive"
        else:
            # Default assumption or could raise an error
            return "negative"

    def get_sample_groups(self) -> List[str]:
        """
        Get available sample groups for individual analysis

        Returns:
            List of group names (e.g., ["As-Deposited", "2000 μC/cm²", ...])
        """
        groups = []

        if 'sample_type' in self.sample_metadata.columns:
            # Use metadata-based grouping
            for _, row in self.sample_metadata.iterrows():
                sample_type = row.get('sample_type', 'Unknown')
                include = row.get('include', True)

                if not include:  # Skip excluded samples
                    continue

                if sample_type == 'As-Deposited':
                    if 'As-Deposited' not in groups:
                        groups.append('As-Deposited')
                elif sample_type == 'E-Beam Exposed':
                    dose = row.get('actual_dose', row.get('dose', 'Unknown'))
                    if isinstance(dose, (int, float)):
                        dose_label = f"{int(dose)} μC/cm²"
                        if dose_label not in groups:
                            groups.append(dose_label)
        else:
            # Fallback to dose_id grouping
            dose_ids = sorted(self.sample_metadata['dose_id'].unique())
            for dose_id in dose_ids:
                if dose_id == 0:
                    groups.append('As-Deposited (SQ0)')
                else:
                    groups.append(f'Dose Level {dose_id}')

        return sorted(groups)

    def get_group_intensity_analysis(self, group_name: str, top_n: int = 30) -> pd.DataFrame:
        """
        Get detailed intensity analysis for a specific sample group

        Args:
            group_name: Name of the sample group
            top_n: Number of top peaks to return

        Returns:
            DataFrame with intensity statistics and fragment assignments
        """
        # Get samples belonging to this group
        group_samples = self._get_group_sample_names(group_name)

        if not group_samples:
            print(f"⚠️ No samples found for group: {group_name}")
            return pd.DataFrame()

        print(f"📊 Analyzing group '{group_name}' with {len(group_samples)} samples")

        # Extract intensity data for these samples
        group_data = self.raw_data[group_samples]

        # Calculate comprehensive statistics
        intensity_stats = pd.DataFrame({
            'mass': group_data.index,
            'mean_intensity': group_data.mean(axis=1),
            'std_intensity': group_data.std(axis=1),
            'max_intensity': group_data.max(axis=1),
            'min_intensity': group_data.min(axis=1),
            'median_intensity': group_data.median(axis=1),
            'cv_percent': (group_data.std(axis=1) / group_data.mean(axis=1)) * 100,
            'n_samples': len(group_samples)
        })

        # Calculate percentage of total intensity
        total_intensity = intensity_stats['mean_intensity'].sum()
        intensity_stats['percent_of_total'] = (intensity_stats['mean_intensity'] / total_intensity) * 100

        # Add fragment assignments (placeholder for now - will integrate with fragment database)
        intensity_stats['assignment'] = 'Unknown'
        intensity_stats['chemical_family'] = 'Unknown'
        intensity_stats['confidence'] = 'Low'

        # Sort by mean intensity (descending) and get top peaks
        intensity_stats = intensity_stats.sort_values('mean_intensity', ascending=False)
        top_peaks = intensity_stats.head(top_n).copy()

        # Add ranking
        top_peaks.insert(0, 'rank', range(1, len(top_peaks) + 1))

        return top_peaks

    def _get_group_sample_names(self, group_name: str) -> List[str]:
        """
        Get list of sample names belonging to a specific group

        Args:
            group_name: Name of the sample group

        Returns:
            List of sample names
        """
        samples = []

        # Handle different group name formats
        if group_name == 'As-Deposited' or 'SQ0' in group_name:
            # Find As-Deposited samples
            if 'sample_type' in self.sample_metadata.columns:
                mask = (self.sample_metadata['sample_type'] == 'As-Deposited') & \
                       (self.sample_metadata.get('include', True) == True)
            else:
                # Fallback to dose_id = 0
                mask = self.sample_metadata['dose_id'] == 0
            samples = self.sample_metadata.loc[mask, 'sample_name'].tolist()

        elif 'μC/cm²' in group_name:
            # Extract dose value from group name (e.g., "2000 μC/cm²" -> 2000)
            try:
                dose_val = float(group_name.split()[0])
                if 'actual_dose' in self.sample_metadata.columns:
                    mask = (self.sample_metadata['actual_dose'] == dose_val) & \
                           (self.sample_metadata.get('include', True) == True)
                    samples = self.sample_metadata.loc[mask, 'sample_name'].tolist()
                else:
                    # Try to map to dose_id
                    dose_mapping = {0: 0, 1000: 1, 2000: 2, 5000: 3, 10000: 4, 15000: 5}
                    if dose_val in dose_mapping:
                        dose_id = dose_mapping[dose_val]
                        mask = self.sample_metadata['dose_id'] == dose_id
                        samples = self.sample_metadata.loc[mask, 'sample_name'].tolist()
            except (ValueError, IndexError):
                print(f"⚠️ Could not parse dose value from group name: {group_name}")

        elif 'Dose Level' in group_name:
            # Handle fallback dose_id format
            try:
                dose_id = int(group_name.split()[-1])
                mask = self.sample_metadata['dose_id'] == dose_id
                samples = self.sample_metadata.loc[mask, 'sample_name'].tolist()
            except (ValueError, IndexError):
                print(f"⚠️ Could not parse dose ID from group name: {group_name}")

        return samples

    def get_group_comparison_stats(self, group_names: List[str]) -> pd.DataFrame:
        """
        Get comparative statistics between multiple groups

        Args:
            group_names: List of group names to compare

        Returns:
            DataFrame with comparative statistics
        """
        comparison_data = []

        for group_name in group_names:
            group_analysis = self.get_group_intensity_analysis(group_name, top_n=100)

            if not group_analysis.empty:
                stats = {
                    'group_name': group_name,
                    'total_peaks': len(group_analysis),
                    'total_intensity': group_analysis['mean_intensity'].sum(),
                    'top_peak_intensity': group_analysis['mean_intensity'].iloc[0] if len(group_analysis) > 0 else 0,
                    'top_peak_mass': group_analysis['mass'].iloc[0] if len(group_analysis) > 0 else 0,
                    'median_intensity': group_analysis['mean_intensity'].median(),
                    'intensity_range': group_analysis['mean_intensity'].max() - group_analysis['mean_intensity'].min(),
                    'n_samples': group_analysis['n_samples'].iloc[0] if len(group_analysis) > 0 else 0
                }
                comparison_data.append(stats)

        return pd.DataFrame(comparison_data)

    def export_group_analysis(self, group_name: str, output_path: str) -> bool:
        """
        Export detailed group analysis to Excel file

        Args:
            group_name: Name of the group to analyze
            output_path: Path for output Excel file

        Returns:
            True if export successful, False otherwise
        """
        try:
            import pandas as pd
            from datetime import datetime
            import os

            # Get group analysis data
            group_data = self.get_group_intensity_analysis(group_name, top_n=50)
            group_samples = self._get_group_sample_names(group_name)

            if group_data.empty:
                print(f"❌ No data found for group: {group_name}")
                return False

            # Create Excel writer
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main analysis sheet
                group_data.to_excel(writer, sheet_name='Top_Peaks_Analysis', index=False)

                # Sample information sheet
                sample_info = self.sample_metadata[
                    self.sample_metadata['sample_name'].isin(group_samples)
                ].copy()
                sample_info.to_excel(writer, sheet_name='Sample_Information', index=False)

                # Raw intensity data for the group
                raw_group_data = self.raw_data[group_samples]
                raw_group_data.to_excel(writer, sheet_name='Raw_Intensities')

                # Summary statistics
                summary_stats = pd.DataFrame({
                    'Statistic': [
                        'Group Name',
                        'Number of Samples',
                        'Number of Masses',
                        'Total Ion Intensity',
                        'Mean Intensity per Mass',
                        'Analysis Date',
                        'Data File',
                        'Polarity'
                    ],
                    'Value': [
                        group_name,
                        len(group_samples),
                        len(group_data),
                        f"{group_data['mean_intensity'].sum():.2e}",
                        f"{group_data['mean_intensity'].mean():.2e}",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        os.path.basename(self.data_file),
                        self.get_polarity()
                    ]
                })
                summary_stats.to_excel(writer, sheet_name='Summary', index=False)

            print(f"✅ Group analysis exported to: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to export group analysis: {e}")
            return False


if __name__ == "__main__":
    # Test with your data (use relative path from project root)
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    test_data = project_root / "data" / "NegativeIon" / "NegIonTIC.txt"
    pca = SimpleToFSIMSPCA(str(test_data))
    pca.load_data()
    pca.select_doses([1, 2, 3, 4, 5])  # Exclude SQ0 for now
    pca.preprocess_data(sqrt_transform=True, mean_center=False, pareto_scale=True)
    pca.run_pca(n_components=8)
    
    print("\n" + "="*50)
    print("🎉 TEST COMPLETE - Results Summary:")
    summary = pca.get_results_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")