#!/usr/bin/env python3
"""Quick correlation test to check what we have"""

import os

def quick_test():
    print("🔍 QUICK CORRELATION TEST")
    print("="*40)
    
    # Check for CSV files
    files_to_check = [
        "negative_ion_assignments.csv",
        "positive_ion_assignments.csv", 
        "fragment_assignment_report.csv"
    ]
    
    found_files = []
    
    for filename in files_to_check:
        if os.path.exists(filename):
            found_files.append(filename)
            print(f"✅ Found: {filename}")
            
            # Quick peek at file contents
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    print(f"   📊 {len(lines)-1} data rows")
                    if len(lines) > 1:
                        header = lines[0].strip()
                        print(f"   📋 Columns: {header}")
                        
                        # Look for key fragments
                        aluminum_count = 0
                        carbon_count = 0
                        for line in lines[1:]:
                            if 'Al' in line:
                                aluminum_count += 1
                            if 'C6H' in line:
                                carbon_count += 1
                        
                        print(f"   🔍 Aluminum fragments: {aluminum_count}")
                        print(f"   🟣 C6H fragments: {carbon_count}")
                        print()
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
        else:
            print(f"❌ Not found: {filename}")
    
    if len(found_files) >= 2:
        print(f"🎯 READY FOR CORRELATION ANALYSIS!")
        print(f"   Found {len(found_files)} data files")
        return True
    else:
        print(f"⚠️  Need at least 2 files for correlation analysis")
        print(f"   Found only {len(found_files)} files")
        return False

def analyze_aluminum_simple(filename):
    """Simple aluminum fragment analysis"""
    if not os.path.exists(filename):
        return []
    
    aluminum_fragments = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            return []
        
        header = lines[0].strip().split(',')
        
        # Find relevant columns
        mz_col = None
        formula_col = None
        loading_col = None
        
        for i, col in enumerate(header):
            if 'm/z' in col:
                mz_col = i
            elif 'Formula' in col or 'Fragment' in col:
                formula_col = i
            elif 'Loading' in col:
                loading_col = i
        
        # Look for aluminum fragments
        for line in lines[1:]:
            values = line.strip().split(',')
            if len(values) > max(mz_col or 0, formula_col or 0):
                try:
                    mz = float(values[mz_col]) if mz_col is not None else 0
                    formula = values[formula_col] if formula_col is not None else ''
                    loading = values[loading_col] if loading_col is not None else '0'
                    
                    # Check for aluminum
                    if 'Al' in formula or abs(mz - 26.9815) < 0.01:
                        aluminum_fragments.append({
                            'mz': mz,
                            'formula': formula,
                            'loading': loading
                        })
                except:
                    continue
    
    return aluminum_fragments

def main():
    has_data = quick_test()
    
    if has_data:
        print("\n🔍 ALUMINUM CHEMISTRY QUICK CHECK")
        print("-"*40)
        
        # Check positive ions for aluminum
        pos_file = "positive_ion_assignments.csv"
        if os.path.exists(pos_file):
            pos_al = analyze_aluminum_simple(pos_file)
            print(f"Positive Al fragments: {len(pos_al)}")
            for frag in pos_al[:3]:  # Show first 3
                print(f"   • {frag['formula']} (m/z {frag['mz']:.4f})")
        
        # Check negative ions for aluminum
        neg_file = "negative_ion_assignments.csv"
        if os.path.exists(neg_file):
            neg_al = analyze_aluminum_simple(neg_file)
            print(f"Negative Al fragments: {len(neg_al)}")
            for frag in neg_al[:3]:  # Show first 3
                print(f"   • {frag['formula']} (m/z {frag['mz']:.4f})")
        
        # Quick conclusion about m/z 41.0036
        print(f"\n🎯 PRELIMINARY CONCLUSION:")
        if os.path.exists(pos_file):
            pos_al_count = len(analyze_aluminum_simple(pos_file))
            if pos_al_count > 0:
                print(f"   Al+ detected → m/z 41.0036 likely C2HO- (ketene)")
            else:
                print(f"   No Al+ detected → Need to verify aluminum presence")
        
        print(f"\n🚀 To run full analysis:")
        print(f"   python3 pos_neg_correlation_analysis.py")
    
    else:
        print(f"\n📋 TO GET CORRELATION DATA:")
        print(f"1. Run Streamlit with negative ion data")
        print(f"2. Export assignments as 'negative_ion_assignments.csv'")
        print(f"3. Run Streamlit with positive ion data")
        print(f"4. Export assignments as 'positive_ion_assignments.csv'")
        print(f"5. Run this analysis again")

if __name__ == "__main__":
    main()