"""
DocMindX AI — Authentication & Security Full Panel Component
Provides a full-page clinical identity portal for Registration, 2FA Login,
Recovery Password, Change Password, and Administrator Authentication.
Clean, modern, glassmorphic UI with full Dark & Light mode parity,
responsive layout, Remember Me, and clean bottom navigation without clutter.
"""
import base64
import datetime
import os
import json
import streamlit as st
import streamlit.components.v1 as components

import database.auth_db as auth_db
import services.auth_service as auth_svc
from components.popup_dialog import trigger_popup, check_and_render_pending_popup


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
    if "login_remember_me_val" not in st.session_state:
        st.session_state["login_remember_me_val"] = True


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
        colors = ["#10B981" if i < score else "#334155" for i in range(5)]
        return score, "Strong Password", "#10B981", colors
    elif score >= 2:
        colors = ["#F59E0B" if i < score else "#334155" for i in range(5)]
        return score, "Moderate Password", "#F59E0B", colors
    else:
        colors = ["#EF4444" if i < 1 else "#334155" for i in range(5)]
        return score, "Weak Password", "#EF4444", colors


def render_password_requirements_box(password: str = "", is_dark: bool = False) -> str:
    """Renders clinical password requirements checklist box with live dynamic validation."""
    p = password or ""
    has_len8 = len(p) >= 8
    has_numbers = any(c.isdigit() for c in p)
    has_letters = any(c.isalpha() for c in p)
    has_special = any(not c.isalnum() for c in p)

    def _get_req_icon(passed: bool) -> str:
        if passed:
            return (
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="#10B981" stroke="none" style="flex-shrink:0;">'
                '<circle cx="12" cy="12" r="10" fill="#10B981"/>'
                '<polyline points="8 12 11 15 16 9" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                '</svg>'
            )
        else:
            border_c = "#64748B" if is_dark else "#94A3B8"
            return (
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{border_c}" stroke-width="2" style="flex-shrink:0;">'
                '<circle cx="12" cy="12" r="10"/>'
                '</svg>'
            )

    icon_len = _get_req_icon(has_len8)
    icon_num = _get_req_icon(has_numbers)
    icon_let = _get_req_icon(has_letters)
    icon_spc = _get_req_icon(has_special)

    passed_color = "#34D399" if is_dark else "#059669"
    unpassed_color = "#94A3B8" if is_dark else "#64748B"

    color_len = passed_color if has_len8 else unpassed_color
    color_num = passed_color if has_numbers else unpassed_color
    color_let = passed_color if has_letters else unpassed_color
    color_spc = passed_color if has_special else unpassed_color

    all_met = has_len8 and has_numbers and has_letters and has_special
    if is_dark:
        box_bg = "rgba(16, 185, 129, 0.12)" if all_met else "rgba(30, 41, 59, 0.65)"
        box_border = "1px solid rgba(16, 185, 129, 0.45)" if all_met else "1px solid rgba(51, 65, 85, 0.85)"
        heading_color = "#38BDF8"
    else:
        box_bg = "rgba(16, 185, 129, 0.05)" if all_met else "rgba(37, 99, 235, 0.03)"
        box_border = "1px solid rgba(16, 185, 129, 0.35)" if all_met else "1px solid rgba(219, 234, 254, 0.8)"
        heading_color = "#1E40AF"

    return f"""
    <div style="background: {box_bg}; border: {box_border}; border-radius: 12px; padding: 10px 14px; margin: 8px 0 12px 0;">
        <div style="font-weight: 700; font-size: 0.78rem; color: {heading_color}; margin-bottom: 6px;">
            Password Requirements:
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px 12px;">
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: {color_len};">
                {icon_len} <span>At least 8 chars</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: {color_num};">
                {icon_num} <span>Include numbers</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: {color_let};">
                {icon_let} <span>Include letters</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: {color_spc};">
                {icon_spc} <span>Special symbol (!@#$)</span>
            </div>
        </div>
    </div>
    """


def get_auth_hero_svg(is_dark: bool = False) -> str:
    """
    Renders the modern 3D glowing shield centerpiece on a glass pedestal.
    """
    filter_opacity = "0.28" if is_dark else "0.16"
    return f"""
    <svg viewBox="0 0 460 260" style="width: 100%; max-width: 420px; height: auto; margin: 8px auto; display: block; filter: drop-shadow(0 12px 24px rgba(37, 99, 235, {filter_opacity}));" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <radialGradient id="centerGlow" cx="50%" cy="55%" r="45%">
                <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.45"/>
                <stop offset="60%" stop-color="#2563EB" stop-opacity="0.15"/>
                <stop offset="100%" stop-color="#2563EB" stop-opacity="0"/>
            </radialGradient>
            <linearGradient id="pedestalRim" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#38BDF8"/>
                <stop offset="50%" stop-color="#60A5FA"/>
                <stop offset="100%" stop-color="#0284C7"/>
            </linearGradient>
            <linearGradient id="pedestalBase" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#0284C7"/>
                <stop offset="100%" stop-color="#0F172A"/>
            </linearGradient>
            <linearGradient id="pedestalTop" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#E0F2FE" stop-opacity="0.9"/>
                <stop offset="100%" stop-color="#7DD3FC" stop-opacity="0.7"/>
            </linearGradient>
            <linearGradient id="shieldGlass" x1="20%" y1="0%" x2="80%" y2="100%">
                <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.95"/>
                <stop offset="45%" stop-color="#2563EB" stop-opacity="0.92"/>
                <stop offset="100%" stop-color="#1D4ED8" stop-opacity="0.98"/>
            </linearGradient>
            <linearGradient id="shieldBorder" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/>
                <stop offset="40%" stop-color="#BAE6FD" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#38BDF8" stop-opacity="0.6"/>
            </linearGradient>
            <linearGradient id="shieldInnerGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.5"/>
                <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
            </linearGradient>
            <linearGradient id="badgeGlass" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.92"/>
                <stop offset="100%" stop-color="#E0F2FE" stop-opacity="0.80"/>
            </linearGradient>
            <filter id="neonShieldGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="7" result="blur1"/>
                <feGaussianBlur stdDeviation="14" result="blur2"/>
                <feMerge>
                    <feMergeNode in="blur2"/>
                    <feMergeNode in="blur1"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>            
            <filter id="badgeShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#0284C7" flood-opacity="0.22"/>
            </filter>
        </defs>
        <ellipse cx="230" cy="155" rx="145" ry="55" fill="url(#centerGlow)"/>
        <ellipse cx="230" cy="155" rx="175" ry="44" fill="none" stroke="#38BDF8" stroke-width="1.8" stroke-dasharray="6 4" opacity="0.65"/>
        <ellipse cx="230" cy="155" rx="160" ry="38" fill="none" stroke="#60A5FA" stroke-width="1" opacity="0.4"/>
        <circle cx="95" cy="135" r="3" fill="#38BDF8" opacity="0.8"/>
        <circle cx="360" cy="170" r="2.5" fill="#60A5FA" opacity="0.8"/>
        <circle cx="140" cy="185" r="2" fill="#38BDF8" opacity="0.6"/>
        <circle cx="330" cy="125" r="3.5" fill="#00E5FF" opacity="0.7"/>
        <ellipse cx="230" cy="215" rx="120" ry="24" fill="#0C4A6E" opacity="0.25"/>
        <path d="M125 200 C125 216 335 216 335 200 L335 210 C335 226 125 226 125 210 Z" fill="url(#pedestalBase)"/>
        <ellipse cx="230" cy="200" rx="105" ry="19" fill="url(#pedestalRim)"/>
        <path d="M145 188 C145 202 315 202 315 188 L315 194 C315 208 145 208 145 194 Z" fill="#0369A1"/>
        <ellipse cx="230" cy="188" rx="85" ry="15" fill="url(#pedestalTop)"/>
        <ellipse cx="230" cy="188" rx="72" ry="11" fill="#0284C7"/>
        <ellipse cx="230" cy="188" rx="66" ry="9" fill="#38BDF8" opacity="0.9"/>
        <ellipse cx="230" cy="188" rx="54" ry="7" fill="#FFFFFF" opacity="0.95"/>
        <g filter="url(#neonShieldGlow)">
            <path d="M230 45 L285 66 C285 122 258 158 230 172 C202 158 175 122 175 66 Z" 
                  fill="url(#shieldGlass)" 
                  stroke="url(#shieldBorder)" 
                  stroke-width="3.5" 
                  stroke-linejoin="round"/>
            <path d="M230 52 L278 70 C278 118 254 150 230 163 C206 150 182 118 182 70 Z" 
                  fill="none" 
                  stroke="url(#shieldInnerGlow)" 
                  stroke-width="1.8"/>
            <path d="M222 84 H238 V98 H252 V114 H238 V128 H222 V114 H208 V98 H222 Z" 
                  fill="#FFFFFF" 
                  filter="drop-shadow(0 4px 8px rgba(30, 58, 138, 0.4))"/>
        </g>
        <!-- 4 Labeled Floating Glass Badges Matching Image 2 -->
        <!-- 1. Top-Left: Health Data -->
        <g class="auth-hero-badge-1" filter="url(#badgeShadow)">
            <rect x="52" y="44" width="58" height="50" rx="14" fill="url(#badgeGlass)" stroke="#BAE6FD" stroke-width="1.4"/>
            <path d="M66 65 H72 L76 57 L81 72 L86 62 L89 65 H95" stroke="#0284C7" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
            <text x="81" y="84" text-anchor="middle" font-size="6.8" font-weight="800" fill="#0369A1" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">Health Data</text>
        </g>
        <!-- 2. Bottom-Left: Trusted Care -->
        <g class="auth-hero-badge-2" filter="url(#badgeShadow)">
            <rect x="48" y="145" width="60" height="50" rx="14" fill="url(#badgeGlass)" stroke="#BAE6FD" stroke-width="1.4"/>
            <circle cx="72" cy="162" r="3.2" fill="#0284C7"/>
            <path d="M66 174 c0 -3 2.5 -4.5 6 -4.5 s6 1.5 6 4.5" fill="#0284C7"/>
            <circle cx="82" cy="163" r="2.6" fill="#38BDF8"/>
            <path d="M78 174 c0 -2.2 1.8 -3.5 4.5 -3.5 s4.5 1.3 4.5 3.5" fill="#38BDF8"/>
            <text x="78" y="186" text-anchor="middle" font-size="6.6" font-weight="800" fill="#0369A1" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">Trusted Care</text>
        </g>
        <!-- 3. Top-Right: Privacy -->
        <g class="auth-hero-badge-3" filter="url(#badgeShadow)">
            <rect x="348" y="44" width="56" height="50" rx="14" fill="url(#badgeGlass)" stroke="#BAE6FD" stroke-width="1.4"/>
            <rect x="367" y="63" width="18" height="13" rx="3" fill="#0284C7"/>
            <path d="M371 63 V58 A5 5 0 0 1 381 58 V63" stroke="#0284C7" stroke-width="2.4" fill="none" stroke-linecap="round"/>
            <circle cx="376" cy="69.5" r="1.6" fill="#FFFFFF"/>
            <text x="376" y="84" text-anchor="middle" font-size="6.8" font-weight="800" fill="#0369A1" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">Privacy</text>
        </g>
        <!-- 4. Bottom-Right: Smart Reports -->
        <g class="auth-hero-badge-4" filter="url(#badgeShadow)">
            <rect x="345" y="145" width="64" height="50" rx="14" fill="url(#badgeGlass)" stroke="#BAE6FD" stroke-width="1.4"/>
            <path d="M369 157 h12 l4 4 v13 a2 2 0 0 1 -2 2 h-14 a2 2 0 0 1 -2 -2 v-15 a2 2 0 0 1 2 -2 z" stroke="#0284C7" stroke-width="1.8" fill="#E0F2FE" fill-opacity="0.3"/>
            <line x1="373" y1="165" x2="381" y2="165" stroke="#0284C7" stroke-width="1.8" stroke-linecap="round"/>
            <line x1="373" y1="169" x2="383" y2="169" stroke="#0284C7" stroke-width="1.8" stroke-linecap="round"/>
            <text x="377" y="186" text-anchor="middle" font-size="6.4" font-weight="800" fill="#0369A1" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">Smart Reports</text>
        </g>
    </svg>
    """


def render_auth_left_hero(view: str, T: dict = None, lang_code: str = "en", is_dark: bool = False) -> str:
    """
    Renders the unified, uncluttered Left Hero Showcase.
    Clean typography, 3 trust badges, 3D glowing shield centerpiece, and trust quote.
    """
    T = T or {}

    # View-specific contextual titles, typewriter dynamic words, and badges
    if view in ("REGISTER", "REGISTER_OTP"):
        h_prefix = "Create Your Encrypted"
        h_words = ["Patient Vault", "Clinical ID", "Health Locker", "Digital Records"]
        accent_color = "#38BDF8" if is_dark else "#2563EB"
        h_sub = "Join DocMindX AI to manage verified clinical records, track diagnostics, and protect your family health with hospital-grade security."
        pills = [
            ("Vault", "Protected", "#10B981", "check"),
            ("HIPAA / WHO", "Compliant", "#2563EB", "doc"),
            ("Encrypted", "End-to-End", "#7C3AED", "lock"),
        ]
    elif view in ("RECOVERY", "RECOVERY_OTP"):
        h_prefix = "Recover Your Secure"
        h_words = ["Account Access", "Health Credentials", "Patient Vault"]
        accent_color = "#38BDF8" if is_dark else "#2563EB"
        h_sub = "Regain access to your health vault with verified cryptographic password recovery protocols."
        pills = [
            ("Safe", "Recovery", "#10B981", "check"),
            ("Zero", "Plaintext", "#2563EB", "doc"),
            ("Encrypted", "End-to-End", "#7C3AED", "lock"),
        ]
    elif view in ("ADMIN_LOGIN", "ADMIN_OTP"):
        h_prefix = "National Command"
        h_words = ["Security Console", "Oversight Portal", "Clinical Intelligence"]
        accent_color = "#F87171" if is_dark else "#EF4444"
        h_sub = "Restricted access for certified National Healthcare Command administrators and oversight officers. All actions are audited."
        pills = [
            ("Admin", "Restricted", "#EF4444", "lock"),
            ("Audited", "Sessions", "#2563EB", "doc"),
            ("TLS 1.3", "Strict", "#10B981", "check"),
        ]
    else:  # LOGIN or LOGIN_OTP
        h_prefix = "Secure Access to Your"
        h_words = ["Health Records", "Clinical Vault", "Medical Data", "Diagnostic Reports", "Patient Care"]
        accent_color = "#38BDF8" if is_dark else "#2563EB"
        h_sub = "Your health data, fully protected with enterprise-grade clinical security, patient privacy, and AI-powered care."
        pills = [
            ("2FA", "Secure Login", "#10B981", "check"),
            ("HIPAA / WHO", "Compliant", "#2563EB", "doc"),
            ("Encrypted", "End-to-End", "#7C3AED", "lock"),
        ]

    def _render_pill_icon(ptype: str, pcolor: str) -> str:
        if ptype == "check":
            return f'<svg width="15" height="15" viewBox="0 0 24 24" fill="{pcolor}"><circle cx="12" cy="12" r="10"/><path d="M8 12l2.5 2.5L16 9" stroke="#FFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'
        elif ptype == "lock":
            return f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{pcolor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
        else:
            return f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{pcolor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'

    pills_html = "".join([
        f"""
        <div class="auth-hero-pill">
            {_render_pill_icon(p[3], p[2])}
            <div>
                <span class="auth-hero-pill-title">{p[0]}</span>
                <span class="auth-hero-pill-sub">{p[1]}</span>
            </div>
        </div>
        """
        for p in pills
    ])

    title_color = "#F8FAFC" if is_dark else "#0F172A"
    sub_color = "#94A3B8" if is_dark else "#475569"
    hero_svg_html = get_auth_hero_svg(is_dark)

    words_js_array = "[" + ", ".join(f"'{w}'" for w in h_words) + "]"
    first_word = h_words[0]

    hero_markup = f"""<div class="auth-left-hero-panel">
    <div class="auth-priority-badge">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#DB2777" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
        <span><strong style="color: #DB2777;">Your Health,</strong> <span style="color: #9333EA;">Our Priority</span></span>
    </div>
    <h1 style="font-size: 2.35rem; font-weight: 900; line-height: 1.18; color: {title_color}; margin: 0 0 12px 0; letter-spacing: -0.03em; min-height: 2.4em;">
        {h_prefix} <br/>
        <span id="auth-typewriter-dynamic" class="auth-tw-accent">{first_word}</span><span id="auth-typewriter-cursor" class="auth-tw-cursor">|</span>
    </h1>
    <p style="font-size: 0.90rem; color: {sub_color}; line-height: 1.55; margin: 0 0 16px 0; max-width: 480px;">{h_sub}</p>
    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">{pills_html}</div>
    {hero_svg_html}
    <div class="auth-hero-quote-card">
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <span style="font-size: 1.5rem; color: #2563EB; line-height: 1; font-weight: 900; font-family: Georgia, serif;">&ldquo;</span>
            <div style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); line-height: 1.5; font-style: italic;">
                Trusted by patients and clinical teams worldwide to keep diagnostic records encrypted, private, and immediately accessible.
            </div>
            <span style="font-size: 1.5rem; color: #2563EB; line-height: 1; font-weight: 900; font-family: Georgia, serif;">&rdquo;</span>
        </div>
    </div>
</div>"""
    return "\n".join(line.strip() for line in hero_markup.splitlines() if line.strip())


def render_auth_bottom_nav(current_mode: str):
    """
    Renders clean, modern navigation buttons at the bottom of the card matching Image 2.
    The currently open page's button is never shown.
    """
    modes = [
        ("LOGIN", "Sign In"),
        ("REGISTER", "Register"),
        ("RECOVERY", "Recovery"),
        ("ADMIN", "Admin"),
    ]
    # Filter out current active mode
    visible_modes = [m for m in modes if m[0] != current_mode]

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="auth-or-divider"><span>OR GO TO</span></div>', unsafe_allow_html=True)

    cols = st.columns(len(visible_modes), gap="small")
    for idx, (m_key, m_label) in enumerate(visible_modes):
        with cols[idx]:
            btn_key = f"auth_nav_dest_{m_key.lower()}"
            if st.button(m_label, key=btn_key, use_container_width=True):
                if m_key == "LOGIN":
                    st.session_state["auth_view"] = "LOGIN"
                elif m_key == "REGISTER":
                    st.session_state["auth_view"] = "REGISTER"
                elif m_key == "RECOVERY":
                    st.session_state["auth_view"] = "RECOVERY"
                elif m_key == "ADMIN":
                    st.session_state["auth_view"] = "ADMIN_LOGIN"
                st.rerun()


def render_auth_portal_panel(T: dict = None, lang_code: str = "en", LANG_OPTIONS: list = None, sync_language=None):
    """
    Renders the dedicated modern Authentication & Clinical Identity Panel.
    Fully implements clean, minimal, glassmorphic UI with Dark & Light mode parity,
    clean bottom navigation without emojis, and uncluttered layout.
    """
    init_auth_session_state()
    check_and_render_pending_popup()
    T = T or {}
    LANG_OPTIONS = LANG_OPTIONS or ["English", "हिन्दी (Hindi)", "ગુજરાતી (Gujarati)"]
    is_dark = bool(st.session_state.get("dark_mode", False))

    # Redirect already logged-in users directly to their designated panel
    curr_user = get_current_user()
    if curr_user and is_authenticated():
        if auth_svc.is_admin_session(curr_user):
            st.session_state["active_panel"] = "Admin Panel"
        else:
            st.session_state["active_panel"] = "Family Management"
        st.rerun()

    # Dynamic error highlight rules for empty required fields
    err_rules = []
    if st.session_state.get("auth_err_email"):
        err_rules.append("div.st-key-panel_login_email div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_pass"):
        err_rules.append("div.st-key-panel_login_password div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_reg_name"):
        err_rules.append("div.st-key-panel_reg_name div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_reg_email"):
        err_rules.append("div.st-key-panel_reg_email div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_reg_pass"):
        err_rules.append("div.st-key-panel_reg_pass div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_reg_conf"):
        err_rules.append("div.st-key-panel_reg_conf div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_rec_email"):
        err_rules.append("div.st-key-panel_rec_email div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_adm_email"):
        err_rules.append("div.st-key-panel_adm_email div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    if st.session_state.get("auth_err_adm_pass"):
        err_rules.append("div.st-key-panel_adm_pass div[data-baseweb='input'] { border: 1.8px solid #EF4444 !important; box-shadow: 0 0 0 3.5px rgba(239, 68, 68, 0.25) !important; }")
    err_css_str = "\n".join(err_rules)

    # Inject Glassmorphism, Focus Animations, and Dark/Light Mode Styles
    st.markdown(f"""
    <style>
    {err_css_str}
    /* Prevent native password reveal icon clashes */
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {{
        display: none !important;
    }}

    /* Hide floating AI assistant and pill buttons on Auth page */
    .st-key-floating_ai_assistant,
    .st-key-floating_chat_pill {{
        display: none !important;
    }}

    /* Left Hero Panel */
    .auth-left-hero-panel {{
        padding: 10px 14px 10px 4px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }}

    /* Hero Trust Pills */
    .auth-hero-pill {{
        background: {'#111D3D' if is_dark else '#FFFFFF'};
        border: 1px solid {'#1E2E4E' if is_dark else '#E2E8F0'};
        border-radius: 12px;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }}
    .auth-hero-pill:hover {{
        transform: translateY(-2px);
    }}
    .auth-hero-pill-title {{
        font-size: 0.74rem;
        font-weight: 800;
        color: {'#F8FAFC' if is_dark else '#1E293B'};
        display: block;
        line-height: 1.15;
    }}
    .auth-hero-pill-sub {{
        font-size: 0.68rem;
        color: {'#94A3B8' if is_dark else '#64748B'};
        display: block;
        line-height: 1.15;
    }}

    /* Bottom Quote Card */
    .auth-hero-quote-card {{
        background: {'rgba(17, 29, 61, 0.75)' if is_dark else 'rgba(255, 255, 255, 0.85)'};
        backdrop-filter: blur(16px);
        border: 1px solid {'#1E2E4E' if is_dark else 'rgba(226, 232, 240, 0.95)'};
        border-radius: 14px;
        padding: 12px 18px;
        margin-top: 14px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }}

    /* Background mesh & subtle dot grid matching Image 2 */
    [data-testid="stAppViewContainer"] {{
        background-color: {'#0B1120' if is_dark else '#F8FAFC'} !important;
        background-image: 
            radial-gradient(circle at 12% 18%, {'rgba(30, 58, 138, 0.35)' if is_dark else 'rgba(219, 234, 254, 0.70)'} 0%, transparent 45%),
            radial-gradient(circle at 88% 22%, {'rgba(67, 56, 202, 0.25)' if is_dark else 'rgba(238, 242, 255, 0.75)'} 0%, transparent 45%),
            radial-gradient(circle at 50% 85%, {'rgba(14, 116, 144, 0.25)' if is_dark else 'rgba(224, 242, 254, 0.60)'} 0%, transparent 50%),
            radial-gradient({'#334155' if is_dark else '#CBD5E1'} 1px, transparent 1px) !important;
        background-size: 100% 100%, 100% 100%, 100% 100%, 24px 24px !important;
    }}

    /* Top Priority Badge Pill */
    .auth-priority-badge {{
        background: {'rgba(219, 39, 119, 0.12)' if is_dark else '#FDF2F8'};
        border: 1px solid {'rgba(244, 114, 182, 0.30)' if is_dark else '#FCE7F3'};
        border-radius: 9999px;
        padding: 5px 14px;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.78rem;
        box-shadow: 0 2px 6px rgba(219, 39, 119, 0.06);
        margin-bottom: 12px;
        width: fit-content;
    }}

    /* Typewriter Heading Two-Tone Gradient matching Image 2 */
    .auth-tw-accent {{
        background: {'linear-gradient(135deg, #38BDF8 0%, #2DD4BF 100%)' if is_dark else 'linear-gradient(135deg, #1D4ED8 0%, #06B6D4 100%)'};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        font-weight: 900;
    }}

    /* Typewriter Blinking Cursor */
    .auth-tw-cursor {{
        display: inline-block;
        color: #06B6D4;
        font-weight: 900;
        margin-left: 2px;
        animation: authTwCursorBlink 0.8s infinite;
    }}
    @keyframes authTwCursorBlink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0; }}
    }}

    /* Floating Badges Keyframes in SVG */
    @keyframes badgeFloat1 {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-4px); }}
    }}
    @keyframes badgeFloat2 {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(4px); }}
    }}
    .auth-hero-badge-1, .auth-hero-badge-4 {{
        animation: badgeFloat1 3.5s ease-in-out infinite;
    }}
    .auth-hero-badge-2, .auth-hero-badge-3 {{
        animation: badgeFloat2 3.8s ease-in-out infinite;
    }}

    /* Right Auth Form Transparent Card as requested */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-center-icon-badge),
    .st-key-auth_right_main_card,
    .st-key-auth_right_main_card [data-testid="stVerticalBlockBorderWrapper"] {{
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border-radius: 28px !important;
        border: none !important;
        box-shadow: none !important;
        padding: 24px 32px !important;
        width: 100% !important;
        max-width: 100% !important;
        transition: all 0.3s ease !important;
    }}

    /* Center Icon Box at Top of Card matching Image 2 */
    .auth-center-icon-badge {{
        width: 56px;
        height: 56px;
        border-radius: 18px;
        background: {'rgba(37, 99, 235, 0.15)' if is_dark else '#EFF6FF'};
        border: 1.5px solid {'rgba(56, 189, 248, 0.35)' if is_dark else '#DBEAFE'};
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 14px auto;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.12);
        flex-shrink: 0;
    }}
    .auth-center-icon-badge svg {{
        display: block;
        margin: 0 auto;
        flex-shrink: 0;
    }}

    /* Form Title & Subtitle */
    .auth-form-title {{
        font-size: 1.65rem;
        font-weight: 800;
        color: {'#F8FAFC' if is_dark else '#0F172A'};
        text-align: center;
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
    }}
    .auth-form-sub {{
        font-size: 0.82rem;
        color: {'#94A3B8' if is_dark else '#64748B'};
        text-align: center;
        margin: 0 auto 20px auto;
        max-width: 480px;
        line-height: 1.45;
    }}

    /* Input Field Labels */
    .auth-clean-label {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        color: {'#E2E8F0' if is_dark else '#1E293B'};
        margin-bottom: 5px;
        margin-top: 6px;
    }}
    .auth-clean-label svg {{
        color: #2563EB;
        stroke: #2563EB;
    }}

    /* Fix: Remove any double border, outline, or square box on inner input */
    div[class*="st-key-panel_"] input,
    div[class*="st-key-panel_"] input:focus,
    div[class*="st-key-panel_"] input:active,
    div[class*="st-key-panel_"] div[data-baseweb="base-input"],
    div[class*="st-key-panel_"] div[data-baseweb="input"] input,
    div[class*="st-key-panel_"] div[data-baseweb="base-input"] input {{
        border: none !important;
        border-width: 0 !important;
        border-style: none !important;
        outline: none !important;
        outline-width: 0 !important;
        -webkit-appearance: none !important;
        box-shadow: none !important;
        background: transparent !important;
        background-color: transparent !important;
        border-radius: 12px !important;
        padding: 9px 14px !important;
        color: {'#F8FAFC' if is_dark else '#0F172A'} !important;
        font-size: 0.90rem !important;
        width: 100% !important;
    }}
    /* Trailing button (e.g. eye icon for password) */
    div[class*="st-key-panel_"] div[data-baseweb="input"] > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    /* Single clean outer rounded border */
    div[class*="st-key-panel_"] div[data-baseweb="input"] {{
        background: {'#141D2E' if is_dark else '#FFFFFF'} !important;
        border: 1.4px solid {'#1E293B' if is_dark else '#E2E8F0'} !important;
        border-radius: 12px !important;
        padding: 0 !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        overflow: hidden !important;
    }}
    /* Single clean active blue focus border on outer container */
    div[class*="st-key-panel_"] div[data-baseweb="input"]:focus-within {{
        border: 1.5px solid #2563EB !important;
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.20) !important;
    }}
    div[class*="st-key-panel_"] input::placeholder {{
        color: {'#64748B' if is_dark else '#94A3B8'} !important;
    }}

    /* "Forgot Password?" Right-Aligned Link Button */
    .st-key-btn_login_forgot_pwd button {{
        background: transparent !important;
        border: none !important;
        color: #2563EB !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0 !important;
        min-height: auto !important;
        height: auto !important;
        box-shadow: none !important;
        text-align: right !important;
        justify-content: flex-end !important;
        margin: 0 !important;
    }}
    .st-key-btn_login_forgot_pwd button:hover {{
        text-decoration: underline !important;
        color: #38BDF8 !important;
        background: transparent !important;
    }}

    /* OR Divider Line */
    .auth-or-divider {{
        display: flex;
        align-items: center;
        margin: 18px 0;
        text-align: center;
    }}
    .auth-or-divider::before,
    .auth-or-divider::after {{
        content: "";
        flex: 1;
        border-bottom: 1px solid {'#1E293B' if is_dark else '#E2E8F0'};
    }}
    .auth-or-divider span {{
        padding: 0 12px;
        font-size: 0.72rem;
        font-weight: 700;
        color: {'#64748B' if is_dark else '#94A3B8'};
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    /* Primary CTA buttons matching Image 2 */
    .st-key-panel_btn_login_submit button,
    .st-key-panel_btn_verify_login button,
    .st-key-panel_btn_submit_reg button,
    .st-key-panel_btn_activate_now button,
    .st-key-panel_btn_send_rec button,
    .st-key-panel_btn_finish_rec button,
    .st-key-panel_btn_adm_cred button,
    .st-key-panel_btn_adm_auth button {{
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        font-size: 0.94rem !important;
        font-weight: 700 !important;
        padding: 13px 24px !important;
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        justify-content: center !important;
        text-align: center !important;
    }}
    /* Circular White Arrow Badge removed as per user instruction */
    .st-key-panel_btn_login_submit button::after {{
        display: none !important;
        content: none !important;
        width: 0 !important;
        height: 0 !important;
    }}
    /* Strictly remove any pseudo-element shield icon */
    .st-key-panel_btn_login_submit button::before,
    div.st-key-panel_btn_login_submit button::before,
    .st-key-panel_btn_verify_login button::before,
    .st-key-panel_btn_submit_reg button::before,
    .st-key-panel_btn_activate_now button::before,
    .st-key-panel_btn_send_rec button::before,
    .st-key-panel_btn_finish_rec button::before,
    .st-key-panel_btn_adm_cred button::before,
    .st-key-panel_btn_adm_auth button::before {{
        display: none !important;
        content: none !important;
        background-image: none !important;
        width: 0 !important;
        height: 0 !important;
    }}
    div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] {{
        margin-left: 0 !important;
        padding-left: 0 !important;
        text-align: center !important;
        width: 100% !important;
    }}
    div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] p {{
        align-items: center !important;
        text-align: center !important;
    }}
    .st-key-panel_btn_adm_cred button,
    .st-key-panel_btn_adm_auth button {{
        background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%) !important;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.35) !important;
    }}
    .st-key-panel_btn_login_submit button:hover,
    .st-key-panel_btn_verify_login button:hover,
    .st-key-panel_btn_submit_reg button:hover,
    .st-key-panel_btn_activate_now button:hover,
    .st-key-panel_btn_send_rec button:hover,
    .st-key-panel_btn_finish_rec button:hover {{
        background: linear-gradient(135deg, #0284C7 0%, #1D4ED8 50%, #1E40AF 100%) !important;
        box-shadow: 0 10px 28px rgba(37, 99, 235, 0.45) !important;
        transform: translateY(-1px);
    }}
    .st-key-panel_btn_adm_cred button:hover,
    .st-key-panel_btn_adm_auth button:hover {{
        background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%) !important;
        box-shadow: 0 10px 28px rgba(239, 68, 68, 0.45) !important;
        transform: translateY(-1px);
    }}

    /* Bottom Navigation Buttons matching Image 2 */
    div[class*="st-key-auth_nav_dest_"] button {{
        background: {'#141D2E' if is_dark else '#FFFFFF'} !important;
        border: 1.2px solid {'#283347' if is_dark else '#E2E8F0'} !important;
        color: {'#F8FAFC' if is_dark else '#1E293B'} !important;
        border-radius: 12px !important;
        font-size: 0.84rem !important;
        font-weight: 700 !important;
        padding: 9px 14px !important;
        min-height: 42px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 7px !important;
    }}
    div[class*="st-key-auth_nav_dest_"] button p {{
        color: {'#F8FAFC' if is_dark else '#1E293B'} !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }}
    div[class*="st-key-auth_nav_dest_"] button:hover p {{
        color: #2563EB !important;
    }}
    div[class*="st-key-auth_nav_dest_"] button:hover {{
        border-color: #2563EB !important;
        color: #2563EB !important;
        background: {'rgba(37, 99, 235, 0.15)' if is_dark else '#EFF6FF'} !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
    }}
    div[class*="st-key-auth_nav_dest_"] button::before {{
        display: inline-block !important;
        width: 15px !important;
        height: 15px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        content: "" !important;
        flex-shrink: 0 !important;
    }}
    /* Vector user-plus icon for Register */
    div.st-key-auth_nav_dest_register button::before {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='9' cy='7' r='4'/%3E%3Cline x1='19' y1='8' x2='19' y2='14'/%3E%3Cline x1='16' y1='11' x2='22' y2='11'/%3E%3C/svg%3E") !important;
    }}
    /* Vector refresh-cw icon for Recovery */
    div.st-key-auth_nav_dest_recovery button::before {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67'/%3E%3C/svg%3E") !important;
    }}
    /* Vector settings/cog icon for Admin */
    div.st-key-auth_nav_dest_admin button::before {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
    }}
    /* Vector log-in icon for Sign In */
    div.st-key-auth_nav_dest_login button::before {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4'/%3E%3Cpolyline points='10 17 15 12 10 7'/%3E%3Cline x1='15' y1='12' x2='3' y2='12'/%3E%3C/svg%3E") !important;
    }}

    /* Footer TLS Notice */
    .auth-card-footer {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 20px;
        padding-top: 14px;
        border-top: 1px solid {'#1E293B' if is_dark else '#F1F5F9'};
        font-size: 0.74rem;
        color: {'#94A3B8' if is_dark else '#64748B'};
    }}

    /* Responsive Mobile Media Queries */
    @media (max-width: 768px) {{
        .auth-left-hero-panel {{
            padding: 8px 0 !important;
            margin-bottom: 20px !important;
        }}
        .auth-hero-pill {{
            padding: 4px 8px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-center-icon-badge),
        .st-key-auth_right_main_card [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 22px 18px !important;
            border-radius: 20px !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

    view = st.session_state.get("auth_view", "LOGIN")

    # 2-Column Split Layout: balanced left hero & right login card matching Image 2
    left_col, right_col = st.columns([0.98, 1.02], gap="large")

    with left_col:
        st.markdown(render_auth_left_hero(view=view, T=T, lang_code=lang_code, is_dark=is_dark), unsafe_allow_html=True)

        # Dynamic Typewriter Animation matching Image 2
        if view in ("REGISTER", "REGISTER_OTP"):
            tw_words = ["Patient Vault", "Clinical ID", "Health Locker", "Digital Records"]
        elif view in ("RECOVERY", "RECOVERY_OTP"):
            tw_words = ["Account Access", "Health Credentials", "Patient Vault"]
        elif view in ("ADMIN_LOGIN", "ADMIN_OTP"):
            tw_words = ["Security Console", "Oversight Portal", "Clinical Intelligence"]
        else:
            tw_words = ["Health Records", "Clinical Vault", "Medical Data", "Patient Care"]

        tw_script = f"""
        <script>
        (function() {{
            const words = {json.dumps(tw_words)};
            function startTypewriter() {{
                try {{
                    const doc = window.parent.document;
                    const el = doc.getElementById('auth-typewriter-dynamic');
                    if (!el) {{
                        setTimeout(startTypewriter, 120);
                        return;
                    }}
                    if (window.parent.__auth_tw_timer) {{
                        clearTimeout(window.parent.__auth_tw_timer);
                    }}

                    let wordIdx = 0;
                    let charIdx = el.textContent ? el.textContent.length : words[0].length;
                    let isDeleting = true;

                    function tick() {{
                        const currentEl = doc.getElementById('auth-typewriter-dynamic');
                        if (!currentEl) return;

                        const word = words[wordIdx];
                        if (isDeleting) {{
                            charIdx--;
                            currentEl.textContent = word.substring(0, charIdx);
                        }} else {{
                            charIdx++;
                            currentEl.textContent = word.substring(0, charIdx);
                        }}

                        let delay = isDeleting ? 45 : 85;
                        if (!isDeleting && charIdx === word.length) {{
                            delay = 2300;
                            isDeleting = true;
                        }} else if (isDeleting && charIdx === 0) {{
                            isDeleting = false;
                            wordIdx = (wordIdx + 1) % words.length;
                            delay = 350;
                        }}

                        window.parent.__auth_tw_timer = setTimeout(tick, delay);
                    }}

                    window.parent.__auth_tw_timer = setTimeout(tick, 2200);
                }} catch (e) {{
                    console.error("Typewriter error:", e);
                }}
            }}

            function setupFocusNormalizers() {{ 
                try {{
                    const doc = window.parent.document;
                    const inputs = doc.querySelectorAll('input');
                    inputs.forEach(inp => {{
                        if (!inp.__normListenerAttached) {{
                            inp.__normListenerAttached = true;
                            const normalize = () => {{
                                const wrap = inp.closest('div[data-baseweb="input"]');
                                if (wrap) {{
                                    wrap.style.setProperty('border-color', '#2563EB', 'important');
                                    wrap.style.setProperty('box-shadow', '0 0 0 3.5px rgba(37, 99, 235, 0.20)', 'important');
                                }}
                                inp.style.setProperty('border', 'none', 'important');
                                inp.style.setProperty('outline', 'none', 'important');
                                inp.style.setProperty('box-shadow', 'none', 'important');
                            }};
                            inp.addEventListener('focus', normalize);
                            inp.addEventListener('click', normalize);
                            inp.addEventListener('input', () => {{
                                const wrap = inp.closest('div[data-baseweb="input"]') || inp;
                                wrap.style.removeProperty('border-color');
                                wrap.style.removeProperty('box-shadow');
                            }});
                        }}
                    }});
                }} catch (e) {{}}
            }}

            if (document.readyState === 'complete') {{
                startTypewriter();
                setupFocusNormalizers();
            }} else {{
                window.addEventListener('load', () => {{
                    startTypewriter();
                    setupFocusNormalizers();
                }});
            }}
            setTimeout(setupFocusNormalizers, 200);
            setTimeout(setupFocusNormalizers, 600);
        }})();
        </script>
        """
        components.html(tw_script, height=0)

    with right_col:
        with st.container(key="auth_right_main_card", border=False):

            # -------------------------------------------------------------
            # VIEW 1: PATIENT SIGN IN (LOGIN)
            # -------------------------------------------------------------
            if view == "LOGIN":
                st.markdown("""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                    </svg>
                </div>
                <div class="auth-form-title">Patient <span style="color: #2563EB;">Sign In</span></div>
                <div class="auth-form-sub">Enter your verified email and password to access your health vault securely.</div>
                """, unsafe_allow_html=True)

                # Email Field
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <span>Registered Email Address</span>
                </div>
                """, unsafe_allow_html=True)
                login_email = st.text_input("Registered Email Address", key="panel_login_email", placeholder="you@example.com", label_visibility="collapsed")

                # Password Field
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>Account Password</span>
                </div>
                """, unsafe_allow_html=True)
                login_password = st.text_input("Account Password", type="password", key="panel_login_password", placeholder="••••••••", label_visibility="collapsed")

                # Remember Me & Forgot Password Row
                r_c1, r_c2 = st.columns([0.60, 0.40])
                with r_c1:
                    st.checkbox("Remember me on this device", key="login_remember_me_val", value=st.session_state.get("login_remember_me_val", True))
                with r_c2:
                    if st.button("Recover Password?", key="btn_login_forgot_pwd", use_container_width=True):
                        st.session_state["auth_view"] = "RECOVERY"
                        st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                # Primary CTA: Continue to 2FA Code
                btn_c2fa = f"**{T.get('auth_btn_continue_2fa', 'Continue to 2FA Code →')}**  \n{T.get('auth_btn_continue_2fa_sub', 'Get verification code on your email')}"
                if st.button(btn_c2fa, type="primary", use_container_width=True, key="panel_btn_login_submit"):
                    clean_email = login_email.strip() if login_email else ""
                    clean_pass = login_password.strip() if login_password else ""
                    if not clean_email or not clean_pass:
                        st.session_state["auth_err_email"] = not bool(clean_email)
                        st.session_state["auth_err_pass"] = not bool(clean_pass)
                        trigger_popup("Credentials Required", "Please enter both your registered email address and account password.", "warning")
                        st.rerun()
                    else:
                        st.session_state.pop("auth_err_email", None)
                        st.session_state.pop("auth_err_pass", None)
                        with st.spinner("Verifying credentials & preparing 2FA token..."):
                            ok, msg, user = auth_svc.authenticate_credentials(clean_email, clean_pass)
                        if ok:
                            st.session_state["auth_temp_email"] = clean_email.lower()
                            st.session_state["auth_temp_name"] = user.get("full_name", "")
                            auth_svc.send_login_verification_code(clean_email)
                            trigger_popup(
                                "Credentials Verified",
                                f"Welcome back, {user.get('full_name', '')}! A 6-digit cryptographic verification code has been dispatched to {clean_email}.",
                                "success"
                            )
                            st.session_state["auth_view"] = "LOGIN_OTP"
                            st.rerun()
                        else:
                            if user and user.get("pending_activation"):
                                trigger_popup(
                                    "Account Pending Activation",
                                    msg or "Your account requires email verification code before signing in.",
                                    "warning"
                                )
                                st.session_state["auth_temp_email"] = clean_email
                                st.session_state["auth_view"] = "REGISTER_OTP"
                                st.rerun()
                            else:
                                trigger_popup(
                                    "Login Failed",
                                    msg or "Invalid email or password. Please verify your credentials and try again.",
                                    "error"
                                )
                                st.rerun()

                # Clean Bottom Navigation (No emojis, hides current view)
                render_auth_bottom_nav("LOGIN")

                # Footer TLS notice (without shield)
                st.markdown("""
                <div class="auth-card-footer">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                        <span>Encrypted with TLS 1.3 & AES-256 Patient Data Isolation</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # -------------------------------------------------------------
            # VIEW 2: LOGIN 2FA OTP VERIFICATION
            # -------------------------------------------------------------
            elif view == "LOGIN_OTP":
                email = st.session_state.get("auth_temp_email", "")
                st.markdown(f"""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <div class="auth-form-title">Two-Factor Authentication</div>
                <div class="auth-form-sub">Enter the 6-digit cryptographic verification code sent to <strong>{email}</strong>.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>6-Digit Verification Code</span>
                </div>
                """, unsafe_allow_html=True)
                otp_input = st.text_input("6-Digit Code", max_chars=6, key="panel_login_otp_input", placeholder="123456", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Verify Code & Complete Sign In →", type="primary", use_container_width=True, key="panel_btn_verify_login"):
                    if not otp_input or len(otp_input.strip()) < 6:
                        trigger_popup("Verification Code Required", "Please enter the complete 6-digit verification code.", "warning")
                        st.rerun()
                    else:
                        with st.spinner("Validating 2FA token..."):
                            ok, msg, session_data = auth_svc.complete_login_with_otp(email, otp_input)
                        if ok:
                            st.session_state["user_auth"] = session_data
                            if auth_svc.is_admin_session(session_data):
                                st.session_state["active_panel"] = "Admin Panel"
                            else:
                                st.session_state["active_panel"] = "Family Management"
                            st.session_state["auth_view"] = "LOGIN"
                            trigger_popup("Login Successful", f"Welcome back, {session_data.get('full_name', 'Patient')}! You have signed in successfully.", "success")
                            st.rerun()
                        else:
                            trigger_popup("Login Failed", msg or "Invalid or expired verification code. Please try again.", "error")
                            st.rerun()

                st.markdown('<div class="auth-or-divider"><span>OPTIONS</span></div>', unsafe_allow_html=True)

                if st.button("Resend Verification Code", use_container_width=True, key="panel_btn_resend_login"):
                    ok, msg = auth_svc.send_login_verification_code(email)
                    if ok:
                        trigger_popup("Code Dispatched", msg or "A new verification code has been dispatched to your email.", "success")
                        st.rerun()
                    else:
                        trigger_popup("Dispatch Failed", msg or "Could not resend verification code. Please try again shortly.", "warning")
                        st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("Back to Sign In", key="panel_btn_back_from_otp", use_container_width=True):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

            # -------------------------------------------------------------
            # VIEW 3: CREATE PATIENT ACCOUNT (REGISTER)
            # -------------------------------------------------------------
            elif view == "REGISTER":
                st.markdown("""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <line x1="19" y1="8" x2="19" y2="14"/>
                        <line x1="16" y1="11" x2="22" y2="11"/>
                    </svg>
                </div>
                <div class="auth-form-title">Create Patient Account</div>
                <div class="auth-form-sub">Register to create your personal encrypted vault and manage verified clinical records.</div>
                """, unsafe_allow_html=True)

                # Full Name
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <span>Full Legal Name</span>
                </div>
                """, unsafe_allow_html=True)
                reg_name = st.text_input("Full Name", key="panel_reg_name", placeholder="e.g. Rahul Sharma", label_visibility="collapsed")

                # Email Address
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    <span>Email Address</span>
                </div>
                """, unsafe_allow_html=True)
                reg_email = st.text_input("Email Address", key="panel_reg_email", placeholder="you@example.com", label_visibility="collapsed")

                # DOB
                today_d = datetime.date.today()
                max_d = datetime.date(today_d.year - 10, today_d.month, min(today_d.day, 28))
                min_d = datetime.date(today_d.year - 120, 1, 1)
                default_d = datetime.date(today_d.year - 25, today_d.month, min(today_d.day, 28))

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    <span>Date of Birth (DOB)</span>
                </div>
                """, unsafe_allow_html=True)
                reg_dob_val = st.date_input("Date of Birth", value=default_d, min_value=min_d, max_value=max_d, key="panel_reg_dob", label_visibility="collapsed")

                # Password
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>Password</span>
                </div>
                """, unsafe_allow_html=True)
                reg_pass = st.text_input("Password", type="password", key="panel_reg_pass", placeholder="••••••••", label_visibility="collapsed")

                # Live Strength Bar
                _, str_label, str_color, str_bars = compute_password_strength(reg_pass)
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px; margin-bottom: 6px;">
                    <div style="display: flex; gap: 4px; flex: 1; max-width: 220px;">
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[0]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[1]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[2]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[3]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[4]};"></span>
                    </div>
                    <span style="font-size: 0.72rem; font-weight: 700; color: {str_color};">{str_label}</span>
                </div>
                """, unsafe_allow_html=True)

                # Confirm Password
                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>Confirm Password</span>
                </div>
                """, unsafe_allow_html=True)
                reg_conf = st.text_input("Confirm Password", type="password", key="panel_reg_conf", placeholder="••••••••", label_visibility="collapsed")

                # Password requirements checklist box
                st.markdown(render_password_requirements_box(reg_pass, is_dark=is_dark), unsafe_allow_html=True)

                if st.button("Create Account & Send Verification Code →", type="primary", use_container_width=True, key="panel_btn_submit_reg"):
                    reg_dob_str = reg_dob_val.strftime("%Y-%m-%d") if reg_dob_val else ""
                    has_err = False
                    if not reg_name or not reg_name.strip():
                        st.session_state["auth_err_reg_name"] = True
                        has_err = True
                    else:
                        st.session_state.pop("auth_err_reg_name", None)

                    if not reg_email or not reg_email.strip():
                        st.session_state["auth_err_reg_email"] = True
                        has_err = True
                    else:
                        st.session_state.pop("auth_err_reg_email", None)

                    if not reg_pass:
                        st.session_state["auth_err_reg_pass"] = True
                        has_err = True
                    else:
                        st.session_state.pop("auth_err_reg_pass", None)

                    if not reg_conf or reg_conf != reg_pass:
                        st.session_state["auth_err_reg_conf"] = True
                        has_err = True
                    else:
                        st.session_state.pop("auth_err_reg_conf", None)

                    if has_err:
                        trigger_popup("Fields Required", "Please fill in all required registration fields correctly.", "warning")
                        st.rerun()
                    else:
                        with st.spinner("Registering vault and sending activation code..."):
                            ok, msg = auth_svc.register_user(reg_name, reg_email, reg_pass, reg_conf, dob=reg_dob_str)
                        if ok:
                            st.session_state["auth_temp_email"] = reg_email.strip().lower()
                            st.session_state["auth_temp_name"] = reg_name.strip()
                            st.session_state["auth_view"] = "REGISTER_OTP"
                            trigger_popup("Registration Successful", f"Account created for {reg_name.strip()}! A 6-digit activation code has been sent to {reg_email.strip()}.", "success")
                            st.rerun()
                        else:
                            trigger_popup("Registration Failed", msg or "Could not complete registration. Please try again.", "error")
                            st.rerun()

                # Clean Bottom Navigation (No emojis, hides current view)
                render_auth_bottom_nav("REGISTER")

            # -------------------------------------------------------------
            # VIEW 4: REGISTER ACTIVATION OTP
            # -------------------------------------------------------------
            elif view == "REGISTER_OTP":
                email = st.session_state.get("auth_temp_email", "")
                name = st.session_state.get("auth_temp_name", "")
                st.markdown(f"""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <div class="auth-form-title">Account Activation</div>
                <div class="auth-form-sub">A single-use activation code has been sent to <strong>{email}</strong>.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <span>6-Digit Activation Code</span>
                </div>
                """, unsafe_allow_html=True)
                reg_otp_code = st.text_input("Activation Code", max_chars=6, key="panel_reg_otp_input", placeholder="123456", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Activate & Sign In →", type="primary", use_container_width=True, key="panel_btn_activate_now"):
                    if not reg_otp_code or len(reg_otp_code.strip()) < 6:
                        trigger_popup("Activation Code Required", "Please enter the complete 6-digit activation code.", "warning")
                        st.rerun()
                    else:
                        with st.spinner("Activating account..."):
                            ok, msg = auth_svc.activate_user_account(email, reg_otp_code)
                        if ok:
                            trigger_popup("Account Activated", msg or "Your account has been successfully verified! You may now sign in.", "success")
                            st.session_state["auth_view"] = "LOGIN"
                            st.rerun()
                        else:
                            trigger_popup("Activation Failed", msg or "Invalid or expired activation code.", "error")
                            st.rerun()

                st.markdown('<div class="auth-or-divider"><span>OPTIONS</span></div>', unsafe_allow_html=True)

                if st.button("Resend Activation Code", use_container_width=True, key="panel_btn_resend_reg"):
                    ok, msg = auth_svc.request_otp(email, "REGISTRATION", name)
                    if ok:
                        trigger_popup("Code Dispatched", msg or "A new activation code has been dispatched to your email.", "success")
                        st.rerun()
                    else:
                        trigger_popup("Dispatch Failed", msg or "Could not resend activation code.", "warning")
                        st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("Back to Registration", key="panel_btn_back_to_reg", use_container_width=True):
                    st.session_state["auth_view"] = "REGISTER"
                    st.rerun()

            # -------------------------------------------------------------
            # VIEW 5: RECOVERY PASSWORD
            # -------------------------------------------------------------
            elif view == "RECOVERY":
                st.markdown("""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="auth-form-title">Password Recovery</div>
                <div class="auth-form-sub">Enter your registered email address to receive a secure password recovery code.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <span>Registered Email Address</span>
                </div>
                """, unsafe_allow_html=True)
                rec_email = st.text_input("Registered Email Address", key="panel_rec_email", placeholder="you@example.com", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Send Recovery Code →", type="primary", use_container_width=True, key="panel_btn_send_rec"):
                    if not rec_email or not rec_email.strip():
                        st.session_state["auth_err_rec_email"] = True
                        trigger_popup("Email Required", "Please enter your registered email address.", "warning")
                        st.rerun()
                    else:
                        st.session_state.pop("auth_err_rec_email", None)
                        with st.spinner("Dispatching cryptographic recovery code..."):
                            ok, msg = auth_svc.initiate_recovery_password(rec_email)
                        if ok:
                            st.session_state["auth_temp_email"] = rec_email.strip().lower()
                            st.session_state["auth_view"] = "RECOVERY_OTP"
                            trigger_popup("Recovery Code Sent", msg or f"A 6-digit recovery code has been sent to {rec_email}.", "success")
                            st.rerun()
                        else:
                            trigger_popup("Recovery Failed", msg or "Could not initiate password recovery.", "error")
                            st.rerun()

                # Clean Bottom Navigation (No emojis, hides current view)
                render_auth_bottom_nav("RECOVERY")

            # -------------------------------------------------------------
            # VIEW 6: RECOVERY OTP & SET NEW PASSWORD
            # -------------------------------------------------------------
            elif view == "RECOVERY_OTP":
                email = st.session_state.get("auth_temp_email", "")
                st.markdown(f"""
                <div class="auth-center-icon-badge">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 2l-2 2m-1.5 1.5L14 9a6 6 0 1 0 3 3l3.5-3.5m0 0l2 2m-2-2l2-2"/>
                        <circle cx="8" cy="16" r="3"/>
                    </svg>
                </div>
                <div class="auth-form-title">Set New Password</div>
                <div class="auth-form-sub">Enter the recovery code sent to <strong>{email}</strong> and configure your new password.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-1.5 1.5L14 9a6 6 0 1 0 3 3l3.5-3.5m0 0l2 2m-2-2l2-2"/><circle cx="8" cy="16" r="3"/></svg>
                    <span>6-Digit Recovery Code</span>
                </div>
                """, unsafe_allow_html=True)
                rec_code = st.text_input("Recovery Code", max_chars=6, key="panel_rec_otp_input", placeholder="Enter 6-digit code", label_visibility="collapsed")

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>New Password</span>
                </div>
                """, unsafe_allow_html=True)
                rec_p1 = st.text_input("New Password", type="password", key="panel_rec_p1", placeholder="••••••••", label_visibility="collapsed")

                _, str_label, str_color, str_bars = compute_password_strength(rec_p1)
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px; margin-bottom: 6px;">
                    <div style="display: flex; gap: 4px; flex: 1; max-width: 220px;">
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[0]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[1]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[2]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[3]};"></span>
                        <span style="flex: 1; height: 4px; border-radius: 3px; background: {str_bars[4]};"></span>
                    </div>
                    <span style="font-size: 0.72rem; font-weight: 700; color: {str_color};">{str_label}</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>Confirm New Password</span>
                </div>
                """, unsafe_allow_html=True)
                rec_p2 = st.text_input("Confirm New Password", type="password", key="panel_rec_p2", placeholder="••••••••", label_visibility="collapsed")

                st.markdown(render_password_requirements_box(rec_p1, is_dark=is_dark), unsafe_allow_html=True)

                if st.button("Reset Password & Save →", type="primary", use_container_width=True, key="panel_btn_finish_rec"):
                    if not rec_code or len(rec_code.strip()) < 6:
                        trigger_popup("Recovery Code Required", "Please enter the complete 6-digit recovery code.", "warning")
                        st.rerun()
                    elif not rec_p1 or not rec_p2:
                        trigger_popup("Password Required", "Please enter and confirm your new password.", "warning")
                        st.rerun()
                    elif rec_p1 != rec_p2:
                        trigger_popup("Password Mismatch", "The passwords entered do not match. Please re-enter.", "warning")
                        st.rerun()
                    else:
                        with st.spinner("Securing new password hash..."):
                            ok, msg = auth_svc.verify_recovery_otp_and_reset_password(email, rec_code, rec_p1, rec_p2)
                        if ok:
                            trigger_popup("Password Reset Successful", msg or "Your password has been reset successfully! You can now sign in with your new password.", "success")
                            st.session_state["auth_view"] = "LOGIN"
                            st.rerun()
                        else:
                            trigger_popup("Password Reset Failed", msg or "Invalid recovery code or password reset failed.", "error")
                            st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("Cancel Recovery", use_container_width=True, key="panel_btn_cancel_rec"):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()

            # -------------------------------------------------------------
            # VIEW 7: ADMINISTRATOR SIGN IN
            # -------------------------------------------------------------
            elif view == "ADMIN_LOGIN":
                st.markdown("""
                <div class="auth-center-icon-badge" style="background: rgba(239, 68, 68, 0.10); border-color: rgba(239, 68, 68, 0.30);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <circle cx="12" cy="11" r="3"/>
                    </svg>
                </div>
                <div class="auth-form-title" style="color: #EF4444;">Administrator Console</div>
                <div class="auth-form-sub">Restricted console for certified National Healthcare Command personnel. All sessions are cryptographically logged.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <span>Administrator Identity</span>
                </div>
                """, unsafe_allow_html=True)
                adm_email = st.text_input("Administrator Identity", placeholder="e.g. docmindxai@gmail.com", key="panel_adm_email", label_visibility="collapsed")

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>Master Security Password</span>
                </div>
                """, unsafe_allow_html=True)
                adm_pass = st.text_input("Master Password", type="password", key="panel_adm_pass", placeholder="••••••••", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Verify Credentials & Request Admin Key →", type="primary", use_container_width=True, key="panel_btn_adm_cred"):
                    if not adm_email or not adm_email.strip() or not adm_pass:
                        st.session_state["auth_err_adm_email"] = not bool(adm_email and adm_email.strip())
                        st.session_state["auth_err_adm_pass"] = not bool(adm_pass)
                        trigger_popup("Admin Credentials Required", "Please enter your administrator ID and master password.", "warning")
                        st.rerun()
                    else:
                        st.session_state.pop("auth_err_adm_email", None)
                        st.session_state.pop("auth_err_adm_pass", None)
                        with st.spinner("Authorizing admin credentials..."):
                            ok, msg = auth_svc.authenticate_admin_credentials(adm_email, adm_pass)
                        if ok:
                            st.session_state["auth_temp_email"] = adm_email.strip().lower()
                            auth_svc.send_admin_login_otp_code(adm_email)
                            trigger_popup("Admin Credentials Verified", f"Security key dispatched to {adm_email}.", "success")
                            st.session_state["auth_view"] = "ADMIN_OTP"
                            st.rerun()
                        else:
                            trigger_popup("Admin Access Denied", msg or "Invalid administrator credentials.", "error")
                            st.rerun()

                # Clean Bottom Navigation (No emojis, hides current view)
                render_auth_bottom_nav("ADMIN")

            # -------------------------------------------------------------
            # VIEW 8: ADMIN KEY OTP
            # -------------------------------------------------------------
            elif view == "ADMIN_OTP":
                email = st.session_state.get("auth_temp_email", "docmindxai@gmail.com")
                st.markdown(f"""
                <div class="auth-center-icon-badge" style="background: rgba(239, 68, 68, 0.10); border-color: rgba(239, 68, 68, 0.30);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 2l-2 2m-1.5 1.5L14 9a6 6 0 1 0 3 3l3.5-3.5m0 0l2 2m-2-2l2-2"/>
                        <circle cx="8" cy="16" r="3"/>
                    </svg>
                </div>
                <div class="auth-form-title" style="color: #EF4444;">Admin Security Key</div>
                <div class="auth-form-sub">High-security authorization key dispatched to <strong>{email}</strong>.</div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="auth-clean-label">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>6-Digit Admin Key</span>
                </div>
                """, unsafe_allow_html=True)
                adm_otp_val = st.text_input("6-Digit Admin Key", max_chars=6, key="panel_adm_otp_val", placeholder="123456", label_visibility="collapsed")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Authenticate Admin Console →", type="primary", use_container_width=True, key="panel_btn_adm_auth"):
                    if not adm_otp_val or len(adm_otp_val.strip()) < 6:
                        trigger_popup("Admin Key Required", "Please enter the 6-digit admin security key.", "warning")
                        st.rerun()
                    else:
                        with st.spinner("Granting elevated admin session..."):
                            ok, msg, session_data = auth_svc.complete_admin_login(email, adm_otp_val)
                        if ok:
                            st.session_state["user_auth"] = session_data
                            st.session_state["active_panel"] = "Admin Panel"
                            trigger_popup("Admin Access Granted", "Welcome to the National Command Administrative Console.", "success")
                            st.rerun()
                        else:
                            trigger_popup("Authentication Failed", msg or "Invalid administrator key.", "error")
                            st.rerun()

                st.markdown('<div class="auth-or-divider"><span>OPTIONS</span></div>', unsafe_allow_html=True)

                if st.button("Resend Admin Key", use_container_width=True, key="panel_btn_resend_adm_key"):
                    ok, msg = auth_svc.send_admin_login_otp_code(email)
                    if ok:
                        trigger_popup("Admin Key Dispatched", msg or "A new security key has been dispatched.", "success")
                        st.rerun()
                    else:
                        trigger_popup("Dispatch Failed", msg or "Could not resend admin key.", "warning")
                        st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("Cancel", key="panel_btn_cancel_adm", use_container_width=True):
                    st.session_state["auth_view"] = "LOGIN"
                    st.rerun()
