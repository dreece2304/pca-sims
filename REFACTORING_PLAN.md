# PCA-SIMS Refactoring Plan
**Branch**: `refactor/codebase-optimization`
**Started**: November 23, 2025
**Status**: Phase 5 Complete - Ready for Phase 6

---

## Goal
Transform monolithic 7000-line GUI application into modular, maintainable MVC architecture while adding Excel import functionality.

---

## ✅ COMPLETED PHASES

### Phase 1: Codebase Cleanup (COMPLETE)
**Commit**: `9cb5038` - Phase 1: Codebase cleanup and reorganization
**Duration**: ~4 hours

**Accomplishments:**
- ❌ Deleted 28 unused files (~3500 lines)
  - `src/multi_ion_manager.py` (later restored as stub)
  - `test_loadings_source.py`
  - `scripts/analysis/` directory (26 investigation scripts)
- 📁 Reorganized scripts:
  - Created `scripts/production/` (13 active scripts)
  - Maintained `scripts/utilities/` and `scripts/archive/`
- 🛠️ Consolidated database tools:
  - Created `scripts/utilities/manage_fragment_database.py`
  - Unified validate/cleanup/backup/stats subcommands
  - Replaced 3 separate cleanup scripts
- 🔧 GUI cleanup:
  - Removed broken "Load Default Data" button
  - Removed non-existent file reference

**Files Changed**: 47 files, +1081/-5609 lines

---

### Phase 2: Excel Import Integration (COMPLETE)
**Commits**:
- `a307d5a` - Phase 2: Excel import integration with critical bug fix
- `fc8230a` - Phase 2 Fix: Restore multi_ion_manager with minimal stub

**Duration**: ~5 hours

**Accomplishments:**

#### Excel Import Feature ✅
- Added "Import Excel" button to GUI data loading section
- Direct Excel import workflow (no more CLI preprocessing)
- Interactive polarity selection dialog
- Automatic fragment database updates
- Processing summary dialog with statistics
- Creates temp .txt file and loads through existing pipeline

#### Critical Bug Fix 🐛
**Problem**: Duplicate m/z handling was averaging intensities
- Multiple fragment candidates for same measured peak (e.g., CH₃⁺ and NH⁺ both at m/z 15.0235)
- Intensities are IDENTICAL for duplicates (same measured peak)
- Old code was averaging them (conceptually wrong)

**Solution**: Simple deduplication
- Changed from `mean()` to `drop_duplicates(keep='first')`
- Intensities remain completely unchanged
- Only unique m/z values kept for PCA

#### Fragment Database Handling (Verified Correct) ✅
- Uses exact calculated m/z from chemical formulas
- Accounts for charge (+/- electrons)
- NOT storing measured m/z (experimental error)
- `fragment_mass_calculator.py` handles formula → exact mass

#### Multi-Ion Manager Fix 🔧
- Restored `multi_ion_manager.py` as minimal stub
- Required by GUI (26+ references)
- Removed complex dual-polarity loading (incomplete)
- Simple polarity tracking sufficient

**Testing Results:**
- ✅ Tested with `AllPosNewwithFragment.xlsx` (115 rows → 103 unique m/z)
- ✅ 12 duplicate m/z correctly removed
- ✅ Intensities verified unchanged (no averaging)
- ✅ Fragment database uses exact calculated masses
- ✅ GUI launches and runs PCA successfully

**Files Changed**: 6 files, +746/-12 lines

---

### Phase 3: Create MVC Foundation (COMPLETE)
**Commits**:
- `d2ebdb0` - Add comprehensive refactoring plan documentation
- `5b8e1a3` - Phase 3.1: Create MVC foundation structure
- `5f7c8d2` - Phase 3.2: Remove unused batch processing code
- `8c9f3e4` - Phase 3.3: Implement model layer

**Duration**: ~6 hours

**Accomplishments:**

#### 3.1: MVC Foundation Structure ✅
- Created directory structure:
  - `src/models/` - Data models (no Qt dependencies)
  - `src/services/` - Business logic layer
  - `src/core/` - Domain logic
  - `src/widgets/` - Reusable UI components
  - `src/widgets/dialogs/` - Dialog windows
  - `src/widgets/plotting/` - Plot canvases

#### 3.2: Removed Unused Batch Processing ✅
- Deleted `tofsims/` package (~2,000 lines)
- Removed 13 batch processing scripts from `scripts/production/` (~3,000 lines)
- Total reduction: ~5,000 lines of unused code

#### 3.3: Model Layer Implementation ✅
Created 4 model modules (~830 lines):
- `models/pca_model.py` - PCA results container with DataFrame conversion
- `models/sample_model.py` - Sample metadata with Polarity enum
- `models/fragment_model.py` - Fragment ions and assignments
- `models/spectrum_model.py` - Mass spectrum data structures

**Key Design Decisions:**
- Models are pure Python dataclasses (no Qt dependencies)
- Used Enum for Polarity instead of strings
- Validation in dataclass __post_init__ methods
- Proper type hints throughout

**Files Changed**: 12 files, +830/-5000 lines

---

### Phase 4: Widget Reorganization (COMPLETE)
**Commit**: `e1f4a7b` - Phase 4: Widget reorganization and package structure

**Duration**: ~2 hours

**Accomplishments:**
- Moved existing files into widget package structure:
  - `matplotlib_plotting.py` → `widgets/plotting/`
  - `stick_spectrum_plotting.py` → `widgets/plotting/`
  - `fragment_group_plotting.py` → `widgets/plotting/`
  - `fragment_analysis_tab.py` → `widgets/`
- Created `NumericTableWidgetItem` in `widgets/common.py`
- Updated all imports in main GUI and dependent files
- Created proper `__init__.py` files with explicit exports

**Files Changed**: 8 files, +45/-12 lines

---

### Phase 5: Extract Dialog Classes (COMPLETE)
**Commit**: `a74a6e9` - Phase 5: Extract dialog classes from main GUI

**Duration**: ~3 hours

**Accomplishments:**
- Extracted 3 large dialog classes from main GUI (1,095 lines):
  - `FragmentAssignmentDialog` (500 lines) - Detailed fragment assignment with plotting
  - `CustomDoseDialog` (201 lines) - Sample metadata configuration
  - `ManualAssignmentDialog` (384 lines) - Element composition calculator
- Created `src/widgets/dialogs/` package with proper exports
- Removed duplicate Polarity class (now using `models.Polarity`)
- Removed duplicate NumericTableWidgetItem (now using `widgets.common`)
- Updated main GUI imports

**Main GUI Reduction:**
- Before: 7,093 lines
- After: 5,998 lines
- Reduction: 1,095 lines (15.4%)

**Testing:** All dialogs tested and functional

**Files Changed**: 7 files, +1095/-1095 lines (net reorganization)

---

## 🚧 REMAINING PHASES

### Phase 6: Tab Extraction from Main GUI (IN PROGRESS)
**Duration**: 7-10 days | **Risk**: MEDIUM-HIGH
**Status**: Phase 6.1 Complete - Partial Implementation

#### Goals
Extract tab implementations from main GUI into separate view modules

#### Strategy (Revised)
Extract simple, self-contained tabs first. Complex tabs with many dependencies will be addressed in Phase 7 (Service Layer) to avoid breaking application.

#### Phase 6.1: Simple Tabs (COMPLETE)
**Commit**: `bc49bd0` - Phase 6.1: Extract simple tab widgets

**Accomplishments:**
- Created `src/widgets/tabs/` package structure
- Extracted **Summary Tab** to `SummaryTab` widget (36 lines)
  - Simple text display widget
  - No external dependencies
- Extracted **Main Results Tab** to `MainResultsTab` widget (38 lines)
  - Wraps PCA plot canvas
  - Minimal dependencies
- Updated main GUI to use new tab widgets
- Maintained backward compatibility

**Main GUI Reduction:**
- Before: 5,998 lines
- After: 5,986 lines
- Reduction: 12 lines

**Testing:** GUI launches successfully, tabs function correctly

#### Phase 6.2: Complex Tabs Analysis

**Complex Tabs Identified:**
1. **Fragment Assignment Tab** (68 lines UI + ~400 lines methods)
   - Depends on: `refresh_assignment_table`, `add_manual_assignment`, `save_assignments_database`, `export_assignment_table`
   - Requires fragment database service layer

2. **Database Management Tab** (166 lines UI + ~300 lines methods)
   - Heavy database operations
   - Requires fragment service layer

3. **Stick Spectrum Tab** (235 lines UI + ~800 lines methods)
   - Most complex tab with extensive filtering logic
   - Depends on: dose selection, filters, plotting, export
   - Requires spectrum service layer

**Decision:** Defer complex tab extraction to Phase 7 after creating service layer. This allows:
- Proper separation of business logic from UI
- Avoid breaking tightly-coupled code
- Create testable service layer first
- Then extract tabs with clean service dependencies

#### Next Steps
Skip to Phase 7: Create Service Layer to decouple business logic, then return to complete tab extraction

---

### Phase 4: Extract Dialogs & Widgets
**Duration**: 4-5 days | **Risk**: LOW-MEDIUM
**Status**: NOT STARTED

#### Goals
Move reusable components out of monolithic GUI

#### Tasks
1. Extract dialog classes
2. Refactor plotting canvases
3. Move fragment analysis tab
4. Update main GUI imports

#### Expected Results
- ~8 files extracted (~2500 lines)
- `pyside_app_matplotlib.py` reduced from 7000 → ~4500 lines

---

### Phase 5: Tab Refactoring Decision Point
**Duration**: 1-2 days | **Risk**: PLANNING
**Status**: NOT STARTED

#### Goals
Review current tabs and decide final structure

#### Current Tabs
1. Main Results - PCA plots
2. Summary - Text variance stats
3. Fragment Assignment - Manual curation
4. Stick Spectrum - Dose-level spectra
5. Database Management - Expert admin
6. Fragment Analysis - Chemical classification

#### Questions to Discuss
- Keep all 6 tabs separate?
- Combine Summary into Main Results?
- Move Database Management to menu?

---

### Phase 6: Create View Layer (Tab Extraction)
**Duration**: 7-10 days | **Risk**: MEDIUM-HIGH
**Status**: NOT STARTED

#### Strategy
Extract one tab at a time, test after each

#### Extraction Order
1. Summary Tab (simplest)
2. Main Results Tab
3. Stick Spectrum Tab
4. Fragment Assignment Tab
5. Database Management Tab
6. Fragment Analysis Tab (already separate)

#### Per-Tab Process
1. Create new view module
2. Extract UI setup code
3. Extract signal connections
4. Create stub controller
5. Update main window
6. Test thoroughly
7. Commit
8. Checkpoint review

---

### Phase 7: Create Controller Layer
**Duration**: 5-7 days | **Risk**: MEDIUM
**Status**: NOT STARTED

#### Goals
Separate business logic from UI

#### Controllers to Create
- DataController - File loading orchestration
- PCAController - Computation orchestration
- SpectrumController - Dose selection & filtering
- FragmentController - Database CRUD operations
- ExportController - Export operations

---

### Phase 8: Migration & Cleanup
**Duration**: 3-4 days | **Risk**: LOW
**Status**: NOT STARTED

#### Tasks
1. Update launch script
2. Delete old monolithic files
3. Update documentation
4. Code quality pass (type hints, docstrings, formatting)

---

### Phase 9: Testing & Validation
**Duration**: 5-7 days | **Risk**: LOW
**Status**: NOT STARTED

#### Goals
Comprehensive testing for no regressions

#### Test Coverage
- Unit tests (80%+ target)
- Integration tests
- GUI tests (Qt framework)
- Regression tests (compare PCA results old vs new)
- Performance benchmarks

---

### Phase 10: Optimization & Polish
**Duration**: 3-5 days | **Risk**: LOW
**Status**: NOT STARTED

#### Goals
Final improvements

#### Tasks
- Performance optimization
- User experience improvements
- Configuration management
- Enhanced error handling

---

## Summary: Before vs After

| Metric | Before | Current | Target | Status |
|--------|--------|---------|--------|--------|
| **Largest file** | 7,093 lines | 5,986 lines | ~800 lines | 🚧 In Progress (16% reduction) |
| **Unused files** | ~30 files | 0 files | 0 files | ✅ Complete |
| **Excel import** | CLI only | GUI + CLI | GUI + CLI | ✅ Complete |
| **Duplicate handling** | Averaging | Deduplication | Deduplication | ✅ Fixed |
| **Code organization** | Monolithic | MVC structure | MVC structure | 🚧 70% Complete |
| **Test coverage** | ~5% | ~5% | 80%+ | 🚧 Planned (Phase 9) |
| **Modularity** | 5/10 | 7/10 | 9/10 | 🚧 Phases 6-8 |

---

## How to Continue

### Starting Point
```bash
cd /home/dreece23/pca-sims
git checkout refactor/codebase-optimization
git pull origin refactor/codebase-optimization  # If pushed
```

### Current State
- ✅ Phases 1-2 complete (Cleanup + Excel import)
- ✅ Phase 3 complete (MVC foundation + models)
- ✅ Phase 4 complete (Widget reorganization)
- ✅ Phase 5 complete (Dialog extraction)
- ✅ Phase 6.1 complete (Simple tab extraction)
- ✅ GUI works correctly
- 🚧 Ready for Phase 7 (Service Layer)

### Next Steps
1. **Phase 7**: Create service layer to decouple business logic from UI
2. Extract fragment database operations to `FragmentService`
3. Extract data loading to `DataLoaderService`
4. Extract export operations to `ExportService`
5. Return to Phase 6 to complete complex tab extraction with clean service dependencies

### Key Principles
- **Incremental**: One phase at a time
- **Tested**: Test after each change
- **Reversible**: Commit after each phase
- **Approval gates**: Review before proceeding
- **Parallel**: Keep old code until new code proven

---

## Git History

```bash
# View commits
git log --oneline refactor/codebase-optimization

# Recent commits:
bc49bd0 Phase 6.1: Extract simple tab widgets (Summary, Main Results)
a74a6e9 Phase 5: Extract dialog classes from main GUI
[Phase 4 commits - widget reorganization]
[Phase 3 commits - MVC foundation and models]
fc8230a Phase 2 Fix: Restore multi_ion_manager with minimal stub
a307d5a Phase 2: Excel import integration with critical bug fix
9cb5038 Phase 1: Codebase cleanup and reorganization
```

---

## Testing Commands

### Launch GUI
```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims
python launch_optimized.py
```

### Test Excel Import
1. Click "Import Excel" button
2. Select `data/PositiveIon/AllPosNewwithFragment.xlsx`
3. Choose polarity (Positive Ion)
4. Review import summary
5. Click OK to load
6. Verify PCA runs

### Run Database Management Tool
```bash
python scripts/utilities/manage_fragment_database.py validate
python scripts/utilities/manage_fragment_database.py stats
```

---

## Important Notes

### Fragment Database
- Uses **exact calculated m/z** from formulas (not measured values)
- Charge properly accounted for in mass calculations
- 50 ppm tolerance for fragment assignment
- Database location: `data/FragmentDatabase/alucone_fragments_complete.json`

### Duplicate m/z Handling
- Multiple fragment candidates for same measured peak
- Intensities are IDENTICAL for true duplicates
- **Do not average** - just remove duplicate rows
- Keep first occurrence only

### Multi-Ion Manager
- Current version is minimal stub
- Complex dual-polarity loading removed
- Can be re-implemented in future phases if needed
- Sufficient for single polarity workflows

---

## Contact / Questions

When resuming this work:
1. Read this document fully
2. Check git log for any new commits
3. Test GUI to verify current state
4. Review Phase 7 plan (Service Layer) before continuing
5. Complex tab extraction deferred until service layer complete

**Last Updated**: November 23, 2025
**Branch**: `refactor/codebase-optimization`
**Status**: Phases 1-6.1 Complete, Ready for Phase 7 (Service Layer)
