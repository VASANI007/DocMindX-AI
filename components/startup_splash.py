"""DocMindX AI — Startup Splash & Loading Screen Component
===================================================================
Provides a branded startup splash/loading screen for DocMindX AI,
reproducing the user's provided visual designs (Desktop & Mobile),
while the Streamlit application performs background initialization.

Strict constraints:
1. Seamless startup: Displays immediately without raw white blank screen.
2. Desktop layout: Matches horizontal connected steps design (Image 2).
3. Mobile layout: Matches vertical timeline list with status indicators (Image 3).
4. Auto-dismissal: Smoothly transitions into main application upon completion.
5. Re-appears on browser refresh; does NOT re-appear on normal in-app interactions.
6. Zero post-startup UI modifications.
"""

import base64
import html
import logging
import os
import time
import streamlit as st
import streamlit.components.v1 as components

_logger = logging.getLogger("DocMindX.Startup")

# Assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
SPLASH_BG_PATH = os.path.join(ASSETS_DIR, "loading", "splash_bg.png")
SPLASH_LOGO_PATH = os.path.join(ASSETS_DIR, "loading", "docmindx_logo.png")
FALLBACK_ICON_PATH = os.path.join(ASSETS_DIR, "logo", "icon.png")

_CACHED_ASSETS = {}


def _get_asset_b64(path: str) -> str:
    """Reads and base64-encodes an image asset with caching."""
    if path in _CACHED_ASSETS:
        return _CACHED_ASSETS[path]
    try:
        if os.path.exists(path):
            ext = "png" if path.lower().endswith(".png") else "jpeg"
            with open(path, "rb") as f:
                encoded = f"data:image/{ext};base64,{base64.b64encode(f.read()).decode('utf-8')}"
                _CACHED_ASSETS[path] = encoded
                return encoded
    except Exception as exc:
        _logger.warning("[Startup] Could not load asset %s: %s", path, exc)
    return ""


# SVG Icons
ICON_GEAR = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""

ICON_DATABASE = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>"""

ICON_BRAIN = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04z"></path></svg>"""

ICON_CLOUD = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>"""

ICON_SHIELD_CHECK = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>"""

ICON_CHECK_SMALL = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>"""

ICON_CHECK_BLUE = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0080FF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>"""

ICON_BULB = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0080FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="18" x2="15" y2="18"></line><line x1="10" y1="22" x2="14" y2="22"></line><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path></svg>"""


def get_splash_overlay_html() -> str:
    """Builds the full-screen overlay HTML with both Desktop and Mobile layouts."""
    logo_b64 = _get_asset_b64(SPLASH_LOGO_PATH) or _get_asset_b64(FALLBACK_ICON_PATH)
    bg_b64 = _get_asset_b64(SPLASH_BG_PATH)

    bg_style = f"background: #F8FAFC url('{bg_b64}') no-repeat center center; background-size: cover;" if bg_b64 else "background: radial-gradient(circle at 50% 30%, #F0F7FC 0%, #E2EFFA 100%);"

    html_code = f"""
    <div id="docmindx-splash-overlay">
        <style>
            #docmindx-splash-overlay {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                z-index: 9999999 !important;
                {bg_style}
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                color: #0F172A !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                margin: 0 !important;
                padding: 1rem !important;
                box-sizing: border-box !important;
            }}

            .splash-container {{
                width: 100% !important;
                max-width: 680px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                text-align: center !important;
                position: relative !important;
                z-index: 10 !important;
                margin: auto !important;
            }}

            /* Logo */
            .splash-logo-wrap {{
                width: 116px !important;
                height: 116px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-bottom: -4px !important;
                filter: drop-shadow(0 8px 24px rgba(0, 128, 255, 0.28)) !important;
                animation: floatLogo 3s ease-in-out infinite alternate !important;
            }}

            .splash-logo-img {{
                width: 100% !important;
                height: 100% !important;
                object-fit: contain !important;
            }}

            /* Typography */
            .splash-brand {{
                font-size: 32px !important;
                font-weight: 800 !important;
                letter-spacing: -0.5px !important;
                line-height: 1.1 !important;
                margin: 0 !important;
                margin-top: 0px !important;
                margin-bottom: 2px !important;
                color: #0F172A !important;
            }}

            .splash-brand-ai {{
                color: #0080FF !important;
            }}

            .splash-subtitle {{
                font-size: 15px !important;
                font-weight: 500 !important;
                color: #475569 !important;
                margin-top: 4px !important;
                margin-bottom: 10px !important;
            }}

            /* Pill Badge */
            .splash-badge {{
                display: inline-flex !important;
                align-items: center !important;
                gap: 8px !important;
                background: rgba(224, 242, 254, 0.9) !important;
                border: 1px solid rgba(186, 230, 253, 0.95) !important;
                border-radius: 9999px !important;
                padding: 4px 16px !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                color: #0284C7 !important;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
            }}

            .badge-sep {{
                opacity: 0.4 !important;
            }}

            /* Status Text */
            .splash-status-title {{
                font-size: 22px !important;
                font-weight: 700 !important;
                margin-top: 22px !important;
                margin-bottom: 4px !important;
                letter-spacing: -0.2px !important;
                color: #0F172A !important;
            }}

            .splash-status-desc {{
                font-size: 13.5px !important;
                color: #64748B !important;
                margin-bottom: 16px !important;
                min-height: 20px !important;
            }}

            /* Progress Bar */
            .splash-progress-row {{
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 14px !important;
                width: 100% !important;
                max-width: 480px !important;
                margin-bottom: 24px !important;
            }}

            .splash-progress-track {{
                flex: 1 !important;
                height: 12px !important;
                background: #E2E8F0 !important;
                border-radius: 9999px !important;
                overflow: hidden !important;
                position: relative !important;
                box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.08) !important;
            }}

            .splash-progress-bar {{
                height: 100% !important;
                background: linear-gradient(90deg, #00D2FF 0%, #0080FF 100%) !important;
                border-radius: 9999px !important;
                width: 0%;
                box-shadow: 0 0 14px rgba(0, 128, 255, 0.65) !important;
                transition: width 0.05s ease-out !important;
            }}

            .splash-progress-pct {{
                font-size: 15px !important;
                font-weight: 800 !important;
                color: #0F172A !important;
                min-width: 44px !important;
                text-align: right !important;
            }}

            /* ------------------------------------------------------------- */
            /* DESKTOP STEPS (Horizontal - Image 2)                          */
            /* ------------------------------------------------------------- */
            .desktop-steps {{
                display: flex !important;
                align-items: flex-start !important;
                justify-content: space-between !important;
                width: 100% !important;
                max-width: 530px !important;
                position: relative !important;
                margin-bottom: 22px !important;
            }}

            .desktop-line-container {{
                position: absolute !important;
                top: 21px !important;
                left: 10% !important;
                right: 10% !important;
                height: 3px !important;
                z-index: 1 !important;
                border-radius: 2px !important;
                overflow: hidden !important;
            }}

            .desktop-line-bg {{
                position: absolute !important;
                inset: 0 !important;
                background: #E2E8F0 !important;
                border-radius: 2px !important;
            }}

            .desktop-line-fill {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                height: 100% !important;
                background: linear-gradient(90deg, #00D2FF, #0080FF) !important;
                border-radius: 2px !important;
                width: 0%;
                transition: width 0.05s ease-out !important;
            }}

            .desktop-step {{
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                position: relative !important;
                z-index: 3 !important;
                flex: 1 !important;
            }}

            .desktop-step-circle {{
                width: 42px !important;
                height: 42px !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                background: #FFFFFF !important;
                border: 2px solid #CBD5E1 !important;
                color: #94A3B8 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            }}

            .desktop-step.active .desktop-step-circle {{
                background: #0080FF !important;
                border-color: #0080FF !important;
                color: #FFFFFF !important;
                box-shadow: 0 0 0 4px rgba(0, 128, 255, 0.2), 0 4px 14px rgba(0, 128, 255, 0.45) !important;
                animation: stepPulse 1.8s infinite !important;
            }}

            .desktop-step.completed .desktop-step-circle {{
                background: #0080FF !important;
                border-color: #0080FF !important;
                color: #FFFFFF !important;
                box-shadow: 0 3px 10px rgba(0, 128, 255, 0.35) !important;
            }}

            .desktop-step-label {{
                font-size: 11px !important;
                font-weight: 600 !important;
                line-height: 1.25 !important;
                margin-top: 7px !important;
                text-align: center !important;
                color: #94A3B8 !important;
                transition: color 0.3s ease !important;
            }}

            .desktop-step.active .desktop-step-label,
            .desktop-step.completed .desktop-step-label {{
                color: #0F172A !important;
            }}

            /* ------------------------------------------------------------- */
            /* MOBILE STEPS (Vertical Timeline - Image 3)                    */
            /* ------------------------------------------------------------- */
            .mobile-steps {{
                display: none !important;
                flex-direction: column !important;
                width: 100% !important;
                max-width: 380px !important;
                position: relative !important;
                margin: 0 auto 20px auto !important;
                padding-left: 10px !important;
                padding-right: 10px !important;
            }}

            .mobile-timeline-line {{
                position: absolute !important;
                top: 20px !important;
                bottom: 20px !important;
                left: 31px !important;
                width: 2px !important;
                background: #E2E8F0 !important;
                z-index: 1 !important;
            }}

            .mobile-step-item {{
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                position: relative !important;
                z-index: 2 !important;
                padding: 8px 0 !important;
                width: 100% !important;
            }}

            .mobile-step-left {{
                display: flex !important;
                align-items: center !important;
                gap: 14px !important;
                text-align: left !important;
            }}

            .mobile-step-circle {{
                width: 42px !important;
                height: 42px !important;
                border-radius: 50% !important;
                background: #FFFFFF !important;
                border: 2px solid #E2E8F0 !important;
                color: #64748B !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                flex-shrink: 0 !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
            }}

            .mobile-step-item.active .mobile-step-circle {{
                background: #0080FF !important;
                border-color: #0080FF !important;
                color: #FFFFFF !important;
                box-shadow: 0 0 0 3px rgba(0, 128, 255, 0.22) !important;
            }}

            .mobile-step-item.completed .mobile-step-circle {{
                background: #0080FF !important;
                border-color: #0080FF !important;
                color: #FFFFFF !important;
            }}

            .mobile-step-text {{
                display: flex !important;
                flex-direction: column !important;
            }}

            .mobile-step-title {{
                font-size: 13px !important;
                font-weight: 700 !important;
                color: #64748B !important;
                transition: color 0.3s ease !important;
            }}

            .mobile-step-item.active .mobile-step-title,
            .mobile-step-item.completed .mobile-step-title {{
                color: #0F172A !important;
            }}

            .mobile-step-desc {{
                font-size: 11px !important;
                color: #94A3B8 !important;
                margin-top: 1px !important;
            }}

            .mobile-step-status {{
                flex-shrink: 0 !important;
                width: 26px !important;
                height: 26px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }}

            .status-ring {{
                width: 18px !important;
                height: 18px !important;
                border: 2px solid #CBD5E1 !important;
                border-radius: 50% !important;
            }}

            .status-spinner {{
                width: 20px !important;
                height: 20px !important;
                border: 2.5px solid rgba(0, 128, 255, 0.25) !important;
                border-top-color: #0080FF !important;
                border-radius: 50% !important;
                animation: spin 0.8s linear infinite !important;
            }}

            /* ------------------------------------------------------------- */
            /* CALLOUT BOX & FOOTER                                          */
            /* ------------------------------------------------------------- */
            .splash-callout {{
                display: flex !important;
                align-items: center !important;
                gap: 14px !important;
                background: rgba(240, 248, 255, 0.94) !important;
                border: 1px solid #D0E8F7 !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                max-width: 500px !important;
                width: 100% !important;
                text-align: left !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
                margin-bottom: 18px !important;
            }}

            .splash-callout-icon {{
                flex-shrink: 0 !important;
                width: 36px !important;
                height: 36px !important;
                border-radius: 50% !important;
                background: #E0F2FE !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }}

            .splash-callout-title {{
                font-size: 13px !important;
                font-weight: 700 !important;
                color: #0F172A !important;
                margin-bottom: 2px !important;
            }}

            .splash-callout-text {{
                font-size: 11.5px !important;
                color: #475569 !important;
                line-height: 1.35 !important;
            }}

            .splash-footer {{
                font-size: 11px !important;
                color: #64748B !important;
                font-weight: 500 !important;
            }}

            .splash-heart {{
                color: #EF4444 !important;
                margin-right: 2px !important;
            }}

            /* Keyframes */
            @keyframes progressAnim {{
                0% {{ width: 0%; }}
                18% {{ width: 20%; }}
                42% {{ width: 45%; }}
                68% {{ width: 72%; }}
                88% {{ width: 90%; }}
                100% {{ width: 100%; }}
            }}

            @keyframes lineAnim {{
                0% {{ width: 0%; }}
                20% {{ width: 25%; }}
                45% {{ width: 50%; }}
                70% {{ width: 75%; }}
                90% {{ width: 100%; }}
                100% {{ width: 100%; }}
            }}

            @keyframes floatLogo {{
                0% {{ transform: translateY(0px) scale(1); }}
                100% {{ transform: translateY(-3px) scale(1.02); }}
            }}

            @keyframes stepPulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(0, 128, 255, 0.45); }}
                70% {{ box-shadow: 0 0 0 8px rgba(0, 128, 255, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(0, 128, 255, 0); }}
            }}

            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}

            /* Media Queries */
            @media (max-width: 767px) {{
                .desktop-steps {{ display: none !important; }}
                .mobile-steps {{ display: flex !important; }}
                .splash-brand {{ font-size: 26px !important; }}
                .splash-logo-wrap {{ width: 96px !important; height: 96px !important; margin-bottom: 10px !important; }}
                .splash-status-title {{ font-size: 19px !important; }}
                .splash-callout {{ padding: 10px 14px !important; }}
                .splash-callout-text {{ font-size: 11px !important; }}
            }}

            @media (min-width: 768px) {{
                .desktop-steps {{ display: flex !important; }}
                .mobile-steps {{ display: none !important; }}
            }}
        </style>

        <div class="splash-container">
            <!-- Brand Logo -->
            <div class="splash-logo-wrap">
                <img src="{logo_b64}" alt="DocMindX AI Logo" class="splash-logo-img"/>
            </div>

            <!-- Title & Subtitle -->
            <h1 class="splash-brand">DocMindX <span class="splash-brand-ai">AI</span></h1>
            <div class="splash-subtitle">Your Family's Health Companion</div>

            <!-- Pill Badge -->
            <div class="splash-badge">
                <span>AI</span>
                <span class="badge-sep">|</span>
                <span>Trusted Data</span>
                <span class="badge-sep">|</span>
                <span>Safer Decisions</span>
            </div>

            <!-- Dynamic Status Headline -->
            <div id="statusTitle" class="splash-status-title">Getting things ready...</div>
            <div id="statusDesc" class="splash-status-desc">Loading AI models, clinical knowledge and healthcare services</div>

            <!-- Dynamic Progress Bar -->
            <div class="splash-progress-row">
                <div class="splash-progress-track">
                    <div id="progressBar" class="splash-progress-bar"></div>
                </div>
                <div id="progressPct" class="splash-progress-pct">0%</div>
            </div>

            <!-- DESKTOP STEPS (Horizontal) -->
            <div class="desktop-steps">
                <div class="desktop-line-container">
                    <div class="desktop-line-bg"></div>
                    <div id="desktopLineFill" class="desktop-line-fill"></div>
                </div>

                <div id="dStep0" class="desktop-step active">
                    <div id="dCircle0" class="desktop-step-circle">{ICON_GEAR}</div>
                    <div class="desktop-step-label">Initializing<br/>Application</div>
                </div>
                <div id="dStep1" class="desktop-step">
                    <div id="dCircle1" class="desktop-step-circle">{ICON_DATABASE}</div>
                    <div class="desktop-step-label">Loading<br/>Clinical Knowledge</div>
                </div>
                <div id="dStep2" class="desktop-step">
                    <div id="dCircle2" class="desktop-step-circle">{ICON_BRAIN}</div>
                    <div class="desktop-step-label">Preparing<br/>AI Models</div>
                </div>
                <div id="dStep3" class="desktop-step">
                    <div id="dCircle3" class="desktop-step-circle">{ICON_CLOUD}</div>
                    <div class="desktop-step-label">Connecting<br/>Healthcare Services</div>
                </div>
                <div id="dStep4" class="desktop-step">
                    <div id="dCircle4" class="desktop-step-circle">{ICON_SHIELD_CHECK}</div>
                    <div class="desktop-step-label">Almost<br/>Ready</div>
                </div>
            </div>

            <!-- MOBILE STEPS (Vertical Timeline - Image 3) -->
            <div class="mobile-steps">
                <div class="mobile-timeline-line"></div>

                <div id="mStep0" class="mobile-step-item active">
                    <div class="mobile-step-left">
                        <div class="mobile-step-circle">{ICON_GEAR}</div>
                        <div class="mobile-step-text">
                            <span class="mobile-step-title">Initializing Application</span>
                            <span class="mobile-step-desc">Setting up essential components...</span>
                        </div>
                    </div>
                    <div id="mStatus0" class="mobile-step-status"><div class="status-spinner"></div></div>
                </div>

                <div id="mStep1" class="mobile-step-item">
                    <div class="mobile-step-left">
                        <div class="mobile-step-circle">{ICON_DATABASE}</div>
                        <div class="mobile-step-text">
                            <span class="mobile-step-title">Loading Clinical Knowledge</span>
                            <span class="mobile-step-desc">Preparing medical databases...</span>
                        </div>
                    </div>
                    <div id="mStatus1" class="mobile-step-status"><div class="status-ring"></div></div>
                </div>

                <div id="mStep2" class="mobile-step-item">
                    <div class="mobile-step-left">
                        <div class="mobile-step-circle">{ICON_BRAIN}</div>
                        <div class="mobile-step-text">
                            <span class="mobile-step-title">Preparing AI Models</span>
                            <span class="mobile-step-desc">Loading AI capabilities...</span>
                        </div>
                    </div>
                    <div id="mStatus2" class="mobile-step-status"><div class="status-ring"></div></div>
                </div>

                <div id="mStep3" class="mobile-step-item">
                    <div class="mobile-step-left">
                        <div class="mobile-step-circle">{ICON_CLOUD}</div>
                        <div class="mobile-step-text">
                            <span class="mobile-step-title">Connecting Healthcare Services</span>
                            <span class="mobile-step-desc">Setting up trusted resources...</span>
                        </div>
                    </div>
                    <div id="mStatus3" class="mobile-step-status"><div class="status-ring"></div></div>
                </div>

                <div id="mStep4" class="mobile-step-item">
                    <div class="mobile-step-left">
                        <div class="mobile-step-circle">{ICON_SHIELD_CHECK}</div>
                        <div class="mobile-step-text">
                            <span class="mobile-step-title">Almost Ready</span>
                            <span class="mobile-step-desc">Finalizing...</span>
                        </div>
                    </div>
                    <div id="mStatus4" class="mobile-step-status"><div class="status-ring"></div></div>
                </div>
            </div>

            <!-- Did You Know Box -->
            <div class="splash-callout">
                <div class="splash-callout-icon">{ICON_BULB}</div>
                <div class="splash-callout-content">
                    <div class="splash-callout-title">Did you know?</div>
                    <div class="splash-callout-text">DocMindX AI uses trusted medical data and AI to support early health insights. It does not replace professional medical advice.</div>
                </div>
            </div>

            <!-- Footer -->
            <div class="splash-footer">
                <span class="splash-heart">❤️</span> Powered by AI &nbsp;|&nbsp; Guided by Science &nbsp;|&nbsp; Built for Families
            </div>
        </div>
    </div>
    """
    return html_code


def get_animation_script_html() -> str:
    """Builds JavaScript component that runs in parent window to drive real-time counter & stages."""
    check_blue_escaped = ICON_CHECK_BLUE.replace('"', '\\"')
    check_small_escaped = ICON_CHECK_SMALL.replace('"', '\\"')

    return f"""
    <script>
        (function() {{
            function startDriver() {{
                let pDoc;
                try {{
                    pDoc = window.parent.document;
                }} catch(e) {{
                    pDoc = null;
                }}
                if (!pDoc) {{
                    try {{
                        pDoc = document;
                    }} catch(e) {{
                        return;
                    }}
                }}

                const pBar = pDoc.getElementById("progressBar");
                const pPct = pDoc.getElementById("progressPct");
                if (!pBar || !pPct) {{
                    setTimeout(startDriver, 35);
                    return;
                }}

                const checkBlue = "{check_blue_escaped}";
                const checkSmall = "{check_small_escaped}";

                const stages = [
                    {{ atPct: 0, title: "Getting things ready...", desc: "Setting up essential components and secure environment...", step: 0 }},
                    {{ atPct: 20, title: "Loading clinical knowledge...", desc: "Preparing medical databases & 280+ symptom taxonomy...", step: 1 }},
                    {{ atPct: 45, title: "Preparing AI models...", desc: "Loading symptom triage engine & diagnostic analyzers...", step: 2 }},
                    {{ atPct: 70, title: "Connecting healthcare services...", desc: "Setting up regional healthcare resources & connection pool...", step: 3 }},
                    {{ atPct: 88, title: "Almost ready...", desc: "Finalizing clinical intelligence systems and security tokens...", step: 4 }},
                    {{ atPct: 96, title: "DocMindX AI is ready", desc: "All clinical intelligence systems online. Welcome to DocMindX AI.", step: 5 }}
                ];

                let pct = 0;
                let currentStage = 0;

                function updateProgress(val) {{
                    if (pBar) {{
                        pBar.style.setProperty("width", val + "%", "important");
                    }}
                    if (pPct) {{
                        pPct.innerText = val + "%";
                    }}
                    const dLine = pDoc.getElementById("desktopLineFill");
                    if (dLine) {{
                        dLine.style.setProperty("width", Math.min(100, Math.max(0, val)) + "%", "important");
                    }}
                }}

                function applyStage(idx) {{
                    const s = stages[Math.min(idx, stages.length - 1)];
                    const sTitle = pDoc.getElementById("statusTitle");
                    const sDesc = pDoc.getElementById("statusDesc");
                    if (sTitle && s) sTitle.innerText = s.title;
                    if (sDesc && s) sDesc.innerText = s.desc;

                    // Update Desktop Nodes
                    for (let i = 0; i <= 4; i++) {{
                        const dStep = pDoc.getElementById("dStep" + i);
                        const dCirc = pDoc.getElementById("dCircle" + i);
                        if (dStep && dCirc) {{
                            if (i < idx) {{
                                dStep.className = "desktop-step completed";
                                dCirc.innerHTML = checkSmall;
                            }} else if (i === idx) {{
                                dStep.className = "desktop-step active";
                            }} else {{
                                dStep.className = "desktop-step";
                            }}
                        }}

                        // Update Mobile Nodes
                        const mStep = pDoc.getElementById("mStep" + i);
                        const mStat = pDoc.getElementById("mStatus" + i);
                        if (mStep && mStat) {{
                            if (i < idx) {{
                                mStep.className = "mobile-step-item completed";
                                mStat.innerHTML = checkBlue;
                            }} else if (i === idx) {{
                                mStep.className = "mobile-step-item active";
                                mStat.innerHTML = '<div class="status-spinner"></div>';
                            }} else {{
                                mStep.className = "mobile-step-item";
                                mStat.innerHTML = '<div class="status-ring"></div>';
                            }}
                        }}
                    }}
                }}

                applyStage(0);
                updateProgress(0);

                const timer = setInterval(() => {{
                    pct += 1;
                    if (pct > 100) pct = 100;

                    updateProgress(pct);

                    if (pct >= 96 && currentStage < 5) {{
                        currentStage = 5;
                        applyStage(5);
                    }} else if (pct >= 88 && currentStage < 4) {{
                        currentStage = 4;
                        applyStage(4);
                    }} else if (pct >= 70 && currentStage < 3) {{
                        currentStage = 3;
                        applyStage(3);
                    }} else if (pct >= 45 && currentStage < 2) {{
                        currentStage = 2;
                        applyStage(2);
                    }} else if (pct >= 20 && currentStage < 1) {{
                        currentStage = 1;
                        applyStage(1);
                    }}

                    if (pct >= 100) {{
                        clearInterval(timer);
                        applyStage(5);
                        const sTitle = pDoc.getElementById("statusTitle");
                        const sDesc = pDoc.getElementById("statusDesc");
                        if (sTitle) sTitle.innerText = "DocMindX AI is ready";
                        if (sDesc) sDesc.innerText = "All clinical intelligence systems online. Welcome to DocMindX AI.";

                        const overlay = pDoc.getElementById("docmindx-splash-overlay");
                        if (overlay) {{
                            overlay.style.transition = "opacity 0.45s ease-out";
                            overlay.style.opacity = "0";
                        }}
                    }}
                }}, 70); // 70ms * 100 = 7.0s smooth continuous count (7 seconds total)
            }}

            startDriver();
        }})();
    </script>
    """


def render_startup_splash_screen() -> None:
    """
    Renders the startup splash screen using a full-viewport fixed overlay.
    Simultaneously performs real background initialization in Python
    (databases, translations, triage engine, and diagnostic analyzers).
    Once finished, marks `_docmindx_startup_ready` and triggers rerun.
    """
    _logger.info("[Startup] Application initialization started (7-second warm-up)")

    raw_html = get_splash_overlay_html()
    # Minify into single-line HTML string: strictly prevents CommonMark from splitting tags
    minified_html = " ".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(minified_html, unsafe_allow_html=True)

    # Launch driver script inside helper component iframe (runs in parent DOM)
    components.html(get_animation_script_html(), height=0, width=0)

    # -------------------------------------------------------------
    # REAL BACKGROUND INITIALIZATION & PRE-WARMING (Executes while splash animates)
    # -------------------------------------------------------------
    t_start = time.time()

    # Stage 1: Seed database & load translations
    try:
        from database.insert_data import seed_sample_records_if_empty
        seed_sample_records_if_empty()
        from config.language import load_translations
        load_translations()
        _logger.info("[Startup] Database & translations pre-loaded")
    except Exception as exc:
        _logger.warning("[Startup] Stage 1 background check warning: %s", exc)

    # Stage 2: Clinical knowledge & Canonical concepts
    try:
        from ai.disease_prediction.canonical_concepts import canonical_normalizer
        _ = canonical_normalizer.normalize("fever")
        _logger.info("[Startup] Clinical knowledge & taxonomy pre-loaded")
    except Exception as exc:
        _logger.warning("[Startup] Stage 2 background check warning: %s", exc)

    # Stage 3: AI Models & Report Analyzers Pre-warming
    try:
        from ai.disease_prediction.predict import SymptomTriageEngine
        from ai.report_ai.blood_report import LabReportAnalyzer
        from ai.report_ai.prescription import PrescriptionAnalyzer
        from ai.report_ai.radiology import RadiologyReportAnalyzer
        from ai.report_ai.general_clinical_report import GeneralClinicalDocumentAnalyzer

        # Warm up the heavy models during the 7-second loading window
        _ = SymptomTriageEngine()
        _ = LabReportAnalyzer()
        _ = PrescriptionAnalyzer()
        _ = RadiologyReportAnalyzer()
        _ = GeneralClinicalDocumentAnalyzer()
        _logger.info("[Startup] All AI models and analyzers pre-warmed in memory")
    except Exception as exc:
        _logger.warning("[Startup] Stage 3 background check warning: %s", exc)

    # Stage 4: Healthcare services & Gemini pool
    try:
        from config.settings import gemini_pool
        _ = gemini_pool.get_active_keys()
        _logger.info("[Startup] Healthcare services & Gemini pool initialized")
    except Exception as exc:
        _logger.warning("[Startup] Stage 4 background check warning: %s", exc)

    # Ensure animation completes all 5 visual stages comfortably (~7.3s total)
    elapsed = time.time() - t_start
    remaining = max(0.0, 7.3 - elapsed)
    if remaining > 0:
        time.sleep(remaining)

    # Mark ready and rerun to reveal the fully initialized application
    st.session_state["_docmindx_startup_ready"] = True
    _logger.info("[Startup] DocMindX AI 100% warmed up & ready (elapsed: %.2fs)", time.time() - t_start)
    st.rerun()
