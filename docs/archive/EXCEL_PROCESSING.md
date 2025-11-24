# ToF-SIMS Excel Processing Guide

## Overview

The ToF-SIMS Excel Processor handles Excel files containing fragment assignments and intensity data from ToF-SIMS instruments. It performs the following operations:

1. **Fragment Database Update**: Checks fragment assignments against the database and adds new fragments
2. **Duplicate Handling**: Merges duplicate m/z values using mean intensities
3. **Data Export**: Outputs cleaned data in tab-delimited format for PCA analysis

## Input Format

The processor expects Excel files with the following structure:

| Column 0        | Column 1  | Column 2+ |
|-----------------|-----------|-----------|
| Fragment Name   | Mass (u)  | Sample intensities (TIC-normalized) |
| H+              | 1.00720   | 0.001630  |
| CH_3+           | 15.02292  | 0.003380  |
| ...             | ...       | ...       |

**Requirements:**
- First column: Fragment assignments (e.g., "H+", "CH_3+", "C_2H_5O-")
- Second column: m/z values (numeric)
- Remaining columns: Sample intensities (already TIC-normalized)
- Intensities should be in decimal format (not percentages)

## Usage

### Python API

```python
from tofsims_excel_processor import process_tofsims_excel

# Process Excel file
df, stats = process_tofsims_excel(
    excel_path="data/PositiveIon/AllPosNewwithFragment.xlsx",
    polarity="positive",
    output_path="data/PositiveIon/processed_data.txt"
)

# Access results
print(f"Unique m/z values: {stats['unique_mz_values']}")
print(f"Duplicates merged: {stats['duplicates_removed']}")
print(f"New fragments added: {stats['new_fragments_added']}")
```

### Command-Line Interface

```bash
# Activate environment
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims

# Process Excel file
python scripts/utilities/process_tofsims_excel.py \
    data/PositiveIon/AllPosNewwithFragment.xlsx \
    positive \
    data/PositiveIon/processed_data.txt
```

**Arguments:**
- `excel_file`: Path to Excel file with fragments and intensities
- `polarity`: Ion polarity ("positive" or "negative")
- `output_file`: (Optional) Output path for tab-delimited file

If `output_file` is not provided, it will be auto-generated as `<input>_processed.txt`.

## Processing Steps

### 1. Fragment Database Update

The processor loads the fragment database (`data/FragmentDatabase/alucone_fragments_complete.json`) and checks each fragment assignment:

- **New fragments**: Added to database with metadata
- **Existing fragments**: Skipped (no duplicate entries)
- **Tolerance**: 0.001 Da (1 mDa) for matching m/z values

**Auto-generated metadata:**
```json
{
  "mass": 15.02292,
  "assignments": ["CH_3+"],
  "formulas": ["CH3"],
  "families": ["Unknown"],
  "polarity": "positive",
  "confidence": "High",
  "notes": "Auto-added from Excel file on 2025-10-19"
}
```

### 2. Duplicate Handling

When multiple rows have the same m/z value (within machine precision):

- **Detection**: Exact m/z matching
- **Merging**: Mean of all duplicate intensities across all samples
- **Reporting**: Details saved in processing stats

**Example:**
```
Input:
  m/z 27.023: [0.0274, 0.0281, 0.0285]
  m/z 27.023: [0.0271, 0.0279, 0.0284]

Output:
  m/z 27.023: [0.02725, 0.0280, 0.02845]  # Mean of duplicates
```

### 3. Data Export

Cleaned data is exported in tab-delimited format compatible with the PCA analysis system:

**Output format:**
```
Mass    P1_SQ1   P1_SQ2   P1_SQ3   ...
1.0072  0.00163  0.00164  0.00161  ...
15.0229 0.00338  0.00335  0.00330  ...
```

This format can be directly loaded into:
- `SimpleToFSIMSPCA` class
- Qt PCA application
- Any tab-delimited data reader

## Processing Statistics

The processor returns detailed statistics:

```python
{
    "total_rows": 115,              # Original row count
    "unique_mz_values": 103,        # After duplicate merging
    "duplicates_removed": 12,       # Number of duplicate m/z values
    "duplicate_details": [...],     # List of merged m/z values
    "new_fragments_added": 34,      # Fragments added to database
    "sample_columns": 18,           # Number of sample columns
    "mz_range": (1.0072, 99.0213)  # m/z range
}
```

## Fragment Database Backup

The processor automatically creates backups before modifying the fragment database:

- **Location**: `data/FragmentDatabase/backups/`
- **Naming**: `backup_YYYYMMDD_HHMMSS.json`
- **Trigger**: Any time new fragments are added

## Error Handling

**Common issues:**

1. **File not found**
   ```
   Error: Excel file does not exist
   Solution: Check file path
   ```

2. **Invalid polarity**
   ```
   Error: Polarity must be 'positive' or 'negative'
   Solution: Use lowercase "positive" or "negative"
   ```

3. **Missing columns**
   ```
   Error: Expected at least 3 columns (fragment, m/z, intensities)
   Solution: Check Excel file structure
   ```

4. **Database write error**
   ```
   Warning: Error saving fragment database (database may be read-only)
   Solution: Check file permissions
   ```

## Integration with PCA Workflow

**Complete workflow:**

```bash
# Step 1: Process Excel file with fragments
python scripts/utilities/process_tofsims_excel.py \
    data/PositiveIon/AllPosNewwithFragment.xlsx \
    positive \
    data/PositiveIon/AllPosNew_PCA_ready.txt

# Step 2: Launch PCA application
python launch_optimized.py

# Step 3: Load processed data in GUI
# File → Load Data → Select AllPosNew_PCA_ready.txt
```

## Technical Implementation

**Module**: `src/tofsims_excel_processor.py`

**Key classes:**
- `ToFSIMSExcelProcessor`: Main processing engine
- Methods:
  - `process_excel_file()`: Complete processing pipeline
  - `_update_fragment_database()`: Fragment database management
  - `_create_intensity_dataframe()`: Duplicate handling
  - `export_to_tab_delimited()`: Data export

**Dependencies:**
- pandas: Excel reading and DataFrame operations
- numpy: Numerical operations
- json: Fragment database I/O

## Best Practices

1. **Always specify polarity correctly** - this affects fragment database organization
2. **Check processing statistics** - verify duplicate handling is reasonable
3. **Review new fragments** - ensure auto-added fragments are correct
4. **Keep backups** - database backups are automatic but consider additional backups
5. **Validate output** - spot-check intensities before PCA analysis

## Example Output

```
📊 ToF-SIMS Excel Processor
============================================================
Input file: data/PositiveIon/AllPosNewwithFragment.xlsx
Polarity: positive

✅ Loaded fragment database: 289 fragments

📊 Processing ToF-SIMS Excel file
   Raw data shape: (115, 20)
   Found 115 fragment assignments
   m/z range: 1.0072 - 99.0213
   Sample columns: 18

🔍 Checking fragment database for new entries...
   Existing positive fragments in database: 117
   ✅ Added 34 new fragments to database
   📦 Created backup: backups/backup_20251119_123919.json

🧹 Creating intensity DataFrame with duplicate handling...
   Found 12 m/z values with duplicates
   ✅ Merged 12 duplicate m/z values using mean

✅ Processing complete:
   Unique m/z values: 103
   Duplicates merged: 12
   New fragments added to database: 34

💾 Exporting to tab-delimited format
   ✅ Exported 103 m/z values × 18 samples

✅ SUCCESS!
   Output saved to: data/PositiveIon/AllPosNew_processed.txt
```

## Future Enhancements

Potential improvements:
- Support for additional Excel formats (multi-sheet, different column orders)
- Configurable duplicate handling (mean, median, max)
- Fragment assignment validation (formula parsing, charge state verification)
- Integration with Qt GUI for one-click processing
