"""
DocMindX AI - Diagnostic Evaluation & Clinical Findings Results Component
Renders the complete clinical evaluation results screen with 100% dynamic data,
zero emojis (pure vector SVGs), dark mode support, and responsive mobile flex layout.
Matches the clinical reference design with KPI cards, 5 numbered clinical guides,
side-by-side sub-cards, parameter breakdown table, and export buttons.
"""
import re
import base64
from datetime import datetime
import streamlit as st
from ai.utils.report_generator import generate_diagnostic_evaluation_pdf


def format_bullets_to_html(raw_text: str) -> str:
    """Converts raw bullet lines into clean structured HTML."""
    if not raw_text:
        return ""
    lines = raw_text.strip().split("\n")
    items = []
    curr_item = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* "):
            if curr_item:
                items.append(" ".join(curr_item))
                curr_item = []
            curr_item.append(stripped.lstrip("-•* ").strip())
        elif stripped:
            if curr_item:
                curr_item.append(stripped)
            else:
                items.append(stripped)
    if curr_item:
        items.append(" ".join(curr_item))
    
    if not items:
        return f"<p style='margin: 0; font-size: 0.86rem; line-height: 1.6;'>{raw_text}</p>"
    
    html = "<ul class='mm-subcard-list'>"
    for it in items:
        m = re.match(r'^([^:]+:)(.*)$', it)
        if m:
            lead = m.group(1)
            rest = m.group(2)
            html += f"<li><strong>{lead}</strong>{rest}</li>"
        else:
            html += f"<li>{it}</li>"
    html += "</ul>"
    return html


def parse_sub_cards(text: str, split_patterns: list) -> tuple:
    """Splits a section into intro text and two sub-cards based on header patterns."""
    p1, p2 = split_patterns
    m1 = re.search(p1, text, re.IGNORECASE)
    m2 = re.search(p2, text, re.IGNORECASE)
    if m1 and m2:
        if m1.start() < m2.start():
            intro = text[:m1.start()].strip()
            box1_raw = text[m1.end():m2.start()].strip()
            box2_raw = text[m2.end():].strip()
        else:
            intro = text[:m2.start()].strip()
            box2_raw = text[m2.end():m1.start()].strip()
            box1_raw = text[m1.end():].strip()
        return intro, box1_raw, box2_raw
    return text, "", ""


def parse_5_sections(text: str) -> dict:
    """Parses raw AI markdown into a structured 5-section dictionary."""
    pattern = r'(?:^|\n)(?:###?\s*|\*\*)?(\d)[\.\)]\s*([^\n\r]+)'
    matches = list(re.finditer(pattern, text))
    sections = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip().rstrip('*#:')
        start_pos = m.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
        body = text[start_pos:end_pos].strip()
        sections[num] = {"title": title, "body": body}
    return sections


def render_diagnostic_evaluation_view(
    doc_name: str,
    doc_type_choice: str,
    age_for_report: str,
    gender_for_report: str,
    findings: list,
    breakdown_text: str,
    kpi_data: dict,
    report_category: str,
    T: dict,
    lang_code: str = "en"
):
    """
    Renders the complete clinical evaluation screen matching the user's reference mockup.
    """
    findings = findings or []
    breakdown_text = breakdown_text or ""

    # =========================================================================
    # 1. TOP REPORT HEADER
    # =========================================================================
    st.markdown(f"""
    <div class="mm-report-results-header">
        <div class="mm-report-results-header-left">
            <div class="mm-report-results-icon-box">
                <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                    <path d="M12 11h4"></path>
                    <path d="M12 16h4"></path>
                    <path d="M8 11h.01"></path>
                    <path d="M8 16h.01"></path>
                </svg>
                <div class="mm-report-results-star-accent">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="#F59E0B" stroke="#F59E0B" stroke-width="1">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                </div>
            </div>
            <div>
                <h2 class="mm-report-results-title">Diagnostic Evaluation & Clinical Findings</h2>
                <div class="mm-report-results-sub">
                    {doc_name} • {doc_type_choice} • Age: {age_for_report} • Gender: {gender_for_report}
                </div>
            </div>
        </div>
        <div class="mm-report-results-header-badge">
            <div class="mm-badge-circle-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div>
                <div class="mm-badge-title">AI ANALYSIS COMPLETE</div>
                <div class="mm-badge-subtitle">Report analyzed successfully</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 2. THREE KPI STAT CARDS
    # =========================================================================
    c1_info = kpi_data.get("card1", {})
    c2_info = kpi_data.get("card2", {})
    c3_info = kpi_data.get("card3", {})

    k_col1, k_col2, k_col3 = st.columns(3)

    # KPI 1: Total Evaluated
    with k_col1:
        st.markdown(f"""
        <div class="mm-diagnostic-kpi-card">
            <div class="mm-diagnostic-kpi-left">
                <div class="mm-diagnostic-kpi-icon" style="background: rgba(37, 99, 235, 0.10); color: #2563EB;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <div>
                    <div class="mm-diagnostic-kpi-label">{c1_info.get('label', 'TOTAL PARAMETERS EVALUATED')}</div>
                    <div class="mm-diagnostic-kpi-val">{c1_info.get('val', 0)}</div>
                    <div class="mm-diagnostic-kpi-sub">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        </svg>
                        <span>{c1_info.get('sub', 'From Lab Report')}</span>
                    </div>
                </div>
            </div>
            <div class="mm-diagnostic-chart-graphic">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="#3B82F6">
                    <rect x="3" y="10" width="4" height="14" rx="1.2"></rect>
                    <rect x="10" y="4" width="4" height="20" rx="1.2"></rect>
                    <rect x="17" y="14" width="4" height="10" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # KPI 2: Abnormal / Out-of-Range
    with k_col2:
        ab_val = c2_info.get('val', 0)
        is_alert = ab_val > 0
        pill_bg = "rgba(239, 68, 68, 0.12)" if is_alert else "rgba(16, 185, 129, 0.12)"
        pill_color = "#DC2626" if is_alert else "#059669"
        arrow_char = f"↑ {ab_val}" if is_alert else "↓ 0"

        st.markdown(f"""
        <div class="mm-diagnostic-kpi-card">
            <div class="mm-diagnostic-kpi-left">
                <div class="mm-diagnostic-kpi-icon" style="background: {'rgba(239, 68, 68, 0.10)' if is_alert else 'rgba(245, 158, 11, 0.10)'}; color: {'#EF4444' if is_alert else '#F59E0B'};">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div>
                    <div class="mm-diagnostic-kpi-label">{c2_info.get('label', 'ABNORMAL / OUT-OF-RANGE')}</div>
                    <div class="mm-diagnostic-kpi-val">{ab_val}</div>
                    <div class="mm-diagnostic-kpi-sub">
                        <span style="background: {pill_bg}; color: {pill_color}; font-size: 0.68rem; font-weight: 700; padding: 2px 7px; border-radius: 6px;">
                            {arrow_char}
                        </span>
                    </div>
                </div>
            </div>
            <div class="mm-diagnostic-chart-graphic">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="{'#F87171' if is_alert else '#60A5FA'}">
                    <rect x="3" y="14" width="4" height="10" rx="1.2"></rect>
                    <rect x="10" y="6" width="4" height="18" rx="1.2"></rect>
                    <rect x="17" y="10" width="4" height="14" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # KPI 3: Overall Status
    with k_col3:
        status_val = c3_info.get('val', 'All Normal')
        is_normal = status_val.lower() in ["all normal", "normal", "verified regimen", "low risk"]
        status_pill_bg = "rgba(16, 185, 129, 0.12)" if is_normal else "rgba(245, 158, 11, 0.12)"
        status_pill_color = "#059669" if is_normal else "#D97706"
        status_sub_text = c3_info.get('sub', 'Within Reference Range' if is_normal else 'Review Recommended')

        st.markdown(f"""
        <div class="mm-diagnostic-kpi-card">
            <div class="mm-diagnostic-kpi-left">
                <div class="mm-diagnostic-kpi-icon" style="background: {'rgba(16, 185, 129, 0.10)' if is_normal else 'rgba(245, 158, 11, 0.10)'}; color: {'#10B981' if is_normal else '#F59E0B'};">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <div>
                    <div class="mm-diagnostic-kpi-label">{c3_info.get('label', 'OVERALL CLINICAL STATUS')}</div>
                    <div class="mm-diagnostic-kpi-val" style="font-size: 1.25rem;">{status_val}</div>
                    <div class="mm-diagnostic-kpi-sub">
                        <span style="background: {status_pill_bg}; color: {status_pill_color}; font-size: 0.68rem; font-weight: 700; padding: 2px 7px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            {status_sub_text}
                        </span>
                    </div>
                </div>
            </div>
            <div class="mm-diagnostic-chart-graphic">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="{'#34D399' if is_normal else '#FBBF24'}">
                    <rect x="3" y="12" width="4" height="12" rx="1.2"></rect>
                    <rect x="10" y="8" width="4" height="16" rx="1.2"></rect>
                    <rect x="17" y="4" width="4" height="20" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 3. AI GUIDE BANNER
    # =========================================================================
    if report_category == "prescription":
        guide_title = "Comprehensive Clinical AI Prescription Guide & Medication Plan"
        guide_sub = "Automated Drug Purpose • Dosage Timing • Food Interactions • Safety Precautions"
    elif report_category == "radiology":
        guide_title = "Comprehensive Clinical AI Radiology Interpretation & Guide"
        guide_sub = "Plain-Language Scan Meaning • Anatomical Observations • Severity • Next Steps"
    else:
        guide_title = "Comprehensive Clinical AI Patient Guide & Recovery Plan"
        guide_sub = "Automated Plain-Language Interpretation • Organ Health • Dietary Recovery • Safety Precautions"

    st.markdown(f"""
    <div class="mm-ai-guide-banner">
        <div class="mm-ai-guide-banner-left">
            <div class="mm-ai-guide-icon-box">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16" rx="4"></rect>
                    <path d="M9 9h6"></path>
                    <path d="M9 13h6"></path>
                    <path d="M9 17h4"></path>
                </svg>
            </div>
            <div>
                <div class="mm-ai-guide-title">{guide_title}</div>
                <div class="mm-ai-guide-sub">{guide_sub}</div>
            </div>
        </div>
        <div class="mm-ai-guide-badge">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"></path>
            </svg>
            <span>AI ANALYSIS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 4. FIVE NUMBERED CLINICAL GUIDE CARDS
    # =========================================================================
    sec_dict = parse_5_sections(breakdown_text)

    # Default titles if not parsed
    def_titles = {
        1: "Key Findings Overview",
        2: "Biological Function in Plain Language",
        3: "Impact on the Body & Symptoms",
        4: "Actionable Diet & Nutrition Plan",
        5: "Medical Precautions & Red Flags"
    }

    # CARD 1: Key Findings Overview
    s1 = sec_dict.get(1, {"title": def_titles[1], "body": breakdown_text[:300] if not sec_dict else ""})
    s1_title = s1.get("title") or def_titles[1]
    s1_body = s1.get("body") or ""
    # Clean up formatting
    s1_html = s1_body.replace("\n", "<br/>")
    st.markdown(f"""
    <div class="mm-eval-section-card">
        <div class="mm-eval-section-header">
            <div class="mm-eval-header-left">
                <div class="mm-eval-num-box" style="background: #2563EB;">1</div>
                <div class="mm-eval-icon-box" style="background: rgba(37, 99, 235, 0.10); color: #2563EB;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <h3 class="mm-eval-section-title">{s1_title}</h3>
            </div>
            <span class="mm-eval-tag-pill mm-tag-blue">SUMMARY</span>
        </div>
        <div class="mm-eval-body-text">{s1_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # CARD 2: Biological Function in Plain Language
    s2 = sec_dict.get(2, {"title": def_titles[2], "body": ""})
    s2_title = s2.get("title") or def_titles[2]
    s2_body = s2.get("body") or ""
    s2_html = s2_body.replace("\n", "<br/>")
    st.markdown(f"""
    <div class="mm-eval-section-card">
        <div class="mm-eval-section-header">
            <div class="mm-eval-header-left">
                <div class="mm-eval-num-box" style="background: #10B981;">2</div>
                <div class="mm-eval-icon-box" style="background: rgba(16, 185, 129, 0.10); color: #10B981;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                </div>
                <h3 class="mm-eval-section-title">{s2_title}</h3>
            </div>
            <span class="mm-eval-tag-pill mm-tag-green">EXPLANATION</span>
        </div>
        <div class="mm-eval-body-text">{s2_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # CARD 3: Impact on the Body & Symptoms
    s3 = sec_dict.get(3, {"title": def_titles[3], "body": ""})
    s3_title = s3.get("title") or def_titles[3]
    s3_body = s3.get("body") or ""
    s3_html = s3_body.replace("\n", "<br/>")
    st.markdown(f"""
    <div class="mm-eval-section-card">
        <div class="mm-eval-section-header">
            <div class="mm-eval-header-left">
                <div class="mm-eval-num-box" style="background: #8B5CF6;">3</div>
                <div class="mm-eval-icon-box" style="background: rgba(139, 92, 246, 0.10); color: #8B5CF6;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <h3 class="mm-eval-section-title">{s3_title}</h3>
            </div>
            <span class="mm-eval-tag-pill mm-tag-purple">PATIENT IMPACT</span>
        </div>
        <div class="mm-eval-body-text">{s3_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # CARD 4: Actionable Diet & Nutrition Plan
    s4 = sec_dict.get(4, {"title": def_titles[4], "body": ""})
    s4_title = s4.get("title") or def_titles[4]
    s4_raw = s4.get("body") or ""
    s4_intro, s4_consume, s4_avoid = parse_sub_cards(s4_raw, [
        r'(?:-\s*)?Foods to Consume\s*:?|क्या खाएं\s*:?',
        r'(?:-\s*)?Foods (?:and Habits )?to Avoid\s*:?|क्या न खाएं\s*:?'
    ])

    st.markdown(f"""
    <div class="mm-eval-section-card">
        <div class="mm-eval-section-header">
            <div class="mm-eval-header-left">
                <div class="mm-eval-num-box" style="background: #F97316;">4</div>
                <div class="mm-eval-icon-box" style="background: rgba(245, 158, 11, 0.12); color: #F59E0B;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"></path>
                        <path d="M10 2c1 .5 2 2 2 5"></path>
                    </svg>
                </div>
                <h3 class="mm-eval-section-title">{s4_title}</h3>
            </div>
            <span class="mm-eval-tag-pill mm-tag-orange">LIFESTYLE GUIDANCE</span>
        </div>
        <div class="mm-eval-body-text">{s4_intro}</div>
        <div class="mm-subcard-grid">
            <div class="mm-subcard mm-subcard-consume">
                <div class="mm-subcard-title mm-subcard-title-green">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>Foods to Consume:</span>
                </div>
                {format_bullets_to_html(s4_consume if s4_consume else s4_raw)}
            </div>
            <div class="mm-subcard mm-subcard-avoid">
                <div class="mm-subcard-title mm-subcard-title-red">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
                    </svg>
                    <span>Foods and Habits to Avoid:</span>
                </div>
                {format_bullets_to_html(s4_avoid if s4_avoid else "Avoid heavily processed foods, high sodium, excess sugars, and eating immediately before bedtime.")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CARD 5: Medical Precautions & Red Flags
    s5 = sec_dict.get(5, {"title": def_titles[5], "body": ""})
    s5_title = s5.get("title") or def_titles[5]
    s5_raw = s5.get("body") or ""
    s5_intro, s5_steps, s5_flags = parse_sub_cards(s5_raw, [
        r'(?:-\s*)?Next Steps\s*:?|अगले कदम\s*:?|डॉक्टर से परामर्श\s*:?',
        r'(?:-\s*)?Red Flags[^\n:]*\s*:?|खतरे के लक्षण[^\n:]*\s*:?|सावधानियां[^\n:]*\s*:?'
    ])

    st.markdown(f"""
    <div class="mm-eval-section-card">
        <div class="mm-eval-section-header">
            <div class="mm-eval-header-left">
                <div class="mm-eval-num-box" style="background: #EF4444;">5</div>
                <div class="mm-eval-icon-box" style="background: rgba(239, 68, 68, 0.10); color: #EF4444;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                </div>
                <h3 class="mm-eval-section-title">{s5_title}</h3>
            </div>
            <span class="mm-eval-tag-pill mm-tag-red">IMPORTANT</span>
        </div>
        <div class="mm-eval-body-text">{s5_intro}</div>
        <div class="mm-subcard-grid">
            <div class="mm-subcard mm-subcard-next">
                <div class="mm-subcard-title mm-subcard-title-blue">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path>
                        <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path>
                        <circle cx="20" cy="10" r="2"></circle>
                    </svg>
                    <span>Next Steps:</span>
                </div>
                {format_bullets_to_html(s5_steps if s5_steps else s5_raw)}
            </div>
            <div class="mm-subcard mm-subcard-flags">
                <div class="mm-subcard-title mm-subcard-title-red">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <span>Red Flags (Seek Immediate Medical Attention):</span>
                </div>
                {format_bullets_to_html(s5_flags if s5_flags else "Severe or sudden pain, persistent high fever with chills, acute breathlessness, or dizziness requires prompt physician review.")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 5. DETAILED PARAMETER BREAKDOWN TABLE (IMAGE 3)
    # =========================================================================
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin: 24px 0 10px 0;">
        <div style="color: #2563EB; display: flex; align-items: center;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
        </div>
        <b style="font-size: 1.10rem; color: var(--mm-text-primary);">Detailed Parameter Breakdown</b>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic Table Rows depending on document type
    table_rows_html = ""

    if report_category == "prescription":
        # Prescription Table
        for m in findings:
            info = m.get("info", {})
            name = m.get("extracted_name", "Medication")
            dose = m.get("frequency", "As directed")
            timing = m.get("timing", "With water")
            gen = info.get("generic_name", "Standard Formulation")
            purp = info.get("purpose", "Prescribed for therapy")
            warn = info.get("warnings", "Take as directed.")
            table_rows_html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><span style="font-weight: 700; color: #2563EB;">{dose}</span></td>
                <td>{timing}</td>
                <td><span class="mm-table-status-pill mm-table-status-normal"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg> {gen}</span></td>
                <td>{purp}</td>
                <td>{warn}</td>
            </tr>
            """
        th_html = """
        <tr>
            <th>Medication Name</th>
            <th>Dosage & Frequency</th>
            <th>Timing</th>
            <th>Generic Formulation</th>
            <th>Indication / Purpose</th>
            <th>Safety & Precautions</th>
        </tr>
        """
    elif report_category == "radiology":
        # Radiology Findings Table
        for item in findings:
            name = item.get("finding_name", item.get("english_name", "Observation"))
            modality = item.get("modality", "Radiology Imaging")
            sev = item.get("severity", "Normal")
            is_crit = sev in ["High", "Emergency"]
            pill_class = "mm-table-status-abnormal" if is_crit else ("mm-table-status-warning" if sev == "Medium" else "mm-table-status-normal")
            exp = item.get("explanation", "Standard anatomical finding.")
            rec = item.get("recommendation", "Clinical correlation recommended.")
            table_rows_html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td>{modality}</td>
                <td><span class="mm-table-status-pill {pill_class}">{sev.upper()}</span></td>
                <td>{exp}</td>
                <td colspan="2">{rec}</td>
            </tr>
            """
        th_html = """
        <tr>
            <th>Finding / Anatomy</th>
            <th>Modality</th>
            <th>Severity Status</th>
            <th>Clinical Explanation</th>
            <th colspan="2">Clinical Advice / Recommendation</th>
        </tr>
        """
    else:
        # Standard Clinical Lab Report Table (Matching Image 3)
        for item in findings:
            name = item.get("test_name", "Parameter")
            val = str(item.get("value", ""))
            unit = item.get("unit", "")
            val_display = f"{val} {unit}".strip()
            ref = item.get("reference_range", "Standard")
            status = item.get("status", "Normal")
            is_normal = status.lower() == "normal"
            val_color = "#10B981" if is_normal else "#EF4444"
            pill_class = "mm-table-status-normal" if is_normal else "mm-table-status-abnormal"
            icon_svg = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>' if is_normal else '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
            exp = item.get("explanation", "Within reference range")
            advice = item.get("action_advice", "Continue routine health monitoring.")
            table_rows_html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><span style="font-weight: 700; color: {val_color};">{val_display}</span></td>
                <td>{ref}</td>
                <td><span class="mm-table-status-pill {pill_class}">{icon_svg} {status.upper()}</span></td>
                <td>{exp}</td>
                <td>{advice}</td>
            </tr>
            """
        th_html = """
        <tr>
            <th>Parameter</th>
            <th>Your Value</th>
            <th>Reference Range</th>
            <th>Status</th>
            <th>Interpretation</th>
            <th>Clinical Advice</th>
        </tr>
        """

    st.markdown(f"""
    <div class="mm-eval-table-card">
        <table class="mm-eval-table">
            <thead>
                {th_html}
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 6. CLINICAL ADVISORY BANNER
    # =========================================================================
    st.markdown("""
    <div class="mm-clinical-advisory-banner" style="background: rgba(234, 88, 12, 0.06); border: 1.2px solid rgba(234, 88, 12, 0.35); border-left: 4px solid #EA580C; border-radius: 10px; padding: 12px 16px; margin: 18px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <b style="color: #EA580C; font-size: 0.86rem; letter-spacing: 0.04em; text-transform: uppercase;">CLINICAL ADVISORY</b>
        </div>
        <p style="margin: 0; font-size: 0.82rem; color: var(--mm-text-primary); line-height: 1.5;">
            DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 7. THREE ACTION BUTTONS ROW (MATCHING IMAGE 3)
    # =========================================================================
    # Pre-generate PDF for download button
    pdf_buf = generate_diagnostic_evaluation_pdf(
        doc_name=doc_name,
        doc_type=doc_type_choice,
        age_group=age_for_report,
        gender=gender_for_report,
        findings=findings,
        breakdown_text=breakdown_text,
        total_eval=c1_info.get('val', len(findings)),
        abnormal_count=c2_info.get('val', 0),
        overall_status=c3_info.get('val', 'All Normal')
    )
    pdf_filename = f"DocMindX_Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    b_col1, b_col2, b_col3 = st.columns([1, 1, 1], gap="medium")

    with b_col1:
        if st.button(
            "✦ Deep Analyze with AI\nGet advanced health insights",
            key="btn_p2_deep_ai_action",
            type="primary",
            use_container_width=True
        ):
            from app import show_deep_ai_report_dialog
            show_deep_ai_report_dialog(
                report_text=st.session_state.get("p2_doc_text_stream", ""),
                report_type=doc_type_choice,
                lang_code=lang_code
            )

    with b_col2:
        if st.button(
            "☁ New Scan / Upload Another Document\nAnalyze a different report",
            key="btn_p2_new_scan_action",
            use_container_width=True
        ):
            st.session_state["p2_step"] = 1
            st.session_state["p2_cached_doc_key"] = None
            st.session_state["p2_cached_doc_text"] = ""
            st.session_state["p2_deep_ai_chat"] = []
            st.session_state["p2_doc_text_stream"] = ""
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("p2_breakdown_")]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()

    with b_col3:
        st.download_button(
            label="📄 Download Report (PDF)\nSave complete analysis",
            data=pdf_buf.getvalue(),
            file_name=pdf_filename,
            mime="application/pdf",
            key="btn_p2_download_pdf",
            use_container_width=True
        )
