"""
DocMindX AI — Authentication & Security Full Panel Component
Provides a full-page clinical identity portal for Registration, 2FA Login,
Recovery Password, Change Password, and Administrator Authentication.
Zero popups/dialogs, zero emojis, clean clinical design system.
"""
import streamlit as st
import datetime
import database.auth_db as auth_db
import services.auth_service as auth_svc
from components.theme_toggle import theme_toggle_switch

def init_auth_session_state():
    """Initializes authentication session state variables."""
    if "user_auth" not in st.session_state:
        st.session_state["user_auth"] = None
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "LOGIN"
    if "auth_temp_email" not in st.session_state:
        st.session_state["auth_temp_email"] = ""
    if "auth_temp_name" not in st.session_state:
        st.session_state["auth_temp_name"] = ""

def is_authenticated() -> bool:
    """Returns True if the current user session is authenticated."""
    auth = st.session_state.get("user_auth")
    return bool(auth and auth.get("authenticated", False))

def get_current_user() -> dict:
    """Returns current authenticated user dictionary or None."""
    return st.session_state.get("user_auth")

def is_admin_authenticated() -> bool:
    """Returns True if the current user session is an authenticated Administrator."""
    auth = get_current_user()
    return bool(auth and auth.get("is_admin", False) and auth_svc.is_admin_session(auth))

def logout_user():
    """Clears current authenticated session and redirects to Health Assessment."""
    st.session_state["user_auth"] = None
    st.session_state["auth_view"] = "LOGIN"
    st.session_state["active_panel"] = "Health Assessment"
def compute_password_strength(password: str) -> tuple:
    """
    Computes dynamic password strength:
    returns (score 0-5, label, label_color, list of 5 bar colors).
    """
    p = password or ""
    if not p:
        return 0, "", "#94A3B8", ["#E2E8F0", "#E2E8F0", "#E2E8F0", "#E2E8F0", "#E2E8F0"]

    has_len8 = len(p) >= 8
    has_letters = any(c.isalpha() for c in p)
    has_numbers = any(c.isdigit() for c in p)
    has_special = any(not c.isalnum() for c in p)
    has_bonus = len(p) >= 12 and any(c.isupper() for c in p) and any(c.islower() for c in p)

    score = sum([has_len8, has_letters, has_numbers, has_special, has_bonus])
    if score >= 4:
        colors = ["#10B981" if i < score else "#E2E8F0" for i in range(5)]
        return score, "Strong Password", "#10B981", colors
    elif score >= 2:
        colors = ["#F59E0B" if i < score else "#E2E8F0" for i in range(5)]
        return score, "Moderate Password", "#F59E0B", colors
    else:
        colors = ["#EF4444" if i < 1 else "#E2E8F0" for i in range(5)]
        return score, "Weak Password", "#EF4444", colors


def render_password_requirements_box(password: str = "") -> str:
    """Renders clinical password requirements checklist box with live dynamic validation matching Image 2 & 4."""
    p = password or ""
    has_len8 = len(p) >= 8
    has_numbers = any(c.isdigit() for c in p)
    has_letters = any(c.isalpha() for c in p)
    has_special = any(not c.isalnum() for c in p)

    def _get_req_icon(passed: bool) -> str:
        if passed:
            return (
                '<svg width="15" height="15" viewBox="0 0 24 24" fill="#10B981" stroke="none" style="flex-shrink:0;">'
                '<circle cx="12" cy="12" r="10" fill="#10B981"/>'
                '<polyline points="8 12 11 15 16 9" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                '</svg>'
            )
        else:
            return (
                '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" style="flex-shrink:0;">'
                '<circle cx="12" cy="12" r="10"/>'
                '</svg>'
            )

    icon_len = _get_req_icon(has_len8)
    icon_num = _get_req_icon(has_numbers)
    icon_let = _get_req_icon(has_letters)
    icon_spc = _get_req_icon(has_special)

    color_len = "#059669" if has_len8 else "#64748B"
    color_num = "#059669" if has_numbers else "#64748B"
    color_let = "#059669" if has_letters else "#64748B"
    color_spc = "#059669" if has_special else "#64748B"

    weight_len = "700" if has_len8 else "500"
    weight_num = "700" if has_numbers else "500"
    weight_let = "700" if has_letters else "500"
    weight_spc = "700" if has_special else "500"

    all_met = has_len8 and has_numbers and has_letters and has_special
    box_bg = "rgba(16, 185, 129, 0.06)" if all_met else "rgba(37, 99, 235, 0.04)"
    box_border = "1px solid rgba(16, 185, 129, 0.4)" if all_met else "1px solid #DBEAFE"
    icon_bg = "#10B981" if all_met else "#2563EB"

    return f"""
    <div class="auth-pwd-req-box" style="background: {box_bg}; border: {box_border}; border-radius: 12px; padding: 12px 14px; margin-top: 10px;">
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <div style="width: 32px; height: 32px; border-radius: 9px; background: {icon_bg}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <polyline points="9 12 11 14 15 10"/>
                </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
                <div style="font-weight: 800; font-size: 0.88rem; color: #1E40AF; margin-bottom: 8px;">
                    Password Requirements:
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px;">
                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.76rem; color: {color_len}; font-weight: {weight_len};">
                        {icon_len} <span>At least 8 characters</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.76rem; color: {color_num}; font-weight: {weight_num};">
                        {icon_num} <span>Include numbers (0-9)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.76rem; color: {color_let}; font-weight: {weight_let};">
                        {icon_let} <span>Include letters (A-Z, a-z)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.76rem; color: {color_spc}; font-weight: {weight_spc};">
                        {icon_spc} <span>Include a special character (e.g. ! @ # $)</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


def render_auth_portal_panel(T: dict = None, lang_code: str = "en", LANG_OPTIONS: list = None, sync_language = None):
    """
    Renders the dedicated full-page Authentication & Clinical Identity Panel.
    Zero popups, zero emojis, 100% compliant with the clinical design system.
    """
    init_auth_session_state()
    T = T or {}
    LANG_OPTIONS = LANG_OPTIONS or ["English", "हिन्दी (Hindi)", "ગુજરાતી (Gujarati)"]

    # Redirect already logged-in users directly to their designated panel
    curr_user = get_current_user()
    if curr_user and is_authenticated():
        if auth_svc.is_admin_session(curr_user):
            st.session_state["active_panel"] = "Admin Panel"
        else:
            st.session_state["active_panel"] = "Family Management"
        st.rerun()

    # 1. Consistent Top Header Bar (identical to Modules 1-5)
    auth_icon_html = (
        '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(37, 99, 235, 0.08); '
        'border: 1.5px solid #2563EB; display: flex; align-items: center; justify-content: center; '
        'box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); flex-shrink: 0;">'
        '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
        '</svg></div>'
    )

    with st.container(key="mm_top_header_card_auth"):
        hdr_c1, hdr_c2, hdr_c3, hdr_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr_c1:
            title_auth = "Clinical Security & Identity Portal"
            sub_auth = "Dual-factor identity verification, patient registration, and credential recovery."
            st.markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{auth_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_auth}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_auth}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with hdr_c2:
            st.markdown(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 38px;">'
                f'<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: rgba(16, 185, 129, 0.10); border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-weight: 700; font-size: 0.80rem; display: inline-flex; align-items: center; gap: 8px;">'
                f'<span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; display: inline-block;"></span>'
                f'2FA SECURITY ACTIVE'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        with hdr_c3:
            if sync_language:
                st.selectbox(
                    "Header Lang Selector Auth",
                    options=LANG_OPTIONS,
                    key="hdr_lang_auth",
                    label_visibility="collapsed",
                    on_change=sync_language,
                    args=("hdr_lang_auth",)
                )
        with hdr_c4:
            new_theme_auth = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_auth")
            if new_theme_auth != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_auth
                st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    view = st.session_state.get("auth_view", "LOGIN")

    if view == "RECOVERY":
        # Top banner for Recovery matching Image 4
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(37, 99, 235, 0.04);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="#2563EB">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    <polyline points="7 12 10 12 11.5 8 13.5 16 15 12 17 12" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div style="text-align: left;">
                    <div class="auth-card-title" style="font-weight: 800; font-size: 1.15rem; color: #0F172A; line-height: 1.1;">DocMindX AI</div>
                    <div class="auth-card-subtitle" style="font-size: 0.65rem; color: #64748B; font-weight: 600; letter-spacing: 0.02em;">Secure Health • Smarter Tomorrow</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 34px; height: 34px; border-radius: 10px; background: #EFF6FF; border: 1.5px solid #BFDBFE; display: flex; align-items: center; justify-content: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <div style="text-align: left;">
                    <div class="auth-card-title" style="font-weight: 700; font-size: 0.82rem; color: #1E293B; line-height: 1.1;">Your Data is Safe</div>
                    <div class="auth-card-subtitle" style="font-size: 0.68rem; color: #64748B;">Encrypted & Protected</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main Grid Layout: Left Info Card + Right Authentication Form
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        with st.container(key="auth_left_vault_card", border=True):
            if view == "RECOVERY":
                st.markdown("""
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center; padding: 6px 4px; height: 100%; justify-content: space-between;">
                    <div>
                        <!-- 3D Open Envelope with Lock and Checkmark -->
                        <svg viewBox="0 0 260 200" style="width: 100%; max-width: 185px; height: auto;" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs>
                                <radialGradient id="envGlow" cx="50%" cy="50%" r="50%">
                                    <stop offset="0%" stop-color="#60A5FA" stop-opacity="0.35"/>
                                    <stop offset="100%" stop-color="#60A5FA" stop-opacity="0"/>
                                </radialGradient>
                                <linearGradient id="envBody" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stop-color="#3B82F6"/>
                                    <stop offset="100%" stop-color="#1D4ED8"/>
                                </linearGradient>
                                <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                    <stop offset="0%" stop-color="#FFFFFF"/>
                                    <stop offset="100%" stop-color="#F1F5F9"/>
                                </linearGradient>
                                <filter id="envShadow" x="-10%" y="-10%" width="130%" height="130%">
                                    <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#1E3A8A" flood-opacity="0.2"/>
                                </filter>
                            </defs>
                            <ellipse cx="130" cy="115" rx="80" ry="40" fill="url(#envGlow)"/>
                            <!-- Envelope Back -->
                            <rect x="55" y="75" width="150" height="95" rx="14" fill="#1E40AF"/>
                            <!-- Card sliding out -->
                            <rect x="75" y="40" width="110" height="75" rx="10" fill="url(#cardGrad)" filter="url(#envShadow)"/>
                            <!-- Lock on Card -->
                            <rect x="115" y="68" width="30" height="24" rx="4" fill="#2563EB"/>
                            <path d="M122 68 V59 A8 8 0 0 1 138 59 V68" stroke="#2563EB" stroke-width="4" fill="none"/>
                            <circle cx="130" cy="78" r="2.5" fill="#FFFFFF"/>
                            <!-- Envelope Flaps -->
                            <path d="M55 85 L130 140 L205 85 V155 C205 163 198 170 190 170 H70 C62 170 55 163 55 155 Z" fill="url(#envBody)" filter="url(#envShadow)"/>
                            <path d="M55 170 L115 120" stroke="#1E40AF" stroke-width="1.5" opacity="0.4"/>
                            <path d="M205 170 L145 120" stroke="#1E40AF" stroke-width="1.5" opacity="0.4"/>
                            <!-- Floating Sparkles -->
                            <circle cx="50" cy="55" r="3" fill="#60A5FA" opacity="0.7"/>
                            <circle cx="210" cy="50" r="2.5" fill="#60A5FA" opacity="0.7"/>
                            <line x1="205" y1="65" x2="215" y2="65" stroke="#60A5FA" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
                            <!-- Green Check Badge -->
                            <circle cx="190" cy="135" r="16" fill="#10B981" filter="url(#envShadow)"/>
                            <polyline points="183 135 188 140 198 130" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <h3 class="auth-card-title" style="margin: 10px 0 4px 0; font-size: 1.30rem; font-weight: 800; color: #0F172A;">Account Recovery</h3>
                        <p class="auth-card-subtitle" style="margin: 0 0 14px 0; font-size: 0.80rem; color: #64748B; max-width: 310px; line-height: 1.4;">
                            We'll send a secure password recovery code to your registered email address.
                        </p>
                        <!-- Safe & Secure Box -->
                        <div style="background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 12px; padding: 10px 14px; display: flex; align-items: center; gap: 12px; width: 100%; max-width: 320px; margin: 0 auto 12px auto; text-align: left;">
                            <div style="width: 34px; height: 34px; border-radius: 10px; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                    <polyline points="9 12 11 14 15 10"/>
                                </svg>
                            </div>
                            <div>
                                <strong style="color: #1E40AF; font-size: 0.82rem; display: block;">Safe & Secure</strong>
                                <span style="color: #64748B; font-size: 0.70rem; line-height: 1.35;">Your information is never shared with anyone and is fully encrypted.</span>
                            </div>
                        </div>
                    </div>
                    <!-- 3 Step Indicators (animated) -->
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 6px; padding-top: 4px;">
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span class="auth-step-dot-1"></span>
                            <span class="auth-step-dot-2"></span>
                            <span class="auth-step-dot-3"></span>
                        </div>
                        <span style="font-size: 0.74rem; color: #94A3B8; font-weight: 600;">Recover &bull; Verify &bull; Get Back</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 12px;">
                    <div style="width: 44px; height: 44px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            <path d="M12 8v8"/>
                            <path d="M8 12h8"/>
                        </svg>
                    </div>
                    <div>
                        <h3 class="auth-card-title" style="margin: 0; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.01em; color: #1E293B;">Enterprise Medical Vault</h3>
                        <p class="auth-card-subtitle" style="margin: 2px 0 0 0; font-size: 0.80rem; color: #64748B; line-height: 1.45;">
                            DocMindX AI enforces bank-grade dual-factor cryptographic identity protocols. Your clinical health records, family profiles, and scan history remain strictly isolated and protected.
                        </p>
                    </div>
                </div>
            <div class="auth-left-middle-grid" style="display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 10px; align-items: center; margin-top: 8px;">
                <!-- 4 Feature Cards -->
                <div style="display: flex; flex-direction: column; gap: 7px;">
                    <!-- 01 -->
                    <div class="auth-feat-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 7px 10px; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #D1FAE5; border: 1px solid #A7F3D0; display: flex; align-items: center; justify-content: center; color: #059669; font-size: 0.70rem; font-weight: 800; flex-shrink: 0;">01</div>
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #ECFDF5; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                        </div>
                        <div>
                            <strong class="auth-card-title" style="font-size: 0.80rem; color: #1E293B; display: block; line-height: 1.15;">Mandatory Dual-Factor (2FA) OTP</strong>
                            <span class="auth-card-subtitle" style="font-size: 0.69rem; color: #64748B; line-height: 1.15;">Single-use cryptographic OTPs sent to your verified email.</span>
                        </div>
                    </div>
                    <!-- 02 -->
                    <div class="auth-feat-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 7px 10px; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #DBEAFE; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; color: #2563EB; font-size: 0.70rem; font-weight: 800; flex-shrink: 0;">02</div>
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8"/><path d="M8 12h8"/>
                            </svg>
                        </div>
                        <div>
                            <strong class="auth-card-title" style="font-size: 0.80rem; color: #1E293B; display: block; line-height: 1.15;">Bcrypt 12-Round Password Encryption</strong>
                            <span class="auth-card-subtitle" style="font-size: 0.69rem; color: #64748B; line-height: 1.15;">Passwords and OTPs are never stored or logged in plaintext.</span>
                        </div>
                    </div>
                    <!-- 03 -->
                    <div class="auth-feat-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 7px 10px; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #FEF3C7; border: 1px solid #FDE68A; display: flex; align-items: center; justify-content: center; color: #D97706; font-size: 0.70rem; font-weight: 800; flex-shrink: 0;">03</div>
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #FFFBEB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                            </svg>
                        </div>
                        <div>
                            <strong class="auth-card-title" style="font-size: 0.80rem; color: #1E293B; display: block; line-height: 1.15;">Relational Family Profiles</strong>
                            <span class="auth-card-subtitle" style="font-size: 0.69rem; color: #64748B; line-height: 1.15;">Attach scans and reports dynamically to individual family members.</span>
                        </div>
                    </div>
                    <div class="auth-feat-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 7px 10px; display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #EDE9FE; border: 1px solid #DDD6FE; display: flex; align-items: center; justify-content: center; color: #7C3AED; font-size: 0.70rem; font-weight: 800; flex-shrink: 0;">04</div>
                        <div style="width: 22px; height: 22px; border-radius: 6px; background: #F5F3FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                            </svg>
                        </div>
                        <div>
                            <strong class="auth-card-title" style="font-size: 0.80rem; color: #1E293B; display: block; line-height: 1.15;">Parameterized SQL Defense</strong>
                            <span class="auth-card-subtitle" style="font-size: 0.69rem; color: #64748B; line-height: 1.15;">100% prepared statements with absolute SQL injection immunity.</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin: 4px 0;">
                    <svg viewBox="0 0 260 210" style="width: 100%; max-width: 145px; height: auto;" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <radialGradient id="pedLight" cx="50%" cy="50%" r="50%">
                                <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.35"/>
                                <stop offset="100%" stop-color="#38BDF8" stop-opacity="0"/>
                            </radialGradient>
                            <linearGradient id="shieldMain" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#38BDF8"/>
                                <stop offset="50%" stop-color="#2563EB"/>
                                <stop offset="100%" stop-color="#1D4ED8"/>
                            </linearGradient>
                            <linearGradient id="pedTopGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stop-color="#E0F2FE"/>
                                <stop offset="100%" stop-color="#BAE6FD"/>
                            </linearGradient>
                            <linearGradient id="pedBaseGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stop-color="#0284C7"/>
                                <stop offset="100%" stop-color="#0369A1"/>
                            </linearGradient>
                            <filter id="shieldGlow" x="-20%" y="-20%" width="140%" height="140%">
                                <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#2563EB" flood-opacity="0.35"/>
                            </filter>
                        </defs>
                        <ellipse cx="130" cy="146" rx="72" ry="24" fill="url(#pedLight)"/>
                        <path d="M60 142 C60 152 200 152 200 142 L200 150 C200 160 60 160 60 150 Z" fill="#0C4A6E" opacity="0.6"/>
                        <path d="M68 136 C68 146 192 146 192 136 L192 144 C192 154 68 154 68 144 Z" fill="url(#pedBaseGrad)"/>
                        <ellipse cx="130" cy="136" rx="62" ry="14" fill="#38BDF8" opacity="0.8"/>
                        <path d="M78 130 C78 138 182 138 182 130 L182 134 C182 142 78 142 78 134 Z" fill="#0284C7"/>
                        <ellipse cx="130" cy="130" rx="52" ry="11" fill="url(#pedTopGrad)"/>
                        <ellipse cx="130" cy="130" rx="44" ry="8" fill="#FFFFFF" opacity="0.9"/>
                        <g filter="url(#shieldGlow)">
                            <path d="M130 38 L166 54 C166 94 148 120 130 130 C112 120 94 94 94 54 Z" fill="url(#shieldMain)"/>
                            <path d="M130 42 L162 56 C162 92 146 116 130 125 C114 116 98 92 98 56 Z" fill="none" stroke="#BAE6FD" stroke-width="1.5" opacity="0.7"/>
                            <path d="M125 66 H135 V77 H146 V87 H135 V98 H125 V87 H114 V77 H125 Z" fill="#FFFFFF"/>
                        </g>
                        <g>
                            <circle cx="72" cy="48" r="14" fill="#2563EB" filter="url(#shieldGlow)"/>
                            <path d="M68 43 H74 L77 46 V53 H68 Z" fill="#FFFFFF"/>
                            <line x1="70" y1="48" x2="75" y2="48" stroke="#2563EB" stroke-width="1"/>
                            <line x1="70" y1="50" x2="74" y2="50" stroke="#2563EB" stroke-width="1"/>
                        </g>
                        <g>
                            <circle cx="188" cy="54" r="14" fill="#2563EB" filter="url(#shieldGlow)"/>
                            <rect x="183" y="51" width="10" height="7" rx="1" fill="#FFFFFF"/>
                            <path d="M185 51 V48 A3 3 0 0 1 191 48 V51" stroke="#FFFFFF" stroke-width="1.5" fill="none"/>
                        </g>
                        <g>
                            <circle cx="58" cy="108" r="14" fill="#0D9488" filter="url(#shieldGlow)"/>
                            <circle cx="58" cy="105" r="3" fill="#FFFFFF"/>
                            <path d="M53 113 C53 110 63 110 63 113" stroke="#FFFFFF" stroke-width="1.6" fill="none"/>
                        </g>
                        <g>
                            <circle cx="196" cy="118" r="14" fill="#7C3AED" filter="url(#shieldGlow)"/>
                            <ellipse cx="196" cy="114" rx="6" ry="2" fill="#FFFFFF"/>
                            <path d="M190 114 V120 C190 122 202 122 202 120 V114" stroke="#FFFFFF" stroke-width="1.2" fill="none"/>
                        </g>
                    </svg>
                    <div style="margin-top: 1px; font-family: 'Segoe Script', 'Comic Sans MS', cursive, sans-serif; font-size: 0.84rem; color: #1E40AF; font-weight: 700; transform: rotate(-3deg);">
                        Your Health Data Our Priority
                        <div style="height: 3px; background: #3B82F6; border-radius: 2px; width: 70%; margin: 2px auto 0 auto;"></div>
                    </div>
                </div>
            </div>
            <div class="auth-alert-banner" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #EF4444; border-radius: 9px; margin-top: 10px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background: #EF4444; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #FFFFFF; font-weight: 900; font-size: 0.74rem;">
                    !
                </div>
                <div style="font-size: 0.74rem; line-height: 1.35;">
                    <strong style="color: #DC2626;">Clinical Privacy Standard:</strong>
                    <span style="color: #991B1B;">Compliant with HIPAA and WHO clinical health data security guidelines.</span>
                </div>
            </div>
            <div class="auth-trust-grid" style="display: grid; grid-template-columns: repeat(4, minmax(72px, 1fr)); gap: 8px; margin-top: 12px; margin-bottom: 4px; width: 100%;">
                <div class="auth-trust-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 10px 8px; display: flex; align-items: flex-start; gap: 6px; min-height: 64px; box-sizing: border-box; overflow: visible;">
                    <div style="width: 26px; height: 26px; border-radius: 6px; background: #DCFCE7; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8"/><path d="M8 12h8"/>
                        </svg>
                    </div>
                    <div style="min-width: 0; flex: 1; word-break: break-word;">
                        <div style="font-weight: 800; font-size: 0.76rem; color: #1E293B; line-height: 1.2;" class="auth-card-title">Secure</div>
                        <div style="font-size: 0.68rem; color: #64748B; line-height: 1.3; margin-top: 2px;" class="auth-card-subtitle">Bank-Grade</div>
                    </div>
                </div>
                <div class="auth-trust-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 10px 8px; display: flex; align-items: flex-start; gap: 6px; min-height: 64px; box-sizing: border-box; overflow: visible;">
                    <div style="width: 26px; height: 26px; border-radius: 6px; background: #DBEAFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                        </svg>
                    </div>
                    <div style="min-width: 0; flex: 1; word-break: break-word;">
                        <div style="font-weight: 800; font-size: 0.76rem; color: #1E293B; line-height: 1.2;" class="auth-card-title">Private</div>
                        <div style="font-size: 0.68rem; color: #64748B; line-height: 1.3; margin-top: 2px;" class="auth-card-subtitle">Your Control</div>
                    </div>
                </div>
                <div class="auth-trust-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 10px 8px; display: flex; align-items: flex-start; gap: 6px; min-height: 64px; box-sizing: border-box; overflow: visible;">
                    <div style="width: 26px; height: 26px; border-radius: 6px; background: #EDE9FE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                        </svg>
                    </div>
                    <div style="min-width: 0; flex: 1; word-break: break-word;">
                        <div style="font-weight: 800; font-size: 0.76rem; color: #1E293B; line-height: 1.2;" class="auth-card-title">Compliant</div>
                        <div style="font-size: 0.68rem; color: #64748B; line-height: 1.3; margin-top: 2px;" class="auth-card-subtitle">HIPAA / WHO</div>
                    </div>
                </div>
                <div class="auth-trust-item" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 9px; padding: 10px 8px; display: flex; align-items: flex-start; gap: 6px; min-height: 64px; box-sizing: border-box; overflow: visible;">
                    <div style="width: 26px; height: 26px; border-radius: 6px; background: #FEF3C7; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                    </div>
                    <div style="min-width: 0; flex: 1; word-break: break-word;">
                        <div style="font-weight: 800; font-size: 0.76rem; color: #1E293B; line-height: 1.2;" class="auth-card-title">Trusted</div>
                        <div style="font-size: 0.68rem; color: #64748B; line-height: 1.3; margin-top: 2px;" class="auth-card-subtitle">Healthcare</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        view = st.session_state.get("auth_view", "LOGIN")

        with st.container(key="auth_right_signin_card", border=True):
            # 1. SIGN IN VIEW
            if view == "LOGIN":
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 44px; height: 44px; border-radius: 12px; background: #EFF6FF; border: 1px solid #DBEAFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                                <circle cx="9" cy="7" r="4"/>
                                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="auth-card-title" style="margin: 0; font-size: 1.35rem; font-weight: 800; color: #0F172A;">Patient Sign In</h3>
                            <p class="auth-card-subtitle" style="margin: 3px 0 0 0; font-size: 0.80rem; color: #64748B;">Enter your registered email and password to receive your 2FA verification code.</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="#2563EB">
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            <polyline points="7 12 10 12 11.5 8 13.5 16 15 12 17 12" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <div style="text-align: left;">
                            <div class="auth-card-title" style="font-weight: 800; font-size: 1.15rem; color: #0F172A; line-height: 1.1;">DocMindX AI</div>
                            <div class="auth-card-subtitle" style="font-size: 0.65rem; color: #64748B; font-weight: 600; letter-spacing: 0.02em;">Secure Health • Smarter Tomorrow</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-input-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <span>Registered Email Address</span>
                </div>
                """, unsafe_allow_html=True)
                login_email = st.text_input("Registered Email Address", key="panel_login_email", placeholder="you@example.com", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="auth-input-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>Account Password</span>
                </div>
                """, unsafe_allow_html=True)

                login_password = st.text_input("Account Password", type="password", key="panel_login_password", placeholder="••••••••", label_visibility="collapsed")

                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                c_btn1, c_btn2 = st.columns([1, 1], gap="medium")
                with c_btn1:
                    if st.button(
                        "**Continue to 2FA Code →**  \nGet verification code on your email",
                        type="primary",
                        use_container_width=True,
                        key="panel_btn_login_submit"
                    ):
                        if not login_email or not login_password:
                            st.error("Please enter both email and password.")
                        else:
                            ok, msg, user = auth_svc.authenticate_credentials(login_email, login_password)
                            if ok:
                                st.session_state["auth_temp_email"] = login_email.strip().lower()
                                st.session_state["auth_temp_name"] = user.get("full_name", "")
                                auth_svc.send_login_verification_code(login_email)
                                st.session_state["auth_view"] = "LOGIN_OTP"
                                st.rerun()
                            else:
                                if user and user.get("pending_activation"):
                                    st.warning(msg)
                                    if st.button("Resend Activation Code", key="panel_btn_resend_act"):
                                        auth_svc.request_otp(login_email, "REGISTRATION")
                                        st.session_state["auth_temp_email"] = login_email
                                        st.session_state["auth_view"] = "REGISTER_OTP"
                                        st.rerun()
                                else:
                                    st.error(msg)
                with c_btn2:
                    if st.button(
                        "**Create New Account**  \nJoin DocMindX AI",
                        use_container_width=True,
                        key="panel_btn_goto_reg"
                    ):
                        st.session_state["auth_view"] = "REGISTER"
                        st.rerun()

                st.markdown('<div class="auth-or-divider"><span>OR</span></div>', unsafe_allow_html=True)
                opt_c1, opt_c2 = st.columns([1, 1], gap="medium")
                with opt_c1:
                    if st.button(
                        "**Recovery Password**  \nReset your account password",
                        use_container_width=True,
                        key="panel_btn_goto_rec"
                    ):
                        st.session_state["auth_view"] = "RECOVERY"
                        st.rerun()
                with opt_c2:
                    if st.button(
                        "**Administrator Access**  \nAuthorized personnel only",
                        use_container_width=True,
                        key="panel_btn_goto_admin"
                    ):
                        st.session_state["auth_view"] = "ADMIN_LOGIN"
                        st.rerun()

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button(
                    "**Return to Clinical Dashboard**  \nBack to main application",
                    use_container_width=True,
                    key="panel_btn_return_dashboard"
                ):
                    st.session_state["active_panel"] = "Health Assessment"
                    st.rerun()

                st.markdown("""
                <div class="auth-card-footer">
                    <div class="auth-footer-left">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                        <span>All communications are encrypted using industry-standard TLS 1.3</span>
                    </div>
                    <div>
                        <span>Version 2.0.0</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 2. LOGIN 2FA OTP VIEW
            elif view == "LOGIN_OTP":
                email = st.session_state.get("auth_temp_email", "")
                st.markdown(f"""
                <div style="background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
                    <div style="font-weight: 700; color: #60A5FA; font-size: 1.0rem; margin-bottom: 4px;">Enter Dual-Factor Verification Code</div>
                    <div style="font-size: 0.84rem; color: #CBD5E1;">A 6-digit cryptographic verification code has been dispatched to <strong>{email}</strong>.</div>
                </div>
                """, unsafe_allow_html=True)

                otp_input = st.text_input("Enter 6-Digit Code", max_chars=6, key="panel_login_otp_input", placeholder="123456")

                c_v1, c_v2 = st.columns([1, 1])
                with c_v1:
                    if st.button("Verify Code & Complete Sign In", type="primary", use_container_width=True, key="panel_btn_verify_login"):
                        if not otp_input or len(otp_input.strip()) < 6:
                            st.error("Please enter the complete 6-digit code.")
                        else:
                            ok, msg, session_data = auth_svc.complete_login_with_otp(email, otp_input)
                            if ok:
                                st.session_state["user_auth"] = session_data
                                if auth_svc.is_admin_session(session_data):
                                    st.session_state["active_panel"] = "Admin Panel"
                                else:
                                    st.session_state["active_panel"] = "Family Management"
                                st.session_state["auth_view"] = "LOGIN"
                                st.success("Successfully authenticated!")
                                st.rerun()
                            else:
                                st.error(msg)
                with c_v2:
                    if st.button("Resend Verification Code", use_container_width=True, key="panel_btn_resend_login"):
                        ok, msg = auth_svc.send_login_verification_code(email)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("← Back to Sign In", key="panel_btn_back_from_otp"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

            # 3. REGISTRATION VIEW
            elif view == "REGISTER":
                # Header matching Image 2
                st.markdown("""
                <div class="auth-patient-card-header" style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 14px; min-width: 0; flex: 1;">
                        <div style="width: 52px; height: 52px; border-radius: 16px; background: #EFF6FF; border: 1.5px solid #DBEAFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="#2563EB">
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                                <circle cx="9" cy="7" r="4"/>
                                <circle cx="18" cy="11" r="5" fill="#2563EB"/>
                                <line x1="18" y1="9" x2="18" y2="13" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"/>
                                <line x1="16" y1="11" x2="20" y2="11" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <div style="min-width: 0;">
                            <h2 class="auth-card-title" style="margin: 0; font-size: 1.45rem; font-weight: 800; color: #0F172A; line-height: 1.2;">
                                Create Patient <span style="color: #2563EB;">Account</span>
                            </h2>
                            <p class="auth-card-subtitle" style="margin: 3px 0 0 0; font-size: 0.80rem; color: #64748B; line-height: 1.4;">
                                Register to create your personal encrypted vault and manage family medical profiles.
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="#2563EB">
                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                <polyline points="7 12 10 12 11.5 8 13.5 16 15 12 17 12" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <div style="text-align: left;">
                                <div class="auth-card-title" style="font-weight: 800; font-size: 1.05rem; color: #0F172A; line-height: 1.1;">DocMindX <span style="color: #2563EB;">AI</span></div>
                                <div class="auth-card-subtitle" style="font-size: 0.62rem; color: #64748B; font-weight: 600; letter-spacing: 0.02em;">Secure Health • Smarter Tomorrow</div>
                            </div>
                        </div>
                        <div style="margin-top: 6px; font-family: 'Segoe Script', 'Comic Sans MS', cursive, sans-serif; font-size: 0.78rem; color: #93C5FD; font-weight: 700; transform: rotate(-3deg);">
                            Your Health Our Priority
                            <div style="height: 2px; background: #3B82F6; border-radius: 1px; width: 60%; margin: 2px 0 0 auto;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 1. Full Name
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>Full Name</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_fn1, c_fn2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_fn1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_fn2:
                    reg_name = st.text_input("Full Name *", key="panel_reg_name", placeholder="e.g. Your Name*", label_visibility="collapsed")
                st.markdown('<div class="auth-input-help">Enter your full name as per your valid identity.</div>', unsafe_allow_html=True)

                # 2. Email Address
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>Email Address</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_em1, c_em2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_em1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,13 2,6"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_em2:
                    reg_email = st.text_input("Email Address *", key="panel_reg_email", placeholder="you@example.com", label_visibility="collapsed")
                st.markdown("<div class='auth-input-help'>We'll send a verification code to this email.</div>", unsafe_allow_html=True)

                # 3. Date of Birth (DOB)
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                    <div class="auth-input-label" style="margin-bottom: 0;">
                        <span>Date of Birth (DOB)</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #64748B;">Min 10 Years (Clinical Protocol)</div>
                </div>
                """, unsafe_allow_html=True)
                c_dob1, c_dob2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_dob1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_dob2:
                    today_d = datetime.date.today()
                    max_d = datetime.date(today_d.year - 10, today_d.month, min(today_d.day, 28))
                    min_d = datetime.date(today_d.year - 120, 1, 1)
                    default_d = datetime.date(today_d.year - 25, today_d.month, min(today_d.day, 28))
                    reg_dob_val = st.date_input("Date of Birth *", value=default_d, min_value=min_d, max_value=max_d, key="panel_reg_dob", label_visibility="collapsed")
                
                curr_calc_age = auth_db.calculate_age_from_dob(reg_dob_val)
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 3px; margin-bottom: 8px;">
                    <div class="auth-input-help" style="margin: 0;">Used to calculate your real-time age accurately.</div>
                    <span style="font-size: 0.74rem; font-weight: 700; color: #2563EB; background: #EFF6FF; border: 1px solid #DBEAFE; padding: 2px 8px; border-radius: 12px;">
                        Age: {curr_calc_age if curr_calc_age is not None else '--'} Years (Auto-updates)
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # 4. Password
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                    <div class="auth-input-label" style="margin-bottom: 0;">
                        <span>Password</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 4px; font-size: 0.74rem; color: #64748B;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        <span>Create a strong password</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c_pw1, c_pw2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_pw1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_pw2:
                    reg_pass = st.text_input("Password *", type="password", key="panel_reg_pass", placeholder="••••••••", label_visibility="collapsed")

                # Dynamic Password Strength Meter
                _, str_label, str_color, str_bars = compute_password_strength(reg_pass)
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; margin-bottom: 8px;">
                    <div style="display: flex; gap: 6px; flex: 1; max-width: 250px;">
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[0]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[1]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[2]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[3]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[4]};"></span>
                    </div>
                    <span style="font-size: 0.74rem; font-weight: 700; color: {str_color};">{str_label}</span>
                </div>
                """, unsafe_allow_html=True)

                # 5. Confirm Password
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>Confirm Password</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_cp1, c_cp2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_cp1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_cp2:
                    reg_conf = st.text_input("Confirm Password *", type="password", key="panel_reg_conf", placeholder="••••••••", label_visibility="collapsed")
                st.markdown('<div class="auth-input-help">Re-enter the same password to confirm.</div>', unsafe_allow_html=True)

                # Password Requirements Box
                st.markdown(render_password_requirements_box(), unsafe_allow_html=True)

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                if st.button("Register & Send Activation Code →", type="primary", use_container_width=True, key="panel_btn_submit_reg"):
                    reg_dob_str = reg_dob_val.strftime("%Y-%m-%d") if reg_dob_val else ""
                    ok, msg = auth_svc.register_user(reg_name, reg_email, reg_pass, reg_conf, dob=reg_dob_str)
                    if ok:
                        st.session_state["auth_temp_email"] = reg_email.strip().lower()
                        st.session_state["auth_temp_name"] = reg_name.strip()
                        st.session_state["auth_view"] = "REGISTER_OTP"
                        st.rerun()
                    else:
                        st.error(msg)

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                if st.button("→ Already have an account? Sign In", use_container_width=True, key="panel_btn_back_to_login"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                if st.button("← Return to Clinical Dashboard", use_container_width=True, key="panel_btn_reg_return_dash"):
                    st.session_state["active_panel"] = "Health Assessment"
                    st.rerun()

                # Footer Trust Badges (Image 2)
                st.markdown("""
                <div class="auth-card-footer-trust" style="display: flex; align-items: center; justify-content: space-between; font-size: 0.72rem; color: #64748B; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                        <span>Secure & Encrypted</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>
                        </svg>
                        <span>HIPAA & WHO Compliant</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0D9488" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                        <span>Trusted Healthcare</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                        </svg>
                        <span>Better Health, Brighter Tomorrow</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 4. REGISTRATION OTP ACTIVATION VIEW
            elif view == "REGISTER_OTP":
                email = st.session_state.get("auth_temp_email", "")
                name = st.session_state.get("auth_temp_name", "")
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
                    <div style="font-weight: 700; color: #34D399; font-size: 1.0rem; margin-bottom: 4px;">Activate Your Account</div>
                    <div style="font-size: 0.84rem; color: #CBD5E1;">A single-use activation code was sent to <strong>{email}</strong>.</div>
                </div>
                """, unsafe_allow_html=True)

                reg_otp_code = st.text_input("Enter 6-Digit Activation Code", max_chars=6, key="panel_reg_otp_input", placeholder="123456")

                c_a1, c_a2 = st.columns([1, 1])
                with c_a1:
                    if st.button("Activate & Sign In", type="primary", use_container_width=True, key="panel_btn_activate_now"):
                        ok, msg = auth_svc.activate_user_account(email, reg_otp_code)
                        if ok:
                            st.success(msg)
                            st.session_state["auth_view"] = "LOGIN"
                            st.rerun()
                        else:
                            st.error(msg)
                with c_a2:
                    if st.button("Resend Activation Code", use_container_width=True, key="panel_btn_resend_reg"):
                        ok, msg = auth_svc.request_otp(email, "REGISTRATION", name)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("← Back to Registration", key="panel_btn_back_to_reg"):
                    st.session_state["auth_view"] = "REGISTER"
                    st.rerun()

            # 5. RECOVERY PASSWORD VIEW (NOT "FORGOT PASSWORD")
            elif view == "RECOVERY":
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    <div>
                        <h3 class="auth-card-title" style="margin: 0; font-size: 1.35rem; font-weight: 800; color: #0F172A;">Recovery Password</h3>
                        <p class="auth-card-subtitle" style="margin: 2px 0 0 0; font-size: 0.80rem; color: #64748B;">Enter your registered email address to receive a secure password recovery code.</p>
                    </div>
                </div>
                <div class="auth-or-divider" style="margin: 14px 0 16px 0;"><span>We'll send a verification code to your email</span></div>
                <div class="auth-input-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <span>Registered Email Address</span>
                </div>
                """, unsafe_allow_html=True)
                rec_email = st.text_input("Registered Email Address", key="panel_rec_email", placeholder="you@example.com", label_visibility="collapsed")

                st.markdown("""
                <div class="auth-info-callout">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #FFFFFF; font-weight: 800; font-size: 0.75rem;">
                        i
                    </div>
                    <div>
                        Make sure to enter the email address you used during registration. Check your inbox (and spam folder) for the recovery code.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Send Recovery Code →", type="primary", use_container_width=True, key="panel_btn_send_rec"):
                    if not rec_email:
                        st.error("Please enter your email address.")
                    else:
                        ok, msg = auth_svc.initiate_recovery_password(rec_email)
                        st.session_state["auth_temp_email"] = rec_email.strip().lower()
                        st.session_state["auth_view"] = "RECOVERY_OTP"
                        st.success(msg)
                        st.rerun()

                st.markdown('<div class="auth-or-divider"><span>OR</span></div>', unsafe_allow_html=True)

                if st.button("Back to Sign In", use_container_width=True, key="panel_btn_back_from_rec"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

                st.markdown("""
                <div class="auth-privacy-banner">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 28px; height: 28px; border-radius: 50%; background: #10B981; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div>
                            <strong style="color: #065F46; font-size: 0.82rem; display: block;">Your Privacy Matters</strong>
                            <span style="color: #047857; font-size: 0.72rem;">We follow HIPAA and WHO clinical data security guidelines.</span>
                        </div>
                    </div>
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="1.2" opacity="0.35">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                """, unsafe_allow_html=True)

            # 6. RECOVERY OTP & NEW PASSWORD VIEW
            elif view == "RECOVERY_OTP":
                email = st.session_state.get("auth_temp_email", "")

                # Header matching Image 4
                st.markdown("""
                <div class="auth-patient-card-header" style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; gap: 14px; min-width: 0; flex: 1;">
                        <div style="width: 52px; height: 52px; border-radius: 16px; background: #EFF6FF; border: 1.5px solid #DBEAFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                <path d="M12 14v4"/>
                                <path d="M10 16a2 2 0 1 0 4 0"/>
                            </svg>
                        </div>
                        <div style="min-width: 0;">
                            <h2 class="auth-card-title" style="margin: 0; font-size: 1.45rem; font-weight: 800; color: #0F172A; line-height: 1.2;">
                                Reset <span style="color: #2563EB;">Password</span>
                            </h2>
                            <p class="auth-card-subtitle" style="margin: 3px 0 0 0; font-size: 0.80rem; color: #64748B; line-height: 1.4;">
                                Enter the recovery code sent to your registered email and configure your new password.
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right; flex-shrink: 0; display: flex; align-items: center; gap: 14px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="#2563EB">
                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                <polyline points="7 12 10 12 11.5 8 13.5 16 15 12 17 12" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <div style="text-align: left;">
                                <div class="auth-card-title" style="font-weight: 800; font-size: 1.05rem; color: #0F172A; line-height: 1.1;">DocMindX <span style="color: #2563EB;">AI</span></div>
                                <div class="auth-card-subtitle" style="font-size: 0.62rem; color: #64748B; font-weight: 600; letter-spacing: 0.02em;">CLINICAL AI HEALTHCARE SYSTEM</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; border-left: 1px solid #E2E8F0; padding-left: 12px;">
                            <div style="width: 30px; height: 30px; border-radius: 8px; background: #EFF6FF; border: 1px solid #DBEAFE; display: flex; align-items: center; justify-content: center;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                    <polyline points="9 12 11 14 15 10"/>
                                </svg>
                            </div>
                            <div style="text-align: left;">
                                <div class="auth-card-title" style="font-weight: 700; font-size: 0.76rem; color: #1E293B; line-height: 1.1;">Secure & Encrypted</div>
                                <div class="auth-card-subtitle" style="font-size: 0.64rem; color: #64748B;">Your data is protected</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                dev_otp = auth_svc.get_dev_otp_fallback(email, "RECOVERY")
                dev_badge = f'<div style="margin-top: 6px; display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 6px; background: rgba(37,99,235,0.08); border: 1px dashed #93C5FD; font-size: 0.72rem; color: #1E40AF;">Testing Fallback Notice: Recovery Code is: <strong style="color: #2563EB; font-family: monospace;">{dev_otp}</strong></div>' if dev_otp else ""

                # Check Your Email card (Image 4)
                email_target_display = email if email else "your registered email"
                st.markdown(f"""
                <div class="auth-check-email-card" style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
                    <div style="display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1;">
                        <div style="width: 42px; height: 42px; border-radius: 12px; background: #DBEAFE; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                <polyline points="22,6 12,13 2,6"/>
                            </svg>
                        </div>
                        <div style="min-width: 0;">
                            <div style="font-weight: 800; font-size: 0.95rem; color: #0369A1; line-height: 1.2;">Check Your Email</div>
                            <div style="font-size: 0.78rem; color: #334155; margin: 2px 0;">
                                We have sent a 6-digit recovery code to <strong style="color: #0284C7;">{email_target_display}</strong>.
                            </div>
                            <div style="font-size: 0.72rem; color: #64748B;">
                                Didn't receive the code? Check your spam folder or request a new code.
                            </div>
                            {dev_badge}
                        </div>
                    </div>
                    <div style="flex-shrink: 0;">
                        <svg width="56" height="42" viewBox="0 0 64 48" fill="none">
                            <path d="M6 24 H18" stroke="#93C5FD" stroke-width="2" stroke-linecap="round"/>
                            <path d="M2 30 H14" stroke="#60A5FA" stroke-width="2" stroke-linecap="round"/>
                            <path d="M8 36 H16" stroke="#93C5FD" stroke-width="1.5" stroke-linecap="round"/>
                            <g transform="rotate(-8 36 24)">
                                <rect x="20" y="10" width="38" height="26" rx="4" fill="#3B82F6" stroke="#2563EB" stroke-width="1.5"/>
                                <path d="M20 12 L39 26 L58 12" stroke="#FFFFFF" stroke-width="1.8" fill="none"/>
                                <path d="M20 36 L32 23" stroke="#1D4ED8" stroke-width="1.2" opacity="0.6"/>
                                <path d="M58 36 L46 23" stroke="#1D4ED8" stroke-width="1.2" opacity="0.6"/>
                            </g>
                        </svg>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 1. 6-Digit Recovery Code
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>6-Digit Recovery Code</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_rc1, c_rc2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_rc1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 2l-2 2m-1.5 1.5L14 9a6 6 0 1 0 3 3l3.5-3.5m0 0l2 2m-2-2l2-2"/>
                            <circle cx="8" cy="16" r="3"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_rc2:
                    rec_code = st.text_input("6-Digit Recovery Code *", max_chars=6, key="panel_rec_otp_input", placeholder="Enter 6-digit code", label_visibility="collapsed")
                st.markdown('<div class="auth-input-help">e.g. 123456</div>', unsafe_allow_html=True)

                # 2. New Password
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>New Password</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_np1, c_np2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_np1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_np2:
                    rec_p1 = st.text_input("New Password *", type="password", key="panel_rec_p1", placeholder="••••••••", label_visibility="collapsed")

                # Dynamic Password Strength Meter
                _, str_label, str_color, str_bars = compute_password_strength(rec_p1)
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; margin-bottom: 8px;">
                    <div style="display: flex; gap: 6px; flex: 1; max-width: 250px;">
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[0]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[1]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[2]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[3]};"></span>
                        <span style="flex: 1; height: 5px; border-radius: 4px; background: {str_bars[4]};"></span>
                    </div>
                    <span style="font-size: 0.74rem; font-weight: 700; color: {str_color};">{str_label}</span>
                </div>
                """, unsafe_allow_html=True)

                # 3. Confirm New Password
                st.markdown("""
                <div class="auth-input-label" style="margin-bottom: 4px;">
                    <span>Confirm New Password</span> <span style="color: #EF4444; font-weight: bold;">*</span>
                </div>
                """, unsafe_allow_html=True)
                c_cn1, c_cn2 = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
                with c_cn1:
                    st.markdown("""
                    <div class="auth-input-icon-box">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                    </div>
                    """, unsafe_allow_html=True)
                with c_cn2:
                    rec_p2 = st.text_input("Confirm New Password *", type="password", key="panel_rec_p2", placeholder="••••••••", label_visibility="collapsed")
                st.markdown('<div class="auth-input-help">Re-enter the same password to confirm.</div>', unsafe_allow_html=True)

                # Password Requirements Box
                st.markdown(render_password_requirements_box(), unsafe_allow_html=True)

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                if st.button("↻ Reset Password & Save →", type="primary", use_container_width=True, key="panel_btn_finish_rec"):
                    ok, msg = auth_svc.verify_recovery_otp_and_reset_password(email, rec_code, rec_p1, rec_p2)
                    if ok:
                        st.success(msg)
                        st.session_state["auth_view"] = "LOGIN"
                        st.rerun()
                    else:
                        st.error(msg)

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                if st.button("← Cancel Recovery", use_container_width=True, key="panel_btn_cancel_rec"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

                # Footer Trust Badges (Image 4)
                st.markdown("""
                <div class="auth-card-footer-trust" style="display: flex; align-items: center; justify-content: center; gap: 14px; font-size: 0.72rem; color: #64748B; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>
                        </svg>
                        <span>HIPAA & WHO Compliant</span>
                    </div>
                    <span style="color: #CBD5E1;">|</span>
                    <span>Trusted Healthcare</span>
                    <span style="color: #CBD5E1;">|</span>
                    <span>Better Health, Brighter Tomorrow</span>
                </div>
                """, unsafe_allow_html=True)

            # 7. ADMIN LOGIN VIEW
            elif view == "ADMIN_LOGIN":
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 44px; height: 44px; border-radius: 12px; background: #FEF2F2; border: 1px solid #FECACA; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                                <circle cx="9" cy="7" r="4"/>
                                <circle cx="19" cy="11" r="2"/>
                                <path d="M19 8v1M19 13v1M17 9.5l.8.5M20.2 12l.8.5M17 12.5l.8-.5M20.2 10l.8-.5"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="auth-card-title" style="margin: 0; font-size: 1.30rem; font-weight: 800; color: #0F172A;">National Administrator Console Sign-In</h3>
                            <p class="auth-card-subtitle" style="margin: 2px 0 0 0; font-size: 0.80rem; color: #64748B;">Restricted access for certified national command center personnel.</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="#2563EB">
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            <polyline points="7 12 10 12 11.5 8 13.5 16 15 12 17 12" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <div style="text-align: left;">
                            <div class="auth-card-title" style="font-weight: 800; font-size: 1.15rem; color: #0F172A; line-height: 1.1;">DocMindX AI</div>
                            <div class="auth-card-subtitle" style="font-size: 0.65rem; color: #64748B; font-weight: 600; letter-spacing: 0.02em;">Secure Health • Smarter Tomorrow</div>
                        </div>
                    </div>
                </div>
                <div class="auth-admin-alert">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #FEE2E2; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    <div>
                        <strong style="color: #DC2626; font-size: 0.84rem; display: block;">Authorized Personnel Only</strong>
                        <span style="color: #991B1B; font-size: 0.76rem; line-height: 1.35;">This console is restricted to verified national command center administrators. All access attempts are logged and monitored.</span>
                    </div>
                </div>
                <div class="auth-input-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                    <span>Administrator Identity</span>
                </div>
                """, unsafe_allow_html=True)
                adm_email = st.text_input("Administrator Identity", placeholder="Enter administrator ID", key="panel_adm_email", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="auth-input-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>Master Password</span>
                </div>
                """, unsafe_allow_html=True)
                adm_pass = st.text_input("Master Password", type="password", key="panel_adm_pass", placeholder="Enter master password", label_visibility="collapsed")

                st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
                if st.button(
                    "**Verify Credentials & Request Admin Key →**  \nAuthenticate and proceed to secure console",
                    type="primary",
                    use_container_width=True,
                    key="panel_btn_adm_cred"
                ):
                    ok, msg = auth_svc.authenticate_admin_credentials(adm_email, adm_pass)
                    if ok:
                        st.session_state["auth_temp_email"] = adm_email.strip().lower()
                        auth_svc.send_admin_login_otp_code(adm_email)
                        st.session_state["auth_view"] = "ADMIN_OTP"
                        st.rerun()
                    else:
                        st.error(msg)

                st.markdown('<div class="auth-or-divider"><span>OR</span></div>', unsafe_allow_html=True)

                if st.button(
                    "**Regular Patient Sign In**  \nReturn to patient portal",
                    use_container_width=True,
                    key="panel_btn_back_from_adm"
                ):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

            # 8. ADMIN OTP VIEW
            elif view == "ADMIN_OTP":
                email = st.session_state.get("auth_temp_email", "docmindxai@gmail.com")
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
                    <div style="font-weight: 700; color: #F87171; font-size: 1.0rem; margin-bottom: 4px;">Admin Dual-Factor Key Verification</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1;">High-security authorization key dispatched to <strong>{email}</strong>.</div>
                </div>
                """, unsafe_allow_html=True)

                dev_otp = auth_svc.get_dev_otp_fallback(email, "ADMIN_LOGIN")
                if dev_otp:
                    st.caption(f"Testing Fallback Notice: Admin Key is: `{dev_otp}`")

                adm_otp_val = st.text_input("6-Digit Admin Key", max_chars=6, key="panel_adm_otp_val", placeholder="123456")

                c_ao1, c_ao2 = st.columns([1, 1])
                with c_ao1:
                    if st.button("Authenticate Admin Console", type="primary", use_container_width=True, key="panel_btn_adm_auth"):
                        ok, msg, session_data = auth_svc.complete_admin_login(email, adm_otp_val)
                        if ok:
                            st.session_state["user_auth"] = session_data
                            st.session_state["active_panel"] = "Admin Panel"
                            st.success("Admin access granted!")
                            st.rerun()
                        else:
                            st.error(msg)
                with c_ao2:
                    if st.button("Resend Key", use_container_width=True, key="panel_btn_resend_adm_key"):
                        ok, msg = auth_svc.send_admin_login_otp_code(email)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("← Cancel", key="panel_btn_cancel_adm"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

    if view == "RECOVERY":
        st.markdown("""
        <div style="text-align: center; margin-top: 24px; padding-top: 14px; font-size: 0.74rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.14em;">
            &mdash;&mdash;&mdash;&nbsp;&nbsp; BETTER HEALTH &bull; SAFER DATA &bull; BRIGHTER TOMORROW &nbsp;&nbsp;&mdash;&mdash;&mdash;
        </div>
        """, unsafe_allow_html=True)
