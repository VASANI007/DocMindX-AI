"""
    DocMindX AI - Clinical Symptom Preprocessing & Feature Engineering
"""
import os
import pandas as pd
import numpy as np

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")

def load_symptoms_and_diseases():
    """Loads master taxonomy data for symptom-disease training."""
    symptoms_path = os.path.join(DATASETS_DIR, "symptoms", "symptoms_master.csv")
    mapping_path = os.path.join(DATASETS_DIR, "disease", "disease_symptom_mapping.csv")
    diseases_path = os.path.join(DATASETS_DIR, "disease", "disease_master.csv")

    df_sym = pd.read_csv(symptoms_path, encoding="utf-8") if os.path.exists(symptoms_path) else pd.DataFrame()
    df_map = pd.read_csv(mapping_path, encoding="utf-8") if os.path.exists(mapping_path) else pd.DataFrame()
    df_dis = pd.read_csv(diseases_path, encoding="utf-8") if os.path.exists(diseases_path) else pd.DataFrame()

    return df_sym, df_map, df_dis

def build_feature_matrix():
    """
    Creates a binary symptom indicator matrix (X) and disease target label (y)
    from clinical disease-symptom probability mappings.
    """
    df_sym, df_map, df_dis = load_symptoms_and_diseases()
    if df_map.empty or df_sym.empty:
        return np.zeros((1, 1)), np.zeros((1,)), []

    symptom_list = sorted(df_sym["symptom_id"].unique().tolist())
    sym_idx = {sid: i for i, sid in enumerate(symptom_list)}

    rows = []
    labels = []

    for dis_id, group in df_map.groupby("disease_id"):
        # Synthetic sampling weighted by clinical symptom frequency
        vec = np.zeros(len(symptom_list))
        for _, row in group.iterrows():
            sid = row.get("symptom_id")
            if sid in sym_idx:
                vec[sym_idx[sid]] = 1.0
        
        rows.append(vec)
        labels.append(dis_id)

    X = np.array(rows)
    y = np.array(labels)
    return X, y, symptom_list
