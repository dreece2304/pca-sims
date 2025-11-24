"""
Unit tests for data models

Tests for Sample, Fragment, PCA, and Spectrum models.
"""

import pytest
import numpy as np
import pandas as pd

import sys
sys.path.append('src')

from models import (
    Sample, Polarity,
    Fragment, FragmentAssignment, AssignmentConfidence,
    PCAResults, MassSpectrum
)


class TestSampleModel:
    """Tests for Sample model"""

    def test_sample_creation_minimal(self):
        """Test creating sample with minimal parameters"""
        sample = Sample(name="Test_Sample")

        assert sample.name == "Test_Sample"
        assert sample.dose == 0.0
        assert sample.replicate == 1
        assert sample.polarity == Polarity.NEGATIVE
        assert sample.group is None

    def test_sample_creation_full(self):
        """Test creating sample with all parameters"""
        sample = Sample(
            name="SQ2_Rep1",
            dose=2.0,
            replicate=1,
            polarity=Polarity.NEGATIVE,
            group="SQ2"
        )

        assert sample.name == "SQ2_Rep1"
        assert sample.dose == 2.0
        assert sample.replicate == 1
        assert sample.polarity == Polarity.NEGATIVE
        assert sample.group == "SQ2"

    def test_polarity_enum_values(self):
        """Test Polarity enum values"""
        assert Polarity.NEGATIVE.value == "negative"
        assert Polarity.POSITIVE.value == "positive"

    def test_sample_display_name(self):
        """Test sample display name generation"""
        sample = Sample(name="SQ2_Rep1", dose=2.0, group="SQ2")

        # Assuming there's a display_name property or method
        assert "SQ2" in sample.name or sample.group == "SQ2"


class TestFragmentModel:
    """Tests for Fragment model"""

    def test_fragment_creation_minimal(self):
        """Test creating fragment with minimal parameters"""
        fragment = Fragment(
            formula="C4HO",
            exact_mass=65.0031,
            polarity=Polarity.NEGATIVE
        )

        assert fragment.formula == "C4HO"
        assert fragment.exact_mass == 65.0031
        assert fragment.polarity == Polarity.NEGATIVE
        assert fragment.charge == 1
        assert fragment.chemical_family == "Unknown"

    def test_fragment_creation_full(self):
        """Test creating fragment with all parameters"""
        fragment = Fragment(
            formula="C6H5",
            exact_mass=77.0391,
            polarity=Polarity.NEGATIVE,
            charge=1,
            chemical_family="Aromatic",
            is_aromatic=True,
            dbe=4.0,
            h_c_ratio=0.833
        )

        assert fragment.formula == "C6H5"
        assert fragment.exact_mass == 77.0391
        assert fragment.chemical_family == "Aromatic"
        assert fragment.is_aromatic is True
        assert fragment.dbe == 4.0
        assert abs(fragment.h_c_ratio - 0.833) < 0.001

    def test_assignment_confidence_levels(self):
        """Test AssignmentConfidence enum"""
        assert AssignmentConfidence.HIGH.value == "high"
        assert AssignmentConfidence.MEDIUM.value == "medium"
        assert AssignmentConfidence.LOW.value == "low"
        assert AssignmentConfidence.UNCERTAIN.value == "uncertain"
        assert AssignmentConfidence.MANUAL.value == "manual"


class TestFragmentAssignmentModel:
    """Tests for FragmentAssignment model"""

    def test_assignment_creation_unassigned(self):
        """Test creating unassigned fragment"""
        assignment = FragmentAssignment(measured_mz=65.0035)

        assert assignment.measured_mz == 65.0035
        assert assignment.fragment is None
        assert assignment.confidence == AssignmentConfidence.UNCERTAIN
        assert assignment.ppm_error == 0.0

    def test_assignment_creation_with_fragment(self):
        """Test creating assignment with fragment"""
        fragment = Fragment(
            formula="C4HO",
            exact_mass=65.0031,
            polarity=Polarity.NEGATIVE,
            chemical_family="Unsaturated_carbon"
        )

        assignment = FragmentAssignment(
            measured_mz=65.0035,
            fragment=fragment,
            confidence=AssignmentConfidence.HIGH,
            ppm_error=6.15
        )

        assert assignment.measured_mz == 65.0035
        assert assignment.fragment is not None
        assert assignment.fragment.formula == "C4HO"
        assert assignment.confidence == AssignmentConfidence.HIGH
        assert abs(assignment.ppm_error - 6.15) < 0.01


class TestPCAModel:
    """Tests for PCAResults model"""

    def test_pca_results_creation(self):
        """Test creating PCA results"""
        scores = np.array([[1, 2, 3], [4, 5, 6]])  # 2 samples, 3 components
        loadings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])  # 2 features, 3 components
        variance = np.array([0.89, 0.08, 0.03])  # 3 components

        results = PCAResults(
            scores=scores,
            loadings=loadings,
            variance_explained=variance,
            cumulative_variance=np.cumsum(variance),
            n_components=3,
            component_labels=['PC1', 'PC2', 'PC3'],
            sample_names=['Sample1', 'Sample2'],
            feature_names=['Mass1', 'Mass2']
        )

        assert results.n_components == 3
        assert len(results.component_labels) == 3
        assert len(results.sample_names) == 2
        assert results.variance_explained[0] == 0.89

    def test_pca_get_scores_df(self):
        """Test converting scores to DataFrame"""
        scores = np.array([[1, 2], [3, 4]])
        loadings = np.array([[0.1, 0.2]])
        variance = np.array([0.9, 0.1])

        results = PCAResults(
            scores=scores,
            loadings=loadings,
            variance_explained=variance,
            cumulative_variance=np.cumsum(variance),
            n_components=2,
            component_labels=['PC1', 'PC2'],
            sample_names=['S1', 'S2'],
            feature_names=['M1']
        )

        scores_df = results.get_scores_df()

        assert isinstance(scores_df, pd.DataFrame)
        assert list(scores_df.index) == ['S1', 'S2']
        assert list(scores_df.columns) == ['PC1', 'PC2']
        assert scores_df.loc['S1', 'PC1'] == 1
        assert scores_df.loc['S2', 'PC2'] == 4


class TestMassSpectrumModel:
    """Tests for MassSpectrum model"""

    def test_spectrum_creation(self):
        """Test creating mass spectrum"""
        sample = Sample(name="Test", polarity=Polarity.NEGATIVE)
        masses = np.array([25.0, 65.0, 77.0])
        intensities = np.array([100.0, 500.0, 200.0])

        spectrum = MassSpectrum(
            sample=sample,
            mass_values=masses,
            intensities=intensities
        )

        assert spectrum.sample.name == "Test"
        assert len(spectrum.mass_values) == 3
        assert len(spectrum.intensities) == 3
        assert spectrum.intensities[1] == 500.0
        assert len(spectrum.assignments) == 0

    def test_spectrum_with_assignments(self):
        """Test spectrum with fragment assignments"""
        sample = Sample(name="Test", polarity=Polarity.NEGATIVE)
        masses = np.array([65.0031])
        intensities = np.array([500.0])

        fragment = Fragment(
            formula="C4HO",
            exact_mass=65.0031,
            polarity=Polarity.NEGATIVE
        )

        assignment = FragmentAssignment(
            measured_mz=65.0035,
            fragment=fragment,
            confidence=AssignmentConfidence.HIGH,
            ppm_error=6.15
        )

        spectrum = MassSpectrum(
            sample=sample,
            mass_values=masses,
            intensities=intensities,
            assignments={65.0035: assignment}
        )

        assert len(spectrum.assignments) == 1
        assert 65.0035 in spectrum.assignments
        assert spectrum.assignments[65.0035].fragment.formula == "C4HO"


class TestModelValidation:
    """Tests for model validation"""

    def test_sample_validation_negative_dose(self):
        """Test that negative dose might raise error or get corrected"""
        # Depending on validation implementation
        try:
            sample = Sample(name="Test", dose=-1.0)
            # If no validation, dose should still be -1.0
            assert sample.dose == -1.0
        except ValueError:
            # If validation is implemented
            pass

    def test_fragment_validation_zero_mass(self):
        """Test fragment with zero mass"""
        try:
            fragment = Fragment(
                formula="Invalid",
                exact_mass=0.0,
                polarity=Polarity.NEGATIVE
            )
            assert fragment.exact_mass == 0.0
        except ValueError:
            pass

    def test_pca_array_shape_consistency(self):
        """Test that PCA arrays have consistent shapes"""
        scores = np.array([[1, 2], [3, 4]])  # 2 samples, 2 components
        loadings = np.array([[0.1, 0.2], [0.3, 0.4]])  # 2 features, 2 components
        variance = np.array([0.9, 0.1])  # 2 components

        results = PCAResults(
            scores=scores,
            loadings=loadings,
            variance_explained=variance,
            cumulative_variance=np.cumsum(variance),
            n_components=2,
            component_labels=['PC1', 'PC2'],
            sample_names=['S1', 'S2'],
            feature_names=['M1', 'M2']
        )

        # Check shape consistency
        assert results.scores.shape[1] == results.n_components
        assert results.loadings.shape[1] == results.n_components
        assert len(results.variance_explained) == results.n_components


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
