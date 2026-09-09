# -*- coding: utf-8 -*-
"""
    DocMindX AI - Clinical Blue & Medical Cyan Design System & Theme Engine
Enterprise Clinical UI/UX Layer for Hospital-Grade Healthcare Platforms.
"""

CUSTOM_CSS = """
    <style>
/* ==========================================================================
   1. TYPOGRAPHY & CORE DESIGN TOKENS
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

/* Global Safety Net & Baseline Reset */
*, *::before, *::after {
    box-sizing: border-box !important;
}
img, svg {
    max-width: 100% !important;
    height: auto !important;
}
.stApp {
    overflow-x: hidden !important;
}

:root {
    --mm-brand-primary: #2563EB;
    --mm-brand-secondary: #06B6D4;
    --mm-brand-accent: #10B981;
    --mm-brand-hover: #1D4ED8;
    --mm-brand-active: #1E40AF;
    --mm-brand-subtle: #E0F2FE;
    --mm-brand-border: #DBEAFE;
    
    --mm-bg-base: #F8FAFC;
    --mm-bg-surface: #FFFFFF;
    --mm-bg-sidebar: #0F172A;
    
    --mm-text-primary: #1E293B;
    --mm-text-secondary: #64748B;
    --mm-text-muted: #94A3B8;
    
    --mm-border-color: #E2E8F0;
    --mm-border-light: #F1F5F9;
    
    --mm-status-critical: #EF4444;
    --mm-status-critical-bg: #FEE2E2;
    --mm-status-warning: #F59E0B;
    --mm-status-warning-bg: #FEF3C7;
    --mm-status-success: #22C55E;
    --mm-status-success-bg: #DCFCE7;
    --mm-status-info: #06B6D4;
    --mm-status-info-bg: #CFFAFE;
    
    --mm-radius-sm: 6px;
    --mm-radius-md: 8px;
    --mm-radius-lg: 12px;
    --mm-radius-xl: 16px;
    
    --mm-shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
    --mm-shadow-card: 0 2px 6px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02);
    --mm-shadow-hover: 0 6px 16px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
}

/* ============================================================
   DARK MODE -- activated when data-theme="dark"is set on root
   ============================================================ */
[data-theme="dark"],
[data-theme="dark"] .stApp,
[data-theme="dark"] body {
    --mm-brand-primary: #3B82F6 !important;
    --mm-brand-secondary: #06B6D4 !important;
    --mm-brand-accent: #10B981 !important;
    --mm-brand-hover: #60A5FA !important;
    --mm-brand-active: #2563EB !important;
    --mm-bg-base: #0B1220 !important;
    --mm-bg-surface: #111827 !important;
    --mm-bg-sidebar: #070C16 !important;
    --mm-text-primary: #F8FAFC !important;
    --mm-text-secondary: #94A3B8 !important;
    --mm-text-muted: #64748B !important;
    --mm-border-color: #1F2937 !important;
    --mm-border-light: #1A2333 !important;
    --mm-brand-subtle: #0C2A4A !important;
    --mm-brand-border: #1E3A5F !important;
    --mm-status-success-bg: #0F2D1E !important;
    --mm-status-info-bg: #083344 !important;
    --mm-status-critical-bg: #2D1215 !important;
    --mm-status-warning-bg: #2D1C00 !important;
    --mm-shadow-card: 0 2px 8px rgba(0,0,0,0.5), 0 1px 3px rgba(0,0,0,0.3) !important;
    --mm-shadow-hover: 0 6px 20px rgba(0,0,0,0.6), 0 2px 6px rgba(0,0,0,0.4) !important;
}

[data-theme="dark"] html,
[data-theme="dark"] body,
[data-theme="dark"] .stApp,
[data-theme="dark"] [class*="css"],
[data-theme="dark"] .stMainBlockContainer,
[data-theme="dark"] .main,
[data-theme="dark"] section.main {
    background-color: #0B1220 !important;
    color: #F8FAFC !important;
}

[data-theme="dark"] .mm-card,
[data-theme="dark"] .mm-hospital-card,
[data-theme="dark"] .stContainer,
[data-theme="dark"] [data-testid="stVerticalBlockBorderWrapper"],
[data-theme="dark"] [data-testid="stHorizontalBlock"] > div,
[data-theme="dark"] [data-testid="element-container"] > div {
    background-color: #111827 !important;
    border-color: #1E293B !important;
    color: #F8FAFC !important;
}

[data-theme="dark"] .mm-hospital-card {
    background: #111827 !important;
    border-color: #1E293B !important;
}

[data-theme="dark"] h1,
[data-theme="dark"] h2,
[data-theme="dark"] h3,
[data-theme="dark"] h4,
[data-theme="dark"] h5,
[data-theme="dark"] h6,
[data-theme="dark"] p,
[data-theme="dark"] span,
[data-theme="dark"] label,
[data-theme="dark"] div {
    color: #F8FAFC !important;
}

/* ==========================================================================
   CODE & PRE INLINE BLOCKS (LIGHT & DARK MODE HIGH CONTRAST)
   ========================================================================== */
code,
[data-testid="stMarkdownContainer"] code,
.stMarkdown code,
p code,
li code,
span code,
div code,
td code {
    background-color: #F1F5F9 !important;
    background: #F1F5F9 !important;
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    border: 1px solid #CBD5E1 !important;
    padding: 2px 7px !important;
    border-radius: 6px !important;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace !important;
    font-size: 0.86em !important;
    font-weight: 600 !important;
    display: inline-block !important;
    line-height: 1.35 !important;
}

[data-theme="dark"] code,
[data-theme="dark"] pre code,
[data-theme="dark"] [data-testid="stMarkdownContainer"] code,
[data-theme="dark"] .stMarkdown code,
[data-theme="dark"] .element-container code,
[data-theme="dark"] p code,
[data-theme="dark"] li code,
[data-theme="dark"] span code,
[data-theme="dark"] div code,
[data-theme="dark"] td code,
[data-theme="dark"] .mm-card code,
[data-theme="dark"] div[class*="mm-"] code {
    background-color: #1E293B !important;
    background: #1E293B !important;
    color: #38BDF8 !important;
    -webkit-text-fill-color: #38BDF8 !important;
    border: 1px solid #334155 !important;
    padding: 2px 7px !important;
    border-radius: 6px !important;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace !important;
    font-size: 0.86em !important;
    font-weight: 600 !important;
    display: inline-block !important;
    line-height: 1.35 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] pre,
[data-theme="dark"] pre[data-testid="stCodeBlock"] {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
}

/* Dark Mode Form Inputs (Inputs, TextAreas, Dropdowns) */
[data-theme="dark"] input,
[data-theme="dark"] textarea,
[data-theme="dark"] [data-baseweb="input"],
[data-theme="dark"] [data-baseweb="base-input"],
[data-theme="dark"] [data-baseweb="input"] input,
[data-theme="dark"] [data-baseweb="base-input"] input,
[data-theme="dark"] [data-baseweb="base-input"] textarea,
[data-theme="dark"] .stTextInput input,
[data-theme="dark"] .stTextInput > div > div,
[data-theme="dark"] .stTextArea textarea,
[data-theme="dark"] .stTextArea > div > div,
[data-theme="dark"] .stSelectbox > div > div,
[data-theme="dark"] [data-baseweb="select"] > div {
    background-color: #111827 !important;
    background: #111827 !important;
    border-color: #1E2E4E !important;
    color: #F8FAFC !important;
}

[data-theme="dark"] input::placeholder,
[data-theme="dark"] textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}

/* Dark Mode File Uploader Dropzone & Controls */
[data-theme="dark"] [data-testid="stFileUploader"],
[data-theme="dark"] [data-testid="stFileUploadDropzone"],
[data-theme="dark"] section[data-testid="stFileUploadDropzone"],
[data-theme="dark"] .stFileUploader,
[data-theme="dark"] .stFileUploader > div,
[data-theme="dark"] .stFileUploader section,
[data-theme="dark"] div[data-testid="stFileUploadDropzone"] {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
}

[data-theme="dark"] [data-testid="stFileUploadDropzone"]:hover,
[data-theme="dark"] section[data-testid="stFileUploadDropzone"]:hover {
    border-color: #2563EB !important;
    background-color: #1E293B !important;
    background: #1E293B !important;
}

[data-theme="dark"] [data-testid="stFileUploadDropzone"] div,
[data-theme="dark"] [data-testid="stFileUploadDropzone"] span,
[data-theme="dark"] [data-testid="stFileUploadDropzone"] small,
[data-theme="dark"] [data-testid="stFileUploadDropzone"] p,
[data-theme="dark"] [data-testid="stFileUploadDropzone"] label,
[data-theme="dark"] section[data-testid="stFileUploadDropzone"] * {
    color: #94A3B8 !important;
}

[data-theme="dark"] [data-testid="stFileUploadDropzone"] svg {
    fill: #94A3B8 !important;
    stroke: #94A3B8 !important;
}

[data-theme="dark"] [data-testid="stFileUploadDropzone"] button,
[data-theme="dark"] [data-testid="stFileUploader"] button,
[data-theme="dark"] [data-testid="stFileUploadDropzone"] [data-testid="baseButton-secondary"],
[data-theme="dark"] [data-testid="stFileUploadDropzone"] button[data-testid="baseButton-secondary"] {
    background-color: #1E293B !important;
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

[data-theme="dark"] [data-testid="stFileUploadDropzone"] button:hover {
    background-color: #334155 !important;
    border-color: #2563EB !important;
    color: #FFFFFF !important;
}

[data-theme="dark"] [data-testid="stFileUploaderFileData"],
[data-theme="dark"] [data-testid="stFileUploaderDeleteBtn"],
[data-theme="dark"] [data-testid="stFileUploaderFile"] {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

/* Dark Mode Text Area (Disabled OCR Stream & Normal) */
[data-theme="dark"] textarea,
[data-theme="dark"] textarea:disabled,
[data-theme="dark"] .stTextArea textarea,
[data-theme="dark"] .stTextArea textarea:disabled,
[data-theme="dark"] [data-baseweb="textarea"],
[data-theme="dark"] [data-baseweb="textarea"]:disabled,
[data-theme="dark"] [data-baseweb="base-input"],
[data-theme="dark"] [data-baseweb="base-input"]:disabled,
[data-theme="dark"] .stTextArea > div,
[data-theme="dark"] .stTextArea > div > div {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1px solid #1E2E4E !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace !important;
    border-radius: 10px !important;
    -webkit-text-fill-color: #E2E8F0 !important;
    opacity: 1 !important;
}

/* Dark Mode Chat Input */
[data-theme="dark"] [data-testid="stChatInput"],
[data-theme="dark"] [data-testid="stChatInput"] > div,
[data-theme="dark"] [data-testid="stChatInputContainer"],
[data-theme="dark"] [data-testid="stBottomBlockContainer"] {
    background-color: transparent !important;
    background: transparent !important;
    border: none !important;
}

[data-theme="dark"] [data-testid="stChatInput"] [data-baseweb="base-input"],
[data-theme="dark"] [data-testid="stChatInput"] [data-baseweb="input"],
[data-theme="dark"] [data-testid="stChatInput"] div[data-baseweb="base-input"] {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1.5px solid #1E2E4E !important;
    border-radius: 24px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
}

[data-theme="dark"] [data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    background: transparent !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    border: none !important;
    font-size: 0.90rem !important;
    font-family: 'Inter', sans-serif !important;
}

[data-theme="dark"] [data-testid="stChatInput"] textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}

[data-theme="dark"] [data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #2563EB, #06B6D4) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 50% !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4) !important;
}

[data-theme="dark"] [data-testid="stChatInput"] button svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}

/* Dark Mode Chat Messages */
[data-theme="dark"] [data-testid="stChatMessage"],
[data-theme="dark"] .stChatMessage {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
    margin-bottom: 8px !important;
}

[data-theme="dark"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-theme="dark"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-theme="dark"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-theme="dark"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-theme="dark"] [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em {
    color: #E2E8F0 !important;
}

/* Dark Mode Status Widget / Progress Spinners */
[data-theme="dark"] [data-testid="stStatusWidget"],
[data-theme="dark"] details[data-testid="stExpander"] {
    background-color: #111827 !important;
    background: #111827 !important;
    border: 1px solid #1E2E4E !important;
    color: #F8FAFC !important;
    border-radius: 12px !important;
}
[data-theme="dark"] [data-testid="stStatusWidget"] * {
    color: #F8FAFC !important;
}

/* Dark Mode Medication Dialog / Modal */
[data-theme="dark"] div[data-testid="stDialog"] > div,
[data-theme="dark"] div[role="dialog"],
[data-theme="dark"] [data-testid="stModal"] {
    background-color: #0B1220 !important;
    background: #0B1220 !important;
    border: 1.5px solid #1E2E4E !important;
    color: #F8FAFC !important;
    border-radius: 16px !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7) !important;
}
[data-theme="dark"] div[data-testid="stDialog"] header,
[data-theme="dark"] div[role="dialog"] header {
    background-color: #0B1220 !important;
    color: #F8FAFC !important;
    border-bottom: 1px solid #1E293B !important;
}
[data-theme="dark"] div[data-testid="stDialog"] h1,
[data-theme="dark"] div[data-testid="stDialog"] h2,
[data-theme="dark"] div[data-testid="stDialog"] h3,
[data-theme="dark"] div[data-testid="stDialog"] p,
[data-theme="dark"] div[data-testid="stDialog"] span,
[data-theme="dark"] div[data-testid="stDialog"] li,
[data-theme="dark"] div[data-testid="stDialog"] b,
[data-theme="dark"] div[data-testid="stDialog"] strong,
[data-theme="dark"] div[data-testid="stDialog"] em {
    color: #F1F5F9 !important;
}
[data-theme="dark"] div[data-testid="stDialog"] code {
    background-color: #1E293B !important;
    color: #38BDF8 !important;
    padding: 3px 7px !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

/* Quick Question Chip buttons inside Dialog */
[data-theme="dark"] div[data-testid="stDialog"] .stButton > button,
[data-theme="dark"] .st-key-p2_quick_q_0 button,
[data-theme="dark"] .st-key-p2_quick_q_1 button,
[data-theme="dark"] .st-key-p2_quick_q_2 button {
    background-color: #1A2333 !important;
    background: #1A2333 !important;
    color: #94A3B8 !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 6px 10px !important;
    transition: all 0.2s ease !important;
}

[data-theme="dark"] div[data-testid="stDialog"] .stButton > button:hover,
[data-theme="dark"] .st-key-p2_quick_q_0 button:hover,
[data-theme="dark"] .st-key-p2_quick_q_1 button:hover,
[data-theme="dark"] .st-key-p2_quick_q_2 button:hover {
    background-color: #1E293B !important;
    border-color: #3B82F6 !important;
    color: #60A5FA !important;
    transform: translateY(-1px) !important;
}

[data-theme="dark"] .stButton > button {
    background-color: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}


[data-theme="dark"] .mm-btn-primary {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #ffffff !important;
}

[data-theme="dark"] header[data-testid="stHeader"] {
    background-color: #0B1220 !important;
    border-bottom-color: #2563EB !important;
}

[data-theme="dark"] .stRadio label,
[data-theme="dark"] .stCheckbox label {
    color: #CBD5E1 !important;
}

[data-theme="dark"] .stTabs [data-baseweb="tab-list"] {
    background-color: #111827 !important;
    border-bottom-color: #1E293B !important;
}

[data-theme="dark"] .stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
}

[data-theme="dark"] .stTabs [aria-selected="true"] {
    color: #2563EB !important;
    border-bottom-color: #2563EB !important;
}

/* ============================================================
   ANIMATED SUN & MOON DAY/NIGHT TOGGLE SWITCH (BaseWeb & Streamlit)
   ============================================================ */
div[data-testid="stToggle"],
.stToggle {
    display: inline-flex !important;
    align-items: center !important;
}

div[data-testid="stToggle"] label,
div[data-testid="stToggle"] [data-baseweb="checkbox"],
.stToggle label,
.stToggle [data-baseweb="checkbox"] {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
}

/* Switch Outer Track (Day / Sky Blue in Light Mode) */
div[data-testid="stToggle"] label > div:first-of-type,
div[data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-of-type,
div[data-testid="stToggle"] div[data-testid="stToggleSwitch"],
.stToggle label > div:first-of-type,
.stToggle [data-baseweb="checkbox"] > div:first-of-type {
    width: 64px !important;
    height: 32px !important;
    min-width: 64px !important;
    border-radius: 30px !important;
    background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.6) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2), 0 2px 10px rgba(56, 189, 248, 0.4) !important;
    position: relative !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    overflow: visible !important;
}

/* Cloud icon in Day mode */
div[data-testid="stToggle"] label > div:first-of-type::after,
div[data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-of-type::after,
div[data-testid="stToggle"] div[data-testid="stToggleSwitch"]::after,
.stToggle label > div:first-of-type::after,
.stToggle [data-baseweb="checkbox"] > div:first-of-type::after {
    content: "" !important;
    position: absolute !important;
    right: 6px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 13px !important;
    line-height: 1 !important;
    opacity: 0.95 !important;
    pointer-events: none !important;
}

/* Night / Starry Track when checked (Dark Mode) */
div[data-testid="stToggle"]:has(input:checked) label > div:first-of-type,
div[data-testid="stToggle"]:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type,
div[data-testid="stToggle"] input:checked + div,
.stToggle:has(input:checked) label > div:first-of-type,
.stToggle:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%) !important;
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5), 0 2px 10px rgba(99, 102, 241, 0.4) !important;
}

/* Star icon in Night mode */
div[data-testid="stToggle"]:has(input:checked) label > div:first-of-type::after,
div[data-testid="stToggle"]:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type::after,
div[data-testid="stToggle"] input:checked + div::after,
.stToggle:has(input:checked) label > div:first-of-type::after,
.stToggle:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type::after {
    content: "" !important;
    left: 7px !important;
    right: auto !important;
    font-size: 12px !important;
    line-height: 1 !important;
    opacity: 0.95 !important;
    pointer-events: none !important;
}

/* Sun Thumb (Light Mode) */
div[data-testid="stToggle"] label > div:first-of-type > div,
div[data-testid="stToggle"] [data-baseweb="checkbox"] > div:first-of-type > div,
div[data-testid="stToggle"] div[data-testid="stToggleSwitch"] > div,
.stToggle label > div:first-of-type > div,
.stToggle [data-baseweb="checkbox"] > div:first-of-type > div {
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    background: #FBBF24 !important;
    background-image: radial-gradient(circle at 35% 35%, #FEF08A 0%, #F59E0B 100%) !important;
    box-shadow: 0 0 10px #F59E0B, inset -1px -1px 2px rgba(0,0,0,0.2) !important;
    transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    position: relative !important;
    top: 2.5px !important;
    left: 3px !important;
}

/* Moon Thumb (Dark Mode) */
div[data-testid="stToggle"]:has(input:checked) label > div:first-of-type > div,
div[data-testid="stToggle"]:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type > div,
div[data-testid="stToggle"] input:checked + div > div,
.stToggle:has(input:checked) label > div:first-of-type > div,
.stToggle:has(input:checked) [data-baseweb="checkbox"] > div:first-of-type > div {
    background: #E2E8F0 !important;
    background-image: radial-gradient(circle at 35% 35%, #FFFFFF 0%, #94A3B8 100%) !important;
    box-shadow: 0 0 12px rgba(226, 232, 240, 0.8), inset -2px -2px 3px rgba(0,0,0,0.3) !important;
    transform: translateX(31px) !important;
}

/* Global resets & typography */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--mm-bg-base) !important;
    color: var(--mm-text-primary) !important;
    -webkit-font-smoothing: antialiased;
    transition: background-color 0.3s ease, color 0.3s ease !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Manrope', 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: var(--mm-text-primary) !important;
    letter-spacing: -0.02em;
}

/* Hairline Top Brand Accent Bar */
header[data-testid="stHeader"] {
    background-color: var(--mm-bg-surface) !important;
    border-bottom: 2px solid var(--mm-brand-primary) !important;
    display: flex !important;
    align-items: center !important;
    z-index: 9999 !important;
}

/* Hide Streamlit deploy button, hamburger menu & cloud badges (Preserve header & sidebar controls) */
#MainMenu, footer, .stDeployButton, .stAppDeployButton, [data-testid="stAppDeployButton"], button[data-testid="stAppDeployButton"], .viewerBadge_container__r5tak, .viewerBadge_link__qRIco, div[class*="viewerBadge"], [data-testid="stStatusWidget"] { 
    display: none !important; 
    visibility: hidden !important; 
}

/* ==========================================================================
   1B. EQUAL HEIGHT CARDS & FLEX COLUMN ALIGNMENT IN ROWS
   When cards sit in columns (e.g. 3 cards in a row), all cards stretch to equal height.
   ========================================================================== */
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"] > div[data-testid="column"] .mm-card {
    flex: 1 1 100% !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
}

/* ==========================================================================
   1C. MULTI-COLUMN & RESPONSIVE LAYOUT SYSTEM
   ========================================================================== */

/* Button Groups & Chips wrap as an inline tag cloud */
[data-testid="stHorizontalBlock"]:has(.stButton),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-pop_sym_chip_"]),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-chip_"]),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-p2_quick_q_"]),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-qa_"]),
[data-testid="stHorizontalBlock"].mm-keep-horizontal {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 8px !important;
    width: 100% !important;
    overflow-x: visible !important;
}

[data-testid="stHorizontalBlock"]:has(.stButton) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-pop_sym_chip_"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-chip_"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-p2_quick_q_"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-qa_"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"].mm-keep-horizontal > div[data-testid="column"] {
    flex: 0 1 auto !important;
    width: auto !important;
    min-width: 0 !important;
}

/* Ensure chips display neatly as rounded pill chips with proper padding and no broken text */
div[class*="st-key-pop_sym_chip_"] button,
div[class*="st-key-chip_"] button,
div[class*="st-key-p2_quick_q_"] button {
    white-space: nowrap !important;
    border-radius: 20px !important;
    padding: 6px 14px !important;
    font-size: 0.82rem !important;
    min-height: 38px !important;
    width: auto !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ==========================================================================
   1D. THREE-TIER COMPREHENSIVE RESPONSIVE LAYOUT SYSTEM
   Standardized Breakpoints:
     Tier 1 (Tablet):       @media (max-width: 992px)
     Tier 2 (Mobile):       @media (max-width: 767px)
     Tier 3 (Small Phone):  @media (max-width: 568px)
     Tier XL (Widescreen):  @media (min-width: 1440px)
   ========================================================================== */

/* ── BASE: Fluid Containers & Layout Defaults (Desktop ≥ 993px) ── */
.main .block-container,
section.main > div.block-container,
[data-testid="stMainBlockContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: clamp(14px, 3vw, 40px) !important;
    padding-right: clamp(14px, 3vw, 40px) !important;
    padding-top: clamp(12px, 2vw, 28px) !important;
    padding-bottom: 60px !important;
    box-sizing: border-box !important;
}

.stApp {
    min-height: 100vh !important;
    min-height: 100dvh !important;
    overflow-x: hidden !important;
}

section.main,
[data-testid="stMain"] {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    overflow-x: hidden !important;
    width: 100% !important;
}

/* Fluid images, media, and tables */
img, svg, video, pre {
    max-width: 100% !important;
    height: auto !important;
    box-sizing: border-box !important;
}

iframe {
    max-width: 100% !important;
    box-sizing: border-box !important;
    border-radius: 12px !important;
}

/* Responsive Table & Scroll Containers */
.table-responsive,
.mm-table-container,
div[style*="overflow-x"] {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    max-width: 100% !important;
}

/* Fluid Cards & Metric Blocks */
.mm-card,
.mm-hospital-card,
[data-testid="stMetric"] {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* Plotly & Altair Charts fluid fit */
[data-testid="stPlotlyChart"],
[data-testid="stAltairChart"],
[data-testid="element-container"] iframe {
    width: 100% !important;
    max-width: 100% !important;
    overflow: hidden !important;
}

/* Sidebar: fluid width */
[data-testid="stSidebar"] > div:first-child {
    width: clamp(220px, 22vw, 280px) !important;
    max-width: 280px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

[data-testid="stSidebar"] {
    white-space: normal !important;
    word-break: break-word !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    white-space: normal !important;
    word-break: break-word !important;
}

/* Multi-column grid utility classes */
.mm-grid-2col {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    align-items: stretch;
}

.mm-grid-4col {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 130px), 1fr));
    gap: 12px;
}

.mm-grid-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
    gap: 14px;
}

/* ── TIER XL: Widescreen (≥ 1440px) ── */
@media (min-width: 1440px) {
    .main .block-container,
    section.main > div.block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: clamp(32px, 4vw, 64px) !important;
        padding-right: clamp(32px, 4vw, 64px) !important;
    }
    .mm-hospital-card {
        min-height: 210px !important;
        height: 210px !important;
    }
    div[class*="st-key-mm_top_header_card"] {
        padding: 24px 36px !important;
        min-height: 100px !important;
    }
}

/* ── TIER 1: TABLET (≤ 992px) ── */
@media (max-width: 992px) {
    .main .block-container,
    section.main > div.block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: clamp(14px, 3vw, 24px) !important;
        padding-right: clamp(14px, 3vw, 24px) !important;
        padding-top: 14px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: clamp(200px, 26vw, 250px) !important;
        max-width: 250px !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label,
    [data-testid="stSidebar"] div[role="radiogroup"] label p,
    [data-testid="stSidebar"] div[role="radiogroup"] label span {
        font-size: 0.82rem !important;
        padding: 8px 10px !important;
    }

    /* 4-column KPI / bordered blocks reduce to 2 columns on tablet */
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        width: 100% !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="stColumn"] {
        flex: 1 1 calc(50% - 12px) !important;
        min-width: 220px !important;
        max-width: calc(50% - 6px) !important;
        box-sizing: border-box !important;
    }

    .mm-hospital-card {
        min-height: 195px !important;
        height: auto !important;
    }

    div[class*="st-key-mm_top_header_card"] {
        padding: 16px 20px !important;
        min-height: 80px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.84rem !important;
        padding: 8px 14px !important;
    }

    div[data-testid="stDialog"] > div[role="dialog"],
    div[role="dialog"] {
        width: min(1160px, 95vw) !important;
        max-width: 95vw !important;
        padding: 20px 22px !important;
    }

    .floating-chat-container {
        width: min(420px, 90vw) !important;
        right: 16px !important;
        bottom: 16px !important;
    }
}

/* ── TIER 2: MOBILE (≤ 767px) ── */
@media (max-width: 767px) {
    .main .block-container,
    section.main > div.block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: 12px !important;
        padding-right: 12px !important;
        padding-top: 10px !important;
        padding-bottom: 84px !important;
    }

    /* Major cards, file uploaders, OCR textareas, plotly charts stack to 100% width */
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]),
    [data-testid="stHorizontalBlock"]:has(.stFileUploader),
    [data-testid="stHorizontalBlock"]:has(.stTextArea),
    [data-testid="stHorizontalBlock"]:has(.stPlotlyChart) {
        display: flex !important;
        flex-direction: column !important;
        flex-wrap: wrap !important;
        gap: 14px !important;
        width: 100% !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"]:has(.stFileUploader) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:has(.stFileUploader) > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:has(.stTextArea) > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"]:has(.stPlotlyChart) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:has(.stPlotlyChart) > [data-testid="stColumn"] {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        box-sizing: border-box !important;
    }

    /* 2-column grids collapse to 1 column */
    .mm-grid-2col {
        grid-template-columns: 1fr !important;
        gap: 12px !important;
    }

    .mm-doc-selector-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }

    .mm-hospital-grid {
        grid-template-columns: 1fr !important;
        gap: 12px !important;
    }

    /* Radio buttons wrap without truncation */
    .stRadio div[role="radiogroup"] label {
        white-space: normal !important;
        word-break: break-word !important;
        min-height: 40px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Minimum Accessible Tap Targets (≥44px) on Mobile */
    .stButton > button {
        min-height: 44px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
    }

    div[class*="st-key-drawer_clear_chat_btn"] button,
    div[class*="st-key-drawer_close_x_btn"] button,
    .st-key-drawer_clear_chat_btn button,
    .st-key-drawer_close_x_btn button,
    button[aria-label*="audio"],
    button[aria-label*="record"],
    button[aria-label*="mic"] {
        min-width: 44px !important;
        min-height: 44px !important;
    }

    /* Form labels & Inputs */
    .stTextInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stRadio label,
    .stSlider label,
    .stFileUploader label,
    div[data-testid="stWidgetLabel"] label,
    div[data-testid="stWidgetLabel"] p {
        font-size: 0.78rem !important;
        margin-bottom: 2px !important;
        word-break: break-word !important;
    }

    .stTextInput input,
    [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] > div:first-child {
        font-size: 0.82rem !important;
        min-height: 38px !important;
        height: 38px !important;
        padding: 0 8px !important;
    }

    .stTextArea textarea {
        font-size: 0.82rem !important;
        min-height: 140px !important;
        height: auto !important;
        line-height: 1.45 !important;
        padding: 8px 10px !important;
    }

    /* Tabs mobile layout */
    .stTabs [data-baseweb="tab-list"] {
        padding-bottom: 2px !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 0.80rem !important;
        min-height: 44px !important;
    }

    /* Floating Chat container on mobile */
    .floating-chat-container {
        width: min(380px, 96vw) !important;
        right: 8px !important;
        bottom: 8px !important;
    }

    /* Stepper Component */
    .mm-stepper {
        padding: 8px 8px !important;
        overflow-x: hidden !important;
        gap: 2px !important;
        justify-content: space-between !important;
        margin-bottom: 14px !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    .mm-stepper::-webkit-scrollbar {
        display: none !important;
    }
    .mm-step-item {
        flex: 1 1 auto !important;
        gap: 5px !important;
        min-width: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    .mm-step-text-sub {
        display: none !important;
    }
    .mm-step-text-title {
        font-size: 0.70rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1.1 !important;
    }
    .mm-step-num {
        width: 25px !important;
        height: 25px !important;
        font-size: 0.75rem !important;
        flex-shrink: 0 !important;
    }
    .mm-step-connector {
        flex: 0 1 14px !important;
        padding: 0 !important;
        gap: 0 !important;
        justify-content: center !important;
    }
    .mm-step-line {
        display: none !important;
    }
    .mm-step-arrow {
        font-size: 0.68rem !important;
        padding: 0 !important;
        color: #94A3B8 !important;
        flex-shrink: 0 !important;
    }
}

/* ── TIER 3: SMALL PHONE (≤ 568px) ── */
@media (max-width: 568px) {
    .main .block-container,
    section.main > div.block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: 8px !important;
        padding-right: 8px !important;
        padding-top: 8px !important;
        padding-bottom: 88px !important;
    }

    /* All multi-column horizontal blocks stack vertically on small phone */
    [data-testid="stHorizontalBlock"]:not(.mm-keep-horizontal):not(:has(div[class*="st-key-chip_"])):not(:has(div[class*="st-key-pop_sym_chip_"])):not(:has(div[class*="st-key-p2_quick_q_"])):not(:has(div[class*="st-key-dyn_chip_"])) {
        flex-direction: column !important;
        flex-wrap: wrap !important;
        gap: 10px !important;
        width: 100% !important;
    }
    [data-testid="stHorizontalBlock"]:not(.mm-keep-horizontal):not(:has(div[class*="st-key-chip_"])):not(:has(div[class*="st-key-pop_sym_chip_"])):not(:has(div[class*="st-key-p2_quick_q_"])):not(:has(div[class*="st-key-dyn_chip_"])) > [data-testid="column"],
    [data-testid="stHorizontalBlock"]:not(.mm-keep-horizontal):not(:has(div[class*="st-key-chip_"])):not(:has(div[class*="st-key-pop_sym_chip_"])):not(:has(div[class*="st-key-p2_quick_q_"])):not(:has(div[class*="st-key-dyn_chip_"])) > [data-testid="stColumn"] {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }

    /* Chip rows and badge clouds wrap inline */
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-chip_"]),
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-pop_sym_chip_"]),
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-p2_quick_q_"]),
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-dyn_chip_"]) {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
    }

    .mm-doc-selector-grid {
        grid-template-columns: 1fr !important;
        gap: 6px !important;
    }

    .mm-grid-4col {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }

    .mm-hospital-card {
        min-height: 165px !important;
        height: auto !important;
        padding: 12px 14px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.74rem !important;
        padding: 6px 8px !important;
    }

    div[data-testid="stDialog"] > div[role="dialog"],
    div[role="dialog"] {
        width: 98vw !important;
        max-width: 98vw !important;
        padding: 14px 12px !important;
        border-radius: 14px !important;
    }

    .floating-chat-container {
        width: 96vw !important;
        right: 2vw !important;
        bottom: 6px !important;
    }
}

/* ── Utility: smooth viewport transitions ── */
.stApp,
.main .block-container,
[data-testid="stSidebar"],
[data-testid="stHorizontalBlock"],
.mm-card,
.mm-hospital-card {
    transition: padding 0.2s ease, width 0.2s ease !important;
}

/* ==========================================================================
   2. SIDEBAR - TOGGLE BUTTONS & NAVIGATION PANEL
   ========================================================================== */

/* All Sidebar Open / Expand Toggle Controls */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
header button[kind="header"],
header button[kind="headerNoPadding"],
header button[data-testid*="Collapse"],
header button[data-testid*="Expand"],
header [data-testid="stSidebarNavCollapseButton"] {
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #2563EB !important;
    background-color: rgba(37, 99, 235, 0.08) !important;
    border: 1px solid rgba(37, 99, 235, 0.3) !important;
    border-radius: 6px !important;
    margin-left: 8px !important;
}

[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
header button[kind="header"] svg,
header button[kind="headerNoPadding"] svg {
    fill: #2563EB !important;
    color: #2563EB !important;
    width: 22px !important;
    height: 22px !important;
}

/* Sidebar Close Button inside Dark Sidebar */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] svg {
    fill: #F8FAFC !important;
    color: #F8FAFC !important;
    width: 22px !important;
    height: 22px !important;
}

[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B !important;
    overflow: hidden !important;
    overflow-x: hidden !important;
    flex-shrink: 0 !important;
    /* NO min-width here — Streamlit sets width:0 when collapsing; min-width would block that */
}

/* Inner content div: THIS is where we set the sidebar's visible width */
[data-testid="stSidebar"] > div:first-child {
    width: clamp(220px, 22vw, 280px) !important;
    max-width: 280px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    padding-top: clamp(10px, 1.8vw, 20px) !important;
    padding-left: 12px !important;
    padding-right: 12px !important;
    box-sizing: border-box !important;
    width: 100% !important;
    overflow-x: hidden !important;
}

[data-testid="stSidebarHeader"] {
    padding-top: 2px !important;
    padding-bottom: 2px !important;
    padding-left: 12px !important;
    padding-right: 12px !important;
    height: auto !important;
    min-height: 0 !important;
    box-sizing: border-box !important;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] b {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Sidebar Selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: var(--mm-radius-md) !important;
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #94A3B8 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #F8FAFC !important;
    font-weight: 500 !important;
}

/* Sidebar Radio Navigation Cards */
[data-testid="stSidebar"] [data-testid="stRadio"],
[data-testid="stSidebar"] .stRadio,
[data-testid="stSidebar"] div[role="radiogroup"] {
    width: 100% !important;
    max-width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    background-color: #141D2E !important;
    border: 1.2px solid #23324D !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    min-height: 42px !important;
    overflow: hidden !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background-color: #1E293B !important;
    border-color: #38BDF8 !important;
    transform: translateX(2px) !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(37, 99, 235, 0.35) 0%, rgba(6, 182, 212, 0.18) 100%) !important;
    border-left: 4px solid #2563EB !important;
    border-color: #2563EB !important;
    box-shadow: 0 2px 10px rgba(37, 99, 235, 0.28) !important;
}

/* Hide native radio input and SVG circle icon */
[data-testid="stSidebar"] div[role="radiogroup"] label input[type="radio"] {
    display: none !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label svg {
    display: none !important;
}

/* Hide radio circle dot wrapper (only when there are multiple child divs) */
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child:not(:last-child) {
    display: none !important;
}

/* Text visibility inside sidebar navigation */
[data-testid="stSidebar"] div[role="radiogroup"] label,
[data-testid="stSidebar"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div[role="radiogroup"] label p,
[data-testid="stSidebar"] div[role="radiogroup"] label span,
[data-testid="stSidebar"] div[role="radiogroup"] label div {
    color: #F8FAFC !important;
    font-size: 0.87rem !important;
    font-weight: 600 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    line-height: 1.2 !important;
    min-width: 0 !important;
    max-width: 100% !important;
    flex: 1 1 0% !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Keep the theme toggle visually consistent with the rest of the
   sidebar (was floating with no card/spacing around it). */
[data-testid="stSidebar"] [data-testid="stToggle"] {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}

[data-testid="stSidebar"] .stSelectbox {
    margin-bottom: 4px !important;
}

/* ==========================================================================
   3. STREAMLIT FORM CONTROLS & WIDGET RESTYLING
   ========================================================================== */

/* Buttons */
.stButton > button,
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background-color: var(--mm-brand-primary) !important;
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border: 1px solid var(--mm-brand-primary) !important;
    border-radius: var(--mm-radius-md) !important;
    padding: 0.65rem 1.4rem !important;
    box-shadow: 0 1px 3px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.18s ease-in-out !important;
}

.stButton > button:hover,
button[kind="primary"]:hover {
    background-color: var(--mm-brand-hover) !important;
    border-color: var(--mm-brand-hover) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
}

.stButton > button:active,
button[kind="primary"]:active {
    background-color: var(--mm-brand-active) !important;
    transform: translateY(0px) !important;
}

.stDownloadButton > button {
    background-color: #FFFFFF !important;
    color: var(--mm-brand-primary) !important;
    border: 1.5px solid var(--mm-brand-primary) !important;
    border-radius: var(--mm-radius-md) !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.18s ease !important;
}

.stDownloadButton > button:hover {
    background-color: var(--mm-brand-subtle) !important;
    color: var(--mm-brand-hover) !important;
    transform: translateY(-1px) !important;
}

/* Equal Action & Hospital Card Action Buttons */
div[data-testid="stColumn"] div[data-testid="stButton"] button,
div[data-testid="stColumn"] div[data-testid="stDownloadButton"] button,
div[data-testid="stColumn"] .stButton > button,
div[data-testid="stColumn"] .stDownloadButton > button,
div[data-testid="stColumn"] div[data-testid="stLinkButton"] a {
    min-height: 38px !important;
    height: 38px !important;
    max-height: 38px !important;
    padding: 0 12px !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    box-sizing: border-box !important;
    text-decoration: none !important;
    width: 100% !important;
    line-height: 1 !important;
}

div[data-testid="stColumn"] div[data-testid="stLinkButton"] a {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1.5px solid #CBD5E1 !important;
}

div[data-testid="stColumn"] div[data-testid="stLinkButton"] a:hover {
    background-color: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
    transform: translateY(-1px) !important;
}

/* -- Verified Healthcare Facility Card -- */
.mm-hospital-card {
    background: #FFFFFF !important;
    border: 1.2px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    min-height: 220px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}

.mm-hospital-card:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08) !important;
    transform: translateY(-1px) !important;
}

.mm-fac-dist-badge {
    background: #EFF6FF !important;
    border: 1.2px solid #BAE6FD !important;
    border-radius: 999px !important;
    padding: 3px 10px !important;
    font-size: 0.78rem !important;
    font-weight: 800 !important;
    color: #0284C7 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
    white-space: nowrap !important;
}

.mm-fac-active-badge {
    background: #ECFDF5 !important;
    border: 1.2px solid #86EFAC !important;
    border-radius: 999px !important;
    padding: 4px 12px !important;
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    color: #059669 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    letter-spacing: 0.3px !important;
    text-transform: uppercase !important;
}

.mm-gis-action-row {
    margin-top: 8px;
    margin-bottom: 22px;
}

.mm-gis-action-row .stButton > button {
    height: 38px !important;
    min-height: 38px !important;
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #2563EB !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
}

.mm-gis-action-row .stLinkButton > a {
    height: 38px !important;
    min-height: 38px !important;
    background-color: #FFFFFF !important;
    border: 1.2px solid #CBD5E1 !important;
    color: #1E293B !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.mm-gis-action-row .stLinkButton > a:hover {
    background-color: #F8FAFC !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Form Field Labels */
.stTextInput label,
.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stFileUploader label,
.stTextArea label {
    font-size: 0.84rem !important;
    color: #475569 !important;
    font-weight: 600 !important;
    margin-bottom: 6px !important;
    letter-spacing: 0.01em !important;
}

/* Text Inputs, Selectboxes, Multiselects & Textareas */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
[data-baseweb="select"] > div {
    background-color: var(--mm-bg-surface) !important;
    border: 1.5px solid var(--mm-border-color) !important;
    border-radius: 8px !important;
    color: var(--mm-text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 2px 6px !important;
}

/* Conditions Multiselect Custom Dropdown Styling */
div[class*="st-key-selected_conditions_widget"] input {
    caret-color: transparent !important;
    cursor: pointer !important;
}
div[class*="st-key-selected_conditions_widget"] input::placeholder {
    color: transparent !important;
    opacity: 0 !important;
}

/* Header Compact Pill Language Dropdown (Rounded on Both Sides) */
div[class*="st-key-hdr_lang_"] [data-baseweb="select"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[class*="st-key-hdr_lang_"] [data-baseweb="select"] > div {
    border-radius: 9999px !important;
    min-height: 36px !important;
    height: 36px !important;
    font-size: 0.82rem !important;
    padding: 0 10px 0 14px !important;
    border: 1.5px solid var(--mm-border-color) !important;
    background: var(--mm-bg-surface) !important;
    color: var(--mm-text-primary) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    display: flex !important;
    align-items: center !important;
}

div[class*="st-key-hdr_lang_"] [data-baseweb="select"] span {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--mm-text-primary) !important;
}

div[class*="st-key-hdr_lang_"] {
    width: 100% !important;
    max-width: 160px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}
div[class*="st-key-hdr_lang_"] .stSelectbox {
    margin: 0 !important;
    padding: 0 !important;
}

/* Modal Dialog: Backdrop — full-screen centered overlay */
div[data-testid="stDialog"],
div[data-modal-container="true"] {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 9999 !important;
}

/* Ghost card killer: Streamlit's internal border wrappers inside dialogs */
div[data-testid="stDialog"] > div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stDialog"] > div[data-testid="stVerticalBlock"],
div[data-testid="stDialog"] > [data-testid],
div[data-modal-container="true"] > div[data-testid="stVerticalBlockBorderWrapper"],
div[data-modal-container="true"] > div[data-testid="stVerticalBlock"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    max-width: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 0 !important;
}

/* Modal Dialog: Large Landscape Layout — scoped ONLY to div[role="dialog"] */
div[data-testid="stDialog"] div[role="dialog"],
div[role="dialog"],
section[role="dialog"],
div[data-modal-container="true"] div[role="dialog"] {
    position: relative !important;
    max-width: 1220px !important;
    width: min(1220px, 94vw) !important;
    min-width: unset !important;
    margin: auto !important;
    left: unset !important;
    top: unset !important;
    transform: none !important;
    border-radius: 20px !important;
    padding: 24px 28px !important;
    background: var(--mm-bg-surface) !important;
    border: 1.5px solid var(--mm-border-color) !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35) !important;
    box-sizing: border-box !important;
}

/* Small dialogs (Profile Actions, confirm etc.) — compact override */
div[data-testid="stDialog"][data-size="small"] div[role="dialog"] {
    max-width: min(480px, 92vw) !important;
    width: min(480px, 92vw) !important;
    padding: 1.25rem 1.4rem !important;
    border-radius: 18px !important;
}

@media (max-width: 768px) {
    div[data-testid="stDialog"] div[role="dialog"],
    div[data-testid="stDialog"] > div,
    div[role="dialog"],
    section[role="dialog"],
    div[data-modal-container="true"] > div,
    .stDialog > div > div {
        max-width: 96vw !important;
        width: 96vw !important;
        min-width: unset !important;
        padding: 16px 12px !important;
        margin: auto !important;
        border-radius: 16px !important;
    }
}


.mm-badge-online-pill {
    background: #F0FDF4 !important;
    color: #166534 !important;
    border: 1.5px solid #DCFCE7 !important;
    border-radius: 9999px !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    padding: 0 14px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    white-space: nowrap !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    height: 36px !important;
    line-height: 36px !important;
    box-sizing: border-box !important;
}

/* Unified Top Header Card Container */
div[class*="st-key-mm_top_header_card"] {
    background: var(--mm-bg-surface) !important;
    border: 1.5px solid var(--mm-border-color) !important;
    border-radius: 20px !important;
    padding: 20px 28px !important;
    box-shadow: var(--mm-shadow-card) !important;
    margin-bottom: 20px !important;
    min-height: 92px !important;
    display: flex !important;
    align-items: center !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    width: 100% !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 14px !important;
    width: 100% !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stColumn"],
div[class*="st-key-mm_top_header_card"] [data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: stretch !important;
    margin: auto 0 !important;
    padding: 0 !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stVerticalBlockBorderWrapper"],
div[class*="st-key-mm_top_header_card"] [data-testid="stColumn"] > div,
div[class*="st-key-mm_top_header_card"] [data-testid="column"] > div {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: stretch !important;
    height: 100% !important;
    margin: auto 0 !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stColumn"] [data-testid="stVerticalBlock"],
div[class*="st-key-mm_top_header_card"] [data-testid="column"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    height: 100% !important;
    gap: 0 !important;
    padding: 0 !important;
    margin: auto 0 !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stColumn"]:first-child [data-testid="stVerticalBlock"],
div[class*="st-key-mm_top_header_card"] [data-testid="column"]:first-child [data-testid="stVerticalBlock"] {
    align-items: flex-start !important;
    justify-content: center !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="element-container"],
div[class*="st-key-mm_top_header_card"] .element-container {
    margin: auto 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stColumn"]:first-child [data-testid="element-container"],
div[class*="st-key-mm_top_header_card"] [data-testid="column"]:first-child [data-testid="element-container"] {
    justify-content: flex-start !important;
}

div[class*="st-key-mm_top_header_card"] [data-testid="stCustomComponentV1"],
div[class*="st-key-hdr_sun_moon_"] [data-testid="stCustomComponentV1"],
div[class*="st-key-hdr_sun_moon_"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    width: 100% !important;
    margin: auto 0 !important;
    padding: 0 !important;
}

div[class*="st-key-mm_top_header_card"] iframe,
div[class*="st-key-hdr_sun_moon_"] iframe {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    border: none !important;
    display: block !important;
    margin: auto !important;
    padding: 0 !important;
    vertical-align: middle !important;
}

@media (max-width: 992px) {
    div[class*="st-key-mm_top_header_card"] {
        padding: 16px 20px !important;
        border-radius: 18px !important;
        min-height: 80px !important;
    }
}

@media (max-width: 767px) {
    div[class*="st-key-mm_top_header_card"] {
        padding: 14px 16px !important;
        border-radius: 16px !important;
        margin-bottom: 14px !important;
        min-height: auto !important;
    }
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 10px 8px !important;
        width: 100% !important;
    }
    /* Row 1: Title & Icon takes full width */
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child,
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
        margin-bottom: 4px !important;
    }
    div[class*="st-key-mm_top_header_card"] img {
        max-width: 44px !important;
        width: 44px !important;
        height: auto !important;
        padding: 4px !important;
        border-radius: 12px !important;
        flex-shrink: 0 !important;
    }
    div[class*="st-key-mm_top_header_card"] div[style*="font-size: 1.45rem"] {
        font-size: 1.15rem !important;
        line-height: 1.25 !important;
        font-weight: 800 !important;
        word-break: break-word !important;
    }
    div[class*="st-key-mm_top_header_card"] div[style*="font-size: 0.85rem"] {
        font-size: 0.76rem !important;
        line-height: 1.25 !important;
        margin-top: 2px !important;
        display: block !important;
        word-break: break-word !important;
    }

    /* Row 2: Controls row (Badge on left, Language & Theme Switch on right) */
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
        flex: 0 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    div[class*="st-key-mm_top_header_card"] .mm-badge,
    div[class*="st-key-mm_top_header_card"] .mm-badge-brand,
    div[class*="st-key-mm_top_header_card"] .mm-badge-online-pill {
        font-size: 0.70rem !important;
        font-weight: 700 !important;
        padding: 0 10px !important;
        height: 36px !important;
        min-height: 36px !important;
        line-height: 36px !important;
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
    }

    /* Language selector - pushed to the right alongside theme toggle */
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3),
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(3) {
        flex: 0 0 86px !important;
        width: 86px !important;
        min-width: 86px !important;
        margin-left: auto !important;
    }
    div[class*="st-key-mm_top_header_card"] .stSelectbox [data-baseweb="select"] > div:first-child {
        min-height: 38px !important;
        height: 38px !important;
        padding: 0 6px !important;
        font-size: 0.78rem !important;
    }

    /* Sun / Moon switch - full 78px width with >=44px touch target container */
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4),
    div[class*="st-key-mm_top_header_card"] [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) {
        flex: 0 0 78px !important;
        width: 78px !important;
        min-width: 78px !important;
        min-height: 44px !important;
    }
    div[class*="st-key-mm_top_header_card"] [data-testid="stCustomComponentV1"],
    div[class*="st-key-mm_top_header_card"] iframe,
    div[class*="st-key-hdr_sun_moon_"] [data-testid="stCustomComponentV1"],
    div[class*="st-key-hdr_sun_moon_"] iframe {
        height: 40px !important;
        min-height: 40px !important;
        max-height: 44px !important;
        width: 78px !important;
        min-width: 78px !important;
        border: none !important;
        display: block !important;
        margin: 0 auto !important;
    }
}

@media (max-width: 568px) {
    div[class*="st-key-mm_top_header_card"] {
        padding: 10px 12px !important;
        border-radius: 14px !important;
    }
    div[class*="st-key-mm_top_header_card"] img {
        max-width: 38px !important;
        width: 38px !important;
        height: auto !important;
        padding: 3px !important;
    }
    div[class*="st-key-mm_top_header_card"] div[style*="font-size: 1.45rem"] {
        font-size: 1.02rem !important;
    }
    div[class*="st-key-mm_top_header_card"] div[style*="font-size: 0.85rem"] {
        font-size: 0.72rem !important;
    }
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
[data-baseweb="select"]:focus-within > div {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.12) !important;
}

/* Read-only & Disabled Text Areas for OCR Stream */
.stTextArea textarea:disabled,
.stTextArea textarea[disabled],
[data-baseweb="textarea"] textarea:disabled,
[data-baseweb="textarea"] textarea[disabled] {
    opacity: 1 !important;
    cursor: text !important;
    user-select: text !important;
    -webkit-text-fill-color: var(--mm-text-primary) !important;
    color: var(--mm-text-primary) !important;
    background-color: rgba(248, 250, 252, 0.7) !important;
    border-color: #CBD5E1 !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    font-size: 0.84rem !important;
    line-height: 1.5 !important;
}
[data-theme="dark"] .stTextArea textarea:disabled,
[data-theme="dark"] .stTextArea textarea[disabled],
[data-dark-mode="true"] .stTextArea textarea:disabled,
[data-dark-mode="true"] .stTextArea textarea[disabled] {
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    border-color: #1E2E4E !important;
}

/* Multiselect Tag Chips */
[data-baseweb="tag"] {
    background-color: var(--mm-brand-subtle) !important;
    border: 1px solid rgba(37, 99, 235, 0.3) !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}

[data-baseweb="tag"] span {
    color: var(--mm-brand-primary) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* Sliders */
.stSlider div[data-baseweb="slider"] div[role="slider"] {
    background-color: var(--mm-brand-primary) !important;
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 0 0 2px var(--mm-brand-primary) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid var(--mm-border-color) !important;
    gap: 8px !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    flex-wrap: nowrap !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    position: relative !important;
    max-width: 100% !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    color: var(--mm-text-secondary) !important;
    padding: 10px 18px !important;
    border-radius: var(--mm-radius-md) var(--mm-radius-md) 0 0 !important;
    transition: all 0.18s ease !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
    min-height: 44px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--mm-brand-primary) !important;
    background-color: rgba(37, 99, 235, 0.04) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--mm-brand-primary) !important;
    border-bottom: 3px solid var(--mm-brand-primary) !important;
}

@media (max-width: 767px) {
    .stTabs [data-baseweb="tab-list"] {
        padding-bottom: 2px !important;
        mask-image: linear-gradient(to right, black calc(100% - 28px), transparent 100%);
        -webkit-mask-image: linear-gradient(to right, black calc(100% - 28px), transparent 100%);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 0.82rem !important;
        min-height: 44px !important;
    }
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: var(--mm-bg-surface) !important;
    border: 1px solid var(--mm-border-color) !important;
    border-radius: var(--mm-radius-lg) !important;
    padding: 16px 20px !important;
    box-shadow: var(--mm-shadow-subtle) !important;
}

[data-testid="stMetricLabel"] {
    color: var(--mm-text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
}

[data-testid="stMetricValue"] {
    color: var(--mm-text-primary) !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.8rem !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: var(--mm-bg-surface) !important;
    border: 1px solid var(--mm-border-color) !important;
    border-radius: var(--mm-radius-md) !important;
    font-weight: 600 !important;
    color: var(--mm-text-primary) !important;
    padding: 12px 18px !important;
}

.streamlit-expanderContent {
    background-color: var(--mm-bg-surface) !important;
    border: 1px solid var(--mm-border-color) !important;
    border-top: none !important;
    border-radius: 0 0 var(--mm-radius-md) var(--mm-radius-md) !important;
    padding: 18px !important;
}

/* File Uploader */
[data-testid="stFileUploader"] {
    background-color: var(--mm-bg-surface) !important;
    border: 1.5px dashed var(--mm-border-color) !important;
    border-radius: var(--mm-radius-lg) !important;
    padding: 16px !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--mm-brand-primary) !important;
}

/* ==========================================================================
   4. CUSTOM ENTERPRISE CLINICAL CARDS & UI COMPONENTS (.mm-*)
   ========================================================================== */

/* Top Breadcrumb / Header Bar */
.mm-header-bar {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 16px;
    padding: 16px 22px;
    margin-bottom: 20px;
    box-shadow: var(--mm-shadow-card);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}

.mm-header-title {
    margin: 0;
    font-size: 1.45rem;
    font-weight: 800;
    color: var(--mm-text-primary);
    display: flex;
    align-items: center;
    gap: 10px;
}

.mm-header-subtitle {
    margin: 4px 0 0 0;
    font-size: 0.88rem;
    color: var(--mm-text-secondary);
}

/* -- Modern Stepper Component -- */
.mm-stepper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 16px;
    padding: 14px 24px;
    margin-bottom: 22px;
    box-shadow: var(--mm-shadow-subtle);
}

.mm-step-item {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    flex: 1;
}

.mm-step-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    font-weight: 800;
    background: rgba(59, 130, 246, 0.12);
    color: #3B82F6;
    border: 1.5px solid rgba(59, 130, 246, 0.3);
    flex-shrink: 0;
    transition: all 0.2s ease;
}

.mm-step-num.active {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    color: #FFFFFF;
    border-color: #2563EB;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.mm-step-num.done {
    background: #10B981;
    color: #FFFFFF;
    border-color: #059669;
}

.mm-step-text-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--mm-text-primary);
    line-height: 1.2;
}

.mm-step-text-title.active {
    color: #2563EB;
}

.mm-step-text-sub {
    font-size: 0.74rem;
    color: var(--mm-text-secondary);
    margin-top: 2px;
}

.mm-step-connector {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 0 1 70px;
    padding: 0 4px;
}

.mm-step-line {
    height: 1.5px;
    flex: 1;
    background: #CBD5E1;
    border-radius: 1px;
}

.mm-step-arrow {
    color: var(--mm-text-muted);
    font-size: 1.1rem;
    padding: 0 4px;
    flex-shrink: 0;
}

[data-theme="dark"] .mm-step-line {
    background: #334155 !important;
}

@media (max-width: 767px) {
    .mm-stepper {
        padding: 8px 8px !important;
        overflow-x: hidden !important;
        gap: 2px !important;
        justify-content: space-between !important;
        margin-bottom: 14px !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    .mm-stepper::-webkit-scrollbar {
        display: none !important;
    }
    .mm-step-item {
        flex: 1 1 auto !important;
        gap: 5px !important;
        min-width: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    .mm-step-text-sub {
        display: none !important;
    }
    .mm-step-text-title {
        font-size: 0.70rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1.1 !important;
    }
    .mm-step-num {
        width: 25px !important;
        height: 25px !important;
        font-size: 0.75rem !important;
        flex-shrink: 0 !important;
    }
    .mm-step-connector {
        flex: 0 1 14px !important;
        padding: 0 !important;
        gap: 0 !important;
        justify-content: center !important;
    }
    .mm-step-line {
        display: none !important;
    }
    .mm-step-arrow {
        font-size: 0.68rem !important;
        padding: 0 !important;
        color: #94A3B8 !important;
        flex-shrink: 0 !important;
    }
}

/* -- Panel Card Surface -- */
.mm-card {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 20px;
    box-shadow: var(--mm-shadow-card);
    color: var(--mm-text-primary);
}

.mm-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid var(--mm-border-color);
}

.mm-card-title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--mm-text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
}

/* -- Panel 1 Robot Assistant Widget Card -- */
.mm-robot-card {
    background: linear-gradient(145deg, #0A1128 0%, #101F42 60%, #0F172A 100%);
    border: 1.5px solid #1E293B;
    border-radius: 18px;
    padding: 20px;
    color: #FFFFFF;
    margin-bottom: 18px;
    box-shadow: 0 12px 30px rgba(10, 17, 40, 0.4);
    position: relative;
    overflow: hidden;
}

.mm-robot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.mm-speech-bubble {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 14px 16px;
    color: #F1F5F9;
    font-size: 0.85rem;
    line-height: 1.45;
    margin: 12px 0 16px 0;
    backdrop-filter: blur(8px);
}

/* -- Quick Action Cards -- */
.mm-quick-action-item {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
    cursor: pointer;
    text-decoration: none;
    color: var(--mm-text-primary);
}

.mm-quick-action-item:hover {
    border-color: #3B82F6;
    background: var(--mm-border-light);
    transform: translateX(3px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
}

/* -- Document Type Pill Selector (Panel 2) -- */
.mm-doc-selector-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}

.mm-doc-pill {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 14px;
    padding: 14px 12px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: var(--mm-text-primary);
}

.mm-doc-pill.active {
    border-color: #2563EB;
    background: var(--mm-brand-subtle);
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

/* -- OCR Text Stream Box -- */
.mm-ocr-box {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 12px;
    padding: 14px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.82rem;
    color: var(--mm-text-primary);
    line-height: 1.5;
    min-height: 180px;
}

/* -- BioPortal Ontology Badges -- */
.mm-ontology-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.mm-ontology-pill {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 10px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--mm-text-primary);
}

/* -- Facility / Hospital Cards Grid (Panel 3) -- */
.mm-hospital-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
    margin-top: 14px;
}

.mm-hospital-card {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
    color: var(--mm-text-primary);
    min-height: 200px;
    box-sizing: border-box;
}

.mm-hospital-card:hover {
    border-color: #2563EB;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12);
}

.mm-cond-card {
    background: var(--mm-bg-surface);
    border: 1.5px solid var(--mm-border-color);
    border-top: 3.5px solid #2563EB;
    border-radius: 16px;
    padding: 16px 18px;
    margin-top: 4px;
    min-height: 185px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.mm-cond-card:hover {
    border-color: #3B82F6;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
}

.mm-fac-dist-badge {
    background: #E0F2FE;
    color: #0284C7;
    border: 1px solid #BAE6FD;
    border-radius: 999px;
    padding: 3px 9px;
    font-size: 0.74rem;
    font-weight: 800;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
}

.mm-fac-active-badge {
    background: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 0.72rem;
    font-weight: 800;
}

.mm-cond-card {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    height: 100%;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-sizing: border-box;
}
.mm-cond-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
    border-color: rgba(37, 99, 235, 0.4);
}

.mm-section-header-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 50%, #EFF6FF 100%);
    border: 1.8px solid #BFDBFE;
    border-left: 6px solid #2563EB;
    border-radius: 20px;
    padding: 18px 24px;
    margin-top: 14px;
    margin-bottom: 16px;
    box-shadow: 0 4px 18px rgba(37, 99, 235, 0.08), 0 2px 6px rgba(0, 0, 0, 0.03);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    box-sizing: border-box;
}

.mm-section-header-avatar {
    width: 46px;
    height: 46px;
    min-width: 46px;
    border-radius: 50%;
    background: #EFF6FF;
    border: 1.5px solid #BFDBFE;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2563EB;
    flex-shrink: 0;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.15);
}

/* -- Trust & Compliance Bottom Footer Bar -- */
.mm-footer-trust-bar {
    background: var(--mm-bg-surface);
    border: 1.2px solid var(--mm-border-color);
    border-radius: 12px;
    padding: 12px 24px;
    margin-top: 24px;
    margin-bottom: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    color: var(--mm-text-secondary);

    width: 100%;
}
.mm-footer-trust-items {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 20px;
    width: 100%;
}
.mm-trust-item {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.80rem;
    color: #475569;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.mm-trust-icon {
    font-size: 0.90rem;
}
.mm-trust-dot {
    color: #CBD5E1;
    font-size: 0.75rem;
}

/* -- Panel 1 Form & Tool Box Polish -- */
.st-key-btn_describe_words {
    display: flex !important;
    align-items: center !important;
    margin-top: auto !important;
    margin-bottom: auto !important;
}
.st-key-btn_describe_words button {
    background: #FFFFFF !important;
    color: #2563EB !important;
    border: 1.5px solid #BFDBFE !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 14px !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
}

.st-key-btn_describe_words button:hover {
    background: #EFF6FF !important;
    border-color: #2563EB !important;
    color: #1D4ED8 !important;
}

/* Popular Symptoms Pills */
.st-key-pop_btn_0 button, .st-key-pop_btn_1 button, .st-key-pop_btn_2 button, .st-key-pop_btn_3 button,
.st-key-pop_btn_4 button, .st-key-pop_btn_5 button, .st-key-pop_btn_6 button, .st-key-pop_btn_7 button {
    background: #F8FAFC !important;
    color: #1E293B !important;
    border: 1.2px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 4px 10px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    min-height: 32px !important;
    height: 32px !important;
    box-shadow: none !important;
    white-space: nowrap !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.15s ease !important;
}

.st-key-pop_btn_0 button:hover, .st-key-pop_btn_1 button:hover, .st-key-pop_btn_2 button:hover, .st-key-pop_btn_3 button:hover,
.st-key-pop_btn_4 button:hover, .st-key-pop_btn_5 button:hover, .st-key-pop_btn_6 button:hover, .st-key-pop_btn_7 button:hover {
    background: #EFF6FF !important;
    border-color: #3B82F6 !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
}

/* Clear All Button */
.st-key-clear_all_sym_btn button {
    background: #FFF1F2 !important;
    color: #E11D48 !important;
    border: 1px solid #FFE4E6 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    padding: 4px 10px !important;
    min-height: 30px !important;
    height: 30px !important;
    box-shadow: none !important;
}

/* Previous Navigation Button */
.st-key-p1_prev_btn button {
    background: #FFFFFF !important;
    color: #475569 !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-size: 0.90rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

.st-key-p1_prev_btn button:hover {
    background: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Quick Actions List Items */
.st-key-qa_upload_presc button,
.st-key-qa_find_hosp button,
.st-key-qa_health_tips button {
    background: #FFFFFF !important;
    color: #1E293B !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    text-align: left !important;
    padding: 12px 14px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    min-height: 54px !important;
    height: auto !important;
    margin-bottom: 8px !important;
    line-height: 1.35 !important;
    transition: all 0.2s ease !important;
}

.st-key-qa_upload_presc button:hover,
.st-key-qa_find_hosp button:hover,
.st-key-qa_health_tips button:hover {
    background: #F8FAFC !important;
    border-color: #3B82F6 !important;
    color: #1D4ED8 !important;
    transform: translateX(2px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12) !important;
}

/* Badges & Status Pills */
.mm-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 11px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.mm-badge-brand {
    background-color: var(--mm-brand-subtle);
    color: var(--mm-brand-primary);
    border: 1px solid var(--mm-brand-border);
}

.mm-badge-critical {
    background-color: var(--mm-status-critical-bg);
    color: var(--mm-status-critical);
    border: 1px solid #F5C6CB;
}

.mm-badge-warning {
    background-color: var(--mm-status-warning-bg);
    color: var(--mm-status-warning);
    border: 1px solid #FFEBAA;
}

.mm-badge-success {
    background-color: var(--mm-status-success-bg);
    color: var(--mm-status-success);
    border: 1px solid #C3E6CB;
}

.mm-badge-info {
    background-color: var(--mm-status-info-bg);
    color: var(--mm-status-info);
    border: 1px solid #B8DAFF;
}

/* Clinical Alert Banners */
.mm-alert-banner {
    border-radius: var(--mm-radius-lg);
    padding: 16px 20px;
    margin: 18px 0;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}

.mm-alert-critical {
    background-color: var(--mm-status-critical-bg);
    border: 1px solid #F5C6CB;
    border-left: 5px solid var(--mm-status-critical);
    color: #721C24;
}

.mm-alert-warning {
    background-color: var(--mm-status-warning-bg);
    border: 1px solid #FFEBAA;
    border-left: 5px solid var(--mm-status-warning);
    color: #856404;
}

.mm-alert-info {
    background-color: var(--mm-status-info-bg);
    border: 1px solid #B8DAFF;
    border-left: 5px solid var(--mm-status-info);
    color: #004085;
}

/* Sidebar Brand Card */
.mm-sidebar-brand {
    background: linear-gradient(180deg, rgba(37, 99, 235, 0.15) 0%, rgba(17, 24, 39, 0) 100%);
    border: 1px solid rgba(37, 99, 235, 0.3);
    border-radius: var(--mm-radius-lg);
    padding: 18px;
    margin-bottom: 20px;
    text-align: center;
}

.mm-sidebar-trust {
    background: #1A2234;
    border: 1px solid #28334E;
    border-radius: var(--mm-radius-md);
    padding: 14px;
    font-size: 0.8rem;
    color: #9CA3AF;
    line-height: 1.4;
    margin-top: 24px;
}

/* Section Header Typography */
.mm-section-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--mm-text-primary);
    margin: 20px 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1.5px solid var(--mm-border-color);
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Context Chip */
.mm-chip {
    display: inline-block;
    background: #F1F3F6;
    color: var(--mm-text-secondary);
    font-size: 0.82rem;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 4px;
    margin-right: 6px;
}
/* ── Section 16: Standardized Medicine & Therapy Gallery Card Engine ── */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content),
.mm-med-card {
    background: var(--mm-bg-surface, #FFFFFF) !important;
    border: 1.5px solid var(--mm-border-color, #E2E8F0) !important;
    border-radius: 20px !important;
    padding: 16px 16px 20px 16px !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
    min-height: 540px !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content) > div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-yoga-card-content) > div[data-testid="stVerticalBlock"] {
    gap: 0 !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content):hover,
.mm-med-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
}

[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content),
[data-theme="dark"] .mm-med-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
}

.mm-med-card-content {
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    box-sizing: border-box !important;
}

.mm-med-hero-img-box {
    width: 100% !important;
    height: 185px !important;
    min-height: 185px !important;
    max-height: 185px !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    background: #F1F5F9 !important;
    margin-bottom: 12px !important;
    position: relative !important;
}
[data-theme="dark"] .mm-med-hero-img-box {
    background: #0B1220 !important;
}

.mm-med-title-top {
    font-size: 1.12rem !important;
    font-weight: 800 !important;
    color: var(--mm-text-primary, #0F172A) !important;
    line-height: 1.25 !important;
    margin-bottom: 4px !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 1 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
}
[data-theme="dark"] .mm-med-title-top {
    color: #F8FAFC !important;
}

.mm-med-desc {
    font-size: 0.82rem !important;
    color: var(--mm-text-secondary, #64748B) !important;
    line-height: 1.4 !important;
    margin-bottom: 12px !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
}
[data-theme="dark"] .mm-med-desc {
    color: #94A3B8 !important;
}

.mm-med-info-box-grid {
    background: var(--mm-bg-base, #F8FAFC) !important;
    border: 1.2px solid var(--mm-border-color, #E2E8F0) !important;
    border-radius: 14px !important;
    padding: 10px 12px !important;
    margin-bottom: 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 6px !important;
    box-sizing: border-box !important;
    min-height: 64px !important;
}
[data-theme="dark"] .mm-med-info-box-grid {
    background: #0B1220 !important;
    border-color: #1F2937 !important;
}

.mm-med-stat-col {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    flex: 1 !important;
    min-width: 0 !important;
}

.mm-med-stat-divider {
    width: 1px !important;
    height: 32px !important;
    background: var(--mm-border-color, #E2E8F0) !important;
    flex-shrink: 0 !important;
}
[data-theme="dark"] .mm-med-stat-divider {
    background: #1F2937 !important;
}

.mm-med-stat-label {
    font-size: 0.62rem !important;
    color: var(--mm-text-muted, #64748B) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-weight: 500 !important;
    line-height: 1.1 !important;
}
[data-theme="dark"] .mm-med-stat-label {
    color: #94A3B8 !important;
}

.mm-med-stat-val {
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    color: var(--mm-text-primary, #0F172A) !important;
    line-height: 1.2 !important;
    word-break: break-word !important;
    white-space: normal !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
}
[data-theme="dark"] .mm-med-stat-val {
    color: #F8FAFC !important;
}

.mm-med-stat-icon-blue {
    width: 28px !important;
    height: 28px !important;
    min-width: 28px !important;
    border-radius: 50% !important;
    background: #E0F2FE !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #0284C7 !important;
    flex-shrink: 0 !important;
}
[data-theme="dark"] .mm-med-stat-icon-blue {
    background: rgba(14, 165, 233, 0.2) !important;
    color: #38BDF8 !important;
}

.mm-med-stat-icon-orange {
    width: 28px !important;
    height: 28px !important;
    min-width: 28px !important;
    border-radius: 50% !important;
    background: #FFEDD5 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #EA580C !important;
    flex-shrink: 0 !important;
}
[data-theme="dark"] .mm-med-stat-icon-orange {
    background: rgba(234, 88, 12, 0.2) !important;
    color: #FB923C !important;
}

.mm-med-stat-icon-purple {
    width: 28px !important;
    height: 28px !important;
    min-width: 28px !important;
    border-radius: 50% !important;
    background: #EDE9FE !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #7C3AED !important;
    flex-shrink: 0 !important;
}
[data-theme="dark"] .mm-med-stat-icon-purple {
    background: rgba(124, 58, 237, 0.2) !important;
    color: #A78BFA !important;
}

.mm-med-badge-rx {
    background: #E0F2FE !important;
    color: #0284C7 !important;
    border: 1.2px solid #BAE6FD !important;
    border-radius: 999px !important;
    padding: 4px 14px !important;
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
}
[data-theme="dark"] .mm-med-badge-rx {
    background: rgba(14, 165, 233, 0.15) !important;
    color: #38BDF8 !important;
    border-color: rgba(14, 165, 233, 0.35) !important;
}

.mm-med-badge-verified {
    background: #DCFCE7 !important;
    color: #16A34A !important;
    border: 1.2px solid #BBF7D0 !important;
    border-radius: 999px !important;
    padding: 4px 14px !important;
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
}
[data-theme="dark"] .mm-med-badge-verified {
    background: rgba(34, 197, 94, 0.15) !important;
    color: #4ADE80 !important;
    border-color: rgba(34, 197, 94, 0.35) !important;
}

/* Primary Action Button inside Medicine Card */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content) button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content) .stButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    height: 44px !important;
    min-height: 44px !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    transition: all 0.2s ease !important;
    margin-top: auto !important;
    width: 100% !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content) button:hover,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content) .stButton > button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-yoga-card-content),
.mm-yoga-card {
    background: var(--mm-bg-surface, #FFFFFF) !important;
    border: 1.5px solid var(--mm-border-color, #E2E8F0) !important;
    border-radius: 20px !important;
    padding: 16px 16px 20px 16px !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
    min-height: 540px !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-yoga-card-content):hover,
.mm-yoga-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
}
[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-yoga-card-content),
[data-theme="dark"] .mm-yoga-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
}

/* ==========================================================================
   REPORT & CLINICAL CARE CARDS DESIGN SYSTEM (Light Mode)
   ========================================================================== */
.mm-triage-header-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 45%, #EFF6FF 100%);
    border: 2px solid #BFDBFE;
    border-left: 10px solid #2563EB;
    border-radius: 28px;
    padding: 34px 40px;
    margin-top: 18px;
    margin-bottom: 26px;
    box-shadow: 0 16px 40px -10px rgba(37, 99, 235, 0.14), 0 4px 14px rgba(0, 0, 0, 0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 24px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}
.mm-triage-header-card::before {
    content: '';
    position: absolute;
    top: -50px;
    right: -50px;
    width: 240px;
    height: 240px;
    background: radial-gradient(circle, rgba(37, 99, 235, 0.09) 0%, rgba(37, 99, 235, 0) 70%);
    border-radius: 50%;
    pointer-events: none;
}
.mm-triage-header-left {
    display: flex;
    align-items: center;
    gap: 22px;
    flex: 1;
    min-width: 320px;
}
.mm-triage-icon-wrap {
    width: 72px;
    height: 72px;
    min-width: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    flex-shrink: 0;
    box-shadow: 0 12px 28px rgba(37, 99, 235, 0.42);
    border: 3px solid rgba(255, 255, 255, 0.85);
}
.mm-triage-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.76rem;
    font-weight: 800;
    color: #2563EB;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
    background: rgba(37, 99, 235, 0.08);
    border: 1px solid rgba(37, 99, 235, 0.22);
    padding: 4px 12px;
    border-radius: 999px;
    width: fit-content;
}
.mm-triage-pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #2563EB;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
    display: inline-block;
}
.mm-triage-header-title {
    font-size: 1.95rem !important;
    font-weight: 900 !important;
    color: var(--mm-text-primary) !important;
    display: block;
    line-height: 1.22 !important;
    letter-spacing: -0.6px !important;
    margin: 0 !important;
}
.mm-triage-header-sub {
    font-size: 1.02rem;
    color: var(--mm-text-secondary);
    margin-top: 6px;
    font-weight: 450;
    line-height: 1.48;
    max-width: 820px;
}
.mm-triage-header-badge {
    background: #FFFFFF;
    border: 2px solid #BFDBFE;
    border-radius: 999px;
    padding: 12px 26px;
    display: inline-flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
    transition: all 0.25s ease;
}
.mm-triage-header-badge-sep {
    width: 1.8px;
    height: 22px;
    background: #BFDBFE;
}
.mm-triage-header-badge-text {
    color: #1D4ED8;
    font-size: 0.88rem;
    font-weight: 850;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
.mm-summary-card {
    background: #EFF6FF;
    border: 1.5px solid #BFDBFE;
    border-left: 5px solid #2563EB;
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.05);
}
.mm-recovery-card {
    background: #F0FDF4;
    border: 1.5px solid #BBF7D0;
    border-left: 5px solid #10B981;
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 18px;
    box-shadow: 0 2px 6px rgba(16, 185, 129, 0.05);
}
.mm-foment-card {
    background: #FFF7ED;
    border: 1.5px solid #FED7AA;
    border-left: 5px solid #EA580C;
    border-radius: 18px;
    padding: 18px 22px;
    margin-top: 14px;
    margin-bottom: 18px;
    box-shadow: 0 2px 8px rgba(234, 88, 12, 0.06);
}
.mm-seasonal-card {
    background: #FFF7ED;
    border: 1.5px solid #FED7AA;
    border-left: 5px solid #EA580C;
    border-radius: 18px;
    padding: 18px 22px;
    margin-top: 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(234, 88, 12, 0.06);
}
.mm-review-card-blue {
    background: #FFFFFF;
    border: 1.5px solid #93C5FD;
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
}
.mm-review-card-purple {
    background: #FFFFFF;
    border: 1.5px solid #DDD6FE;
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.06);
}
.mm-review-card-green {
    background: #FFFFFF;
    border: 1.5px solid #BBF7D0;
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.06);
}
.mm-review-row-blue {
    background: #EFF6FF;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
.mm-review-row-purple {
    background: #FAF5FF;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
.mm-review-row-green {
    background: #F0FDF4;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_1),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_2),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_3),
.st-key-gis_panel_col_1,
.st-key-gis_panel_col_2,
.st-key-gis_panel_col_3 {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 22px 24px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04) !important;
    height: 100% !important;
    box-sizing: border-box !important;
}
.mm-gis-icon-box {
    width: 44px;
    height: 44px;
    min-width: 44px;
    border-radius: 12px;
    background: #DBEAFE;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2563EB;
}
.mm-gis-title {
    font-size: 1.22rem;
    font-weight: 800;
    color: #1E3A8A;
    letter-spacing: -0.2px;
}
.st-key-gis_city_search_input input,
div.st-key-gis_city_search_input input,
.st-key-gis_panel_col_1 input {
    text-indent: 26px !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%232563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;
}
.st-key-gis_city_search_input input::placeholder,
.st-key-gis_panel_col_1 input::placeholder {
    text-indent: 26px !important;
}
.mm-gis-engine-badge {
    background: #EFF6FF;
    border: 1.5px solid #DBEAFE;
    color: #2563EB;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    border-radius: 999px;
    padding: 7px 18px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.08);
}
.mm-gis-helpline-box {
    background: #E0F2FE;
    border: 1.2px solid #BAE6FD;
    border-radius: 12px;
    padding: 10px 14px;
    margin-top: 12px;
    font-size: 0.74rem;
    color: #0369A1;
    display: flex;
    align-items: center;
    gap: 10px;
    line-height: 1.35;
}
.mm-diag-test-card {
    background: #FAF5FF;
    border: 1.5px solid #DDD6FE;
    border-left: 5px solid #7C3AED;
    border-radius: 20px;
    padding: 20px 24px;
    margin-top: 18px;
    margin-bottom: 18px;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.06);
}
.mm-diag-chip {
    background: #EDE9FE;
    color: #4C1D95;
    border: 1.2px solid #C4B5FD;
    border-radius: 999px;
    padding: 8px 18px;
    font-size: 0.84rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s ease;
}
.mm-diag-chip:hover {
    background: #DDD6FE;
    transform: translateY(-1px);
}
.mm-dietary-card {
    background: #FFFFFF;
    border: 1.5px solid #10B981;
    border-left: 5px solid #059669;
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.06);
}
.mm-clinical-care-card {
    background: #FFFFFF;
    border: 1.5px solid #3B82F6;
    border-left: 5px solid #2563EB;
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
}
.mm-subbox-green {
    background: #F0FDF4;
    border: 1.2px solid #DCFCE7;
    border-radius: 16px;
    padding: 16px 18px;
}
.mm-subbox-orange {
    background: #FFF7ED;
    border: 1.2px solid #FFEDD5;
    border-radius: 16px;
    padding: 16px 18px;
}
.mm-subbox-blue {
    background: #EFF6FF;
    border: 1.2px solid #DBEAFE;
    border-radius: 16px;
    padding: 16px 18px;
}
.mm-subbox-red {
    background: #FEF2F2;
    border: 1.2px solid #FEE2E2;
    border-radius: 16px;
    padding: 16px 18px;
}
.mm-subbox-purple {
    background: #FAF5FF;
    border: 1.2px solid #F3E8FF;
    border-radius: 16px;
    padding: 16px 18px;
}
.mm-text-green { color: #047857; }
.mm-text-orange { color: #C2410C; }
.mm-text-blue { color: #1D4ED8; }
.mm-text-red { color: #DC2626; }
.mm-text-purple { color: #7C3AED; }

/* ── Enterprise Session Cards (Image 4 Design Spec) ── */
.mm-session-card {
    background: var(--mm-bg-surface, #FFFFFF);
    border: 1.5px solid #E2E8F0;
    border-radius: 14px;
    margin-bottom: 14px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.mm-session-card:hover {
    border-color: rgba(37, 99, 235, 0.4);
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
}
.mm-session-card summary {
    list-style: none;
    cursor: pointer;
    outline: none;
    user-select: none;
    padding: 14px 18px;
    background: #F8FAFC;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    border-bottom: 1.5px solid transparent;
    transition: background 0.2s ease, border-color 0.2s ease;
}
.mm-session-card summary::-webkit-details-marker {
    display: none;
}
.mm-session-card[open] > summary {
    border-bottom: 1.5px solid #E2E8F0;
    background: #F1F5F9;
}
.mm-session-card .mm-session-summary-left {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    font-weight: 700;
    color: #0F172A;
    flex: 1 1 auto;
    min-width: 240px;
}
.mm-session-card .mm-chevron-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    color: #2563EB;
}
.mm-session-card[open] .mm-chevron-icon {
    transform: rotate(90deg);
}
.mm-session-card .mm-session-summary-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
}
.mm-session-date {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.78rem;
    color: #64748B;
    font-weight: 500;
}
.mm-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}
.mm-status-pill-abnormal {
    background: #FEE2E2;
    border: 1px solid #FECACA;
    color: #DC2626;
}
.mm-status-pill-normal {
    background: #DCFCE7;
    border: 1px solid #BBF7D0;
    color: #16A34A;
}
.mm-status-pill-warning {
    background: #FEF3C7;
    border: 1px solid #FDE68A;
    color: #D97706;
}
.mm-session-body {
    padding: 18px 20px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
    background: #FFFFFF;
}
@media (max-width: 768px) {
    .mm-session-body {
        grid-template-columns: 1fr;
        gap: 16px;
    }
}
.mm-session-col-left {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 14px;
}
.mm-session-col-right {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.mm-field-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.mm-field-badge {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-badge-blue { background: rgba(37, 99, 235, 0.1); color: #2563EB; }
.mm-badge-green { background: rgba(16, 185, 129, 0.1); color: #10B981; }
.mm-badge-purple { background: rgba(139, 92, 246, 0.1); color: #8B5CF6; }
.mm-field-text {
    flex: 1;
}
.mm-field-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 2px;
}
.mm-field-desc {
    font-size: 0.84rem;
    color: #64748B;
    line-height: 1.45;
    margin: 0;
}
.mm-excerpt-box {
    background: rgba(37, 99, 235, 0.04);
    border: 1px solid rgba(37, 99, 235, 0.2);
    border-radius: 8px;
    padding: 10px 12px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.78rem;
    color: #1D4ED8;
    word-break: break-word;
    margin-top: 6px;
    line-height: 1.4;
}
.mm-right-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 4px;
}
.mm-metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, 130px);
    gap: 12px;
    align-items: start;
    justify-content: start;
}
.mm-metric-card {
    padding: 12px 10px;
    border-radius: 12px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 130px;
    height: 104px;
    box-sizing: border-box;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.mm-metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.mm-metric-card-high {
    background: #FEF2F2;
    border: 1.2px solid #FECACA;
}
.mm-metric-card-normal {
    background: #F0FDF4;
    border: 1.2px solid #BBF7D0;
}
.mm-metric-card-borderline {
    background: #FFFBEB;
    border: 1.2px solid #FDE68A;
}
.mm-metric-card-default {
    background: #EFF6FF;
    border: 1.2px solid #BFDBFE;
}
.mm-metric-val {
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 2px;
    line-height: 1.2;
}
.mm-metric-lbl {
    font-size: 0.76rem;
    font-weight: 600;
    color: #64748B;
    margin-bottom: 6px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}
.mm-metric-pill {
    font-size: 0.70rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 12px;
    display: inline-block;
    line-height: 1.3;
}
.mm-doctor-advisory {
    background: rgba(37, 99, 235, 0.06);
    border: 1px solid rgba(37, 99, 235, 0.18);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.76rem;
    color: #2563EB;
    font-weight: 500;
    margin-top: 6px;
}

/* Footer Slogan Pill */
.mm-footer-slogan-pill {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #2563EB;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 4px 14px;
    border-radius: 20px;
    white-space: nowrap;
}

/* Mobile Flex Responsiveness */
@media (max-width: 768px) {
    .mm-session-body {
        flex-direction: column !important;
        gap: 16px !important;
        padding: 14px !important;
    }
    .mm-session-col-left, .mm-session-col-right {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .mm-session-card summary {
        padding: 12px 14px !important;
        flex-direction: column !important;
        align-items: flex-start !important;
    }
    .mm-session-summary-right {
        margin-top: 8px !important;
        width: 100% !important;
        justify-content: space-between !important;
    }
    .mm-metrics-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        justify-content: stretch !important;
    }
    .mm-metric-card {
        width: 100% !important;
        height: 104px !important;
    }
}
/* ============================================================
   CLINICAL AUTHENTICATION PORTAL -- IMAGE 2 SPECIFICATION
   ============================================================ */
div[data-testid="stHorizontalBlock"]:has(.st-key-auth_left_vault_card) {
    display: flex !important;
    align-items: stretch !important;
}

div[data-testid="column"]:has(.st-key-auth_left_vault_card),
div[data-testid="column"]:has(.st-key-auth_right_signin_card) {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 0 !important;
    align-self: stretch !important;
    height: 100% !important;
}

div[data-testid="column"]:has(.st-key-auth_left_vault_card) > div[data-testid="stVerticalBlock"],
div[data-testid="column"]:has(.st-key-auth_right_signin_card) > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

.st-key-auth_left_vault_card,
.st-key-auth_right_signin_card {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

.st-key-auth_left_vault_card > div,
.st-key-auth_right_signin_card > div {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

.st-key-auth_left_vault_card div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-auth_right_signin_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(37, 99, 235, 0.06) !important;
    padding: 22px 24px 24px 24px !important;
    transition: all 0.25s ease !important;
    flex: 1 1 100% !important;
    height: 100% !important;
    min-height: 600px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
}

.st-key-auth_left_vault_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%) !important;
}

.auth-trust-grid {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(72px, 1fr)) !important;
    gap: 8px !important;
    width: 100% !important;
}

.auth-trust-item {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 9px !important;
    padding: 10px 8px !important;
    display: flex !important;
    align-items: flex-start !important;
    gap: 6px !important;
    min-height: 64px !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}

.auth-trust-item > div:last-child {
    min-width: 0 !important;
    flex: 1 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}

/* Auth input labels */
.auth-input-label {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    margin-bottom: 6px !important;
}
.auth-input-label svg {
    flex-shrink: 0 !important;
}

/* Auth Text Inputs */
.st-key-panel_login_email input,
.st-key-panel_login_password input {
    border-radius: 10px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    padding: 10px 14px !important;
    font-size: 0.90rem !important;
    color: #0F172A !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease !important;
}
.st-key-panel_login_email input:focus,
.st-key-panel_login_password input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* Forgot Password Link Button */
.st-key-auth_btn_forgot_pwd_link {
    display: flex !important;
    justify-content: flex-end !important;
}
.st-key-auth_btn_forgot_pwd_link button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    min-height: auto !important;
    height: auto !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #2563EB !important;
    cursor: pointer !important;
    margin: 0 !important;
    text-align: right !important;
}
.st-key-auth_btn_forgot_pwd_link button:hover {
    color: #1D4ED8 !important;
    text-decoration: underline !important;
    background: transparent !important;
}
.st-key-auth_btn_forgot_pwd_link button p {
    color: #2563EB !important;
    margin: 0 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* Auth Action Buttons Base */
.st-key-panel_btn_login_submit button,
.st-key-panel_btn_goto_reg button,
.st-key-panel_btn_goto_rec button,
.st-key-panel_btn_goto_admin button,
.st-key-panel_btn_return_dashboard button {
    position: relative !important;
    padding: 10px 14px 10px 54px !important;
    min-height: 56px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
}

.st-key-panel_btn_login_submit button::before,
.st-key-panel_btn_goto_reg button::before,
.st-key-panel_btn_goto_rec button::before,
.st-key-panel_btn_goto_admin button::before,
.st-key-panel_btn_return_dashboard button::before {
    content: '' !important;
    position: absolute !important;
    left: 16px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 24px !important;
    height: 24px !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: contain !important;
    z-index: 2 !important;
}

/* Button 1: Continue to 2FA (Primary Solid - High Specificity to prevent button[kind=primary] override) */
div.st-key-panel_btn_login_submit > button,
div.st-key-panel_btn_login_submit button[kind="primary"],
div.st-key-panel_btn_login_submit button[data-testid="baseButton-primary"],
.st-key-panel_btn_login_submit button {
    background: #2563EB !important;
    border: 1.5px solid #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
    padding-left: 56px !important;
    padding-right: 14px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    min-height: 56px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
}
div.st-key-panel_btn_login_submit > button:hover,
div.st-key-panel_btn_login_submit button[kind="primary"]:hover,
div.st-key-panel_btn_login_submit button[data-testid="baseButton-primary"]:hover,
.st-key-panel_btn_login_submit button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38) !important;
    transform: translateY(-1px) !important;
}
div.st-key-panel_btn_login_submit button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/%3E%3Cpath d='M12 8v8'/%3E%3Cpath d='M8 12h8'/%3E%3C/svg%3E") !important;
}
div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] {
    margin-left: 0 !important;
    padding-left: 0 !important;
    text-align: left !important;
    width: 100% !important;
}
div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: center !important;
    text-align: left !important;
    font-size: 0.74rem !important;
    color: rgba(255, 255, 255, 0.88) !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.25 !important;
}
div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] p br {
    display: none !important;
}
div.st-key-panel_btn_login_submit button div[data-testid="stMarkdownContainer"] p strong {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin-bottom: 2px !important;
    text-align: left !important;
}

/* Button 2: Create New Account (Outline) */
.st-key-panel_btn_goto_reg button {
    background: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}
.st-key-panel_btn_goto_reg button:hover {
    border-color: #3B82F6 !important;
    background: #F8FAFC !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_goto_reg button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='9' cy='7' r='4'/%3E%3Cline x1='19' y1='8' x2='19' y2='14'/%3E%3Cline x1='22' y1='11' x2='16' y2='11'/%3E%3C/svg%3E") !important;
}

/* Button 3: Recovery Password (Outline) */
.st-key-panel_btn_goto_rec button {
    background: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}
.st-key-panel_btn_goto_rec button:hover {
    border-color: #3B82F6 !important;
    background: #F8FAFC !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_goto_rec button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 2l-2 2m-1.5 1.5L14 9l-1.5-1.5L11 9l-1.5-1.5L8 9 2 15a6 6 0 1 0 7 7l6-6 1.5 1.5L18 16l1.5-1.5 1.5 1.5L22 16l2-2-4-4-1-1z'/%3E%3Ccircle cx='7.5' cy='16.5' r='1.5'/%3E%3C/svg%3E") !important;
}

/* Button 4: Administrator Access (Outline) */
.st-key-panel_btn_goto_admin button {
    background: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}
.st-key-panel_btn_goto_admin button:hover {
    border-color: #3B82F6 !important;
    background: #F8FAFC !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_goto_admin button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
}

/* Button 5: Return to Clinical Dashboard (Full Width) */
.st-key-panel_btn_return_dashboard button {
    background: #EFF6FF !important;
    border: 1.5px solid #BFDBFE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    justify-content: center !important;
    padding-left: 52px !important;
}
.st-key-panel_btn_return_dashboard button:hover {
    background: #DBEAFE !important;
    border-color: #3B82F6 !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_return_dashboard button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='19' y1='12' x2='5' y2='12'/%3E%3Cpolyline points='12 19 5 12 12 5'/%3E%3C/svg%3E") !important;
    left: 24px !important;
}

/* Secondary Button typography */
.st-key-panel_btn_goto_reg button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_goto_rec button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_goto_admin button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_return_dashboard button div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: center !important;
    text-align: left !important;
    font-size: 0.74rem !important;
    color: #64748B !important;
    margin: 0 !important;
    line-height: 1.25 !important;
}
.st-key-panel_btn_goto_reg button div[data-testid="stMarkdownContainer"] p br,
.st-key-panel_btn_goto_rec button div[data-testid="stMarkdownContainer"] p br,
.st-key-panel_btn_goto_admin button div[data-testid="stMarkdownContainer"] p br,
.st-key-panel_btn_return_dashboard button div[data-testid="stMarkdownContainer"] p br {
    display: none !important;
}
.st-key-panel_btn_goto_reg button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_goto_rec button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_goto_admin button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_return_dashboard button div[data-testid="stMarkdownContainer"] p strong {
    font-size: 0.90rem !important;
    font-weight: 700 !important;
    color: #1E40AF !important;
    margin-bottom: 2px !important;
}

/* OR Divider */
.auth-or-divider {
    display: flex !important;
    align-items: center !important;
    text-align: center !important;
    margin: 16px 0 !important;
    color: #94A3B8 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
}
.auth-or-divider::before,
.auth-or-divider::after {
    content: '' !important;
    flex: 1 !important;
    border-bottom: 1px solid #E2E8F0 !important;
}
.auth-or-divider span {
    padding: 0 14px !important;
}

/* Card Footer */
.auth-card-footer {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin-top: auto !important;
    padding-top: 14px !important;
    border-top: 1px solid #F1F5F9 !important;
    font-size: 0.74rem !important;
    color: #64748B !important;
}
.auth-footer-left {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

/* Responsive Rules for Auth Cards */
@media (max-width: 992px) {
    .auth-left-middle-grid {
        grid-template-columns: 1fr !important;
    }
    .auth-trust-grid {
        grid-template-columns: repeat(2, minmax(72px, 1fr)) !important;
    }
    .auth-trust-item {
        min-height: 56px !important;
    }
}
@media (max-width: 640px) {
    .st-key-auth_left_vault_card div[data-testid="stVerticalBlockBorderWrapper"],
    .st-key-auth_right_signin_card div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 16px !important;
    }
    .auth-trust-grid {
        grid-template-columns: repeat(2, minmax(72px, 1fr)) !important;
    }
    .auth-trust-item {
        min-height: 56px !important;
        flex-direction: row !important;
        align-items: flex-start !important;
    }
    .auth-card-footer {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 6px !important;
    }
    .auth-privacy-banner {
        flex-direction: column !important;
        align-items: flex-start !important;
    }
}
/* Administrator & Recovery Buttons & Inputs */
.st-key-panel_btn_adm_cred button,
.st-key-panel_btn_back_from_adm button,
.st-key-panel_btn_send_rec button,
.st-key-panel_btn_back_from_rec button {
    position: relative !important;
    padding: 10px 14px 10px 52px !important;
    min-height: 52px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
}

.st-key-panel_btn_adm_cred button::before,
.st-key-panel_btn_back_from_adm button::before,
.st-key-panel_btn_send_rec button::before,
.st-key-panel_btn_back_from_rec button::before {
    content: '' !important;
    position: absolute !important;
    left: 18px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 22px !important;
    height: 22px !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: contain !important;
}

/* Verify Credentials & Request Admin Key (Primary) */
.st-key-panel_btn_adm_cred button {
    background: #2563EB !important;
    border: 1.5px solid #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
}
.st-key-panel_btn_adm_cred button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38) !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_adm_cred button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/%3E%3Cpolyline points='9 12 11 14 15 10'/%3E%3C/svg%3E") !important;
}
.st-key-panel_btn_adm_cred button div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: center !important;
    text-align: left !important;
    font-size: 0.74rem !important;
    color: rgba(255, 255, 255, 0.88) !important;
    margin: 0 !important;
    line-height: 1.25 !important;
}
.st-key-panel_btn_adm_cred button div[data-testid="stMarkdownContainer"] p br {
    display: none !important;
}
.st-key-panel_btn_adm_cred button div[data-testid="stMarkdownContainer"] p strong {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin-bottom: 2px !important;
}

/* Regular Patient Sign In (Outline) */
.st-key-panel_btn_back_from_adm button {
    background: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}
.st-key-panel_btn_back_from_adm button:hover {
    border-color: #3B82F6 !important;
    background: #F8FAFC !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_back_from_adm button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='19' y1='12' x2='5' y2='12'/%3E%3Cpolyline points='12 19 5 12 12 5'/%3E%3C/svg%3E") !important;
}
.st-key-panel_btn_back_from_adm button div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: center !important;
    text-align: left !important;
    font-size: 0.74rem !important;
    color: #64748B !important;
    margin: 0 !important;
    line-height: 1.25 !important;
}
.st-key-panel_btn_back_from_adm button div[data-testid="stMarkdownContainer"] p br {
    display: none !important;
}
.st-key-panel_btn_back_from_adm button div[data-testid="stMarkdownContainer"] p strong {
    font-size: 0.90rem !important;
    font-weight: 700 !important;
    color: #1E40AF !important;
    margin-bottom: 2px !important;
}

/* Send Recovery Code Button */
.st-key-panel_btn_send_rec button {
    background: #2563EB !important;
    border: 1.5px solid #1D4ED8 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    justify-content: center !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
}
.st-key-panel_btn_send_rec button:hover {
    background: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38) !important;
}
.st-key-panel_btn_send_rec button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='22' y1='2' x2='11' y2='13'/%3E%3Cpolygon points='22 2 15 22 11 13 2 9 22 2'/%3E%3C/svg%3E") !important;
    left: 20px !important;
}
.st-key-panel_btn_send_rec button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Back to Sign In Button */
.st-key-panel_btn_back_from_rec button {
    background: #FFFFFF !important;
    border: 1.5px solid #BFDBFE !important;
    color: #2563EB !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    justify-content: center !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
}
.st-key-panel_btn_back_from_rec button:hover {
    border-color: #3B82F6 !important;
    background: #F8FAFC !important;
    transform: translateY(-1px) !important;
}
.st-key-panel_btn_back_from_rec button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='19' y1='12' x2='5' y2='12'/%3E%3Cpolyline points='12 19 5 12 12 5'/%3E%3C/svg%3E") !important;
    left: 20px !important;
}
.st-key-panel_btn_back_from_rec button p {
    color: #2563EB !important;
    font-weight: 700 !important;
}

/* Text Inputs for Admin and Recovery */
.st-key-panel_adm_email input,
.st-key-panel_adm_pass input,
.st-key-panel_rec_email input {
    border-radius: 10px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    padding: 10px 14px !important;
    font-size: 0.90rem !important;
    color: #0F172A !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease !important;
}
.st-key-panel_adm_email input:focus,
.st-key-panel_adm_pass input:focus,
.st-key-panel_rec_email input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* Authorized Personnel Alert Box */
.auth-admin-alert {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 12px 14px !important;
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
    border-left: 4px solid #EF4444 !important;
    border-radius: 10px !important;
    margin-bottom: 18px !important;
}

/* Info Callout Box (Recovery View) */
.auth-info-callout {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 11px 14px !important;
    background: #EFF6FF !important;
    border: 1px solid #DBEAFE !important;
    border-radius: 10px !important;
    margin: 12px 0 18px 0 !important;
    font-size: 0.78rem !important;
    color: #1E40AF !important;
    line-height: 1.4 !important;
}

/* Privacy Matters Banner (Recovery View) */
.auth-privacy-banner {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 14px 16px !important;
    background: #F0FDF4 !important;
    border: 1px solid #BBF7D0 !important;
    border-radius: 10px !important;
    margin-top: 18px !important;
    min-height: 64px !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

/* 3-Step Indicator Dots Animation */
@keyframes auth-dot-pulse {
    0%, 100% { opacity: 0.3; transform: scale(0.8); }
    50%       { opacity: 1;   transform: scale(1.25); }
}
.auth-step-dot-1 {
    display: inline-block !important;
    width: 9px !important;
    height: 9px !important;
    border-radius: 50% !important;
    background: #3B82F6 !important;
    animation: auth-dot-pulse 1.5s ease-in-out infinite !important;
    animation-delay: 0s !important;
}
.auth-step-dot-2 {
    display: inline-block !important;
    width: 9px !important;
    height: 9px !important;
    border-radius: 50% !important;
    background: #93C5FD !important;
    animation: auth-dot-pulse 1.5s ease-in-out infinite !important;
    animation-delay: 0.3s !important;
}
.auth-step-dot-3 {
    display: inline-block !important;
    width: 9px !important;
    height: 9px !important;
    border-radius: 50% !important;
    background: #93C5FD !important;
    animation: auth-dot-pulse 1.5s ease-in-out infinite !important;
    animation-delay: 0.6s !important;
}
/* ============================================================
   PATIENT REGISTRATION & PASSWORD RECOVERY CARDS (IMAGE 2 & 4)
   ============================================================ */
.auth-input-icon-box {
    width: 44px !important;
    height: 44px !important;
    border-radius: 10px !important;
    background: #EFF6FF !important;
    border: 1.5px solid #DBEAFE !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    transition: all 0.2s ease !important;
    margin: 0 auto !important;
}
.auth-input-icon-box:hover {
    border-color: #93C5FD !important;
    background: #E0F2FE !important;
}
.auth-input-help {
    font-size: 0.74rem !important;
    color: #64748B !important;
    margin-top: 2px !important;
    margin-bottom: 8px !important;
    padding-left: 2px !important;
    line-height: 1.3 !important;
}
.auth-pwd-req-box {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 12px !important;
    padding: 13px 16px !important;
    margin: 14px 0 !important;
}
.auth-check-email-card {
    background: #F0F9FF !important;
    border: 1.2px solid #BAE6FD !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin-bottom: 14px !important;
}
.auth-card-footer-trust {
    border-top: 1px solid #E2E8F0 !important;
    padding-top: 14px !important;
    margin-top: 16px !important;
}

/* Secondary & Tertiary Outline Buttons in Registration & Recovery */
.st-key-panel_btn_back_to_login button,
.st-key-panel_btn_reg_return_dash button,
.st-key-panel_btn_cancel_rec button {
    background: #FFFFFF !important;
    border: 1.5px solid #2563EB !important;
    color: #2563EB !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    min-height: 44px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08) !important;
}
.st-key-panel_btn_back_to_login button:hover,
.st-key-panel_btn_reg_return_dash button:hover,
.st-key-panel_btn_cancel_rec button:hover {
    background: rgba(37, 99, 235, 0.08) !important;
    border-color: #1D4ED8 !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.15) !important;
}
.st-key-panel_btn_back_to_login button p,
.st-key-panel_btn_reg_return_dash button p,
.st-key-panel_btn_cancel_rec button p {
    color: #2563EB !important;
    font-weight: 700 !important;
}
.st-key-panel_btn_back_to_login button:hover p,
.st-key-panel_btn_reg_return_dash button:hover p,
.st-key-panel_btn_cancel_rec button:hover p {
    color: #1D4ED8 !important;
}

/* Primary Registration & Reset Buttons */
.st-key-panel_btn_submit_reg button,
.st-key-panel_btn_finish_rec button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    min-height: 46px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s ease !important;
}
.st-key-panel_btn_submit_reg button:hover,
.st-key-panel_btn_finish_rec button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.5) !important;
}
.st-key-panel_btn_submit_reg button p,
.st-key-panel_btn_finish_rec button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Registration & Recovery Inputs */
.st-key-panel_reg_name input,
.st-key-panel_reg_email input,
.st-key-panel_reg_pass input,
.st-key-panel_reg_conf input,
.st-key-panel_rec_otp_input input,
.st-key-panel_rec_p1 input,
.st-key-panel_rec_p2 input {
    border-radius: 10px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    padding: 10px 14px !important;
    font-size: 0.90rem !important;
    color: #0F172A !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease !important;
}
.st-key-panel_reg_name input:focus,
.st-key-panel_reg_email input:focus,
.st-key-panel_reg_pass input:focus,
.st-key-panel_reg_conf input:focus,
.st-key-panel_rec_otp_input input:focus,
.st-key-panel_rec_p1 input:focus,
.st-key-panel_rec_p2 input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

/* ============================================================
   MY PROFILE & FAMILY VAULT ENHANCEMENTS (IMAGE 2 & IMAGE 4)
   ============================================================ */
.patient-hero-card {
    background: linear-gradient(180deg, #F0F7FF 0%, #FFFFFF 100%) !important;
    border: 1.5px solid #DBEAFE !important;
    border-radius: 18px !important;
    padding: 22px 26px !important;
    margin-bottom: 22px !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.06) !important;
}

.family-member-card {
    background: #FFFFFF !important;
    border: 1.2px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
    transition: all 0.2s ease !important;
}
.family-member-card:hover {
    border-color: #BFDBFE !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08) !important;
}

.account-settings-card {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 18px !important;
    padding: 24px 28px !important;
    margin-top: 10px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04) !important;
}

.account-field-icon-box {
    width: 40px !important;
    height: 40px !important;
    border-radius: 10px !important;
    background: #EFF6FF !important;
    border: 1.5px solid #DBEAFE !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    margin: 0 0 0 auto !important;
}

/* Tighten icon-to-input gap in account profile fields */
[data-testid="stHorizontalBlock"]:has(.account-field-icon-box) {
    gap: 4px !important;
    column-gap: 4px !important;
    align-items: center !important;
}
[data-testid="stHorizontalBlock"]:has(.account-field-icon-box) > [data-testid="column"]:first-child {
    padding-right: 0 !important;
    flex: 0 0 48px !important;
    max-width: 48px !important;
    min-width: 48px !important;
    width: 48px !important;
}
[data-testid="stHorizontalBlock"]:has(.account-field-icon-box) > [data-testid="column"]:not(:first-child) {
    padding-left: 0 !important;
    flex: 1 1 0 !important;
    min-width: 0 !important;
}

/* Update Name Button (Image 4) */
.st-key-btn_update_prof_name button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    min-height: 42px !important;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.3) !important;
    transition: all 0.2s ease !important;
}
.st-key-btn_update_prof_name button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 14px rgba(37, 99, 235, 0.45) !important;
}
.st-key-btn_update_prof_name button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Sign Out / Logout Outline Button (Image 4) */
.st-key-btn_prof_logout_main button {
    background: #FFFFFF !important;
    border: 1.5px solid #2563EB !important;
    color: #2563EB !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    min-height: 42px !important;
    box-shadow: 0 1px 4px rgba(37, 99, 235, 0.08) !important;
    transition: all 0.2s ease !important;
}
.st-key-btn_prof_logout_main button:hover {
    background: rgba(37, 99, 235, 0.08) !important;
    border-color: #1D4ED8 !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15) !important;
}
.st-key-btn_prof_logout_main button p {
    color: #2563EB !important;
    font-weight: 700 !important;
}
.st-key-btn_prof_logout_main button:hover p {
    color: #1D4ED8 !important;
}

/* Add New Family Member Button (Image 2) */
.st-key-btn_add_family_hero button {
    background: #2563EB !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    min-height: 40px !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
}
.st-key-btn_add_family_hero button:hover {
    background: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
}
.st-key-btn_add_family_hero button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Account Profile Inputs */
.st-key-panel_prof_email input,
.st-key-panel_prof_name input,
.st-key-panel_prof_status input,
.st-key-panel_prof_last_login input,
.st-key-panel_prof_member_since input {
    border-radius: 10px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    padding: 10px 14px !important;
    font-size: 0.90rem !important;
    color: #0F172A !important;
}
.st-key-panel_prof_status input {
    background: #F0FDF4 !important;
    color: #166534 !important;
    border-color: #BBF7D0 !important;
    font-weight: 700 !important;
}
/* Form Sub-Cards (Add Family Member & Password Requirements) */
.form-subcard {
    background: #FFFFFF !important;
    border: 1.2px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02) !important;
}

/* Save Family Member Button */
.st-key-btn_save_family_profile button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    min-height: 46px !important;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.3) !important;
    transition: all 0.2s ease !important;
}
.st-key-btn_save_family_profile button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 14px rgba(37, 99, 235, 0.45) !important;
}
.st-key-btn_save_family_profile button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Cancel Password Button */
.st-key-btn_cancel_change_pwd button {
    background: #FFFFFF !important;
    border: 1.5px solid #2563EB !important;
    color: #2563EB !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    min-height: 42px !important;
    box-shadow: 0 1px 4px rgba(37, 99, 235, 0.08) !important;
    transition: all 0.2s ease !important;
}
.st-key-btn_cancel_change_pwd button:hover {
    background: rgba(37, 99, 235, 0.08) !important;
    border-color: #1D4ED8 !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
}
.st-key-btn_cancel_change_pwd button p {
    color: #2563EB !important;
    font-weight: 700 !important;
}

/* Update Password Submit Button */
.st-key-btn_update_pwd_submit button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    min-height: 42px !important;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.3) !important;
    transition: all 0.2s ease !important;
}
.st-key-btn_update_pwd_submit button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 14px rgba(37, 99, 235, 0.45) !important;
}
.st-key-btn_update_pwd_submit button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ============================================================
   ADMINISTRATOR SESSION CARD -- IMAGE 2 SPECIFICATION
   ============================================================ */
.adm-session-outer-wrap {
    width: 100%;
    max-width: 100%;
    margin: 0 0 20px 0;
    box-sizing: border-box;
}

.adm-session-top-brand {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 0 4px;
    flex-wrap: wrap;
    gap: 12px;
}

.adm-session-card {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 18px;
    box-shadow: 0 6px 28px rgba(37, 99, 235, 0.07);
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

.adm-session-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    margin-bottom: 18px;
}

.adm-session-hdr-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.adm-session-lock-box {
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%);
    border: 1.5px solid #BFDBFE;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.16);
    flex-shrink: 0;
}

.adm-session-title {
    margin: 0;
    font-size: 1.65rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.01em;
    line-height: 1.2;
}

.adm-session-title span {
    color: #2563EB;
}

.adm-session-subtitle {
    margin: 3px 0 0 0;
    font-size: 0.86rem;
    color: #64748B;
    line-height: 1.35;
}

.adm-session-hdr-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    position: relative;
    padding-right: 12px;
}

.adm-session-cursive {
    font-family: 'Segoe Script', 'Comic Sans MS', cursive, sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #38BDF8;
    line-height: 1.25;
    text-align: right;
    transform: rotate(-3deg);
    position: relative;
}

/* Middle Navy Banner */
.adm-session-banner {
    background: linear-gradient(135deg, #07152B 0%, #0D2342 55%, #13335D 100%);
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    padding: 18px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.adm-session-admin-block {
    display: flex;
    align-items: center;
    gap: 14px;
}

.adm-session-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
    border: 2px solid #60A5FA;
    color: #FFFFFF;
    font-size: 1.3rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    flex-shrink: 0;
}

.adm-session-crown-badge {
    background: rgba(13, 148, 136, 0.18);
    border: 1px solid #14B8A6;
    border-radius: 16px;
    padding: 2px 10px;
    color: #2DD4BF;
    font-size: 0.68rem;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    letter-spacing: 0.03em;
}

.adm-session-divider {
    width: 1px;
    height: 44px;
    background: rgba(255, 255, 255, 0.12);
}

.adm-session-metric-block {
    display: flex;
    align-items: center;
    gap: 12px;
}

.adm-session-icon-box {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.adm-session-status-pill {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10B981;
    border-radius: 24px;
    padding: 7px 18px;
    color: #34D399;
    font-weight: 800;
    font-size: 0.74rem;
    letter-spacing: 0.06em;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
}

.adm-session-status-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
}

/* Notice Bar */
.adm-session-notice {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 18px;
    color: #1E40AF;
}

/* Logout Button */
div.st-key-btn_admin_logout > button,
.st-key-btn_admin_logout button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: 1.5px solid #1D4ED8 !important;
    border-radius: 10px !important;
    padding: 10px 22px 10px 52px !important;
    min-height: 48px !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    position: relative !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
    transition: all 0.2s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
}

div.st-key-btn_admin_logout > button:hover,
.st-key-btn_admin_logout button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38) !important;
    transform: translateY(-1px) !important;
}

div.st-key-btn_admin_logout > button::before,
.st-key-btn_admin_logout button::before {
    content: '' !important;
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 24px !important;
    height: 24px !important;
    border-radius: 6px !important;
    background-color: #EF4444 !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 14px 14px !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/%3E%3Cpolyline points='16 17 21 12 16 7'/%3E%3Cline x1='21' y1='12' x2='9' y2='12'/%3E%3C/svg%3E") !important;
    z-index: 2 !important;
}

div.st-key-btn_admin_logout > button p,
.st-key-btn_admin_logout button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    margin: 0 !important;
}

/* Footer Trust Badges */
.adm-session-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 22px;
    padding-top: 14px;
    border-top: 1px solid #E2E8F0;
    font-size: 0.74rem;
    color: #64748B;
    flex-wrap: wrap;
    gap: 12px;
}

/* Responsive Rules for Mobile */
@media (max-width: 768px) {
    .adm-session-card {
        padding: 16px;
    }
    .adm-session-card-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .adm-session-hdr-right {
        align-items: flex-start;
        padding-right: 0;
        margin-top: 10px;
    }
    .adm-session-banner {
        flex-direction: column;
        align-items: flex-start;
        padding: 16px;
    }
    .adm-session-divider {
        display: none;
    }
    .adm-session-footer {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
}

/* ============================================================
   DocMindX AI -- ADMIN PORTAL UNIFIED DESIGN SYSTEM
   ============================================================ */
.adm-portal-outer-wrap {
    width: 100%;
    max-width: 100%;
    margin: 0 0 24px 0;
    box-sizing: border-box;
}

.adm-portal-card {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 18px;
    box-shadow: 0 6px 28px rgba(37, 99, 235, 0.07);
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

.adm-portal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    margin-bottom: 20px;
}

.adm-portal-hdr-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.adm-portal-icon-box {
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%);
    border: 1.5px solid #BFDBFE;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.16);
    flex-shrink: 0;
}

.adm-portal-title {
    margin: 0;
    font-size: 1.65rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.01em;
    line-height: 1.2;
}

.adm-portal-title span {
    color: #2563EB;
}

.adm-portal-subtitle {
    margin: 3px 0 0 0;
    font-size: 0.86rem;
    color: #64748B;
    line-height: 1.35;
}

.adm-portal-filter-lbl {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #334155;
    margin-bottom: 6px;
}

.adm-portal-counter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 14px 0 16px 0;
    font-size: 0.84rem;
    color: #475569;
    flex-wrap: wrap;
    gap: 8px;
}

.adm-portal-status-pill-green {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #059669;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.76rem;
    font-weight: 700;
}

/* User Account Cards */
.adm-user-row-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.adm-user-row-card:hover {
    border-color: #BFDBFE;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
}

.adm-avatar-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.95rem;
    flex-shrink: 0;
}

/* ============================================================
   ADMIN USER MANAGEMENT RESPONSIVE CARD SYSTEM
   ============================================================ */
.adm-user-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.adm-user-card-main {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;
    min-width: 220px;
}

.adm-user-meta-wrap {
    min-width: 0;
    flex: 1;
}

.adm-user-row-id-mail {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.adm-user-badge-id {
    background: #EFF6FF;
    color: #2563EB;
    border: 1px solid #DBEAFE;
    padding: 1px 7px;
    border-radius: 6px;
    font-size: 0.70rem;
    font-weight: 700;
    flex-shrink: 0;
}

.adm-user-mail-txt {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--mm-text-primary);
    word-break: break-word;
    line-height: 1.3;
}

.adm-user-name-txt {
    font-size: 0.80rem;
    color: #64748B;
    margin-top: 2px;
    font-weight: 600;
}

.adm-user-chips-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 6px;
}

.adm-chip-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 0.70rem;
    color: #64748B;
    font-weight: 500;
}

.adm-user-card-pills {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    align-self: flex-start;
}

/* Action Toolbar: Strictly Forces 3 Side-by-Side Equal Columns Even On Mobile */
.adm-user-actions-wrap {
    margin-top: 4px;
    margin-bottom: 8px;
    width: 100%;
}

.adm-user-actions-wrap [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    width: 100% !important;
}

.adm-user-actions-wrap [data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
    width: 33.333% !important;
    padding: 0 !important;
}

.adm-user-actions-wrap button {
    width: 100% !important;
    min-height: 36px !important;
    height: 36px !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    padding: 2px 6px !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    box-shadow: none !important;
}

/* Button 1: Disable/Enable styling */
.adm-user-actions-wrap [data-testid="column"]:first-child button {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    color: #2563EB !important;
}
.adm-user-actions-wrap [data-testid="column"]:first-child button:hover {
    background: #DBEAFE !important;
    border-color: #93C5FD !important;
    color: #1D4ED8 !important;
}

/* Button 2: Edit popover styling */
.adm-user-actions-wrap [data-testid="column"]:nth-child(2) button {
    background: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    color: #334155 !important;
}
.adm-user-actions-wrap [data-testid="column"]:nth-child(2) button:hover {
    background: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Button 3: Delete popover styling */
.adm-user-actions-wrap [data-testid="column"]:nth-child(3) button {
    background: #FFF1F2 !important;
    border: 1px solid #FECDD3 !important;
    color: #E11D48 !important;
}
.adm-user-actions-wrap [data-testid="column"]:nth-child(3) button:hover {
    background: #FFE4E6 !important;
    border-color: #FDA4AF !important;
    color: #BE123C !important;
}

/* Scan Record Cards */
.adm-scan-row-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
}

.adm-scan-row-card:hover {
    border-color: #BFDBFE;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
}

.adm-scan-id-badge {
    background: #EFF6FF;
    border: 1px solid #DBEAFE;
    border-radius: 12px;
    padding: 6px 16px;
    text-align: center;
}

/* Audit Log Cards */
.adm-audit-row-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
}

.adm-audit-row-card:hover {
    border-color: #BFDBFE;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.06);
}

.adm-chip-meta {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.74rem;
    color: #475569;
}

/* "View All Logs ->" Button Styling */
.st-key-btn_adm_view_all_logs {
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
}

.st-key-btn_adm_view_all_logs button {
    background: #EFF6FF !important;
    border: 1px solid #DBEAFE !important;
    color: #2563EB !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    padding: 5px 14px !important;
    border-radius: 8px !important;
    line-height: 1.3 !important;
    min-height: 32px !important;
    height: 32px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    width: auto !important;
    margin-left: auto !important;
}

.st-key-btn_adm_view_all_logs button:hover {
    background: #DBEAFE !important;
    border-color: #93C5FD !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12) !important;
}

.st-key-btn_adm_view_all_logs button:active {
    transform: translateY(0) !important;
}

/* User Metadata Detail Box */
.adm-user-details-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
}

/* Top Admin Header Card */
.adm-top-header-card {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 16px;
    padding: 16px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    position: relative;
    overflow: hidden;
}

/* KPI Cards */
.adm-kpi-card {
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
}

.adm-kpi-card:hover {
    border-color: #BFDBFE;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
}

.adm-kpi-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* Activity Items */
.adm-activity-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
}

.adm-activity-card:hover {
    border-color: #BFDBFE;
}

@media (max-width: 768px) {
    .adm-portal-card {
        padding: 16px;
    }
    .adm-portal-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .adm-scan-row-card, .adm-user-row-card, .adm-audit-row-card, .adm-top-header-card {
        flex-direction: column;
        align-items: flex-start;
        padding: 14px;
    }
    .adm-kpi-card {
        padding: 12px;
    }
}

/* ==========================================================================
   MEDICAL REPORT - EQUAL SIZED CARDS (DOCUMENT UPLOAD & OCR TEXT STREAM)
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]),
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_ocr_card),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_ocr_card"]) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) [data-testid="stLayoutWrapper"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) [data-testid="stLayoutWrapper"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

div[class*="st-key-med_report_upload_card"],
div[class*="st-key-med_report_ocr_card"],
.st-key-med_report_upload_card,
.st-key-med_report_ocr_card,
.st-key-med_report_upload_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_ocr_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_upload_card div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_ocr_card div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-med_report_upload_card),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-med_report_ocr_card),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-med_report_upload_card"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-med_report_ocr_card"]) {
    height: 100% !important;
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    box-sizing: border-box !important;
    border-radius: 14px !important;
}

div[class*="st-key-med_report_upload_card"] > div[data-testid="stVerticalBlock"],
div[class*="st-key-med_report_ocr_card"] > div[data-testid="stVerticalBlock"],
.st-key-med_report_upload_card > div[data-testid="stVerticalBlock"],
.st-key-med_report_ocr_card > div[data-testid="stVerticalBlock"],
.st-key-med_report_upload_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"],
.st-key-med_report_ocr_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

/* Ensure action button aligns at the bottom of upload card */
.st-key-med_report_upload_card .stButton,
div[class*="st-key-med_report_upload_card"] .stButton {
    margin-top: auto !important;
    padding-top: 10px !important;
}

/* Ensure OCR textarea expands to fill exact available vertical space */
div[class*="st-key-med_report_ocr_card"] .stTextArea,
.st-key-med_report_ocr_card .stTextArea,
div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"],
.st-key-med_report_ocr_card [data-testid="stTextArea"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    margin-bottom: 0 !important;
}

div[class*="st-key-med_report_ocr_card"] .stTextArea > div,
.st-key-med_report_ocr_card .stTextArea > div,
div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"] > div,
.st-key-med_report_ocr_card [data-testid="stTextArea"] > div {
    flex: 1 1 auto !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}

div[class*="st-key-med_report_ocr_card"] .stTextArea textarea,
.st-key-med_report_ocr_card .stTextArea textarea,
div[class*="st-key-med_report_ocr_card"] textarea,
.st-key-med_report_ocr_card textarea {
    flex: 1 1 auto !important;
    height: 100% !important;
    min-height: 180px !important;
    box-sizing: border-box !important;
    resize: none !important;
}

/* ==========================================================================
   CUSTOMER SUPPORT & HELPDESK - EQUAL SIZED CARDS (FORM & INFO PANELS)
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]),
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) [data-testid="stLayoutWrapper"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) [data-testid="stLayoutWrapper"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
}

/* Left card container stretches full height */
div[class*="st-key-about_supp_form_card"],
.st-key-about_supp_form_card,
.st-key-about_supp_form_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_form_card div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-about_supp_form_card"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_form_card) {
    height: 100% !important;
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    box-sizing: border-box !important;
    border-radius: 14px !important;
}

div[class*="st-key-about_supp_form_card"] > div[data-testid="stVerticalBlock"],
.st-key-about_supp_form_card > div[data-testid="stVerticalBlock"],
.st-key-about_supp_form_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

/* Ensure Send Support Ticket button aligns nicely to bottom */
.st-key-about_supp_form_card .stButton,
div[class*="st-key-about_supp_form_card"] .stButton {
    margin-top: auto !important;
    padding-top: 10px !important;
}

/* Right column stretches cards to fill vertical space */
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    gap: 12px !important;
}

.st-key-about_supp_card_info,
.st-key-about_supp_card_report,
.st-key-about_supp_card_help,
div[class*="st-key-about_supp_card_info"],
div[class*="st-key-about_supp_card_report"],
div[class*="st-key-about_supp_card_help"],
.st-key-about_supp_card_info > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_card_report > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_card_help > div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_info),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_report),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_help) {
    flex: 1 1 auto !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    border-radius: 12px !important;
}
</style>
"""
DARK_CSS_OVERRIDE = """
<style>
/* ============================================================
   DocMindX AI -- COMPLETE CLINICAL DARK MODE SYSTEM OVERRIDE
   ============================================================ */

/* -- 1. Root Variable Tokens for Dark Mode -- */
:root {
    --mm-brand-primary: #3B82F6 !important;
    --mm-brand-secondary: #06B6D4 !important;
    --mm-brand-accent: #10B981 !important;
    --mm-brand-hover: #60A5FA !important;
    --mm-brand-active: #2563EB !important;
    --mm-brand-subtle: #0C2A4A !important;
    --mm-brand-border: #1E3A5F !important;

    --mm-bg-base: #0B1220 !important;
    --mm-bg-surface: #111827 !important;
    --mm-bg-sidebar: #070C16 !important;

    --mm-text-primary: #F8FAFC !important;
    --mm-text-secondary: #94A3B8 !important;
    --mm-text-muted: #64748B !important;

    --mm-border-color: #1F2937 !important;
    --mm-border-light: #1A2333 !important;

    --mm-status-critical: #EF4444 !important;
    --mm-status-critical-bg: #2D1215 !important;
    --mm-status-warning: #F59E0B !important;
    --mm-status-warning-bg: #2D1C00 !important;
    --mm-status-success: #22C55E !important;
    --mm-status-success-bg: #0F2D1E !important;
    --mm-status-info: #06B6D4 !important;
    --mm-status-info-bg: #083344 !important;

    --mm-shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    --mm-shadow-card: 0 4px 14px rgba(0, 0, 0, 0.5) !important;
    --mm-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.65) !important;
}

/* -- 2. Core App Background & Base Layout -- */
html, body, .stApp, section.main, .stMainBlockContainer, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"], .block-container {
    background-color: #0B1220 !important;
    background: #0B1220 !important;
    color: #F8FAFC !important;
}

/* -- 3. Typography & Global Elements -- */
h1, h2, h3, h4, h5, h6, b, strong, .mm-card-title, .mm-step-text-title, .mm-header-title {
    color: #F8FAFC !important;
}
p, span, div {
    color: #CBD5E1 !important;
}
.mm-section-header {
    color: #F8FAFC !important;
    border-bottom-color: #1E293B !important;
}
.mm-header-subtitle,
.mm-step-text-sub {
    color: #94A3B8 !important;
}

/* -- 4. Top Header Cards (All Panels) -- */
div[class*="st-key-mm_top_header_card"] {
    background: #111827 !important;
    background-color: #111827 !important;
    border-color: #1E293B !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
}
div[class*="st-key-mm_top_header_card"] div {
    color: #F8FAFC !important;
}
div[class*="st-key-mm_top_header_card"] .mm-badge-brand {
    background: rgba(37, 99, 235, 0.15) !important;
    color: #60A5FA !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
}
div[class*="st-key-mm_top_header_card"] .mm-badge-online-pill {
    background: #0F2D1E !important;
    color: #4ADE80 !important;
    border-color: #14532D !important;
}

/* Header Language Selector (Pill Dropdown) */
div[class*="st-key-hdr_lang_"] [data-baseweb="select"] > div {
    background: #1E293B !important;
    background-color: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
}
div[class*="st-key-hdr_lang_"] [data-baseweb="select"] span {
    color: #F8FAFC !important;
}
div[class*="st-key-hdr_lang_"] [data-baseweb="select"] svg {
    fill: #CBD5E1 !important;
}

/* -- 5. Cards, Containers & Custom Badges -- */
.mm-card,
.mm-hospital-card,
.mm-header-bar,
.mm-quick-action-item,
.mm-ocr-box,
.mm-footer-trust-bar,
.stContainer,
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #111827 !important;
    background-color: #111827 !important;
    border-color: #1E293B !important;
    color: #F8FAFC !important;
}
.mm-card:hover,
.mm-hospital-card:hover {
    border-color: rgba(225,29,72,0.35) !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.55), 0 0 14px rgba(37, 99, 235,0.22) !important;
}
.mm-card * { color: #F8FAFC !important; }
.mm-card p, .mm-card span, .mm-card div { color: #CBD5E1 !important; }

.mm-doc-pill,
.mm-ontology-pill {
    background: #111827 !important;
    border-color: #1E293B !important;
    color: #E2E8F0 !important;
}
.mm-doc-pill.active {
    background: #1E3A8A !important;
    border-color: #3B82F6 !important;
    color: #FFFFFF !important;
}
.mm-chip {
    background: #1E293B !important;
    color: #CBD5E1 !important;
}

/* -- 6. Clinical Stepper -- */
.mm-stepper {
    background: #111827 !important;
    background-color: #111827 !important;
    border-color: #1E293B !important;
}
.mm-stepper .mm-step-text-title { color: #F1F5F9 !important; }
.mm-stepper .mm-step-text-title.active { color: #60A5FA !important; }
.mm-stepper .mm-step-text-sub { color: #94A3B8 !important; }
.mm-stepper .mm-step-arrow { color: #64748B !important; }
.mm-stepper .mm-step-num {
    background: #1E293B !important;
    color: #94A3B8 !important;
    border-color: #334155 !important;
}
.mm-stepper .mm-step-num.active {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%) !important;
    color: #FFFFFF !important;
    border-color: #2563EB !important;
    box-shadow: 0 0 14px rgba(37, 99, 235, 0.5) !important;
}
.mm-stepper .mm-step-num.done {
    background: #10B981 !important;
    color: #FFFFFF !important;
    border-color: #059669 !important;
}

/* -- 7. Form Labels, Inputs & Textboxes -- */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stRadio label,
.stCheckbox label,
.stSlider label,
.stFileUploader label,
div[data-testid="stRadio"] label,
div[data-testid="stCheckbox"] label {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}
div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] label p,
div[data-testid="stCheckbox"] label span,
div[data-testid="stCheckbox"] label p {
    color: #CBD5E1 !important;
}

/* Radio circle inner styles */
div[data-testid="stRadio"] [role="radiogroup"] > label > div:first-child {
    background-color: #0F172A !important;
    border-color: #475569 !important;
}

input,
textarea,
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
[data-baseweb="base-input"] textarea,
.stTextInput input,
.stTextInput > div,
.stTextInput > div > div,
.stTextArea textarea,
.stTextArea > div,
.stTextArea > div > div,
.stSelectbox > div,
.stSelectbox > div > div,
[data-baseweb="select"] > div {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1.5px solid #1E2E4E !important;
    border-color: #1E2E4E !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
}

input:focus,
textarea:focus,
[data-baseweb="input"]:focus-within,
[data-baseweb="select"]:focus-within > div,
.stTextInput > div > div:focus-within,
.stTextArea > div > div:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.3) !important;
}

input::placeholder,
textarea::placeholder,
[data-baseweb="select"] input::placeholder,
[data-baseweb="select"] div[class*="Placeholder"],
[data-baseweb="select"] div[class*="placeholder"],
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}

/* MultiSelect Selected Badges/Tags */
[data-baseweb="tag"] {
    background-color: rgba(37, 99, 235,0.25) !important;
    background: rgba(37, 99, 235,0.25) !important;
    border: 1px solid rgba(37, 99, 235,0.55) !important;
}
[data-baseweb="tag"] span,
[data-baseweb="tag"] svg {
    color: #FCA5A5 !important;
    fill: #FCA5A5 !important;
}

/* Dropdown Menu Popovers */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="menu"] li,
[role="listbox"],
[role="option"],
ul[role="listbox"],
div[data-testid="stSelectboxVirtualDropdown"],
ul[data-testid="stVirtualDropdown"] {
    background-color: #111827 !important;
    background: #111827 !important;
    color: #F8FAFC !important;
    border: 1px solid #1E293B !important;
}

li[role="option"],
div[role="option"],
[data-baseweb="menu"] li {
    color: #F8FAFC !important;
    border-bottom: 1px solid #1E293B !important;
}
li[role="option"] *,
div[role="option"] *,
[data-baseweb="menu"] li * {
    color: #F8FAFC !important;
}

li[role="option"]:hover,
div[role="option"]:hover,
li[role="option"][aria-selected="true"],
div[role="option"][aria-selected="true"],
li[role="option"]:focus,
div[role="option"]:focus,
[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background-color: #1E293B !important;
    background: #1E293B !important;
    color: #60A5FA !important;
}
li[role="option"]:hover *,
div[role="option"]:hover *,
li[role="option"][aria-selected="true"] *,
div[role="option"][aria-selected="true"] * {
    color: #60A5FA !important;
}

/* -- 8. File Uploader Dropzone -- */
[data-testid="stFileUploader"],
[data-testid="stFileUploadDropzone"],
section[data-testid="stFileUploadDropzone"],
.stFileUploader,
.stFileUploader > div,
.stFileUploader section,
div[data-testid="stFileUploadDropzone"] {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}
[data-testid="stFileUploadDropzone"]:hover,
section[data-testid="stFileUploadDropzone"]:hover {
    border-color: #2563EB !important;
    background-color: #1E293B !important;
    background: #1E293B !important;
}
[data-testid="stFileUploadDropzone"] div,
[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] label,
section[data-testid="stFileUploadDropzone"] * {
    color: #94A3B8 !important;
}
[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploader"] button {
    background-color: #1E293B !important;
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F8FAFC !important;
}

/* -- 9. Buttons & Interactive Elements -- */
.stButton > button {
    background-color: #1E293B !important;
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F1F5F9 !important;
}
.stButton > button:hover {
    background-color: #27354A !important;
    border-color: #475569 !important;
    color: #FFFFFF !important;
}
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%) !important;
    color: #FFFFFF !important;
    border-color: #2563EB !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235,0.4) !important;
}

/* Quick Action / Symptom Chips */
.st-key-pop_sym_chip_0 button, .st-key-pop_sym_chip_1 button,
.st-key-pop_sym_chip_2 button, .st-key-pop_sym_chip_3 button,
.st-key-pop_sym_chip_4 button, .st-key-pop_sym_chip_5 button,
.st-key-pop_sym_chip_6 button {
    background: #1E293B !important;
    color: #CBD5E1 !important;
    border-color: #334155 !important;
}
.st-key-pop_sym_chip_0 button:hover, .st-key-pop_sym_chip_1 button:hover,
.st-key-pop_sym_chip_2 button:hover, .st-key-pop_sym_chip_3 button:hover,
.st-key-pop_sym_chip_4 button:hover, .st-key-pop_sym_chip_5 button:hover,
.st-key-pop_sym_chip_6 button:hover {
    background: #27354A !important;
    border-color: #38BDF8 !important;
    color: #38BDF8 !important;
}

.st-key-btn_describe_words button,
.st-key-qa_upload_presc button,
.st-key-qa_find_hosp button,
.st-key-qa_health_tips button {
    background: #1E293B !important;
    color: #93C5FD !important;
    border-color: #334155 !important;
}
.st-key-btn_describe_words button:hover,
.st-key-qa_upload_presc button:hover,
.st-key-qa_find_hosp button:hover,
.st-key-qa_health_tips button:hover {
    background: #27354A !important;
    border-color: #38BDF8 !important;
    color: #38BDF8 !important;
}
.st-key-clear_all_sym_btn button {
    background: #2D1215 !important;
    color: #FCA5A5 !important;
    border-color: #1E3A5F !important;
}

/* -- 10. Sidebar Navigation (Dark Mode Colors) -- */
[data-testid="stSidebar"] {
    background-color: #070C16 !important;
    border-right-color: #1E293B !important;
}
[data-testid="stSidebar"] * { color: #F8FAFC !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #94A3B8 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #111827 !important;
    border-color: #1E293B !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    background-color: #141D2E !important;
    border-color: #23324D !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background-color: #1E293B !important;
    border-color: #38BDF8 !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(37, 99, 235, 0.35) 0%, rgba(6, 182, 212, 0.18) 100%) !important;
    border-left: 5px solid #2563EB !important;
    border-color: #2563EB !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.30) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label,
[data-testid="stSidebar"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div[role="radiogroup"] label p,
[data-testid="stSidebar"] div[role="radiogroup"] label span,
[data-testid="stSidebar"] div[role="radiogroup"] label div {
    color: #F8FAFC !important;
}

/* -- 11. Tabs & Navigation -- */
.stTabs [data-baseweb="tab-list"] {
    background-color: #111827 !important;
    border-bottom-color: #1E293B !important;
}
.stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
}
.stTabs [aria-selected="true"] {
    color: #60A5FA !important;
    border-bottom-color: #3B82F6 !important;
}

/* -- 12. Expanders, Metrics & Uploaders -- */
[data-testid="stMetric"] {
    background: #111827 !important;
    border-color: #1E293B !important;
}
[data-testid="stMetricLabel"] { color: #94A3B8 !important; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; }

.streamlit-expanderHeader,
details[data-testid="stExpander"] {
    background: #111827 !important;
    border-color: #1E293B !important;
    color: #F8FAFC !important;
}
.streamlit-expanderContent {
    background: #0F172A !important;
    border-color: #1E293B !important;
    color: #CBD5E1 !important;
}

/* -- 13. Floating Chatbot Drawer & Suggestion Chips -- */
.floating-chat-container,
div[class*="st-key-slide_chat_drawer"],
div.st-key-slide_chat_drawer,
.st-key-slide_chat_drawer {
    background: #0A0E1A !important;
    background-color: #0A0E1A !important;
    border-color: #1E293B !important;
    color: #F8FAFC !important;
}
div.st-key-slide_chat_drawer [data-testid="stVerticalBlock"],
div.st-key-slide_chat_drawer [data-testid="stHorizontalBlock"],
div.st-key-slide_chat_drawer [data-testid="element-container"],
div.st-key-slide_chat_drawer [data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
    background-color: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}
div.st-key-slide_chat_drawer [data-testid="stHeightContainer"] {
    background: #0A0E1A !important;
    border-color: #1E293B !important;
}
div[class*="st-key-floating_chat_user_input"] [data-baseweb="base-input"],
div[class*="st-key-floating_chat_user_input"] [data-baseweb="input"],
div[class*="st-key-floating_chat_user_input"] [data-baseweb="base-input"] input,
div[class*="st-key-floating_chat_user_input"] .stTextInput > div > div,
div[class*="st-key-floating_chat_user_input"] .stTextInput > div > div > input,
.st-key-slide_chat_form [data-baseweb="base-input"],
.st-key-slide_chat_form [data-baseweb="input"],
.st-key-slide_chat_form [data-baseweb="base-input"] input,
.st-key-slide_chat_form .stTextInput > div > div,
.st-key-slide_chat_form .stTextInput > div > div > input {
    background-color: #1E293B !important;
    background: #1E293B !important;
    color: #F8FAFC !important;
    border-color: #334155 !important;
}
div[class*="st-key-popup_unified_header"] {
    background: linear-gradient(135deg, #0B1220 0%, #1E3A8A 50%, #2563EB 100%) !important;
}
div[class*="st-key-dyn_chip_"] button,
div[class*="st-key-dyn_chip_"] [data-testid="baseButton-secondary"],
.floating-chat-container div[class*="st-key-dyn_chip_"] button {
    background-color: #1E293B !important;
    background: #1E293B !important;
    color: #E2E8F0 !important;
    border-color: #334155 !important;
}
div[class*="st-key-dyn_chip_"] button:hover,
div[class*="st-key-dyn_chip_"] [data-testid="baseButton-secondary"]:hover {
    background-color: #1E293B !important;
    border-color: #38BDF8 !important;
    color: #38BDF8 !important;
}
div[class*="st-key-drawer_clear_chat_btn"] button,
div[class*="st-key-drawer_close_x_btn"] button,
.st-key-drawer_clear_chat_btn button,
.st-key-drawer_close_x_btn button {
    background-color: #1E293B !important;
    background: #1E293B !important;
    color: #CBD5E1 !important;
    border-color: #334155 !important;
}
div[class*="st-key-drawer_clear_chat_btn"] button:hover,
div[class*="st-key-drawer_close_x_btn"] button:hover,
.st-key-drawer_clear_chat_btn button:hover,
.st-key-drawer_close_x_btn button:hover {
    background-color: #1E293B !important;
    border-color: #38BDF8 !important;
    color: #38BDF8 !important;
}

/* Chat Messages */
[data-testid="stChatMessage"],
.stChatMessage {
    background-color: #0F172A !important;
    background: #0F172A !important;
    border: 1px solid #1E293B !important;
    color: #F8FAFC !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em {
    color: #E2E8F0 !important;
}

/* -- 14. Dialogs, Modals & Quick Question Buttons -- */
[data-testid="stModal"],
div[data-testid="stDialog"] > div,
div[role="dialog"] {
    background-color: #0B1220 !important;
    background: #0B1220 !important;
    border-color: #1E2E4E !important;
    color: #F8FAFC !important;
}
div[data-testid="stDialog"] header,
div[role="dialog"] header {
    background-color: #0B1220 !important;
    color: #F8FAFC !important;
    border-bottom-color: #1E293B !important;
}
div[data-testid="stDialog"] .stButton > button,
.st-key-p2_quick_q_0 button,
.st-key-p2_quick_q_1 button,
.st-key-p2_quick_q_2 button {
    background-color: #1A2333 !important;
    background: #1A2333 !important;
    color: #94A3B8 !important;
    border-color: #1E293B !important;
}
div[data-testid="stDialog"] .stButton > button:hover,
.st-key-p2_quick_q_0 button:hover,
.st-key-p2_quick_q_1 button:hover,
.st-key-p2_quick_q_2 button:hover {
    background-color: #1E293B !important;
    border-color: #3B82F6 !important;
    color: #60A5FA !important;
}
div[data-testid="stStatusWidget"] {
    background: #111827 !important;
    border-color: #1E293B !important;
    color: #F8FAFC !important;
}

/* ==========================================================================
   15. ADVANCED MICRO-INTERACTIONS, TRANSITIONS & ANIMATIONS ENGINE
   ========================================================================== */

/* ── Smooth Scrolling ── */
html {
    scroll-behavior: smooth !important;
}

/* ── Global Card & Container Entrance Animations ── */
@keyframes mmFadeInUp {
    0% {
        opacity: 0;
        transform: translateY(10px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes mmFadeInScale {
    0% {
        opacity: 0;
        transform: scale(0.97);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes mmShimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes mmPulseGlow {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.4);
    }
    50% {
        box-shadow: 0 0 0 6px rgba(37, 99, 235, 0);
    }
}

@keyframes mmToastIn {
    0% {
        opacity: 0;
        transform: translateY(-8px) scale(0.98);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Card Entrance animation */
.mm-card,
.mm-hospital-card,
div[class*="st-key-mm_top_header_card"],
[data-testid="stMetric"],
[data-testid="stChatMessage"] {
    animation: mmFadeInUp 0.32s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* ── Micro-Interaction: Smooth Elevation & Hover Transitions ── */
.mm-card,
.mm-hospital-card,
[data-testid="stMetric"],
.streamlit-expanderHeader {
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1),
                border-color 0.22s cubic-bezier(0.16, 1, 0.3, 1),
                background-color 0.22s ease !important;
}

.mm-card:hover,
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12), 0 2px 6px rgba(0, 0, 0, 0.04) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
}

[data-theme="dark"] .mm-card:hover,
[data-theme="dark"] [data-testid="stMetric"]:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6), 0 0 14px rgba(59, 130, 246, 0.2) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
}

/* ── Button Micro-Interactions & Ripple Feedback ── */
.stButton > button,
.mm-btn,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-primary"] {
    position: relative !important;
    overflow: hidden !important;
    transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.18s cubic-bezier(0.16, 1, 0.3, 1),
                background-color 0.18s ease,
                border-color 0.18s ease !important;
}

.stButton > button:hover,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22) !important;
}

.stButton > button:active,
button[data-testid="baseButton-secondary"]:active,
button[data-testid="baseButton-primary"]:active {
    transform: scale(0.96) translateY(0) !important;
    box-shadow: 0 1px 3px rgba(37, 99, 235, 0.15) !important;
    transition: transform 0.08s ease !important;
}

/* Ripple Span */
.mm-ripple {
    position: absolute;
    border-radius: 50%;
    transform: scale(0);
    animation: mmRippleEffect 0.55s linear;
    background-color: rgba(255, 255, 255, 0.35);
    pointer-events: none;
    z-index: 10;
}
[data-theme="dark"] .mm-ripple {
    background-color: rgba(56, 189, 248, 0.35);
}
@keyframes mmRippleEffect {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

/* ── Skeleton Loaders ── */
.mm-skeleton {
    background: linear-gradient(90deg, rgba(226, 232, 240, 0.6) 25%, rgba(248, 250, 252, 0.95) 50%, rgba(226, 232, 240, 0.6) 75%) !important;
    background-size: 200% 100% !important;
    animation: mmShimmer 1.5s infinite !important;
    border-radius: var(--mm-radius-md) !important;
}

[data-theme="dark"] .mm-skeleton {
    background: linear-gradient(90deg, rgba(30, 41, 59, 0.7) 25%, rgba(51, 65, 85, 0.95) 50%, rgba(30, 41, 59, 0.7) 75%) !important;
    background-size: 200% 100% !important;
    animation: mmShimmer 1.5s infinite !important;
}

/* ── Expanders & Accordions ── */
.streamlit-expanderContent {
    transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* ── Alert & Toast Notifications ── */
.stAlert,
[data-testid="stAlert"] {
    animation: mmToastIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) both !important;
    border-radius: var(--mm-radius-lg) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

/* ── Interactive Badges & Chips Lift ── */
.mm-badge,
[data-baseweb="tag"],
div[class*="st-key-pop_sym_chip_"] button,
div[class*="st-key-chip_"] button,
div[class*="st-key-dyn_chip_"] button {
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.mm-badge:hover,
[data-baseweb="tag"]:hover,
div[class*="st-key-pop_sym_chip_"] button:hover,
div[class*="st-key-chip_"] button:hover,
div[class*="st-key-dyn_chip_"] button:hover {
    transform: translateY(-1px) !important;
}

/* ── Active Status Indicator Pulse ── */
.mm-badge-online-pill::before {
    content: "";
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #16A34A;
    margin-right: 6px;
    animation: mmPulseGlow 2s infinite;
}

/* ── Section 16 Dark Overrides: Medicine & Yoga Cards ── */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-med-card-content),
.mm-med-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
}
.mm-med-hero-img-box {
    background: #0B1220 !important;
}
.mm-med-title-top {
    color: #F8FAFC !important;
}
.mm-med-desc {
    color: #94A3B8 !important;
}
.mm-med-info-box-grid {
    background: #0B1220 !important;
    border-color: #1F2937 !important;
}
.mm-med-stat-divider {
    background: #1F2937 !important;
}
.mm-med-stat-label {
    color: #94A3B8 !important;
}
.mm-med-stat-val {
    color: #F8FAFC !important;
}
.mm-med-stat-icon-blue {
    background: rgba(14, 165, 233, 0.2) !important;
    color: #38BDF8 !important;
}
.mm-med-stat-icon-orange {
    background: rgba(234, 88, 12, 0.2) !important;
    color: #FB923C !important;
}
.mm-med-stat-icon-purple {
    background: rgba(124, 58, 237, 0.2) !important;
    color: #A78BFA !important;
}
.mm-med-badge-rx {
    background: rgba(14, 165, 233, 0.15) !important;
    color: #38BDF8 !important;
    border-color: rgba(14, 165, 233, 0.35) !important;
}
.mm-med-badge-verified {
    background: rgba(34, 197, 94, 0.15) !important;
    color: #4ADE80 !important;
    border-color: rgba(34, 197, 94, 0.35) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mm-yoga-card-content),
.mm-yoga-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
}

/* ==========================================================================
   REPORT & CLINICAL CARE CARDS DESIGN SYSTEM (Dark Mode Overrides)
   ========================================================================== */
.mm-triage-header-card {
    background: linear-gradient(135deg, #0B132B 0%, #0F172A 50%, rgba(30, 58, 138, 0.35) 100%) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
    border-left: 10px solid #3B82F6 !important;
    box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.7), 0 0 30px rgba(37, 99, 235, 0.22) !important;
}
.mm-triage-header-card::before {
    background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(59, 130, 246, 0) 70%) !important;
}
.mm-triage-icon-wrap {
    border-color: rgba(147, 197, 253, 0.5) !important;
    box-shadow: 0 12px 30px rgba(37, 99, 235, 0.55), 0 0 16px rgba(59, 130, 246, 0.4) !important;
}
.mm-triage-eyebrow {
    color: #93C5FD !important;
    background: rgba(30, 58, 138, 0.35) !important;
    border-color: rgba(96, 165, 250, 0.4) !important;
}
.mm-triage-pulse-dot {
    background: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3) !important;
}
.mm-triage-header-badge {
    background: rgba(15, 23, 42, 0.88) !important;
    border-color: rgba(96, 165, 250, 0.5) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55) !important;
}
.mm-triage-header-badge-sep {
    background: rgba(96, 165, 250, 0.45) !important;
}
.mm-triage-header-badge-text {
    color: #93C5FD !important;
}
.mm-summary-card {
    background: rgba(37, 99, 235, 0.09) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    border-left: 5px solid #3B82F6 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-recovery-card {
    background: rgba(16, 185, 129, 0.09) !important;
    border-color: rgba(16, 185, 129, 0.35) !important;
    border-left: 5px solid #10B981 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-foment-card {
    background: rgba(234, 88, 12, 0.08) !important;
    border-color: rgba(249, 115, 22, 0.35) !important;
    border-left: 5px solid #F97316 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-seasonal-card {
    background: rgba(234, 88, 12, 0.08) !important;
    border-color: rgba(249, 115, 22, 0.35) !important;
    border-left: 5px solid #F97316 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-review-card-blue {
    background: #111827 !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-review-card-purple {
    background: #111827 !important;
    border-color: rgba(124, 58, 237, 0.35) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-review-card-green {
    background: #111827 !important;
    border-color: rgba(16, 185, 129, 0.35) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-review-row-blue {
    background: rgba(37, 99, 235, 0.09) !important;
}
.mm-review-row-purple {
    background: rgba(124, 58, 237, 0.09) !important;
}
.mm-review-row-green {
    background: rgba(16, 185, 129, 0.09) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_1),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_2),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-gis_panel_col_3),
.st-key-gis_panel_col_1,
.st-key-gis_panel_col_2,
.st-key-gis_panel_col_3 {
    background: #111827 !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-gis-icon-box {
    background: rgba(37, 99, 235, 0.22) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    color: #60A5FA !important;
}
.mm-gis-title {
    color: #93C5FD !important;
}
.st-key-gis_city_search_input input,
div.st-key-gis_city_search_input input,
.st-key-gis_panel_col_1 input {
    text-indent: 26px !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%2360A5FA" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 15px 15px !important;
}
.st-key-gis_city_search_input input::placeholder,
.st-key-gis_panel_col_1 input::placeholder {
    text-indent: 26px !important;
}
.mm-gis-engine-badge {
    background: rgba(37, 99, 235, 0.18) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    color: #60A5FA !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
}
.mm-gis-helpline-box {
    background: rgba(2, 132, 199, 0.15) !important;
    border-color: rgba(2, 132, 199, 0.35) !important;
    color: #38BDF8 !important;
}
.mm-diag-test-card {
    background: rgba(109, 40, 217, 0.09) !important;
    border-color: rgba(139, 92, 246, 0.35) !important;
    border-left: 5px solid #8B5CF6 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-diag-chip {
    background: rgba(124, 58, 237, 0.22) !important;
    border-color: rgba(167, 139, 250, 0.4) !important;
    color: #DDD6FE !important;
}
.mm-diag-chip:hover {
    background: rgba(124, 58, 237, 0.35) !important;
}
.mm-dietary-card {
    background: #111827 !important;
    border-color: rgba(16, 185, 129, 0.4) !important;
    border-left: 5px solid #10B981 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-clinical-care-card {
    background: #111827 !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    border-left: 5px solid #3B82F6 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
}
.mm-subbox-green {
    background: rgba(16, 185, 129, 0.09) !important;
    border-color: rgba(16, 185, 129, 0.28) !important;
}
.mm-subbox-orange {
    background: rgba(234, 88, 12, 0.09) !important;
    border-color: rgba(234, 88, 12, 0.28) !important;
}
.mm-subbox-blue {
    background: rgba(37, 99, 235, 0.09) !important;
    border-color: rgba(37, 99, 235, 0.28) !important;
}
.mm-subbox-red {
    background: rgba(239, 68, 68, 0.09) !important;
    border-color: rgba(239, 68, 68, 0.28) !important;
}
.mm-subbox-purple {
    background: rgba(147, 51, 234, 0.09) !important;
    border-color: rgba(147, 51, 234, 0.28) !important;
}
.mm-text-green { color: #34D399 !important; }
.mm-text-orange { color: #FB923C !important; }
.mm-text-blue { color: #60A5FA !important; }
.mm-text-red { color: #F87171 !important; }
.mm-text-purple { color: #C4B5FD !important; }
.mm-cond-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    border-top: 3.5px solid #3B82F6 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
}
.mm-hospital-card {
    background: #111827 !important;
    border-color: #1F2937 !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45) !important;
}
.mm-hospital-card:hover {
    border-color: #3B82F6 !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.65), 0 0 14px rgba(59, 130, 246, 0.3) !important;
}
.mm-fac-dist-badge {
    background: rgba(2, 132, 199, 0.2) !important;
    color: #38BDF8 !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
}
.mm-fac-active-badge {
    background: rgba(5, 150, 105, 0.2) !important;
    color: #34D399 !important;
    border-color: rgba(52, 211, 153, 0.4) !important;
}
.mm-section-header-card {
    background: linear-gradient(135deg, #0F172A 0%, #111827 50%, rgba(30, 58, 138, 0.25) 100%) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    border-left: 6px solid #3B82F6 !important;
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.5) !important;
}
.mm-section-header-avatar {
    background: rgba(37, 99, 235, 0.2) !important;
    border-color: rgba(96, 165, 250, 0.45) !important;
    color: #60A5FA !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}
[data-theme="dark"] .mm-gis-action-row .stLinkButton > a {
    background-color: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-gis-action-row .stLinkButton > a:hover {
    background-color: #334155 !important;
    border-color: #64748B !important;
    color: #FFFFFF !important;
}

/* ── Dark Mode Overrides for Enterprise Session Cards ── */
[data-theme="dark"] .mm-session-card {
    background: #1E293B !important;
    border-color: #334155 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}
[data-theme="dark"] .mm-session-card summary {
    background: #0F172A !important;
}
[data-theme="dark"] .mm-session-card[open] > summary {
    background: #182234 !important;
    border-bottom-color: #334155 !important;
}
[data-theme="dark"] .mm-session-card .mm-session-summary-left {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-session-card .mm-chevron-icon {
    color: #60A5FA !important;
}
[data-theme="dark"] .mm-session-date {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-status-pill-abnormal {
    background: rgba(239, 68, 68, 0.2) !important;
    border-color: rgba(239, 68, 68, 0.4) !important;
    color: #F87171 !important;
}
[data-theme="dark"] .mm-status-pill-normal {
    background: rgba(34, 197, 94, 0.2) !important;
    border-color: rgba(34, 197, 94, 0.4) !important;
    color: #4ADE80 !important;
}
[data-theme="dark"] .mm-status-pill-warning {
    background: rgba(245, 158, 11, 0.2) !important;
    border-color: rgba(245, 158, 11, 0.4) !important;
    color: #FBBF24 !important;
}
[data-theme="dark"] .mm-session-body {
    background: #1E293B !important;
}
[data-theme="dark"] .mm-field-title,
[data-theme="dark"] .mm-right-title {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-field-desc {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-excerpt-box {
    background: rgba(14, 165, 233, 0.12) !important;
    border-color: rgba(14, 165, 233, 0.35) !important;
    color: #7DD3FC !important;
}
[data-theme="dark"] .mm-metric-card-high {
    background: rgba(239, 68, 68, 0.12) !important;
    border-color: rgba(239, 68, 68, 0.35) !important;
}
[data-theme="dark"] .mm-metric-card-normal {
    background: rgba(34, 197, 94, 0.12) !important;
    border-color: rgba(34, 197, 94, 0.35) !important;
}
[data-theme="dark"] .mm-metric-card-borderline {
    background: rgba(245, 158, 11, 0.12) !important;
    border-color: rgba(245, 158, 11, 0.35) !important;
}
[data-theme="dark"] .mm-metric-card-default {
    background: rgba(37, 99, 235, 0.12) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
}
[data-theme="dark"] .mm-metric-lbl {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-doctor-advisory {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
    color: #93C5FD !important;
}
[data-theme="dark"] .mm-footer-trust-bar {
    background: #1E293B !important;
    border-color: #334155 !important;
}
[data-theme="dark"] .mm-footer-slogan-pill {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(37, 99, 235, 0.35) !important;
    color: #93C5FD !important;
}
/* ==========================================================================
   ASSESSMENT STEP CARD SYSTEM (Image 2 & Image 4 Design)
   ========================================================================== */
.st-key-assessment_step_card,
div[data-testid="stVerticalBlockBorderWrapper"].st-key-assessment_step_card,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-assessment_step_card) {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid var(--mm-border, #E2E8F0) !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin-bottom: 20px !important;
}

.st-key-assessment_step_card > div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"].st-key-assessment_step_card > div[data-testid="stVerticalBlock"] {
    padding: 0 !important;
    gap: 14px !important;
}

.st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:first-child,
div[data-testid="stVerticalBlockBorderWrapper"].st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:first-child {
    padding: 0 !important;
    margin: 0 !important;
}

.st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:not(:first-child),
div[data-testid="stVerticalBlockBorderWrapper"].st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:not(:first-child) {
    padding-left: 20px !important;
    padding-right: 20px !important;
}

.st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:last-child,
div[data-testid="stVerticalBlockBorderWrapper"].st-key-assessment_step_card > div[data-testid="stVerticalBlock"] > div:last-child {
    padding-bottom: 20px !important;
}

/* Step Card Header Banner */
.mm-step-card-header {
    background: #F0F7FF;
    border-bottom: 1.2px solid #E2E8F0;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    border-radius: 18px 18px 0 0;
}

.mm-step-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
}

.mm-step-header-icon {
    width: 44px;
    height: 44px;
    min-width: 44px;
    border-radius: 12px;
    background: #E0F2FE;
    border: 1.2px solid #BAE6FD;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.mm-step-header-title {
    font-size: 1.18rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.25;
    margin: 0;
}

.mm-step-header-sub {
    font-size: 0.82rem;
    color: #64748B;
    margin: 3px 0 0 0;
    line-height: 1.4;
    font-weight: 500;
}

/* Info Callout Pill on Header Right (Image 4) */
.mm-step-info-pill {
    background: #E0F2FE;
    border: 1px solid #BAE6FD;
    border-radius: 12px;
    padding: 8px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.76rem;
    color: #0284C7;
    font-weight: 600;
    line-height: 1.35;
    max-width: 360px;
}
.mm-step-info-pill svg {
    flex-shrink: 0;
}

/* Field Labels with Vector Icons (Image 2 & 4) */
.mm-field-label-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.86rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 6px;
}
.mm-field-label-wrap svg {
    flex-shrink: 0;
}
.mm-field-icon-badge {
    width: 28px;
    height: 28px;
    min-width: 28px;
    border-radius: 8px;
    background: #EFF6FF;
    border: 1px solid #DBEAFE;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-field-icon-badge svg {
    width: 17px;
    height: 17px;
}

/* Step Progress Indicator (Image 2: STEP 1 OF 4 / BASIC INFORMATION) */
.mm-step-progress-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 8px;
    flex-shrink: 0;
}
.mm-step-progress-bar {
    width: 3.5px;
    height: 32px;
    background: #2563EB;
    border-radius: 2px;
    flex-shrink: 0;
}
.mm-step-progress-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
}
.mm-step-progress-step {
    font-size: 0.80rem;
    font-weight: 800;
    color: #2563EB;
    letter-spacing: 0.5px;
    line-height: 1.2;
}
.mm-step-progress-sub {
    font-size: 0.68rem;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 0.5px;
    line-height: 1.2;
    text-transform: uppercase;
}

/* Symptom Tag Pills (Image 2) */
.mm-symptom-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #E0F2FE;
    color: #0284C7;
    border: 1px solid #BAE6FD;
    border-radius: 9999px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    margin: 3px 6px 3px 0;
    text-transform: uppercase;
}
.mm-symptom-tag-x {
    color: #0284C7;
    font-size: 0.70rem;
    font-weight: 700;
    opacity: 0.8;
}

/* Navigation Buttons (Image 2 & 4) */
.st-key-p2_prev_btn button,
.st-key-p3_prev_btn button,
.st-key-p4_prev_btn button,
div[class*="st-key-p2_prev_btn"] button,
div[class*="st-key-p3_prev_btn"] button,
div[class*="st-key-p4_prev_btn"] button {
    background: #60A5FA !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 10px 18px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(96, 165, 250, 0.3) !important;
}
.st-key-p2_prev_btn button:hover,
.st-key-p3_prev_btn button:hover,
.st-key-p4_prev_btn button:hover,
div[class*="st-key-p2_prev_btn"] button:hover,
div[class*="st-key-p3_prev_btn"] button:hover,
div[class*="st-key-p4_prev_btn"] button:hover {
    background: #3B82F6 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

.st-key-btn_goto_step2 button,
.st-key-btn_goto_step3 button,
.st-key-btn_goto_step4 button,
.st-key-btn_run_triage button,
div[class*="st-key-btn_goto_step2"] button,
div[class*="st-key-btn_goto_step3"] button,
div[class*="st-key-btn_goto_step4"] button,
div[class*="st-key-btn_run_triage"] button {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 10px 22px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 3px 10px rgba(29, 78, 216, 0.35) !important;
}
.st-key-btn_goto_step2 button:hover,
.st-key-btn_goto_step3 button:hover,
.st-key-btn_goto_step4 button:hover,
.st-key-btn_run_triage button:hover,
div[class*="st-key-btn_goto_step2"] button:hover,
div[class*="st-key-btn_goto_step3"] button:hover,
div[class*="st-key-btn_goto_step4"] button:hover,
div[class*="st-key-btn_run_triage"] button:hover {
    background: #1E40AF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(30, 64, 175, 0.45) !important;
}

/* Dark Mode Overrides for Assessment Step Card */
[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-assessment_step_card),
[data-theme="dark"] .st-key-assessment_step_card {
    background: #0F172A !important;
    border-color: #1E293B !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
}
[data-theme="dark"] .mm-step-card-header {
    background: #162032 !important;
    border-bottom-color: #1E293B !important;
}
[data-theme="dark"] .mm-step-header-icon {
    background: rgba(37, 99, 235, 0.2) !important;
    border-color: rgba(37, 99, 235, 0.4) !important;
}
[data-theme="dark"] .mm-step-header-title {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-step-header-sub {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-step-info-pill {
    background: rgba(14, 165, 233, 0.15) !important;
    border-color: rgba(14, 165, 233, 0.35) !important;
    color: #7DD3FC !important;
}
[data-theme="dark"] .mm-field-label-wrap {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-field-icon-badge {
    background: #1E293B !important;
    border-color: #334155 !important;
}
[data-theme="dark"] .mm-step-progress-bar {
    background: #38BDF8 !important;
}
[data-theme="dark"] .mm-step-progress-step {
    color: #38BDF8 !important;
}
[data-theme="dark"] .mm-step-progress-sub {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-symptom-tag {
    background: rgba(14, 165, 233, 0.18) !important;
    color: #38BDF8 !important;
    border-color: rgba(14, 165, 233, 0.35) !important;
}
[data-theme="dark"] .mm-symptom-tag-x {
    color: #38BDF8 !important;
}
[data-theme="dark"] .st-key-p2_prev_btn button,
[data-theme="dark"] .st-key-p3_prev_btn button,
[data-theme="dark"] .st-key-p4_prev_btn button {
    background: #2563EB !important;
    color: #FFFFFF !important;
}
[data-theme="dark"] .st-key-btn_goto_step2 button,
[data-theme="dark"] .st-key-btn_goto_step3 button,
[data-theme="dark"] .st-key-btn_goto_step4 button,
[data-theme="dark"] .st-key-btn_run_triage button {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-assessment_step_card) > div[data-testid="stVerticalBlock"] > div:not(:first-child) {
        padding-left: 14px !important;
        padding-right: 14px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-assessment_step_card) > div[data-testid="stVerticalBlock"] > div:last-child {
        padding-bottom: 16px !important;
    }
    .mm-step-card-header {
        padding: 14px 16px;
    }
}

/* ==========================================================================
   MEDICAL REPORT - EQUAL SIZED CARDS (DOCUMENT UPLOAD & OCR TEXT STREAM)
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]),
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"] > div,
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"] > div,
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"] > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
}

/* ==========================================================================
   MEDICAL REPORT (P2) - EQUAL SIZED CARDS (UPLOAD & OCR TEXT STREAM)
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card),
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) [data-testid="stLayoutWrapper"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) [data-testid="stLayoutWrapper"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
}

div[class*="st-key-med_report_upload_card"],
div[class*="st-key-med_report_ocr_card"],
.st-key-med_report_upload_card,
.st-key-med_report_ocr_card,
.st-key-med_report_upload_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_ocr_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_upload_card div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-med_report_ocr_card div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-med_report_upload_card),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-med_report_ocr_card) {
    height: 100% !important;
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    box-sizing: border-box !important;
    border-radius: 14px !important;
}

div[class*="st-key-med_report_upload_card"] > div[data-testid="stVerticalBlock"],
div[class*="st-key-med_report_ocr_card"] > div[data-testid="stVerticalBlock"],
.st-key-med_report_upload_card > div[data-testid="stVerticalBlock"],
.st-key-med_report_ocr_card > div[data-testid="stVerticalBlock"],
.st-key-med_report_upload_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"],
.st-key-med_report_ocr_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

/* Ensure action button aligns at the bottom of upload card */
.st-key-med_report_upload_card .stButton {
    margin-top: auto !important;
    padding-top: 10px !important;
}

/* Ensure OCR textarea expands to fill exact available vertical space */
div[class*="st-key-med_report_ocr_card"] .stTextArea,
.st-key-med_report_ocr_card .stTextArea,
div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"],
.st-key-med_report_ocr_card [data-testid="stTextArea"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    margin-bottom: 0 !important;
}

div[class*="st-key-med_report_ocr_card"] .stTextArea > div,
.st-key-med_report_ocr_card .stTextArea > div,
div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"] > div,
.st-key-med_report_ocr_card [data-testid="stTextArea"] > div {
    flex: 1 1 auto !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}

div[class*="st-key-med_report_ocr_card"] .stTextArea textarea,
.st-key-med_report_ocr_card .stTextArea textarea,
div[class*="st-key-med_report_ocr_card"] textarea,
.st-key-med_report_ocr_card textarea {
    flex: 1 1 auto !important;
    height: 100% !important;
    min-height: 180px !important;
    box-sizing: border-box !important;
    resize: none !important;
}

/* ==========================================================================
   CUSTOMER SUPPORT & HELPDESK - EQUAL SIZED CARDS (FORM & INFO PANELS)
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]),
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
    height: 100% !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) [data-testid="stLayoutWrapper"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) [data-testid="stLayoutWrapper"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
}

/* Left card container stretches full height */
div[class*="st-key-about_supp_form_card"],
.st-key-about_supp_form_card,
.st-key-about_supp_form_card > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_form_card div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-about_supp_form_card"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_form_card) {
    height: 100% !important;
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    box-sizing: border-box !important;
    border-radius: 14px !important;
}

div[class*="st-key-about_supp_form_card"] > div[data-testid="stVerticalBlock"],
.st-key-about_supp_form_card > div[data-testid="stVerticalBlock"],
.st-key-about_supp_form_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
}

/* Ensure Send Support Ticket button aligns nicely to bottom */
.st-key-about_supp_form_card .stButton {
    margin-top: auto !important;
    padding-top: 10px !important;
}

/* Right column stretches cards to fill vertical space */
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    gap: 12px !important;
}

.st-key-about_supp_card_info,
.st-key-about_supp_card_report,
.st-key-about_supp_card_help,
div[class*="st-key-about_supp_card_info"],
div[class*="st-key-about_supp_card_report"],
div[class*="st-key-about_supp_card_help"],
.st-key-about_supp_card_info > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_card_report > div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-about_supp_card_help > div[data-testid="stVerticalBlockBorderWrapper"] {
    flex: 1 1 auto !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    border-radius: 12px !important;
}

/* ==========================================================================
   ESSENTIAL MEDICINE INVENTORY & STOCKOUT TRIAGE - UNIFIED CARD HEIGHTS
   ========================================================================== */
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-cc_inv_fac_card"]),
[data-testid="stHorizontalBlock"]:has(.st-key-cc_inv_fac_card) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-cc_inv_fac_card"]) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-cc_inv_fac_card"]) > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.st-key-cc_inv_fac_card) > div[data-testid="column"],
[data-testid="stHorizontalBlock"]:has(.st-key-cc_inv_fac_card) > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(div[class*="st-key-cc_inv_fac_card"]) > div[data-testid="column"] > div,
[data-testid="stHorizontalBlock"]:has(div[class*="st-key-cc_inv_fac_card"]) > div[data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.st-key-cc_inv_fac_card) > div[data-testid="column"] > div,
[data-testid="stHorizontalBlock"]:has(.st-key-cc_inv_fac_card) > div[data-testid="stColumn"] > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: stretch !important;
}

div[class*="st-key-cc_inv_fac_card"],
.st-key-cc_inv_fac_card,
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-cc_inv_fac_card"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-cc_inv_fac_card) {
    min-height: 96px !important;
    height: 96px !important;
    max-height: 96px !important;
    padding: 10px 14px !important;
    border-radius: 12px !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1px solid var(--mm-border, #E2E8F0) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
}

[data-theme="dark"] div[class*="st-key-cc_inv_fac_card"],
[data-theme="dark"] .st-key-cc_inv_fac_card,
[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-cc_inv_fac_card"]),
[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-cc_inv_fac_card) {
    background: #1E293B !important;
    border-color: #334155 !important;
}

div[class*="st-key-cc_inv_fac_card"] > div[data-testid="stVerticalBlock"],
.st-key-cc_inv_fac_card > div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-cc_inv_fac_card) > div[data-testid="stVerticalBlock"] {
    gap: 4px !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

div[class*="st-key-cc_inv_fac_card"] .stSelectbox,
.st-key-cc_inv_fac_card .stSelectbox,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-cc_inv_fac_card) .stSelectbox {
    margin: 0 !important;
    padding: 0 !important;
}

div[class*="st-key-cc_inv_fac_card"] [data-baseweb="select"],
.st-key-cc_inv_fac_card [data-baseweb="select"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-cc_inv_fac_card) [data-baseweb="select"] {
    min-height: 38px !important;
    height: 38px !important;
}

div[class*="st-key-cc_inv_fac_card"] [data-baseweb="select"] > div,
.st-key-cc_inv_fac_card [data-baseweb="select"] > div,
/* ==========================================================================
   DIAGNOSTIC EVALUATION & CLINICAL FINDINGS (RESULTS VIEW - IMAGE 3)
   ========================================================================== */
.mm-report-results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;
}
.mm-report-results-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
}
.mm-report-results-icon-box {
    width: 48px;
    height: 48px;
    min-width: 48px;
    border-radius: 14px;
    background: #EFF6FF;
    border: 1.5px solid #BFDBFE;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
}
[data-theme="dark"] .mm-report-results-icon-box {
    background: rgba(37, 99, 235, 0.15);
    border-color: rgba(37, 99, 235, 0.35);
}
.mm-report-results-star-accent {
    position: absolute;
    bottom: -3px;
    right: -3px;
    width: 17px;
    height: 17px;
    background: #FEF3C7;
    border: 1.5px solid #FCD34D;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
[data-theme="dark"] .mm-report-results-star-accent {
    background: #78350F;
    border-color: #D97706;
}
.mm-report-results-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--mm-text-primary);
    line-height: 1.25;
    margin: 0;
}
.mm-report-results-sub {
    font-size: 0.82rem;
    color: var(--mm-text-secondary);
    margin-top: 3px;
    font-weight: 500;
}
.mm-report-results-header-badge {
    background: rgba(16, 185, 129, 0.10);
    border: 1.2px solid rgba(16, 185, 129, 0.35);
    border-radius: 28px;
    padding: 6px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}
[data-theme="dark"] .mm-report-results-header-badge {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.40);
}
.mm-badge-circle-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #10B981;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mm-badge-circle-icon svg {
    stroke: #FFFFFF;
}
.mm-badge-title {
    font-size: 0.76rem;
    font-weight: 800;
    color: #059669;
    letter-spacing: 0.4px;
}
[data-theme="dark"] .mm-badge-title {
    color: #34D399;
}
.mm-badge-subtitle {
    font-size: 0.68rem;
    color: var(--mm-text-secondary);
    font-weight: 500;
}

/* 3 KPI Stat Cards */
.mm-diagnostic-kpi-card {
    background: var(--mm-card-bg, #FFFFFF);
    border: 1px solid var(--mm-border, #E2E8F0);
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 96px;
    height: 96px;
    box-sizing: border-box;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
[data-theme="dark"] .mm-diagnostic-kpi-card {
    background: #1E293B !important;
    border-color: #334155 !important;
}
.mm-diagnostic-kpi-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.mm-diagnostic-kpi-icon {
    width: 42px;
    height: 42px;
    min-width: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mm-diagnostic-kpi-label {
    font-size: 0.66rem;
    font-weight: 700;
    color: var(--mm-text-secondary);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.mm-diagnostic-kpi-val {
    font-size: 1.45rem;
    font-weight: 800;
    color: var(--mm-text-primary);
    line-height: 1.2;
    margin: 1px 0;
}
.mm-diagnostic-kpi-sub {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--mm-text-secondary);
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.mm-diagnostic-chart-graphic {
    opacity: 0.75;
    flex-shrink: 0;
}

/* AI Guide Banner */
.mm-ai-guide-banner {
    background: rgba(99, 102, 241, 0.04);
    border: 1.2px solid rgba(99, 102, 241, 0.22);
    border-left: 4px solid #6366F1;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 16px 0 14px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
[data-theme="dark"] .mm-ai-guide-banner {
    background: rgba(99, 102, 241, 0.10);
    border-color: rgba(99, 102, 241, 0.35);
}
.mm-ai-guide-banner-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.mm-ai-guide-icon-box {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-ai-guide-title {
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--mm-text-primary);
    line-height: 1.25;
}
.mm-ai-guide-sub {
    font-size: 0.78rem;
    color: var(--mm-text-secondary);
    margin-top: 2px;
}
.mm-ai-guide-badge {
    border: 1.5px solid #6366F1;
    color: #4F46E5;
    background: transparent;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    letter-spacing: 0.4px;
}
[data-theme="dark"] .mm-ai-guide-badge {
    color: #A5B4FC;
    border-color: #818CF8;
}

/* 5 Numbered Section Cards */
.mm-eval-section-card {
    background: var(--mm-card-bg, #FFFFFF);
    border: 1px solid var(--mm-border, #E2E8F0);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
[data-theme="dark"] .mm-eval-section-card {
    background: #1E293B !important;
    border-color: #334155 !important;
}
.mm-eval-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
}
.mm-eval-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}
.mm-eval-num-box {
    width: 30px;
    height: 30px;
    min-width: 30px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.92rem;
    font-weight: 800;
    color: #FFFFFF;
}
.mm-eval-icon-box {
    width: 32px;
    height: 32px;
    min-width: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mm-eval-section-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--mm-text-primary);
    margin: 0;
}
.mm-eval-tag-pill {
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.mm-tag-blue { background: rgba(37, 99, 235, 0.10); color: #2563EB; }
.mm-tag-green { background: rgba(16, 185, 129, 0.10); color: #059669; }
.mm-tag-purple { background: rgba(139, 92, 246, 0.10); color: #7C3AED; }
.mm-tag-orange { background: rgba(245, 158, 11, 0.12); color: #D97706; }
.mm-tag-red { background: rgba(239, 68, 68, 0.10); color: #DC2626; }

[data-theme="dark"] .mm-tag-blue { background: rgba(37, 99, 235, 0.20); color: #93C5FD; }
[data-theme="dark"] .mm-tag-green { background: rgba(16, 185, 129, 0.20); color: #6EE7B7; }
[data-theme="dark"] .mm-tag-purple { background: rgba(139, 92, 246, 0.20); color: #C4B5FD; }
[data-theme="dark"] .mm-tag-orange { background: rgba(245, 158, 11, 0.20); color: #FCD34D; }
[data-theme="dark"] .mm-tag-red { background: rgba(239, 68, 68, 0.20); color: #FCA5A5; }

.mm-eval-body-text {
    font-size: 0.88rem;
    line-height: 1.65;
    color: var(--mm-text-secondary);
}
.mm-eval-body-text strong {
    color: var(--mm-text-primary);
}

/* Sub-cards inside Section 4 & 5 */
.mm-subcard-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 12px;
}
@media (max-width: 768px) {
    .mm-subcard-grid {
        grid-template-columns: 1fr;
    }
}
.mm-subcard {
    border-radius: 12px;
    padding: 14px 16px;
    box-sizing: border-box;
}
.mm-subcard-consume {
    background: rgba(16, 185, 129, 0.04);
    border: 1.2px solid rgba(16, 185, 129, 0.25);
}
.mm-subcard-avoid {
    background: rgba(239, 68, 68, 0.04);
    border: 1.2px solid rgba(239, 68, 68, 0.25);
}
.mm-subcard-next {
    background: rgba(37, 99, 235, 0.04);
    border: 1.2px solid rgba(37, 99, 235, 0.25);
}
.mm-subcard-flags {
    background: rgba(239, 68, 68, 0.05);
    border: 1.2px solid rgba(239, 68, 68, 0.30);
}
[data-theme="dark"] .mm-subcard-consume {
    background: rgba(16, 185, 129, 0.10);
    border-color: rgba(16, 185, 129, 0.35);
}
[data-theme="dark"] .mm-subcard-avoid {
    background: rgba(239, 68, 68, 0.10);
    border-color: rgba(239, 68, 68, 0.35);
}
[data-theme="dark"] .mm-subcard-next {
    background: rgba(37, 99, 235, 0.10);
    border-color: rgba(37, 99, 235, 0.35);
}
[data-theme="dark"] .mm-subcard-flags {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.40);
}
.mm-subcard-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.88rem;
    font-weight: 800;
    margin-bottom: 8px;
}
.mm-subcard-title-green { color: #059669; }
.mm-subcard-title-red { color: #DC2626; }
.mm-subcard-title-blue { color: #2563EB; }
[data-theme="dark"] .mm-subcard-title-green { color: #34D399; }
[data-theme="dark"] .mm-subcard-title-red { color: #F87171; }
[data-theme="dark"] .mm-subcard-title-blue { color: #60A5FA; }

.mm-subcard-list {
    margin: 0;
    padding-left: 18px;
    font-size: 0.84rem;
    line-height: 1.6;
    color: var(--mm-text-secondary);
}
.mm-subcard-list li {
    margin-bottom: 4px;
}

/* Clinical Table */
.mm-eval-table-card {
    background: var(--mm-card-bg, #FFFFFF);
    border: 1px solid var(--mm-border, #E2E8F0);
    border-radius: 12px;
    overflow-x: auto;
    margin-top: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
[data-theme="dark"] .mm-eval-table-card {
    background: #1E293B !important;
    border-color: #334155 !important;
}
.mm-eval-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
}
.mm-eval-table th {
    background: rgba(241, 245, 249, 0.8);
    color: var(--mm-text-secondary);
    font-weight: 700;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 14px;
    border-bottom: 1.5px solid var(--mm-border, #E2E8F0);
    text-align: left;
}
[data-theme="dark"] .mm-eval-table th {
    background: rgba(15, 23, 42, 0.6);
    border-bottom-color: #334155;
}
.mm-eval-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--mm-border, #E2E8F0);
    color: var(--mm-text-secondary);
    vertical-align: middle;
}
[data-theme="dark"] .mm-eval-table td {
    border-bottom-color: #334155;
}
.mm-eval-table tr:last-child td {
    border-bottom: none;
}
.mm-table-status-pill {
    padding: 3px 8px;
    border-radius: 14px;
    font-size: 0.72rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    letter-spacing: 0.3px;
}
.mm-table-status-normal {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #059669;
}
.mm-table-status-abnormal {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #DC2626;
}
.mm-table-status-warning {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #D97706;
}
[data-theme="dark"] .mm-table-status-normal {
    color: #34D399;
}
[data-theme="dark"] .mm-table-status-abnormal {
    color: #F87171;
}
[data-theme="dark"] .mm-table-status-warning {
    color: #FCD34D;
}

/* Action Buttons Styling */
.st-key-btn_p2_deep_ai_action button,
.st-key-btn_p2_new_scan_action button,
.st-key-btn_p2_download_pdf button {
    height: 52px !important;
    min-height: 52px !important;
    max-height: 52px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-sizing: border-box !important;
    padding: 6px 14px !important;
    line-height: 1.25 !important;
    white-space: pre-line !important;
    text-align: center !important;
}

.st-key-btn_p2_deep_ai_action button {
    background: #2563EB !important;
    border: 1.5px solid #2563EB !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
}
.st-key-btn_p2_deep_ai_action button:hover {
    background: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
}

.st-key-btn_p2_new_scan_action button,
.st-key-btn_p2_download_pdf button {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid var(--mm-border, #E2E8F0) !important;
    color: var(--mm-text-primary) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
[data-theme="dark"] .st-key-btn_p2_new_scan_action button,
[data-theme="dark"] .st-key-btn_p2_download_pdf button {
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}
.st-key-btn_p2_new_scan_action button:hover,
.st-key-btn_p2_download_pdf button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    transform: translateY(-1px) !important;
}

/* ==========================================================================
   OFFICIAL TRANSFER RECOMMENDATION MANIFEST (TAB 5) - PIXEL ACCURATE STYLING
   ========================================================================== */
.mm-manifest-top-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 14px;
    margin-top: 10px;
}
.mm-manifest-top-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 280px;
}
.mm-manifest-top-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
    color: #2563EB;
}
[data-theme="dark"] .mm-manifest-top-icon {
    background: #1E293B;
    border-color: #3B82F6;
    color: #60A5FA;
}
.mm-manifest-top-title {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--mm-text-primary, #0F172A);
    letter-spacing: -0.02em;
}
.mm-manifest-top-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.80rem;
    color: var(--mm-text-secondary, #64748B);
    line-height: 1.3;
}
.mm-manifest-badges-group {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.mm-gov-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--mm-card-bg, #FFFFFF);
    border: 1px solid var(--mm-border, #E2E8F0);
    padding: 6px 12px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
[data-theme="dark"] .mm-gov-badge {
    background: #1E293B;
    border-color: #334155;
}
.mm-trust-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    padding: 6px 12px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(16,185,129,0.06);
}
[data-theme="dark"] .mm-trust-badge {
    background: rgba(16, 185, 129, 0.12);
    border-color: rgba(16, 185, 129, 0.3);
}

/* Notification Banner */
.mm-manifest-notify-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 16px;
}
[data-theme="dark"] .mm-manifest-notify-banner {
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.3);
}
.mm-manifest-notify-left {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.86rem;
    color: #15803D;
    flex-wrap: wrap;
}
[data-theme="dark"] .mm-manifest-notify-left {
    color: #4ADE80;
}
.mm-manifest-pill-id {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #2563EB;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
}
[data-theme="dark"] .mm-manifest-pill-id {
    background: rgba(37, 99, 235, 0.2);
    border-color: #3B82F6;
    color: #93C5FD;
}
.mm-manifest-notify-right {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.76rem;
    color: #166534;
    white-space: nowrap;
}
[data-theme="dark"] .mm-manifest-notify-right {
    color: #86EFAC;
}

/* Main Manifest Card Box */
.mm-manifest-card-box {
    background: var(--mm-card-bg, #FFFFFF);
    border: 1.5px solid #10B981;
    border-radius: 16px;
    padding: clamp(16px, 3.5vw, 24px);
    box-sizing: border-box;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.08);
    margin-bottom: 16px;
}
[data-theme="dark"] .mm-manifest-card-box {
    background: #1E293B;
    border-color: #10B981;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
}
.mm-manifest-header-inner {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--mm-border, #E2E8F0);
    margin-bottom: 16px;
}
[data-theme="dark"] .mm-manifest-header-inner {
    border-bottom-color: #334155;
}

/* 4 KPI Grid */
.mm-manifest-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 16px;
}
@media (max-width: 1024px) {
    .mm-manifest-kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 600px) {
    .mm-manifest-kpi-grid {
        grid-template-columns: 1fr;
    }
}
.mm-manifest-kpi-card {
    background: var(--mm-card-bg, #FFFFFF);
    border: 1px solid var(--mm-border, #E2E8F0);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
[data-theme="dark"] .mm-manifest-kpi-card {
    background: #0F172A;
    border-color: #334155;
}
.mm-manifest-kpi-icon {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-manifest-kpi-content {
    flex: 1;
    min-width: 0;
}
.mm-manifest-kpi-kicker {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--mm-text-secondary, #64748B);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.mm-manifest-kpi-val {
    font-size: 0.98rem;
    font-weight: 800;
    color: var(--mm-text-primary, #0F172A);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mm-manifest-kpi-sub {
    font-size: 0.74rem;
    color: var(--mm-text-secondary, #64748B);
    margin-top: 2px;
}

/* Middle Reallocation Flow Row */
.mm-manifest-flow-row {
    display: grid;
    grid-template-columns: 1fr 140px 1fr;
    gap: 14px;
    align-items: center;
    margin-bottom: 16px;
}
@media (max-width: 900px) {
    .mm-manifest-flow-row {
        grid-template-columns: 1fr;
        gap: 12px;
    }
}
.mm-manifest-facility-card {
    background: var(--mm-card-bg, #FFFFFF);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.mm-facility-source {
    border: 1.5px solid #BFDBFE;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.04) 0%, rgba(59, 130, 246, 0.01) 100%);
}
[data-theme="dark"] .mm-facility-source {
    border-color: rgba(59, 130, 246, 0.35);
    background: rgba(59, 130, 246, 0.08);
}
.mm-facility-dest {
    border: 1.5px solid #A7F3D0;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, rgba(16, 185, 129, 0.01) 100%);
}
[data-theme="dark"] .mm-facility-dest {
    border-color: rgba(16, 185, 129, 0.35);
    background: rgba(16, 185, 129, 0.08);
}
.mm-facility-icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
}
.mm-facility-arrow-badge {
    position: absolute;
    bottom: -4px;
    right: -4px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #FFFFFF;
}
[data-theme="dark"] .mm-facility-arrow-badge {
    border-color: #1E293B;
}
.mm-flow-middle {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    text-align: center;
}
.mm-flow-chevron-box {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3B82F6;
}
.mm-flow-pill {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1D4ED8;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 6px 10px;
    border-radius: 8px;
    text-align: center;
    line-height: 1.2;
}
[data-theme="dark"] .mm-flow-pill {
    background: rgba(37, 99, 235, 0.18);
    border-color: #3B82F6;
    color: #93C5FD;
}

/* Justification Box */
.mm-manifest-justification-box {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(0,0,0,0.02);
    border: 1px solid var(--mm-border, #E2E8F0);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 12px;
}
[data-theme="dark"] .mm-manifest-justification-box {
    background: rgba(255,255,255,0.03);
    border-color: #334155;
}

/* Operational Governance Box */
.mm-manifest-governance-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 6px;
}
[data-theme="dark"] .mm-manifest-governance-box {
    background: rgba(245, 158, 11, 0.08);
    border-color: rgba(245, 158, 11, 0.25);
}
.mm-gov-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 260px;
}
.mm-gov-right-signoff {
    display: flex;
    align-items: center;
    gap: 10px;
    border-left: 1px solid rgba(0,0,0,0.08);
    padding-left: 16px;
}
[data-theme="dark"] .mm-gov-right-signoff {
    border-left-color: rgba(255,255,255,0.12);
}

/* Bottom Action Buttons */
.mm-manifest-action-link {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 12px !important;
    padding: 12px 18px !important;
    border-radius: 10px !important;
    text-decoration: none !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-sizing: border-box !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 52px !important;
}
.mm-manifest-btn-outline {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid #3B82F6 !important;
    color: #1D4ED8 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
}
[data-theme="dark"] .mm-manifest-btn-outline {
    background: #1E293B !important;
    border-color: #3B82F6 !important;
    color: #60A5FA !important;
}
.mm-manifest-btn-outline:hover {
    background: #EFF6FF !important;
    border-color: #2563EB !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
}
[data-theme="dark"] .mm-manifest-btn-outline:hover {
    background: rgba(59, 130, 246, 0.15) !important;
    border-color: #60A5FA !important;
}

.st-key-btn_close_manifest button {
    background: #2563EB !important;
    border: 1.5px solid #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    min-height: 52px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.st-key-btn_close_manifest button:hover {
    background: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
}

/* ==========================================================================
   TAB 8: FEDERATED LEARNING ARCHITECTURE POLISH (Image 3 Design)
   ========================================================================== */
div:has(> button[aria-label*="Learn More"]),
div:has(> button[aria-label*="View Architecture"]) {
    width: 100% !important;
}
button[kind="secondary"][aria-label*="Learn More"],
button[kind="secondary"][aria-label*="View Architecture"] {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid var(--mm-border, #E2E8F0) !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    font-weight: 700 !important;
    color: var(--mm-text-primary, #0F172A) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
button[kind="secondary"][aria-label*="Learn More"]:hover,
button[kind="secondary"][aria-label*="View Architecture"]:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
}
[data-theme="dark"] button[kind="secondary"][aria-label*="Learn More"],
[data-theme="dark"] button[kind="secondary"][aria-label*="View Architecture"] {
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}

/* ==========================================================================
   HEALTH ASSESSMENT WIZARD (STEPS 1-4) CONTAINER & BUTTONS (IMAGE 2 & 4 DESIGN)
   ========================================================================== */
.st-key-assessment_step_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid #BFDBFE !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px -2px rgba(37, 99, 235, 0.08) !important;
    overflow: hidden !important;
}
[data-theme="dark"] .st-key-assessment_step_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1E293B !important;
    border-color: #334155 !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3) !important;
}

/* Previous Step Buttons (Soft Cornflower Blue) */
.st-key-p2_prev_btn button,
.st-key-p3_prev_btn button,
.st-key-p4_prev_btn button {
    background: #5B8EF7 !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 6px rgba(91, 142, 247, 0.25) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.st-key-p2_prev_btn button:hover,
.st-key-p3_prev_btn button:hover,
.st-key-p4_prev_btn button:hover {
    background: #4A7DF4 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(91, 142, 247, 0.35) !important;
}
.st-key-p2_prev_btn button p,
.st-key-p3_prev_btn button p,
.st-key-p4_prev_btn button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Next Step Buttons (Deep Royal Blue) */
.st-key-btn_goto_step2 button,
.st-key-btn_goto_step3 button,
.st-key-btn_goto_step4 button {
    background: #1D4ED8 !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 8px rgba(29, 78, 216, 0.25) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.st-key-btn_goto_step2 button:hover,
.st-key-btn_goto_step3 button:hover,
.st-key-btn_goto_step4 button:hover {
    background: #1E40AF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(29, 78, 216, 0.35) !important;
}
.st-key-btn_goto_step2 button p,
.st-key-btn_goto_step3 button p,
.st-key-btn_goto_step4 button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ==========================================================================
   SYMPTOMS SEARCH & CLINICAL EXTRACTOR CARD (IMAGE 2 DESIGN)
   ========================================================================== */
.st-key-symptoms_search_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid #BFDBFE !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px -2px rgba(37, 99, 235, 0.08) !important;
    overflow: hidden !important;
    margin-top: 24px !important;
}
[data-theme="dark"] .st-key-symptoms_search_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1E293B !important;
    border-color: #334155 !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3) !important;
}

/* Describe in Your Own Words Button (Outline Button) */
.st-key-btn_describe_words button {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.5px solid #3B82F6 !important;
    color: #1D4ED8 !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    height: 100% !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.st-key-btn_describe_words button:hover {
    background: #EFF6FF !important;
    border-color: #1D4ED8 !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15) !important;
}
.st-key-btn_describe_words button p {
    color: #1D4ED8 !important;
    font-weight: 700 !important;
}
[data-theme="dark"] .st-key-btn_describe_words button {
    background: #1E293B !important;
    border-color: #3B82F6 !important;
    color: #60A5FA !important;
}
[data-theme="dark"] .st-key-btn_describe_words button p {
    color: #60A5FA !important;
}
[data-theme="dark"] .st-key-btn_describe_words button:hover {
    background: rgba(59, 130, 246, 0.15) !important;
    border-color: #60A5FA !important;
}

/* Multilingual Extractor Form Button */
form[data-testid="stForm"] button[kind="primary"] {
    background: #1D4ED8 !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    border-radius: 10px !important;
    min-height: 46px !important;
    box-shadow: 0 2px 8px rgba(29, 78, 216, 0.25) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
form[data-testid="stForm"] button[kind="primary"]:hover {
    background: #1E40AF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(29, 78, 216, 0.35) !important;
}
form[data-testid="stForm"] button[kind="primary"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Audio Input Container (Speech to Text) */
div[data-testid="stAudioInput"] {
    background: var(--mm-card-bg, #FFFFFF) !important;
    border: 1.2px solid #BFDBFE !important;
    border-radius: 12px !important;
    padding: 6px 14px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
}
[data-theme="dark"] div[data-testid="stAudioInput"] {
    background: #1E293B !important;
    border-color: #334155 !important;
}

/* Common Symptoms Chips (Horizontal 7-Pill Layout) */
div[class*="st-key-pop_sym_chip_"] button {
    background: #2563EB !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.84rem !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    padding: 6px 12px !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.20) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
}
div[class*="st-key-pop_sym_chip_"] button:hover {
    background: #1D4ED8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
}
div[class*="st-key-pop_sym_chip_"] button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

@media (max-width: 768px) {
    .st-key-symptoms_search_card div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
    }
    div[class*="st-key-pop_sym_chip_"] button {
        font-size: 0.76rem !important;
        padding: 4px 8px !important;
        min-height: 38px !important;
    }
}
/* ============================================================
   CLINICAL AUTHENTICATION PORTAL -- DARK MODE OVERRIDE
   ============================================================ */
.st-key-auth_left_vault_card div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-auth_right_signin_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}
.st-key-auth_left_vault_card div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.85) 100%) !important;
}

.auth-input-label {
    color: #F8FAFC !important;
}

.st-key-panel_login_email input,
.st-key-panel_login_password input {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    color: #F8FAFC !important;
}
.st-key-panel_login_email input:focus,
.st-key-panel_login_password input:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

.st-key-auth_btn_forgot_pwd_link button,
.st-key-auth_btn_forgot_pwd_link button p {
    color: #60A5FA !important;
}

.st-key-panel_btn_goto_reg button,
.st-key-panel_btn_goto_rec button,
.st-key-panel_btn_goto_admin button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
}
.st-key-panel_btn_goto_reg button:hover,
.st-key-panel_btn_goto_rec button:hover,
.st-key-panel_btn_goto_admin button:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #60A5FA !important;
}
.st-key-panel_btn_goto_reg button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_goto_rec button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_goto_admin button div[data-testid="stMarkdownContainer"] p strong,
.st-key-panel_btn_return_dashboard button div[data-testid="stMarkdownContainer"] p strong {
    color: #93C5FD !important;
}
.st-key-panel_btn_goto_reg button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_goto_rec button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_goto_admin button div[data-testid="stMarkdownContainer"] p,
.st-key-panel_btn_return_dashboard button div[data-testid="stMarkdownContainer"] p {
    color: #94A3B8 !important;
}

.st-key-panel_btn_return_dashboard button {
    background: rgba(30, 41, 59, 0.45) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
}
.st-key-panel_btn_return_dashboard button:hover {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: #60A5FA !important;
}

.auth-or-divider::before,
.auth-or-divider::after {
    border-bottom-color: rgba(51, 65, 85, 0.8) !important;
}
.auth-or-divider {
    color: #64748B !important;
}

.auth-card-footer {
    border-top-color: rgba(51, 65, 85, 0.5) !important;
    color: #94A3B8 !important;
}

/* Feature and Trust cards in dark mode */
.auth-feat-item {
    background: rgba(30, 41, 59, 0.45) !important;
    border-color: rgba(51, 65, 85, 0.6) !important;
}
.auth-trust-item {
    background: rgba(30, 41, 59, 0.45) !important;
    border-color: rgba(51, 65, 85, 0.6) !important;
}
.auth-card-title {
    color: #F8FAFC !important;
}
.auth-card-subtitle {
    color: #94A3B8 !important;
}
.auth-alert-banner {
    background: rgba(239, 68, 68, 0.12) !important;
    border-color: rgba(239, 68, 68, 0.35) !important;
    border-left-color: #EF4444 !important;
    color: #FECACA !important;
}
/* Dark Mode Overrides for Admin & Recovery */
.st-key-panel_adm_email input,
.st-key-panel_adm_pass input,
.st-key-panel_rec_email input {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    color: #F8FAFC !important;
}
.st-key-panel_adm_email input:focus,
.st-key-panel_adm_pass input:focus,
.st-key-panel_rec_email input:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

.st-key-panel_btn_back_from_adm button,
.st-key-panel_btn_back_from_rec button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
}
.st-key-panel_btn_back_from_adm button:hover,
.st-key-panel_btn_back_from_rec button:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #60A5FA !important;
}
.st-key-panel_btn_back_from_adm button div[data-testid="stMarkdownContainer"] p strong {
    color: #93C5FD !important;
}
.st-key-panel_btn_back_from_adm button div[data-testid="stMarkdownContainer"] p {
    color: #94A3B8 !important;
}
.st-key-panel_btn_back_from_rec button p {
    color: #93C5FD !important;
}

.auth-admin-alert {
    background: rgba(239, 68, 68, 0.12) !important;
    border-color: rgba(239, 68, 68, 0.35) !important;
    border-left-color: #EF4444 !important;
}
.auth-info-callout {
    background: rgba(30, 58, 138, 0.25) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    color: #93C5FD !important;
}
.auth-privacy-banner {
    background: rgba(16, 185, 129, 0.12) !important;
    border-color: rgba(16, 185, 129, 0.3) !important;
}

/* Dark Mode overrides for Registration & Password Reset (Image 2 & 4) */
.auth-input-icon-box {
    background: rgba(30, 58, 138, 0.35) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
}
.auth-input-help {
    color: #94A3B8 !important;
}
.auth-pwd-req-box {
    background: rgba(30, 58, 138, 0.22) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
}
.auth-pwd-req-box div {
    color: #E2E8F0 !important;
}
.auth-pwd-req-box span {
    color: #CBD5E1 !important;
}
.auth-check-email-card {
    background: rgba(30, 58, 138, 0.25) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
}
.auth-check-email-card div {
    color: #E2E8F0 !important;
}
.auth-card-footer-trust {
    border-top-color: rgba(51, 65, 85, 0.5) !important;
    color: #94A3B8 !important;
}
.st-key-panel_reg_name input,
.st-key-panel_reg_email input,
.st-key-panel_reg_pass input,
.st-key-panel_reg_conf input,
.st-key-panel_rec_otp_input input,
.st-key-panel_rec_p1 input,
.st-key-panel_rec_p2 input {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    color: #F8FAFC !important;
}
.st-key-panel_reg_name input:focus,
.st-key-panel_reg_email input:focus,
.st-key-panel_reg_pass input:focus,
.st-key-panel_reg_conf input:focus,
.st-key-panel_rec_otp_input input:focus,
.st-key-panel_rec_p1 input:focus,
.st-key-panel_rec_p2 input:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}
.st-key-panel_btn_back_to_login button,
.st-key-panel_btn_reg_return_dash button,
.st-key-panel_btn_cancel_rec button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
    color: #60A5FA !important;
}
.st-key-panel_btn_back_to_login button:hover,
.st-key-panel_btn_reg_return_dash button:hover,
.st-key-panel_btn_cancel_rec button:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #93C5FD !important;
    color: #93C5FD !important;
}
.st-key-panel_btn_back_to_login button p,
.st-key-panel_btn_reg_return_dash button p,
.st-key-panel_btn_cancel_rec button p {
    color: #60A5FA !important;
}
.st-key-panel_btn_back_to_login button:hover p,
.st-key-panel_btn_reg_return_dash button:hover p,
.st-key-panel_btn_cancel_rec button:hover p {
    color: #93C5FD !important;
}

/* Dark Mode Overrides for Family Vault & Account Settings */
.patient-hero-card {
    background: linear-gradient(180deg, #0D1B36 0%, #081124 100%) !important;
    border-color: #1E3A8A !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}
.patient-hero-card h2 {
    color: #F8FAFC !important;
}
.family-member-card {
    background: rgba(30, 41, 59, 0.5) !important;
    border-color: rgba(51, 65, 85, 0.6) !important;
}
.family-member-card:hover {
    border-color: #38BDF8 !important;
}
.account-settings-card {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}
.account-field-icon-box {
    background: rgba(30, 58, 138, 0.35) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
}
.st-key-panel_prof_email input,
.st-key-panel_prof_name input,
.st-key-panel_prof_last_login input,
.st-key-panel_prof_member_since input {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(59, 130, 246, 0.25) !important;
    color: #F8FAFC !important;
}
.st-key-panel_prof_status input {
    background: rgba(22, 101, 52, 0.2) !important;
    color: #4ADE80 !important;
    border-color: rgba(34, 197, 94, 0.3) !important;
    font-weight: 700 !important;
}
.st-key-btn_prof_logout_main button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
    color: #60A5FA !important;
}
.st-key-btn_prof_logout_main button:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #93C5FD !important;
    color: #93C5FD !important;
}
.st-key-btn_prof_logout_main button p {
    color: #60A5FA !important;
}
.st-key-btn_prof_logout_main button:hover p {
    color: #93C5FD !important;
}
.form-subcard {
    background: rgba(30, 41, 59, 0.45) !important;
    border-color: rgba(51, 65, 85, 0.6) !important;
}
.st-key-btn_cancel_change_pwd button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(59, 130, 246, 0.45) !important;
    color: #60A5FA !important;
}
.st-key-btn_cancel_change_pwd button:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #93C5FD !important;
    color: #93C5FD !important;
}
.st-key-btn_cancel_change_pwd button p {
    color: #60A5FA !important;
}
.st-key-btn_cancel_change_pwd button:hover p {
    color: #93C5FD !important;
}

/* Administrator Session Card Dark Mode Override */
.adm-session-card {
    background: #0F172A !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
}
.adm-session-title {
    color: #F8FAFC !important;
}
.adm-session-title span {
    color: #60A5FA !important;
}
.adm-session-title-brand {
    color: #F8FAFC !important;
}
.adm-session-sec-brand {
    color: #F8FAFC !important;
}
.adm-session-lock-box {
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
}
.adm-session-notice {
    background: rgba(37, 99, 235, 0.12) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    color: #93C5FD !important;
}
.adm-session-notice span {
    color: #BFDBFE !important;
}
.adm-session-footer {
    border-top-color: rgba(51, 65, 85, 0.6) !important;
    color: #94A3B8 !important;
}
.adm-session-ftr-title {
    color: #F8FAFC !important;
}
.adm-session-ftr-sep {
    background: rgba(51, 65, 85, 0.6) !important;
}
.adm-session-ftr-cursive {
    color: #60A5FA !important;
}

/* Admin Portal Unified Dark Mode Overrides */
.adm-portal-card {
    background: #0F172A !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
}
.adm-portal-title {
    color: #F8FAFC !important;
}
.adm-portal-title span {
    color: #60A5FA !important;
}
.adm-portal-icon-box {
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
}
.adm-portal-subtitle {
    color: #94A3B8 !important;
}
.adm-portal-filter-lbl {
    color: #CBD5E1 !important;
}
.adm-portal-counter-bar {
    color: #94A3B8 !important;
}
.adm-user-row-card, .adm-scan-row-card, .adm-audit-row-card {
    background: rgba(15, 23, 42, 0.75) !important;
    border-color: rgba(51, 65, 85, 0.7) !important;
}
.adm-user-row-card:hover, .adm-scan-row-card:hover, .adm-audit-row-card:hover {
    border-color: rgba(96, 165, 250, 0.5) !important;
    background: rgba(30, 41, 59, 0.7) !important;
}
.adm-chip-meta {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(51, 65, 85, 0.8) !important;
    color: #94A3B8 !important;
}
.adm-scan-id-badge {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    color: #93C5FD !important;
}
.adm-user-details-box {
    background: rgba(15, 23, 42, 0.8) !important;
    border-color: rgba(51, 65, 85, 0.8) !important;
}
.adm-top-header-card {
    background: #0F172A !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
}
.adm-kpi-card {
    background: rgba(15, 23, 42, 0.75) !important;
    border-color: rgba(51, 65, 85, 0.7) !important;
}
.adm-kpi-card:hover {
    border-color: rgba(96, 165, 250, 0.5) !important;
    background: rgba(30, 41, 59, 0.7) !important;
}
.adm-activity-card {
    background: rgba(15, 23, 42, 0.65) !important;
    border-color: rgba(51, 65, 85, 0.6) !important;
}
.adm-activity-card:hover {
    border-color: rgba(96, 165, 250, 0.4) !important;
}
.st-key-btn_adm_view_all_logs button {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    color: #60A5FA !important;
}
.st-key-btn_adm_view_all_logs button:hover {
    background: rgba(37, 99, 235, 0.28) !important;
    border-color: #60A5FA !important;
    color: #93C5FD !important;
}
[data-theme="dark"] .adm-chip-item {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(51, 65, 85, 0.7) !important;
    color: #94A3B8 !important;
}
[data-theme="dark"] .adm-user-badge-id {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.35) !important;
    color: #60A5FA !important;
}
[data-theme="dark"] .adm-user-actions-wrap [data-testid="column"]:first-child button {
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    color: #60A5FA !important;
}
[data-theme="dark"] .adm-user-actions-wrap [data-testid="column"]:nth-child(2) button {
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(51, 65, 85, 0.8) !important;
    color: #CBD5E1 !important;
}
[data-theme="dark"] .adm-user-actions-wrap [data-testid="column"]:nth-child(3) button {
    background: rgba(225, 29, 72, 0.15) !important;
    border-color: rgba(244, 63, 94, 0.4) !important;
    color: #FB7185 !important;
}
</style>
"""


def apply_theme(dark_mode: bool = False):
    """
    Injects the DocMindX AI enterprise medical stylesheet into the Streamlit app.
    Dynamically applies dark mode or light mode styles.
    """
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    if dark_mode:
        st.markdown(DARK_CSS_OVERRIDE, unsafe_allow_html=True)