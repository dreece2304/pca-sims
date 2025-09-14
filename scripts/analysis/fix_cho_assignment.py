#!/usr/bin/env python3
"""
Fix the CHO+ assignment at m/z 28.9899
413.9 ppm error is unacceptable - find correct assignment
"""

def fix_cho_assignment():
    observed = 28.9899
    
    print("🔧 FIXING CHO+ ASSIGNMENT ERROR")
    print("=" * 35)
    print(f"Observed m/z: {observed}")
    print(f"Current assignment: CHO+ (29.0019) - ERROR: 413.9 ppm")
    print()
    
    # Reference candidates from the provided data
    candidates = [
        ('C2H4+', 28.03, 'Ethylene cation'),
        ('Si+', 27.9762, 'Silicon cation'),
        ('C2H3+', 27.0233, 'Vinyl cation'),
        ('AlH+', 27.9893, 'Aluminum hydride (calculated)'),
        ('CHO+', 29.0019, 'Formyl cation (current - WRONG)')
    ]
    
    print("🧮 CHECKING ALL POSSIBILITIES:")
    print("-" * 30)
    
    best_match = None
    best_error = float('inf')
    
    for formula, ref_mass, description in candidates:
        error_ppm = abs(observed - ref_mass) / observed * 1000000
        status = "✅" if error_ppm <= 55 else "🔶" if error_ppm <= 100 else "❌"
        
        print(f"{status} {formula:<8} {ref_mass:8.4f} ({error_ppm:6.1f} ppm) - {description}")
        
        if error_ppm < best_error:
            best_error = error_ppm
            best_match = (formula, ref_mass, description, error_ppm)
    
    print()
    print("🎯 BEST MATCH:")
    if best_match:
        formula, mass, desc, error = best_match
        print(f"✨ {formula} at {mass:.4f} ({error:.1f} ppm)")
        print(f"   Description: {desc}")
        print()
        
        if error <= 55:
            print("✅ EXCELLENT match - update recommended")
        elif error <= 100:
            print("🔶 ACCEPTABLE match - consider updating")
        else:
            print("❌ Still poor match - may be novel fragment")
    
    print()
    print("🔍 CHEMICAL CONTEXT:")
    print("m/z 28.9899 has PC1 loading: 0.256703 (3rd highest!)")
    print("This is a MAJOR fragment - must get assignment right")
    print()
    
    # Check if it could be an aluminum fragment
    print("🧪 ALUMINUM CHEMISTRY CHECK:")
    al_mass = 26.9815
    alh_mass = al_mass + 1.0078
    alh2_mass = al_mass + 2 * 1.0078
    
    alh_error = abs(observed - alh_mass) / observed * 1000000
    alh2_error = abs(observed - alh2_mass) / observed * 1000000
    
    print(f"• AlH+: {alh_mass:.4f} ({alh_error:.1f} ppm)")
    print(f"• AlH2+: {alh2_mass:.4f} ({alh2_error:.1f} ppm)")
    
    return best_match

if __name__ == "__main__":
    result = fix_cho_assignment()
    if result:
        formula, mass, desc, error = result
        if error <= 100:
            print(f"\n📝 RECOMMENDATION: Update to {formula}")
        else:
            print(f"\n❓ UNCLEAR: No good standard match - may be novel alucone fragment")