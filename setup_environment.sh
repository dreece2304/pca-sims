#!/bin/bash
# Setup script for ToF-SIMS PCA environment

echo "🚀 Setting up ToF-SIMS PCA Environment"
echo "======================================"

# Remove old environment if it exists
echo "🧹 Cleaning up old environment..."
conda deactivate 2>/dev/null || true
conda env remove -n pca-sims -y 2>/dev/null || true

# Create fresh environment
echo "🆕 Creating fresh environment..."
conda create -n pca-sims python=3.11 -y

# Activate environment
echo "🔌 Activating environment..."
source /home/dreece23/miniforge3/etc/profile.d/conda.sh
conda activate pca-sims

# Install core packages via conda
echo "📦 Installing core packages..."
conda install pandas numpy scikit-learn plotly streamlit matplotlib -c conda-forge -y

# Install PySide6 via pip for better Qt6 compatibility with your native Qt 6.10.0
echo "🖼️  Installing PySide6 (compatible with Qt 6.10.0)..."
# Try specific version first, fallback to latest
pip install PySide6==6.8.0 || pip install PySide6

# Verify installation
echo "✅ Verifying installation..."
python -c "import pandas, numpy, sklearn, plotly, streamlit; print('✅ Core packages OK')"
python -c "from PySide6.QtWidgets import QApplication; print('✅ PySide6 OK')"

# Try WebEngine (may fail, that's ok)
python -c "from PySide6.QtWebEngineWidgets import QWebEngineView; print('✅ WebEngine OK')" 2>/dev/null || echo "⚠️  WebEngine not available (will use fallback)"

echo ""
echo "🎯 Environment setup complete!"
echo "📋 To use:"
echo "   conda activate pca-sims"
echo "   python launch_optimized.py"
echo ""