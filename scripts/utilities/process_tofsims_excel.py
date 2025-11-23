#!/usr/bin/env python3
"""
Process ToF-SIMS Excel files with fragment assignments and intensity data

Usage:
    python scripts/utilities/process_tofsims_excel.py <excel_file> <polarity> [output_file]

Arguments:
    excel_file: Path to Excel file with fragment assignments and intensities
    polarity: Ion polarity ("positive" or "negative")
    output_file: Optional output path for tab-delimited file (default: auto-generated)

Example:
    python scripts/utilities/process_tofsims_excel.py \\
        data/PositiveIon/AllPosNewwithFragment.xlsx \\
        positive \\
        data/PositiveIon/AllPosNew_processed.txt
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tofsims_excel_processor import process_tofsims_excel


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    excel_file = sys.argv[1]
    polarity = sys.argv[2].lower()

    if polarity not in ["positive", "negative"]:
        print("❌ Error: Polarity must be 'positive' or 'negative'")
        sys.exit(1)

    # Auto-generate output filename if not provided
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]
    else:
        # Generate output filename from input
        excel_path = Path(excel_file)
        output_file = excel_path.parent / f"{excel_path.stem}_processed.txt"

    # Process the file
    print(f"📊 ToF-SIMS Excel Processor")
    print(f"=" * 60)
    print(f"Input file: {excel_file}")
    print(f"Polarity: {polarity}")
    print(f"Output file: {output_file}")
    print()

    try:
        df, stats = process_tofsims_excel(
            excel_file,
            polarity=polarity,
            output_path=str(output_file)
        )

        print(f"\n✅ SUCCESS!")
        print(f"   Processed: {stats['unique_mz_values']} unique m/z values")
        print(f"   Samples: {stats['sample_columns']}")
        print(f"   Duplicates merged: {stats['duplicates_removed']}")
        print(f"   New fragments added: {stats['new_fragments_added']}")
        print(f"\n   Output saved to: {output_file}")
        print(f"\n   You can now load this file in the PCA application!")

    except Exception as e:
        print(f"\n❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
