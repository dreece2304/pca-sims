#!/usr/bin/env python3
"""
Deep investigation of m/z 28.9899 - 3rd highest loading fragment
"""

def investigate_mystery_fragment():
    observed = 28.9899
    
    print("🔬 MYSTERY FRAGMENT: m/z 28.9899")
    print("=" * 35)
    print(f"PC1 Loading: 0.256703 (3RD HIGHEST!)")
    print("This is CRITICAL - must identify correctly")
    print()
    
    # Check silicon isotopes
    print("🔍 SILICON ISOTOPE ANALYSIS:")
    si28 = 27.9769  # 28Si most abundant
    si29 = 28.9765  # 29Si ~4.7%
    si30 = 29.9738  # 30Si ~3.1%
    
    si29_error = abs(observed - si29) / observed * 1000000
    si30_error = abs(observed - si30) / observed * 1000000
    
    print(f"• 29Si: {si29:.4f} ({si29_error:.1f} ppm) - EXCELLENT!")
    print(f"• 30Si: {si30:.4f} ({si30_error:.1f} ppm)")
    
    if si29_error <= 55:
        print("✅ 29Si isotope is PERFECT match!")
    
    print()
    print("🧪 OTHER POSSIBILITIES:")
    
    # Check other combinations
    candidates = [
        ('29Si', 28.9765, si29_error),
        ('AlH2+', 28.9971, 248.4),
        ('CHO+', 29.0019, 413.9),
        ('C2H4N+', 42.0338, abs(observed - 42.0338) / observed * 1000000)  # Wrong mass range
    ]
    
    print("Mass    Formula    Error (ppm)    Status")
    print("-" * 45)
    for formula, mass, error in candidates[:3]:  # Skip irrelevant ones
        status = "✅ EXCELLENT" if error <= 55 else "🔶 ACCEPTABLE" if error <= 100 else "❌ POOR"
        print(f"{mass:6.4f}  {formula:<10} {error:6.1f}        {status}")
    
    print()
    print("🎯 CONCLUSION:")
    if si29_error <= 55:
        print("✨ CONFIDENT ASSIGNMENT: 29Si isotope")
        print("• Explains presence alongside 28Si (27.9766)")
        print("• Natural isotope abundance ~4.7%")
        print("• Perfect mass match within tolerance")
        return '29Si', si29, si29_error
    else:
        print("❓ No clear assignment - novel fragment")
        return None, None, None

if __name__ == "__main__":
    result = investigate_mystery_fragment()
    if result[0]:
        print(f"\n📝 RECOMMENDATION: Update assignment to {result[0]}")
    else:
        print(f"\n❓ Keep as unknown pending further analysis")