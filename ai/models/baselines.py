from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

def get_svm_model():
    return SVC(probability=True, random_state=42)

def get_rf_model():
    return RandomForestClassifier(n_estimators=100, random_state=42)

def get_dt_model():
    return DecisionTreeClassifier(random_state=42)
