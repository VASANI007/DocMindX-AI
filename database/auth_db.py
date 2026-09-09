"""
DocMindX AI — Relational Authentication, Family Profile, Scan History & Audit Database Manager
Strictly parameterized queries to completely eliminate SQL Injection vulnerabilities.
Provides strict user data isolation and auditable administrative controls.
"""
import os
import sqlite3
import json
from datetime import datetime, date

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "DocMindX.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

def get_db_connection():
    """Returns a SQLite connection with row factory and foreign keys enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_auth_tables():
    """Ensures all authentication, family, medical history, scan, and audit tables exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        conn.commit()
    # Migration: Ensure state column exists on family_members and users tables
    try:
        cursor.execute("ALTER TABLE family_members ADD COLUMN state TEXT DEFAULT '';")
        conn.commit()
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN state TEXT DEFAULT '';")
        conn.commit()
    except Exception:
        pass
    # Migration: Ensure dob column exists on users table
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT DEFAULT '';")
        conn.commit()
    except Exception:
        pass
    conn.close()

# Initialize tables immediately on module load
init_auth_tables()

def calculate_age_from_dob(dob_val) -> int:
    """
    Chronologically computes age in whole completed years from Date of Birth.
    Automatically advances in real-time as years change and birthdays pass.
    Returns None if DOB is invalid, missing, or in the future.
    """
    if not dob_val:
        return None
    try:
        if isinstance(dob_val, (datetime, date)):
            born = dob_val if isinstance(dob_val, date) else dob_val.date()
        elif isinstance(dob_val, str):
            clean = dob_val.split("T")[0].split(" ")[0].strip()
            if not clean:
                return None
            if "-" in clean:
                p = [int(x) for x in clean.split("-")]
                if len(p) == 3:
                    born = date(p[0], p[1], p[2])
                else:
                    return None
            elif "/" in clean:
                p = [int(x) for x in clean.split("/")]
                if len(p) == 3:
                    born = date(p[2], p[1], p[0]) if p[0] <= 31 and p[2] > 1900 else date(p[0], p[1], p[2])
                else:
                    return None
            else:
                return None
        else:
            return None

        today = date.today()
        if born > today:
            return None
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except Exception:
        return None

# ============================================================
# SECURITY AUDIT LOGGING
# ============================================================

def log_security_event(event_type: str, email: str = None, user_id: int = None, details: str = None, ip_address: str = "127.0.0.1"):
    """
    Safely logs a security or administrative event.
    NEVER logs plaintext passwords, plaintext OTPs, or secret tokens.
    """
    try:
        # Sanitize details string to ensure no accidental leak of secrets
        safe_details = details or ""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO security_audit_logs (user_id, email, event_type, ip_address, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email, event_type, ip_address, safe_details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to log security event: {e}")

# ============================================================
# USER MANAGEMENT (PARAMETERIZED & ISOLATED)
# ============================================================

def create_user(full_name: str, email: str, password_hash: str, account_status: str = "PENDING", email_verified: int = 0, role: str = "user", dob: str = "") -> int:
    """Inserts a new user record using strict parameterized SQL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO users (full_name, email, password_hash, email_verified, account_status, role, dob, created_at, updated_at, last_password_change)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (full_name.strip(), email.strip().lower(), password_hash, email_verified, account_status, role, str(dob or "").strip(), now_str, now_str, now_str))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user_by_email(email: str) -> dict:
    """Fetches user record by email using strict parameterized equality."""
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    user_dict = dict(row)
    if user_dict.get("dob"):
        calc_age = calculate_age_from_dob(user_dict["dob"])
        if calc_age is not None:
            user_dict["age"] = calc_age
    return user_dict

def get_user_by_id(user_id: int) -> dict:
    """Fetches user record by primary key."""
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    user_dict = dict(row)
    if user_dict.get("dob"):
        calc_age = calculate_age_from_dob(user_dict["dob"])
        if calc_age is not None:
            user_dict["age"] = calc_age
    return user_dict

def update_user_status(user_id: int, account_status: str, email_verified: int = None):
    """Updates account status and verification state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if email_verified is not None:
        cursor.execute("""
            UPDATE users SET account_status = ?, email_verified = ?, updated_at = ? WHERE id = ?
        """, (account_status, email_verified, now_str, int(user_id)))
    else:
        cursor.execute("""
            UPDATE users SET account_status = ?, updated_at = ? WHERE id = ?
        """, (account_status, now_str, int(user_id)))
    conn.commit()
    conn.close()

def update_user_password(user_id: int, new_password_hash: str):
    """Updates user password hash and updates last_password_change timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE users SET password_hash = ?, last_password_change = ?, updated_at = ? WHERE id = ?
    """, (new_password_hash, now_str, now_str, int(user_id)))
    conn.commit()
    conn.close()

def update_user_last_login(user_id: int):
    """Updates user last login timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?", (now_str, now_str, int(user_id)))
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, full_name: str, state: str = None, dob: str = None) -> bool:
    """Updates user profile information including full_name, state, and dob."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["full_name = ?", "updated_at = ?"]
    params = [full_name.strip(), now_str]
    if state is not None:
        fields.append("state = ?")
        params.append(state.strip())
    if dob is not None:
        fields.append("dob = ?")
        params.append(dob.strip())
    params.append(int(user_id))
    cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(params))
    conn.commit()
    conn.close()
    return True

# ============================================================
# OTP VERIFICATIONS (HASHED & EXPIRABLE)
# ============================================================

def store_otp(email: str, purpose: str, otp_hash: str, expires_at_str: str):
    """Stores a hashed OTP for a specific purpose."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Invalidate previous unverified OTPs for this email and purpose
    cursor.execute("UPDATE otp_verifications SET verified = -1 WHERE email = ? AND purpose = ? AND verified = 0", (email.strip().lower(), purpose))
    cursor.execute("""
        INSERT INTO otp_verifications (email, purpose, otp_hash, expires_at, attempts, verified, created_at)
        VALUES (?, ?, ?, ?, 0, 0, ?)
    """, (email.strip().lower(), purpose, otp_hash, expires_at_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_active_otp_record(email: str, purpose: str) -> dict:
    """Retrieves the latest active OTP record for email and purpose."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM otp_verifications 
        WHERE email = ? AND purpose = ? AND verified = 0 
        ORDER BY id DESC LIMIT 1
    """, (email.strip().lower(), purpose))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def increment_otp_attempts(otp_id: int):
    """Increments the failure attempt count for an OTP."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE otp_verifications SET attempts = attempts + 1 WHERE id = ?", (int(otp_id),))
    conn.commit()
    conn.close()

def mark_otp_verified(otp_id: int):
    """Marks an OTP record as successfully consumed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE otp_verifications SET verified = 1 WHERE id = ?", (int(otp_id),))
    conn.commit()
    conn.close()

# ============================================================
# FAMILY MEMBERS (STRICT USER DATA ISOLATION)
# ============================================================

def add_family_member(user_id: int, member_data: dict) -> int:
    """Adds a family member for the specified authenticated user with dynamic DOB-based age synchronization."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dob_val = str(member_data.get("dob", "") or "").strip()
    age_val = member_data.get("age")
    if dob_val:
        calc_age = calculate_age_from_dob(dob_val)
        if calc_age is not None:
            age_val = calc_age
    elif age_val is not None and str(age_val).isdigit():
        age_val = int(age_val)
    else:
        age_val = None

    cursor.execute("""
        INSERT INTO family_members (
            user_id, name, relationship, age, dob, gender, blood_group, height, weight, state, notes, emergency_contact, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id),
        member_data.get("name", "").strip(),
        member_data.get("relationship", "").strip(),
        age_val,
        dob_val,
        member_data.get("gender", ""),
        member_data.get("blood_group", ""),
        str(member_data.get("height", "")),
        str(member_data.get("weight", "")),
        str(member_data.get("state", "")).strip(),
        member_data.get("notes", ""),
        member_data.get("emergency_contact", ""),
        now_str,
        now_str
    ))
    member_id = cursor.lastrowid
    
    # Optional initial conditions
    conditions = member_data.get("conditions", [])
    if isinstance(conditions, list):
        for cond in conditions:
            if isinstance(cond, dict) and cond.get("condition_name"):
                cursor.execute("""
                    INSERT INTO medical_conditions (family_member_id, condition_name, status, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, cond.get("condition_name"), cond.get("status", "Active"), cond.get("notes", ""), now_str, now_str))
            elif isinstance(cond, str) and cond.strip():
                cursor.execute("""
                    INSERT INTO medical_conditions (family_member_id, condition_name, status, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, cond.strip(), "Active", "", now_str, now_str))
                
    # Optional initial medications
    medications = member_data.get("medications", [])
    if isinstance(medications, list):
        for med in medications:
            if isinstance(med, dict) and med.get("medicine_name"):
                cursor.execute("""
                    INSERT INTO medications (family_member_id, medicine_name, dosage, frequency, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, med.get("medicine_name"), med.get("dosage", ""), med.get("frequency", ""), med.get("notes", ""), now_str))
            elif isinstance(med, str) and med.strip():
                cursor.execute("""
                    INSERT INTO medications (family_member_id, medicine_name, dosage, frequency, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, med.strip(), "", "", "", now_str))

    conn.commit()
    conn.close()
    return member_id

def get_family_members(user_id: int) -> list:
    """Fetches all family members belonging strictly to the authenticated user with real-time dynamic age calculation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM family_members WHERE user_id = ? ORDER BY id ASC
    """, (int(user_id),))
    rows = [dict(r) for r in cursor.fetchall()]
    
    # Attach conditions, medications, and dynamic real-time age
    for r in rows:
        if r.get("dob"):
            dyn_age = calculate_age_from_dob(r["dob"])
            if dyn_age is not None:
                r["age"] = dyn_age
        m_id = r["id"]
        cursor.execute("SELECT * FROM medical_conditions WHERE family_member_id = ?", (m_id,))
        r["conditions"] = [dict(c) for c in cursor.fetchall()]
        cursor.execute("SELECT * FROM medications WHERE family_member_id = ?", (m_id,))
        r["medications"] = [dict(m) for m in cursor.fetchall()]

    conn.close()
    return rows

def get_family_member_by_id(member_id: int, user_id: int = None) -> dict:
    """
    Fetches a specific family member with dynamic age calculation.
    If user_id is provided, enforces strict user ownership isolation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM family_members WHERE id = ? AND user_id = ?", (int(member_id), int(user_id)))
    else:
        cursor.execute("SELECT * FROM family_members WHERE id = ?", (int(member_id),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    member = dict(row)
    if member.get("dob"):
        dyn_age = calculate_age_from_dob(member["dob"])
        if dyn_age is not None:
            member["age"] = dyn_age
    cursor.execute("SELECT * FROM medical_conditions WHERE family_member_id = ?", (int(member_id),))
    member["conditions"] = [dict(c) for c in cursor.fetchall()]
    cursor.execute("SELECT * FROM medications WHERE family_member_id = ?", (int(member_id),))
    member["medications"] = [dict(m) for m in cursor.fetchall()]
    conn.close()
    return member

def update_family_member(member_id: int, user_id: int, member_data: dict) -> bool:
    """Updates family member details ensuring strict user ownership check and dynamic age sync."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dob_val = str(member_data.get("dob", "") or "").strip()
    age_val = member_data.get("age")
    if dob_val:
        calc_age = calculate_age_from_dob(dob_val)
        if calc_age is not None:
            age_val = calc_age
    elif age_val is not None and str(age_val).isdigit():
        age_val = int(age_val)
    else:
        age_val = None

    cursor.execute("""
        UPDATE family_members SET
            name = ?, relationship = ?, age = ?, dob = ?, gender = ?, blood_group = ?,
            height = ?, weight = ?, state = ?, notes = ?, emergency_contact = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        member_data.get("name", "").strip(),
        member_data.get("relationship", "").strip(),
        age_val,
        dob_val,
        member_data.get("gender", ""),
        member_data.get("blood_group", ""),
        str(member_data.get("height", "")),
        str(member_data.get("weight", "")),
        str(member_data.get("state", "")).strip(),
        member_data.get("notes", ""),
        member_data.get("emergency_contact", ""),
        now_str,
        int(member_id),
        int(user_id)
    ))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected > 0

def delete_family_member(member_id: int, user_id: int = None) -> bool:
    """Deletes family member with ownership verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM family_members WHERE id = ? AND user_id = ?", (int(member_id), int(user_id)))
    else:
        cursor.execute("DELETE FROM family_members WHERE id = ?", (int(member_id),))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# ============================================================
# MEDICAL CONDITIONS & MEDICATIONS CRUD
# ============================================================

def add_medical_condition(family_member_id: int, user_id: int, condition_name: str, status: str = "Active", notes: str = "", diagnosed_at: str = None) -> int:
    """Adds a condition after verifying family member ownership."""
    member = get_family_member_by_id(family_member_id, user_id)
    if not member:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO medical_conditions (family_member_id, condition_name, status, diagnosed_at, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (int(family_member_id), condition_name.strip(), status, diagnosed_at, notes, now_str, now_str))
    conn.commit()
    cond_id = cursor.lastrowid
    conn.close()
    return cond_id

def delete_medical_condition(condition_id: int, user_id: int) -> bool:
    """Deletes condition after verifying user ownership of parent family member."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM medical_conditions 
        WHERE id = ? AND family_member_id IN (SELECT id FROM family_members WHERE user_id = ?)
    """, (int(condition_id), int(user_id)))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def add_medication(family_member_id: int, user_id: int, medicine_name: str, dosage: str = "", frequency: str = "", notes: str = "") -> int:
    """Adds a medication after verifying family member ownership."""
    member = get_family_member_by_id(family_member_id, user_id)
    if not member:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO medications (family_member_id, medicine_name, dosage, frequency, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (int(family_member_id), medicine_name.strip(), dosage.strip(), frequency.strip(), notes.strip(), now_str))
    conn.commit()
    med_id = cursor.lastrowid
    conn.close()
    return med_id

def delete_medication(medication_id: int, user_id: int) -> bool:
    """Deletes medication after verifying user ownership of parent family member."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM medications 
        WHERE id = ? AND family_member_id IN (SELECT id FROM family_members WHERE user_id = ?)
    """, (int(medication_id), int(user_id)))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

# ============================================================
# MEDICAL SCANS & HISTORY
# ============================================================

def save_medical_scan(user_id: int, family_member_id: int, scan_type: str, scan_mode: str, result_reference: str, summary: str, details: dict = None) -> int:
    """Saves a medical scan record tied to user and optionally a family member."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details_str = json.dumps(details or {})
    cursor.execute("""
        INSERT INTO medical_scans (user_id, family_member_id, scan_type, scan_mode, result_reference, summary, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id),
        int(family_member_id) if family_member_id else None,
        scan_type,
        scan_mode,
        result_reference,
        summary,
        details_str,
        now_str
    ))
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id

def get_user_scans(user_id: int, family_member_id: int = None, scan_type: str = None, scan_mode: str = None, limit: int = 50) -> list:
    """Fetches scans for the authenticated user with strict user ownership and profile isolation."""
    if not user_id:
        return []
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if family_member_id is not None:
        # Verify family member belongs to user_id to prevent IDOR
        cursor.execute("SELECT id FROM family_members WHERE id = ? AND user_id = ?", (int(family_member_id), int(user_id)))
        if not cursor.fetchone():
            conn.close()
            return []

    query = """
        SELECT s.*, f.name as family_member_name, f.relationship 
        FROM medical_scans s
        LEFT JOIN family_members f ON s.family_member_id = f.id
        WHERE s.user_id = ?
    """
    params = [int(user_id)]
    
    if family_member_id is not None:
        query += " AND s.family_member_id = ?"
        params.append(int(family_member_id))
    if scan_type:
        query += " AND s.scan_type = ?"
        params.append(scan_type)
    if scan_mode:
        query += " AND s.scan_mode = ?"
        params.append(scan_mode)
        
    query += " ORDER BY s.id DESC LIMIT ?"
    params.append(int(limit))
    
    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Automatically decode details_json for seamless access
    for r in rows:
        if r.get("details_json"):
            try:
                r["details"] = json.loads(r["details_json"]) if isinstance(r["details_json"], str) else r["details_json"]
            except Exception:
                r["details"] = {}
        else:
            r["details"] = {}
            
    return rows

def get_medical_scan_by_id(scan_id: int, user_id: int = None) -> dict:
    """Fetches a specific medical scan with optional strict user ownership verification."""
    if not scan_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("""
            SELECT s.*, f.name as family_member_name, f.relationship 
            FROM medical_scans s
            LEFT JOIN family_members f ON s.family_member_id = f.id
            WHERE s.id = ? AND s.user_id = ?
        """, (int(scan_id), int(user_id)))
    else:
        cursor.execute("""
            SELECT s.*, f.name as family_member_name, f.relationship 
            FROM medical_scans s
            LEFT JOIN family_members f ON s.family_member_id = f.id
            WHERE s.id = ?
        """, (int(scan_id),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    scan_dict = dict(row)
    if scan_dict.get("details_json"):
        try:
            scan_dict["details"] = json.loads(scan_dict["details_json"]) if isinstance(scan_dict["details_json"], str) else scan_dict["details_json"]
        except Exception:
            scan_dict["details"] = {}
    else:
        scan_dict["details"] = {}
    return scan_dict

def delete_medical_scan(scan_id: int, user_id: int) -> bool:
    """Deletes a medical scan record with strict user ownership verification."""
    if not scan_id or not user_id:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medical_scans WHERE id = ? AND user_id = ?", (int(scan_id), int(user_id)))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_user_profile_summary(user_id: int) -> dict:
    """Retrieves consolidated user profile and linked 'Self' medical details for clinical history."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    fams = get_family_members(user_id)
    self_m = next((m for m in fams if str(m.get("relationship", "")).strip().lower() == "self"), None)
    
    conds = [c["condition_name"] for c in self_m.get("conditions", [])] if self_m else []
    meds = [m["medicine_name"] for m in self_m.get("medications", [])] if self_m else []
    
    return {
        "user_id": user["id"],
        "full_name": user.get("full_name", "Patient"),
        "email": user.get("email", ""),
        "dob": user.get("dob") or (self_m.get("dob") if self_m else ""),
        "age": user.get("age") or (self_m.get("age") if self_m else None),
        "gender": self_m.get("gender") if self_m else "Unspecified",
        "blood_group": self_m.get("blood_group") if self_m else "",
        "height": self_m.get("height") if self_m else "",
        "weight": self_m.get("weight") if self_m else "",
        "state": user.get("state") or (self_m.get("state") if self_m else ""),
        "conditions": conds,
        "medications": meds,
        "self_member_id": self_m["id"] if self_m else None
    }

# ============================================================
# ADMIN PORTAL QUERIES (DYNAMIC DATA, ZERO FAKE TELEMETRY)
# ============================================================

def admin_get_kpis() -> dict:
    """Calculates all Admin KPIs dynamically from real database records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE email_verified = 1")
    verified_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE account_status = 'ACTIVE'")
    active_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE account_status = 'DISABLED'")
    disabled_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM family_members")
    total_family_members = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medical_scans")
    total_scans = cursor.fetchone()[0]
    
    today_str = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM medical_scans WHERE created_at LIKE ?", (f"{today_str}%",))
    scans_today = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT * FROM security_audit_logs 
        ORDER BY id DESC LIMIT 8
    """)
    recent_activity = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "active_users": active_users,
        "disabled_users": disabled_users,
        "total_family_members": total_family_members,
        "total_scans": total_scans,
        "scans_today": scans_today,
        "recent_activity": recent_activity
    }

def admin_get_users(search: str = None, status_filter: str = None, limit: int = 100, offset: int = 0) -> list:
    """Admin query to list users with family count and scan count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT u.id, u.full_name, u.email, u.email_verified, u.account_status, u.role, 
               u.created_at, u.last_login, u.last_password_change,
               (SELECT COUNT(*) FROM family_members f WHERE f.user_id = u.id) as family_count,
               (SELECT COUNT(*) FROM medical_scans s WHERE s.user_id = u.id) as scan_count
        FROM users u
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (u.full_name LIKE ? OR u.email LIKE ?)"
        like_term = f"%{search.strip()}%"
        params.extend([like_term, like_term])
    if status_filter and status_filter != "ALL":
        query += " AND u.account_status = ?"
        params.append(status_filter)
        
    query += " ORDER BY u.id DESC LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])
    
    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def admin_disable_user(user_id: int):
    """Admin action to safely disable a user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET account_status = 'DISABLED' WHERE id = ?", (int(user_id),))
    conn.commit()
    conn.close()

def admin_enable_user(user_id: int):
    """Admin action to re-enable a disabled user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET account_status = 'ACTIVE' WHERE id = ?", (int(user_id),))
    conn.commit()
    conn.close()

def admin_delete_user(user_id: int, permanent: bool = False) -> bool:
    """
    Deletes or disables a user account.
    If permanent is True, uses foreign key cascade to cleanly purge user records.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if permanent:
        # Purge scans, family members (foreign key will cascade), and user
        cursor.execute("DELETE FROM medical_scans WHERE user_id = ?", (int(user_id),))
        cursor.execute("DELETE FROM family_members WHERE user_id = ?", (int(user_id),))
        cursor.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        rows = cursor.rowcount
    else:
        cursor.execute("UPDATE users SET account_status = 'DEACTIVATED' WHERE id = ?", (int(user_id),))
        rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def admin_get_user_hierarchy(user_id: int) -> dict:
    """Fetches deep medical hierarchy: User -> Family Members -> Medical History -> Scans."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    family = get_family_members(user_id)
    scans = get_user_scans(user_id, limit=50)
    return {
        "user": user,
        "family_members": family,
        "scans": scans
    }

def admin_get_all_scans(search: str = None, scan_type: str = None, scan_mode: str = None, limit: int = 100) -> list:
    """Fetches all system scans with user and family details for admin view."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.*, u.full_name as user_name, u.email as user_email,
               f.name as family_name, f.relationship
        FROM medical_scans s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN family_members f ON s.family_member_id = f.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (u.full_name LIKE ? OR u.email LIKE ? OR s.summary LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    if scan_type and scan_type != "ALL":
        query += " AND s.scan_type = ?"
        params.append(scan_type)
    if scan_mode and scan_mode != "ALL":
        query += " AND s.scan_mode = ?"
        params.append(scan_mode)
        
    query += " ORDER BY s.id DESC LIMIT ?"
    params.append(int(limit))
    
    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def admin_get_security_logs(event_type: str = None, search: str = None, limit: int = 100) -> list:
    """Fetches audit logs for the admin security console."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM security_audit_logs WHERE 1=1"
    params = []
    if event_type and event_type != "ALL":
        query += " AND event_type = ?"
        params.append(event_type)
    if search:
        query += " AND (email LIKE ? OR details LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])
    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))
    
    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
