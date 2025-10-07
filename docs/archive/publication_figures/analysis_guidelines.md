# PUBLICATION ANALYSIS GUIDELINES

## Figure Generation Workflow

### Step 1: Data Preparation
1. Export both positive and negative ion assignments from Streamlit
2. Ensure all fragment assignments are validated
3. Calculate dose-response statistics for each fragment family
4. Prepare error bars (standard deviation across P1, P2, P3)

### Step 2: Fragment Family Analysis
```
ALUMINUM CHEMISTRY:
- Al+ (m/z 26.98): Should increase with dose
- AlO- (m/z 42.98): Should decrease (oxygen migration)
- AlCH2- (m/z 41.00): Likely assignment for mysterious peak

AROMATIC FORMATION:  
- C6H- (m/z 73.01): Strong increase (thermodynamic stabilization)
- Calculate C6H-/C4H- ratio as crosslinking index

CARBONYL CASCADE:
- C4HO- (m/z 65.00): +119% increase
- C3HO- (m/z 53.00): +69% increase  
- C2HO- (m/z 41.00): +52% increase
- COOH- (m/z 44.99): +98% increase
```

### Step 3: Statistical Analysis
- Calculate R² values for all dose trends
- Perform correlation analysis between fragment pairs
- Validate pattern reproducibility across P1, P2, P3
- Assess mass accuracy for all assignments

### Step 4: Mechanistic Validation
- Confirm Al+ vs AlO- inverse correlation
- Validate carbonyl cascade progression
- Check H- generation → consumption pattern
- Cross-correlate positive and negative ion data

## Key Metrics to Report

### PCA Quality Metrics:
- PC1 variance explained (should be >60%)
- Loading distribution (top 10 fragments)
- Score progression with dose (R² > 0.9)

### Chemical Validation Metrics:
- Fragment assignment success rate (aim for >80%)
- Mass accuracy distribution (median <5 mDa)  
- Cross-correlation coefficients
- Isotope pattern validation

### Process Chemistry Metrics:
- C6H-/C4H- crosslinking ratio progression
- AlO- → carbonyl oxygen balance
- H- generation/consumption balance
- Cl- isotope ratio validation (3.4:1)

## Quality Control Checklist

Before publication:
☐ All major peaks (loading >0.02) assigned
☐ Error bars on all experimental data
☐ Statistical significance marked (p-values)
☐ Cross-correlation validation complete
☐ Mechanistic consistency checked
☐ Figure quality >300 DPI
☐ Color scheme accessible (colorblind-friendly)
☐ Font sizes readable (>12pt)
