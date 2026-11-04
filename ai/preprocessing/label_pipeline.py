import ast
import pandas as pd

def assign_class_canonical(scp_codes_dict):
    """
    Canonical 4-class mapping for CardioGuard AI.
    Maps PTB-XL SCP-ECG codes to one of 4 research classes.
    
    0 = Normal (NORM)
    1 = AFIB (Atrial Fibrillation)
    2 = Conduction Block (LAFB, LPFB, LBBB, RBBB, CRBBB, IRBBB, 1AVB, 2AVB, 3AVB, WPW, IVCD)
    3 = Other Arrhythmia (Any other diagnosis, MI, STTC, HYP, etc.)
    
    Parameters:
    - scp_codes_dict: dictionary of scp codes e.g. {'NORM': 100.0} or string representation of it.
    
    Returns:
    - int: 0, 1, 2, or 3
    """
    if isinstance(scp_codes_dict, str):
        try:
            scp_codes_dict = ast.literal_eval(scp_codes_dict)
        except Exception:
            return 3 # Unknown falls to Other
            
    if not isinstance(scp_codes_dict, dict):
        return 3
        
    codes = set(scp_codes_dict.keys())
    
    # Hierarchy of assignment:
    # 1. AFIB is the most critical rhythm to detect in this project.
    if 'AFIB' in codes:
        return 1
        
    # 2. Conduction Blocks
    blocks = {'LAFB', 'LPFB', 'LBBB', 'RBBB', 'CRBBB', 'IRBBB', '1AVB', '2AVB', '3AVB', 'WPW', 'IVCD'}
    if not blocks.isdisjoint(codes):
        return 2
        
    # 3. Normal Sinus Rhythm (must be strictly NORM without other major pathology)
    if 'NORM' in codes:
        return 0
        
    # 4. Everything else
    return 3
