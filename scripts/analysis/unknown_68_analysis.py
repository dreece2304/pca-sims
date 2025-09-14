#!/usr/bin/env python3
"""
Systematic analysis of mysterious m/z 68.9984 fragment
High loading (0.030378) with strong dose increase (+122%)
"""

def analyze_unknown_68_9984():
    """Systematic analysis of the m/z 68.9984 fragment"""
    
    mz_target = 68.9984
    print(f"🔍 SYSTEMATIC ANALYSIS: m/z {mz_target}")
    print("="*50)
    
    # Check for potential chemical identities
    potential_identities = [
        # Silicon-based (substrate related)
        (67.9719, "SiO2-", "Silicon dioxide anion", "substrate_interference"),
        (67.9668, "SiO2-", "Silicon dioxide (alt calc)", "substrate_interference"), 
        
        # Aluminum-based combinations
        (68.9714, "AlO2-", "Aluminum dioxide", "alucone_degradation"),
        (68.9893, "Al13C-", "Aluminum-carbon (13C)", "metal_organic"),
        
        # Organic combinations from alucone
        (69.0340, "C4H5O-", "Organic fragment with oxygen", "polymer_degradation"),
        (68.0262, "C4H4O-", "Dehydrated diol fragment", "linker_degradation"),
        (69.0027, "C3HO2-", "Three-carbon dioxy", "radical_product"),
        
        # Chlorinated species
        (68.9689, "ClO2-", "Chlorine dioxide", "hcl_chemistry"),
        (70.9659, "37ClO-", "Chlorine-37 oxide", "hcl_oxidation"),
        
        # Complex organics
        (69.0078, "C5H-", "Five-carbon chain", "crosslinking"),
        (67.0184, "C4H3O-", "Unsaturated organic", "degradation"),
        
        # Contamination possibilities
        (69.9580, "ClF-", "Chlorine fluoride", "contamination"),
        (68.9950, "CF2H-", "Difluoromethyl", "fluorine_contamination")
    ]
    
    print("🧪 POTENTIAL CHEMICAL IDENTITIES:")
    print("-" * 40)
    
    best_matches = []
    
    for ref_mass, formula, description, category in potential_identities:
        mass_diff = abs(mz_target - ref_mass)
        confidence = "HIGH" if mass_diff < 0.005 else "MEDIUM" if mass_diff < 0.01 else "LOW"
        
        print(f"{formula:>12} | {ref_mass:>8.4f} | Δ{mass_diff:>6.4f} | {confidence:>6} | {description}")
        
        if mass_diff < 0.02:  # Keep reasonable candidates
            best_matches.append((mass_diff, formula, description, category, confidence))
    
    # Sort by mass accuracy
    best_matches.sort(key=lambda x: x[0])
    
    print(f"\n🎯 BEST CANDIDATES (within ±0.02 Da):")
    print("-" * 50)
    
    for mass_diff, formula, description, category, confidence in best_matches[:5]:
        print(f"✅ {formula}: {description}")
        print(f"   Δ{mass_diff:.4f} Da | {confidence} confidence | Category: {category}")
        
        # Chemical reasoning
        if "SiO2" in formula:
            print("   💡 Silicon substrate interference - could explain consistent presence")
        elif "AlO2" in formula:
            print("   💡 Aluminum oxide formation - expected with e-beam processing")
        elif "C4H5O" in formula or "C4H4O" in formula:
            print("   💡 Organic degradation from diol linker - fits dose trend")
        elif "Cl" in formula:
            print("   💡 HCl development chemistry byproduct")
        
        print()
    
    print("🔬 VERIFICATION STRATEGY:")
    print("-" * 30)
    print("1. Check for Al+ in positive ion mode (if AlO2-)")
    print("2. Look for Si+ substrate signals (if SiO2-)")
    print("3. Examine C4H5+ or C4H4+ in positive mode (if organic)")
    print("4. Search for isotope patterns (Si, Al have isotopes)")
    print("5. Compare with blank Si substrate sample")
    
    print(f"\n📊 DOSE TREND ANALYSIS:")
    print("-" * 25)
    print("Strong increase (+122%) suggests:")
    print("• NOT substrate interference (would be constant)")
    print("• NOT simple contamination (would decrease)")
    print("• LIKELY: Chemical transformation product")
    print("• POSSIBLE: Metal oxide formation (Al2O3 → AlO2-)")
    print("• POSSIBLE: Organic degradation product")
    
    return best_matches

def check_isotope_expectations():
    """Check what isotope patterns we should expect"""
    
    print(f"\n🧬 ISOTOPE PATTERN EXPECTATIONS:")
    print("="*40)
    
    isotope_patterns = {
        "Silicon": {
            "28Si": "92.2%", "29Si": "4.7%", "30Si": "3.1%",
            "expected_partners": ["69.9984 (29Si)", "70.9984 (30Si)"]
        },
        "Aluminum": {
            "27Al": "100%", 
            "expected_partners": ["No isotopes - monoisotopic"]
        },
        "Carbon": {
            "12C": "98.9%", "13C": "1.1%",
            "expected_partners": ["69.9984 or 70.9984 (+1 or +2 Da)"]
        }
    }
    
    for element, info in isotope_patterns.items():
        print(f"\n{element}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

def main():
    """Main analysis function"""
    best_matches = analyze_unknown_68_9984()
    check_isotope_expectations()
    
    print(f"\n🎯 RECOMMENDATION:")
    print("="*30)
    print("TOP CANDIDATES for m/z 68.9984:")
    print("1. AlO2- (aluminum dioxide) - fits alucone system")
    print("2. C4H5O- (organic degradation) - fits dose trend") 
    print("3. SiO2- (substrate interference) - but dose trend argues against")
    print("\nNEXT STEPS:")
    print("• Check positive ion mode for Al+, Si+, C4H5+")
    print("• Look for isotope partners around m/z 70-71")
    print("• Compare with substrate-only reference")

if __name__ == "__main__":
    main()