"""
DocMindX AI — Supabase PostgreSQL Table & Medicine Cache Utilities
"""
import os
from config.database import get_db_connection as config_get_db_connection

DB_DIR = os.path.dirname(__file__)
SCHEMA_PG_PATH = os.path.join(DB_DIR, "schema_postgres.sql")

def get_connection():
    """Returns an active Supabase PostgreSQL database connection."""
    return config_get_db_connection()

def init_db():
    """Initializes PostgreSQL schema in Supabase."""
    conn = get_connection()
    cursor = conn.cursor()
    if os.path.exists(SCHEMA_PG_PATH):
        with open(SCHEMA_PG_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        conn.commit()
    conn.close()
    print("[OK] Supabase PostgreSQL database initialized successfully.")

def cache_medicine(medicine_name, generic_name="", active_ingredients="", manufacturer="", purpose="", warnings="", dosage="", interactions="", source="OpenFDA"):
    """Caches pharmacology formulary data into Supabase medicine_cache."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        med_name_clean = medicine_name.lower().strip()
        cursor.execute("""
            INSERT INTO medicine_cache 
            (medicine_name, generic_name, active_ingredients, manufacturer, purpose, warnings, dosage_instructions, drug_interactions, source, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (medicine_name) DO UPDATE SET
                generic_name = EXCLUDED.generic_name,
                active_ingredients = EXCLUDED.active_ingredients,
                manufacturer = EXCLUDED.manufacturer,
                purpose = EXCLUDED.purpose,
                warnings = EXCLUDED.warnings,
                dosage_instructions = EXCLUDED.dosage_instructions,
                drug_interactions = EXCLUDED.drug_interactions,
                source = EXCLUDED.source,
                last_updated = CURRENT_TIMESTAMP
        """, (med_name_clean, generic_name, active_ingredients, manufacturer, purpose, warnings, dosage, interactions, source))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching medicine: {e}")

def get_cached_medicine(medicine_name):
    """Retrieves cached drug information from Supabase PostgreSQL."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        name_clean = medicine_name.lower().strip()
        cursor.execute("SELECT * FROM medicine_cache WHERE LOWER(medicine_name) = %s OR LOWER(generic_name) = %s", 
                       (name_clean, name_clean))
        row = cursor.fetchone()
        conn.close()
        if row:
            if isinstance(row, dict) or hasattr(row, 'keys'):
                return {
                    "id": row["id"],
                    "medicine_name": row["medicine_name"],
                    "generic_name": row["generic_name"],
                    "active_ingredients": row["active_ingredients"],
                    "manufacturer": row["manufacturer"],
                    "purpose": row["purpose"],
                    "warnings": row["warnings"],
                    "dosage_instructions": row["dosage_instructions"],
                    "drug_interactions": row["drug_interactions"],
                    "source": row["source"],
                    "last_updated": row["last_updated"]
                }
            else:
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
