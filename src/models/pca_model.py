"""
PCA Model - Data structures for PCA state and results.

Pure Python data models with no Qt or UI dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import numpy as np
import pandas as pd
from datetime import datetime


@dataclass
class PCAResults:
    """
    Container for PCA analysis results.

    Attributes:
        scores: PC scores for each sample (samples x components)
        loadings: PC loadings for each variable (variables x components)
        variance_explained: Variance explained by each PC (%)
        cumulative_variance: Cumulative variance explained (%)
        n_components: Number of principal components
        component_labels: Labels for components (PC1, PC2, ...)
        sample_names: Names of samples in order
        feature_names: Names of features/variables in order
        preprocessing: Dictionary of preprocessing parameters used
        timestamp: When the analysis was performed
    """
    scores: np.ndarray
    loadings: np.ndarray
    variance_explained: np.ndarray
    cumulative_variance: np.ndarray
    n_components: int
    component_labels: List[str]
    sample_names: List[str]
    feature_names: List[str]
    preprocessing: Dict[str, any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate data shapes after initialization."""
        # Validate scores shape
        if self.scores.shape[1] != self.n_components:
            raise ValueError(
                f"Scores has {self.scores.shape[1]} components but n_components={self.n_components}"
            )

        # Validate loadings shape
        if self.loadings.shape[1] != self.n_components:
            raise ValueError(
                f"Loadings has {self.loadings.shape[1]} components but n_components={self.n_components}"
            )

        # Validate variance arrays
        if len(self.variance_explained) != self.n_components:
            raise ValueError(
                f"variance_explained has {len(self.variance_explained)} values but n_components={self.n_components}"
            )

    def get_scores_df(self) -> pd.DataFrame:
        """Get scores as a DataFrame with sample names as index."""
        return pd.DataFrame(
            self.scores,
            index=self.sample_names,
            columns=self.component_labels
        )

    def get_loadings_df(self) -> pd.DataFrame:
        """Get loadings as a DataFrame with feature names as index."""
        return pd.DataFrame(
            self.loadings,
            index=self.feature_names,
            columns=self.component_labels
        )

    def get_top_loadings(self, component: int, n: int = 10, absolute: bool = True) -> pd.DataFrame:
        """
        Get top N loadings for a specific component.

        Args:
            component: Component index (0-based)
            n: Number of top loadings to return
            absolute: If True, sort by absolute value

        Returns:
            DataFrame with feature names and loading values
        """
        if component >= self.n_components:
            raise ValueError(f"Component {component} out of range (max: {self.n_components-1})")

        loadings_col = self.loadings[:, component]
        df = pd.DataFrame({
            'feature': self.feature_names,
            'loading': loadings_col,
            'abs_loading': np.abs(loadings_col)
        })

        sort_col = 'abs_loading' if absolute else 'loading'
        return df.nlargest(n, sort_col)[['feature', 'loading']]


@dataclass
class PCAModel:
    """
    Model for PCA analysis state and configuration.

    This class holds the current state of a PCA analysis including
    input data, preprocessing settings, and results.

    Attributes:
        data: Raw input data (samples x features)
        sample_metadata: Metadata for each sample
        feature_metadata: Metadata for each feature
        preprocessing_config: Configuration for preprocessing
        results: PCA results (None until analysis is run)
        is_computed: Whether PCA has been computed
    """
    data: Optional[pd.DataFrame] = None
    sample_metadata: Optional[pd.DataFrame] = None
    feature_metadata: Optional[pd.DataFrame] = None
    preprocessing_config: Dict[str, any] = field(default_factory=lambda: {
        'scaling': 'mean_center',  # 'mean_center', 'standardize', 'pareto', 'none'
        'log_transform': False,
        'remove_outliers': False,
        'outlier_threshold': 3.0
    })
    results: Optional[PCAResults] = None
    is_computed: bool = False

    @property
    def n_samples(self) -> int:
        """Number of samples in the dataset."""
        return len(self.data) if self.data is not None else 0

    @property
    def n_features(self) -> int:
        """Number of features in the dataset."""
        return len(self.data.columns) if self.data is not None else 0

    @property
    def has_data(self) -> bool:
        """Whether data has been loaded."""
        return self.data is not None and not self.data.empty

    def set_data(self, data: pd.DataFrame, sample_metadata: Optional[pd.DataFrame] = None,
                 feature_metadata: Optional[pd.DataFrame] = None):
        """
        Set input data for PCA analysis.

        Args:
            data: Input data matrix (samples x features)
            sample_metadata: Optional metadata for samples
            feature_metadata: Optional metadata for features
        """
        self.data = data.copy()
        self.sample_metadata = sample_metadata.copy() if sample_metadata is not None else None
        self.feature_metadata = feature_metadata.copy() if feature_metadata is not None else None
        self.is_computed = False
        self.results = None

    def update_preprocessing(self, **kwargs):
        """
        Update preprocessing configuration.

        Args:
            **kwargs: Preprocessing parameters to update
        """
        self.preprocessing_config.update(kwargs)
        # Invalidate results if preprocessing changes
        if self.is_computed:
            self.is_computed = False
            self.results = None

    def clear(self):
        """Clear all data and results."""
        self.data = None
        self.sample_metadata = None
        self.feature_metadata = None
        self.results = None
        self.is_computed = False
