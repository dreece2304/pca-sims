# Results: ToF-SIMS Analysis of Electron Beam-Induced Chemical Transformations in BTY Alucone

## 3.X ToF-SIMS Characterization of Dose-Dependent Chemical Evolution

Time-of-flight secondary ion mass spectrometry (ToF-SIMS) was employed to investigate the radiation-induced chemical transformations in BTY alucone thin films as a function of electron beam dose. The analysis of 116 positive and 82 negative secondary ion species across five dose levels (500–15,000 μC/cm²) revealed systematic chemical changes consistent with cross-linking, aromatization, and the formation of a protective organic overlayer.

### 3.X.1 Aromatic Formation

The most striking observation was the pronounced increase in aromatic secondary ion fragments with increasing e-beam dose (Figure Xa). The tropylium cation (C₇H₇⁺, m/z 91), a well-established marker for aromatic character in ToF-SIMS analysis of polymers \cite{Nie2017, Petrat1996}, increased by 82.7% from 500 to 15,000 μC/cm² with excellent linearity (R² = 0.96). This fragment is particularly diagnostic as it represents the resonance-stabilized seven-membered aromatic ring commonly formed from benzyl precursors during SIMS ionization \cite{Jusko2018}. The phenyl cation (C₆H₅⁺) and cyclopentadienyl cation (C₅H₅⁺) exhibited parallel increases of 51.7% and 52.3%, respectively, confirming the formation of diverse aromatic ring systems.

To quantify the extent of aromatization, we employed the aromatic index (AI), defined as the intensity ratio C₇H₇⁺/C₄H₇⁺, following the methodology established by Petrat et al. for monitoring aromatic integrity in plasma-modified polymers \cite{Petrat1996}. The AI increased from 0.123 at 500 μC/cm² to 0.215 at 15,000 μC/cm², representing a 74.8% increase (R² = 0.96, p = 0.003). This substantial change indicates that the internal alkyne groups in the BTY backbone undergo radiation-induced cyclization and polymerization to form aromatic structures.

### 3.X.2 Cross-linking Index

The degree of cross-linking was assessed using the ρ parameter (C₆H⁻/C₄H⁻ intensity ratio), a metric recently validated by Nie and coworkers for quantifying cross-link density in polymer thin films \cite{Nie2025, NaderiGohar2017}. Cross-linking fundamentally involves hydrogen abstraction and C–C bond formation between adjacent chains, which increases the local carbon density and manifests as enhanced emission of hydrogen-deficient hydrocarbon fragments \cite{Trebicky2014}. The ρ parameter increased from 0.287 to 0.304 (6.0% increase, R² = 0.87, p = 0.02) over the dose range studied. While this change is modest compared to other metrics, it represents a statistically significant shift toward higher cross-link density.

### 3.X.3 Unsaturation and Double Bond Equivalent Analysis

The intensity-weighted average double bond equivalent (DBE), calculated from the distribution of hydrocarbon fragment ions, provides a measure of overall unsaturation in the material \cite{McLafferty1993, Pellegrin1983}. DBE values increased from 1.07 to 1.22 (14.7% increase, R² = 0.96, p = 0.003), consistent with the conversion of saturated C–H bonds to unsaturated π systems through dehydrogenation and ring formation. This observation aligns with the unsaturation pointer metric, defined as the ratio of hydrogen-deficient fragments (H/C < 1) to total C₂–C₈ hydrocarbon emission \cite{Lianos1994}, which increased by 32.9% (R² = 0.96, p = 0.003).

### 3.X.4 BTY Backbone Consumption

Concurrent with aromatic formation, fragments characteristic of the intact BTY backbone exhibited systematic decreases. The C₃HO⁻ and C₄H₃O⁻ ions, which arise from fragmentation of the –O–CH₂–C≡C–CH₂–O– linker, decreased by 30.1% and 22.7%, respectively. This inverse correlation between backbone and aromatic fragments provides direct evidence that the alkyne-containing linker serves as the reactive site for radiation-induced cross-linking and cyclization chemistry.

### 3.X.5 Aluminum Species and Surface Chemistry

An intriguing asymmetry was observed in the dose-dependent behavior of aluminum-containing fragments: positive mode Al species (Al⁺, AlOH⁺, Al₂O₂Hₓ⁺) collectively decreased by 7.8%, while negative mode Al species (AlO₂⁻, AlO₃Hₓ⁻) increased by 15.7%. This divergent behavior, combined with the 21.6% increase in the C/Al fragment ratio (R² = 0.93, p = 0.008), suggests that the aluminum-oxide framework becomes progressively buried beneath a cross-linked organic overlayer rather than being lost from the film. Such burial would reduce the accessibility of Al species to the primary ion beam while the underlying Al–O network remains structurally intact—a favorable outcome for maintaining resist mechanical integrity.

The strong correlation between H⁻ intensity and total aromatic fragment emission (r = 0.996, p < 0.001; Figure Xb) further supports this interpretation. In ToF-SIMS, secondary ion yields are highly sensitive to the local electronic environment (the "matrix effect") \cite{Weng2016}. The increasing H⁻ signal likely reflects enhanced ionization efficiency on the increasingly conjugated surface rather than an increase in hydrogen content, which would contradict the observed dehydrogenation chemistry.

### 3.X.6 Proposed Mechanism

Taken together, the ToF-SIMS data support a mechanism wherein electron beam irradiation initiates radical formation at the alkyne (C≡C) sites of the BTY backbone, consistent with the known high reactivity of triple bonds toward radiation-induced polymerization \cite{George2008, Lee2013}. These radicals undergo cyclization and intermolecular coupling to form aromatic and cross-linked structures, accompanied by H₂ evolution (Scheme X). The resulting material exhibits the characteristics expected of a negative-tone EUV/e-beam resist: conversion from soluble (intact backbone) to insoluble (cross-linked aromatic network) chemistry upon exposure \cite{Lim2023, Hasan2024}.

---

## Summary Table: ToF-SIMS Derived Metrics

| Metric | Definition | 500 μC/cm² | 15,000 μC/cm² | % Change | R² | p-value |
|--------|------------|------------|---------------|----------|-----|---------|
| Cross-linking index (ρ) | C₆H⁻/C₄H⁻ | 0.287 | 0.304 | +6.0 | 0.87 | 0.021 |
| Aromatic index (AI) | C₇H₇⁺/C₄H₇⁺ | 0.123 | 0.215 | +74.8 | 0.96 | 0.003 |
| Unsaturation pointer | H-deficient/total C₂–C₈ | 0.214 | 0.285 | +32.9 | 0.96 | 0.003 |
| Average DBE | Intensity-weighted | 1.07 | 1.22 | +14.7 | 0.96 | 0.003 |
| C/Al ratio | ΣC fragments/ΣAl fragments | 2.75 | 3.34 | +21.6 | 0.93 | 0.008 |

---

## Figure Captions

**Figure X.** ToF-SIMS analysis of e-beam dose-dependent chemical evolution in BTY alucone thin films. (a) Aromatic fragment formation showing monotonic increases in tropylium (C₇H₇⁺), phenyl (C₆H₅⁺), and cyclopentadienyl (C₅H₅⁺) cations. (b) BTY backbone consumption indicated by decreasing C₃HO⁻ and C₄H₃O⁻ fragment intensities. (c) Aromatic index (C₇H₇⁺/C₄H₇⁺ ratio) evolution. (d) Cross-linking index (ρ = C₆H⁻/C₄H⁻). (e) Intensity-weighted average double bond equivalent. (f) C/Al fragment ratio indicating surface carbon enrichment. Dashed lines represent linear least-squares fits. Error bars represent standard deviation across three measurement patterns.

**Figure X+1.** Correlation between H⁻ intensity and total aromatic fragment signal (C₆H₅⁻ + C₅H₅⁻ + C₆⁻ + C₇⁻) in negative ion mode. Data points are colored by e-beam dose. The strong positive correlation (r = 0.996) suggests matrix-enhanced ionization on the increasingly aromatic surface rather than increased hydrogen content.

---

## References

See accompanying BibTeX file for complete citation information.
