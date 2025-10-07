# Stick Spectrum Tab - Implementation Plan
**Feature Branch**: `feature/stick-spectrum-tab`
**Created**: 2025-10-07
**Status**: Planning Phase

---

## Overview

Add a new tab to the Qt GUI for displaying stick spectra (mass spectrum visualization) with fragment assignment and manual curation capabilities.

---

## Functional Requirements

### 1. Sample Selection
- **User selects ONE dose level**: SQ0 (as-deposited), SQ2 (2000), SQ3 (5000), SQ4 (10000), or SQ5 (15000 µC/cm²)
- **Automatic replicate averaging**: Average intensities across P1, P2, P3 replicates
- **Polarity-aware**: Respect current polarity (negative/positive) from main tab

### 2. Data Processing
- **Source data**: Raw TIC-normalized intensities from `data/NegativeIon/NegAllCompoundSearch.txt` or `data/PositiveIon/PosAllCompoundSearch.txt`
- **No preprocessing transforms**: Use raw intensities (NOT sqrt-transformed, NOT mean-centered)
- **Justification**:
  - TIC normalization already applied (appropriate for ToF-SIMS)
  - Stick spectra show absolute intensities (standard in mass spec)
  - Transforms distort relative peak heights

### 3. Stick Spectrum Visualization

#### Main Plot
- **X-axis**: m/z (mass-to-charge ratio)
- **Y-axis**: Mean intensity (TIC-normalized, averaged across replicates)
- **Sticks**: Vertical lines from baseline to intensity value
- **Fragment labels**: Displayed for selected peaks (user-controlled via table)
- **Clean design**: No error bars on sticks (keeps visualization uncluttered)

#### Secondary Plot (Toggle On/Off)
- **Standard Deviation Plot**: Separate subplot showing SD vs m/z
- **Purpose**: Shows replicate variability without cluttering main spectrum
- **Toggle button**: "Show/Hide Replicate Variability"

### 4. Filtering System (6 Filters, Implemented Incrementally)

#### Filter 1: Intensity Threshold (PRIORITY 1)
- **Type**: Adjustable slider
- **Range**: 0-100% of maximum intensity
- **Default**: 0% (show all)
- **Label**: "Min Intensity: X.XXX (Y% of max)"

#### Filter 2: Top N Peaks (PRIORITY 2)
- **Type**: Dropdown
- **Options**: 20, 50, 100, 200, All
- **Default**: All
- **Behavior**: Show only N highest intensity peaks

#### Filter 3: m/z Range (PRIORITY 3)
- **Type**: Two input fields (min, max)
- **Default**: Full range (auto-detect from data)
- **Validation**: min < max

#### Filter 4: PCA Loading Filter (PRIORITY 4)
- **Type**: Checkbox + slider
- **Enable condition**: Only if PCA has been run
- **Range**: 0-1.0 (absolute loading threshold)
- **Purpose**: Show only peaks that drive PCA separation
- **Scientific justification**: Focuses on chemically significant peaks

#### Filter 5: Statistical Significance (PRIORITY 5)
- **Type**: Checkbox + dropdown
- **Options**: Mean > 1×SD, Mean > 2×SD, Mean > 3×SD
- **Purpose**: Filter out highly variable/unreliable peaks

#### Filter 6: Assignment Status (PRIORITY 6)
- **Type**: Radio buttons
- **Options**: All, Assigned Only, Unassigned Only
- **Purpose**: QC and manual assignment workflow

### 5. Fragment Assignment Table (Pop-out Dialog)

#### Table Structure
**Columns**:
1. `m/z` (float, 4 decimals)
2. `Mean Intensity` (scientific notation)
3. `Std Dev` (scientific notation)
4. `CV%` (coefficient of variation: SD/mean × 100)
5. `Assignment` (string: formula or "Unassigned")
6. `Confidence` (High/Medium/Low or blank if unassigned)
7. `Show Label?` (checkbox)

**Features**:
- Sortable by any column
- Searchable (filter by m/z or assignment text)
- Double-click row → Opens Manual Assignment Dialog
- Export button → Save table to CSV

#### Manual Assignment Dialog (Reuse Existing Pattern)
**Tabs**:
1. **Peak Intensities**: Show replicate-level data (P1, P2, P3)
2. **Candidate Matches**: Auto-search database within tolerance
3. **Manual Entry**: User input form

**Manual Entry Form Fields**:
- **Formula** (required): Input field with element buttons (C, H, O, N, Al, Si, Cl, F, Na, K)
- **Element counts**: Number spinners (0-99 for each element)
- **Assignment name**: Text field (e.g., "C6H-", "AlO-")
- **Chemical family**: Dropdown (Al-based, Saturated_carbon, Unsaturated_carbon, Organic_oxygen, Carbonyl, Hydroxyl, Contamination, Unknown)
- **Confidence**: Dropdown (High, Medium, Low)
- **Notes**: Text area (optional)

**Validation**:
1. **Element validation**:
   - Allowed elements: C, H, O, N, Al, Si, Cl, F, Na, K (material + common contaminants)
   - At least one element must have count > 0
   - Warn if unusual combinations (e.g., Al + N)

2. **Chemical plausibility**:
   - Check valence rules (C=4, H=1, O=2, etc.)
   - Warn if violates common bonding patterns
   - Allow override with confirmation

3. **Mass accuracy validation**:
   - Calculate exact mass from formula
   - Compare to observed m/z
   - **Warn if error > 50 ppm**: "Calculated: X.XXXX Da, Observed: Y.YYYY Da, Error: ZZZ ppm"
   - Allow assignment anyway (user may have reason)

4. **Polarity validation**:
   - Check if assignment already exists in opposite polarity
   - Warn: "This assignment exists for [opposite] ions. Continue?"

**Save Action**:
- Update JSON database (`alucone_fragments_complete.json`)
- Create timestamped backup BEFORE modification: `alucone_fragments_complete_backup_YYYYMMDD_HHMMSS.json`
- Refresh assignment table
- Update stick plot labels

---

## Technical Implementation

### Code Reuse Strategy (Minimal New Code)

**REUSE existing infrastructure:**
1. **Data loading**: `simple_tof_sims_pca.py` → `load_data()`, `raw_data`, `mass_values`
2. **Database operations**: `pyside_app_matplotlib.py` → `load_fragment_database()`, `backup_database()`, `save_assignments_database()`
3. **Plotting setup**: `matplotlib_plotting.py` → `setup_matplotlib_for_screen()`, `FigureCanvas` base class
4. **Dialog pattern**: `pyside_app_matplotlib.py` → `FragmentAssignmentDialog` pattern (extend, don't duplicate)

### File Structure
```
src/
├── pyside_app_matplotlib.py          # EXTEND: Add StickSpectrumTab class (reuses existing methods)
├── stick_spectrum_plotting.py        # NEW: Minimal - inherits from FigureCanvas, uses existing setup
└── simple_tof_sims_pca.py           # REUSE: Import data loading methods
```

**NO separate fragment_assignment_utils.py** - database methods already exist in main app

### Data Flow
```
Raw TIC files → Load selected dose → Average replicates → Apply filters →
  Plot sticks + labels → User interaction → Manual assignment → Update database
```

### Database Management

#### Current State
- **Source of truth**: `data/FragmentDatabase/alucone_fragments_complete.json`
- **Unused files**: `NegFragmentsList.xlsx`, `PosFragmentsList.xlsx` → Move to `data/FragmentDatabase/archive/`

#### JSON Schema (from existing)
```json
{
  "metadata": {
    "version": "string",
    "total_fragments": int,
    "negative_fragments": int,
    "positive_fragments": int
  },
  "fragments": [
    {
      "mass": float,
      "assignments": [string],
      "formulas": [string],
      "families": [string],
      "confidences": [string],
      "polarity": "negative" | "positive",
      "notes": string (optional)
    }
  ]
}
```

#### Write Operations
1. Load JSON
2. Create backup with timestamp
3. Find fragment by m/z (±0.0001 Da) and polarity
4. If exists: Update fields
5. If new: Append to fragments list
6. Update metadata counts
7. Write to JSON (pretty print, indent=2)
8. Log action to console

---

## UI Layout (Stick Spectrum Tab)

```
┌─────────────────────────────────────────────────────────────┐
│ Dose Selection: [SQ0 ▼] [SQ2] [SQ3] [SQ4] [SQ5]           │
│ Polarity: Negative Ion (from main tab)                     │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐  │
│ │ [Filters Panel - Collapsible]                         │  │
│ │ ☐ Intensity Threshold: [====|----] 0.001 (5% of max) │  │
│ │ ☐ Top N Peaks: [All ▼]                               │  │
│ │ ☐ m/z Range: [1.0] to [300.0]                        │  │
│ │ ☐ PCA Loadings: [====----] |PC1| > 0.05              │  │
│ │ ☐ Statistical: Mean > 3×SD                           │  │
│ │ ☐ Assignment: ⦿ All  ○ Assigned  ○ Unassigned        │  │
│ └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐  │
│ │         MAIN STICK SPECTRUM                           │  │
│ │  Intensity                                             │  │
│ │  ^                                                     │  │
│ │  │    |                                                │  │
│ │  │    |         |      |                              │  │
│ │  │  | | |   |   |  |   | |  |                         │  │
│ │  │  | | | | | | |  | | | |  |                         │  │
│ │  └────────────────────────────────────────────> m/z   │  │
│ │       H⁻    C₆H⁻  Cl⁻   (selected labels shown)      │  │
│ └───────────────────────────────────────────────────────┘  │
│ [☐ Show Replicate Variability (SD plot)]                  │
│ ┌───────────────────────────────────────────────────────┐  │
│ │         SD PLOT (if toggled)                          │  │
│ │  SD                                                    │  │
│ │  ^     ·  ·                                            │  │
│ │  │   ·   ·  · ·  ·                                    │  │
│ │  └────────────────────────────────────────────> m/z   │  │
│ └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ [📋 View Fragment Table] [💾 Export Plot] [📊 Export Data]│
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Stages (Incremental Testing)

### Stage 1: Basic Stick Spectrum (NO FILTERS)
- ✓ Add tab to GUI
- ✓ Dose selection dropdown
- ✓ Load raw data for selected dose
- ✓ Average replicates (P1, P2, P3)
- ✓ Calculate SD
- ✓ Plot stick spectrum (all peaks, no labels)
- ✓ Toggle SD plot
- **TEST**: Visual inspection, verify averages match manual calculation

### Stage 2: Fragment Assignment Integration
- ✓ Load assignments from JSON database
- ✓ Match m/z to assignments (±0.0001 Da tolerance)
- ✓ Display assigned formulas as labels on plot
- ✓ Fragment table pop-out (read-only)
- **TEST**: Verify assignments match database, labels display correctly

### Stage 3: Filter 1 - Intensity Threshold
- ✓ Add intensity slider
- ✓ Filter peaks below threshold
- ✓ Update plot dynamically
- **TEST**: Verify filtering is correct, UI responsiveness

### Stage 4: Filter 2 - Top N Peaks
- ✓ Add Top N dropdown
- ✓ Sort by intensity, keep top N
- ✓ Update plot
- **TEST**: Count peaks, verify correct ranking

### Stage 5: Filter 3 - m/z Range
- ✓ Add min/max inputs
- ✓ Validation (min < max)
- ✓ Filter peaks outside range
- **TEST**: Boundary conditions, edge cases

### Stage 6: Filter 4 - PCA Loadings (Advanced)
- ✓ Check if PCA has been run
- ✓ Load PCA loadings
- ✓ Match m/z between spectrum and loadings
- ✓ Filter by |loading| threshold
- **TEST**: Verify PCA integration, loading values correct

### Stage 7: Filters 5 & 6 - Statistical & Assignment
- ✓ Implement statistical filter (mean > N×SD)
- ✓ Implement assignment filter (All/Assigned/Unassigned)
- **TEST**: Verify filtering logic, edge cases

### Stage 8: Manual Assignment Dialog
- ✓ Create dialog UI (reuse existing pattern)
- ✓ Element input system (buttons + spinners)
- ✓ Formula validation (elements, valence)
- ✓ Mass calculation and ppm check
- ✓ Polarity validation
- **TEST**: Try valid and invalid formulas, check warnings

### Stage 9: Database Write Operations
- ✓ Backup creation
- ✓ JSON read/modify/write
- ✓ Metadata updates
- ✓ Error handling (file permissions, JSON corruption)
- **TEST**: Verify backups created, JSON structure preserved, new assignments persist

### Stage 10: Polish & Integration
- ✓ Consistent styling with other tabs
- ✓ Keyboard shortcuts
- ✓ Export functionality (plot PNG/SVG, data CSV)
- ✓ Help tooltips
- ✓ Loading indicators
- **TEST**: Full workflow testing, user experience review

---

## Scientific Validation Checklist

### Data Integrity
- [ ] Raw intensities unchanged (no unintended preprocessing)
- [ ] Replicate averaging mathematically correct (mean, SD)
- [ ] TIC normalization preserved
- [ ] m/z precision maintained (4 decimals minimum)

### Chemical Validity
- [ ] Element constraints appropriate for material system
- [ ] Valence rules checked for common violations
- [ ] Mass accuracy within instrumental precision (50 ppm)
- [ ] Polarity assignments respected (no negative → positive mixing)

### Statistical Rigor
- [ ] SD calculated correctly (N=3 replicates)
- [ ] Filtering thresholds scientifically justified
- [ ] PCA loading integration mathematically sound
- [ ] No data manipulation or fake values introduced

### Visualization Standards
- [ ] Stick spectrum follows mass spec conventions
- [ ] Labels clear and non-overlapping (or handle overlap intelligently)
- [ ] Axes labeled correctly (m/z, Intensity TIC-normalized)
- [ ] Publication-quality output (300 DPI, vector formats)

---

## Edge Cases & Error Handling

1. **No replicates for selected dose**: Warn user, disable averaging
2. **Database file missing/corrupted**: Create new database from scratch, warn user
3. **Backup creation fails (permissions)**: Abort write, display error
4. **Invalid formula input**: Clear validation messages, prevent database update
5. **Duplicate assignments**: Warn user, offer to replace or append
6. **Very large number of peaks (>1000)**: Warn about performance, suggest filtering
7. **Label overlap**: Implement smart label positioning or rotation

---

## Testing Strategy

### Unit Tests
- Formula validation (valid/invalid inputs)
- Mass calculation (known formulas)
- ppm error calculation
- Database read/write operations

### Integration Tests
- Full workflow: load → filter → assign → save → reload
- Filter combinations (multiple filters active)
- PCA integration (with and without PCA run)

### User Acceptance Tests
- Real data from both polarities
- Manual assignment of 5+ fragments
- Database backup verification
- Export functionality (plots and data)

---

## Documentation Updates Required

1. **README.md**: Add stick spectrum tab to features list
2. **TECHNICAL_REFERENCE.md**: Document filtering methods
3. **CLAUDE.md**: Update with new tab implementation
4. **Code comments**: Docstrings for all new functions/classes

---

## Files to Archive/Remove

Move to `data/FragmentDatabase/archive/`:
- `NegFragmentsList.xlsx` (source used to create JSON, no longer needed)
- `PosFragmentsList.xlsx` (source used to create JSON, no longer needed)

**Justification**: JSON is single source of truth, Excel files not referenced in code.

---

## Potential Future Enhancements (NOT in initial scope)

- Multi-dose overlay (show multiple doses on same plot with color coding)
- Peak deconvolution for overlapping peaks
- Isotope pattern recognition and labeling
- Export to publication-ready figure templates
- Integration with NIST mass spec database
- Machine learning-assisted assignment suggestions

---

## Confirmed Design Decisions

1. **Formula input UX**: ✓ Element buttons + spinners (foolproof, structured)
2. **Label positioning**: ✓ Auto-position with smart algorithm to avoid overlap
3. **Color scheme**: ✓ Match PCA tab (viridis for consistency)
4. **SD plot**: ✓ Stacked subplot (below main spectrum)
5. **Code architecture**: ✓ Modular - reuse existing methods, no duplication

---

**END OF PLANNING DOCUMENT**
**Next step**: Review plan, address questions, create feature branch, implement Stage 1
