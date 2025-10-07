"""
Test script to verify loadings data source consistency
"""
import sys
sys.path.append('src')

from simple_tof_sims_pca import SimpleToFSIMSPCA
import numpy as np

print("=" * 70)
print("Testing PCA Loadings Data Source")
print("=" * 70)

# Load data
data_file = "data/PositiveIon/PosAllCompoundSearch.txt"
print(f"\n📁 Loading: {data_file}")

pca = SimpleToFSIMSPCA(data_file)
pca.load_data()

print(f"\n📊 Original data shape: {pca.raw_data.shape}")
print(f"   Mass range: {pca.mass_values.min():.3f} - {pca.mass_values.max():.3f}")

# Select only SQ0 and SQ2 samples
print("\n🎯 Selecting only SQ0 and SQ2 samples...")
import pandas as pd
mask = pca.sample_metadata['dose_id'].isin([0, 2])
selected_samples = pca.sample_metadata.loc[mask, 'sample_name'].tolist()
print(f"   Selected samples: {selected_samples}")
print(f"   Total: {len(selected_samples)} samples")

# Update working data to only include selected samples
pca.working_data = pca.raw_data[selected_samples].copy()
pca.working_metadata = pca.sample_metadata[mask].copy()
pca.sample_mask = mask.values

print(f"   Working data shape: {pca.working_data.shape}")

# Apply preprocessing with transformations
print("\n🔧 Applying preprocessing:")
print("   - Square root transformation: YES")
print("   - Filter contamination peaks: YES")

pca.preprocess_data(
    sqrt_transform=True,
    filter_contamination_peaks=True,
    pareto_scale=False
)

print(f"\n📊 After preprocessing:")
print(f"   Preprocessed data shape: {pca.preprocessed_data.shape}")
if hasattr(pca, 'current_mass_values'):
    print(f"   Current mass values: {len(pca.current_mass_values)} masses")
    print(f"   Mass range: {pca.current_mass_values.min():.3f} - {pca.current_mass_values.max():.3f}")
    print(f"   First 10 masses: {pca.current_mass_values[:10]}")
else:
    print("   ⚠️  No current_mass_values attribute!")

# Run PCA
print("\n🔬 Running PCA...")
pca.run_pca(n_components=5)

print(f"\n📈 PCA Results:")
print(f"   Loadings shape: {pca.loadings.shape}")
print(f"   PC1 variance explained: {pca.explained_variance_ratio[0]*100:.1f}%")

# Get loadings dataframe (same as GUI does)
print("\n🔍 Getting loadings dataframe...")
loadings_df = pca.get_loadings_dataframe()

print(f"\n📊 Loadings DataFrame:")
print(f"   Shape: {loadings_df.shape}")
print(f"   Index type: {type(loadings_df.index)}")
print(f"   Index values (first 10): {loadings_df.index[:10].tolist()}")
print(f"   PC1 range: {loadings_df['PC1'].min():.6f} to {loadings_df['PC1'].max():.6f}")

# Get top loadings (same calculation as both plot and table)
print("\n🔝 Top 10 PC1 Loadings (by absolute value):")
top_loadings = loadings_df['PC1'].abs().sort_values(ascending=False).head(10)

for i, (mass, abs_val) in enumerate(top_loadings.items(), 1):
    original_val = loadings_df.loc[mass, 'PC1']
    print(f"   {i:2d}. m/z {mass:8.4f}: loading={original_val:+.6f}, |loading|={abs_val:.6f}")

print("\n" + "=" * 70)
print(f"✅ TOP LOADING: m/z {top_loadings.index[0]:.4f}")
print("=" * 70)

# Check if contamination masses were actually removed
print("\n🧪 Verifying contamination filtering:")
contamination_check = [15.0, 23.0, 39.0, 41.0, 44.0, 78.0]
for mass in contamination_check:
    # Check if mass is within 0.1 of any index value
    close_matches = loadings_df.index[np.abs(loadings_df.index - mass) < 0.1]
    if len(close_matches) > 0:
        print(f"   ⚠️  Contamination mass {mass:.1f} still present: {close_matches.tolist()}")
    else:
        print(f"   ✅ Contamination mass {mass:.1f} removed")
