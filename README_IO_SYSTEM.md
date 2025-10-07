# ToF-SIMS Multi-Ion IO System - Quick Reference

## 📦 What You Have

**Unified IO layer** for loading and preprocessing PCA outputs from multiple analysis types.

### Files Created
```
config/tofsims.yaml              Configuration (patterns, schemas, parameters)
tofsims/io.py                    IO layer (loaders, scanners)
tofsims/preprocess.py            Preprocessing (cleaning, merging, validation)
tests/test_io.py                 Smoke tests
scripts/cache_pca.py             Cache generation script
docs/IO_CONTRACT.md              Detailed specification
docs/IMPLEMENTATION_SUMMARY.md   Full implementation report
```

### Cache Files Generated
```
results/cache/
├── scores_merged.parquet           102 rows (15 samples × 12 runs)
├── loadings_merged.parquet       1,176 rows (201 m/z × 12 runs)
├── variance_explained.parquet       72 rows (6 PCs × 12 runs)
└── replicate_validation.csv         12 groups validated
```

---

## 🚀 Usage

### Import Raw Intensities (First Time Setup)
```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims
python scripts/import_matrix_intensities.py
```

**Imports from**:
- `data/NegativeIon/NegAllCompoundSearch.txt`
- `data/PositiveIon/PosAllCompoundSearch.txt`

**Generates**:
- `results/cache/intensities_long.parquet` (3,075 rows)
- `results/cache/intensities_long_head.csv` (preview)

See `docs/README_INTENSITIES.md` for details on SQ/P layout and dose mapping.

### Load Cached Data
```python
import pandas as pd
from tofsims.io import load_intensities_cache

# PCA outputs
scores = pd.read_parquet('results/cache/scores_merged.parquet')
loadings = pd.read_parquet('results/cache/loadings_merged.parquet')
variance = pd.read_parquet('results/cache/variance_explained.parquet')

# Raw intensities
intensities = load_intensities_cache()

# Filter examples
pairwise = scores[scores['analysis_type'] == 'pairwise']
positive = loadings[loadings['polarity'] == 'positive']
assigned = loadings[loadings['assignment'].notna()]
dose_10k = intensities[intensities['dose_label'] == '10000']
```

### Regenerate Cache
```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims
python scripts/cache_pca.py
```

### Run Tests
```bash
python tests/test_io.py
```

---

## 📊 Data Structure

### Scores (102 rows)
| Key Columns | Description |
|-------------|-------------|
| `analysis_id` | e.g., `pairwise_positive_10000` |
| `analysis_type` | `pairwise`, `dose_trajectory`, `dose_dependent` |
| `polarity` | `positive`, `negative` |
| `dose_label` | `2000`, `5000`, `10000`, `15000`, `trajectory`, `dependant` |
| `sample_id` | e.g., `P1_SQ4` |
| `replicate` | `1`, `2`, `3` |
| `PC1..PC8` | Principal component scores |

### Loadings (1,176 rows)
| Key Columns | Description |
|-------------|-------------|
| `analysis_id` | Unique analysis identifier |
| `mz` | Mass-to-charge ratio |
| `loading_PC1..PC8` | Loading values |
| `assignment` | Fragment assignment (25.5% assigned) |
| `confidence` | `High`, `Medium`, `Low` |
| `ppm_error` | Error in ppm |

### Variance (72 rows)
| Key Columns | Description |
|-------------|-------------|
| `analysis_id` | Unique analysis identifier |
| `component` | PC number (1, 2, 3, ...) |
| `variance_ratio` | Fraction of variance (0-1) |
| `cumulative_variance` | Cumulative fraction (0-1) |

---

## 🔧 Configuration

Edit `config/tofsims.yaml` to:
- Add dose mapping: `dose_mapping: {"2000": 2000.0, ...}`
- Configure intensities (when ready): `intensities.file_glob`, `intensities.mapping_csv`
- Set plotting utils (if needed): `plotting_utils.module`, `plotting_utils.savefig`

---

## ✅ Current Status

**Analysis Coverage**:
- ✅ 8 pairwise comparisons (4 doses × 2 polarities)
- ✅ 2 dose trajectory analyses (1 per polarity)
- ✅ 2 dose dependent analyses (1 per polarity)

**Data Quality**:
- ✅ 102 scores (15 samples, 8 PCs)
- ✅ 1,176 loadings (201 m/z, 25.5% assigned)
- ✅ All 12 groups have 3 replicates ✓

**Tests**: ✅ All passing

---

## 📋 TODOs for You

1. **Dose Mapping**: Fill `dose_mapping` in `config/tofsims.yaml`
2. **Intensities**: Provide file patterns and mapping CSV (optional)
3. **Plotting**: Specify plotting utils if migrating to Paper2 (optional)

---

## 📖 Documentation

- **Full Specification**: `docs/IO_CONTRACT.md`
- **Implementation Details**: `docs/IMPLEMENTATION_SUMMARY.md`
- **Config Reference**: `config/tofsims.yaml` (inline comments)

---

## 🎯 Next Steps

1. Use cached parquet files as input for downstream analysis
2. Implement statistical tests (t-tests, ANOVA, regression)
3. Build visualization pipelines using cached data
4. Export results to publication-ready formats

---

**Questions?** See `docs/IMPLEMENTATION_SUMMARY.md` for detailed Q&A.
