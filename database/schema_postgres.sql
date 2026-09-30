-- ============================================================
-- DOCMINDX AI — PRODUCTION SUPABASE POSTGRESQL SCHEMA
-- Fully relational, secure, indexed, and clinical/supply-chain separated
-- ============================================================

-- 1. MEDICINE CACHE (OpenFDA & DailyMed Drug Knowledge)
CREATE TABLE IF NOT EXISTS medicine_cache (
    id SERIAL PRIMARY KEY,
    medicine_name TEXT UNIQUE NOT NULL,
    generic_name TEXT,
    active_ingredients TEXT,
    manufacturer TEXT,
    purpose TEXT,
    warnings TEXT,
    dosage_instructions TEXT,
    drug_interactions TEXT,
    source TEXT DEFAULT 'OpenFDA/DailyMed',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. TRIAGE HISTORY
CREATE TABLE IF NOT EXISTS triage_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
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

-- 3. REPORT ANALYSIS HISTORY (Lab & Blood OCR Analytics)
CREATE TABLE IF NOT EXISTS report_analysis_history (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    report_name TEXT,
    report_type TEXT,
    extracted_text TEXT,
    summary TEXT,
    abnormal_count INTEGER DEFAULT 0,
    details_json TEXT
);

-- 4. USERS (Authentication & Role Base Access)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    dob TEXT DEFAULT '',
    state TEXT DEFAULT '',
    email_verified INTEGER DEFAULT 0,
    account_status TEXT DEFAULT 'PENDING',
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. FAMILY MEMBERS (Strict User Data Isolation)
CREATE TABLE IF NOT EXISTS family_members (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    age INTEGER,
    dob TEXT,
    gender TEXT,
    blood_group TEXT,
    height TEXT,
    weight TEXT,
    state TEXT DEFAULT '',
    notes TEXT,
    emergency_contact TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. MEDICAL CONDITIONS
CREATE TABLE IF NOT EXISTS medical_conditions (
    id SERIAL PRIMARY KEY,
    family_member_id INTEGER NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    condition_name TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    diagnosed_at TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. MEDICATIONS
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    family_member_id INTEGER NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    start_date TEXT,
    end_date TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. MEDICAL SCANS
CREATE TABLE IF NOT EXISTS medical_scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL,
    scan_type TEXT NOT NULL,
    scan_mode TEXT NOT NULL,
    result_reference TEXT,
    summary TEXT,
    details_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. OTP VERIFICATIONS
CREATE TABLE IF NOT EXISTS otp_verifications (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    purpose TEXT NOT NULL,
    otp_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attempts INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. SECURITY AUDIT LOGS
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    email TEXT,
    event_type TEXT NOT NULL,
    ip_address TEXT DEFAULT '127.0.0.1',
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- NATIONAL COMMAND CENTER / HEALTH SUPPLY CHAIN TABLES
-- ============================================================

-- 11. COMMAND CENTER SOURCES
CREATE TABLE IF NOT EXISTS command_center_sources (
    id SERIAL PRIMARY KEY,
    source_code TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT,
    api_endpoint TEXT,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    records_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',
    provenance TEXT,
    source_date TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. COMMAND CENTER FACILITIES
CREATE TABLE IF NOT EXISTS command_center_facilities (
    id SERIAL PRIMARY KEY,
    facility_id TEXT UNIQUE NOT NULL,
    facility_name TEXT NOT NULL,
    facility_type TEXT,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    pincode TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    total_beds INTEGER DEFAULT 0,
    icu_beds INTEGER DEFAULT 0,
    oxygen_cylinders INTEGER DEFAULT 0,
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. COMMAND CENTER INVENTORY
CREATE TABLE IF NOT EXISTS command_center_inventory (
    id SERIAL PRIMARY KEY,
    facility_id TEXT REFERENCES command_center_facilities(facility_id) ON DELETE CASCADE,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT,
    stock_on_hand INTEGER DEFAULT 0,
    days_of_supply DOUBLE PRECISION,
    consumption_rate DOUBLE PRECISION,
    stockout_risk_score DOUBLE PRECISION,
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. COMMAND CENTER DEMAND FORECASTS
CREATE TABLE IF NOT EXISTS command_center_demand (
    id SERIAL PRIMARY KEY,
    facility_id TEXT,
    state TEXT,
    district TEXT,
    disease_code TEXT,
    forecast_date DATE,
    predicted_cases INTEGER,
    model_version TEXT,
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. COMMAND CENTER ALERTS
CREATE TABLE IF NOT EXISTS command_center_alerts (
    id SERIAL PRIMARY KEY,
    alert_id TEXT UNIQUE,
    facility_id TEXT,
    state TEXT,
    district TEXT,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    action_recommended TEXT,
    status TEXT DEFAULT 'OPEN',
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 16. COMMAND CENTER PREDICTIONS
CREATE TABLE IF NOT EXISTS command_center_predictions (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    target_variable TEXT,
    prediction_payload JSONB,
    confidence_score DOUBLE PRECISION,
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. COMMAND CENTER TRANSFERS
CREATE TABLE IF NOT EXISTS command_center_transfers (
    id SERIAL PRIMARY KEY,
    transfer_id TEXT UNIQUE NOT NULL,
    from_facility_id TEXT,
    to_facility_id TEXT,
    item_code TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT DEFAULT 'PENDING',
    eta_hours DOUBLE PRECISION,
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 18. COMMAND CENTER MODEL RUNS
CREATE TABLE IF NOT EXISTS command_center_model_runs (
    id SERIAL PRIMARY KEY,
    run_id TEXT UNIQUE NOT NULL,
    model_name TEXT NOT NULL,
    train_loss DOUBLE PRECISION,
    val_metric DOUBLE PRECISION,
    duration_seconds DOUBLE PRECISION,
    status TEXT DEFAULT 'COMPLETED',
    source TEXT,
    source_date TEXT,
    provenance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES FOR MAXIMUM QUERY EFFICIENCY AND CONSTRAINTS
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_pg_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_pg_family_user_id ON family_members(user_id);
CREATE INDEX IF NOT EXISTS idx_pg_conditions_fam_id ON medical_conditions(family_member_id);
CREATE INDEX IF NOT EXISTS idx_pg_meds_fam_id ON medications(family_member_id);
CREATE INDEX IF NOT EXISTS idx_pg_scans_user_id ON medical_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_pg_scans_fam_id ON medical_scans(family_member_id);
CREATE INDEX IF NOT EXISTS idx_pg_otp_email_purpose ON otp_verifications(email, purpose);
CREATE INDEX IF NOT EXISTS idx_pg_audit_event ON security_audit_logs(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_pg_cc_facilities_state ON command_center_facilities(state, district);
CREATE INDEX IF NOT EXISTS idx_pg_cc_inventory_fac ON command_center_inventory(facility_id);
CREATE INDEX IF NOT EXISTS idx_pg_cc_alerts_status ON command_center_alerts(status, severity);
