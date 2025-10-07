# ToF-SIMS Analysis IO Contract

## File Structure Inventory

### Directory Layout
```
outputs/
├── Pairwise/
│   ├── Positive/
│   │   ├── 2000/    [pca_analysis.xlsx, fragment_assignments.csv]
│   │   ├── 5000/    [pca_analysis.xlsx, fragment_assignments.csv]
│   │   ├── 10000/   [pca_analysis.xlsx, fragment_assignments.csv]
│   │   └── 15000/   [pca_analysis.xlsx, fragment_assignments.csv]
│   └── Negative/
│       ├── 2000/    [pca_analysis.xlsx, fragment_assignments.csv]
│       ├── 5000/    [pca_analysis.xlsx, fragment_assignments.csv]
│       ├── 10000/   [pca_analysis.xlsx, fragment_assignments.csv]
│       └── 15000/   [pca_analysis.xlsx, fragment_assignments.csv]
├── Dose-Trajectory/
│   ├── Positive/    [pca_analysis.xlsx, fragment_assignments.csv]
│   └── Negative/    [pca_analysis.xlsx, fragment_assignments.csv]
└── Dose-Dependant/
    ├── Positive/    [pca_analysis.xlsx, fragment_assignments.csv]
    └── Negative/    [pca_analysis.xlsx, fragment_assignments.csv]
```

**Total Files**: 12 pca_analysis.xlsx + 12 fragment_assignments.csv = 24 files

### Glob Patterns
- **Pairwise**: `outputs/Pairwise/{Positive,Negative}/*/pca_analysis.xlsx`
- **Dose-Trajectory**: `outputs/Dose-Trajectory/{Positive,Negative}/pca_analysis.xlsx`
- **Dose-Dependant**: `outputs/Dose-Dependant/{Positive,Negative}/pca_analysis.xlsx`
- **Assignments**: `outputs/**/fragment_assignments.csv` (co-located with each PCA analysis)

---

## Excel File Structure

### `pca_analysis.xlsx` Sheets
All PCA files contain identical sheet structure:

1. **Analysis Summary** - Metadata and parameters
2. **PCA Scores** - Sample coordinates in PC space
3. **PCA Loadings** - Variable (m/z) contributions
4. **Variance Explained** - PC variance statistics
5. **Top 20 Loadings** - Ranked important features (PC1)

---

## Data Schemas

### 1. PCA Scores Sheet
**File**: `pca_analysis.xlsx`, Sheet: `PCA Scores`
**One row per sample**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `sample_name` | str | Original sample identifier | `P1_SQ4` |
| `pattern` | int | Pattern/treatment group | `1` |
| `dose` | int | Dose level identifier | `4` |
| `replicate_id` | int | Replicate number | `1` |
| `dose_id` | int | Dose identifier | `4` |
| `sample_type` | str | Sample category | `experimental` |
| `actual_dose` | float | Actual dose value | `10000.0` |
| `dose_units` | str | Dose units | `µC/cm²` |
| `include` | bool | Inclusion flag | `True` |
| `notes` | str | Sample notes | `""` |
| `display_name` | str | Display label | `P1 10k (1)` |
| `PC1` | float | Principal Component 1 score | `0.123456` |
| `PC2` | float | Principal Component 2 score | `-0.045678` |
| `PC3` | float | Principal Component 3 score | `0.003968` |
| `PC4` | float | Principal Component 4 score | `0.002920` |
| `PC5` | float | Principal Component 5 score | `0.000193` |

**Required Columns for Analysis**:
- Identifiers: `sample_name`, `dose`, `replicate_id`
- Metadata: `polarity` (from path), `analysis_type` (from path)
- PCA: `PC1`, `PC2`, `PC3` (minimum), `PC4`, `PC5` (optional)

---

### 2. PCA Loadings Sheet
**File**: `pca_analysis.xlsx`, Sheet: `PCA Loadings`
**One row per m/z feature**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `index` | float | m/z value | `77.0383` |
| `PC1` | float | PC1 loading | `0.56856` |
| `PC2` | float | PC2 loading | `0.108713` |
| `PC3` | float | PC3 loading | `-0.056432` |
| `PC4` | float | PC4 loading | `-0.002791` |
| `PC5` | float | PC5 loading | `-0.167501` |
| `PC1_Abs_Loading` | float | Absolute PC1 loading | `0.56856` |
| `PC1_Rank` | int | Rank by PC1 importance | `1` |

**Required Columns**:
- Feature: `index` (m/z value)
- Loadings: `PC1`, `PC2`, `PC3` (minimum)
- Metadata: `PC1_Abs_Loading`, `PC1_Rank` (optional but useful)

---

### 3. Variance Explained Sheet
**File**: `pca_analysis.xlsx`, Sheet: `Variance Explained`
**One row per principal component**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `Component` | str | PC identifier | `PC1` |
| `Variance_Explained_Percent` | float | Individual variance % | `99.774431` |
| `Cumulative_Variance_Percent` | float | Cumulative variance % | `99.774431` |

**Required Columns**: All three

---

### 4. Fragment Assignments CSV
**File**: `fragment_assignments.csv` (co-located with each PCA file)
**One row per assigned fragment (top N loadings)**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `m/z` | float | Mass-to-charge ratio | `77.0383` |
| `PC1 Loading` | float | PC1 loading value | `+0.568087` |
| `Current Assignment` | str | Fragment assignment | `C_6H_5+ (C6H5)` |
| `Confidence` | str | Assignment confidence | `High` |
| `Action` | str | Curation action needed | `""` |
| `Notes` | str | Additional notes | `"Unknown, 0ppm"` |

**Required Columns**:
- `m/z`, `PC1 Loading`, `Current Assignment`, `Confidence`

**Note**: These are **already assigned** and should be used as-is. No re-assignment needed.

---

## Metadata Extraction from Paths

Since metadata is embedded in directory structure, extract:

```python
# Example path: outputs/Pairwise/Positive/10000/pca_analysis.xlsx
path_parts = path.split('/')

analysis_type = path_parts[1]      # "Pairwise"
polarity = path_parts[2].lower()   # "positive" → "positive"
dose_label = path_parts[3]         # "10000" (for pairwise only)
```

**Analysis Types**:
- `Pairwise` - specific dose comparisons (has dose subfolder)
- `Dose-Trajectory` - dose progression analysis
- `Dose-Dependant` - dose-dependent analysis

**Polarities**: `positive`, `negative`

---

## Unified Data Model

### Combined Scores DataFrame
After loading all files:

| Column | Type | Source |
|--------|------|--------|
| `analysis_id` | str | Generated: `{analysis_type}_{polarity}_{dose_label}` |
| `analysis_type` | str | From path (`Pairwise`, `Dose-Trajectory`, `Dose-Dependant`) |
| `polarity` | category | From path (`positive`, `negative`) |
| `dose_label` | str | From path or "all" |
| `dose_uC_cm2` | float | From `actual_dose` column |
| `replicate` | int | From `replicate_id` |
| `sample_id` | str | From `sample_name` |
| `display_name` | str | From `display_name` |
| `PC1` | float | From scores |
| `PC2` | float | From scores |
| `PC3` | float | From scores (optional) |

### Combined Loadings DataFrame

| Column | Type | Source |
|--------|------|--------|
| `analysis_id` | str | Generated: `{analysis_type}_{polarity}_{dose_label}` |
| `analysis_type` | str | From path |
| `polarity` | str | From path |
| `dose_label` | str | From path or "all" |
| `mz` | float | From `index` |
| `loading_PC1` | float | From `PC1` |
| `loading_PC2` | float | From `PC2` |
| `loading_PC3` | float | From `PC3` (optional) |
| `abs_loading_PC1` | float | From `PC1_Abs_Loading` |
| `rank_PC1` | int | From `PC1_Rank` |

### Combined Variance DataFrame

| Column | Type | Source |
|--------|------|--------|
| `analysis_id` | str | Generated |
| `analysis_type` | str | From path |
| `polarity` | str | From path |
| `dose_label` | str | From path or "all" |
| `PC` | int | Extracted from `Component` (1,2,3...) |
| `variance_ratio` | float | From `Variance_Explained_Percent` / 100 |
| `cumulative_variance` | float | From `Cumulative_Variance_Percent` / 100 |

### Combined Assignments DataFrame

| Column | Type | Source |
|--------|------|--------|
| `analysis_id` | str | Generated |
| `analysis_type` | str | From path |
| `polarity` | str | From path |
| `dose_label` | str | From path or "all" |
| `mz` | float | From `m/z` |
| `loading_PC1` | float | From `PC1 Loading` |
| `assignment` | str | From `Current Assignment` |
| `confidence` | str | From `Confidence` |
| `notes` | str | From `Notes` |

---

## Dose Label Mapping

**Pairwise analyses** have explicit dose folders:
- `2000` → 2000 µC/cm²
- `5000` → 5000 µC/cm²
- `10000` → 10000 µC/cm²
- `15000` → 15000 µC/cm²

**Other analyses** span multiple doses:
- `Dose-Trajectory` → dose_label = `"trajectory"`
- `Dose-Dependant` → dose_label = `"dependant"`

---

## Configuration Requirements

The `config/tofsims.yaml` should specify:
1. **Root output directory**: `outputs`
2. **Analysis types and patterns**: glob patterns for each
3. **Sheet names**: standardized names for Excel sheets
4. **Column mappings**: rename rules if needed
5. **Dose mapping**: folder name → actual dose value
6. **Results directory**: where unified datasets are saved

---

## Questions for Confirmation

### 1. Sheet Names
✅ Confirmed:
- `PCA Scores`
- `PCA Loadings`
- `Variance Explained`
- `Top 20 Loadings` (not yet used but available)
- `Analysis Summary` (metadata, not yet used)

### 2. Fragment Assignments
✅ Confirmed:
- **Location**: Co-located with each PCA file
- **Format**: CSV with columns `m/z`, `PC1 Loading`, `Current Assignment`, `Confidence`, `Action`, `Notes`
- **Status**: Already assigned, no re-assignment needed

### 3. Intensities Table
❓ **Question**: Do you have a raw intensities table (long-format with sample × m/z × intensity)?
- If yes: Where is it located and what format (CSV, Parquet, Excel)?
- If no: Should we extract intensities from the original ToF-SIMS data files?
- **Purpose**: Needed for univariate statistics (t-tests, effect sizes) alongside PCA

### 4. Additional Metadata
❓ **Question**: Should we preserve the `Analysis Summary` sheet contents?
- Contains: analysis parameters, date, software version, preprocessing steps
- Useful for: reproducibility, provenance tracking

### 5. Output Location
❓ **Question**: Where should unified/combined datasets be saved?
- Option 1: `outputs/combined/` (new directory)
- Option 2: `results/` (existing directory)
- Formats: Parquet (fast), CSV (portable), or both?

---

## Next Steps

1. Review proposed schemas and confirm they match your needs
2. Answer the 3 questions above (intensities, metadata, output location)
3. I'll generate `config/tofsims.yaml` with your specifications
4. Implement loaders: `load_pca_scores()`, `load_pca_loadings()`, `load_variance()`, `load_assignments()`
