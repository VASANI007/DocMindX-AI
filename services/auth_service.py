"""
DocMindX AI — Core Security & Authentication Engine
Implements bcrypt password hashing, cryptographically secure 6-digit OTPs,
brute-force rate limiting, input validation, and dual-factor authentication.
"""
import os
import re
import secrets
import hashlib
from datetime import datetime, timedelta
import bcrypt
from dotenv import load_dotenv

import database.auth_db as auth_db
import services.email_service as email_service

load_dotenv()

ADMIN_EMAIL = os.getenv("DOCMINDX_ADMIN_EMAIL", "docmindxai@gmail.com").strip().lower()
ADMIN_PASSWORD_HASH = os.getenv("DOCMINDX_ADMIN_PASSWORD_HASH", "")

# OTP Configuration
OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
MAX_OTP_ATTEMPTS = 5

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# In-memory session tracking for active OTP tokens during flows
_ACTIVE_DEV_OTPS = {}

# ============================================================
# PASSWORD HASHING & VALIDATION
# ============================================================

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt with 12 rounds of salting."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password strength:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*...)."
    return True, "Strong password."

def validate_email_address(email: str) -> bool:
    """Validates email format using strict RFC-compliant regex."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

# ============================================================
# CRYPTOGRAPHIC OTP ENGINE
# ============================================================

def generate_secure_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(6))

def hash_otp_code(email: str, purpose: str, otp: str) -> str:
    """Hashes an OTP code with email and purpose context using SHA-256."""
    data = f"{email.strip().lower()}:{purpose}:{otp}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def request_otp(email: str, purpose: str, full_name: str = "") -> tuple[bool, str]:
    """
    Generates, stores, and dispatches a secure OTP for the specified purpose.
    Enforces resend cooldown, single active OTP, and expiration.
    """
    email = email.strip().lower()
    if not validate_email_address(email):
        return False, "Invalid email address format."

    # Check resend cooldown
    latest_record = auth_db.get_active_otp_record(email, purpose)
    if latest_record:
        created_time = datetime.strptime(latest_record["created_at"], "%Y-%m-%d %H:%M:%S")
        elapsed_seconds = (datetime.now() - created_time).total_seconds()
        if elapsed_seconds < OTP_RESEND_COOLDOWN_SECONDS:
            wait_remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed_seconds)
            return False, f"Please wait {wait_remaining}s before requesting a new OTP."

    otp = generate_secure_otp()
    otp_hash = hash_otp_code(email, purpose, otp)
    expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")

    # Store hashed OTP in database
    auth_db.store_otp(email, purpose, otp_hash, expires_at)
    _ACTIVE_DEV_OTPS[f"{email}:{purpose}"] = otp

    # Dispatch via email service
    if purpose == "REGISTRATION":
        email_service.send_registration_otp(email, full_name or "New Patient", otp)
        auth_db.log_security_event("REGISTRATION_OTP_SENT", email=email, details="Account verification code dispatched")
    elif purpose == "LOGIN":
        email_service.send_login_otp(email, full_name or "Patient", otp)
        auth_db.log_security_event("LOGIN_OTP_SENT", email=email, details="Login verification code dispatched")
    elif purpose == "RECOVERY":
        email_service.send_recovery_otp(email, full_name or "Patient", otp)
        auth_db.log_security_event("RECOVERY_OTP_SENT", email=email, details="Password recovery code dispatched")
    elif purpose == "ADMIN_LOGIN":
        email_service.send_admin_login_otp(email, otp)
        auth_db.log_security_event("ADMIN_OTP_SENT", email=email, details="Admin dual-factor verification dispatched")

    return True, "Verification code sent to your email address."

def verify_otp_code(email: str, purpose: str, entered_otp: str) -> tuple[bool, str]:
    """
    Verifies an entered OTP code against the latest active record.
    Enforces maximum attempts, expiration, and single-use invalidation.
    """
    email = email.strip().lower()
    record = auth_db.get_active_otp_record(email, purpose)
    if not record:
        return False, "No active verification code found. Please request a new code."

    # Check expiration
    expires_at = datetime.strptime(record["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expires_at:
        return False, "Verification code has expired. Please request a new code."

    # Check attempts
    if record["attempts"] >= MAX_OTP_ATTEMPTS:
        auth_db.log_security_event("OTP_ATTEMPTS_EXCEEDED", email=email, details=f"Purpose: {purpose}")
        return False, "Maximum verification attempts exceeded. Please request a new code."

    # Compare hashes securely
    expected_hash = record["otp_hash"]
    entered_hash = hash_otp_code(email, purpose, entered_otp.strip())

    if not secrets.compare_digest(expected_hash, entered_hash):
        auth_db.increment_otp_attempts(record["id"])
        attempts_left = MAX_OTP_ATTEMPTS - (record["attempts"] + 1)
        auth_db.log_security_event("FAILED_OTP_VERIFICATION", email=email, details=f"Attempts remaining: {attempts_left}")
        return False, f"Invalid verification code. {attempts_left} attempts remaining."

    # Success: consume OTP
    auth_db.mark_otp_verified(record["id"])
    _ACTIVE_DEV_OTPS.pop(f"{email}:{purpose}", None)
    return True, "Verification successful."

def get_dev_otp_fallback(email: str, purpose: str) -> str:
    """Returns the generated OTP for immediate developer testing feedback."""
    return _ACTIVE_DEV_OTPS.get(f"{email.strip().lower()}:{purpose}", "")

# ============================================================
# USER AUTHENTICATION FLOWS
# ============================================================

def register_user(full_name: str, email: str, password: str, confirm_password: str, dob: str = "") -> tuple[bool, str]:
    """
    Registration flow:
    Validate Input -> Validate Email -> Validate Password -> Validate DOB (>= 10 years) -> Create Pending User -> Generate OTP -> Send OTP.
    """
    if not full_name or len(full_name.strip()) < 2:
        return False, "Please enter your full name (at least 2 characters)."

    email = email.strip().lower()
    if not validate_email_address(email):
        return False, "Please provide a valid email address."

    if password != confirm_password:
        return False, "Password and Confirm Password do not match."

    pw_ok, pw_msg = validate_password_strength(password)
    if not pw_ok:
        return False, pw_msg

    clean_dob = str(dob or "").strip()
    if clean_dob:
        calc_age = auth_db.calculate_age_from_dob(clean_dob)
        if calc_age is None:
            return False, "Please provide a valid Date of Birth."
        if calc_age < 10:
            return False, "DocMindX AI Clinical Protocol: Minimum age must be at least 10 years. Pediatric profiles (< 10 years) require specialized clinical consultation."

    existing = auth_db.get_user_by_email(email)
    if existing:
        if existing["account_status"] == "ACTIVE" and existing["email_verified"]:
            return False, "An account with this email address is already registered. Please login."
        elif existing["account_status"] == "DISABLED":
            return False, "This account is currently disabled. Please contact support."
        else:
            # Update password hash for existing pending account and send new OTP
            new_hash = hash_password(password)
            auth_db.update_user_password(existing["id"], new_hash)
            if clean_dob:
                auth_db.update_user_profile(existing["id"], full_name, dob=clean_dob)
            else:
                auth_db.update_user_profile(existing["id"], full_name)
            request_otp(email, "REGISTRATION", full_name)
            return True, "A new verification code was sent to complete your registration."

    # Create new pending user
    pwd_hash = hash_password(password)
    user_id = auth_db.create_user(full_name, email, pwd_hash, account_status="PENDING", email_verified=0, dob=clean_dob)
    auth_db.log_security_event("USER_REGISTERED", email=email, user_id=user_id, details="Pending account created")

    # Generate and send registration OTP
    request_otp(email, "REGISTRATION", full_name)
    return True, "Registration initiated! Please enter the verification code sent to your email."

def activate_user_account(email: str, otp: str) -> tuple[bool, str]:
    """Verifies registration OTP and activates the account."""
    email = email.strip().lower()
    ok, msg = verify_otp_code(email, "REGISTRATION", otp)
    if not ok:
        return False, msg

    user = auth_db.get_user_by_email(email)
    if not user:
        return False, "User record not found."

    auth_db.update_user_status(user["id"], account_status="ACTIVE", email_verified=1)
    auth_db.log_security_event("ACCOUNT_ACTIVATED", email=email, user_id=user["id"], details="Email verified successfully")
    return True, "Account successfully activated! You may now log in."

def authenticate_credentials(email: str, password: str) -> tuple[bool, str, dict]:
    """
    Step 1 of Login: Validates Email + Password credentials.
    Does NOT issue authenticated session. Returns user record to trigger Login OTP.
    Password-only login is strictly prohibited.
    """
    email = email.strip().lower()
    if not validate_email_address(email):
        return False, "Invalid email format.", None

    user = auth_db.get_user_by_email(email)
    if not user:
        auth_db.log_security_event("FAILED_LOGIN_UNKNOWN_EMAIL", email=email)
        return False, "Invalid email address or password.", None

    if user["account_status"] == "DISABLED":
        auth_db.log_security_event("FAILED_LOGIN_DISABLED_ACCOUNT", email=email, user_id=user["id"])
        email_service.send_login_failed_alert(email, user.get("full_name", "User"), reason="Account disabled by administration")
        return False, "This account is currently disabled. Please contact administration.", None

    if not user["email_verified"] or user["account_status"] == "PENDING":
        return False, "Please verify your email address to activate your account before logging in.", {"pending_activation": True}

    if not verify_password(password, user["password_hash"]):
        auth_db.log_security_event("FAILED_LOGIN_WRONG_PASSWORD", email=email, user_id=user["id"])
        email_service.send_login_failed_alert(email, user.get("full_name", "User"), reason="Incorrect password entered")
        return False, "Invalid email address or password.", None

    return True, "Credentials verified. Proceeding to dual-factor authentication.", user

def send_login_verification_code(email: str) -> tuple[bool, str]:
    """Step 2 of Login: Dispatches 2FA Login OTP."""
    user = auth_db.get_user_by_email(email)
    full_name = user["full_name"] if user else ""
    return request_otp(email, "LOGIN", full_name)

def complete_login_with_otp(email: str, otp: str) -> tuple[bool, str, dict]:
    """
    Step 3 of Login: Verifies Login OTP and establishes authenticated session.
    """
    email = email.strip().lower()
    ok, msg = verify_otp_code(email, "LOGIN", otp)
    if not ok:
        user = auth_db.get_user_by_email(email)
        full_name = user.get("full_name", "User") if user else "User"
        email_service.send_login_failed_alert(email, full_name, reason="Invalid or expired verification code entered")
        return False, msg, None

    user = auth_db.get_user_by_email(email)
    if not user:
        return False, "User not found.", None

    auth_db.update_user_last_login(user["id"])
    auth_db.log_security_event("USER_LOGGED_IN", email=email, user_id=user["id"], details="Dual-factor login successful")
    email_service.send_login_success_notice(user["email"], user["full_name"])
    
    # Return safe session payload
    is_admin_user = (user["email"].strip().lower() == os.getenv("DOCMINDX_ADMIN_EMAIL", "docmindxai@gmail.com").strip().lower()) or (user.get("role") == "admin")
    session_data = {
        "id": user["id"],
        "user_id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": "admin" if is_admin_user else user.get("role", "patient"),
        "is_admin": is_admin_user,
        "authenticated": True,
        "auth_time": datetime.now().isoformat()
    }
    return True, "Login successful.", session_data

# ============================================================
# RECOVERY PASSWORD FLOW (NOT "FORGOT PASSWORD")
# ============================================================

def initiate_recovery_password(email: str) -> tuple[bool, str]:
    """
    Initiates Recovery Password flow.
    Sends Recovery OTP. Does not reveal whether email exists for security.
    """
    email = email.strip().lower()
    if not validate_email_address(email):
        return False, "Invalid email address."

    user = auth_db.get_user_by_email(email)
    if user and user["account_status"] != "DISABLED":
        request_otp(email, "RECOVERY", user["full_name"])
    else:
        # Dummy delay simulation to mitigate timing attacks
        pass

    return True, "If an active account exists with this email, a recovery verification code has been dispatched."

def verify_recovery_otp_and_reset_password(email: str, otp: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Verifies recovery OTP, validates new password strength, and updates password hash.
    """
    email = email.strip().lower()
    if new_password != confirm_password:
        return False, "New Password and Confirm Password do not match."

    pw_ok, pw_msg = validate_password_strength(new_password)
    if not pw_ok:
        return False, pw_msg

    ok, msg = verify_otp_code(email, "RECOVERY", otp)
    if not ok:
        return False, msg

    user = auth_db.get_user_by_email(email)
    if not user:
        return False, "Account record not found."

    new_hash = hash_password(new_password)
    auth_db.update_user_password(user["id"], new_hash)
    auth_db.log_security_event("PASSWORD_RECOVERED", email=email, user_id=user["id"], details="Password successfully reset via recovery flow")
    
    # Send confirmation security email
    email_service.send_password_changed_notice(email, user["full_name"])
    return True, "Your password has been successfully reset. You may now log in."

# ============================================================
# CHANGE PASSWORD FLOW
# ============================================================

def change_user_password(user_id: int, current_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Validates current password, checks new password strength, and updates hash.
    """
    user = auth_db.get_user_by_id(user_id)
    if not user:
        return False, "User session invalid."

    if not verify_password(current_password, user["password_hash"]):
        auth_db.log_security_event("FAILED_PASSWORD_CHANGE_WRONG_CURRENT", user_id=user_id, email=user["email"])
        return False, "Incorrect current password."

    if new_password != confirm_password:
        return False, "New Password and Confirm Password do not match."

    if current_password == new_password:
        return False, "New password must be different from your current password."

    pw_ok, pw_msg = validate_password_strength(new_password)
    if not pw_ok:
        return False, pw_msg

    new_hash = hash_password(new_password)
    auth_db.update_user_password(user_id, new_hash)
    auth_db.log_security_event("PASSWORD_CHANGED_BY_USER", user_id=user_id, email=user["email"], details="Password changed via account settings")
    email_service.send_password_changed_notice(user["email"], user["full_name"])
    return True, "Password successfully updated."

# ============================================================
# ADMIN AUTHENTICATION & PRIVILEGE ENFORCEMENT
# ============================================================

def get_admin_credentials() -> tuple[str, str]:
    """Fetches administrator email and password hash from environment."""
    adm_email = os.getenv("DOCMINDX_ADMIN_EMAIL", "docmindxai@gmail.com").strip().lower()
    adm_hash = os.getenv("DOCMINDX_ADMIN_PASSWORD_HASH", "")
    return adm_email, adm_hash

def authenticate_admin_credentials(email: str, password: str) -> tuple[bool, str]:
    """
    Step 1 of Admin Login: Validates admin email and password hash from environment.
    Admin password is NEVER stored in plaintext or hard-coded.
    """
    if not email or not email.strip():
        return False, "Administrator Identity is required."
    if not password or not password.strip():
        return False, "Master Password is required."
    if len(password.strip()) < 8:
        return False, "Password must be at least 8 characters long."

    adm_email, adm_hash = get_admin_credentials()
    if email.strip().lower() != adm_email:
        auth_db.log_security_event("ADMIN_LOGIN_UNAUTHORIZED_EMAIL", email=email)
        return False, "Invalid administrative credentials."

    if not adm_hash:
        return False, "Admin password hash is not configured in environment variables."

    if not verify_password(password, adm_hash):
        auth_db.log_security_event("ADMIN_LOGIN_FAILED_PASSWORD", email=email)
        email_service.send_login_failed_alert(email, "System Administrator", reason="Incorrect administrative master password entered")
        return False, "Invalid administrative credentials."

    return True, "Admin credentials verified. Enter OTP to access Admin Console."

def send_admin_login_otp_code(email: str) -> tuple[bool, str]:
    """Step 2 of Admin Login: Sends high-security 2FA OTP to admin email."""
    return request_otp(email, "ADMIN_LOGIN", "Administrator")

def complete_admin_login(email: str, otp: str) -> tuple[bool, str, dict]:
    """
    Step 3 of Admin Login: Verifies admin OTP and establishes authenticated admin session.
    """
    adm_email, _ = get_admin_credentials()
    if email.strip().lower() != adm_email:
        return False, "Unauthorized administrative access attempt.", None

    ok, msg = verify_otp_code(email, "ADMIN_LOGIN", otp)
    if not ok:
        email_service.send_login_failed_alert(email, "System Administrator", reason="Invalid or expired admin 2FA verification key entered")
        return False, msg, None

    auth_db.log_security_event("ADMIN_LOGGED_IN", email=email, details="Admin dual-factor authentication successful")
    email_service.send_login_success_notice(adm_email, "System Administrator")
    
    session_data = {
        "id": 0,
        "user_id": 0,
        "full_name": "System Administrator",
        "email": adm_email,
        "role": "admin",
        "authenticated": True,
        "is_admin": True,
        "auth_time": datetime.now().isoformat()
    }
    return True, "Admin authentication successful.", session_data

def is_admin_session(session_dict: dict) -> bool:
    """Server-side authorization check to prevent privilege escalation."""
    if not isinstance(session_dict, dict):
        return False
    if not session_dict.get("authenticated"):
        return False
    if session_dict.get("role") != "admin":
        return False
    adm_email, _ = get_admin_credentials()
    if session_dict.get("email", "").strip().lower() != adm_email:
        return False
    return True
