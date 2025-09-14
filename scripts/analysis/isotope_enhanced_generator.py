#!/usr/bin/env python3
"""
Enhanced Fragment Generator with Isotope Support
Generates fragments including common isotopes
"""

import csv
import itertools

# Monoisotopic masses
ATOMIC_MASSES = {
    'H': 1.007825,
    'C': 12.000000,
    'N': 14.003074,
    'O': 15.994915,
    'F': 18.998403,
    'Si': 27.976927,
    'Al': 26.981539,
    'Cl': 34.968853,
    'Na': 22.989770
}

# Common isotopes with natural abundances
ISOTOPES = {
    '13C': {'mass': 13.003355, 'abundance': 0.011},  # 1.1% per C
    '15N': {'mass': 15.000109, 'abundance': 0.0037},
    '17O': {'mass': 16.999132, 'abundance': 0.0004},
    '18O': {'mass': 17.999160, 'abundance': 0.002},
    '29Si': {'mass': 28.976495, 'abundance': 0.047},  # 4.7%
    '30Si': {'mass': 29.973770, 'abundance': 0.031},  # 3.1%
    '37Cl': {'mass': 36.965903, 'abundance': 0.32},   # 32% vs 35Cl
    '2H': {'mass': 2.014102, 'abundance': 0.00015}    # Deuterium
}

def generate_base_formulas(max_mass=200):
    """Generate base molecular formulas"""
    formulas = []
    
    # Reasonable limits for alucone system
    limits = {
        'C': min(15, int(max_mass / ATOMIC_MASSES['C'])),
        'H': min(40, int(max_mass / ATOMIC_MASSES['H'])),
        'O': min(10, int(max_mass / ATOMIC_MASSES['O'])),
        'Al': min(3, int(max_mass / ATOMIC_MASSES['Al'])),
        'Si': min(3, int(max_mass / ATOMIC_MASSES['Si'])),
        'N': min(5, int(max_mass / ATOMIC_MASSES['N'])),
        'F': min(5, int(max_mass / ATOMIC_MASSES['F'])),
        'Cl': min(2, int(max_mass / ATOMIC_MASSES['Cl'])),
        'Na': min(1, int(max_mass / ATOMIC_MASSES['Na']))
    }
    
    elements = ['C', 'H', 'O', 'Al', 'Si']  # Core alucone elements
    
    print(f"Generating base formulas with limits: {limits}")
    
    count = 0
    for c in range(limits['C'] + 1):
        for h in range(limits['H'] + 1):
            for o in range(limits['O'] + 1):
                for al in range(limits['Al'] + 1):
                    for si in range(limits['Si'] + 1):
                        count += 1
                        if count % 50000 == 0:
                            print(f"Processed {count:,} combinations...")
                        
                        # Skip empty formula
                        if c + h + o + al + si == 0:
                            continue
                            
                        # Calculate mass
                        mass = (c * ATOMIC_MASSES['C'] + 
                               h * ATOMIC_MASSES['H'] + 
                               o * ATOMIC_MASSES['O'] + 
                               al * ATOMIC_MASSES['Al'] + 
                               si * ATOMIC_MASSES['Si'])
                        
                        if mass <= max_mass:
                            composition = {'C': c, 'H': h, 'O': o, 'Al': al, 'Si': si}
                            formula_str = build_formula_string(composition)
                            formulas.append((formula_str, mass, composition))
    
    print(f"Generated {len(formulas):,} base formulas")
    return formulas

def build_formula_string(composition):
    """Build formula string from composition dict"""
    formula = ""
    for element in ['C', 'H', 'N', 'O', 'F', 'Si', 'Al', 'Cl', 'Na']:
        if element in composition and composition[element] > 0:
            if composition[element] == 1:
                formula += element
            else:
                formula += f"{element}{composition[element]}"
    return formula

def generate_isotope_variants(base_formulas, max_isotopes=2):
    """Generate isotope variants of base formulas"""
    isotope_variants = []
    
    for formula, mass, composition in base_formulas:
        # Add monoisotopic version
        isotope_variants.append((formula, mass, composition, "monoisotopic"))
        
        # 13C isotopes (most common and important)
        if 'C' in composition and composition['C'] > 0:
            for num_13c in range(1, min(composition['C'] + 1, max_isotopes + 1)):
                if num_13c <= composition['C']:
                    isotope_mass = mass + num_13c * (ISOTOPES['13C']['mass'] - ATOMIC_MASSES['C'])
                    isotope_formula = f"[{formula}+{num_13c}×13C]"
                    isotope_variants.append((isotope_formula, isotope_mass, composition, f"{num_13c}×13C"))
        
        # 29Si and 30Si isotopes (important for alucone)
        if 'Si' in composition and composition['Si'] > 0:
            for isotope in ['29Si', '30Si']:
                isotope_mass = mass + (ISOTOPES[isotope]['mass'] - ATOMIC_MASSES['Si'])
                isotope_formula = f"[{formula}+{isotope}]"
                isotope_variants.append((isotope_formula, isotope_mass, composition, isotope))
        
        # 37Cl isotope
        if 'Cl' in composition and composition['Cl'] > 0:
            isotope_mass = mass + (ISOTOPES['37Cl']['mass'] - ATOMIC_MASSES['Cl'])
            isotope_formula = f"[{formula}+37Cl]"
            isotope_variants.append((isotope_formula, isotope_mass, composition, "37Cl"))
    
    print(f"Generated {len(isotope_variants):,} isotope variants")
    return isotope_variants

def add_ion_variants(formulas):
    """Add positive and negative ion variants"""
    ion_variants = []
    
    for formula, mass, composition, isotope_type in formulas:
        # Positive ions
        pos_mass = mass - 0.000549  # Remove electron
        ion_variants.append({
            'formula': f"{formula}+",
            'mass': pos_mass,
            'charge': 'positive',
            'composition': composition,
            'isotope_type': isotope_type,
            'description': 'Molecular cation',
            'chemical_class': classify_fragment(composition),
            'alucone_relevance': assess_alucone_relevance(composition)
        })
        
        # Negative ions
        neg_mass = mass + 0.000549  # Add electron
        ion_variants.append({
            'formula': f"{formula}-",
            'mass': neg_mass,
            'charge': 'negative',
            'composition': composition,
            'isotope_type': isotope_type,
            'description': 'Molecular anion',
            'chemical_class': classify_fragment(composition),
            'alucone_relevance': assess_alucone_relevance(composition)
        })
    
    print(f"Generated {len(ion_variants):,} ion variants")
    return ion_variants

def classify_fragment(composition):
    """Classify fragment by chemical class"""
    if composition['Al'] > 0:
        if composition['C'] > 0:
            return "Al-organic_hybrid"
        elif composition['O'] > 0:
            return "Aluminum_oxide"
        else:
            return "Aluminum"
    elif composition['Si'] > 0:
        if composition['C'] > 0:
            return "Si-organic_hybrid"
        else:
            return "Silicon"
    elif composition['C'] >= 6:
        return "Aromatic_capable"
    elif composition['C'] >= 2:
        return "Hydrocarbon"
    elif composition['O'] > 0:
        return "Oxygen"
    else:
        return "Other"

def assess_alucone_relevance(composition):
    """Assess alucone relevance"""
    score = 0
    
    if composition['Al'] > 0:
        score += 10  # Aluminum is key
    if composition['C'] == 4:
        score += 5   # C4 backbone
    if composition['O'] > 0:
        score += 3   # Oxygen from diol
    if composition['C'] >= 5:
        score += 4   # Aromatic formation
    if composition['Si'] > 0:
        score += 2   # Silicon contamination/substrate
    
    if score >= 10:
        return "High"
    elif score >= 5:
        return "Medium"
    else:
        return "Low"

def save_enhanced_database(fragments, filename):
    """Save enhanced database with isotopes"""
    with open(filename, 'w', newline='') as file:
        fieldnames = ['formula', 'mass', 'charge', 'composition', 'isotope_type',
                     'description', 'chemical_class', 'alucone_relevance']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        for fragment in fragments:
            # Convert composition dict to string for CSV
            comp_str = str(fragment['composition'])
            row = fragment.copy()
            row['composition'] = comp_str
            writer.writerow(row)
    
    print(f"Saved {len(fragments):,} fragments to {filename}")

def main():
    print("🧬 ISOTOPE-ENHANCED FRAGMENT GENERATOR")
    print("=" * 50)
    
    # Generate base molecular formulas
    base_formulas = generate_base_formulas(max_mass=170)  # Leave room for isotopes
    
    # Generate isotope variants
    isotope_formulas = generate_isotope_variants(base_formulas, max_isotopes=2)
    
    # Add ion variants
    all_fragments = add_ion_variants(isotope_formulas)
    
    # Sort by mass
    all_fragments.sort(key=lambda x: x['mass'])
    
    # Filter by relevance for different databases
    high_relevance = [f for f in all_fragments if f['alucone_relevance'] == 'High']
    medium_high = [f for f in all_fragments if f['alucone_relevance'] in ['High', 'Medium']]
    
    print(f"\nTotal fragments: {len(all_fragments):,}")
    print(f"High relevance: {len(high_relevance):,}")
    print(f"Med+High relevance: {len(medium_high):,}")
    
    # Save databases
    save_enhanced_database(all_fragments, 'data/isotope_enhanced_fragments_all.csv')
    save_enhanced_database(medium_high, 'data/isotope_enhanced_fragments_relevant.csv')
    save_enhanced_database(high_relevance, 'data/isotope_enhanced_fragments_priority.csv')
    
    print("\n🎯 SAMPLE FRAGMENTS WITH ISOTOPES:")
    print("-" * 45)
    
    # Show some key examples
    for fragment in all_fragments[:30]:
        if 'Si' in fragment['formula'] or '13C' in fragment['formula']:
            print(f"{fragment['formula']:<20} {fragment['mass']:8.4f} - {fragment['isotope_type']}")
    
    print("\n✅ Enhanced databases created with isotope support!")

if __name__ == "__main__":
    main()