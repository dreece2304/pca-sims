#!/usr/bin/env python3
"""Simple debug without pandas dependency"""

import sys
import os

sys.path.insert(0, 'src')

# Check the positive fragment database formulas directly
print("🔍 CHECKING POSITIVE FRAGMENT DATABASE")
print("="*45)

try:
    with open('src/positive_fragment_database.py', 'r') as f:
        content = f.read()
        
    # Look for formulas with negative signs
    lines = content.split('\n')
    negative_formulas_in_positive = []
    
    for i, line in enumerate(lines):
        if '"formula"' in line and '-' in line:
            negative_formulas_in_positive.append((i+1, line.strip()))
    
    if negative_formulas_in_positive:
        print("❌ FOUND NEGATIVE FORMULAS IN POSITIVE DATABASE:")
        for line_num, line in negative_formulas_in_positive:
            print(f"   Line {line_num}: {line}")
    else:
        print("✅ No negative formulas found in positive database")
    
    # Count positive vs negative formulas
    positive_count = content.count('"+",')
    negative_count = content.count('"-",') 
    
    print(f"\n📊 FORMULA COUNTS IN POSITIVE DATABASE:")
    print(f"   Positive formulas (+): {positive_count}")
    print(f"   Negative formulas (-): {negative_count}")
    
    if negative_count > 0:
        print(f"⚠️  WARNING: Positive database contains {negative_count} negative formulas!")
    
except Exception as e:
    print(f"❌ Error reading file: {e}")

print("\n🔍 CHECKING NEGATIVE FRAGMENT DATABASE")
print("="*45)

try:
    with open('src/fragment_database.py', 'r') as f:
        content = f.read()
        
    # Count positive vs negative formulas
    positive_count = content.count('"+",')
    negative_count = content.count('"-",')
    
    print(f"📊 FORMULA COUNTS IN NEGATIVE DATABASE:")
    print(f"   Positive formulas (+): {positive_count}")
    print(f"   Negative formulas (-): {negative_count}")
    
    if positive_count > 0:
        print(f"⚠️  WARNING: Negative database contains {positive_count} positive formulas!")
    
except Exception as e:
    print(f"❌ Error reading file: {e}")

print("\n🎯 DIAGNOSIS:")
print("If the issue persists, it might be:")
print("1. Database selection logic in Streamlit")
print("2. Caching issues in Streamlit session state")
print("3. Mixed formulas in databases")
print("4. Fragment assignment logic errors")