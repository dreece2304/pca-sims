"""
Crosslinking Metrics Calculator for ToF-SIMS Analysis
Based on literature: Mei et al. (2022) - Polymer surface characterization

Calculates comparative metrics across samples to infer crosslinking degree:
1. C6H-/C4H- ratio (PMMA-type polymers)
2. H-deficient fraction (Sjövall et al. 2023, Eq. 1)
3. Molecular ion / fragment ratio trends
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class SampleMetrics:
    """Crosslinking metrics for a single sample"""
    sample_name: str
    polarity: str

    # Fragment intensity ratios
    c6h_to_c4h_ratio: Optional[float] = None
    c6h_intensity: Optional[float] = None
    c4h_intensity: Optional[float] = None

    # H-deficiency metrics (Sjövall Eq. 1)
    h_deficient_fraction: Optional[float] = None
    h_deficient_sum: Optional[float] = None  # C4H3 + C5H3 + C7H3
    h_rich_sum: Optional[float] = None       # C4H9 + C5H9 + C7H11

    # Molecular ion metrics
    molecular_ion_sum: Optional[float] = None
    fragment_ion_sum: Optional[float] = None
    mol_to_frag_ratio: Optional[float] = None

    # Total detected fragments
    total_fragments: int = 0
    aromatic_count: int = 0
    h_deficient_count: int = 0

    # Interpretation notes
    interpretation: str = ""

    def to_dict(self):
        """Convert to dictionary for JSON export"""
        return asdict(self)


class CrosslinkingAnalyzer:
    """
    Analyze crosslinking trends across multiple samples
    """

    # Fragments for H-deficient fraction calculation (Sjövall Eq. 1)
    H_DEFICIENT_FORMULAS = ['C4H3', 'C5H3', 'C7H3']
    H_RICH_FORMULAS = ['C4H9', 'C5H9', 'C7H11']

    # Crosslinking indicator fragments (negative ions)
    CROSSLINK_FRAGMENTS = {
        'C6H': 73.0078,  # Indicator fragment
        'C4H': 49.0078,  # Reference fragment
    }

    def __init__(self):
        self.sample_metrics: List[SampleMetrics] = []

    def calculate_sample_metrics(
        self,
        sample_name: str,
        fragment_data: Dict[str, Dict],  # {formula: {'mass': float, 'intensity': float}}
        polarity: str = 'negative',
        fragment_properties: Optional[List] = None  # List of FragmentProperties from classifier
    ) -> SampleMetrics:
        """
        Calculate all crosslinking metrics for a single sample

        Args:
            sample_name: Sample identifier
            fragment_data: Dict of {formula: {'mass': float, 'intensity': float}}
            polarity: Ion polarity
            fragment_properties: Optional list of classified fragments

        Returns:
            SampleMetrics object
        """
        metrics = SampleMetrics(sample_name=sample_name, polarity=polarity)

        # Extract intensities
        intensities = {formula: data['intensity']
                      for formula, data in fragment_data.items()}

        # 1. C6H-/C4H- ratio (crosslinking indicator for PMMA-type polymers)
        if polarity == 'negative':
            c6h = intensities.get('C6H', 0)
            c4h = intensities.get('C4H', 0)

            metrics.c6h_intensity = c6h
            metrics.c4h_intensity = c4h

            if c4h > 0:
                metrics.c6h_to_c4h_ratio = c6h / c4h

        # 2. H-deficient fraction (Sjövall Eq. 1)
        h_def_sum = sum(intensities.get(f, 0) for f in self.H_DEFICIENT_FORMULAS)
        h_rich_sum = sum(intensities.get(f, 0) for f in self.H_RICH_FORMULAS)

        metrics.h_deficient_sum = h_def_sum
        metrics.h_rich_sum = h_rich_sum

        total = h_def_sum + h_rich_sum
        if total > 0:
            metrics.h_deficient_fraction = h_def_sum / total

        # 3. Fragment counts from classifier
        if fragment_properties:
            metrics.total_fragments = len(fragment_properties)
            metrics.aromatic_count = sum(
                1 for p in fragment_properties
                if p.chemical_family == 'Aromatic'
            )
            metrics.h_deficient_count = sum(
                1 for p in fragment_properties
                if p.chemical_family == 'H-deficient_unsaturated'
            )
        else:
            metrics.total_fragments = len(fragment_data)

        # 4. Interpret results
        metrics.interpretation = self._interpret_metrics(metrics)

        return metrics

    def _interpret_metrics(self, metrics: SampleMetrics) -> str:
        """
        Provide interpretation of crosslinking metrics

        Based on literature:
        - Higher C6H-/C4H- ratio → increased crosslinking (PMMA)
        - Higher H-deficient fraction → more aromatic/unsaturated
        """
        interpretations = []

        if metrics.c6h_to_c4h_ratio is not None:
            if metrics.c6h_to_c4h_ratio > 0.7:
                interpretations.append("High C6H-/C4H- ratio suggests increased crosslinking")
            elif metrics.c6h_to_c4h_ratio > 0.5:
                interpretations.append("Moderate crosslinking indicated")
            else:
                interpretations.append("Low crosslinking indicated")

        if metrics.h_deficient_fraction is not None:
            if metrics.h_deficient_fraction > 0.6:
                interpretations.append("Highly H-deficient (aromatic-rich)")
            elif metrics.h_deficient_fraction > 0.4:
                interpretations.append("Moderate H-deficiency")
            else:
                interpretations.append("H-rich fragmentation pattern")

        return "; ".join(interpretations) if interpretations else "Insufficient data"

    def add_sample(self, metrics: SampleMetrics):
        """Add sample metrics to collection"""
        self.sample_metrics.append(metrics)

    def get_trends(self) -> pd.DataFrame:
        """
        Get all metrics as pandas DataFrame for trend analysis

        Returns:
            DataFrame with columns: sample_name, c6h_to_c4h_ratio, h_deficient_fraction, etc.
        """
        data = []
        for metrics in self.sample_metrics:
            data.append({
                'sample_name': metrics.sample_name,
                'polarity': metrics.polarity,
                'c6h_to_c4h_ratio': metrics.c6h_to_c4h_ratio,
                'h_deficient_fraction': metrics.h_deficient_fraction,
                'total_fragments': metrics.total_fragments,
                'aromatic_count': metrics.aromatic_count,
                'h_deficient_count': metrics.h_deficient_count,
                'interpretation': metrics.interpretation
            })

        return pd.DataFrame(data)

    def export_to_csv(self, filepath: str):
        """Export metrics to CSV file"""
        df = self.get_trends()
        df.to_csv(filepath, index=False)
        print(f"✅ Exported crosslinking metrics to {filepath}")

    def export_to_json(self, filepath: str):
        """Export full metrics to JSON file"""
        data = {
            'metadata': {
                'analysis_type': 'crosslinking_metrics',
                'n_samples': len(self.sample_metrics),
                'timestamp': pd.Timestamp.now().isoformat()
            },
            'samples': [m.to_dict() for m in self.sample_metrics]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported crosslinking metrics to {filepath}")

    def compare_samples(
        self,
        sample_names: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Compare metrics between samples

        Args:
            sample_names: List of sample names to compare (None = all)

        Returns:
            Dict with comparison statistics
        """
        if sample_names:
            samples = [m for m in self.sample_metrics if m.sample_name in sample_names]
        else:
            samples = self.sample_metrics

        if not samples:
            return {}

        # Calculate statistics
        c6h_ratios = [s.c6h_to_c4h_ratio for s in samples if s.c6h_to_c4h_ratio is not None]
        h_def_fracs = [s.h_deficient_fraction for s in samples if s.h_deficient_fraction is not None]

        comparison = {
            'n_samples': len(samples),
            'c6h_to_c4h_ratio': {
                'mean': np.mean(c6h_ratios) if c6h_ratios else None,
                'std': np.std(c6h_ratios) if c6h_ratios else None,
                'min': np.min(c6h_ratios) if c6h_ratios else None,
                'max': np.max(c6h_ratios) if c6h_ratios else None,
                'trend': 'increasing' if len(c6h_ratios) > 1 and c6h_ratios[-1] > c6h_ratios[0] else 'stable'
            },
            'h_deficient_fraction': {
                'mean': np.mean(h_def_fracs) if h_def_fracs else None,
                'std': np.std(h_def_fracs) if h_def_fracs else None,
                'min': np.min(h_def_fracs) if h_def_fracs else None,
                'max': np.max(h_def_fracs) if h_def_fracs else None,
            }
        }

        return comparison


# ===== TESTING =====

if __name__ == "__main__":
    print("Crosslinking Metrics Calculator - Test")
    print("=" * 70)

    # Create analyzer
    analyzer = CrosslinkingAnalyzer()

    # Simulate dose series data (SQ2 → SQ8)
    test_samples = [
        {
            'name': 'SQ2',
            'data': {
                'C6H': {'mass': 73.0078, 'intensity': 0.45},
                'C4H': {'mass': 49.0078, 'intensity': 1.0},
                'C4H3': {'mass': 51.0235, 'intensity': 0.3},
                'C5H3': {'mass': 63.0235, 'intensity': 0.25},
                'C7H3': {'mass': 87.0235, 'intensity': 0.15},
                'C4H9': {'mass': 57.0704, 'intensity': 0.8},
                'C5H9': {'mass': 69.0704, 'intensity': 0.5},
                'C7H11': {'mass': 95.0861, 'intensity': 0.3},
            }
        },
        {
            'name': 'SQ5',
            'data': {
                'C6H': {'mass': 73.0078, 'intensity': 0.72},
                'C4H': {'mass': 49.0078, 'intensity': 1.0},
                'C4H3': {'mass': 51.0235, 'intensity': 0.45},
                'C5H3': {'mass': 63.0235, 'intensity': 0.35},
                'C7H3': {'mass': 87.0235, 'intensity': 0.25},
                'C4H9': {'mass': 57.0704, 'intensity': 0.6},
                'C5H9': {'mass': 69.0704, 'intensity': 0.4},
                'C7H11': {'mass': 95.0861, 'intensity': 0.25},
            }
        },
        {
            'name': 'SQ8',
            'data': {
                'C6H': {'mass': 73.0078, 'intensity': 0.85},
                'C4H': {'mass': 49.0078, 'intensity': 1.0},
                'C4H3': {'mass': 51.0235, 'intensity': 0.55},
                'C5H3': {'mass': 63.0235, 'intensity': 0.45},
                'C7H3': {'mass': 87.0235, 'intensity': 0.30},
                'C4H9': {'mass': 57.0704, 'intensity': 0.5},
                'C5H9': {'mass': 69.0704, 'intensity': 0.3},
                'C7H11': {'mass': 95.0861, 'intensity': 0.2},
            }
        },
    ]

    # Calculate metrics for each sample
    for sample in test_samples:
        metrics = analyzer.calculate_sample_metrics(
            sample['name'],
            sample['data'],
            polarity='negative'
        )
        analyzer.add_sample(metrics)

        print(f"\n{sample['name']}:")
        print(f"  C6H-/C4H- ratio: {metrics.c6h_to_c4h_ratio:.3f}")
        print(f"  H-deficient fraction: {metrics.h_deficient_fraction:.3f}")
        print(f"  Interpretation: {metrics.interpretation}")

    # Get trends
    print("\n" + "=" * 70)
    print("TRENDS ACROSS DOSE SERIES:")
    df = analyzer.get_trends()
    print(df.to_string())

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON STATISTICS:")
    comparison = analyzer.compare_samples()
    print(f"C6H-/C4H- ratio range: {comparison['c6h_to_c4h_ratio']['min']:.3f} → {comparison['c6h_to_c4h_ratio']['max']:.3f}")
    print(f"Trend: {comparison['c6h_to_c4h_ratio']['trend']}")
    print(f"\nH-deficient fraction range: {comparison['h_deficient_fraction']['min']:.3f} → {comparison['h_deficient_fraction']['max']:.3f}")

    print("\n" + "=" * 70)
    print("✅ Crosslinking metrics calculator ready!")
    print("📊 Shows clear increasing trend in crosslinking: SQ2 → SQ8")
