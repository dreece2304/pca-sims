# GUI Integration Guide - Fragment Analysis Tab

## Changes Required to `pyside_app_matplotlib.py`

### 1. Add Import at Top of File

```python
# Add after other imports (around line 41)
from fragment_analysis_tab import FragmentAnalysisTab
```

### 2. Initialize Fragment Analysis Tab in `create_plots_section()`

Add after Database Management tab (around line 1609):

```python
# Fragment Analysis tab (NEW - activates after PCA)
self.fragment_analysis_widget = FragmentAnalysisTab()
self.fragment_analysis_tab_index = self.plot_tabs.addTab(
    self.fragment_analysis_widget,
    "🧬 Fragment Analysis"
)
# Disable until PCA completes
self.plot_tabs.setTabEnabled(self.fragment_analysis_tab_index, False)
```

### 3. Populate Fragment Analysis Tab in `on_pca_finished()`

Add after existing result processing (after line where scores plots are updated):

```python
def on_pca_finished(self, results):
    """Handle PCA completion"""
    # ... existing code ...

    # NEW: Populate Fragment Analysis tab
    self._populate_fragment_analysis(results)

    # Enable Fragment Analysis tab
    self.plot_tabs.setTabEnabled(self.fragment_analysis_tab_index, True)
```

### 4. Add Helper Method `_populate_fragment_analysis()`

Add as new method in the class:

```python
def _populate_fragment_analysis(self, pca_results):
    """
    Populate Fragment Analysis tab with classified fragments and metrics

    Args:
        pca_results: Dict from PCA worker with loadings, scores, variance
    """
    try:
        # Get fragment data from PCA
        masses = self.pca.mass_list
        sample_names = self.pca.sample_names

        # Get current polarity
        polarity = self.multi_ion_manager.current_polarity

        # Get formulas - try to match from database or use manual assignments
        formulas = []
        for mass in masses:
            formula = self._get_fragment_formula(mass, polarity)
            formulas.append(formula if formula else f"Unknown_{mass:.4f}")

        # Get intensities for all samples (normalized)
        intensities = []
        for i in range(len(sample_names)):
            sample_intensities = self.pca.data_normalized[i, :]
            intensities.append(sample_intensities)

        # Build fragment data dict
        fragment_data = {
            'masses': masses,
            'formulas': formulas,
            'intensities': intensities
        }

        # Populate the tab
        self.fragment_analysis_widget.set_data(
            fragment_data,
            pca_results,
            sample_names,
            polarity
        )

        print(f"✅ Fragment Analysis tab populated: {len(masses)} fragments, {len(sample_names)} samples")

    except Exception as e:
        print(f"⚠️  Error populating Fragment Analysis: {e}")
        import traceback
        traceback.print_exc()


def _get_fragment_formula(self, mass, polarity):
    """
    Get chemical formula for a fragment mass

    Tries (in order):
    1. User-confirmed manual assignments
    2. Fragment database matches
    3. Returns None if no match

    Args:
        mass: Fragment m/z value
        polarity: 'negative' or 'positive'

    Returns:
        Chemical formula string or None
    """
    # Check user-confirmed assignments first
    mass_key = f"{mass:.4f}"
    if mass_key in self.user_confirmed_assignments:
        assignment = self.user_confirmed_assignments[mass_key]
        # Extract formula from assignment (e.g., "C_6H_5+" -> "C6H5")
        formula = assignment.replace('_', '').replace('+', '').replace('-', '')
        return formula

    # Check fragment database
    if hasattr(self, 'fragment_db') and self.fragment_db:
        matches = self.find_fragment_matches(mass, polarity, tolerance_da=0.01)
        if matches:
            # Use first (best) match
            best_match = matches[0]
            if 'formulas' in best_match and best_match['formulas']:
                return best_match['formulas'][0].replace('_', '')

    return None
```

## Expected Workflow After Integration

1. **User loads data** → Fragment Analysis tab disabled (grayed out)

2. **User runs PCA** → PCA worker processes data

3. **PCA completes** → `on_pca_finished()` called:
   - Existing plots update (scores, loadings)
   - **NEW**: Fragment Analysis tab populated
   - Fragment Analysis tab enabled (clickable)

4. **User clicks Fragment Analysis tab**:
   - See "Fragment Groups" sub-tab:
     - All fragments colored by chemical family
     - PC1 loadings overlaid by default
     - Can change PC, adjust threshold, filter
   - See "Chemical Metrics" sub-tab:
     - Table with C6H-/C4H- ratios for all samples
     - Plot showing trends
     - Export buttons

5. **User exports data**:
   - CSV: All fragments with DBE, H/C ratio, loadings
   - JSON: Complete classification with metadata
   - PNG/PDF: Plots for publication

## Testing Checklist

After integration, test:

- [ ] Fragment Analysis tab is disabled on startup
- [ ] Tab enables after PCA completes
- [ ] Fragment Groups shows classified fragments
- [ ] Can select different PCs
- [ ] Loading threshold slider works
- [ ] "Show only high-loading" filter works
- [ ] Chemical Metrics table populates
- [ ] Trends plot shows data
- [ ] CSV export works
- [ ] JSON export works
- [ ] Plot export works
- [ ] Works with both negative and positive ions
- [ ] Works with AllPosNew_processed.txt test data

## Fallback Plan

If fragment formula matching doesn't work initially:
- System will use `"Unknown_{mass}"` as placeholder
- Fragment classifier will still work (uses mass + formula)
- Classification will be less accurate but won't crash
- Can improve formula matching incrementally

## File Locations

All new code is in:
```
src/fragment_classifier.py          - DBE, H/C calculations
src/fragment_group_plotting.py      - Visualization module
src/crosslinking_metrics.py         - Metrics calculator
src/fragment_analysis_tab.py        - Main tab widget
```

No changes to existing analysis code (`simple_tof_sims_pca.py`)

## Git Status

All modules committed:
```bash
git log --oneline -5
c22399d Add Fragment Analysis tab with fragment groups and metrics
292bc47 Remove auto-interpretations from crosslinking metrics
976cb86 Add crosslinking metrics calculator with trend analysis
fd4c17d Add fragment group plotting with PCA loadings overlay
426fd50 Add fragment classifier with DBE, H/C ratio, and aromatic marker detection
```

Ready for integration into main GUI.
