#!/usr/bin/env python3
"""
Test comprehensive fragment database against unknown assignments
"""

import csv

def load_fragment_database(filename):
    """Load fragment database from CSV"""
    fragments = {}
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mass = float(row['mass'])
            fragments[mass] = row
    return fragments

def find_matches(observed_mz, database, tolerance_ppm=55):
    """Find all matches within tolerance"""
    matches = []
    
    for db_mass, fragment_data in database.items():
        error_ppm = abs(observed_mz - db_mass) / observed_mz * 1000000
        
        if error_ppm <= tolerance_ppm:
            matches.append({
                'formula': fragment_data['formula'],
                'mass': db_mass,
                'error_ppm': error_ppm,
                'charge': fragment_data['charge'],
                'description': fragment_data['description'],
                'chemical_class': fragment_data['chemical_class'],
                'alucone_relevance': fragment_data['alucone_relevance']
            })
    
    # Sort by error
    matches.sort(key=lambda x: x['error_ppm'])
    return matches

def test_unknowns():
    """Test unknown fragments against comprehensive database"""
    
    # Load comprehensive database
    print("📚 Loading comprehensive fragment database...")
    database = load_fragment_database('data/comprehensive_fragments_relevant.csv')
    print(f"Loaded {len(database):,} fragments")
    
    # Unknown positive ions to test
    unknown_positive = [
        (28.9899, 'Unknown (was CHO+)', 0.256703),  # 3rd highest
        (77.0296, 'Unknown', 0.090565),             # 8th highest  
        (57.0232, 'Unknown', 0.077507),             # 11th highest
        (52.9919, 'Unknown', 0.048309),
        (42.0144, 'Unknown', 0.047264),
        (79.0001, 'Unknown', 0.040879),
        (31.0165, 'Unknown', 0.036001),
        (55.0181, 'Unknown', 0.032093),
        (78.0405, 'Unknown', 0.030977),
        (165.0597, 'Unknown', 0.030517),
        (129.0558, 'Unknown', 0.030399),
        (127.0508, 'Unknown', 0.029889)
    ]
    
    print("\n🔍 TESTING UNKNOWN POSITIVE IONS:")
    print("=" * 60)
    
    results = []
    
    for obs_mz, current, loading in unknown_positive:
        print(f"\n📍 m/z {obs_mz} (PC1: {loading}) - {current}")
        print("-" * 45)
        
        matches = find_matches(obs_mz, database, tolerance_ppm=55)
        
        if matches:
            print(f"Found {len(matches)} matches within 55 ppm:")
            
            # Show top 5 matches
            for i, match in enumerate(matches[:5]):
                status = "✅" if match['error_ppm'] <= 25 else "🔶"
                print(f"{status} {match['formula']:<12} {match['mass']:8.4f} "
                      f"({match['error_ppm']:4.1f} ppm) - {match['description']}")
                
                if i == 0:  # Best match
                    results.append({
                        'mz': obs_mz,
                        'pc1_loading': loading,
                        'best_formula': match['formula'],
                        'best_mass': match['mass'],
                        'error_ppm': match['error_ppm'],
                        'chemical_class': match['chemical_class'],
                        'alucone_relevance': match['alucone_relevance'],
                        'num_matches': len(matches)
                    })
        else:
            print("❌ No matches found within 55 ppm tolerance")
            results.append({
                'mz': obs_mz,
                'pc1_loading': loading,
                'best_formula': None,
                'best_mass': None,
                'error_ppm': None,
                'chemical_class': None,
                'alucone_relevance': None,
                'num_matches': 0
            })
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 30)
    
    assigned = len([r for r in results if r['best_formula'] is not None])
    total = len(results)
    
    print(f"Successfully assigned: {assigned}/{total} ({assigned/total*100:.1f}%)")
    
    high_priority_assigned = len([r for r in results if r['best_formula'] is not None and r['pc1_loading'] > 0.05])
    high_priority_total = len([r for r in results if r['pc1_loading'] > 0.05])
    
    print(f"High priority (PC1>0.05): {high_priority_assigned}/{high_priority_total}")
    
    # Save results
    with open('comprehensive_assignment_results.csv', 'w', newline='') as file:
        fieldnames = ['mz', 'pc1_loading', 'best_formula', 'best_mass', 'error_ppm', 
                     'chemical_class', 'alucone_relevance', 'num_matches']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n💾 Results saved to: comprehensive_assignment_results.csv")
    
    return results

if __name__ == "__main__":
    results = test_unknowns()