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

## 📁 **Clean Project Structure**

```
/home/dreece23/pca-sims/
├── launch_optimized.py                 # ✅ Primary Qt6 launcher (WORKING)
├── data/NegativeIon/NegIonTIC.txt     # ✅ ToF-SIMS data (921 masses, 15 samples)
├── src/                               # ✅ Core application modules
│   ├── pyside_app_matplotlib.py       # ✅ Main Qt6 application (55KB)
│   ├── simple_tof_sims_pca.py         # ✅ PCA analysis engine
│   ├── matplotlib_plotting.py         # ✅ Native matplotlib plotting
│   └── data_preview_dialog.py         # ✅ Data preview component
├── scripts/                           # ✅ Organized utilities
│   ├── tests/                         # Test scripts
│   └── utilities/                     # Helper utilities
├── outputs/                           # ✅ Results export directory
├── data/                             # ✅ Input data directory
├── docs/                             # Documentation
└── literature/                       # Scientific references
```

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

### **Recent Updates (September 2025)**
🧹 **Project Reorganization**: Removed 14 redundant files
🧹 **Single Launcher**: Consolidated to `launch_optimized.py`
🧹 **Clean Structure**: Organized scientific project layout
🧹 **Bug Fix**: Sample deselection/reselection now works correctly
🎨 **Viridis Colors**: Consistent viridis color scheme throughout
📊 **Enhanced Results**: Added PC1 score and loadings interpretation
🧪 **Test Policy**: Clean up successful tests, maintain strict structure

**Ready for Enhancement**: Add new analysis features, improve visualizations, extend data support.

**Last Updated**: September 2025 - Enhanced Production System