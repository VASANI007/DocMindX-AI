"""
    DocMindX AI - Database Data Insertion and Session Logging Helper
"""
import os
import sqlite3
import json
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "DocMindX.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_triage_session(session_data: dict) -> int:
    """Inserts a completed triage session into triage_history table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO triage_history (
        session_id, age_group, gender, state, district, duration,
        symptoms_list, existing_conditions, current_medicines,
        urgency_level, possible_conditions_json, red_flag_alert
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    symptoms_str = json.dumps(session_data.get("symptoms", []))
    conditions_json = json.dumps(session_data.get("ranked_conditions", []))
    
    cursor.execute(query, (
        session_data.get("session_id", str(datetime.datetime.now().timestamp())),
        session_data.get("age", "Adult"),
        session_data.get("gender", "Unspecified"),
        session_data.get("state", "India"),
        session_data.get("district", "Unknown"),
        session_data.get("duration", "Few Days"),
        symptoms_str,
        session_data.get("existing_conditions", "None"),
        session_data.get("current_medicines", "None"),
        session_data.get("urgency_level", "NORMAL"),
        conditions_json,
        1 if session_data.get("is_emergency") else 0
    ))
    
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def log_report_analysis(report_name: str, report_type: str, extracted_text: str, summary: str, findings: list, abnormal_count: int = 0) -> int:
    """Inserts a blood/lab report OCR analysis log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO report_analysis_history (
        report_name, report_type, extracted_text, summary, abnormal_count, details_json
    ) VALUES (?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (
        report_name,
        report_type,
        extracted_text[:3000] if extracted_text else "",
        summary,
        int(abnormal_count),
        json.dumps(findings)
    ))
    
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_recent_triage_history(limit: int = 20) -> list:
    """Fetches recent triage assessments from DocMindX.db."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM triage_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching triage history: {e}")
        return []

def get_recent_report_history(limit: int = 20) -> list:
    """Fetches recent report analyses from DocMindX.db."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM report_analysis_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching report history: {e}")
        return []

def seed_sample_records_if_empty():
    """Seeds starter sample records into DocMindX.db if empty."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM report_analysis_history")
        count_reports = cursor.fetchone()[0]
        
        if count_reports == 0:
            cursor.execute("""
            INSERT INTO report_analysis_history (report_name, report_type, extracted_text, summary, abnormal_count, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Complete Blood Count (CBC)",
                "Pathology Lab Report",
                "Hemoglobin: 13.8 g/dL, WBC: 7400, Platelets: 2.1 Lakh, Fasting Blood Sugar: 96 mg/dL",
                "All primary CBC parameters are within normal biological reference intervals.",
                0,
                json.dumps([{"test": "Hemoglobin", "value": "13.8 g/dL", "status": "Normal"}, {"test": "WBC", "value": "7400 cells/mcL", "status": "Normal"}])
            ))
            cursor.execute("""
            INSERT INTO report_analysis_history (report_name, report_type, extracted_text, summary, abnormal_count, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Lipid Profile Panel",
                "Biochemistry Report",
                "Total Cholesterol: 214 mg/dL, HDL: 46 mg/dL, LDL: 138 mg/dL, Triglycerides: 160 mg/dL",
                "Mild borderline elevation in LDL and Total Cholesterol. Dietary lifestyle modification advised.",
                1,
                json.dumps([{"test": "Total Cholesterol", "value": "214 mg/dL", "status": "Borderline High"}, {"test": "LDL", "value": "138 mg/dL", "status": "Borderline"}])
            ))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Notice during seeding: {e}")
