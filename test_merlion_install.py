"""Quick test to verify Merlion installation"""

import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

try:
    import numpy
    print(f"✅ NumPy {numpy.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import scipy
    print(f"✅ SciPy {scipy.__version__}")
except ImportError as e:
    print(f"❌ SciPy: {e}")

try:
    import pandas
    print(f"✅ Pandas {pandas.__version__}")
except ImportError as e:
    print(f"❌ Pandas: {e}")

try:
    import sklearn
    print(f"✅ Scikit-learn {sklearn.__version__}")
except ImportError as e:
    print(f"❌ Scikit-learn: {e}")

try:
    from merlion.models.anomaly import IsolationForest
    print(f"✅ Merlion IsolationForest imported successfully!")
    print("\n🎉 ALL DEPENDENCIES INSTALLED CORRECTLY!")
except ImportError as e:
    print(f"❌ Merlion: {e}")
    print("\nTroubleshooting: Run these commands:")
    print("  pip install --upgrade pip")
    print("  pip install -r requirements.txt")