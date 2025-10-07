# ToF-SIMS PCA Data Processing & Analysis Pipeline

## **Status: PRODUCTION READY**

A robust, reproducible data processing system for Time-of-Flight Secondary Ion Mass Spectrometry (ToF-SIMS) analysis with PCA computation, fragment assignment, and statistical analysis tools.

**Last Updated**: October 2025

---

## 🚀 **Quick Start**

### **Environment Setup**
```bash
# Required: pca-sims mamba environment (Python 3.10.18)
source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims
```

### **Core Workflows**

**GUI Application** (Qt6 with matplotlib):
```bash
python launch_optimized.py
```

**Data Import & Caching**:
```bash
# Import raw intensity matrices
python scripts/import_matrix_intensities.py

# Generate unified PCA cache
python scripts/cache_pca.py
```

### **Key Capabilities**
- **SIMS-Optimized PCA**: √(intensity) transform, mean centering, Pareto scaling
- **Fragment Assignment**: Multi-database integration with ppm tolerance matching
- **Statistical Analysis**: Pairwise comparisons, dose-response trends, replicate validation
- **Data Export**: Excel workbooks, CSV, parquet caching, high-resolution plots

---

## 📊 **System Performance**

| Metric | Performance |
|--------|-------------|
| **Complete Workflow** | <60s |
| **PCA Computation** | <10s (921 features × 15 samples) |
| **Fragment Assignment** | <1s (1,176 loadings) |
| **Database Queries** | <10ms average |
| **Cache Loading** | <0.5s (parquet) |
| **Memory Usage** | <1GB |

### **Data Processing Results**
- **Dataset**: 12 PCA analyses (8 pairwise, 2 trajectory, 2 dependent)
- **Samples**: 102 scores records (15 unique samples)
- **Features**: 1,176 loading records (201 unique m/z)
- **Assignments**: 25.5% fragments assigned with confidence scores
- **Replicates**: 3 per condition, validated

---

## 📋 **Data Processing Workflow**

### **1. Raw Data Import**
- Input: Tab-delimited ToF-SIMS intensity matrices
- Formats: `P{replicate}_SQ{dose}` (e.g., P1_SQ4, P2_SQ2)
- Dose mapping: SQ0 (as-deposited), SQ2-SQ5 (2000-15000 µC/cm²)
- Note: SQ1 excluded (fully removed during development)

### **2. PCA Analysis**
- **Preprocessing**:
  - √(intensity) transform for variance stabilization
  - Mean centering for covariance analysis
  - Pareto scaling for peak balancing
- **Components**: 5-8 PCs capture >99% variance
- **Sample Selection**: P1-P3 patterns, SQ2-SQ5 doses

### **3. Fragment Assignment**
- **Methods**:
  - ppm tolerance matching (default: 10 ppm)
  - Mass defect analysis
  - Isotope pattern validation
- **Confidence Scoring**: High (>70%), Medium (50-70%), Low (<50%)
- **Element Constraints**: Configurable by material system

### **4. Statistical Analysis**
- Pairwise t-tests and effect sizes
- Dose-response correlation analysis
- Fragment trend visualization
- Replicate validation

### **5. Data Export**
- Excel workbooks (multi-sheet: scores, loadings, variance, assignments)
- CSV files for external analysis
- Parquet caching for fast repeated access
- High-resolution plots (PNG/SVG, 300 DPI)

---

## 🏗️ **System Architecture**

### **Core Modules**
```
pca-sims/
├── src/                             # Core analysis code
│   ├── simple_tof_sims_pca.py      # PCA engine
│   ├── matplotlib_plotting.py      # Visualization
│   ├── pyside_app_matplotlib.py    # Qt6 GUI
│   └── multi_ion_manager.py        # Multi-polarity coordination
├── tofsims/                         # Data IO package
│   ├── io.py                       # Data loaders
│   ├── preprocess.py               # Cleaning, validation
│   ├── stats.py                    # Statistical tests
│   └── figures.py                  # Plot generation
├── scripts/                         # Analysis pipelines
│   ├── cache_pca.py
│   ├── import_matrix_intensities.py
│   ├── process_all_pairwise_stats.py
│   └── visualize_fragment_trends.py
├── data/                            # Input data (raw)
│   ├── NegativeIon/
│   ├── PositiveIon/
│   └── FragmentDatabase/
├── outputs/                         # PCA results (generated, gitignored)
├── results/                         # Analysis outputs (generated, gitignored)
│   ├── cache/                      # Parquet files
│   ├── figures/                    # Plots
│   └── tables/                     # Statistical results
├── docs/                            # Technical documentation
│   ├── TECHNICAL_REFERENCE.md      # Methods & capabilities
│   ├── IO_CONTRACT.md              # Data schemas
│   └── README_INTENSITIES.md       # Intensity import guide
└── config/                          # System configuration
    └── tofsims.yaml                # Analysis parameters
```

### **Data Flow**
```
Raw ToF-SIMS Data → Import → PCA Analysis → Fragment Assignment → Statistics → Export
     (.txt)           ↓         (Excel)           (CSV)              ↓          ↓
                  Parquet                                         Figures   Tables
                  Cache
```

---

## 🔧 **Technical Specifications**

### **Environment**
- **Python**: 3.10.18 (mamba environment: `pca-sims`)
- **Core Packages**: NumPy 2.2.6, Pandas 2.3.2, Scikit-learn, Matplotlib 3.x
- **GUI**: PySide6 (Qt6), native matplotlib backend
- **Visualization**: Plotly 5.x, Altair 4.2.2
- **Platform**: Linux (WSL2 compatible)

### **Data Compatibility**
- **Input Format**: Tab-delimited ToF-SIMS data
- **Sample Size**: 15-50 samples, 500-2000 m/z features
- **Replicate Structure**: 3 replicates per condition
- **Polarity**: Positive and negative ion modes

### **Fragment Database**
- **Size**: 50,691+ fragments
- **Query Performance**: <10ms average
- **Assignment Methods**: Exact mass, mass defect, isotope patterns
- **Confidence Scoring**: Multi-criteria validation
- **Element Constraints**: Material-specific (C,H,O,Al for alucone)

---

## 📚 **Usage Examples**

### **Load Cached Data**
```python
import pandas as pd
from tofsims.io import load_intensities_cache

# Load PCA outputs
scores = pd.read_parquet('results/cache/scores_merged.parquet')
loadings = pd.read_parquet('results/cache/loadings_merged.parquet')
variance = pd.read_parquet('results/cache/variance_explained.parquet')

# Load raw intensities
intensities = load_intensities_cache()

# Filter examples
pairwise_10k = scores[scores['analysis_id'] == 'pairwise_positive_10000']
high_conf = loadings[loadings['confidence'] == 'High']
```

### **Run PCA Analysis**
```python
from src.simple_tof_sims_pca import SimpleToFSIMSPCA

pca = SimpleToFSIMSPCA('data/NegativeIon/NegIonTIC.txt')
pca.load_data()
pca.preprocess_data()  # Applies SIMS-optimized pipeline
pca.run_pca(5)

print(f"PC1 variance: {pca.variance_explained[0]:.1f}%")
```

### **Statistical Analysis**
```bash
# Pairwise comparisons
python scripts/process_all_pairwise_stats.py

# Fragment trends across doses
python scripts/visualize_fragment_trends.py

# Generate summary statistics
python scripts/analyze_fragment_statistics.py
```

---

## 🔧 **Troubleshooting**

### **Common Issues**
1. **Import errors**: Ensure `conda activate pca-sims` before running
2. **Empty cache**: Run `python scripts/cache_pca.py` first
3. **Missing files**: Check file paths in `config/tofsims.yaml`
4. **Assignment failures**: Adjust ppm_tolerance (try 10-50 ppm)

### **Validation Checks**
```bash
# Test core functionality
cd /home/dreece23/pca-sims
source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims

# Quick PCA test
python -c "
import sys; sys.path.append('src')
from simple_tof_sims_pca import SimpleToFSIMSPCA
pca = SimpleToFSIMSPCA('data/NegativeIon/NegIonTIC.txt')
pca.load_data(); pca.preprocess_data(); pca.run_pca(5)
print(f'✅ System OK: PC1 variance = {pca.variance_explained[0]:.1f}%')
"
```

### **Expected Output**
```
✅ System OK: PC1 variance = 89.3%
```

---

## 📖 **Documentation**

- **[TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)**: Methods, capabilities, configuration
- **[IO_CONTRACT.md](docs/IO_CONTRACT.md)**: Data schemas and file formats
- **[README_INTENSITIES.md](docs/README_INTENSITIES.md)**: Raw intensity import guide
- **[CLAUDE.md](CLAUDE.md)**: Development environment and workflows

---

## 🎯 **Project Scope**

**This toolkit provides**:
- ✅ Data import and preprocessing
- ✅ PCA computation with SIMS optimization
- ✅ Fragment assignment with confidence scoring
- ✅ Statistical analysis tools
- ✅ Data export and visualization
- ✅ Reproducible caching system

**This toolkit does NOT provide**:
- ❌ Scientific interpretation or conclusions
- ❌ Mechanistic explanations
- ❌ Publication figure preparation
- ❌ Research planning or experimental design

**Researchers use this system to generate analyzed datasets for their own interpretation and publication.**

---

## 📝 **Citation**

If you use this system in your research:
```
ToF-SIMS PCA Data Processing & Analysis Pipeline
Modular Data Processing System for Mass Spectrometry Analysis
[Your Institution], 2025
```

## 🤝 **Support**

For technical issues:
1. Check documentation: `docs/TECHNICAL_REFERENCE.md`
2. Verify environment: `conda activate pca-sims`
3. Run validation checks (see Troubleshooting section)
4. Check configuration: `config/tofsims.yaml`
