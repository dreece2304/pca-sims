#!/usr/bin/env python3
"""
Comprehensive Unassigned Peaks Analysis
Systematic identification of remaining unknown fragments
"""

import os
import numpy as np

def analyze_unassigned_peaks():
    """Analyze remaining unassigned peaks from both positive and negative data"""
    
    print("🔍 COMPREHENSIVE UNASSIGNED PEAKS ANALYSIS")
    print("="*60)
    
    # Load both datasets
    neg_unassigned = get_unassigned_fragments("negative_ion_assignments.csv")
    pos_unassigned = get_unassigned_fragments("positive_ion_assignments.csv") 
    
    print(f"📊 SUMMARY:")
    print(f"   Negative ion unassigned: {len(neg_unassigned)}")
    print(f"   Positive ion unassigned: {len(pos_unassigned)}")
    
    # Priority analysis based on PC1 loading
    high_priority_neg = [f for f in neg_unassigned if abs(float(f.get('loading', 0))) > 0.02]
    high_priority_pos = [f for f in pos_unassigned if abs(float(f.get('loading', 0))) > 0.02]
    
    print(f"\n🎯 HIGH PRIORITY (|Loading| > 0.02):")
    print(f"   Negative: {len(high_priority_neg)} fragments")
    print(f"   Positive: {len(high_priority_pos)} fragments")
    
    # Detailed analysis of high priority peaks
    analyze_high_priority_peaks(high_priority_neg, "NEGATIVE")
    analyze_high_priority_peaks(high_priority_pos, "POSITIVE")
    
    # Cross-correlation analysis
    cross_correlate_unassigned(neg_unassigned, pos_unassigned)
    
    # Mass region analysis
    analyze_mass_regions(neg_unassigned + pos_unassigned)
    
    # Generate recommendations
    generate_assignment_recommendations()

def get_unassigned_fragments(filepath):
    """Extract unassigned fragments from CSV"""
    if not os.path.exists(filepath):
        return []
    
    unassigned = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            return []
        
        header = lines[0].strip().split(',')
        
        # Find column indices
        mz_col = next((i for i, col in enumerate(header) if 'm/z' in col), 0)
        loading_col = next((i for i, col in enumerate(header) if 'Loading' in col), 1) 
        fragment_col = next((i for i, col in enumerate(header) if 'Fragment' in col), 3)
        formula_col = next((i for i, col in enumerate(header) if 'Formula' in col), 4)
        
        for line in lines[1:]:
            values = line.strip().split(',')
            if len(values) > max(mz_col, loading_col, fragment_col):
                fragment = values[fragment_col] if fragment_col < len(values) else ''
                
                # Check if unassigned
                if fragment in ['Unknown', 'Unidentified', ''] or 'Unknown' in fragment:
                    try:
                        unassigned.append({
                            'mz': float(values[mz_col]),
                            'loading': values[loading_col] if loading_col < len(values) else '0',
                            'formula': values[formula_col] if formula_col < len(values) else 'Unknown'
                        })
                    except:
                        continue
    
    return unassigned

def analyze_high_priority_peaks(peaks, ion_mode):
    """Detailed analysis of high priority unassigned peaks"""
    
    if not peaks:
        return
        
    print(f"\n🔬 HIGH PRIORITY {ion_mode} ION PEAKS:")
    print("-" * 40)
    
    # Sort by loading magnitude
    peaks_sorted = sorted(peaks, key=lambda x: abs(float(x['loading'])), reverse=True)
    
    for i, peak in enumerate(peaks_sorted[:10], 1):  # Top 10
        mz = peak['mz']
        loading = float(peak['loading'])
        
        print(f"\n{i}. m/z {mz:.4f} (Loading: {loading:.6f})")
        
        # Chemical analysis
        candidates = identify_chemical_candidates(mz, ion_mode)
        
        if candidates:
            print("   🧪 Potential identities:")
            for candidate, mass_diff, confidence in candidates:
                print(f"      • {candidate} (Δ{mass_diff:.4f} Da) [{confidence}]")
        else:
            print("   ❓ No clear chemical candidates")
        
        # Mass region context
        mass_context = get_mass_region_context(mz)
        print(f"   📍 Mass region: {mass_context}")
        
        # Process chemistry context
        process_context = get_process_context(mz, loading > 0)
        print(f"   ⚗️  Process context: {process_context}")

def identify_chemical_candidates(mz, ion_mode):
    """Identify potential chemical candidates for unknown m/z"""
    
    # Comprehensive chemical database
    if ion_mode == "NEGATIVE":
        candidates_db = [
            # Silicon compounds (substrate)
            (26.9769, "Si-", "Silicon anion"),
            (28.9765, "29Si-", "Silicon-29 isotope"),
            (43.9719, "SiO-", "Silicon oxide"),
            (59.9668, "SiO2-", "Silicon dioxide"),
            
            # Complex carbonyls
            (67.0184, "C4H3O-", "Unsaturated carbonyl"), 
            (69.0340, "C4H5O-", "Saturated carbonyl"),
            (71.0133, "C3H3O2-", "Malonate-like"),
            (85.0289, "C4H5O2-", "Succinate-like"),
            
            # Halogenated species
            (62.9689, "ClO2-", "Chlorine dioxide"),
            (78.9183, "Br-", "Bromine"),
            (126.9045, "I-", "Iodine"),
            
            # Metal oxides/hydroxides  
            (72.9898, "BO2-", "Borate"),
            (40.9618, "NaO-", "Sodium oxide"),
            (56.9624, "FeO-", "Iron oxide"),
            
            # Complex aluminum species
            (54.9815, "Al(OH)-", "Aluminum hydroxide"),
            (70.9714, "Al(OH)2-", "Aluminum dihydroxide"),
            (84.9893, "AlCH3O-", "Aluminum methoxide"),
            
            # Process artifacts
            (74.9269, "HSO3-", "Bisulfite"),
            (96.9696, "HSO4-", "Bisulfate"),
            (62.0049, "NO3-", "Nitrate"),
            (79.9568, "SO3-", "Sulfite")
        ]
    else:  # POSITIVE
        candidates_db = [
            # Silicon compounds  
            (27.9769, "Si+", "Silicon cation"),
            (43.9719, "SiO+", "Silicon oxide"),
            (44.9797, "SiOH+", "Silicon hydroxide"),
            
            # Extended aluminum chemistry
            (42.9815, "AlOH+", "Aluminum hydroxide"),
            (58.9714, "AlO2H+", "Aluminum oxyhydroxide"),
            (56.0284, "Al(CH3)2+", "Aluminum dimethyl"),
            (71.0519, "Al(CH3)3+", "Trimethylaluminum"),
            
            # Organic cations
            (43.0548, "C3H7+", "Propyl"),
            (57.0704, "C4H9+", "Butyl"),
            (55.0548, "C4H7+", "Butenyl"),
            (67.0548, "C5H7+", "Pentenyl"),
            
            # Carbonyl cations
            (71.0497, "C4H7O+", "Butenal"),
            (85.0653, "C5H9O+", "Pentenal"),
            (57.0340, "C3H5O+", "Acrolein"),
            
            # Metal cations
            (22.9898, "Na+", "Sodium"),
            (38.9637, "K+", "Potassium"), 
            (39.9626, "Ca+", "Calcium"),
            (55.9349, "Fe+", "Iron"),
            
            # Process species
            (18.0338, "NH4+", "Ammonium"),
            (46.0049, "NO2+", "Nitronium"),
            (64.9619, "SO2+", "Sulfur dioxide")
        ]
    
    matches = []
    for ref_mz, formula, description in candidates_db:
        mass_diff = abs(mz - ref_mz)
        
        if mass_diff < 0.02:  # Within 20 mDa
            if mass_diff < 0.005:
                confidence = "HIGH"
            elif mass_diff < 0.01:
                confidence = "MEDIUM" 
            else:
                confidence = "LOW"
            
            matches.append((f"{formula} - {description}", mass_diff, confidence))
    
    # Sort by mass accuracy
    matches.sort(key=lambda x: x[1])
    
    return matches[:5]  # Top 5 matches

def get_mass_region_context(mz):
    """Get context based on mass region"""
    if mz < 20:
        return "Light elements (H, C, N, O, F)"
    elif mz < 50:
        return "Small molecules/metal ions"
    elif mz < 100:
        return "Organic fragments/metal compounds"
    elif mz < 200:
        return "Complex organics/clusters"
    else:
        return "Large clusters/polymeric fragments"

def get_process_context(mz, increases_with_dose):
    """Get process chemistry context"""
    if increases_with_dose:
        return "Likely transformation product (thermodynamic stabilization)"
    else:
        return "Likely consumed precursor or volatilized species"

def cross_correlate_unassigned(neg_peaks, pos_peaks):
    """Cross-correlate unassigned peaks between positive and negative modes"""
    
    print(f"\n🔗 CROSS-CORRELATION ANALYSIS:")
    print("-" * 35)
    
    correlations = []
    
    for neg_peak in neg_peaks:
        for pos_peak in pos_peaks:
            mass_diff = abs(neg_peak['mz'] - pos_peak['mz'])
            
            if mass_diff < 0.05:  # Within 50 mDa
                correlations.append({
                    'neg_mz': neg_peak['mz'],
                    'pos_mz': pos_peak['mz'], 
                    'mass_diff': mass_diff,
                    'neg_loading': neg_peak['loading'],
                    'pos_loading': pos_peak['loading']
                })
    
    if correlations:
        print("Potential positive-negative correlations:")
        correlations.sort(key=lambda x: x['mass_diff'])
        
        for corr in correlations[:10]:  # Top 10
            print(f"   • m/z {corr['neg_mz']:.4f} (−) ↔ m/z {corr['pos_mz']:.4f} (+)")
            print(f"     Δ{corr['mass_diff']:.4f} Da, Loadings: {corr['neg_loading']} / {corr['pos_loading']}")
    else:
        print("No clear positive-negative correlations found")

def analyze_mass_regions(all_peaks):
    """Analyze distribution of unassigned peaks by mass region"""
    
    print(f"\n📊 MASS REGION DISTRIBUTION:")
    print("-" * 30)
    
    regions = {
        "0-25 Da": [p for p in all_peaks if p['mz'] < 25],
        "25-50 Da": [p for p in all_peaks if 25 <= p['mz'] < 50],
        "50-100 Da": [p for p in all_peaks if 50 <= p['mz'] < 100],
        "100-200 Da": [p for p in all_peaks if 100 <= p['mz'] < 200],
        ">200 Da": [p for p in all_peaks if p['mz'] >= 200]
    }
    
    for region, peaks in regions.items():
        if peaks:
            avg_loading = np.mean([abs(float(p['loading'])) for p in peaks])
            print(f"{region:>12}: {len(peaks):>2} peaks (avg |loading|: {avg_loading:.4f})")
        else:
            print(f"{region:>12}:  0 peaks")

def generate_assignment_recommendations():
    """Generate specific recommendations for peak assignment"""
    
    print(f"\n🎯 ASSIGNMENT RECOMMENDATIONS:")
    print("="*40)
    
    recommendations = [
        {
            "priority": "HIGH",
            "action": "MS/MS fragmentation analysis",
            "targets": "All peaks with |loading| > 0.05",
            "reason": "High impact on PCA model"
        },
        {
            "priority": "HIGH", 
            "action": "Higher mass resolution ToF-SIMS",
            "targets": "Peaks in crowded mass regions (40-70 Da)",
            "reason": "Resolve overlapping signals"
        },
        {
            "priority": "MEDIUM",
            "action": "Isotope pattern analysis", 
            "targets": "Peaks with potential isotope partners",
            "reason": "Confirm molecular formulas"
        },
        {
            "priority": "MEDIUM",
            "action": "Blank/reference sample analysis",
            "targets": "Low-loading contamination suspects",
            "reason": "Distinguish process vs contamination"
        },
        {
            "priority": "LOW",
            "action": "Literature database search",
            "targets": "All unassigned peaks", 
            "reason": "Check against known fragment libraries"
        }
    ]
    
    for rec in recommendations:
        print(f"\n{rec['priority']} PRIORITY:")
        print(f"   Action: {rec['action']}")
        print(f"   Targets: {rec['targets']}")
        print(f"   Reason: {rec['reason']}")
    
    print(f"\n✅ SYSTEMATIC APPROACH:")
    print("1. Focus on high-loading unknowns first")
    print("2. Use complementary analytical techniques")
    print("3. Validate assignments with isotope patterns") 
    print("4. Cross-correlate positive and negative modes")
    print("5. Update fragment database iteratively")

def main():
    """Main analysis function"""
    analyze_unassigned_peaks()
    
    print(f"\n🔬 NEXT STEPS FOR COMPLETE ANALYSIS:")
    print("1. Run MS/MS on high-priority unknowns")
    print("2. Increase mass resolution for overlapping peaks") 
    print("3. Analyze blank samples for contamination")
    print("4. Update publication figures with complete assignments")
    print("5. Validate all assignments before publication")

if __name__ == "__main__":
    main()