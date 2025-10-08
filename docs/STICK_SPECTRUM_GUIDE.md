# Stick Spectrum Tab - User Guide

## Overview

The **Stick Spectrum** tab provides a powerful interface for visualizing and analyzing ToF-SIMS mass spectra with dose-averaged intensities, comprehensive filtering options, and manual fragment assignment capabilities.

## Features

### 1. Dose Selection & Plotting
- **Dose Selection**: Choose from SQ0 (as-deposited), SQ2-SQ5 (various exposure levels)
- **Replicate Averaging**: Automatically averages across P1, P2, P3 replicates
- **Standard Deviation Display**: Toggle SD plot to show measurement variability
- **Fragment Assignment**: Automatic matching to database with 100 ppm tolerance

### 2. Six Filter System

All filters can be enabled/disabled independently and work in combination:

#### Filter 1: Intensity Threshold
- **Purpose**: Remove low-intensity noise peaks
- **Control**: Slider (0-100% of maximum intensity)
- **Usage**: Start at 5-10% to remove baseline noise
- **Display**: Shows threshold value in scientific notation

#### Filter 2: Top N Peaks
- **Purpose**: Show only the highest intensity peaks
- **Control**: Dropdown (All, 20, 50, 100, 200)
- **Usage**: Select "Top 20" for focused analysis of major fragments
- **Note**: Applied AFTER intensity filter

#### Filter 3: m/z Range
- **Purpose**: Focus on specific mass range
- **Control**: Min/Max input fields with real-time validation
- **Usage**: Enter range like "10-50" for low-mass fragments
- **Validation**: ✓ green (valid), ✗ red (invalid)

#### Filter 4: PCA Loadings
- **Purpose**: Show chemically significant peaks (high PC1 loadings)
- **Control**: Slider (0.00-1.00 absolute loading threshold)
- **Requirement**: Must run PCA first
- **Usage**: Start at 0.05, increase to see fewer peaks
- **Status**: Shows "PCA not run" or "PCA available"

#### Filter 5: Statistical Significance
- **Purpose**: Show peaks with mean > N×SD (signal-to-noise ratio)
- **Control**: Dropdown (Mean > 1×SD, 2×SD, 3×SD)
- **Usage**: 2×SD = typical significance threshold
- **Note**: Ensures reliable measurements

#### Filter 6: Assignment Status
- **Purpose**: Filter by database assignment status
- **Control**: Radio buttons (All / Assigned Only / Unassigned Only)
- **Usage**: "Unassigned Only" to find peaks needing identification

### 3. Fragment Assignment Table

**Access**: Click "View Fragment Table" button

**Features**:
- 7 columns: m/z, Mean Intensity, Std Dev, CV%, Assignment, Confidence, Show Label
- Sortable by any column (click header)
- Search box: Filter by m/z or assignment name
- Label toggles: Check boxes to show/hide peak labels on plot
- Export: Save table to CSV

**Table Actions**:
- **Select row** + **Manual Assign**: Open manual assignment dialog
- **Toggle checkboxes**: Show/hide labels on spectrum plot
- **Export to CSV**: Save filtered results for external analysis

### 4. Manual Fragment Assignment

**Purpose**: Assign fragments not in database or correct existing assignments

**How to Use**:
1. Click "View Fragment Table"
2. Select a peak (especially unassigned ones)
3. Click "✏️ Manual Assign" button

**Dialog Features**:

#### Element Composition
- **Spinners**: Set counts for C, H, O, N, Al, Si, Cl, F, Na, K
- **Quick Set Buttons**: CH, C₂H, OH, AlO (common fragments)
- **Clear All**: Reset all element counts

#### Real-Time Calculation
- **Formula**: Displays element composition (e.g., C_2H)
- **Calculated Mass**: Shows theoretical mass
- **Mass Error**: ppm and Da error from observed m/z
- **Color Coding**:
  - ✓ Green: <50 ppm (excellent match)
  - ⚠ Orange: 50-100 ppm (acceptable)
  - ✗ Red: ≥100 ppm (poor match)

#### Validation Warnings
- Mass error exceeds 50 ppm threshold
- Unusual hydrogen count (valence issues)
- Al + high carbon (uncommon for alucone)
- Na/K detected (likely contamination)

#### Assignment Details
- **Assignment Name**: Display name (e.g., "C₂H⁻")
- **Chemical Family**: Al-based, Saturated_carbon, Unsaturated_carbon, etc.
- **Confidence**: High, Medium, Low
- **Notes**: Optional description

#### Save Behavior
- ✅ **Creates timestamped backup** of fragment database
- ✅ **Updates or adds fragment** to database
- ✅ **Updates metadata** (counts, timestamp)
- ✅ **Reloads database** automatically
- ✅ **Refreshes plot** with new assignment

### 5. Database Management

**Location**: `data/FragmentDatabase/alucone_fragments_complete.json`

**Backup System**:
- **Auto-backup**: Every manual assignment creates backup
- **Backup location**: `data/FragmentDatabase/backups/`
- **Naming**: `before_manual_assignment_YYYYMMDD_HHMMSS.json`
- **Safety**: Original database preserved if errors occur

**Error Handling**:
- Permission denied → Shows error, no database change
- JSON corruption → Alerts user, suggests backup restore
- Unexpected error → Safe failure, backup untouched

## Typical Workflow

### Basic Analysis
1. Load data in main tab
2. Navigate to "Stick Spectrum" tab
3. Select dose (e.g., SQ4 for high exposure)
4. Click "Plot Spectrum"
5. Enable 5% intensity filter to remove noise
6. View assigned peaks

### Focused Analysis
1. Run PCA in main tab first
2. Switch to Stick Spectrum
3. Enable PCA loadings filter (threshold 0.05)
4. Enable "Mean > 2×SD" statistical filter
5. Enable "Assigned Only" filter
6. See only significant, identified fragments

### Manual Assignment
1. Plot spectrum for any dose
2. Click "View Fragment Table"
3. Search for "Unassigned"
4. Select an unassigned peak
5. Click "✏️ Manual Assign"
6. Use quick set buttons or manually enter elements
7. Verify mass error <50 ppm (green ✓)
8. Fill in assignment name and details
9. Click "💾 Save Assignment"
10. Confirm backup created

### Export Results
1. Apply desired filters
2. Click "View Fragment Table"
3. Click "💾 Export to CSV"
4. Choose filename and location
5. Use in Excel, Origin, or other software

## Tips & Best Practices

### Filter Combinations
- **General cleanup**: 5% intensity + Mean > 2×SD
- **Major peaks only**: 10% intensity + Top 20
- **PCA-relevant**: PCA loadings ≥0.05 + Assigned Only
- **Find unknowns**: 5% intensity + Unassigned Only

### Mass Error Guidelines
- **<10 ppm**: Excellent match (unambiguous)
- **10-50 ppm**: Good match (confident assignment)
- **50-100 ppm**: Acceptable (verify with chemistry)
- **>100 ppm**: Poor match (likely incorrect)

### Assignment Confidence
- **High**: Well-known fragment, <20 ppm error
- **Medium**: Reasonable match, 20-50 ppm error
- **Low**: Tentative assignment, >50 ppm error or unusual formula

### Database Maintenance
- **Backup policy**: Keep at least last 5 backups
- **Review assignments**: Periodically check "Low" confidence assignments
- **Cleanup**: Remove test assignments from database
- **Restore**: Use backup if database becomes corrupted

## Keyboard Shortcuts

Currently available:
- **Tab**: Switch between input fields in manual assignment dialog
- **Enter**: Accept manual assignment (when focused on save button)
- **Esc**: Cancel manual assignment dialog

## Troubleshooting

### "PCA not run" Status
- **Problem**: PCA loadings filter unavailable
- **Solution**: Switch to main tab, run PCA, return to Stick Spectrum

### No Peaks Visible After Filtering
- **Problem**: All peaks filtered out
- **Solution**: Reduce filter stringency (lower intensity %, lower PCA threshold)

### Assignment Not Saving
- **Problem**: Database write error
- **Solution**: Check file permissions on `alucone_fragments_complete.json`

### Mass Error Always High
- **Problem**: Incorrect element composition
- **Solution**: Verify formula matches observed m/z, check polarity

### Plot Not Updating
- **Problem**: Filters not applied
- **Solution**: Toggle filter checkbox off/on to refresh

## Advanced Features

### Combined Filters
Filters are applied sequentially in order:
1. Intensity threshold
2. Top N peaks
3. m/z range
4. PCA loadings
5. Statistical significance
6. Assignment status

Each filter narrows the peak list further.

### Statistical Significance
- **1×SD**: Very permissive, includes most peaks
- **2×SD**: Standard significance (p ≈ 0.05)
- **3×SD**: High confidence (p ≈ 0.01)

### Label Management
- Labels only show for assigned peaks
- Toggle labels individually in fragment table
- Labels persist when switching doses
- Export includes label status

## Data Format

### Fragment Table CSV Export
```
m/z,Mean Intensity,Std Dev,CV%,Assignment,Confidence,Show Label
25.0086,5.234e-02,1.023e-02,19.56,C₂H⁻,High,Yes
```

### Database JSON Structure
```json
{
  "mass": 25.0086,
  "assignments": ["C₂H⁻"],
  "formulas": ["C2H"],
  "families": ["Unsaturated_carbon"],
  "polarity": "negative",
  "confidence": "High",
  "notes": "Manual assignment - User-assigned"
}
```

## Version History

- **v1.0** (2025-10): Initial release
  - Dose selection and replicate averaging
  - 6 comprehensive filters
  - Fragment assignment table
  - Manual assignment dialog with database write
  - Timestamped backups

## Support

For issues or feature requests:
- Check `docs/` folder for additional documentation
- Review `CLAUDE.md` for development environment
- Inspect `data/FragmentDatabase/backups/` if database issues occur

---

**Generated with Claude Code** | Last updated: 2025-10-08
