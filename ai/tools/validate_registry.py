import json
import os
import sys

def main():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "config", "registry.json")
    if not os.path.exists(registry_path):
        print(f"FAIL: Registry not found at {registry_path}")
        sys.exit(1)
        
    with open(registry_path, "r") as f:
        registry = json.load(f)
        
    paths_to_check = {
        "Artifact Path": registry.get("artifact_path"),
        "Scaler Path": registry.get("scaler_path"),
        "SHAP Background": registry.get("shap_background_path")
    }
    
    all_passed = True
    print(f"Validating Model Registry version {registry.get('version')}")
    print("-" * 50)
    for name, path in paths_to_check.items():
        if not path:
            print(f"FAIL: {name} is missing in registry.")
            all_passed = False
            continue
            
        if os.path.exists(path):
            print(f"PASS: {name} exists ({path})")
        else:
            print(f"FAIL: {name} DOES NOT EXIST ({path})")
            all_passed = False
            
    print("-" * 50)
    if all_passed:
        print("ALL REGISTRY PATHS VALIDATED.")
        sys.exit(0)
    else:
        print("REGISTRY VALIDATION FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
