# ToF-SIMS PCA Application Test Suite

## Overview

Comprehensive test suite for the ToF-SIMS PCA application covering unit tests, integration tests, and workflows.

## Test Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_fragment_service.py  # FragmentService tests (20+ tests)
│   └── test_models.py             # Model tests (15+ tests)
├── integration/                   # Integration tests for workflows
│   └── test_fragment_workflow.py  # Complete workflow tests (7+ tests)
└── README.md                      # This file
```

## Running Tests

### Prerequisites

Ensure you're in the conda environment:

```bash
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims
```

Install pytest if not already installed:

```bash
conda install pytest
```

### Run All Tests

```bash
cd /home/dreece23/pca-sims
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_fragment_service.py

# Specific test class
pytest tests/unit/test_fragment_service.py::TestFragmentService

# Specific test method
pytest tests/unit/test_fragment_service.py::TestFragmentService::test_load_database_success
```

### Run with Output

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Both
pytest -v -s
```

### Run with Coverage (if pytest-cov installed)

```bash
pytest --cov=src --cov-report=html
```

## Test Coverage

### Unit Tests (tests/unit/)

#### FragmentService Tests (`test_fragment_service.py`)
- ✅ Service initialization
- ✅ Database loading (success and failure cases)
- ✅ Mass indexing structure
- ✅ Fragment candidate search (exact match, tolerance, polarity filtering)
- ✅ Candidate sorting by PPM error
- ✅ Fragment retrieval and filtering
- ✅ Metadata access
- ✅ Manual assignment saving
- ✅ Backup file creation
- ✅ PPM calculation accuracy

**Coverage**: 20+ test cases covering all FragmentService methods

#### Model Tests (`test_models.py`)
- ✅ Sample model creation and validation
- ✅ Polarity enum values
- ✅ Fragment model creation with all parameters
- ✅ AssignmentConfidence levels
- ✅ FragmentAssignment creation (assigned and unassigned)
- ✅ PCAResults creation and DataFrame conversion
- ✅ MassSpectrum creation with assignments
- ✅ Model validation edge cases
- ✅ Array shape consistency

**Coverage**: 15+ test cases covering all model types

### Integration Tests (tests/integration/)

#### Fragment Workflow Tests (`test_fragment_workflow.py`)
- ✅ Loading real database
- ✅ Searching for known fragments
- ✅ Complete assignment workflow (load → search → assign → save)
- ✅ Polarity filtering across workflow
- ✅ Metadata consistency checking
- ✅ Backup creation verification

**Coverage**: 7 comprehensive workflow tests

## Test Data

### Unit Tests
- Use temporary databases created in fixtures
- Minimal test data (3 fragments) for fast execution
- No dependencies on external files

### Integration Tests
- Use real fragment database when available
- Create temporary copies for destructive testing
- Skip tests if database not found (graceful degradation)

## Writing New Tests

### Unit Test Template

```python
import pytest
import sys
sys.path.append('src')

from services import YourService


class TestYourService:
    """Test suite for YourService"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return YourService()

    def test_basic_functionality(self, service):
        """Test basic service functionality"""
        result = service.do_something()
        assert result is not None
```

### Integration Test Template

```python
import pytest
from pathlib import Path
import sys
sys.path.append('src')


class TestWorkflow:
    """Integration tests for complete workflow"""

    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        # Create test data
        yield data
        # Cleanup

    def test_complete_workflow(self, setup_data):
        """Test complete workflow from start to finish"""
        # Step 1
        # Step 2
        # Assert final state
        pass
```

## Test Markers

Tests can be marked for categorization:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_integration_workflow():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

Run specific markers:

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=xml --cov-report=term

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Maintenance

### Adding New Tests
1. Create test file following naming convention (`test_*.py`)
2. Use fixtures for setup/teardown
3. Test both success and failure cases
4. Include docstrings explaining what is being tested
5. Run tests locally before committing

### Updating Tests
- Update tests when refactoring code
- Keep test data minimal and focused
- Use parameterized tests for similar test cases
- Maintain test independence (no shared state)

## Known Limitations

1. GUI tests not yet implemented (requires Qt test framework)
2. Performance benchmarks not included
3. Some edge cases may not be covered

## Future Test Enhancements

- [ ] Add GUI tests using PyTest-Qt
- [ ] Add performance/benchmark tests
- [ ] Increase coverage to 80%+
- [ ] Add regression tests for PCA computations
- [ ] Add property-based testing with Hypothesis

## Troubleshooting

### Import Errors
If you get import errors, ensure:
- You're in the correct conda environment
- `src/` is in the Python path (tests add it automatically)
- All dependencies are installed

### Database Not Found
Integration tests will skip if database not found:
```
SKIPPED [1] test_fragment_workflow.py:20: Fragment database not found
```

This is expected behavior and not a failure.

### Fixture Errors
If fixtures fail:
- Check temp directory permissions
- Ensure sufficient disk space
- Verify database file is valid JSON

## Contact

For test-related questions or issues, refer to:
- `docs/ARCHITECTURE.md` - Architecture documentation
- `REFACTORING_PLAN.md` - Refactoring progress
- `CLAUDE.md` - Development environment setup
