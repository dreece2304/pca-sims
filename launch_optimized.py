#!/usr/bin/env python3
"""
Optimized launcher for ToF-SIMS PCA with native Qt6 + WebEngine
Works with fresh mamba environment and native Qt6 installation
"""

import subprocess
import sys
import os
from pathlib import Path

def detect_qt6_installation():
    """Detect Qt6 installation and return best version"""
    qt_base = Path("/home/dreece23/Qt")

    # Prefer newer stable versions
    qt_versions = ["6.10.0", "6.9.2", "6.9.1", "6.8.3"]

    for version in qt_versions:
        qt_path = qt_base / version / "gcc_64"
        if qt_path.exists():
            # Verify essential components
            required_libs = [
                "libQt6Core.so",
                "libQt6Gui.so",
                "libQt6Widgets.so",
                "libQt6WebEngineWidgets.so"
            ]

            lib_path = qt_path / "lib"
            if all((lib_path / lib).exists() for lib in required_libs):
                return qt_path, version

    return None, None

def setup_environment(qt_path):
    """Setup optimized environment for Qt6 + PySide6"""
    env = os.environ.copy()

    # Qt6 native paths (highest priority)
    env['QTDIR'] = str(qt_path)
    env['QT_PLUGIN_PATH'] = str(qt_path / "plugins")
    env['QML2_IMPORT_PATH'] = str(qt_path / "qml")

    # Library path - Qt6 first, then system
    qt_lib = str(qt_path / "lib")
    env['LD_LIBRARY_PATH'] = f"{qt_lib}:{env.get('LD_LIBRARY_PATH', '')}"

    # Binary path
    qt_bin = str(qt_path / "bin")
    env['PATH'] = f"{qt_bin}:{env['PATH']}"

    # Display and platform
    env['QT_QPA_PLATFORM'] = 'xcb'
    env['DISPLAY'] = env.get('DISPLAY', ':0')

    # Silence Qt warnings
    env['QT_LOGGING_RULES'] = 'qt.qpa.plugin.debug=false'

    # Python module path
    env['PYTHONPATH'] = str(Path(__file__).parent / "src")

    return env

def test_environment():
    """Test the environment setup"""
    print("🧪 Testing environment setup...")

    try:
        # Test basic Qt import
        result = subprocess.run([
            "bash", "-c",
            "source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python -c \"from PySide6.QtCore import QCoreApplication; print('✅ PySide6 Core OK')\""
        ], capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            print(f"❌ PySide6 test failed: {result.stderr}")
            return False

        print(result.stdout.strip())

        # Test WebEngine import
        result = subprocess.run([
            "bash", "-c",
            "source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python -c \"from PySide6.QtWebEngineWidgets import QWebEngineView; print('✅ WebEngine OK')\""
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print("📊 Using native matplotlib plotting (preferred method)")

        return True

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 ToF-SIMS PCA Optimized Launcher")
    print("=" * 50)

    # Step 1: Detect Qt6
    qt_path, qt_version = detect_qt6_installation()
    if not qt_path:
        print("❌ No suitable Qt6 installation found in ~/Qt/")
        print("💡 Install Qt6 with WebEngine from qt.io")
        return False

    print(f"✅ Using Qt {qt_version} at: {qt_path}")

    # Step 2: Setup environment
    env = setup_environment(qt_path)

    # Step 3: Test environment
    if not test_environment():
        print("❌ Environment test failed")
        print("💡 Try: conda env remove -n pca-sims && conda create -n pca-sims python=3.11")
        return False

    # Step 4: Launch application
    print("\n🚀 Launching ToF-SIMS PCA Application...")
    print("🎯 Enabled features:")
    print(f"  ✅ Qt {qt_version} with native plotting")
    print("  ✅ Publication-quality matplotlib visualizations")
    print("  ✅ Group-based sample management")
    print("  ✅ Threaded PCA computation")
    print("  ✅ Multi-sheet Excel export functionality")
    print("-" * 50)

    app_path = Path(__file__).parent / "src" / "pyside_app_matplotlib.py"

    cmd = [
        "bash", "-c",
        f"source /home/dreece23/miniforge3/etc/profile.d/conda.sh && conda activate pca-sims && python {app_path}"
    ]

    try:
        subprocess.run(cmd, env=env)
        return True
    except KeyboardInterrupt:
        print("\n👋 Application closed")
        return True
    except Exception as e:
        print(f"❌ Launch failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n🔧 Troubleshooting:")
        print("  1. Recreate conda environment: conda env remove -n pca-sims")
        print("  2. Install fresh: conda create -n pca-sims python=3.11")
        print("  3. Install PySide6: pip install PySide6")
        print("  4. Verify Qt6 in ~/Qt/ with WebEngine")
        sys.exit(1)