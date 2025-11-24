# Fragment Groups & Metrics Implementation Plan

## Overview
This document outlines the integration of fragment classification and chemical metrics into the ToF-SIMS PCA GUI.

## Scientific Basis

### Literature References
1. **Sjövall et al. (2023)** - Energy & Fuels - PAH fragmentation patterns
2. **Mei et al. (2022)** - Journal of Polymer Science - Polymer surface characterization

### Key Findings
- **Aromatic fragments** can be identified by characteristic markers (C₆H₅⁺, C₇H₇⁺, C₆H₅O⁻)
- **Saturation** determined by DBE (Double Bond Equivalents) calculation
- **H-deficiency** indicated by H/C ratios < 0.8 (polyynes, allenes)
- **Crosslinking** inferred from fragment intensity ratios (C₆H⁻/C₄H⁻)

## Implementation Components

### 1. Fragment Classifier (`fragment_classifier.py`) ✅
**Status:** Completed and committed

**Functions:**
- `classify_fragment()` - Complete classification of a fragment
- `calculate_dbe()` - Double bond equivalents
- `calculate_h_c_ratio()` - Hydrogen/carbon ratio
- `is_aromatic_marker()` - Check against literature markers
- `classify_chemical_family()` - Assign to family group

**Classification System:**
```python
families = {
    'Aromatic',                  # Literature-validated markers
    'H-deficient_unsaturated',   # Polyynes, allenes (H/C < 0.8)
    'Unsaturated_carbon',        # DBE = 1-3
    'Saturated_carbon',          # DBE = 0
    'Organic_oxygen',            # Contains oxygen
    'Al-based',                  # Aluminum-containing
    'Carbonyl',                  # High O/H ratio
    'Contamination',
    'Unknown'
}
```

### 2. Fragment Group Plotting (`fragment_group_plotting.py`) ✅
**Status:** Completed and committed

**Visualization Modes:**

#### Mode 1: Fragment Groups + PCA Loadings (After PCA)
- **Top panel:** Intensity stick spectrum colored by chemical family
- **Bottom panel:** PCA loadings showing which fragments drive PC separation
- **Highlighting:** High-loading fragments (|loading| > threshold) emphasized

#### Mode 2: Family Summary (Before PCA, Exploratory)
- **Pie chart:** Fragment count by family
- **Bar chart:** Total intensity by family

**Color Scheme:**
```python
FAMILY_COLORS = {
    'Aromatic': '#E74C3C',              # Red
    'H-deficient_unsaturated': '#9B59B6',  # Purple
    'Unsaturated_carbon': '#3498DB',    # Blue
    'Saturated_carbon': '#2ECC71',      # Green
    'Organic_oxygen': '#F39C12',        # Orange
    'Al-based': '#95A5A6',              # Gray
}
```

### 3. Crosslinking Metrics Calculator ⏳
**Status:** In progress

**Metrics to Calculate:**
1. **C₆H⁻/C₄H⁻ ratio** - PMMA crosslinking indicator (negative ions)
2. **H-deficient fraction** - From Sjövall Eq. 1:
   ```
   f_deficient = (C₄H₃ + C₅H₃ + C₇H₃) / (C₄H₃ + C₅H₃ + C₇H₃ + C₄H₉ + C₅H₉ + C₇H₁₁)
   ```
3. **Molecular ion / fragment ratio** - Decreases with crosslinking

**Comparative Analysis:**
- Calculate for each sample in PCA
- Plot trends across sample series (e.g., SQ2 → SQ8)
- Enable comparison between treatment conditions

## GUI Integration Plan

### Phase 1: Add Fragment Groups Tab to Stick Spectrum ⏳

**Location:** Stick Spectrum tab → Add sub-tabs
```
Stick Spectrum
├── [Mass Spectrum] (existing)
├── [Fragment Groups] (NEW)
└── [Crosslinking Metrics] (NEW)
```

**Workflow:**
1. User loads data
2. User runs PCA
3. **Fragment Groups tab automatically activates:**
   - Classifies all detected fragments
   - Plots intensity by chemical family
   - Overlays PCA loadings for selected PC
4. **Crosslinking Metrics tab:**
   - Shows C₆H⁻/C₄H⁻ ratios for all samples
   - Plots H-deficient fraction trends
   - Enables sample-to-sample comparison

### Phase 2: Interactive Features

**User Controls:**
- **PC selector:** Choose which PC's loadings to display
- **Loading threshold slider:** Adjust |loading| cutoff for highlighting (0.05 - 0.3)
- **Family filter checkboxes:** Show/hide specific chemical families
- **Sample selector:** Choose which sample to analyze (for metrics)

**Hover Tooltips:**
- Fragment formula and mass
- Chemical family
- DBE and H/C ratio
- PCA loading value

### Phase 3: Export Capabilities

**Data Export:**
- CSV of classified fragments with properties
- Crosslinking metrics table (all samples)

**Figure Export:**
- High-res PNG/PDF of fragment groups plot
- Combined report with all visualizations

## Usage Example

### Scenario: Analyzing Alucone Dose Series (SQ2 → SQ8)

**Step 1: Load and Run PCA**
```
User: Load AllPosNew_processed.txt
User: Run PCA with 5 components
```

**Step 2: Examine Fragment Groups**
```
GUI shows:
- PC1 loadings highlight aromatic fragments (C₆H₅⁺, C₇H₇⁺)
- PC2 loadings show H-deficient fragments (C₄H⁻, C₆H⁻)
- Color-coded families reveal composition patterns
```

**Step 3: Check Crosslinking Metrics**
```
GUI calculates:
- C₆H⁻/C₄H⁻ ratio: SQ2 = 0.45, SQ5 = 0.72, SQ8 = 0.85
- Interpretation: Higher doses → increased crosslinking
```

**Step 4: Interpret Results**
- **PC1 separation:** Driven by aromatic content differences
- **Crosslinking trend:** Monotonic increase with dose
- **Scientific conclusion:** E-beam exposure increases network formation

## Code Integration Points

### In `pyside_app_matplotlib.py`:

```python
# After PCA computation in PCAWorker:
def run(self):
    # ... existing PCA code ...

    # NEW: Classify fragments after PCA
    from fragment_classifier import classify_fragment

    fragment_properties = []
    for i, mass in enumerate(self.pca.mass_list):
        # Get formula from database or manual assignment
        formula = self.get_fragment_formula(mass)
        if formula:
            props = classify_fragment(formula, mass, self.polarity)
            fragment_properties.append(props)

    self.results['fragment_properties'] = fragment_properties
    self.finished.emit(self.results)
```

### In Stick Spectrum Tab:

```python
# Add sub-tabs
self.stick_tabs = QTabWidget()
self.mass_spectrum_widget = ... # existing
self.fragment_groups_widget = FragmentGroupWidget()
self.crosslinking_widget = CrosslinkingMetricsWidget()

self.stick_tabs.addTab(self.mass_spectrum_widget, "Mass Spectrum")
self.stick_tabs.addTab(self.fragment_groups_widget, "Fragment Groups")
self.stick_tabs.addTab(self.crosslinking_widget, "Crosslinking Metrics")
```

### Fragment Groups Widget:

```python
class FragmentGroupWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Canvas
        self.canvas = FragmentGroupPlotCanvas()

        # Controls
        self.pc_selector = QComboBox()  # PC1, PC2, ...
        self.threshold_slider = QSlider()  # 0.05 - 0.3
        self.family_filters = {}  # Checkboxes for each family

    def update_plot(self, fragments, loadings, pc_num):
        """Called after PCA completes"""
        self.canvas.plot_fragment_groups(
            fragments, loadings, pc_num,
            loading_threshold=self.threshold_slider.value()/100
        )
```

## Testing Strategy

### Unit Tests
- ✅ `test_fragment_classifier.py` - Classification accuracy
- ⏳ `test_fragment_plotting.py` - Visualization correctness
- ⏳ `test_crosslinking_metrics.py` - Metric calculations

### Integration Tests
- ⏳ End-to-end: Load data → PCA → Fragment groups display
- ⏳ Verify fragment counts match between modules
- ⏳ Confirm loading values correspond to correct fragments

### Visual QA
- ⏳ Check color scheme consistency
- ⏳ Verify high-loading fragments are correctly highlighted
- ⏳ Confirm tooltips show correct information

## Git Workflow

```bash
# Current branch
feature/stick-spectrum-tab

# Commits so far:
✅ fd4c17d - Add fragment group plotting with PCA loadings overlay
✅ 426fd50 - Add fragment classifier with DBE and aromatic markers

# Next commits:
⏳ Add crosslinking metrics calculator
⏳ Integrate fragment groups into Stick Spectrum tab
⏳ Add interactive controls and tooltips
⏳ Add export capabilities
```

## Next Steps

1. **Implement crosslinking metrics calculator** (30 min)
2. **Create FragmentGroupWidget** for GUI (1 hour)
3. **Integrate into existing Stick Spectrum tab** (1 hour)
4. **Test with real data** (AllPosNew_processed.txt) (30 min)
5. **Add export features** (30 min)

**Total estimated time:** 3.5 hours

## Questions for User

1. **Plotting preference:**
   - Option A: Plot ALL fragment groups (comprehensive)
   - Option B: Plot only top N highest-loading fragments (focused)
   - Option C: Both (tabs or toggle) ← **Recommended**

2. **Crosslinking metrics:**
   - Display as table or plot?
   - Show all samples simultaneously or select one?

3. **Export format:**
   - CSV only, or also JSON/Excel?
   - Separate files or combined report?

---

**Generated:** 2025-11-21
**Status:** Implementation in progress
**Branch:** `feature/stick-spectrum-tab`
