#!/usr/bin/env python3
"""
Systematic analysis of ALL unassigned fragments with isotope pattern checking
"""

def extract_unassigned_fragments():
    """Extract all unassigned fragments from CSV"""
    
    # Read the fragment assignment report
    unassigned = []
    with open('fragment_assignment_report.csv', 'r') as f:
        lines = f.readlines()
    
    for line in lines[1:]:  # Skip header
        parts = line.strip().split(',')
        if len(parts) >= 4 and parts[3] == 'Unknown':
            mz = float(parts[0])
            loading = float(parts[2])
            unassigned.append((mz, loading))
    
    return unassigned

def get_raw_data_for_mz(target_mz, tolerance=0.0005):
    """Get raw data from NegIonTIC.txt for a specific m/z"""
    
    try:
        with open('data/NegIonTIC.txt', 'r') as f:
            lines = f.readlines()
        
        # Find the matching m/z line
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            if len(parts) > 1:
                mz = float(parts[0])
                if abs(mz - target_mz) <= tolerance:
                    # Extract sample values (skip SQ1 columns: 2,7,12)
                    values = []
                    sample_names = ['P1_SQ2', 'P1_SQ3', 'P1_SQ4', 'P1_SQ5',
                                  'P2_SQ2', 'P2_SQ3', 'P2_SQ4', 'P2_SQ5', 
                                  'P3_SQ2', 'P3_SQ3', 'P3_SQ4', 'P3_SQ5']
                    indices = [1,3,4,5,6,8,9,10,11,13,14,15]  # Skip SQ1 columns
                    
                    for i, idx in enumerate(indices):
                        if idx < len(parts):
                            val = float(parts[idx])
                            values.append((sample_names[i], val))
                    
                    return mz, values
    except:
        return None, []
    
    return None, []

def check_isotope_pattern(mz1, mz2, tolerance=0.01):
    """Check if two m/z values could be isotope pairs"""
    
    common_isotope_pairs = [
        (1.0031, "1H/2H"),      # H/D isotopes
        (1.9958, "12C/13C"),    # Carbon isotopes  
        (1.9970, "35Cl/37Cl"),  # Chlorine isotopes
        (2.0044, "32S/34S"),    # Sulfur isotopes
        (0.9970, "16O/17O"),    # Oxygen isotopes
        (2.0090, "16O/18O"),    # Oxygen heavy isotope
    ]
    
    mass_diff = abs(mz2 - mz1)
    
    for expected_diff, pair_name in common_isotope_pairs:
        if abs(mass_diff - expected_diff) <= tolerance:
            return True, pair_name, expected_diff
    
    return False, None, mass_diff

def analyze_fragment_chemistry(mz, loading):
    """Analyze fragment based on exact mass and chemistry"""
    
    # Database of exact masses for common ToF-SIMS fragments
    fragment_database = {
        1.0078: ("H-", "Hydrogen anion", "Very common"),
        12.0000: ("C-", "Carbon anion", "Carbonization"),
        13.0078: ("CH-", "Carbon-hydrogen", "Organic"),
        14.0031: ("N-", "Nitrogen anion", "Contamination"),
        15.9949: ("O-", "Oxygen anion", "Very common"),
        16.9991: ("OH-", "Hydroxyl", "Very common"),
        18.9984: ("F-", "Fluorine", "Contamination"),
        22.9898: ("Na-", "Sodium", "Contamination"),
        24.3050: ("Mg-", "Magnesium", "Metal"),
        26.9815: ("Al-", "Aluminum", "Expected"),
        27.9769: ("Si-", "Silicon", "Substrate"),
        30.9738: ("P-", "Phosphorus", "Contamination"),
        31.9721: ("S-", "Sulfur", "Contamination"),
        34.9689: ("35Cl-", "Chlorine-35", "Contamination"),
        36.9659: ("37Cl-", "Chlorine-37", "Contamination"),
        39.0983: ("K-", "Potassium", "Contamination"),
        
        # Organic fragments
        25.0078: ("C2H-", "Two-carbon", "Organic"),
        26.0031: ("CN-", "Cyanide", "Possible"),
        27.9949: ("CO-", "Carbon monoxide", "Degradation"),
        29.0027: ("CHO-", "Aldehyde", "Degradation"),
        37.0078: ("C3H-", "Three-carbon", "Organic"),
        41.0391: ("C3H5-", "Propyl", "Organic"),
        43.9898: ("CO2-", "Carbon dioxide", "Degradation"),
        44.9982: ("COOH-", "Carboxyl", "Degradation"),
        45.0340: ("C2H5O-", "Ethoxy", "Organic"),
        49.0078: ("C4H-", "Four-carbon", "Reference"),
        53.0391: ("C4H5-", "Butadienyl", "Organic"),
        55.0184: ("C3H3O-", "Organic-O", "Linker"),
        61.0078: ("C5H-", "Five-carbon", "Organic"),
        65.0391: ("C5H5-", "Cyclopentadienyl", "Aromatic"),
        73.0078: ("C6H-", "Six-carbon", "Crosslinking"),
    }
    
    best_match = None
    best_diff = 0.01
    
    for ref_mass, (name, desc, category) in fragment_database.items():
        diff = abs(mz - ref_mass)
        if diff < best_diff:
            best_match = (name, desc, category, diff)
            best_diff = diff
    
    return best_match

def main():
    """Main analysis function"""
    
    print("=" * 70)
    print("🔬 SYSTEMATIC UNASSIGNED FRAGMENT ANALYSIS")
    print("=" * 70)
    
    # Get all unassigned fragments
    unassigned = extract_unassigned_fragments()
    
    print(f"\n📊 Found {len(unassigned)} unassigned fragments")
    print("Analyzing each one with isotope pattern checking...\n")
    
    # Group by mass ranges for systematic analysis
    light = [(mz, load) for mz, load in unassigned if mz < 20]
    medium = [(mz, load) for mz, load in unassigned if 20 <= mz < 100]
    heavy = [(mz, load) for mz, load in unassigned if mz >= 100]
    
    print(f"Light fragments (< 20 Da): {len(light)}")
    print(f"Medium fragments (20-100 Da): {len(medium)}")  
    print(f"Heavy fragments (≥ 100 Da): {len(heavy)}")
    
    all_fragments = sorted(unassigned, key=lambda x: x[1], reverse=True)  # Sort by loading
    
    print("\n" + "=" * 50)
    print("🎯 DETAILED FRAGMENT-BY-FRAGMENT ANALYSIS")
    print("=" * 50)
    
    for i, (mz, loading) in enumerate(all_fragments[:15]):  # Top 15 by loading
        
        print(f"\n[{i+1}] m/z {mz:.4f} (Loading: {loading:.6f})")
        print("-" * 40)
        
        # Get raw data for this m/z
        actual_mz, raw_values = get_raw_data_for_mz(mz)
        
        if actual_mz:
            print(f"📊 Exact m/z from data: {actual_mz:.4f}")
            
            # Show dose trend (sample a few values)
            if raw_values:
                sq2_vals = [v[1] for v in raw_values if 'SQ2' in v[0]]
                sq5_vals = [v[1] for v in raw_values if 'SQ5' in v[0]]
                if sq2_vals and sq5_vals:
                    sq2_avg = sum(sq2_vals) / len(sq2_vals)
                    sq5_avg = sum(sq5_vals) / len(sq5_vals)
                    trend = "increases" if sq5_avg > sq2_avg else "decreases"
                    print(f"📈 Dose trend: {trend} from SQ2→SQ5 ({sq2_avg:.4f}→{sq5_avg:.4f})")
        
        # Chemical identification
        match = analyze_fragment_chemistry(mz, loading)
        if match:
            name, desc, category, mass_diff = match
            confidence = "HIGH" if mass_diff < 0.005 else "MEDIUM" if mass_diff < 0.01 else "LOW"
            print(f"🔬 PROPOSED: {name} ({desc})")
            print(f"✅ Category: {category} | Confidence: {confidence} (Δ{mass_diff:.4f})")
        else:
            print("❓ No standard fragment match")
        
        # Check for potential isotope partners
        isotope_found = False
        for other_mz, other_loading in all_fragments:
            if other_mz != mz:
                is_isotope, pair_name, mass_diff = check_isotope_pattern(mz, other_mz)
                if is_isotope and abs(other_loading - loading) < loading * 0.5:  # Similar loading
                    print(f"🔗 ISOTOPE PAIR: m/z {other_mz:.4f} ({pair_name}, Δ{mass_diff:.4f})")
                    isotope_found = True
                    break
        
        if not isotope_found and mz > 30:
            print("💡 No clear isotope partner found")
        
        print(f"🚨 PRIORITY: {'CRITICAL' if loading > 0.3 else 'HIGH' if loading > 0.1 else 'MEDIUM' if loading > 0.05 else 'LOW'}")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY & NEXT STEPS")
    print("=" * 50)
    print("Review each proposed assignment above.")
    print("Focus on CRITICAL and HIGH priority fragments first.")
    print("Verify isotope pairs and dose trends.")
    print("Update fragment database with confirmed assignments.")

if __name__ == "__main__":
    main()