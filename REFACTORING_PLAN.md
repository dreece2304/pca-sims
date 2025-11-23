# PCA-SIMS Refactoring Plan
**Branch**: `refactor/codebase-optimization`
**Started**: November 23, 2025
**Status**: Phase 2 Complete

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

## 🚧 REMAINING PHASES (To Continue Later)

### Phase 3: Create MVC Foundation
**Duration**: 5-7 days | **Risk**: MEDIUM
**Status**: NOT STARTED

#### Goals
Establish new architecture WITHOUT breaking existing GUI

#### Strategy
Create new directory structure alongside existing code. Old GUI continues working.

#### Directory Structure to Create
```
src/
├── [EXISTING FILES - KEEP UNCHANGED DURING PHASE 3]
├── pyside_app_matplotlib.py          # Keep working
├── simple_tof_sims_pca.py            # Keep until migrated
│
├── [NEW ARCHITECTURE]
├── models/                # Data models (no Qt, no UI)
│   ├── pca_model.py              # PCA state & results
│   ├── sample_model.py           # Sample metadata
│   ├── fragment_model.py         # Fragment assignments
│   └── spectrum_model.py         # Mass spectrum data
│
├── services/              # Shared business logic
│   ├── data_loader.py            # Unified Excel + txt loading
│   ├── pca_service.py            # PCA orchestration
│   ├── fragment_service.py       # Database operations
│   ├── export_service.py         # Export functionality
│   └── validation_service.py     # Data validation
│
├── core/                  # Domain logic
│   ├── pca_engine.py             # Pure PCA math
│   ├── fragment_classifier.py    # [MOVE EXISTING]
│   ├── crosslinking_metrics.py   # [MOVE EXISTING]
│   └── fragment_mass_calculator.py # [MOVE EXISTING]
│
└── widgets/               # Reusable UI components
    ├── plotting/
    │   ├── base_canvas.py
    │   ├── pca_canvas.py
    │   ├── spectrum_canvas.py
    │   └── fragment_canvas.py
    └── dialogs/
        ├── data_preview_dialog.py
        ├── fragment_assignment_dialog.py
        ├── custom_dose_dialog.py
        └── manual_assignment_dialog.py
```

#### Tasks
1. Create model classes (pure Python, no Qt)
2. Create service layer
3. Extract core PCA engine
4. Extract plotting base class
5. Write unit tests for models and services

#### Deliverables
- ~15 new Python modules
- Unit test suite (tests/test_models/, tests/test_services/)
- Architecture documentation (docs/ARCHITECTURE.md)
- Old GUI still functional

**Approval Gate**: Test new components, verify old GUI unchanged

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

| Metric | Before | After (Target) | Status |
|--------|--------|----------------|--------|
| **Largest file** | 7000 lines | ~800 lines | 🚧 In Progress |
| **Unused files** | ~30 files | 0 files | ✅ Complete |
| **Excel import** | CLI only | GUI + CLI | ✅ Complete |
| **Duplicate handling** | Averaging | Deduplication | ✅ Fixed |
| **Test coverage** | ~5% | 80%+ | 🚧 Planned |
| **Modularity** | 5/10 | 9/10 | 🚧 Phases 3-8 |

---

## How to Continue

### Starting Point
```bash
cd /home/dreece23/pca-sims
git checkout refactor/codebase-optimization
git pull origin refactor/codebase-optimization  # If pushed
```

### Current State
- ✅ Phase 1 & 2 complete
- ✅ GUI works correctly
- ✅ Excel import functional
- ✅ Critical bugs fixed
- 🚧 Ready for Phase 3

### Next Steps
1. Review Phase 3 plan above
2. Create model classes (`src/models/`)
3. Create service layer (`src/services/`)
4. Write unit tests as you go
5. Keep old GUI working in parallel

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

# Current commits:
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
4. Review Phase 3 plan before starting
5. Ask questions about architecture decisions

**Last Updated**: November 23, 2025
**Branch**: `refactor/codebase-optimization`
**Status**: Phases 1-2 Complete, Ready for Phase 3
