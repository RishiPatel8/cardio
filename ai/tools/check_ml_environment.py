import sys
import platform

def check_env():
    print("=" * 40)
    print("Environment Check")
    print("=" * 40)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    
    packages = ["numpy", "pandas", "sklearn", "imblearn", "shap"]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            print(f"{pkg}: PASS ({getattr(mod, '__version__', 'unknown')})")
        except ImportError:
            print(f"{pkg}: FAIL (PACKAGE MISSING)")

    print("-" * 40)
    try:
        import tensorflow as tf
        print(f"TensorFlow: PASS ({tf.__version__})")
    except ImportError as e:
        if "DLL load failed" in str(e) or "Application Control" in str(e):
            print("TensorFlow: FAIL (OS / DLL / Application Control BLOCKED)")
        else:
            print("TensorFlow: FAIL (PACKAGE MISSING OR OTHER IMPORT ERROR)")
        print(f"Details: {repr(e)}")
    print("=" * 40)

if __name__ == "__main__":
    check_env()
