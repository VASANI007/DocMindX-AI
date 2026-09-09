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

-- ============================================================
-- AUTHENTICATION, FAMILY PROFILES, MEDICAL HISTORY & AUDIT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    dob TEXT DEFAULT '',
    email_verified INTEGER DEFAULT 0,
    account_status TEXT DEFAULT 'PENDING',
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_password_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    age INTEGER,
    dob TEXT,
    gender TEXT,
    blood_group TEXT,
    height TEXT,
    weight TEXT,
    notes TEXT,
    emergency_contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medical_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_member_id INTEGER NOT NULL,
    condition_name TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    diagnosed_at TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_member_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    start_date TEXT,
    end_date TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medical_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    family_member_id INTEGER,
    scan_type TEXT NOT NULL,
    scan_mode TEXT NOT NULL,
    result_reference TEXT,
    summary TEXT,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS otp_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL COLLATE NOCASE,
    purpose TEXT NOT NULL,
    otp_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email TEXT,
    event_type TEXT NOT NULL,
    ip_address TEXT DEFAULT '127.0.0.1',
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high performance and integrity
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_family_user_id ON family_members(user_id);
CREATE INDEX IF NOT EXISTS idx_conditions_fam_id ON medical_conditions(family_member_id);
CREATE INDEX IF NOT EXISTS idx_meds_fam_id ON medications(family_member_id);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON medical_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_fam_id ON medical_scans(family_member_id);
CREATE INDEX IF NOT EXISTS idx_otp_email_purpose ON otp_verifications(email, purpose);
CREATE INDEX IF NOT EXISTS idx_audit_event ON security_audit_logs(event_type, created_at);

