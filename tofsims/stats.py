"""
Statistical analysis for ToF-SIMS PCA outputs.

Functions for:
- PCA scores statistics (dose group comparisons)
- PCA loadings significance tests
- Fragment family parsing and grouping
- Dose trajectory analysis
"""

import logging
from typing import List, Optional, Tuple, Dict
import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import kruskal, spearmanr, f_oneway
from statsmodels.stats.multitest import multipletests


logger = logging.getLogger(__name__)


# ===== Fragment Family Parsing =====

def parse_fragment_formula(assignment: str) -> Dict[str, int]:
    """
    Parse fragment assignment into element counts.

    Examples:
        "C_6H_5+ (C6H5)" -> {"C": 6, "H": 5}
        "CHO+ (CHO)" -> {"C": 1, "H": 1, "O": 1}

    Parameters
    ----------
    assignment : str
        Fragment assignment string

    Returns
    -------
    dict
        Element counts {element: count}
    """
    if pd.isna(assignment) or not assignment:
        return {}

    # Extract formula from parentheses or use full string
    match = re.search(r'\(([^)]+)\)', assignment)
    if match:
        formula = match.group(1)
    else:
        # Try to extract from underscore notation: C_6H_5+
        formula = assignment.replace('_', '').replace('+', '').replace('-', '')

    # Parse element counts: C6H5 -> {C: 6, H: 5}
    elements = {}
    pattern = r'([A-Z][a-z]?)(\d*)'

    for match in re.finditer(pattern, formula):
        element = match.group(1)
        count = match.group(2)
        count = int(count) if count else 1
        elements[element] = elements.get(element, 0) + count

    return elements


def classify_fragment(assignment: str) -> str:
    """
    Classify fragment into chemical family.

    Families:
    - "C-H only" - hydrocarbons
    - "C-H-O" - oxygenated
    - "C-H-N" - nitrogenated
    - "Other" - contains other elements
    - "Unknown" - no assignment

    Parameters
    ----------
    assignment : str
        Fragment assignment

    Returns
    -------
    str
        Fragment family classification
    """
    if pd.isna(assignment) or not assignment:
        return "Unknown"

    elements = parse_fragment_formula(assignment)

    if not elements:
        return "Unknown"

    elem_set = set(elements.keys())

    # Check families
    if elem_set <= {'C', 'H'}:
        return "C-H only"
    elif elem_set <= {'C', 'H', 'O'}:
        return "C-H-O"
    elif elem_set <= {'C', 'H', 'N'}:
        return "C-H-N"
    else:
        return "Other"


def calculate_hc_ratio(assignment: str) -> Optional[float]:
    """
    Calculate H/C ratio for a fragment.

    Parameters
    ----------
    assignment : str
        Fragment assignment

    Returns
    -------
    float or None
        H/C ratio, or None if not calculable
    """
    elements = parse_fragment_formula(assignment)

    if 'C' not in elements or 'H' not in elements:
        return None

    if elements['C'] == 0:
        return None

    return elements['H'] / elements['C']


def group_by_fragment_family(loadings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add fragment family classifications to loadings dataframe.

    Parameters
    ----------
    loadings_df : pd.DataFrame
        Loadings with 'assignment' column

    Returns
    -------
    pd.DataFrame
        Loadings with added columns: fragment_family, hc_ratio
    """
    df = loadings_df.copy()

    if 'assignment' not in df.columns:
        logger.warning("No 'assignment' column found")
        df['fragment_family'] = "Unknown"
        df['hc_ratio'] = np.nan
        return df

    df['fragment_family'] = df['assignment'].apply(classify_fragment)
    df['hc_ratio'] = df['assignment'].apply(calculate_hc_ratio)

    logger.info(f"Fragment families: {df['fragment_family'].value_counts().to_dict()}")

    return df


# ===== PCA Scores Statistics =====

def scores_anova(
    scores_df: pd.DataFrame,
    pc: str = 'PC1',
    grouping_col: str = 'dose_label',
    test: str = 'kruskal',
    alpha: float = 0.05
) -> Dict:
    """
    Test for differences in PC scores between groups.

    Parameters
    ----------
    scores_df : pd.DataFrame
        PCA scores with PC columns and grouping variable
    pc : str
        Principal component to test (default: PC1)
    grouping_col : str
        Column to group by (default: dose_label)
    test : str
        'kruskal' (non-parametric) or 'anova' (parametric)
    alpha : float
        Significance level

    Returns
    -------
    dict
        Results: statistic, pvalue, groups, means
    """
    if pc not in scores_df.columns:
        raise ValueError(f"PC column '{pc}' not found in scores_df")

    if grouping_col not in scores_df.columns:
        raise ValueError(f"Grouping column '{grouping_col}' not found")

    # Group data
    groups = []
    group_names = []
    group_means = {}

    for group_name, group_data in scores_df.groupby(grouping_col, observed=True):
        group_scores = group_data[pc].dropna().values
        if len(group_scores) > 0:
            groups.append(group_scores)
            group_names.append(str(group_name))
            group_means[str(group_name)] = group_scores.mean()

    if len(groups) < 2:
        logger.warning(f"Need at least 2 groups, found {len(groups)}")
        return {}

    # Perform test
    if test == 'kruskal':
        statistic, pvalue = kruskal(*groups)
        test_name = 'Kruskal-Wallis'
    elif test == 'anova':
        statistic, pvalue = f_oneway(*groups)
        test_name = 'ANOVA'
    else:
        raise ValueError(f"Unknown test: {test}")

    result = {
        'pc': pc,
        'test': test_name,
        'statistic': statistic,
        'pvalue': pvalue,
        'significant': pvalue < alpha,
        'n_groups': len(groups),
        'group_names': group_names,
        'group_means': group_means
    }

    logger.info(
        f"{test_name} on {pc} scores: p={pvalue:.4f} "
        f"({'significant' if pvalue < alpha else 'not significant'} at α={alpha})"
    )

    return result


def scores_trajectory(
    scores_df: pd.DataFrame,
    pc: str = 'PC1',
    dose_col: str = 'actual_dose'
) -> Dict:
    """
    Analyze dose trajectory in PC scores.

    Tests:
    - Linear correlation (Spearman)
    - Linear regression slope

    Parameters
    ----------
    scores_df : pd.DataFrame
        PCA scores
    pc : str
        Principal component
    dose_col : str
        Dose column (numeric)

    Returns
    -------
    dict
        Correlation, slope, p-value
    """
    if pc not in scores_df.columns:
        raise ValueError(f"PC column '{pc}' not found")

    if dose_col not in scores_df.columns:
        raise ValueError(f"Dose column '{dose_col}' not found")

    # Remove NaN
    data = scores_df[[pc, dose_col]].dropna()

    if len(data) < 3:
        logger.warning("Insufficient data for trajectory analysis")
        return {}

    x = data[dose_col].values
    y = data[pc].values

    # Spearman correlation
    corr, pvalue_corr = spearmanr(x, y)

    # Linear regression
    slope, intercept, r_value, pvalue_reg, stderr = stats.linregress(x, y)

    result = {
        'pc': pc,
        'dose_col': dose_col,
        'correlation': corr,
        'pvalue_corr': pvalue_corr,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'pvalue_reg': pvalue_reg
    }

    logger.info(
        f"Trajectory {pc} vs {dose_col}: "
        f"r={corr:.3f} (p={pvalue_corr:.4f}), "
        f"slope={slope:.4e}"
    )

    return result


# ===== PCA Loadings Statistics =====

def loadings_significance(
    loadings_df: pd.DataFrame,
    pc: str = 'PC1',
    threshold: float = 0.1,
    top_k: Optional[int] = None
) -> pd.DataFrame:
    """
    Identify significant loadings.

    Significance criteria:
    - Absolute loading > threshold
    - Or in top k by absolute value

    Parameters
    ----------
    loadings_df : pd.DataFrame
        PCA loadings
    pc : str
        Principal component
    threshold : float
        Absolute loading threshold for significance
    top_k : int, optional
        Number of top loadings to mark as significant

    Returns
    -------
    pd.DataFrame
        Loadings with 'significant' column
    """
    loading_col = f'loading_{pc}'

    if loading_col not in loadings_df.columns:
        raise ValueError(f"Loading column '{loading_col}' not found")

    df = loadings_df.copy()

    # Absolute loading
    df['abs_loading'] = df[loading_col].abs()

    # Threshold criterion
    df['significant'] = df['abs_loading'] >= threshold

    # Top-k criterion
    if top_k is not None:
        top_indices = df.nlargest(top_k, 'abs_loading').index
        df.loc[top_indices, 'significant'] = True

    n_sig = df['significant'].sum()
    logger.info(f"Significant loadings for {pc}: {n_sig}/{len(df)} (threshold={threshold})")

    return df


def fragment_family_summary(
    loadings_df: pd.DataFrame,
    pc: str = 'PC1'
) -> pd.DataFrame:
    """
    Summarize loadings by fragment family.

    Parameters
    ----------
    loadings_df : pd.DataFrame
        Loadings with fragment_family column
    pc : str
        Principal component

    Returns
    -------
    pd.DataFrame
        Summary with columns: fragment_family, n_fragments, mean_loading,
        mean_abs_loading, direction (positive/negative/mixed)
    """
    loading_col = f'loading_{pc}'

    if loading_col not in loadings_df.columns:
        raise ValueError(f"Loading column '{loading_col}' not found")

    if 'fragment_family' not in loadings_df.columns:
        logger.warning("No fragment_family column. Run group_by_fragment_family() first.")
        return pd.DataFrame()

    # Group by family
    summary = loadings_df.groupby('fragment_family', observed=True).agg({
        loading_col: ['count', 'mean', lambda x: x.abs().mean()],
        'mz': 'count'
    }).reset_index()

    summary.columns = ['fragment_family', 'n_fragments', 'mean_loading', 'mean_abs_loading', '_']
    summary = summary.drop(columns=['_'])

    # Determine predominant direction
    def direction(row):
        if row['mean_loading'] > 0.05:
            return 'positive'
        elif row['mean_loading'] < -0.05:
            return 'negative'
        else:
            return 'mixed'

    summary['direction'] = summary.apply(direction, axis=1)

    # Sort by mean absolute loading
    summary = summary.sort_values('mean_abs_loading', ascending=False)

    logger.info(f"\nFragment family summary for {pc}:\n{summary.to_string(index=False)}")

    return summary


# ===== Helper Functions =====

def select_top_loadings(
    loadings_df: pd.DataFrame,
    pc: str = 'PC1',
    k: int = 30,
    include_sign: bool = True
) -> pd.DataFrame:
    """
    Select top k loadings for analysis.

    Parameters
    ----------
    loadings_df : pd.DataFrame
        PCA loadings
    pc : str
        Principal component
    k : int
        Number of top loadings
    include_sign : bool
        If True, select k positive and k negative (2k total)

    Returns
    -------
    pd.DataFrame
        Filtered loadings
    """
    loading_col = f'loading_{pc}'

    if loading_col not in loadings_df.columns:
        raise ValueError(f"Loading column '{loading_col}' not found")

    if include_sign:
        # Top k positive and top k negative
        pos = loadings_df.nlargest(k, loading_col)
        neg = loadings_df.nsmallest(k, loading_col)
        top = pd.concat([pos, neg]).drop_duplicates(subset=['mz'])
    else:
        # Top k by absolute value
        df_abs = loadings_df.copy()
        df_abs['abs_loading'] = df_abs[loading_col].abs()
        top = df_abs.nlargest(k, 'abs_loading')

    logger.info(f"Selected {len(top)} top loadings from {pc} (k={k}, include_sign={include_sign})")

    return top


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("ToF-SIMS PCA Stats Module Test")
    print("=" * 60)

    # Test fragment parsing
    test_assignments = [
        "C_6H_5+ (C6H5)",
        "C_3H_5+ (C3H5)",
        "CHO+ (CHO)",
        "Al+ (Al)",
        ""
    ]

    print("\nFragment parsing:")
    for assignment in test_assignments:
        elements = parse_fragment_formula(assignment)
        family = classify_fragment(assignment)
        hc_ratio = calculate_hc_ratio(assignment)
        print(f"  {assignment:20s} -> {elements}, family={family}, H/C={hc_ratio}")

    # Test scores ANOVA
    print("\nScores ANOVA test:")
    scores_data = pd.DataFrame({
        'PC1': np.random.randn(15),
        'dose_label': ['0', '0', '0', '2000', '2000', '2000',
                       '5000', '5000', '5000', '10000', '10000', '10000',
                       '15000', '15000', '15000']
    })

    result = scores_anova(scores_data, pc='PC1', grouping_col='dose_label')
    print(f"  Result: {result}")
