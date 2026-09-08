-- DocMindX AI Database Schema

CREATE TABLE IF NOT EXISTS medicine_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT UNIQUE NOT NULL,
    generic_name TEXT,
    active_ingredients TEXT,
    manufacturer TEXT,
    purpose TEXT,
    warnings TEXT,
    dosage_instructions TEXT,
    drug_interactions TEXT,
    source TEXT DEFAULT 'OpenFDA/DailyMed',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS triage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    age_group TEXT,
    gender TEXT,
    state TEXT,
    district TEXT,
    duration TEXT,
    symptoms_list TEXT,
    existing_conditions TEXT,
    current_medicines TEXT,
    urgency_level TEXT,
    possible_conditions_json TEXT,
    red_flag_alert INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS report_analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_name TEXT,
    report_type TEXT,
    extracted_text TEXT,
    summary TEXT,
    abnormal_count INTEGER DEFAULT 0,
    details_json TEXT
);
