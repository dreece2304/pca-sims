# ToF-SIMS Figure Design Plan
## Publication Figure Strategy & Implementation Guide

---

## 🎯 **Figure Integration Strategy**

### **Main Figure: SEM + ToF-SIMS Fragment Maps**
**Concept**: Combine morphological evolution (SEM) with chemical mechanism (ToF-SIMS fragment maps)

**Structure**:
- **Top row**: SEM images of dose squares (4-5 key doses to match ToF-SIMS: SQ2, SQ3, SQ4, SQ5)
- **Bottom rows**: 2-3 ToF-SIMS fragment maps per dose square showing chemical evolution

**Key Fragment Maps to Display**:
1. **H⁻** (confirmed - highest loading, radical chemistry indicator)
2. **Al⁺** (aluminum chemistry, positive mode)
3. **C₆H⁻** (aromatic formation marker)
4. **One carbonyl** (C₄HO⁻ or COOH⁻ - to be determined based on visual impact)

**Data Requirements**:
- SEM images of dose squares from original 12-square array
- ToF-SIMS software fragment maps for selected fragments
- Dose-to-square correlation (SQ2=2000 μC/cm², SQ3=5000 μC/cm², etc.)

---

### **Separate Detailed Figure: Chemical Transformation Families**
**Concept**: Systematic dose-response curves organized by chemical families

**Organization**: Chemical families (not positive vs negative separation)
**Families to Include**:
1. **Aluminum Chemistry**: Al⁺, AlH⁺, AlO⁻, AlO₂⁻, AlCH₂⁻
2. **Aromatic Formation**: C₆H⁻, C₅H⁻ (if detected), related aromatic fragments
3. **Carbonyl Cascade**: C₄HO⁻, C₃HO⁻, C₂HO⁻, COOH⁻
4. **Radical Chemistry**: H⁻, other radical species
5. **Process Validation**: Cl⁻ isotopes, reference ions

**Visual Strategy**:
- **Loading impact representation**: Line thickness, color intensity, or legend notation (TBD)
- **Positive and negative ions**: Same plots per family
- **Error bars**: Standard deviation across P1, P2, P3 patterns

---

### **Fragment Assignment Table**
**Scope**: Top 10-15 most significant fragments
**Cutoff Criterion**: |PC1 loading| > 0.02 or 0.03 (to be determined)
**Format**: 
- Single table with horizontal sub-headings
- "Positive Ions" section
- "Negative Ions" section
**Location**: With main figure or in supplementary information

---

## 📊 **Software Implementation Plan**

### **Data Analysis & Plotting**:
- **Environment**: mamba env with matplotlib/plotly
- **Scripts**: Use existing analysis tools + custom plotting scripts

### **Chemical Mechanism Diagrams**:
- **Primary option**: ChemDraw (current workflow)
- **Linux alternatives to explore**:
  - **Avogadro** (better for thin-film/extended structures)
  - **MarvinSketch** (academic license, good for reaction schemes)
  - **ChemSketch** (free, runs in Wine)

### **Figure Assembly**:
- **Adobe Illustrator** (final assembly and layout)

---

## ⚠️ **Critical Issues to Resolve**

### **1. Fragment Assignment Verification** (HIGH PRIORITY)
- **Bug identified**: Streamlit GUI assigning negative ions in positive ion mode
- **Action required**: Fix ion mode-specific assignment logic
- **Impact**: Affects fragment identification accuracy

### **2. Complete Fragment Assignment**
- **Current status**: Some significant fragments still unassigned
- **Requirement**: All fragments with |loading| > 0.02 must be assigned
- **Method**: Systematic analysis using exact mass matching + cross-correlation

### **3. Fragment Selection for Maps**
- **H⁻**: Confirmed (highest loading)
- **Remaining 2-3 fragments**: Requires further analysis of visual impact and chemical significance

---

## 🔄 **Implementation Workflow**

### **Phase 1: Bug Fixes & Data Validation**
1. **Fix Streamlit ion mode assignment bug**
2. **Complete fragment assignment verification** 
3. **Validate all high-loading fragment identities**

### **Phase 2: Data Preparation**
1. **Extract dose-response data** for all significant fragments
2. **Organize by chemical families**
3. **Calculate statistics** (means, standard deviations across patterns)
4. **Prepare fragment maps** from ToF-SIMS software

### **Phase 3: Figure Generation**
1. **Generate dose-response plots** (chemical families)
2. **Create fragment assignment table**
3. **Prepare mechanism diagrams**
4. **Assemble in Illustrator**

### **Phase 4: Integration with SEM Data**
1. **Select matching dose squares** between SEM and ToF-SIMS
2. **Align spatial scales** and image registration
3. **Finalize fragment map selection**
4. **Composite figure assembly**

---

## 📋 **Design Specifications**

### **Figure Quality Standards**:
- **Resolution**: 300 DPI minimum
- **Color scheme**: Consistent across figures, colorblind-friendly
- **Fonts**: Arial, 12pt minimum
- **Error bars**: Always included for experimental data

### **Chemical Family Color Scheme** (Preliminary):
```
Aluminum Chemistry: #e74c3c (red)
Aromatic Formation: #9b59b6 (purple)
Carbonyl Cascade: #f39c12 (orange)
Radical Chemistry: #27ae60 (green)
Process Validation: #34495e (dark blue)
```

### **Loading Representation Options** (TBD):
- Line thickness proportional to |loading|
- Color intensity based on loading magnitude  
- Numerical values in legend/table

---

## 🎯 **Decision Points Requiring Resolution**

### **Fragment Selection**:
- [ ] Finalize 2-3 additional fragments for ToF-SIMS maps (beyond H⁻)
- [ ] Determine loading cutoff for fragment table (0.02 vs 0.03)
- [ ] Choose loading representation method for family plots

### **Mechanism Diagrams**:
- [ ] Decide on conceptual pathway complexity level
- [ ] Choose between ChemDraw vs Linux alternatives
- [ ] Determine if separate reaction schemes needed for each family

### **Table vs Figure Placement**:
- [ ] Fragment assignment table: Main figure or supplementary?
- [ ] PCA scores/loadings: Supplementary confirmed, detailed format TBD

---

## ✅ **Success Criteria**

### **Main Figure Success**:
- [ ] Clear visual connection between SEM morphology and chemical changes
- [ ] Fragment maps show meaningful spatial/dose evolution
- [ ] Professional quality suitable for publication

### **Chemical Families Figure Success**:
- [ ] All significant fragments assigned and validated
- [ ] Clear dose-response trends for each family
- [ ] Statistical rigor (error bars, significance testing)
- [ ] Mechanistic coherence across families

### **Overall Integration Success**:
- [ ] Figures support the thermodynamic stabilization mechanism
- [ ] Data quality meets publication standards
- [ ] Story flows logically from morphology to chemistry to mechanism

---

*This plan provides the roadmap for creating publication-quality ToF-SIMS figures that integrate seamlessly with your broader materials characterization story.*