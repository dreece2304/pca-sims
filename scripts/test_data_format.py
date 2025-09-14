"""
Test script to validate P1_SQ1 data format parsing
Run this after creating the mamba environment
"""

import pandas as pd
import numpy as np
import sys
import os

def create_test_data():
    """
    Create test data in P1_SQ1 format for validation
    """
    print("Creating test data in P1_SQ1 format...")
    
    # Create sample mass values (1-100 m/z)
    masses = np.linspace(1, 100, 100)
    
    # Create sample names in P1_SQ1 format
    # 3 patterns (P1, P2, P3), each with 5 squares (SQ1-SQ5)  
    sample_names = []
    for pattern in [1, 2, 3]:
        for square in [1, 2, 3, 4, 5]:
            sample_names.append(f"P{pattern}_SQ{square}")
    
    print(f"Sample names: {sample_names}")
    
    # Create random intensity data (simulate ToF-SIMS data)
    np.random.seed(42)  # For reproducible results
    
    data = {}
    data['Mass (u)'] = masses
    
    # Add different patterns to simulate real biological differences
    for i, sample_name in enumerate(sample_names):
        pattern_num = int(sample_name.split('_')[0][1])  # Extract pattern number
        
        # Base intensity with some pattern-specific differences
        base_intensity = np.random.exponential(0.01, len(masses))
        
        # Add pattern-specific peaks (simulate biological differences)
        if pattern_num == 1:
            base_intensity[20:25] *= 2  # Higher intensity at m/z 21-25
        elif pattern_num == 2:  
            base_intensity[30:35] *= 2  # Higher intensity at m/z 31-35
        elif pattern_num == 3:
            base_intensity[40:45] *= 2  # Higher intensity at m/z 41-45
        
        # Add some noise
        base_intensity += np.random.normal(0, 0.001, len(masses))
        base_intensity = np.maximum(base_intensity, 0)  # Ensure non-negative
        
        data[sample_name] = base_intensity
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save test data
    test_file = "/home/dreece23/pca-sims/data/test_P1_SQ_format.txt"
    df.to_csv(test_file, sep='\t', index=False)
    print(f"Test data saved to: {test_file}")
    
    return test_file

def test_parsing():
    """
    Test the sample name parsing logic
    """
    print("\\nTesting P1_SQ1 format parsing...")
    
    sample_names = ["P1_SQ1", "P1_SQ2", "P2_SQ1", "P2_SQ3", "P3_SQ5"]
    
    for sample_name in sample_names:
        if '_' in sample_name:
            parts = sample_name.split('_')
            if len(parts) >= 2:
                pattern = parts[0]  # P1, P2, P3
                square = parts[1]   # SQ1, SQ2, etc.
                
                # Extract numeric values
                import re
                pattern_num = int(re.findall(r'\\d+', pattern)[0]) if re.findall(r'\\d+', pattern) else 0
                square_num = int(re.findall(r'\\d+', square)[0]) if re.findall(r'\\d+', square) else 0
                
                print(f"  {sample_name} -> Pattern: {pattern} ({pattern_num}), Square: {square} ({square_num})")

if __name__ == "__main__":
    print("=== Testing P1_SQ1 Data Format ===")
    
    # Test parsing logic
    test_parsing()
    
    # Create test data
    test_file = create_test_data()
    
    print(f"\\n=== Test completed ===")
    print(f"Test data available at: {test_file}")
    print("\\nNext steps:")
    print("1. Create mamba environment with provided commands")
    print("2. Activate environment: mamba activate pca-sims")  
    print("3. Test PCA implementation: python src/tof_sims_pca.py")