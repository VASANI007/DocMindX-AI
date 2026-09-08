"""
    DocMindX AI - Medicine Search & Formulary Lookup Engine
"""
import os
import pandas as pd

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")

class MedicineSearchEngine:
    """Provides rapid search across clinical formulary and master medicine catalogs."""
    def __init__(self):
        self.df_medicines = self._load_medicines()

    def _load_medicines(self):
        csv_path = os.path.join(DATASETS_DIR, "medicines", "medicines_master.csv")
        if os.path.exists(csv_path):
            try:
                return pd.read_csv(csv_path, encoding="utf-8")
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    def search_medicine(self, query: str, limit: int = 10) -> list:
        if not query or not isinstance(query, str) or not query.strip():
            return []
        
        q_lower = query.lower().strip()
        if self.df_medicines.empty:
            return []

        # Search across medicine name, generic name, brands, indications
        mask = (
            self.df_medicines["medicine_name"].str.lower().str.contains(q_lower, na=False) |
            self.df_medicines.get("generic_name", pd.Series([])).str.lower().str.contains(q_lower, na=False) |
            self.df_medicines.get("brand_names", pd.Series([])).str.lower().str.contains(q_lower, na=False) |
            self.df_medicines.get("primary_indication", pd.Series([])).str.lower().str.contains(q_lower, na=False)
        )

        results = self.df_medicines[mask].head(limit)
        return results.to_dict(orient="records")

medicine_search_engine = MedicineSearchEngine()
