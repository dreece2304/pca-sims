#!/usr/bin/env python3
"""
Process dose-trajectory statistical analysis (ANOVA and regression).
"""

from analyze_fragment_statistics import analyze_dose_trajectory
from pathlib import Path


if __name__ == '__main__':
    print("="*80)
    print("PROCESSING DOSE-TRAJECTORY STATISTICAL ANALYSES")
    print("="*80)

    for ion_mode in ['Positive', 'Negative']:
        print(f"\nProcessing {ion_mode.upper()} ion mode...")

        intensity_file = f'outputs/Dose-Trajectory/{ion_mode}/fragment_intensities.csv'
        output_file = f'outputs/Dose-Trajectory/{ion_mode}/dose_trajectory_statistics.csv'

        result = analyze_dose_trajectory(intensity_file, ion_mode.lower())
        result.to_csv(output_file, index=False)

        # Summary stats
        n_sig_anova = result['anova_significant'].sum()
        n_linear = result['linear_trend'].sum()
        n_total = len(result)

        print(f"  ✓ Saved: {output_file}")
        print(f"  ANOVA significant: {n_sig_anova}/{n_total}")
        print(f"  Linear trends: {n_linear}/{n_total}")

        # Trend breakdown
        print("\n  Trend classification:")
        trend_counts = result['trend_type'].value_counts()
        for trend, count in trend_counts.items():
            print(f"    {trend}: {count}")

        # Show top linear trends
        linear_df = result[result['linear_trend'] == True].copy()
        if len(linear_df) > 0:
            linear_df['abs_slope'] = linear_df['slope'].abs()
            linear_df = linear_df.sort_values('abs_slope', ascending=False)

            print(f"\n  Top 5 linear trends by |slope|:")
            print(linear_df[['m/z', 'Fragment', 'slope', 'R_squared', 'trend_type']].head(5).to_string(index=False))

    print("\n" + "="*80)
    print("DOSE-TRAJECTORY STATISTICS COMPLETED")
    print("="*80)
