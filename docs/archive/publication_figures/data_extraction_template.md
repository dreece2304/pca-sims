# DATA EXTRACTION TEMPLATE

## Required Data Files
1. negative_ion_assignments.csv (from Streamlit export)
2. positive_ion_assignments.csv (from Streamlit export) 
3. Raw ToF-SIMS data files (for dose-response curves)

## Key Fragment Data to Extract

### HIGH PRIORITY FRAGMENTS (for main figures):
```
Fragment    | m/z      | Ion Mode | Expected Trend    | Figure
H-          | 1.0078   | Negative | Decrease (-28%)   | 1B, 3D
35Cl-       | 34.97    | Negative | Decrease (HCl)    | 1B, 2E
37Cl-       | 36.97    | Negative | Decrease (HCl)    | 1B, 2E  
C2HO-       | 41.00    | Negative | Increase (+52%)   | 2C, 3B
COOH-       | 44.99    | Negative | Increase (+98%)   | 2C, 3B
C4HO-       | 65.00    | Negative | Increase (+119%)  | 2C, 3B
C6H-        | 73.01    | Negative | Increase (+154%)  | 2B, 3C
Al+         | 26.98    | Positive | Increase          | 2A, 3A
AlO-        | 42.98    | Negative | Decrease          | 2A, 3A
```

### DOSE RESPONSE DATA STRUCTURE:
```
Dose (μC/cm²) | SQ2: 2000 | SQ3: 5000 | SQ4: 10000 | SQ5: 15000
Pattern P1    | value     | value     | value      | value
Pattern P2    | value     | value     | value      | value  
Pattern P3    | value     | value     | value      | value
Mean          | calc      | calc      | calc       | calc
Std Dev       | calc      | calc      | calc       | calc
```

## Fragment Family Groupings

### For Figure 2 (Chemical Families):
```python
families = {
    'Aluminum': ['Al+', 'AlH+', 'AlO-', 'AlO2-', 'AlCH2-'],
    'Aromatic': ['C6H-', 'C5H-', 'C7H-', 'C8H-'],
    'Carbonyl': ['C4HO-', 'C3HO-', 'C2HO-', 'COOH-', 'CHO-'],
    'Radical': ['H-', 'F-'],
    'HCl_Dev': ['Cl-35', 'Cl-37'], 
    'Reference': ['C4H-', 'C2H-', 'C3H-']
}
```

## Statistical Calculations

### Correlation Analysis:
- Al+ vs AlO- inverse correlation
- C6H- vs dose positive correlation  
- H- vs dose negative correlation
- Cl- isotope ratio validation

### Error Propagation:
- Standard deviation across patterns
- Propagate errors in ratio calculations
- Report 95% confidence intervals

## Visualization Parameters

### Color Palette (Colorblind-Friendly):
```python
COLORS = {
    'Aluminum': '#d62728',    # Red
    'Aromatic': '#9467bd',    # Purple  
    'Carbonyl': '#ff7f0e',    # Orange
    'Radical': '#2ca02c',     # Green
    'HCl': '#1f77b4',        # Blue
    'Reference': '#17becf'    # Cyan
}
```

### Plot Specifications:
- Figure size: 12x8 inches (main), 8x6 inches (panels)
- DPI: 300 minimum
- Font: Arial, 12pt minimum
- Line width: 2pt minimum
- Marker size: 8pt minimum
- Error bar caps: 5pt
