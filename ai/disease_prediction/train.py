"""
    DocMindX AI - Disease Prediction Machine Learning Model Trainer
Trains a clinical decision model and serializes weights to model.pkl.
"""
import os
import sys
import pickle
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sklearn.ensemble import RandomForestClassifier
from ai.disease_prediction.preprocessing import build_feature_matrix

def train_disease_model():
    """Trains a Random Forest classifier over the clinical symptom bipartite graph."""
    X, y, symptom_list = build_feature_matrix()
    if X.shape[0] < 2:
        print("Insufficient training data")
        return False

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)

    model_payload = {
        "model": clf,
        "symptom_features": symptom_list,
        "classes": clf.classes_.tolist()
    }

    out_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(model_payload, f)

    # Also save in models/
    models_dir_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "disease_model.pkl")
    with open(models_dir_path, "wb") as f:
        pickle.dump(model_payload, f)

    print(f"[OK] Successfully trained disease model with {len(clf.classes_)} classes and {len(symptom_list)} features.")
    return True

if __name__ == "__main__":
    train_disease_model()
