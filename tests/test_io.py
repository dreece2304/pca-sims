"""
Smoke tests for ToF-SIMS IO layer.

Tests basic functionality:
- Config loading
- Run scanning
- Excel file loading (scores, loadings, variance)
- Assignment loading
- Required columns present
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import tofsims.io as io
import tofsims.preprocess as preprocess


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_config_load():
    """Test configuration file loading."""
    print("\n" + "=" * 60)
    print("TEST: Config Loading")
    print("=" * 60)

    cfg = io.load_config("config/tofsims.yaml")

    assert cfg is not None, "Config should not be None"
    assert 'sheets' in cfg, "Config should have 'sheets' section"
    assert 'analyses' in cfg, "Config should have 'analyses' section"

    print("✓ Config loaded successfully")
    print(f"  Analysis types: {list(cfg['analyses'].keys())}")
    print(f"  Sheet names: {list(cfg['sheets'].values())}")

    return cfg


def test_scan_runs(cfg):
    """Test PCA run scanning."""
    print("\n" + "=" * 60)
    print("TEST: Scan PCA Runs")
    print("=" * 60)

    runs_df = io.scan_pca_runs(cfg)

    assert len(runs_df) > 0, "Should find at least one PCA run"
    assert 'analysis_id' in runs_df.columns, "Should have analysis_id column"
    assert 'path_scores' in runs_df.columns, "Should have path_scores column"

    print(f"✓ Found {len(runs_df)} PCA runs")
    print(f"\n{runs_df[['analysis_id', 'analysis_type', 'polarity', 'dose_label']].to_string()}")

    return runs_df


def test_load_scores(runs_df, cfg):
    """Test scores loading from first run."""
    print("\n" + "=" * 60)
    print("TEST: Load PCA Scores")
    print("=" * 60)

    first_run = runs_df.iloc[0]
    scores = io.load_scores(first_run['path_scores'], cfg['sheets']['scores'])

    assert len(scores) > 0, "Should load at least one score row"
    assert 'PC1' in scores.columns, "Should have PC1 column"
    assert 'PC2' in scores.columns, "Should have PC2 column"
    assert 'sample_id' in scores.columns, "Should have sample_id column (renamed from sample_name)"

    print(f"✓ Loaded {len(scores)} scores from {first_run['analysis_id']}")
    print(f"  Shape: {scores.shape}")
    print(f"  Columns: {list(scores.columns)}")
    print(f"\n{scores.head(3).to_string()}")

    return scores


def test_load_loadings(runs_df, cfg):
    """Test loadings loading from first run."""
    print("\n" + "=" * 60)
    print("TEST: Load PCA Loadings")
    print("=" * 60)

    first_run = runs_df.iloc[0]
    loadings = io.load_loadings(first_run['path_loadings'], cfg['sheets']['loadings'])

    assert len(loadings) > 0, "Should load at least one loading row"
    assert 'mz' in loadings.columns, "Should have mz column (renamed from index)"
    assert 'loading_PC1' in loadings.columns, "Should have loading_PC1 column"
    assert 'loading_PC2' in loadings.columns, "Should have loading_PC2 column"

    print(f"✓ Loaded {len(loadings)} loadings from {first_run['analysis_id']}")
    print(f"  Shape: {loadings.shape}")
    print(f"  Columns: {list(loadings.columns)}")
    print(f"\n{loadings.head(3).to_string()}")

    return loadings


def test_load_variance(runs_df, cfg):
    """Test variance explained loading."""
    print("\n" + "=" * 60)
    print("TEST: Load Variance Explained")
    print("=" * 60)

    first_run = runs_df.iloc[0]
    variance = io.load_explained(first_run['path_explained'], cfg['sheets']['explained'])

    assert len(variance) > 0, "Should load at least one variance row"
    assert 'component' in variance.columns, "Should have component column"
    assert 'variance_ratio' in variance.columns, "Should have variance_ratio column"
    assert 'cumulative_variance' in variance.columns, "Should have cumulative_variance column"

    print(f"✓ Loaded {len(variance)} components from {first_run['analysis_id']}")
    print(f"\n{variance.to_string()}")

    return variance


def test_load_assignments(runs_df):
    """Test assignments loading if available."""
    print("\n" + "=" * 60)
    print("TEST: Load Fragment Assignments")
    print("=" * 60)

    first_run = runs_df.iloc[0]

    if not first_run['path_assignments']:
        print("⚠ No assignments file found, skipping")
        return None

    assignments = io.load_assignments(first_run['path_assignments'])

    if len(assignments) == 0:
        print("⚠ Assignments file empty")
        return None

    assert 'mz' in assignments.columns, "Should have mz column"
    assert 'assignment' in assignments.columns, "Should have assignment column"

    print(f"✓ Loaded {len(assignments)} assignments from {first_run['analysis_id']}")
    print(f"  Columns: {list(assignments.columns)}")
    print(f"\n{assignments.head(5).to_string()}")

    return assignments


def test_preprocess_merge(loadings, assignments, cfg):
    """Test assignment merging with ppm tolerance."""
    if assignments is None or len(assignments) == 0:
        print("\n⚠ Skipping merge test (no assignments)")
        return

    print("\n" + "=" * 60)
    print("TEST: Merge Assignments with ppm Tolerance")
    print("=" * 60)

    tol_ppm = cfg.get('preprocessing', {}).get('assignment_ppm_tolerance', 10.0)
    merged = preprocess.merge_assignments(loadings, assignments, tol_ppm=tol_ppm)

    assert len(merged) >= len(loadings), "Merged should have at least as many rows as loadings"
    assert 'assignment' in merged.columns, "Should have assignment column"

    n_assigned = merged['assignment'].notna().sum()
    pct_assigned = n_assigned / len(loadings) * 100

    print(f"✓ Merged assignments: {n_assigned}/{len(loadings)} ({pct_assigned:.1f}%) assigned")
    print(f"  ppm tolerance: {tol_ppm}")

    if 'assignment_conflict' in merged.columns:
        n_conflicts = merged['assignment_conflict'].sum()
        print(f"  Conflicts: {n_conflicts}")


def test_clean_meta(scores, runs_df, cfg):
    """Test metadata cleaning."""
    print("\n" + "=" * 60)
    print("TEST: Clean Metadata")
    print("=" * 60)

    first_run = runs_df.iloc[0]

    cleaned = preprocess.clean_meta(
        scores,
        analysis_id=first_run['analysis_id'],
        analysis_type=first_run['analysis_type'],
        polarity=first_run['polarity'],
        dose_label=first_run.get('dose_label'),
        cfg=cfg
    )

    assert 'analysis_id' in cleaned.columns, "Should have analysis_id"
    assert 'analysis_type' in cleaned.columns, "Should have analysis_type"
    assert 'polarity' in cleaned.columns, "Should have polarity"

    print(f"✓ Metadata cleaned for {first_run['analysis_id']}")
    print(f"  Added columns: analysis_id, analysis_type, polarity")
    print(f"  Polarity normalized: {cleaned['polarity'].iloc[0]}")


def run_all_tests():
    """Run all smoke tests."""
    print("\n" + "=" * 80)
    print("ToF-SIMS IO Layer Smoke Tests")
    print("=" * 80)

    try:
        # Test 1: Config
        cfg = test_config_load()

        # Test 2: Scan runs
        runs_df = test_scan_runs(cfg)

        # Test 3: Load scores
        scores = test_load_scores(runs_df, cfg)

        # Test 4: Load loadings
        loadings = test_load_loadings(runs_df, cfg)

        # Test 5: Load variance
        variance = test_load_variance(runs_df, cfg)

        # Test 6: Load assignments
        assignments = test_load_assignments(runs_df)

        # Test 7: Merge assignments
        test_preprocess_merge(loadings, assignments, cfg)

        # Test 8: Clean metadata
        test_clean_meta(scores, runs_df, cfg)

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)

        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
