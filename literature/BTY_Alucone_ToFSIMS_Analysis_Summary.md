# ToF-SIMS Analysis of E-beam Irradiated BTY Alucone
## Comprehensive Summary with Suggested Visuals and Literature Support

---

## 1. Executive Summary

This analysis examined dose-dependent chemical transformations in BTY alucone (TMA + 2-butyne-1,4-diol) thin films under e-beam irradiation from 500–15,000 μC/cm². ToF-SIMS revealed clear evidence of:

1. **Aromatic ring formation** from alkyne polymerization/cyclization
2. **BTY backbone consumption** as starting material is transformed
3. **Aluminum burial** rather than loss (asymmetric +/- ion behavior)
4. **Matrix effects** correlating H⁻ yield with surface aromaticity

---

## 2. Key Findings Summary

### 2.1 Aromatic Formation (Cross-linking Evidence)

| Fragment | Assignment | % Change | R² | Significance |
|----------|------------|----------|-----|--------------|
| C₇H₇⁺ | Tropylium cation | +83% | 0.96 | Classic aromatic marker |
| C₆H₅⁺ | Phenyl cation | +52% | 0.94 | Benzene ring formation |
| C₆H₆⁺ | Benzene M⁺ | +72% | 0.93 | Molecular aromatic |
| C₅H₅⁺ | Cyclopentadienyl | +52% | 0.91 | 5-membered ring |
| C₆H₅⁻ | Phenyl anion | +103% | 0.97 | Confirms aromatization |

**Interpretation:** Alkyne (C≡C) polymerization/cyclization creates benzene and cyclopentadiene rings with highly linear dose response.

### 2.2 BTY Backbone Consumption

| Fragment | Assignment | % Change | Significance |
|----------|------------|----------|--------------|
| C₃HO⁻ | Backbone fragment | -30% | Major BTY signature decreasing |
| C₄H₃O⁻ | Oxygenated BTY | -23% | Linker being consumed |
| C₃H₃O⁺ | BTY fragment | -11% | Backbone transformation |
| C₄H₂O₂⁻ | Dioxygenated C4 | -34% | Strongest backbone decrease |

**Interpretation:** Starting material signatures decrease as cross-linking reactions consume the linear BTY backbone.

### 2.3 Aluminum Species Asymmetry

| Polarity | Species | % Change | Observation |
|----------|---------|----------|-------------|
| Positive | Total Al signal | -7.8% | Surface Al less accessible |
| Positive | AlH⁺ | -18% | Largest positive decrease |
| Positive | Al₂O₂H₂⁺ | -19% | Larger clusters decrease more |
| Negative | Total Al signal | +15.7% | Subsurface Al still detected |
| Negative | AlO₂⁻ | +18% | Oxidized Al increasing |

**Interpretation:** Al is NOT being lost (would show decrease in both polarities). Instead, Al is being buried under a cross-linked organic layer and/or fragmentation patterns change due to more conjugated bonding environment.

### 2.4 Matrix Effects

- H⁻ increases +26% and correlates with aromatics (r = 0.996)
- C/Al ratio increases from 1.77 → 2.16 (positive mode)
- Indicates increasing organic character at surface

### 2.5 Oxygenated Aromatics

| Fragment | % Change | Possible Structure |
|----------|----------|-------------------|
| C₅HO⁺ | +69% | Furan-type |
| C₆H₄O⁺ | +64% | Phenol/aryl ether |
| C₆H₆O⁺ | +48% | Phenol M⁺ |

**Interpretation:** Formation of stable aromatic ethers and O-heterocycles contributes to resist stability and insolubility.

---

## 3. Proposed Chemical Mechanism

```
Low Dose (500 μC/cm²)              High Dose (15000 μC/cm²)
                                    
–Al–O–CH₂–C≡C–CH₂–O–Al–            Aromatic/conjugated network
       │                                   ╱  │  ╲
       │  e-beam                         C₆  C₅  C₇ (benzene, Cp, tropylium)
       │  • H₂ loss                       │   │   │
       ↓  • alkyne polymerization         └───┴───┘ ← cross-linked surface
          • ring formation                    │
                                        –Al–O–···–O–Al– ← buried Al-O network
```

**Key transformations:**
1. Alkyne (C≡C) serves as primary reactive site
2. Dehydrogenation releases H₂
3. Ring formation via cyclization (C5, C6, C7 rings)
4. Cross-linking between polymer chains
5. Al-O framework buried beneath aromatic overlayer

---

## 4. Suggested Figures and Tables

### Figure 1: Dose-Dependent Trends by Fragment Family
**Type:** Multi-panel line plot with error bars
**Content:**
- Panel A: Aromatic fragments (C₅H₅⁺, C₆H₅⁺, C₆H₆⁺, C₇H₇⁺) vs dose
- Panel B: BTY backbone fragments (C₃HO⁻, C₄H₃O⁻) vs dose  
- Panel C: Al species comparison (Al⁺, AlH⁺ positive vs AlO₂⁻, AlO⁻ negative)
- X-axis: E-beam dose (μC/cm²)
- Y-axis: Normalized intensity (to SQ1) or absolute intensity
- Error bars: Standard deviation from P1/P2/P3 replicates
- Include R² values for linear fits

### Figure 2: Fragment Ratio Analysis
**Type:** Line plot with separate panels
**Content:**
- Panel A: C/Al ratio vs dose (shows organic enrichment)
- Panel B: Aromatic/Aliphatic ratio (C₇H₇⁺/C₄H₇⁺) vs dose
- Panel C: C₆H₆⁺/C₄H₆⁺ ratio vs dose
- Panel D: AlO₂⁻/Al⁺ ratio vs dose

### Figure 3: H⁻ Correlation with Aromatization
**Type:** Scatter plot with linear regression
**Content:**
- X-axis: Total aromatic fragment intensity
- Y-axis: H⁻ intensity
- Show r² = 0.99 and equation
- Data points labeled by dose
- Supports matrix effect interpretation

### Figure 4: Chemical Summary Schematic
**Type:** Cartoon/diagram
**Content:**
- Before/after illustration of BTY structure
- Show alkyne → aromatic transformation
- Indicate Al "burial" concept with depth indication
- Include key fragment assignments with arrows

### Figure 5: Positive/Negative Ion Asymmetry
**Type:** Bar chart or diverging bar plot
**Content:**
- Al-containing species grouped by fragment
- Show % change for both positive (left) and negative (right)
- Highlight the asymmetry visually
- Color code: red for decrease, blue for increase

### Table 1: Complete Fragment Assignment
**Content:** All 198 fragments with:
- m/z value
- Formula assignment
- Family classification
- % change (SQ1→SQ5)
- R² for linear fit
- Chemical interpretation
- Flag duplicate masses with resolution

### Table 2: Fragment Family Statistics
| Family | N fragments | Avg % Change | Key Species | Trend |
|--------|-------------|--------------|-------------|-------|
| Aromatic (C6+) | 16 pos, 12 neg | +61% | C₇H₇⁺, C₆H₅⁻ | ↑↑ |
| Cyclopentadienyl | 9 pos, 6 neg | +48% | C₅H₅⁺ | ↑↑ |
| BTY backbone | 8 pos, 10 neg | -15% | C₃HO⁻, C₄H₃O⁻ | ↓ |
| Al-oxide (pos) | 9 | -5% | Al⁺, AlOH⁺ | ↓ |
| Al-oxide (neg) | 9 | +15% | AlO₂⁻ | ↑ |

### Table 3: Quantitative Metrics
| Metric | SQ1 (500) | SQ2 (2500) | SQ3 (5000) | SQ4 (10000) | SQ5 (15000) |
|--------|-----------|------------|------------|-------------|-------------|
| C/Al ratio (pos) | 1.77 | 1.86 | 1.95 | 2.06 | 2.16 |
| C/Al ratio (neg) | 5.41 | 5.61 | 5.83 | 6.04 | 6.24 |
| Total aromatic | 0.0123 | 0.0156 | 0.0178 | 0.0201 | 0.0224 |
| H⁻ fraction | 31.8% | 31.3% | 32.3% | 32.7% | 33.0% |

### Supplementary: Heat Map
**Type:** Color-coded intensity matrix
**Content:**
- All fragments (rows) vs dose (columns)
- Color scale: blue (decrease) → white (stable) → red (increase)
- Sorted by fragment family or trend direction
- Hierarchical clustering optional

---

## 5. Quantitative Metrics

### 5.1 Double Bond Equivalent (DBE)

**Formula:** DBE = (2C + 2 + N - H - X) / 2

| Fragment | Formula | DBE | Interpretation |
|----------|---------|-----|----------------|
| BTY core | C₄H₄ | 3 | One triple bond |
| Benzene | C₆H₆ | 4 | Aromatic ring (1 ring + 3 DB) |
| Tropylium | C₇H₇⁺ | 4 | Aromatic 7-membered ring |
| Cyclopentadienyl | C₅H₅ | 3 | Cyclic + 2 double bonds |
| Phenyl | C₆H₅ | 4.5 | Aromatic + radical |

**Application:** Calculate intensity-weighted average DBE across all fragments at each dose. Expect increase with aromatization.

### 5.2 H/C Ratio
- Starting BTY: H/C = 6/4 = 1.5
- Benzene: H/C = 6/6 = 1.0  
- Tropylium: H/C = 7/7 = 1.0

**Application:** Calculate weighted H/C from fragment intensities. Should decrease with dose as dehydrogenation occurs.

### 5.3 Key Fragment Ratios

| Ratio | What it Indicates | Expected Trend | Literature Support |
|-------|-------------------|----------------|-------------------|
| C₇H₇⁺/C₄H₇⁺ | Aromatic/aliphatic balance | Increase | Petrat et al. [52] |
| C₆H₆⁺/C₄H₆⁺ | Ring formation extent | Increase | - |
| AlO₂⁻/Al⁺ | Al environment change | Increase | - |
| C₄H₃⁻/C₄H₇⁺ | Dehydrogenation extent | Increase | - |
| ΣAromatic/ΣAliphatic | Overall aromatization | Increase | Leggett et al. [20] |

---

## 6. Literature Support

### 6.1 ToF-SIMS Fundamentals and Polymer Analysis

**Key Reference:** Mei et al. (2022) "Characterization of polymeric surfaces and interfaces using time-of-flight secondary ion mass spectrometry" *Journal of Polymer Science*
- Comprehensive review of ToF-SIMS for polymer analysis
- Discusses matrix effects and ionization probability variations
- Notes that secondary ion yields depend on chemical environment

**Key Reference:** Chan & Weng (2014) "Polymer surface structures determined using ToF-SIMS" *Reviews in Analytical Chemistry* 33: 11-30
- Foundational polymer ToF-SIMS methodology
- Fragment identification strategies

### 6.2 Aromatic Fragment Identification (Tropylium, Phenyl)

**Key Reference:** Ng et al. (2018) "ToF-SIMS and computation analysis: Fragmentation mechanisms of polystyrene, polystyrene-d5, and polypentafluorostyrene" *Surface and Interface Analysis*
- C₇H₇⁺ (tropylium) confirmed as resonance-stabilized aromatic marker
- C₆H₅⁺ and C₅H₅⁺ fragmentation mechanisms elucidated
- Computational validation of fragment structures

**Key Reference:** Petrat et al. (1994) - Referenced in SIMS literature
- **Critical finding:** C₇H₇⁺/C₄H₇⁺ ratio monitors aromatic system integrity
- Tropylium (m/z 91) = aromatic indicator
- C₄H₇⁺ (m/z 55) = aliphatic indicator
- Widely used metric for plasma-modified polymers

**Key Reference:** Wikipedia/Grokipedia - Tropylium cation
- m/z = 91 is standard mass spec signature for aromatics
- 6 π-electrons satisfy Hückel's rule
- Formed by rearrangement of benzyl cation

### 6.3 Fragment Ratios and Structural Indicators

**Key Reference:** Lianos (1994) "Surface structural studies of polyethylene, polypropylene and their copolymers with ToF SIMS" *Surface and Interface Analysis*
- **Key metric:** Ratio of hydrogen-deficient fragments to total C2-C8 clusters indicates unsaturation
- C6-C8 cluster emission indicates branching

**Key Reference:** Oran et al. - SIMS structural indicators for plasma polymers
- Sum of aromatic ion intensities (Σarom) as aromaticity indicator
- Cross-linking and unsaturation detectable via fragment patterns

**Key Reference:** Leggett et al. (1995) - Plasma-polymerized styrene
- SSIMS sensitive to cross-linked and unsaturated content
- Structural comparison between conventional and plasma-polymerized PS

### 6.4 Double Bond Equivalent (DBE) and Aromaticity Index

**Key Reference:** Koch & Dittmar (2006) "From mass to structure: an aromaticity index for high-resolution mass data of natural organic matter" *Rapid Communications in Mass Spectrometry* 20(5): 926-932
- Introduced aromaticity index (AI) for mass spectrometry
- DBE/C > 0.5 indicates aromatic compounds
- DBE/C > 0.67 indicates condensed aromatics
- Widely adopted in FT-ICR-MS and applicable to SIMS

**Key Reference:** Pellegrin (1983) "Molecular formulas of organic compounds: the nitrogen rule and degree of unsaturation" *Journal of Chemical Education* 60(8): 626
- Classic DBE calculation methodology
- Foundation for unsaturation analysis

**Key Reference:** Abdullah et al. (2013) "Investigation on Aromaticity Index and Double-Bond Equivalent of Aromatic Compounds" *Journal of Chemistry*
- AI = (1 + C - O - S - 0.5H) / (C - O - S - N - P)
- DBE = Σ(Ni × Vi)/2 - (N/2) + 1
- Applied to predict aromatic character from molecular formula

### 6.5 Matrix Effects in ToF-SIMS

**Key Reference:** JASMS (2022) "ToF-SIMS Depth Profiling... in Atmospheres of H2, C2H2, CO, and O2"
- Matrix effect defined: substrate affects ionization probability
- Can increase or decrease positive/negative ion yields
- Aromatic surfaces have different ionization characteristics

**Key Reference:** Cesium ionization studies
- Cs enhances negative ionization probability
- Aromatic samples show different sputter behavior than aliphatic

### 6.6 Radiation Chemistry of Polymers

**Key Reference:** Hill "Radiation Chemistry of Polymers" *Wiley Major Reference Works*
- Polymers either cross-link or degrade under radiation
- **Critical:** Aromatic groups reduce overall reaction yield (radiation protection)
- Cross-linking vs. scission depends on polymer structure

**Key Reference:** IAEA-TECDOC-1420 "Advances in radiation chemistry of polymers"
- Comprehensive review of radiation-induced cross-linking
- Electron beam mechanisms

**Key Reference:** Cross-linking of polymers by various radiations (2022) ResearchGate
- Presence of unsaturation (C=C) increases radical formation
- Addition mechanism follows from unsaturated bonds

### 6.7 EUV/E-beam Resist Mechanisms

**Key Reference:** Le et al. (2025) "In Situ Analysis of Electron-Induced Chemical Transformations in Vapor-Phase-Synthesized Al-Based Inorganic-Organic Hybrid Thin Films for EUV Resist Platform" *ACS Applied Materials & Interfaces*
- **Directly relevant:** Al-based MLD films (TMA + hydroquinone)
- Cross-linking pathways analyzed by XPS, Raman, FTIR
- Negative tone behavior in TMAH developer

**Key Reference:** Lockyer et al. (2022) "SIMS Analysis of Thin EUV Photoresist Films" *Analytical Chemistry*
- ToF-SIMS and OrbiTrap-SIMS for resist analysis
- PAG fragmentation under EUV exposure
- Gas cluster ion beam for minimal damage

**Key Reference:** Naqvi et al. (2024) "EUV Lithographic Performance and Reaction Mechanism of Polymeric Resist—Utilizing Radical- and Acid-Amplified Cross-Linking" *Chemistry of Materials*
- Secondary electron generation in EUV
- Radical cross-linking mechanisms
- Bond scission vs. cross-linking balance

**Key Reference:** MDPI (2024) "Recent Advances in Metal-Oxide-Based Photoresists for EUV Lithography"
- EUV photon (92 eV) ionizes resist matrix
- Secondary electron cascade
- Cross-linking from reactive species

### 6.8 Alkyne Polymerization and Cyclization

**Key Reference:** Wikipedia - Alkyne trimerisation
- [2+2+2] cycloaddition forms benzene rings from alkynes
- Highly exergonic (ΔG = -142 kcal/mol)
- Metal catalysts enable reaction at lower temperatures
- Tethered triynes form fused ring systems

**Key Reference:** Nature Chemistry (2023) "The role of aromaticity in cyclization and polymerization of alkyne-substituted porphyrins"
- On-surface alkyne cyclization reactions
- Aromaticity affects reactivity
- STM/AFM evidence for ring formation

**Key Reference:** ACS Nano (2024) "Understanding Electron Beam-Induced Chemical Polymerization Processes"
- E-beam induced polymerization of small organics
- DFT calculations support radical mechanisms
- Cross-section calculations for ionization

---

## 7. Certainty Assessment

### Definitive (Strong evidence)
✓ Aromatic species (C₅H₅⁺, C₆H₅⁺, C₆H₆⁺, C₇H₇⁺) increase with dose  
✓ BTY backbone fragments (C₃HO⁻, C₄H₃O⁻) decrease with dose  
✓ Dose response is monotonic and highly linear (R² > 0.9)  
✓ Positive Al decreases while negative Al increases (asymmetry)  
✓ H⁻ correlates with aromatic formation (r = 0.996)  

### Probable (Supported but not proven)
? Al is buried rather than lost (consistent with asymmetry + C/Al ratio)  
? Alkyne (C≡C) is primary radiation chemistry site  
? Cross-linking causes the solubility switch to insoluble  
? Oxygenated aromatics (furans, phenols) contribute to stability  

### Uncertain (Requires additional experiments)
? Exact aromatic structures formed (benzene vs. fused rings vs. polycyclic)  
? Whether any Al-O bonds break or just become inaccessible  
? Quantitative oxygen loss (CO/CO₂ evolution not measured)  
? Depth distribution of species (would need depth profiling)  
? Role of radicals vs. ionic mechanisms  

---

## 8. Recommended Additional Experiments

1. **XPS depth profiling** - Confirm Al burial with depth-resolved Al 2p spectra
2. **Raman spectroscopy** - Detect aromatic C=C stretching at ~1600 cm⁻¹
3. **FTIR** - Monitor alkyne C≡C disappearance at ~2100 cm⁻¹
4. **Residual gas analysis** - Quantify H₂, CO, CO₂ evolution during exposure
5. **AFM/nanoindentation** - Correlate mechanical properties with cross-linking
6. **ToF-SIMS depth profiling** - Map chemical gradients with depth

---

## 9. References (Organized by Topic)

### ToF-SIMS Methodology
1. Mei et al. (2022) J. Polym. Sci. - ToF-SIMS polymer characterization review
2. Chan & Weng (2014) Rev. Anal. Chem. 33:11-30 - Polymer surface structures
3. Lianos (1994) Surf. Interface Anal. - Polyolefin structural studies

### Aromatic Fragments
4. Ng et al. (2018) Surf. Interface Anal. - Polystyrene fragmentation mechanisms
5. Petrat et al. (1994) - C₇H₇⁺/C₄H₇⁺ ratio for aromaticity
6. Kawashima et al. (2014) Surf. Interface Anal. - PS fragment ion analysis

### DBE and Aromaticity
7. Koch & Dittmar (2006) Rapid Commun. Mass Spectrom. 20:926-932 - Aromaticity index
8. Pellegrin (1983) J. Chem. Educ. 60:626 - DBE calculations
9. Abdullah et al. (2013) J. Chem. - AI and DBE for aromatics

### Radiation Chemistry
10. Hill - Radiation Chemistry of Polymers (Wiley)
11. IAEA-TECDOC-1420 - Advances in radiation chemistry of polymers
12. Cross-linking mechanisms (2022) ResearchGate

### EUV/E-beam Resists
13. Le et al. (2025) ACS Appl. Mater. Interfaces - Al-based MLD resists
14. Lockyer et al. (2022) Anal. Chem. - SIMS of EUV photoresists
15. Naqvi et al. (2024) Chem. Mater. - Radical/acid cross-linking
16. MDPI (2024) - Metal-oxide photoresists review

### Alkyne Chemistry
17. Wikipedia - Alkyne trimerisation
18. Nature Chemistry (2023) - Alkyne cyclization on surfaces
19. ACS Nano (2024) - E-beam polymerization mechanisms

---

*Document prepared: November 2025*
*Analysis of ToF-SIMS data from BTY alucone e-beam exposure series*
