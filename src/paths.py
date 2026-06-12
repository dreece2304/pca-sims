"""
Project Paths Configuration

Centralized path management for the ToF-SIMS PCA application.
All paths are dynamically determined based on the project location.
"""

from pathlib import Path

# Project root is the parent of the src directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
POSITIVE_ION_DIR = DATA_DIR / "PositiveIon"
NEGATIVE_ION_DIR = DATA_DIR / "NegativeIon"
FRAGMENT_DATABASE_DIR = DATA_DIR / "FragmentDatabase"
PROJECT_ASSIGNMENTS_DIR = DATA_DIR / "project_assignments"

# Fragment database file
FRAGMENT_DATABASE_PATH = FRAGMENT_DATABASE_DIR / "alucone_fragments_complete.json"

# Output directories
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Ensure output directories exist
OUTPUTS_DIR.mkdir(exist_ok=True)


def get_default_data_path() -> Path:
    """Get the default data directory path"""
    return DATA_DIR


def get_default_output_path() -> Path:
    """Get the default output directory path"""
    return OUTPUTS_DIR


def get_fragment_database_path() -> Path:
    """Get the fragment database path"""
    return FRAGMENT_DATABASE_PATH


def get_backup_path(filename: str) -> Path:
    """Get a backup path in the FragmentDatabase/backups directory"""
    backup_dir = FRAGMENT_DATABASE_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir / filename
