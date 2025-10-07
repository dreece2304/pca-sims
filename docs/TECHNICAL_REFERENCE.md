# ToF-SIMS PCA Analysis - Technical Reference

**Quick reference for analysis methods, data processing, and system capabilities.**

---

## Data Loading

### Input Data Formats

**Raw ToF-SIMS Intensities** (matrix format):
- Location: `data/NegativeIon/NegAllCompoundSearch.txt`, `data/PositiveIon/PosAllCompoundSearch.txt`
- Format: Tab-delimited with m/z column + 18 intensity columns (P1-P3 × SQ0-SQ5)
- Import: `python scripts/import_matrix_intensities.py`
- Output: `results/cache/intensities_long.parquet`

**PCA Analysis Outputs** (Excel format):
- Location: `outputs/{analysis_type}/{polarity}/[dose]/pca_analysis.xlsx`
- Sheets: PCA Scores, PCA Loadings, Variance Explained, Top 20 Loadings, Analysis Summary
- Fragment Assignments: `fragment_assignments.csv` (co-located with each analysis)

### Quick Data Loading

```python
import pandas as pd
from tofsims.io import load_intensities_cache

# Load cached PCA outputs
scores = pd.read_parquet('results/cache/scores_merged.parquet')
loadings = pd.read_parquet('results/cache/loadings_merged.parquet')
variance = pd.read_parquet('results/cache/variance_explained.parquet')

# Load raw intensities
intensities = load_intensities_cache()

# Filter examples
pairwise_neg = scores[(scores['analysis_type'] == 'pairwise') & (scores['polarity'] == 'negative')]
dose_10k = intensities[intensities['dose_label'] == '10000']
assigned = loadings[loadings['assignment'].notna()]
```

### Cache Generation

```bash
# Generate unified cache from all PCA outputs
python scripts/cache_pca.py

# Outputs:
# - results/cache/scores_merged.parquet (102 rows)
# - results/cache/loadings_merged.parquet (1,176 rows)
# - results/cache/variance_explained.parquet (72 rows)
# - results/cache/replicate_validation.csv
```

---

## PCA Analysis

### Preprocessing Options

**SIMS-Optimized Pipeline** (all DEFAULT ON):
1. **√(intensity) transform** - Variance stabilization for count data
2. **Mean centering** - Required for PCA covariance analysis
3. **Pareto scaling** - Balances large and small peaks (√(std deviation))

```python
from tofsims.core import ToFSIMSPCA

pca = ToFSIMSPCA('data/NegativeIon/NegIonTIC.txt', 'outputs', False)
pca.load_data()
pca.preprocess_data(sqrt_transform=True, mean_center=True, pareto_scale=True)
pca.run_pca(n_components=5)

# Results
print(f"PC1 variance: {pca.variance_explained[0]:.1f}%")
```

### Sample Selection

**SQ Groups** (dose mapping):
- SQ0 = 0 µC/cm² (as-deposited)
- SQ1 = **EXCLUDED** (fully removed during development)
- SQ2 = 2000 µC/cm²
- SQ3 = 5000 µC/cm²
- SQ4 = 10000 µC/cm²
- SQ5 = 15000 µC/cm²

**Replicates**: P1, P2, P3 (3 replicates per condition)

---

## Fragment Assignment

### Assignment Methods

**1. ppm Tolerance Matching**
- Match observed m/z to database formulas within tolerance (typically 10-50 ppm)
- Default: 10 ppm for high-resolution ToF-SIMS

```python
from tofsims.preprocess import merge_assignments

# Merge loadings with fragment assignments
loadings_assigned = merge_assignments(
    loadings_df,
    assignments_df,
    ppm_tolerance=10.0
)
```

**2. Confidence Scoring**

Multi-criteria scoring system (0-100%):
- **m/z Accuracy** (25%): Mass error in ppm
- **Mass Defect Consistency** (20%): Formula vs observed defect
- **Isotope Pattern Matching** (15%): Expected vs observed isotopes
- **Element Constraints** (15%): Adherence to allowed elements
- **Chemical Plausibility** (10%): Valence rules, atom counts
- **Trend Consistency** (10%): Dose-response patterns
- **Fragment Correlations** (5%): Relationships with known fragments

**Confidence Levels**:
- High: >70%
- Medium: 50-70%
- Low: <50%

**3. Mass Defect Analysis**

Classification based on mass defect patterns:
- **Positive defect** (>+0.01 Da): Organic/H-rich fragments
- **Negative defect** (<-0.01 Da): Metal-containing fragments
- **Near zero** (±0.01 Da): Ambiguous C/N/O combinations

### Element Constraint System

**Material Presets**:
- Alucone: C, H, O, Al
- Tincone: C, H, O, Sn
- General Organic: C, H, O, N
- Custom: User-defined

**Contamination Handling**: Si, Cl, F, Na, K (common contaminants)

### Isotope Pattern Validation

**Automatic Detection**:
- Cl isotopes: ³⁵Cl/³⁷Cl (expected ratio 3:1)
- Si isotopes: ²⁸Si/²⁹Si/³⁰Si
- C isotopes: ¹²C/¹³C (1.1% natural abundance)

**Validation**:
- Mass separation verification (expected Δm/z)
- Intensity ratio comparison (observed vs expected)

---

## Statistical Analysis

### Available Scripts

**Pairwise Comparisons**:
```bash
python scripts/process_all_pairwise_stats.py
# T-tests, effect sizes for each dose pair
```

**Dose Trajectory**:
```bash
python scripts/process_dose_trajectory_stats.py
# Correlation analysis, trend fitting across doses
```

**Fragment Trends**:
```bash
python scripts/visualize_fragment_trends.py
# Dose-response curves for selected fragments
```

**Fragment Statistics**:
```bash
python scripts/analyze_fragment_statistics.py
# Summary statistics, assignment success rates
```

### Replicate Validation

```python
from tofsims.preprocess import validate_replicates

# Check expected replicate counts
validation = validate_replicates(
    scores_df,
    expected_reps=3,
    group_cols=['polarity', 'dose_label']
)
```

---

## Data Export

### Formats Supported

**Excel Workbooks** (multi-sheet):
- PCA Scores
- PCA Loadings
- Variance Explained
- Top 20 Loadings
- Analysis Summary

**CSV Files**:
- Fragment assignments with confidence scores
- Statistical test results
- Summary tables

**Parquet** (cached datasets):
- Fast loading for repeated analysis
- Compressed storage
- Preserves data types

**Plots**:
- PNG (high-resolution, 300 DPI)
- SVG (vector, publication-quality)

### Provenance Tracking

```python
from tofsims.preprocess import save_provenance

# Save analysis metadata
save_provenance(
    analysis_id='pairwise_negative_10000',
    metadata={
        'preprocessing': ['sqrt', 'mean_center', 'pareto_scale'],
        'n_components': 5,
        'ppm_tolerance': 10.0,
        'date': '2025-10-07'
    },
    output_path='results/metadata/'
)
```

---

## Configuration

### Main Configuration File

**Location**: `config/tofsims.yaml`

**Key Sections**:
- Analysis type patterns (pairwise, trajectory, dependent)
- Sheet names for Excel import
- Dose mapping (label → µC/cm²)
- Results directory structure
- Preprocessing parameters
- Fragment assignment settings

### Example Configuration

```yaml
analysis_types:
  pairwise:
    pattern: "outputs/Pairwise/{polarity}/{dose}/pca_analysis.xlsx"

preprocessing:
  ppm_tolerance: 10.0
  expected_replicates: 3

dose_mapping:
  "2000": 2000.0
  "5000": 5000.0
  "10000": 10000.0
  "15000": 15000.0
```

---

## Data Schemas

### Scores Schema

| Column | Type | Description |
|--------|------|-------------|
| `analysis_id` | str | e.g., "pairwise_positive_10000" |
| `analysis_type` | category | pairwise, dose_trajectory, dose_dependent |
| `polarity` | category | positive, negative |
| `dose_label` | category | 2000, 5000, 10000, 15000 |
| `dose_uC_cm2` | float | Dose in µC/cm² |
| `replicate` | category | 1, 2, 3 |
| `sample_id` | str | e.g., "P1_SQ4" |
| `PC1..PC8` | float | Principal component scores |

### Loadings Schema

| Column | Type | Description |
|--------|------|-------------|
| `analysis_id` | str | Unique analysis identifier |
| `mz` | float | Mass-to-charge ratio |
| `loading_PC1..PC8` | float | Loading values |
| `assignment` | str | Fragment assignment (if matched) |
| `confidence` | str | High, Medium, Low |
| `ppm_error` | float | Assignment error in ppm |

### Intensities Schema

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | str | e.g., "negative_P1_SQ4" |
| `dose_label` | str | 2000, 5000, 10000, 15000 |
| `dose_uC_cm2` | float | Dose in µC/cm² |
| `replicate` | int | 1, 2, 3 |
| `polarity` | category | positive, negative |
| `mz` | float | Mass-to-charge ratio |
| `intensity` | float | Measured intensity |

---

## System Architecture

### Package Structure

```
pca-sims/
├── src/                          # Core analysis modules
│   ├── simple_tof_sims_pca.py   # PCA engine
│   ├── matplotlib_plotting.py   # Visualization
│   └── multi_ion_manager.py     # Multi-polarity coordination
├── tofsims/                      # Data IO package
│   ├── io.py                    # Data loaders
│   ├── preprocess.py            # Cleaning, validation
│   ├── stats.py                 # Statistical tests
│   └── figures.py               # Plot generation
├── scripts/                      # Analysis pipelines
│   ├── cache_pca.py
│   ├── import_matrix_intensities.py
│   └── process_*.py
├── data/                         # Input data
├── outputs/                      # PCA results (read-only)
├── results/                      # Generated outputs
│   ├── cache/                   # Parquet files
│   ├── tables/                  # Statistical results
│   └── figures/                 # Plots
└── config/                       # Configuration
    └── tofsims.yaml
```

### Key Modules

**tofsims.io**:
- `load_config()` - Load YAML configuration
- `scan_pca_runs()` - Discover all PCA analyses
- `load_scores()`, `load_loadings()`, `load_explained()` - Load PCA outputs
- `load_intensities_cache()` - Load raw intensity data

**tofsims.preprocess**:
- `clean_meta()` - Normalize metadata
- `merge_assignments()` - Join loadings with assignments
- `validate_replicates()` - Check replicate counts
- `aggregate_*()` - Combine multiple analyses

**tofsims.stats**:
- Statistical test implementations
- Correlation analysis
- Effect size calculations

---

## Performance Notes

### Expected Performance

- **Cache generation**: <5 seconds for 12 analyses
- **PCA computation**: <10 seconds for 921 features × 15 samples
- **Fragment assignment**: <1 second for 1,176 loadings
- **Parquet loading**: <0.5 seconds for full dataset

### Optimization

- Use parquet caching for repeated analysis
- Filter data early in the pipeline
- Use categorical dtypes for metadata columns
- Leverage pandas vectorized operations

---

## Validation Checks

### Data Quality

**Automatic checks performed**:
- ✓ Column count validation (expected format)
- ✓ m/z conversion to float (invalid rows dropped)
- ✓ SQ1 exclusion (known to be removed)
- ✓ NaN/negative intensity removal
- ✓ Replicate count verification (3 per dose)

**Manual verification**:
```python
# Check sample counts
df.groupby(['polarity', 'dose_label', 'replicate']).size()

# Check m/z ranges
df.groupby('polarity')['mz'].agg(['min', 'max', 'count'])

# Check for missing values
df.isnull().sum()
```

---

## Troubleshooting

### Common Issues

**Import errors**: Ensure `conda activate pca-sims` before running
**Missing cache**: Run `python scripts/cache_pca.py` first
**Empty results**: Check file paths in `config/tofsims.yaml`
**Assignment failures**: Verify ppm_tolerance setting (try 10-50 ppm)

### Debug Mode

Set logging level in scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**For detailed data format specifications, see `docs/IO_CONTRACT.md`**
**For intensity import details, see `docs/README_INTENSITIES.md`**
