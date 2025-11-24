# ToF-SIMS PCA Application Architecture

**Last Updated**: November 23, 2025
**Refactoring Phase**: Phases 1-7.1 Complete

---

## Overview

The ToF-SIMS PCA application has been refactored from a monolithic 7,093-line GUI file into a modular MVC (Model-View-Controller) architecture with separate services, models, and UI components.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PySide6 Qt Application                   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Main GUI (pyside_app_matplotlib.py)          │  │
│  │                    5,848 lines                        │  │
│  └─────────────┬───────────────────────────┬─────────────┘  │
│                │                           │                 │
│    ┌───────────▼─────────┐    ┌───────────▼──────────┐     │
│    │   Widgets/Tabs      │    │   Dialogs            │     │
│    │  - SummaryTab       │    │  - DataPreview       │     │
│    │  - MainResultsTab   │    │  - FragmentAssign    │     │
│    │  - Plotting         │    │  - CustomDose        │     │
│    └───────────┬─────────┘    │  - ManualAssignment  │     │
│                │              └───────────┬──────────┘     │
│                │                          │                 │
│    ┌───────────▼──────────────────────────▼─────────┐     │
│    │              Services Layer                      │     │
│    │  ┌──────────────────────────────────────────┐   │     │
│    │  │  FragmentService (280 lines)             │   │     │
│    │  │  - load_database()                        │   │     │
│    │  │  - find_candidates()                      │   │     │
│    │  │  - save_manual_assignment()               │   │     │
│    │  │  - get_all_fragments()                    │   │     │
│    │  └──────────────────────────────────────────┘   │     │
│    └───────────┬──────────────────────────────────────┘     │
│                │                                             │
│    ┌───────────▼──────────────────────────────────────┐     │
│    │              Models Layer                          │     │
│    │  ┌────────────────┐  ┌────────────────┐          │     │
│    │  │  PCAModel      │  │  SampleModel   │          │     │
│    │  │  (182 lines)   │  │  (216 lines)   │          │     │
│    │  └────────────────┘  └────────────────┘          │     │
│    │  ┌────────────────┐  ┌────────────────┐          │     │
│    │  │ FragmentModel  │  │ SpectrumModel  │          │     │
│    │  │  (211 lines)   │  │  (216 lines)   │          │     │
│    │  └────────────────┘  └────────────────┘          │     │
│    └──────────────────────────────────────────────────┘     │
│                                                              │
│    ┌──────────────────────────────────────────────────┐     │
│    │              Core Domain Logic                    │     │
│    │  - fragment_classifier.py                         │     │
│    │  - crosslinking_metrics.py                        │     │
│    │  - fragment_mass_calculator.py                    │     │
│    └──────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
src/
├── models/                      # Data models (no Qt dependencies)
│   ├── __init__.py
│   ├── pca_model.py            # PCA results container
│   ├── sample_model.py         # Sample metadata with Polarity enum
│   ├── fragment_model.py       # Fragment ions and assignments
│   └── spectrum_model.py       # Mass spectrum data structures
│
├── services/                    # Business logic layer
│   ├── __init__.py
│   └── fragment_service.py     # Fragment database operations
│
├── widgets/                     # Reusable UI components
│   ├── __init__.py
│   ├── common.py               # NumericTableWidgetItem
│   ├── fragment_analysis_tab.py  # Fragment analysis UI
│   │
│   ├── tabs/                   # Tab widgets
│   │   ├── __init__.py
│   │   ├── summary_tab.py      # Summary statistics display
│   │   └── main_results_tab.py # PCA plot canvas wrapper
│   │
│   ├── dialogs/                # Dialog windows
│   │   ├── __init__.py
│   │   ├── data_preview_dialog.py
│   │   ├── fragment_assignment_dialog.py
│   │   ├── custom_dose_dialog.py
│   │   └── manual_assignment_dialog.py
│   │
│   └── plotting/               # Plot canvases
│       ├── __init__.py
│       ├── matplotlib_plotting.py
│       ├── stick_spectrum_plotting.py
│       └── fragment_group_plotting.py
│
├── core/                        # Domain logic
│   ├── __init__.py
│   ├── fragment_classifier.py
│   ├── crosslinking_metrics.py
│   └── fragment_mass_calculator.py
│
├── pyside_app_matplotlib.py     # Main GUI application (5,848 lines)
├── simple_tof_sims_pca.py      # PCA analysis engine
├── tofsims_excel_processor.py  # Excel import processor
└── multi_ion_manager.py        # Multi-polarity data manager
```

---

## Layer Responsibilities

### 1. Models Layer (`src/models/`)

**Purpose**: Pure Python data structures with no UI dependencies

**Characteristics:**
- Python `dataclasses` with type hints
- No Qt imports
- Immutable where possible
- Validation in `__post_init__`
- Can be easily tested and serialized

**Key Models:**
- **PCAModel**: PCA results, scores, loadings, variance
- **SampleModel**: Sample metadata, dose, polarity, groups
- **FragmentModel**: Fragment ions, assignments, confidence levels
- **SpectrumModel**: Mass spectrum data with assignments

### 2. Services Layer (`src/services/`)

**Purpose**: Business logic and data operations

**Characteristics:**
- Stateful service objects
- Caching and optimization
- No direct UI interaction
- Testable independently
- Returns data, not UI elements

**Key Services:**
- **FragmentService** (280 lines):
  - Database loading and caching
  - Fast mass-based indexing (O(1) lookups)
  - PPM tolerance-based fragment matching
  - Automatic backup management
  - Polarity filtering

### 3. Widgets Layer (`src/widgets/`)

**Purpose**: Reusable UI components

**Sub-packages:**
- **tabs/**: Tab widget implementations
- **dialogs/**: Modal dialog windows
- **plotting/**: Matplotlib canvas wrappers

**Design Principles:**
- Self-contained UI components
- Minimal coupling to main application
- Signal-based communication
- Reusable across different contexts

### 4. Core Layer (`src/core/`)

**Purpose**: Domain-specific algorithms and logic

**Components:**
- Fragment classification logic
- Crosslinking metrics calculations
- Mass calculation from chemical formulas

### 5. Main GUI (`pyside_app_matplotlib.py`)

**Purpose**: Application orchestration and top-level UI

**Responsibilities:**
- Window management
- Menu bar and actions
- Tab coordination
- Service initialization
- Event handling and routing

**Size Progression:**
- Before refactoring: 7,093 lines
- Current: 5,848 lines
- Reduction: 17.6%

---

## Key Design Patterns

### 1. Service Layer Pattern

Services encapsulate business logic and provide clean APIs:

```python
from services import FragmentService

# Initialize service
fragment_service = FragmentService()

# Load database
fragment_service.load_database()

# Find matching fragments
candidates = fragment_service.find_candidates(
    mz_value=65.0031,
    polarity='negative',
    ppm_tolerance=50.0
)
```

### 2. Model-View Separation

Models are pure data with no UI knowledge:

```python
from models import Sample, Polarity

# Create sample (no Qt dependencies)
sample = Sample(
    name="SQ2_Rep1",
    dose=2.0,
    replicate=1,
    polarity=Polarity.NEGATIVE,
    group="SQ2"
)
```

### 3. Widget Composition

Tabs and dialogs are self-contained components:

```python
from widgets.tabs import SummaryTab

# Create and use tab widget
summary_tab = SummaryTab()
summary_tab.update_summary(summary_text)
```

---

## Data Flow

### Fragment Assignment Flow

```
User Action (GUI)
    │
    ▼
ManualAssignmentDialog
    │
    ▼
FragmentService.save_manual_assignment()
    │
    ├─► Create backup (JSON)
    ├─► Update database
    ├─► Rebuild index
    │
    ▼
FragmentService.load_database()
    │
    ▼
GUI receives updated data
```

### PCA Analysis Flow

```
Load Data File
    │
    ▼
SimpleToFSIMSPCA.load_data()
    │
    ▼
User selects samples/options
    │
    ▼
PCAWorker (QThread)
    │
    ├─► Preprocess data
    ├─► Compute PCA
    ├─► Calculate variance
    │
    ▼
Update GUI with results
    │
    ├─► MainResultsTab (plot canvas)
    ├─► SummaryTab (text stats)
    └─► Fragment Assignment tab
```

---

## Testing Strategy

### Unit Tests (Models & Services)

Models and services are designed for easy testing:

```python
# Test FragmentService
def test_fragment_service():
    service = FragmentService()
    service.load_database()

    candidates = service.find_candidates(65.0031, 'negative')
    assert len(candidates) > 0
    assert candidates[0]['ppm_error'] < 50
```

### Integration Tests

Test service integration with data:

```python
# Test fragment assignment workflow
def test_assignment_workflow():
    service = FragmentService()
    service.load_database()

    assignment_data = {
        'assignment': 'C₄HO⁻',
        'formula': 'C4HO',
        'calculated_mass': 65.0033,
        'error_ppm': 3.0,
        'chemical_family': 'Unsaturated_carbon',
        'confidence': 'High'
    }

    success, msg = service.save_manual_assignment(
        65.0031, assignment_data, 'negative'
    )
    assert success
```

---

## Performance Considerations

### Fragment Database Indexing

The FragmentService uses integer mass buckets for fast lookups:

```python
# O(1) lookup by mass bucket instead of O(n) linear search
mass_key = int(mz_value)  # e.g., 65.0031 → 65
candidates = fragment_mass_index[mass_key]  # Fast bucket access
```

### Caching Strategy

- Fragment database loaded once and cached
- Mass index built once at load time
- No repeated file I/O during analysis

---

## Future Improvements

### Additional Services to Extract

1. **DataLoaderService**: Centralize data loading logic
2. **ExportService**: Handle all export operations
3. **PCAService**: Wrap PCA computation and caching
4. **ValidationService**: Data validation utilities

### Complex Tab Extraction

Remaining tabs to extract (requires additional services):
- Fragment Assignment Tab (68 lines UI + 400 lines methods)
- Database Management Tab (166 lines UI + 300 lines methods)
- Stick Spectrum Tab (235 lines UI + 800 lines methods)

### Testing

- Increase unit test coverage to 80%+
- Add integration tests for workflows
- GUI regression tests
- Performance benchmarks

---

## Migration Guide

### Adding a New Service

1. Create service file in `src/services/`
2. Define service class with clear responsibilities
3. Add type hints for all methods
4. Update `src/services/__init__.py`
5. Integrate into main GUI
6. Write unit tests

### Adding a New Model

1. Create model file in `src/models/`
2. Use `@dataclass` decorator
3. Add type hints for all fields
4. No Qt dependencies
5. Update `src/models/__init__.py`
6. Write validation tests

### Extracting a Tab

1. Create tab file in `src/widgets/tabs/`
2. Inherit from `QWidget`
3. Move UI setup to `setup_ui()`
4. Use signals for communication
5. Update `src/widgets/tabs/__init__.py`
6. Replace inline code in main GUI
7. Test thoroughly

---

## Code Quality Standards

### Type Hints

All new code should include type hints:

```python
def find_candidates(self, mz_value: float, polarity: str,
                   ppm_tolerance: Optional[float] = None) -> List[Dict]:
    """Find fragment candidates for observed m/z value."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def save_manual_assignment(self, mz_value: float,
                          assignment_data: Dict[str, Any],
                          polarity: str) -> Tuple[bool, str]:
    """Save a manual fragment assignment to the database.

    Args:
        mz_value: Observed m/z value
        assignment_data: Dict with assignment, formula, confidence, etc.
        polarity: 'positive' or 'negative'

    Returns:
        Tuple[bool, str]: (success, message)
    """
    ...
```

### Import Organization

1. Standard library
2. Third-party packages
3. Local imports

```python
import json
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import QWidget

from models import Fragment
from services import FragmentService
```

---

## References

- **REFACTORING_PLAN.md**: Detailed refactoring progress
- **CLAUDE.md**: Development environment setup
- **README.md**: Project overview and usage
