#!/usr/bin/env python3
"""
Comprehensive Fragment Database Generator
Creates all possible molecular fragments up to a specified mass limit
"""

import itertools
import csv
from collections import defaultdict

# Atomic masses (monoisotopic)
ATOMIC_MASSES = {
    'H': 1.007825,
    'C': 12.000000,
    'N': 14.003074,
    'O': 15.994915,
    'F': 18.998403,
    'Si': 27.976927,
    'Al': 26.981539,
    'Cl': 34.968853,  # 35Cl
    'Cl37': 36.965903,  # 37Cl
    'Na': 22.989770,
    'S': 31.972071
}

# Common isotopes to include
ISOTOPES = {
    '13C': 13.003355,
    '15N': 15.000109,
    '17O': 16.999132,
    '18O': 17.999160,
    '29Si': 28.976495,
    '30Si': 29.973770
}

def generate_molecular_formulas(max_mass=200, elements=['C', 'H', 'O', 'N', 'Al', 'Si']):
    """
    Generate all possible molecular formulas up to max_mass
    """
    formulas = []
    
    # Define reasonable limits for each element to avoid infinite loops
    element_limits = {
        'C': min(20, int(max_mass / ATOMIC_MASSES['C'])),
        'H': min(50, int(max_mass / ATOMIC_MASSES['H'])),
        'O': min(15, int(max_mass / ATOMIC_MASSES['O'])),
        'N': min(10, int(max_mass / ATOMIC_MASSES['N'])),
        'Al': min(5, int(max_mass / ATOMIC_MASSES['Al'])),
        'Si': min(5, int(max_mass / ATOMIC_MASSES['Si'])),
        'F': min(10, int(max_mass / ATOMIC_MASSES['F'])),
        'Cl': min(3, int(max_mass / ATOMIC_MASSES['Cl'])),
        'Na': min(2, int(max_mass / ATOMIC_MASSES['Na'])),
        'S': min(3, int(max_mass / ATOMIC_MASSES['S']))
    }
    
    print(f"Generating formulas with limits: {element_limits}")
    
    # Generate all combinations
    ranges = []
    for element in elements:
        if element in element_limits:
            ranges.append(range(element_limits[element] + 1))
    
    total_combinations = 1
    for r in ranges:
        total_combinations *= len(r)
    print(f"Total combinations to check: {total_combinations:,}")
    
    count = 0
    for combination in itertools.product(*ranges):
        count += 1
        if count % 100000 == 0:
            print(f"Processed {count:,} combinations...")
            
        # Create formula dictionary
        formula_dict = {element: combination[i] for i, element in enumerate(elements)}
        
        # Skip empty formula
        if sum(formula_dict.values()) == 0:
            continue
            
        # Calculate mass
        mass = sum(ATOMIC_MASSES[element] * count for element, count in formula_dict.items() if count > 0)
        
        if mass <= max_mass:
            # Create formula string
            formula_str = ""
            for element in ['C', 'H', 'N', 'O', 'F', 'Si', 'Al', 'Cl', 'Na', 'S']:
                if element in formula_dict and formula_dict[element] > 0:
                    if formula_dict[element] == 1:
                        formula_str += element
                    else:
                        formula_str += f"{element}{formula_dict[element]}"
            
            if formula_str:  # Don't add empty formulas
                formulas.append((formula_str, mass, formula_dict))
    
    return formulas

def add_charge_variants(formulas):
    """
    Add positive and negative ion variants
    """
    variants = []
    
    for formula, mass, composition in formulas:
        # Positive ions (remove electron)
        pos_mass = mass - 0.000549  # electron mass
        variants.append((f"{formula}+", pos_mass, "positive", composition, "Molecular ion"))
        
        # Negative ions (add electron)  
        neg_mass = mass + 0.000549
        variants.append((f"{formula}-", neg_mass, "negative", composition, "Molecular anion"))
        
        # Common positive ion formations
        if 'H' in composition and composition['H'] > 0:
            # [M-H]+ (loss of H atom, not H+)
            mh_mass = mass - ATOMIC_MASSES['H'] - 0.000549
            if mh_mass > 0:
                variants.append((f"[{formula}-H]+", mh_mass, "positive", composition, "Hydrogen loss"))
        
        # Protonated species [M+H]+
        mh_plus_mass = mass + ATOMIC_MASSES['H'] - 0.000549
        variants.append((f"[{formula}+H]+", mh_plus_mass, "positive", composition, "Protonated"))
        
        # Deprotonated species [M-H]-
        if 'H' in composition and composition['H'] > 0:
            mh_minus_mass = mass - ATOMIC_MASSES['H'] + 0.000549
            variants.append((f"[{formula}-H]-", mh_minus_mass, "negative", composition, "Deprotonated"))
    
    return variants

def generate_alucone_specific_fragments(max_mass=200):
    """
    Generate fragments specifically relevant to alucone chemistry
    """
    fragments = []
    
    # Key alucone building blocks
    precursor_elements = ['C', 'H', 'O', 'Al']  # From TMA + butynediol
    
    # Generate comprehensive set
    base_formulas = generate_molecular_formulas(max_mass, precursor_elements)
    
    # Add charge variants
    all_variants = add_charge_variants(base_formulas)
    
    # Add common fragmentation patterns
    fragmentation_patterns = []
    
    for formula, mass, charge, composition, description in all_variants:
        fragments.append({
            'formula': formula,
            'mass': mass,
            'charge': charge,
            'description': description,
            'chemical_class': classify_fragment(composition),
            'alucone_relevance': assess_alucone_relevance(composition)
        })
    
    # Sort by mass
    fragments.sort(key=lambda x: x['mass'])
    
    return fragments

def classify_fragment(composition):
    """
    Classify fragment by chemical class
    """
    if 'Al' in composition and composition['Al'] > 0:
        if 'C' in composition and composition['C'] > 0:
            return "Al-organic_hybrid"
        elif 'O' in composition and composition['O'] > 0:
            return "Aluminum_oxide"
        else:
            return "Aluminum"
    elif 'C' in composition and composition['C'] >= 4:
        if composition['C'] >= 6:
            return "Aromatic_capable"
        else:
            return "Hydrocarbon"
    elif 'O' in composition and composition['O'] > 0:
        if 'C' in composition and composition['C'] > 0:
            return "Organic_oxygen"
        else:
            return "Oxygen"
    else:
        return "Other"

def assess_alucone_relevance(composition):
    """
    Assess how relevant fragment is to alucone chemistry
    """
    score = 0
    
    # Aluminum-containing fragments are highly relevant
    if 'Al' in composition and composition['Al'] > 0:
        score += 10
        
    # C4 chain from butynediol backbone
    if 'C' in composition and composition['C'] == 4:
        score += 5
        
    # Oxygen from diol
    if 'O' in composition and composition['O'] > 0:
        score += 3
        
    # Aromatic formation (C5+)
    if 'C' in composition and composition['C'] >= 5:
        score += 4
    
    if score >= 10:
        return "High"
    elif score >= 5:
        return "Medium"
    else:
        return "Low"

def save_fragment_database(fragments, filename, max_entries=None):
    """
    Save fragment database to CSV
    """
    if max_entries:
        fragments = fragments[:max_entries]
        
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['formula', 'mass', 'charge', 'description', 'chemical_class', 'alucone_relevance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for fragment in fragments:
            writer.writerow(fragment)
    
    print(f"Saved {len(fragments)} fragments to {filename}")

def main():
    print("🧮 COMPREHENSIVE FRAGMENT DATABASE GENERATOR")
    print("=" * 50)
    
    # Generate comprehensive database up to 200 Da
    print("\n📊 Generating alucone-specific fragments...")
    fragments = generate_alucone_specific_fragments(max_mass=200)
    
    print(f"\nGenerated {len(fragments):,} total fragments")
    
    # Filter by relevance
    high_relevance = [f for f in fragments if f['alucone_relevance'] == 'High']
    medium_relevance = [f for f in fragments if f['alucone_relevance'] == 'Medium']
    
    print(f"High relevance: {len(high_relevance):,} fragments")
    print(f"Medium relevance: {len(medium_relevance):,} fragments")
    
    # Save different databases
    save_fragment_database(fragments, 'data/comprehensive_fragments_all.csv')
    save_fragment_database(high_relevance + medium_relevance, 'data/comprehensive_fragments_relevant.csv')
    save_fragment_database(high_relevance, 'data/comprehensive_fragments_high_priority.csv')
    
    # Show some examples
    print("\n🎯 SAMPLE HIGH PRIORITY FRAGMENTS:")
    print("-" * 40)
    for fragment in high_relevance[:20]:
        print(f"{fragment['formula']:<12} {fragment['mass']:8.4f} - {fragment['description']}")
    
    print(f"\n✅ Fragment databases created!")
    print("Files saved:")
    print("• comprehensive_fragments_all.csv - Complete database")
    print("• comprehensive_fragments_relevant.csv - High + Medium relevance")
    print("• comprehensive_fragments_high_priority.csv - High relevance only")

if __name__ == "__main__":
    main()