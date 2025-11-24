# Claude Development Environment - ToF-SIMS PCA Analysis

## 🚀 **Working Qt Application Environment: `pca-sims`**

### **Critical Environment Activation**
The project uses **miniforge/mamba** with a dedicated `pca-sims` environment that contains all required packages.

**ALWAYS use this command pattern for ALL Python operations:**
```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python [your_command]
```

### **Environment Details**
- **Location**: `/home/dreece23/miniforge3/envs/pca-sims/`
- **Python**: 3.10.18
- **Key Packages**:
  - PySide6 (Qt6 GUI framework)
  - pandas 2.3.2, numpy 2.2.6
  - scikit-learn (PCA computation)
  - matplotlib 3.x (native plotting)

---

## 📁 **Refactored MVC Project Structure**

**Status**: Refactored (Phases 1-7.1 Complete - November 2025)

```
/home/dreece23/pca-sims/
├── launch_optimized.py                 # ✅ Primary Qt6 launcher
├── data/                              # ✅ ToF-SIMS data files
│   ├── NegativeIon/NegIonTIC.txt     # Example dataset (921 masses, 15 samples)
│   └── FragmentDatabase/              # Fragment assignment database
│       └── alucone_fragments_complete.json
├── src/                               # ✅ MVC Architecture
│   ├── models/                        # 📦 Data models (no Qt dependencies)
│   │   ├── pca_model.py              # PCA results container
│   │   ├── sample_model.py           # Sample metadata with Polarity enum
│   │   ├── fragment_model.py         # Fragment ions and assignments
│   │   └── spectrum_model.py         # Mass spectrum data
│   ├── services/                      # 🔧 Business logic layer
│   │   └── fragment_service.py       # Fragment database operations (280 lines)
│   ├── widgets/                       # 🎨 Reusable UI components
│   │   ├── tabs/                     # Tab widgets
│   │   │   ├── summary_tab.py
│   │   │   └── main_results_tab.py
│   │   ├── dialogs/                  # Dialog windows
│   │   │   ├── data_preview_dialog.py
│   │   │   ├── fragment_assignment_dialog.py
│   │   │   ├── custom_dose_dialog.py
│   │   │   └── manual_assignment_dialog.py
│   │   ├── plotting/                 # Matplotlib canvases
│   │   │   ├── matplotlib_plotting.py
│   │   │   ├── stick_spectrum_plotting.py
│   │   │   └── fragment_group_plotting.py
│   │   ├── fragment_analysis_tab.py  # Fragment analysis UI
│   │   └── common.py                 # Shared widgets
│   ├── core/                          # 🧮 Domain logic
│   │   ├── fragment_classifier.py
│   │   ├── crosslinking_metrics.py
│   │   └── fragment_mass_calculator.py
│   ├── pyside_app_matplotlib.py       # ✅ Main GUI (5,848 lines - down from 7,093)
│   ├── simple_tof_sims_pca.py        # PCA analysis engine
│   ├── tofsims_excel_processor.py    # Excel import processor
│   └── multi_ion_manager.py          # Multi-polarity data manager
├── scripts/utilities/                 # ✅ Organized utilities
│   └── manage_fragment_database.py   # Database management tool
├── outputs/                           # ✅ Results export directory
├── docs/                             # 📚 Documentation
│   ├── ARCHITECTURE.md               # Detailed architecture documentation
│   ├── REFACTORING_PLAN.md           # Refactoring progress tracking
│   └── TECHNICAL_REFERENCE.md        # Methods and capabilities
└── literature/                       # Scientific references
```

**Refactoring Impact:**
- Main GUI: 7,093 → 5,848 lines (17.6% reduction)
- ~15,000 lines removed/reorganized
- MVC architecture with services and models
- Improved modularity: 5/10 → 7.5/10

---

## 🚀 **Single Launch Command**

### **Start Qt6 Application**
```bash
cd /home/dreece23/pca-sims
source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python launch_optimized.py
```

**Features Available:**
- ✅ Native Qt6 interface with matplotlib plotting
- ✅ Data loading and preview
- ✅ PCA computation with progress tracking
- ✅ Interactive visualization
- ✅ Group-based sample management
- ✅ Multi-sheet Excel export functionality
- ✅ Publication-quality plots

---

## 🧪 **Test Core Functionality**
```bash
cd /home/dreece23/pca-sims
source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python -c "
import sys; sys.path.append('src')
from simple_tof_sims_pca import SimpleToFSIMSPCA
pca = SimpleToFSIMSPCA('data/NegativeIon/NegIonTIC.txt')
pca.load_data(); pca.preprocess_data(); pca.run_pca(5)
print(f'✅ PC1 variance: {pca.variance_explained[0]:.1f}%')
"
```
**Expected Output**: `✅ PC1 variance: ~89.3%`

---

## 📊 **System Capabilities**

### **PCA Analysis Engine** (`simple_tof_sims_pca.py`)
- **Data Loading**: ToF-SIMS text file format support
- **Preprocessing**: Mean centering, scaling options
- **PCA Computation**: scikit-learn implementation
- **Variance Explained**: Component contribution analysis

### **Qt6 Application** (`pyside_app_matplotlib.py`)
- **Native Interface**: PySide6 with matplotlib backend
- **Threaded PCA**: Non-blocking computation with progress
- **Interactive Plotting**: Publication-ready visualizations
- **Data Management**: Sample grouping and selection
- **Export Functionality**: Results to Excel/CSV formats

### **Plotting System** (`matplotlib_plotting.py`)
- **Scores Plots**: Principal component visualization
- **Loadings Analysis**: Variable contribution plots
- **Interactive Features**: Zoom, pan, save functionality
- **Publication Quality**: High-DPI, customizable styling

---

## 🔧 **Qt6 Environment Setup**

### **Required Qt6 Installation**
- **Location**: `/home/dreece23/Qt/6.x.x/gcc_64/`
- **Components**: Core, Gui, Widgets, WebEngineWidgets
- **Platform**: xcb (X11) display support

### **Environment Variables (Set Automatically)**
```bash
QTDIR=/home/dreece23/Qt/6.x.x/gcc_64
QT_PLUGIN_PATH=$QTDIR/plugins
LD_LIBRARY_PATH=$QTDIR/lib:$LD_LIBRARY_PATH
QT_QPA_PLATFORM=xcb
```

---

## ⚙️ **Development Workflow**

### **Adding New Features**
1. **Modify Core**: Update `simple_tof_sims_pca.py` for analysis features
2. **Extend GUI**: Add components to `pyside_app_matplotlib.py`
3. **Update Plotting**: Enhance `matplotlib_plotting.py` for visualization
4. **Test**: Use single launcher to verify functionality

### **Data Analysis Pipeline**
1. **Load Data**: ToF-SIMS text files with mass spectra
2. **Preprocess**: Optional scaling and transformation
3. **Compute PCA**: Dimensionality reduction analysis
4. **Visualize**: Interactive scores and loadings plots
5. **Export**: Results to Excel with multiple sheets

### **File Organization**
- **Keep `src/` Clean**: Only essential application modules
- **Use `scripts/`**: For utilities and testing
- **Output to `outputs/`**: All generated results
- **Document in `docs/`**: Analysis documentation

### **Test and Debug Policy**
- **Clean up successful tests**: Remove test files after verification
- **No persistent debug scripts**: Delete debug files once issues are resolved
- **Maintain strict structure**: Only keep necessary files for production
- **Document major fixes**: Add brief notes to CLAUDE.md, remove detailed test files

---

## 📝 **Documentation Governance**

### **Project Scope - Data Processing NOT Interpretation**
This is a **data processing and analysis toolkit** - it generates analyzed datasets, NOT scientific conclusions.

### **Allowed Documentation**
✅ **Technical specifications** (data formats, schemas, APIs)
✅ **Usage instructions** (how to run scripts, load data)
✅ **Configuration references** (YAML parameters, options)
✅ **Code structure** (module organization, key functions)
✅ **Development workflow** (git, testing, deployment)
✅ **Performance metrics** (speed, memory usage, validation results)

### **Prohibited Documentation**
❌ **Scientific interpretations** (chemistry, mechanisms, "why" explanations)
❌ **Research conclusions** (findings, discoveries, cause-effect claims)
❌ **Publication materials** (figures, tables, manuscripts)
❌ **Future research plans** (experiments, hypotheses, speculative applications)
❌ **Summary/report markdown files** (unless explicitly requested by user)

### **Documentation Standards**

**✅ Good Examples** (objective, data-focused):
- "Fragment m/z 65.0031 assigned to C₄HO⁻ with High confidence (±0.0004 Da error)"
- "Intensity increases 119% from SQ2 to SQ5 (3 replicates, p < 0.01)"
- "PC1 explains 89.3% variance across dose series"
- "Assignment success rate: 95% (improved from 60% via database fix)"

**❌ Bad Examples** (interpretive, conclusive):
- "Thermodynamic stabilization creates optimized networks"
- "Carbonyl cascade demonstrates radical rearrangement mechanism"
- "E-beam processing transforms resist into semiconductive material"
- "This discovery enables novel applications in quantum devices"

### **AI Assistant Instructions**
- **Never create** summary/report markdown files without explicit user request
- **Provide summaries** in chat responses only (not as files)
- **Update existing docs** only for technical changes (new features, bug fixes, config updates)
- **Ask before creating** any new documentation file
- **Consolidate** rather than proliferate documents
- **Report trends and patterns** without causal explanations - let researchers interpret

### **Core Documentation Files** (keep minimal)
1. `README.md` - Project overview, quick start, technical specs
2. `CLAUDE.md` - Development environment, workflows, governance (this file)
3. `docs/TECHNICAL_REFERENCE.md` - Methods, capabilities, configuration
4. `docs/IO_CONTRACT.md` - Data schemas and file formats
5. `docs/README_INTENSITIES.md` - Intensity import guide
6. `config/tofsims.yaml` - System configuration

All other documentation should be archived or deleted unless actively needed for development.

---

## 🏗️ **MVC Architecture Overview**

### **Design Philosophy**
The application follows Model-View-Controller (MVC) principles with an additional Service layer for business logic.

### **Layer Responsibilities**

#### **Models** (`src/models/`)
- Pure Python dataclasses with type hints
- No Qt or UI dependencies
- Validation in `__post_init__`
- Easy to test and serialize

```python
from models import Sample, Polarity

sample = Sample(
    name="SQ2_Rep1",
    dose=2.0,
    polarity=Polarity.NEGATIVE
)
```

#### **Services** (`src/services/`)
- Business logic and data operations
- Stateful service objects with caching
- No direct UI interaction
- Independently testable

```python
from services import FragmentService

fragment_service = FragmentService()
fragment_service.load_database()
candidates = fragment_service.find_candidates(65.0031, 'negative')
```

#### **Widgets** (`src/widgets/`)
- Reusable UI components
- Self-contained with minimal coupling
- Signal-based communication
- Tabs, dialogs, and plotting canvases

#### **Core** (`src/core/`)
- Domain-specific algorithms
- Fragment classification
- Crosslinking metrics
- Mass calculations

#### **Main GUI** (`src/pyside_app_matplotlib.py`)
- Application orchestration
- Event handling and routing
- Service initialization
- Top-level window management

**See `docs/ARCHITECTURE.md` for detailed architecture documentation.**

---

## 🔄 **Git Workflow & Development Process**

### **Repository Setup**
- **GitHub Repository**: `git@github.com:dreece2304/pca-sims.git`
- **Main Branch**: `main` (protected, production-ready code)
- **Clean Initial Commit**: All core functionality committed and documented

### **Feature Development Workflow**
```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/new-analysis-tool

# 2. Develop and test feature
# ... make changes ...
git add .
git commit -m "Add new analysis tool with tests

✅ Features implemented
🧪 Tests passing
📚 Documentation updated"

# 3. Push feature branch
git push -u origin feature/new-analysis-tool

# 4. Create pull request on GitHub
# 5. Review, test, and merge to main
```

### **Branch Protection Strategy**
- **Main branch**: Protected, requires pull requests
- **Feature branches**: `feature/description` for new functionality
- **Hotfix branches**: `hotfix/bug-description` for critical fixes
- **Experimental branches**: `experiment/research-topic` for research

### **Commit Message Convention**
```
Brief description of change

✅ What was implemented/fixed
🧪 Testing status
📚 Documentation updates
🔄 Breaking changes (if any)

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### **Development Guidelines**
1. **Always branch from main** for new features
2. **Keep commits focused** on single features/fixes
3. **Test before committing** - run PCA analysis to verify
4. **Clean up test files** after successful implementation
5. **Update CLAUDE.md** with significant changes
6. **Use descriptive branch names** that explain the feature

### **Release Process**
1. **Feature branches** → **main** via pull request
2. **Tag releases** for major versions: `v1.0.0`, `v1.1.0`
3. **GitHub Releases** with changelog and analysis examples
4. **Backup critical data** before major updates

---

## 📋 **Status: PRODUCTION READY**

✅ **Core Functionality**: PCA analysis with ToF-SIMS data
✅ **Qt6 Interface**: Native application with matplotlib
✅ **Data Handling**: Load, preview, process mass spectra
✅ **Visualization**: Interactive publication-quality plots
✅ **Export Capabilities**: Excel, CSV, image formats
✅ **Environment**: Stable mamba/conda setup
✅ **Project Structure**: Clean, organized, maintainable

### **Recent Updates (October 2025)**
📦 **IO System**: Unified data loading with parquet caching
📊 **Statistical Tools**: Pairwise comparisons, dose trajectory analysis
🗃️ **Data Pipeline**: tofsims package for data import/preprocessing
📚 **Documentation Consolidation**: Streamlined to core technical docs
🎯 **Project Scope**: Clear separation of data processing vs interpretation

### **Major Refactoring (November 2025) - Phases 1-7.1 Complete**

#### **Phase 1-2: Cleanup & Excel Import**
- 🧹 Removed 30 unused files (~5,000 lines)
- 📊 Direct Excel import with GUI
- 🐛 Fixed duplicate m/z handling bug
- 🧬 Fragment database uses exact calculated m/z

#### **Phase 3: MVC Foundation**
- 📦 Created `src/models/` with 4 dataclass models (875 lines)
- 🔧 Created `src/core/` for domain logic
- 📁 Organized widget/dialog/plotting structure
- ✅ Removed unused batch processing system (~5,000 lines)

#### **Phase 4-5: Widget & Dialog Extraction**
- 🎨 Reorganized widgets into package structure
- 💬 Extracted 3 large dialogs (1,095 lines)
- 📝 Created proper `__init__.py` exports
- ✅ All GUI functionality preserved

#### **Phase 6.1: Tab Extraction**
- 📋 Extracted Summary and Main Results tabs
- 🔧 Created `src/widgets/tabs/` package
- ✅ Reduced main GUI by 12 lines

#### **Phase 7.1: Service Layer**
- 🔧 Created `src/services/` package
- 📊 Implemented FragmentService (280 lines):
  - Fast mass-based indexing (O(1) lookups)
  - PPM tolerance-based fragment matching
  - Automatic backup management
  - Polarity filtering
- ✅ Reduced main GUI by 138 lines (2.3%)

#### **Phase 8: Documentation & Cleanup**
- 📚 Created comprehensive `docs/ARCHITECTURE.md`
- 📝 Updated `CLAUDE.md` with MVC architecture
- ✅ All code has type hints and docstrings

**Current Status:**
- Main GUI: 7,093 → 5,848 lines (17.6% reduction)
- Total code removed/reorganized: ~15,000 lines
- MVC architecture established
- Modularity improved: 5/10 → 7.5/10

**Last Updated**: November 23, 2025 - Phase 8 Complete