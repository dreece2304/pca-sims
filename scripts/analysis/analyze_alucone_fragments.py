#!/usr/bin/env python3
"""
Analyze high-priority unknown fragments against alucone-specific database
"""

import csv
import sys

# High-priority unknown m/z values to analyze
UNKNOWN_MZ = {
    # Positive ions
    41.0363: 0.244719,  # 2nd highest loading!
    77.0296: 0.090565,
    128.0618: 0.061234,
    63.0217: 0.058166,
    52.9919: 0.048309,
    42.0144: 0.047264,
    79.0001: 0.040879,
    31.0165: 0.036001,
    152.0542: 0.034610,
    
    # Negative ions (lower priority)
    66.9811: 0.024022,
    62.0166: 0.018767,
    96.9636: 0.017334,
    47.9993: 0.017168
}

def calculate_ppm_error(observed, theoretical):
    """Calculate mass error in ppm"""
    return abs(observed - theoretical) / observed * 1000000

def analyze_fragments():
    """Analyze unknowns against alucone database"""
    
    print("🔬 ALUCONE FRAGMENT ANALYSIS")
    print("=" * 50)
    
    # Load alucone fragment database
    fragments = []
    with open('/home/dreece23/pca-sims/data/alucone_radical_fragments.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['Fragment'].startswith('#'):  # Skip comments
                fragments.append(row)
    
    print(f"📚 Loaded {len(fragments)} alucone-specific fragments")
    print()
    
    # Analyze each unknown
    matches_found = 0
    for unknown_mz, pc1_loading in sorted(UNKNOWN_MZ.items(), key=lambda x: x[1], reverse=True):
        
        print(f"🎯 ANALYZING m/z {unknown_mz} (PC1 Loading: {pc1_loading:.6f})")
        print("-" * 45)
        
        # Find potential matches within expanded tolerance
        candidates = []
        
        for fragment in fragments:
            try:
                theoretical_mz = float(fragment['Exact_Mass'])
                error_ppm = calculate_ppm_error(unknown_mz, theoretical_mz)
                
                # Use expanded tolerance up to 200 ppm for novel fragments
                if error_ppm <= 200:
                    candidates.append({
                        'fragment': fragment['Fragment'],
                        'formula': fragment['Formula'],
                        'mass': theoretical_mz,
                        'error_ppm': error_ppm,
                        'category': fragment['Category'],
                        'mechanism': fragment['Formation_Mechanism'],
                        'isotopes': fragment['Expected_Isotopes'],
                        'notes': fragment['Notes']
                    })
            except ValueError:
                continue
        
        # Sort by mass error
        candidates.sort(key=lambda x: x['error_ppm'])
        
        if candidates:
            matches_found += 1
            print(f"✅ Found {len(candidates)} potential matches:")
            
            for i, candidate in enumerate(candidates[:3], 1):  # Show top 3
                print(f"   {i}. {candidate['formula']} ({candidate['fragment']})")
                print(f"      Mass: {candidate['mass']:.4f} (Error: {candidate['error_ppm']:.1f} ppm)")
                print(f"      Category: {candidate['category']}")
                print(f"      Formation: {candidate['mechanism']}")
                if candidate['isotopes'] != 'None':
                    print(f"      Isotopes: {candidate['isotopes']}")
                print(f"      Notes: {candidate['notes']}")
                print()
        else:
            print("❌ No matches found within 200 ppm tolerance")
            print("   → Likely system-specific fragment requiring further analysis")
            print()
        
        print()
    
    print(f"📊 SUMMARY: Found potential assignments for {matches_found}/{len(UNKNOWN_MZ)} unknowns")
    print()
    
    # Highlight best matches (< 55 ppm)
    print("🏆 HIGH-CONFIDENCE MATCHES (< 55 ppm):")
    print("=" * 40)
    
    high_confidence = 0
    for unknown_mz, pc1_loading in sorted(UNKNOWN_MZ.items(), key=lambda x: x[1], reverse=True):
        best_match = None
        best_error = float('inf')
        
        for fragment in fragments:
            try:
                theoretical_mz = float(fragment['Exact_Mass'])
                error_ppm = calculate_ppm_error(unknown_mz, theoretical_mz)
                
                if error_ppm < best_error:
                    best_error = error_ppm
                    best_match = fragment
            except ValueError:
                continue
        
        if best_match and best_error <= 55:
            high_confidence += 1
            print(f"✨ m/z {unknown_mz} → {best_match['Formula']} ({best_error:.1f} ppm)")
            print(f"   Category: {best_match['Category']}")
            print(f"   Mechanism: {best_match['Formation_Mechanism']}")
            print()
    
    if high_confidence == 0:
        print("   No matches found within 55 ppm tolerance")
        print("   → Consider isotope analysis and novel fragment pathways")
    
    print(f"🎯 HIGH-CONFIDENCE ASSIGNMENTS: {high_confidence}")

if __name__ == "__main__":
    analyze_fragments()