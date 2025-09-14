#!/usr/bin/env python3
"""
Systematic analysis of next 5 unassigned fragments with isotope checking
"""

def get_next_5_unassigned():
    """Get the next 5 highest loading unassigned fragments after the critical ones"""
    
    # From updated CSV, next 5 after H-, Cl-, AlCH2/C2HO-, COOH-
    next_5 = [
        (65.0031, 0.048954, "6th highest unassigned"),
        (18.9991, 0.036696, "7th highest - F- candidate"), 
        (68.9984, 0.030378, "8th highest"),
        (66.9811, 0.024022, "9th highest"),
        (53.0032, 0.021632, "10th highest")
    ]
    
    return next_5

def get_raw_data_intensities(mz_target, data_file="data/NegIonTIC.txt"):
    """Extract raw intensities for a specific m/z from your data"""
    
    try:
        with open(data_file, 'r') as f:
            lines = f.readlines()
    except:
        print(f"Cannot read {data_file}")
        return None
    
    # Find the closest m/z match
    best_match = None
    best_diff = float('inf')
    
    for line in lines[1:]:  # Skip header
        parts = line.strip().split('\t')
        if len(parts) > 1:
            try:
                mz = float(parts[0])
                diff = abs(mz - mz_target)
                if diff < best_diff and diff < 0.01:  # Within 0.01 Da
                    best_match = (mz, parts[1:])  # Skip m/z column
                    best_diff = diff
            except:
                continue
    
    if best_match:
        actual_mz, intensities = best_match
        
        # Parse sample names from header
        header = lines[0].strip().split('\t')[1:]  # Skip 'Mass (u)'
        
        # Extract SQ2-5 data (omit SQ1)
        sq_data = {}
        for i, sample_name in enumerate(header):
            if '_SQ1' not in sample_name and i < len(intensities):
                try:
                    intensity = float(intensities[i])
                    sq_num = int(sample_name.split('_SQ')[1])
                    pattern = sample_name.split('_')[0]
                    
                    if sq_num not in sq_data:
                        sq_data[sq_num] = []
                    sq_data[sq_num].append(intensity)
                except:
                    continue
        
        return actual_mz, sq_data
    
    return None

def check_isotope_candidates(mz_list, data_file="data/NegIonTIC.txt"):
    """Check for isotope patterns between fragments"""
    
    print("=== ISOTOPE PATTERN ANALYSIS ===")
    
    isotope_pairs = []
    
    for i, (mz1, _, _) in enumerate(mz_list):
        for j, (mz2, _, _) in enumerate(mz_list):
            if i < j:  # Avoid duplicate pairs
                mass_diff = abs(mz2 - mz1)
                
                # Common isotope mass differences
                if 1.9 < mass_diff < 2.1:  # ~2 Da (13C, 18O, 34S)
                    isotope_pairs.append((mz1, mz2, mass_diff, "13C/18O/34S isotope"))
                elif 0.9 < mass_diff < 1.1:  # ~1 Da (17O, 2H)
                    isotope_pairs.append((mz1, mz2, mass_diff, "17O/2H isotope"))
    
    if isotope_pairs:
        print("Potential isotope pairs found:")
        for mz1, mz2, diff, isotope_type in isotope_pairs:
            print(f"  m/z {mz1:.4f} ↔ m/z {mz2:.4f} (Δ{diff:.4f}) - {isotope_type}")
            
            # Get intensity data for both
            data1 = get_raw_data_intensities(mz1, data_file)
            data2 = get_raw_data_intensities(mz2, data_file)
            
            if data1 and data2:
                _, sq_data1 = data1
                _, sq_data2 = data2
                
                # Calculate average ratio across doses
                ratios = []
                for sq in [2, 3, 4, 5]:
                    if sq in sq_data1 and sq in sq_data2:
                        avg1 = sum(sq_data1[sq]) / len(sq_data1[sq])
                        avg2 = sum(sq_data2[sq]) / len(sq_data2[sq])
                        if avg2 > 0:
                            ratios.append(avg1 / avg2)
                
                if ratios:
                    avg_ratio = sum(ratios) / len(ratios)
                    print(f"    Average intensity ratio: {avg_ratio:.2f}")
                    
                    # Check if ratio is consistent with known isotopes
                    if isotope_type == "13C/18O/34S isotope":
                        if 20 < avg_ratio < 100:
                            print(f"    ✅ Consistent with 13C isotope pair")
                        elif 200 < avg_ratio < 600:
                            print(f"    ✅ Consistent with 18O isotope pair")
                    
    else:
        print("No clear isotope pairs found among these fragments")
    
    return isotope_pairs

def analyze_fragment_chemistry_detailed(mz, loading, raw_data):
    """Detailed chemical analysis with dose trends"""
    
    print(f"\n{'='*50}")
    print(f"FRAGMENT: m/z {mz:.4f} (Loading: {loading:.6f})")
    print(f"{'='*50}")
    
    if raw_data:
        actual_mz, sq_data = raw_data
        print(f"📊 Exact m/z in data: {actual_mz:.4f}")
        
        # Show dose trend
        if len(sq_data) >= 3:
            print("📈 Dose progression (SQ2→SQ5):")
            trends = []
            for sq in sorted(sq_data.keys()):
                avg_intensity = sum(sq_data[sq]) / len(sq_data[sq])
                dose = {2: 2000, 3: 5000, 4: 10000, 5: 15000}.get(sq, sq)
                trends.append((dose, avg_intensity))
                print(f"   SQ{sq} ({dose} μC/cm²): {avg_intensity:.6f}")
            
            # Calculate overall trend
            if len(trends) >= 2:
                first_val = trends[0][1]
                last_val = trends[-1][1]
                if first_val > 0:
                    change_percent = ((last_val - first_val) / first_val) * 100
                    trend_desc = "increases" if change_percent > 10 else "decreases" if change_percent < -10 else "stable"
                    print(f"   📊 Overall trend: {trend_desc} ({change_percent:+.1f}%)")
    else:
        print("❌ Could not find this m/z in raw data")
    
    # Chemical identification
    exact_mass_candidates = identify_by_exact_mass(mz)
    
    print(f"\n🔬 CHEMICAL IDENTITY ANALYSIS:")
    if exact_mass_candidates:
        print("Exact mass matches (±0.01 Da):")
        for candidate, diff, description in exact_mass_candidates:
            confidence = "HIGH" if diff < 0.005 else "MEDIUM" if diff < 0.01 else "LOW"
            print(f"   ✅ {candidate} (Δ{diff:.4f}) - {description} [{confidence} confidence]")
    else:
        print("   ❓ No exact mass matches found")
        
        # Provide chemical context based on mass range
        if mz < 20:
            print("   💡 Light fragment: Likely H, C, N, O, F or simple combinations")
        elif 20 <= mz < 50:
            print("   💡 Small organic or inorganic: Possible CnHx, metal ions, or small molecules")
        elif 50 <= mz < 100:
            print("   💡 Medium organic fragment: Likely polymer degradation product or complex ion")
        else:
            print("   💡 Large fragment: Possible cluster, polymer chain, or complex molecule")
    
    # Process context
    print(f"\n🧪 PROCESS CHEMISTRY CONTEXT:")
    if raw_data:
        _, sq_data = raw_data
        if 2 in sq_data and 5 in sq_data:
            sq2_avg = sum(sq_data[2]) / len(sq_data[2])
            sq5_avg = sum(sq_data[5]) / len(sq_data[5])
            
            if sq5_avg > sq2_avg * 1.2:
                print("   📈 INCREASES with dose → Likely degradation/fragmentation product")
            elif sq5_avg < sq2_avg * 0.8:
                print("   📉 DECREASES with dose → Likely intact structure being consumed")
            else:
                print("   ➡️  STABLE with dose → Possible contamination or invariant species")

def identify_by_exact_mass(mz):
    """Identify fragment based on exact mass with comprehensive database"""
    
    # Comprehensive exact mass database
    mass_database = [
        # Light elements and simple ions
        (1.0078, "H-", "Hydrogen anion"),
        (12.0000, "C-", "Carbon anion"),
        (13.0078, "CH-", "Carbon-hydrogen"),
        (14.0031, "N-", "Nitrogen anion"), 
        (15.9949, "O-", "Oxygen anion"),
        (16.9991, "OH-", "Hydroxyl"),
        (18.9984, "F-", "Fluorine"),
        (22.9898, "Na-", "Sodium"),
        
        # Halogenated species
        (34.9689, "35Cl-", "Chlorine-35"),
        (36.9659, "37Cl-", "Chlorine-37"),
        (78.9183, "79Br-", "Bromine-79"),
        (80.9163, "81Br-", "Bromine-81"),
        
        # Simple organic fragments
        (25.0078, "C2H-", "Acetylide"),
        (26.0031, "CN-", "Cyanide"),
        (27.9949, "CO-", "Carbon monoxide"),
        (29.0027, "CHO-", "Formyl"),
        (37.0078, "C3H-", "Propargyl"),
        (41.0391, "C3H5-", "Allyl/propyl"),
        (43.9898, "CO2-", "Carbon dioxide"),
        (44.9982, "COOH-", "Carboxyl"),
        (49.0078, "C4H-", "Four-carbon"),
        (53.0391, "C4H5-", "Butadienyl"),
        (61.0078, "C5H-", "Five-carbon"),
        (65.0391, "C5H5-", "Cyclopentadienyl"),
        (73.0078, "C6H-", "Six-carbon"),
        
        # Silicon-based (substrate)
        (27.9769, "Si-", "Silicon"),
        (28.9765, "29Si-", "Silicon-29"),
        (43.9719, "SiO-", "Silicon monoxide"),
        (44.9698, "29SiO-", "Silicon-29 monoxide"),
        (59.9668, "SiO2-", "Silicon dioxide"),
        
        # Aluminum-based (alucone)
        (26.9815, "Al-", "Aluminum"),
        (42.9765, "AlO-", "Aluminum monoxide"),
        (58.9714, "AlO2-", "Aluminum dioxide"),
        (40.9971, "AlCH2-", "Aluminum methyl"),
        
        # Process-specific
        (41.0027, "C2HO-", "Ketene/acetyl"),
        
        # Sulfur-based (contamination)
        (31.9721, "S-", "Sulfur"),
        (47.9671, "SO-", "Sulfur monoxide"),
        (63.9619, "SO2-", "Sulfur dioxide"),
        
        # Complex organics
        (55.0184, "C3H3O-", "Organic oxygen"),
        (67.0184, "C4H3O-", "Furan-like"),
        (69.0340, "C4H5O-", "Organic degradation"),
    ]
    
    candidates = []
    for ref_mass, formula, description in mass_database:
        diff = abs(mz - ref_mass)
        if diff <= 0.01:  # Within 0.01 Da
            candidates.append((formula, diff, description))
    
    # Sort by mass difference (best matches first)
    candidates.sort(key=lambda x: x[1])
    
    return candidates

def main():
    """Main analysis function"""
    
    print("🔬 SYSTEMATIC ANALYSIS: NEXT 5 UNASSIGNED FRAGMENTS")
    print("=" * 70)
    
    fragments = get_next_5_unassigned()
    
    print(f"Analyzing {len(fragments)} fragments with isotope checking...")
    print()
    
    # Check for isotope patterns first
    check_isotope_candidates(fragments)
    
    # Detailed analysis of each fragment
    print(f"\n{'='*70}")
    print("DETAILED FRAGMENT-BY-FRAGMENT ANALYSIS")
    print(f"{'='*70}")
    
    for i, (mz, loading, description) in enumerate(fragments):
        print(f"\n[{i+1}/5] {description}")
        
        # Get raw data for this fragment
        raw_data = get_raw_data_intensities(mz)
        
        # Detailed analysis
        analyze_fragment_chemistry_detailed(mz, loading, raw_data)
        
        print(f"\n{'🤔 DISCUSSION POINT:':<20}")
        if mz == 65.0031:
            print("This could be C5H5- (aromatic) - is aromatic formation expected?")
        elif mz == 18.9991:
            print("Very close to F- - fluorine contamination or processing residue?")
        elif mz == 68.9984:
            print("Unknown - could be metal oxide or organic fragment?")
        elif mz == 66.9811:
            print("Close to 68.9984 - isotope pair or separate species?") 
        elif mz == 53.0032:
            print("Close to C4H5- - butadiene-like fragment from linker breakdown?")
        
        print("\\n" + "="*50 + "\\n")
    
    print(f"\n{'='*70}")
    print("SUMMARY AND NEXT STEPS")
    print(f"{'='*70}")
    print("1. Review each proposed assignment above")
    print("2. Focus on fragments that increase with dose (degradation products)")
    print("3. Verify isotope pairs with intensity ratios")
    print("4. Consider chemical context of your alucone system")
    print("5. Update fragment database with confirmed assignments")

if __name__ == "__main__":
    main()