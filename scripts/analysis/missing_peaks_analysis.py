#!/usr/bin/env python3
"""
Analysis of unassigned fragments from ToF-SIMS data
Focus on high-impact unknown peaks for chemical identification
"""

import pandas as pd
import numpy as np

def analyze_unassigned_fragments():
    """Analyze unassigned fragments and suggest chemical identities"""
    
    # Load the fragment assignment data
    data = pd.read_csv('fragment_assignment_report.csv')
    
    # Focus on unassigned fragments with significant loadings
    unassigned = data[data['Fragment'] == 'Unknown'].copy()
    unassigned['mz_float'] = unassigned['m/z'].astype(float)
    unassigned['loading_float'] = unassigned['|Loading|'].astype(float)
    
    print("=== HIGH-IMPACT UNASSIGNED FRAGMENTS ANALYSIS ===")
    print(f"Total unassigned fragments: {len(unassigned)}")
    
    # Focus on highest impact fragments (top 15 by loading)
    high_impact = unassigned.nlargest(15, 'loading_float')
    
    print("\n=== TOP 15 UNASSIGNED FRAGMENTS BY LOADING ===")
    
    fragment_assignments = []
    
    for _, row in high_impact.iterrows():
        mz = row['mz_float']
        loading = row['loading_float']
        
        # Chemical identification logic based on m/z
        identity = identify_fragment(mz)
        
        fragment_assignments.append({
            'm/z': f"{mz:.4f}",
            'Loading': f"{loading:.6f}",
            'Proposed_Identity': identity['name'],
            'Formula': identity['formula'],
            'Category': identity['category'],
            'Description': identity['description'],
            'Confidence': identity['confidence'],
            'Notes': identity['notes']
        })
        
        print(f"m/z {mz:.4f} (Loading: {loading:.6f})")
        print(f"  → {identity['name']} ({identity['formula']})")
        print(f"  → {identity['description']}")
        print(f"  → Confidence: {identity['confidence']}")
        if identity['notes']:
            print(f"  → Notes: {identity['notes']}")
        print()
    
    # Create detailed assignment dataframe
    assignments_df = pd.DataFrame(fragment_assignments)
    
    print("\n=== ASSIGNMENT SUMMARY ===")
    confidence_counts = assignments_df['Confidence'].value_counts()
    for conf, count in confidence_counts.items():
        print(f"{conf}: {count} assignments")
    
    return assignments_df

def identify_fragment(mz):
    """Identify chemical fragment based on m/z value"""
    
    # Tolerance for mass matching
    tol = 0.01
    
    # Common ToF-SIMS negative ion fragments for organic/inorganic materials
    fragment_library = [
        # Hydrogen/Light elements
        (1.0078, "H-", "H-", "Light_element", "Hydrogen anion", "High", "Common in negative ToF-SIMS"),
        
        # Carbon-containing
        (12.0000, "C-", "C-", "Hydrocarbon", "Carbon anion", "Medium", "Pure carbon fragment"),
        
        # Fluorine (possible contamination)
        (18.9984, "F-", "F-", "Contamination", "Fluorine anion", "High", "Common contamination from processing"),
        
        # Chlorine isotopes
        (34.9689, "Cl-", "Cl-", "Contamination", "Chlorine-35 anion", "High", "Chlorine contamination"),
        (36.9659, "Cl-", "37Cl-", "Contamination", "Chlorine-37 anion", "High", "Heavy chlorine isotope"),
        
        # Sodium loss/exchange
        (22.9898, "Na-", "Na-", "Contamination", "Sodium anion", "Medium", "Possible sodium contamination"),
        (23.9999, "Na-/Mg-", "24Mg- or organics", "Mixed", "Magnesium or organic fragment", "Low", "Could be Mg- or C2H4-"),
        
        # Sulfur compounds
        (31.9721, "S-", "S-", "Contamination", "Sulfur anion", "Medium", "Sulfur contamination"),
        (47.9982, "SO-", "SO-", "Contamination", "Sulfur monoxide", "Medium", "Sulfur oxidation product"),
        (63.9619, "SO2-", "SO2-", "Contamination", "Sulfur dioxide", "Medium", "Sulfur oxidation product"),
        
        # Phosphorus (possible contamination)
        (30.9738, "P-", "P-", "Contamination", "Phosphorus anion", "Medium", "Phosphorus contamination"),
        
        # Silicon compounds (substrate)
        (28.9765, "Si-", "29Si-", "Substrate", "Silicon-29 isotope", "Medium", "Heavy silicon isotope from substrate"),
        (43.9719, "SiO-", "29SiO-", "Substrate", "Silicon-29 monoxide", "Medium", "Silicon isotope oxide"),
        
        # Extended organic fragments
        (41.0391, "C3H5-", "C3H5-", "Hydrocarbon", "Propyl/allyl fragment", "Medium", "Three-carbon organic fragment"),
        (53.0391, "C4H5-", "C4H5-", "Hydrocarbon", "Butadienyl fragment", "Medium", "Unsaturated four-carbon fragment"),
        (65.0391, "C5H5-", "C5H5-", "Hydrocarbon", "Cyclopentadienyl fragment", "Medium", "Five-carbon aromatic fragment"),
        (71.0547, "C4H7O-", "C4H7O-", "Organic_linker", "Modified diol fragment", "Medium", "Altered linker fragment"),
        
        # Metal clusters/isotopes
        (75.9245, "AsO-", "AsO-", "Contamination", "Arsenic oxide (contamination)", "Low", "Heavy metal contamination"),
        (78.9183, "Br-", "Br-", "Contamination", "Bromine anion", "Medium", "Bromine contamination"),
        
        # High mass - likely organic clusters or substrate features
        (102.9548, "Complex", "Unknown_complex", "Complex", "Complex organic or inorganic cluster", "Low", "Needs MS/MS identification"),
        (118.9456, "Complex", "Unknown_complex", "Complex", "Complex fragment or cluster", "Low", "Requires detailed analysis"),
        (136.9589, "Complex", "Unknown_complex", "Complex", "Large fragment or cluster", "Low", "Complex structure - needs identification"),
        
        # Very high mass - likely instrumental artifacts or large clusters
        (200.0, "Artifact", "Large_cluster", "Artifact", "Possible instrumental artifact or large molecular cluster", "Low", "m/z > 200 often artifacts in ToF-SIMS")
    ]
    
    # Try to match m/z to known fragments
    for ref_mz, name, formula, category, description, confidence, notes in fragment_library:
        if abs(mz - ref_mz) <= tol:
            return {
                'name': name,
                'formula': formula,
                'category': category,
                'description': description,
                'confidence': confidence,
                'notes': notes
            }
    
    # If no match found, categorize by mass range
    if mz < 20:
        return {
            'name': "Light_element",
            'formula': f"m/z_{mz:.4f}",
            'category': "Light_element", 
            'description': "Light element or small molecular fragment",
            'confidence': "Low",
            'notes': "Requires isotope pattern analysis"
        }
    elif mz < 50:
        return {
            'name': "Small_organic",
            'formula': f"CxHyOz_{mz:.4f}",
            'category': "Small_organic",
            'description': "Small organic fragment or inorganic ion",
            'confidence': "Low", 
            'notes': "Could be organic fragment or inorganic contamination"
        }
    elif mz < 100:
        return {
            'name': "Medium_organic", 
            'formula': f"CxHyOz_{mz:.4f}",
            'category': "Medium_organic",
            'description': "Medium-sized organic fragment or metal complex",
            'confidence': "Low",
            'notes': "Likely organic fragment from polymer degradation"
        }
    elif mz < 200:
        return {
            'name': "Large_fragment",
            'formula': f"Complex_{mz:.4f}",
            'category': "Large_fragment", 
            'description': "Large organic fragment or molecular cluster",
            'confidence': "Very_Low",
            'notes': "May be polymer fragment or cluster ion"
        }
    else:
        return {
            'name': "Very_large_cluster",
            'formula': f"Cluster_{mz:.4f}",
            'category': "Artifact",
            'description': "Very large cluster or possible instrumental artifact", 
            'confidence': "Very_Low",
            'notes': "High mass - likely artifact or unusual cluster"
        }

if __name__ == "__main__":
    assignments = analyze_unassigned_fragments()
    
    # Save results
    assignments.to_csv('proposed_fragment_assignments.csv', index=False)
    print(f"\n✅ Proposed assignments saved to: proposed_fragment_assignments.csv")
    print("\n📋 Next steps:")
    print("1. Review high-confidence assignments")
    print("2. Update fragment database with confirmed assignments")  
    print("3. Use MS/MS or isotope patterns to confirm low-confidence assignments")
    print("4. Consider chemical context (alucone resist, electron beam processing)")