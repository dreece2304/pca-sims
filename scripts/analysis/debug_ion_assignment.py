#!/usr/bin/env python3
"""
Debug ion mode assignment issue
Check if positive ion mode is assigning negative ions
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

try:
    from fragment_database import AluconeFragmentDatabase
    from positive_fragment_database import AluconePositiveFragmentDatabase
    
    print("🔍 ION ASSIGNMENT DEBUG")
    print("="*40)
    
    # Create both databases
    neg_db = AluconeFragmentDatabase()
    pos_db = AluconePositiveFragmentDatabase()
    
    print(f"✅ Negative DB: {len(neg_db.fragments)} fragments")
    print(f"✅ Positive DB: {len(pos_db.fragments)} fragments")
    
    # Check for formula consistency
    print(f"\n🧪 CHECKING FORMULA CONSISTENCY:")
    print("-" * 35)
    
    # Check negative database formulas
    neg_formulas = []
    for name, frag in neg_db.fragments.items():
        formula = frag['formula']
        neg_formulas.append(formula)
        if '+' in formula:
            print(f"⚠️  NEGATIVE DB has positive formula: {name} = {formula}")
    
    # Check positive database formulas  
    pos_formulas = []
    for name, frag in pos_db.fragments.items():
        formula = frag['formula']
        pos_formulas.append(formula)
        if '-' in formula:
            print(f"⚠️  POSITIVE DB has negative formula: {name} = {formula}")
    
    print(f"\n📊 FORMULA STATISTICS:")
    print(f"   Negative DB: {sum(1 for f in neg_formulas if '-' in f)} negative, {sum(1 for f in neg_formulas if '+' in f)} positive")
    print(f"   Positive DB: {sum(1 for f in pos_formulas if '+' in f)} positive, {sum(1 for f in pos_formulas if '-' in f)} negative")
    
    # Test fragment identification
    print(f"\n🔬 TESTING FRAGMENT IDENTIFICATION:")
    print("-" * 40)
    
    test_masses = [
        (26.9815, "Al+ (should be in positive DB)"),
        (26.9815, "Al- (should be in negative DB)"), 
        (73.0078, "C6H+ (should be in positive DB)"),
        (73.0078, "C6H- (should be in negative DB)")
    ]
    
    for mz, expected in test_masses:
        # Test negative database
        neg_match = neg_db.get_fragment_by_mz(mz, tolerance=0.01)
        neg_result = neg_match['formula'] if neg_match else "Not found"
        
        # Test positive database
        pos_match = pos_db.get_fragment_by_mz(mz, tolerance=0.01)
        pos_result = pos_match['formula'] if pos_match else "Not found"
        
        print(f"m/z {mz:.4f} ({expected}):")
        print(f"   Negative DB: {neg_result}")
        print(f"   Positive DB: {pos_result}")
        
        # Check for cross-contamination
        if neg_match and '+' in neg_match['formula']:
            print(f"   ❌ PROBLEM: Negative DB returning positive formula!")
        if pos_match and '-' in pos_match['formula']:
            print(f"   ❌ PROBLEM: Positive DB returning negative formula!")
        print()
    
    print("🎯 DIAGNOSIS COMPLETE")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")