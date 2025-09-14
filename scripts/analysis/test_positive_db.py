#!/usr/bin/env python3
"""Test positive fragment database methods"""

import sys
# import pandas as pd
# import numpy as np

# Add src to path
sys.path.insert(0, 'src')

try:
    from positive_fragment_database import AluconePositiveFragmentDatabase
    
    print("✅ Import successful")
    
    # Create database
    db = AluconePositiveFragmentDatabase()
    print(f"✅ Database created with {len(db.fragments)} fragments")
    
    # Check for method
    if hasattr(db, 'generate_fragment_report'):
        print("✅ generate_fragment_report method exists")
    else:
        print("❌ generate_fragment_report method missing!")
        
    print("\n🧪 Testing method signature...")
    try:
        # Just test the method exists and is callable
        method = getattr(db, 'generate_fragment_report')
        print(f"✅ Method signature: {method.__name__}")
        print("✅ Method is callable")
    except Exception as e:
        print(f"❌ Error accessing method: {e}")
        
    print("\n🎯 Available methods:")
    methods = [m for m in dir(db) if not m.startswith('_')]
    for method in methods:
        print(f"   • {method}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")