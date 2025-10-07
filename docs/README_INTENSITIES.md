# ToF-SIMS Intensities Import - Matrix Format

## Overview

Imports raw ToF-SIMS intensity matrices from tab-delimited text files with fixed column layout.

## File Locations

**Negative ions**: `data/NegativeIon/NegAllCompoundSearch.txt`
**Positive ions**: `data/PositiveIon/PosAllCompoundSearch.txt`

## File Format

**Structure**: Tab-delimited text with header row

**Columns**:
1. `Mass (u)` - m/z values
2-19. Intensity columns in fixed order:
   - P1_SQ1, P1_SQ2, P1_SQ3, P1_SQ4, P1_SQ5
   - P2_SQ1, P2_SQ2, P2_SQ3, P2_SQ4, P2_SQ5
   - P3_SQ1, P3_SQ2, P3_SQ3, P3_SQ4, P3_SQ5
   - P1_SQ0, P2_SQ0, P3_SQ0

**Layout**: P{replicate}_SQ{dose}
- P1/P2/P3 = replicates 1, 2, 3
- SQ groups appear in order: SQ1, SQ2, SQ3, SQ4, SQ5, SQ0

## SQ Group → Dose Mapping

| SQ Group | Status | Dose Label | Dose (µC/cm²) | Description |
|----------|--------|------------|---------------|-------------|
| SQ0 | ✓ Keep | "0" | 0.0 | As-deposited |
| **SQ1** | ✗ **EXCLUDE** | - | - | **Dropped entirely** |
| SQ2 | ✓ Keep | "2000" | 2000.0 | Low dose |
| SQ3 | ✓ Keep | "5000" | 5000.0 | Medium-low dose |
| SQ4 | ✓ Keep | "10000" | 10000.0 | Medium-high dose |
| SQ5 | ✓ Keep | "15000" | 15000.0 | High dose |

**Important**: SQ1 is excluded from all analyses.

## Replicate Numbering

P{n} in column names maps to `replicate` field:
- P1 → replicate = 1
- P2 → replicate = 2
- P3 → replicate = 3

## Polarity Assignment

Inferred from directory name:
- `NegativeIon/` → `polarity = 'negative'`
- `PositiveIon/` → `polarity = 'positive'`

## Sample ID Format

Generated as: `{polarity}_{replicate_code}_{sq_group}`

**Examples**:
- `negative_P1_SQ4` - Negative ion, replicate 1, 10000 µC/cm²
- `positive_P3_SQ0` - Positive ion, replicate 3, as-deposited
- `negative_P2_SQ5` - Negative ion, replicate 2, 15000 µC/cm²

## Output Schema

**Long-format table** with columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `sample_id` | str | Unique sample identifier | `negative_P1_SQ4` |
| `dose_label` | str | Dose label (string) | `"10000"` |
| `dose_uC_cm2` | float | Dose in µC/cm² | `10000.0` |
| `replicate` | int | Replicate number | `1` |
| `polarity` | category | Ion polarity | `negative` |
| `mz` | float | Mass-to-charge ratio | `77.0383` |
| `intensity` | float | Measured intensity | `0.568087` |

## Import Process

### Step 1: Run Import Script

```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims
python scripts/import_matrix_intensities.py
```

### Step 2: Outputs Generated

**Parquet cache** (fast loading):
```
results/cache/intensities_long.parquet
```

**CSV preview** (QA check, first 200 rows):
```
results/cache/intensities_long_head.csv
```

### Step 3: Expected Summary

```
NEGATIVE:
  SQ groups: SQ0, SQ2, SQ3, SQ4, SQ5 (SQ1 excluded)
  Doses: 0, 2000, 5000, 10000, 15000 µC/cm²
  Samples: 15 (3 replicates each)
  m/z features: ~94
  Replicate validation: ✓ 15 samples (3 per dose)

POSITIVE:
  SQ groups: SQ0, SQ2, SQ3, SQ4, SQ5 (SQ1 excluded)
  Doses: 0, 2000, 5000, 10000, 15000 µC/cm²
  Samples: 15 (3 replicates each)
  m/z features: ~111
  Replicate validation: ✓ 15 samples (3 per dose)

COMBINED:
  Total samples: 30
  Total m/z: ~205
  Shape: ~3,075 rows × 7 columns
```

## Loading Cached Intensities

### Python API

```python
from tofsims.io import load_intensities_cache

# Load all intensities
df = load_intensities_cache()

# Filter by polarity
neg = df[df['polarity'] == 'negative']
pos = df[df['polarity'] == 'positive']

# Filter by dose
dose_10k = df[df['dose_label'] == '10000']

# Get specific m/z range
mz_range = df[(df['mz'] >= 50) & (df['mz'] <= 100)]

# Exclude as-deposited
treated = df[df['dose_label'] != '0']
```

### Example: Compute Mean Intensity per m/z and Dose

```python
import pandas as pd
from tofsims.io import load_intensities_cache

df = load_intensities_cache()

# Mean intensity per (polarity, dose, m/z)
means = (
    df
    .groupby(['polarity', 'dose_label', 'mz'])
    ['intensity']
    .mean()
    .reset_index()
)

print(means.head(10))
```

## Data Validation

### Automatic Checks

The import script performs:
1. ✓ Column count validation (19 expected)
2. ✓ m/z conversion to float (invalid rows dropped)
3. ✓ SQ1 exclusion (3 columns per polarity)
4. ✓ NaN/negative intensity removal
5. ✓ Replicate count verification (3 per dose)

### QA Checks After Import

**Check preview CSV**:
```bash
head -20 results/cache/intensities_long_head.csv
```

**Verify sample counts**:
```python
from tofsims.io import load_intensities_cache

df = load_intensities_cache()

# Should have 15 samples per polarity (5 doses × 3 replicates)
print(df.groupby(['polarity', 'dose_label', 'replicate']).size())
```

**Check m/z ranges**:
```python
print(df.groupby('polarity')['mz'].agg(['min', 'max', 'count']))
```

## Integration with PCA Outputs

### Matching Sample IDs

**Note**: Sample IDs from intensities may not directly match PCA sample names.

**PCA sample names** (from scores): `P1_SQ4`, `P2_SQ0`, etc.
**Intensities sample_id**: `negative_P1_SQ4`, `positive_P2_SQ0`, etc.

To merge:
1. Extract SQ group and replicate from PCA `sample_name`
2. Combine with `polarity` from analysis metadata
3. Build lookup key: `{polarity}_{sample_name}`

### Example: Link PCA Scores to Intensities

```python
import pandas as pd
from tofsims.io import load_intensities_cache

# Load PCA scores
scores = pd.read_parquet('results/cache/scores_merged.parquet')

# Load intensities
intensities = load_intensities_cache()

# Create matching key in scores
scores['intensity_key'] = scores['polarity'] + '_' + scores['sample_id']

# Create matching key in intensities
# (already has correct format: negative_P1_SQ4, etc.)

# Example: Get intensities for samples in a specific PCA analysis
pairwise_10k = scores[scores['analysis_id'] == 'pairwise_positive_10000']
sample_keys = pairwise_10k['intensity_key'].unique()

# Filter intensities
analysis_intensities = intensities[intensities['sample_id'].isin(sample_keys)]
```

## Troubleshooting

### Missing File Warning

```
WARNING: File not found: data/NegativeIon/NegAllCompoundSearch.txt
```

**Solution**: Check file path. Script will continue with available polarity.

### Column Count Error

```
ValueError: Expected 19 columns (1 m/z + 18 intensities), got 20
```

**Solution**: File format mismatch. Verify tab-delimited with header row.

### Empty Cache

```python
df = load_intensities_cache()
# Returns empty DataFrame
```

**Solution**: Run import script first:
```bash
python scripts/import_matrix_intensities.py
```

## File Locations Reference

**Source data**:
- `data/NegativeIon/NegAllCompoundSearch.txt`
- `data/PositiveIon/PosAllCompoundSearch.txt`

**Generated cache**:
- `results/cache/intensities_long.parquet` (primary)
- `results/cache/intensities_long_head.csv` (QA preview)

**Import script**:
- `scripts/import_matrix_intensities.py`

**Loader function**:
- `tofsims/io.py::load_intensities_cache()`

## Summary

✅ **Fixed layout import** - Handles P{rep}_SQ{dose} column format
✅ **SQ1 exclusion** - Automatically drops excluded group
✅ **Long-format output** - Ready for statistical analysis
✅ **Cached parquet** - Fast repeated loading
✅ **Schema validation** - Ensures correct structure
✅ **Replicate tracking** - 3 replicates per dose validated
