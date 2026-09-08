"""
    Database initialization and management utilities for DocMindX AI
"""
import sqlite3
import os

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "DocMindX.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        conn.commit()
    conn.close()
    print(f"[OK] Database initialized successfully at {DB_PATH}")

def cache_medicine(medicine_name, generic_name="", active_ingredients="", manufacturer="", purpose="", warnings="", dosage="", interactions="", source="OpenFDA"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO medicine_cache 
            (medicine_name, generic_name, active_ingredients, manufacturer, purpose, warnings, dosage_instructions, drug_interactions, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (medicine_name.lower().strip(), generic_name, active_ingredients, manufacturer, purpose, warnings, dosage, interactions, source))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching medicine: {e}")

def get_cached_medicine(medicine_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medicine_cache WHERE LOWER(medicine_name) = ? OR LOWER(generic_name) = ?", 
                       (medicine_name.lower().strip(), medicine_name.lower().strip()))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "medicine_name": row[1],
                "generic_name": row[2],
                "active_ingredients": row[3],
                "manufacturer": row[4],
                "purpose": row[5],
                "warnings": row[6],
                "dosage_instructions": row[7],
                "drug_interactions": row[8],
                "source": row[9],
                "last_updated": row[10]
            }
    except Exception as e:
        print(f"Error reading cached medicine: {e}")
    return None

if __name__ == "__main__":
    init_db()
