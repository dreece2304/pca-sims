#!/usr/bin/env python3
"""
Simple analysis of unassigned fragments without pandas dependency
"""

def analyze_fragments():
    """Analyze the top unassigned fragments"""
    
    # Top unassigned fragments from the CSV (manually extracted)
    unassigned_fragments = [
        (1.0085, 0.300180, "2nd highest loading!"),
        (34.9699, 0.239048, "3rd highest loading"),  
        (23.9999, 0.231786, "4th highest loading"),
        (59.9852, 0.216935, "5th highest loading"),
        (75.9745, 0.170791, "High loading"),
        (76.9827, 0.162672, "High loading"), 
        (18.9991, 0.151257, "Significant loading"),
        (36.9669, 0.079838, "Moderate loading"),
        (12.0006, 0.077154, "Moderate loading"),
        (41.0036, 0.076398, "Moderate loading"),
        (47.9993, 0.056001, "Moderate loading"),
        (44.9981, 0.047206, "Low-moderate loading")
    ]
    
    print("=== CRITICAL UNASSIGNED FRAGMENTS ANALYSIS ===")
    print(f"Analyzing {len(unassigned_fragments)} high-impact unassigned fragments")
    print("These need immediate attention due to high PC1 loadings!")
    print()
    
    assignments = []
    
    for mz, loading, importance in unassigned_fragments:
        identity = identify_fragment_simple(mz)
        assignments.append((mz, loading, identity))
        
        print(f"m/z {mz:.4f} (Loading: {loading:.6f}) - {importance}")
        print(f"  🔍 PROPOSED: {identity['name']} ({identity['formula']})")
        print(f"  📋 {identity['description']}")
        print(f"  ⭐ Confidence: {identity['confidence']}")
        print(f"  💡 {identity['notes']}")
        print()
    
    return assignments

def identify_fragment_simple(mz):
    """Simple fragment identification based on m/z"""
    
    # High-confidence assignments based on exact masses
    if abs(mz - 1.0078) < 0.01:
        return {
            'name': 'H-',
            'formula': 'H-', 
            'description': 'Hydrogen anion - very common in negative ToF-SIMS',
            'confidence': 'Very High',
            'notes': '⚠️ CRITICAL: 2nd highest loading! Indicates strong hydrogen activity'
        }
    
    elif abs(mz - 34.9689) < 0.01:
        return {
            'name': 'Cl-',
            'formula': '35Cl-',
            'description': 'Chlorine-35 anion - contamination from processing',
            'confidence': 'Very High', 
            'notes': '🚨 MAJOR CONTAMINATION: Chlorine from cleaning/processing chemicals'
        }
    
    elif abs(mz - 36.9659) < 0.01:
        return {
            'name': 'Cl- (heavy)',
            'formula': '37Cl-',
            'description': 'Chlorine-37 anion - heavy isotope of chlorine',
            'confidence': 'Very High',
            'notes': '🔗 ISOTOPE PAIR: Confirms Cl- contamination (isotope ratio should be ~3:1)'
        }
        
    elif abs(mz - 18.9984) < 0.01:
        return {
            'name': 'F-',
            'formula': 'F-',
            'description': 'Fluorine anion - processing contamination',
            'confidence': 'Very High',
            'notes': '⚠️ FLUORINE CONTAMINATION: From cleaning agents or substrate processing'
        }
        
    elif abs(mz - 23.9999) < 0.01:
        return {
            'name': 'Mg- or C2H4-',
            'formula': '24Mg- or C2H4-',
            'description': 'Magnesium anion OR ethyl fragment (same nominal mass)',
            'confidence': 'Medium',
            'notes': '🤔 AMBIGUOUS: Need high-resolution data to distinguish Mg vs C2H4'
        }
    
    elif abs(mz - 12.0000) < 0.01:
        return {
            'name': 'C-',
            'formula': 'C-',
            'description': 'Pure carbon anion - carbonization indicator', 
            'confidence': 'High',
            'notes': '🔥 CARBONIZATION: Pure carbon suggests graphitization at high e-beam doses'
        }
        
    elif abs(mz - 41.0391) < 0.01:
        return {
            'name': 'C3H5-',
            'formula': 'C3H5-',
            'description': 'Propyl or allyl fragment - organic degradation product',
            'confidence': 'Medium',
            'notes': '🧬 ORGANIC DEGRADATION: Three-carbon fragment from polymer breakdown'
        }
    
    elif abs(mz - 47.9982) < 0.01:
        return {
            'name': 'SO- or TiO-',
            'formula': 'SO- or 48TiO-',
            'description': 'Sulfur monoxide OR titanium oxide',
            'confidence': 'Medium',
            'notes': '⚗️ CONTAMINATION: Either sulfur contamination or Ti from substrate/processing'
        }
        
    elif abs(mz - 44.9981) < 0.01:
        return {
            'name': 'SiOH- or COOH-',
            'formula': 'SiOH- or COOH-',
            'description': 'Silicon hydroxide OR carboxyl group',
            'confidence': 'Medium', 
            'notes': '🔍 NEEDS MS/MS: Could be substrate (Si) or organic acid (COOH)'
        }
        
    elif abs(mz - 59.9852) < 0.01:
        return {
            'name': 'SiO2- or C2H4O2-',
            'formula': 'SiO2- or C2H4O2-',
            'description': 'Silicon dioxide OR acetic acid fragment',
            'confidence': 'Low',
            'notes': '🎯 HIGH PRIORITY: 5th highest loading - critical for identification!'
        }
        
    elif abs(mz - 75.9745) < 0.01:
        return {
            'name': 'AsO- or Complex',
            'formula': 'AsO- or complex',
            'description': 'Possible arsenic oxide or complex organic fragment',
            'confidence': 'Low',
            'notes': '🚨 INVESTIGATE: High loading unknown - could be contamination or artifact'
        }
        
    elif abs(mz - 76.9827) < 0.01:
        return {
            'name': 'Heavy_isotope',
            'formula': 'Unknown_isotope',
            'description': 'Heavy isotope of previous fragment or separate species',
            'confidence': 'Low',
            'notes': '🔗 ISOTOPE?: Check if related to m/z 75.97 - could be +1 isotope'
        }
    
    # Default for unmatched
    else:
        if mz < 20:
            cat = "Light element or small ion"
        elif mz < 50:
            cat = "Small organic or inorganic fragment"  
        elif mz < 100:
            cat = "Medium organic fragment"
        else:
            cat = "Large fragment or cluster"
            
        return {
            'name': f'Unknown_{mz:.1f}',
            'formula': f'm/z_{mz:.4f}',
            'description': f'{cat} - requires detailed analysis',
            'confidence': 'Very Low',
            'notes': '❓ UNKNOWN: Needs MS/MS, isotope patterns, or chemical context for ID'
        }

def generate_recommendations():
    """Generate specific recommendations for fragment identification"""
    
    print("\n" + "="*60)
    print("🎯 CRITICAL RECOMMENDATIONS FOR FRAGMENT IDENTIFICATION")
    print("="*60)
    
    print("\n🚨 IMMEDIATE ACTION ITEMS:")
    print("1. m/z 1.0085 (H-): Verify this is indeed H- - extremely high loading!")
    print("2. m/z 34.97/36.97: Confirm Cl- contamination - check cleaning protocols")
    print("3. m/z 59.99: HIGH PRIORITY - 5th highest loading, unknown identity")
    print("4. m/z 75.97/76.98: Investigate these high-loading unknowns")
    
    print("\n🔬 ANALYTICAL RECOMMENDATIONS:")
    print("• Use high-resolution ToF-SIMS to distinguish isobaric species")
    print("• Perform MS/MS on unknown fragments for structural information") 
    print("• Check isotope patterns to confirm elemental compositions")
    print("• Compare with blank/reference samples to identify contamination")
    
    print("\n🧪 CHEMICAL CONTEXT:")
    print("• Alucone = Al + organic linker - expect Al, C, H, O fragments")
    print("• E-beam processing - expect carbonization (C-, CnH-) at high doses")
    print("• Si substrate - some SiO-, SiO2- expected but should be low")
    print("• Contamination (Cl-, F-) suggests cleaning or processing residues")
    
    print("\n📊 FRAGMENT DATABASE UPDATES NEEDED:")
    print("• Add confirmed H- fragment (if verified)")
    print("• Add Cl-/F- contamination fragments with trends")
    print("• Add C- as carbonization indicator")
    print("• Include substrate-related fragments (SiO-, SiO2-)")
    
    print("\n✅ NEXT STEPS:")
    print("1. Verify high-confidence assignments (H-, Cl-, F-, C-)")
    print("2. Get additional data for ambiguous cases (m/z 24, 48, 45, 60)")
    print("3. Update fragment database with confirmed assignments")
    print("4. Re-run analysis with expanded database")

if __name__ == "__main__":
    assignments = analyze_fragments()
    generate_recommendations()