#!/usr/bin/env python3
"""
Positive Ion Analysis for Alucone Resist Study
Cross-correlation with negative ion findings
"""

# import pandas as pd
# import numpy as np
from src.positive_fragment_database import AluconePositiveFragmentDatabase
import os

def analyze_positive_ion_data():
    """Analyze positive ion data and cross-correlate with negative ion findings"""
    
    print("🔬 POSITIVE ION ANALYSIS FOR ALUCONE RESIST")
    print("="*60)
    
    # Initialize positive fragment database
    pos_db = AluconePositiveFragmentDatabase()
    
    # Check available positive ion data files
    pos_data_files = []
    data_dir = "data"
    
    if os.path.exists(f"{data_dir}/PosDataNorm.xlsx"):
        pos_data_files.append("PosDataNorm.xlsx")
    if os.path.exists(f"{data_dir}/PosPeakList.xlsx"):
        pos_data_files.append("PosPeakList.xlsx")
    
    print(f"📊 Available positive ion data files:")
    for file in pos_data_files:
        print(f"   • {file}")
    
    print(f"\\n🧪 EXPECTED MAJOR POSITIVE ION FRAGMENTS:")
    print("-" * 50)
    
    major_fragments = pos_db.get_expected_major_fragments()
    for frag_name in major_fragments:
        if frag_name in pos_db.fragments:
            frag = pos_db.fragments[frag_name]
            print(f"{frag['formula']:>8} | m/z {frag['mz']:>7.4f} | {frag['description']}")
    
    print(f"\\n🔗 POSITIVE-NEGATIVE ION CORRELATIONS:")
    print("-" * 50)
    
    counterparts = pos_db.get_negative_ion_counterparts()
    
    key_correlations = [
        ("Al+", "Al-", "Aluminum chemistry validation"),
        ("C6H+", "C6H-", "Aromatic formation (crosslinking indicator)"),
        ("C4H+", "C4H-", "Reference ion comparison"),
        ("CHO+", "CHO-", "Aldehyde formation from diol degradation"),
        ("H+", "H-", "Hydrogen radical chemistry"),
        ("COOH+", "COOH-", "Carboxyl formation mechanism"),
        ("C2HO+", "C2HO-", "Ketene formation validation")
    ]
    
    print("Expected correlations for mechanism validation:")
    for pos_ion, neg_ion, description in key_correlations:
        if pos_ion in pos_db.fragments:
            pos_mz = pos_db.fragments[pos_ion]["mz"]
            print(f"   {pos_ion:>6} (m/z {pos_mz:>7.4f}) ↔ {neg_ion:>6} | {description}")
    
    print(f"\\n⚡ ALUMINUM CHEMISTRY FOCUS:")
    print("-" * 40)
    print("Aluminum fragments should be PROMINENT in positive mode:")
    
    al_fragments = pos_db.get_aluminum_fragments()
    for name, frag in al_fragments.items():
        trend_desc = frag["expected_trend"].replace("_", " ")
        print(f"   {frag['formula']:>10} | m/z {frag['mz']:>7.4f} | {trend_desc}")
    
    print(f"\\n📈 PREDICTED DOSE TRENDS:")
    print("-" * 30)
    
    trends = pos_db.predict_dose_trends()
    
    print("INCREASE with e-beam dose:")
    for frag in trends["increase_with_dose"][:8]:  # Show first 8
        if frag in pos_db.fragments:
            formula = pos_db.fragments[frag]["formula"]
            print(f"   • {formula} - {pos_db.fragments[frag]['description']}")
    
    print("\\nDECREASE with e-beam dose:")
    for frag in trends["decrease_with_dose"][:8]:  # Show first 8  
        if frag in pos_db.fragments:
            formula = pos_db.fragments[frag]["formula"]
            print(f"   • {formula} - {pos_db.fragments[frag]['description']}")
    
    return pos_db

def cross_validate_mechanisms():
    """Cross-validate mechanisms between positive and negative ion data"""
    
    print(f"\\n🔍 MECHANISM CROSS-VALIDATION STRATEGY:")
    print("="*50)
    
    validation_tests = [
        {
            "mechanism": "Aromatic Formation (Thermodynamic Stabilization)",
            "negative_evidence": "C6H- increases +154% (strongest increase)",
            "positive_prediction": "C6H+ should also increase strongly",
            "validation_method": "Compare C6H+/C4H+ ratio with C6H-/C4H- ratio"
        },
        {
            "mechanism": "Carbonyl Cascade (C4HO- → C3HO- → C2HO- → COOH-)",
            "negative_evidence": "All carbonyls increase: C4HO-(+119%), C3HO-(+69%), C2HO-(+52%), COOH-(+98%)",
            "positive_prediction": "Positive carbonyl counterparts should show similar trends",
            "validation_method": "Track CHO+, COOH+, C2HO+ dose progressions"
        },
        {
            "mechanism": "Hydrogen Radical Chemistry",
            "negative_evidence": "H- decreases -28% (consumed in stabilization)",
            "positive_prediction": "H+ should show complementary behavior",
            "validation_method": "Compare H+ vs H- dose trends"
        },
        {
            "mechanism": "HCl Development Validation",
            "negative_evidence": "Cl- isotopes decrease (crosslinking resists HCl)",
            "positive_prediction": "Should NOT see Cl+ (HCl produces Cl-, not Cl+)",
            "validation_method": "Confirm absence of significant Cl+ signals"
        },
        {
            "mechanism": "Aluminum Network Integrity",
            "negative_evidence": "Al- signal absent (supports C2HO- over AlCH2- assignment)",
            "positive_prediction": "Al+ should be detectable and stable/decreasing",
            "validation_method": "Quantify Al+ levels and dose trends"
        }
    ]
    
    for i, test in enumerate(validation_tests, 1):
        print(f"\\n{i}. {test['mechanism']}")
        print(f"   Negative evidence: {test['negative_evidence']}")
        print(f"   Positive prediction: {test['positive_prediction']}")
        print(f"   Validation: {test['validation_method']}")
    
    print(f"\\n🎯 CRITICAL VALIDATION TARGETS:")
    print("-" * 35)
    print("1. Al+ presence/absence (resolves m/z 41.0036 identity)")
    print("2. C6H+ dose trend (validates aromatic mechanism)")  
    print("3. CHO+/COOH+ trends (validates carbonyl cascade)")
    print("4. Si+ levels (substrate interference check)")
    print("5. Overall positive vs negative ion correlation")

def analyze_unknown_68_validation():
    """Specific validation strategy for mysterious m/z 68.9984"""
    
    print(f"\\n🔍 VALIDATION STRATEGY FOR m/z 68.9984 (Unknown):")
    print("="*55)
    
    candidates = [
        {
            "identity": "CF2H-",
            "positive_check": "Look for CF2H+ at m/z 68.9950",
            "validation": "Fluorine contamination should appear in both modes"
        },
        {
            "identity": "C3HO2-", 
            "positive_check": "Look for C3HO2+ at m/z 69.0027",
            "validation": "Radical products should have positive counterparts"
        },
        {
            "identity": "Al13C-",
            "positive_check": "Look for Al+ (m/z 26.9815) and 13C isotope patterns",
            "validation": "Aluminum presence confirms Al-carbon fragments possible"
        },
        {
            "identity": "C5H-",
            "positive_check": "Look for C5H+ at m/z 61.0078",
            "validation": "Hydrocarbon fragments appear in both modes"
        }
    ]
    
    print("Validation matrix for m/z 68.9984 candidates:")
    for candidate in candidates:
        print(f"\\n   If {candidate['identity']}:")
        print(f"      Check: {candidate['positive_check']}")
        print(f"      Logic: {candidate['validation']}")
    
    print(f"\\n🧪 RECOMMENDED ANALYSIS WORKFLOW:")
    print("-" * 40)
    print("1. Load positive ion data into PCA analysis")
    print("2. Identify major positive ion fragments")
    print("3. Cross-correlate with verified negative fragments") 
    print("4. Validate thermodynamic stabilization mechanism")
    print("5. Resolve m/z 68.9984 and other unknowns")
    print("6. Generate comprehensive positive-negative correlation report")

def main():
    """Main analysis function"""
    pos_db = analyze_positive_ion_data()
    cross_validate_mechanisms()
    analyze_unknown_68_validation()
    
    print(f"\\n✅ POSITIVE ION DATABASE CREATED")
    print(f"   • {len(pos_db.fragments)} expected fragments catalogued")
    print(f"   • Aluminum fragments: {len(pos_db.get_aluminum_fragments())}")
    print(f"   • Organic fragments: {len(pos_db.get_organic_fragments())}")
    print(f"   • Cross-validation targets identified")
    
    print(f"\\n🚀 NEXT STEPS:")
    print("   1. Modify GUI to handle positive ion data")
    print("   2. Run PCA analysis on positive ion data")  
    print("   3. Execute cross-validation analysis")
    print("   4. Generate final positive-negative correlation report")

if __name__ == "__main__":
    main()