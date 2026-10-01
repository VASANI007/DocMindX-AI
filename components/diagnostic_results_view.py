"""
DocMindX AI - Diagnostic Evaluation & Clinical Findings Results Component
Renders the complete clinical evaluation results screen with 100% dynamic data,
zero emojis (pure vector SVGs), dark mode support, and responsive mobile flex layout.
Matches the clinical reference design with KPI cards, 5 numbered clinical guides,
side-by-side sub-cards, parameter breakdown table, and export buttons.
"""
import re
from datetime import datetime
import streamlit as st
from ai.utils.report_generator import generate_diagnostic_evaluation_pdf


def render_html(html_str: str):
    """Safely renders HTML via st.markdown by stripping leading whitespace from all lines.
    This strictly prevents CommonMark from accidentally parsing indented HTML tags as markdown code blocks.
    """
    if not isinstance(html_str, str):
        html_str = str(html_str)
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def format_bullets_to_html(raw_text: str, bullet_color: str = "#2563EB", is_dark: bool = False) -> str:
    """Converts raw bullet lines into clean structured HTML with custom SVG bullets and bold highlights."""
    if not raw_text:
        return ""
    lines = raw_text.strip().split("\n")
    items = []
    curr_item = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* ") or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in [".", ")"]):
            if curr_item:
                items.append(" ".join(curr_item))
                curr_item = []
            cleaned_line = re.sub(r'^(?:[-•*]|\d+[\.\)])\s*', '', stripped).strip()
            if cleaned_line:
                curr_item.append(cleaned_line)
        else:
            if curr_item:
                curr_item.append(stripped)
            else:
                items.append(stripped)
    if curr_item:
        items.append(" ".join(curr_item))

    # Filter out empty items
    items = [it.strip() for it in items if it and it.strip() and it.strip() not in ["-", "•", "*"]]

    text_c = "#CBD5E1" if is_dark else "#334155"
    bold_c = "#F8FAFC" if is_dark else "#0F172A"

    if not items:
        cleaned_raw = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', raw_text)
        return f"<p style='margin: 0; font-size: 0.86rem; line-height: 1.6; color: {text_c};'>{cleaned_raw}</p>"

    html_items = []
    for it in items:
        it_clean = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', it)
        if "<strong>" not in it_clean and ":" in it_clean:
            parts = it_clean.split(":", 1)
            it_clean = f'<strong style="color: {bold_c}; font-weight: 700;">{parts[0].strip()}:</strong> {parts[1].strip()}'

        dot = f'<span style="display: inline-block; width: 6px; height: 6px; min-width: 6px; border-radius: 50%; background: {bullet_color}; margin-top: 7px; flex-shrink: 0;"></span>'
        html_items.append(f'<div style="display: flex; align-items: flex-start; gap: 9px; margin-bottom: 8px; font-size: 0.86rem; line-height: 1.55; color: {text_c};">{dot}<div style="flex: 1;">{it_clean}</div></div>')

    return "".join(html_items)


def clean_body_html(text: str, is_dark: bool = False, dot_color: str = "#3B82F6") -> str:
    """Formats markdown paragraphs and bullet lines into clean HTML without breaking CommonMark."""
    if not text:
        return ""
    text_c = "#CBD5E1" if is_dark else "#334155"
    bold_c = "#F8FAFC" if is_dark else "#0F172A"

    lines = text.strip().split("\n")
    formatted_parts = []
    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            for b in bullet_items:
                b_clean = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', b)
                if "<strong>" not in b_clean and ":" in b_clean:
                    parts = b_clean.split(":", 1)
                    b_clean = f'<strong style="color: {bold_c}; font-weight: 700;">{parts[0].strip()}:</strong> {parts[1].strip()}'
                dot = f'<span style="display: inline-block; width: 6px; height: 6px; min-width: 6px; border-radius: 50%; background: {dot_color}; margin-top: 7px; flex-shrink: 0;"></span>'
                formatted_parts.append(f'<div style="display: flex; align-items: flex-start; gap: 9px; margin-bottom: 7px; font-size: 0.88rem; line-height: 1.55; color: {text_c};">{dot}<div style="flex: 1;">{b_clean}</div></div>')
            bullet_items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_bullets()
            continue
        if stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* ") or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in [".", ")"]):
            cleaned = re.sub(r'^(?:[-•*]|\d+[\.\)])\s*', '', stripped).strip()
            if cleaned:
                bullet_items.append(cleaned)
        else:
            flush_bullets()
            para = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', stripped)
            formatted_parts.append(f'<p style="margin: 0 0 10px 0; font-size: 0.88rem; line-height: 1.65; color: {text_c};">{para}</p>')

    flush_bullets()
    return "".join(formatted_parts)


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
    Provides harmonious dark/light mode rendering, crisp alignment, zero unrendered code blocks,
    and responsive mobile-desktop layout.
    """
    findings = findings or []
    breakdown_text = breakdown_text or ""
    is_dark = st.session_state.get("dark_mode", False)

    # Core Design Tokens
    card_bg = "#111827" if is_dark else "#FFFFFF"
    card_border = "rgba(59, 130, 246, 0.28)" if is_dark else "#E2E8F0"
    card_shadow = "0 4px 16px rgba(0, 0, 0, 0.35)" if is_dark else "0 2px 8px rgba(0, 0, 0, 0.04)"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#64748B"
    text_muted = "#64748B" if is_dark else "#94A3B8"

    # =========================================================================
    # 1. TOP REPORT HEADER CARD
    # =========================================================================
    badge_bg = "rgba(16, 185, 129, 0.16)" if is_dark else "rgba(16, 185, 129, 0.10)"
    badge_border = "rgba(16, 185, 129, 0.35)" if is_dark else "rgba(16, 185, 129, 0.30)"
    badge_title_c = "#34D399" if is_dark else "#059669"
    icon_box_bg = "rgba(37, 99, 235, 0.18)" if is_dark else "#EFF6FF"
    icon_box_border = "rgba(59, 130, 246, 0.35)" if is_dark else "#BFDBFE"

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 18px 22px; margin-bottom: 16px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="width: 46px; height: 46px; min-width: 46px; border-radius: 12px; background: {icon_box_bg}; border: 1.2px solid {icon_box_border}; display: flex; align-items: center; justify-content: center; position: relative; flex-shrink: 0;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                    <path d="M12 11h4"></path>
                    <path d="M12 16h4"></path>
                    <path d="M8 11h.01"></path>
                    <path d="M8 16h.01"></path>
                </svg>
            </div>
            <div>
                <h2 style="font-size: 1.28rem; font-weight: 800; color: {text_primary}; margin: 0; line-height: 1.25;">Diagnostic Evaluation & Clinical Findings</h2>
                <div style="font-size: 0.82rem; color: {text_secondary}; margin-top: 3px; font-weight: 500;">
                    {doc_name} • {doc_type_choice} • Age: {age_for_report} • Gender: {gender_for_report}
                </div>
            </div>
        </div>
        <div style="background: {badge_bg}; border: 1px solid {badge_border}; border-radius: 9999px; padding: 7px 16px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 22px; height: 22px; border-radius: 50%; background: #10B981; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div>
                <div style="font-size: 0.72rem; font-weight: 800; color: {badge_title_c}; letter-spacing: 0.5px;">AI ANALYSIS COMPLETE</div>
                <div style="font-size: 0.68rem; color: {text_secondary}; font-weight: 500;">Report analyzed successfully</div>
            </div>
        </div>
    </div>
    """)

    # =========================================================================
    # 2. THREE KPI STAT CARDS
    # =========================================================================
    c1_info = kpi_data.get("card1", {})
    c2_info = kpi_data.get("card2", {})
    c3_info = kpi_data.get("card3", {})

    k_col1, k_col2, k_col3 = st.columns(3)

    # KPI 1: Total Evaluated
    with k_col1:
        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 16px 18px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 98px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 12px; background: rgba(37, 99, 235, 0.14); border: 1px solid rgba(59, 130, 246, 0.3); display: flex; align-items: center; justify-content: center; color: #3B82F6; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 800; color: {text_secondary}; letter-spacing: 0.5px; text-transform: uppercase;">{c1_info.get('label', 'TOTAL PARAMETERS EVALUATED')}</div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: {text_primary}; line-height: 1.2; margin: 2px 0;">{c1_info.get('val', 0)}</div>
                    <div style="font-size: 0.70rem; font-weight: 600; color: #3B82F6; display: inline-flex; align-items: center; gap: 4px;">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        </svg>
                        <span>{c1_info.get('sub', 'From Lab Report')}</span>
                    </div>
                </div>
            </div>
            <div style="opacity: 0.85; flex-shrink: 0;">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="#3B82F6">
                    <rect x="3" y="10" width="4" height="14" rx="1.2"></rect>
                    <rect x="10" y="4" width="4" height="20" rx="1.2"></rect>
                    <rect x="17" y="14" width="4" height="10" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """)

    # KPI 2: Abnormal / Out-of-Range
    with k_col2:
        ab_val = c2_info.get('val', 0)
        is_alert = ab_val > 0
        pill_bg = "rgba(239, 68, 68, 0.18)" if is_alert else "rgba(16, 185, 129, 0.18)"
        pill_color = "#F87171" if (is_alert and is_dark) else ("#DC2626" if is_alert else ("#34D399" if is_dark else "#059669"))
        pill_border = "rgba(239, 68, 68, 0.35)" if is_alert else "rgba(16, 185, 129, 0.35)"
        icon_bg = "rgba(239, 68, 68, 0.14)" if is_alert else "rgba(245, 158, 11, 0.14)"
        icon_border = "rgba(239, 68, 68, 0.3)" if is_alert else "rgba(245, 158, 11, 0.3)"
        icon_color = "#EF4444" if is_alert else "#F59E0B"
        arrow_char = f"↑ {ab_val}" if is_alert else "↓ 0"

        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 16px 18px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 98px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 12px; background: {icon_bg}; border: 1px solid {icon_border}; display: flex; align-items: center; justify-content: center; color: {icon_color}; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 800; color: {text_secondary}; letter-spacing: 0.5px; text-transform: uppercase;">{c2_info.get('label', 'ABNORMAL / OUT-OF-RANGE')}</div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: {'#EF4444' if is_alert else text_primary}; line-height: 1.2; margin: 2px 0;">{ab_val}</div>
                    <div style="font-size: 0.70rem; font-weight: 700;">
                        <span style="background: {pill_bg}; color: {pill_color}; border: 1px solid {pill_border}; padding: 2px 8px; border-radius: 6px; display: inline-block;">
                            {arrow_char}
                        </span>
                    </div>
                </div>
            </div>
            <div style="opacity: 0.85; flex-shrink: 0;">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="{'#EF4444' if is_alert else '#3B82F6'}">
                    <rect x="3" y="14" width="4" height="10" rx="1.2"></rect>
                    <rect x="10" y="6" width="4" height="18" rx="1.2"></rect>
                    <rect x="17" y="10" width="4" height="14" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """)

    # KPI 3: Overall Status
    with k_col3:
        status_val = c3_info.get('val', 'All Normal')
        is_normal = status_val.lower() in ["all normal", "normal", "verified regimen", "low risk"]
        status_pill_bg = "rgba(16, 185, 129, 0.18)" if is_normal else "rgba(245, 158, 11, 0.18)"
        status_pill_color = "#34D399" if (is_normal and is_dark) else ("#059669" if is_normal else ("#FCD34D" if is_dark else "#D97706"))
        status_pill_border = "rgba(16, 185, 129, 0.35)" if is_normal else "rgba(245, 158, 11, 0.35)"
        status_sub_text = c3_info.get('sub', 'Within Reference Range' if is_normal else 'Review Recommended')
        kpi3_icon_bg = "rgba(16, 185, 129, 0.14)" if is_normal else "rgba(245, 158, 11, 0.14)"
        kpi3_icon_border = "rgba(16, 185, 129, 0.3)" if is_normal else "rgba(245, 158, 11, 0.3)"
        kpi3_icon_color = "#10B981" if is_normal else "#F59E0B"

        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 16px 18px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 98px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 12px; background: {kpi3_icon_bg}; border: 1px solid {kpi3_icon_border}; display: flex; align-items: center; justify-content: center; color: {kpi3_icon_color}; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 800; color: {text_secondary}; letter-spacing: 0.5px; text-transform: uppercase;">{c3_info.get('label', 'OVERALL CLINICAL STATUS')}</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: {text_primary}; line-height: 1.25; margin: 2px 0;">{status_val}</div>
                    <div style="font-size: 0.70rem; font-weight: 700;">
                        <span style="background: {status_pill_bg}; color: {status_pill_color}; border: 1px solid {status_pill_border}; padding: 2px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            {status_sub_text}
                        </span>
                    </div>
                </div>
            </div>
            <div style="opacity: 0.85; flex-shrink: 0;">
                <svg width="24" height="20" viewBox="0 0 24 24" fill="{'#10B981' if is_normal else '#F59E0B'}">
                    <rect x="3" y="12" width="4" height="12" rx="1.2"></rect>
                    <rect x="10" y="8" width="4" height="16" rx="1.2"></rect>
                    <rect x="17" y="4" width="4" height="20" rx="1.2"></rect>
                </svg>
            </div>
        </div>
        """)

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

    guide_banner_bg = "rgba(99, 102, 241, 0.12)" if is_dark else "rgba(99, 102, 241, 0.05)"
    guide_banner_border = "rgba(99, 102, 241, 0.35)" if is_dark else "rgba(99, 102, 241, 0.25)"

    render_html(f"""
    <div style="background: {guide_banner_bg}; border: 1px solid {guide_banner_border}; border-left: 4px solid #6366F1; border-radius: 12px; padding: 14px 18px; margin: 18px 0 16px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 38px; height: 38px; min-width: 38px; border-radius: 10px; background: rgba(99, 102, 241, 0.18); display: flex; align-items: center; justify-content: center; color: #818CF8; flex-shrink: 0;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16" rx="4"></rect>
                    <path d="M9 9h6"></path>
                    <path d="M9 13h6"></path>
                    <path d="M9 17h4"></path>
                </svg>
            </div>
            <div>
                <div style="font-size: 1.02rem; font-weight: 800; color: {text_primary}; line-height: 1.25;">{guide_title}</div>
                <div style="font-size: 0.78rem; color: {text_secondary}; margin-top: 2px;">{guide_sub}</div>
            </div>
        </div>
        <div style="border: 1.5px solid #818CF8; color: {'#A5B4FC' if is_dark else '#4F46E5'}; padding: 4px 12px; border-radius: 9999px; font-size: 0.74rem; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; letter-spacing: 0.4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"></path>
            </svg>
            <span>AI ANALYSIS</span>
        </div>
    </div>
    """)

    # =========================================================================
    # 4. FIVE NUMBERED CLINICAL GUIDE CARDS
    # =========================================================================
    sec_dict = parse_5_sections(breakdown_text)
    def_titles = {
        1: "Key Findings Overview",
        2: "Biological Function in Plain Language",
        3: "Impact on the Body & Symptoms",
        4: "Actionable Diet & Nutrition Plan",
        5: "Medical Precautions & Red Flags"
    }

    # CARD 1: Key Findings Overview
    s1 = sec_dict.get(1, {"title": def_titles[1], "body": breakdown_text[:350] if not sec_dict else ""})
    s1_title = s1.get("title") or def_titles[1]
    s1_body = s1.get("body") or ""
    s1_content_html = clean_body_html(s1_body, is_dark, "#3B82F6")

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; box-shadow: {card_shadow};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #2563EB; display: flex; align-items: center; justify-content: center; font-size: 0.88rem; font-weight: 800; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);">1</div>
                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 8px; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; color: #3B82F6; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <h3 style="font-size: 1.08rem; font-weight: 800; color: {text_primary}; margin: 0;">{s1_title}</h3>
            </div>
            <span style="background: {'rgba(37, 99, 235, 0.20)' if is_dark else 'rgba(37, 99, 235, 0.10)'}; color: {'#93C5FD' if is_dark else '#2563EB'}; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px;">SUMMARY</span>
        </div>
        <div>{s1_content_html}</div>
    </div>
    """)

    # CARD 2: Biological Function in Plain Language
    s2 = sec_dict.get(2, {"title": def_titles[2], "body": ""})
    s2_title = s2.get("title") or def_titles[2]
    s2_body = s2.get("body") or ""
    s2_content_html = clean_body_html(s2_body, is_dark, "#10B981")

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; box-shadow: {card_shadow};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #10B981; display: flex; align-items: center; justify-content: center; font-size: 0.88rem; font-weight: 800; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 6px rgba(16, 185, 129, 0.35);">2</div>
                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 8px; background: rgba(16, 185, 129, 0.12); display: flex; align-items: center; justify-content: center; color: #10B981; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.08rem; font-weight: 800; color: {text_primary}; margin: 0;">{s2_title}</h3>
            </div>
            <span style="background: {'rgba(16, 185, 129, 0.20)' if is_dark else 'rgba(16, 185, 129, 0.10)'}; color: {'#6EE7B7' if is_dark else '#059669'}; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px;">EXPLANATION</span>
        </div>
        <div>{s2_content_html}</div>
    </div>
    """)

    # CARD 3: Impact on the Body & Symptoms
    s3 = sec_dict.get(3, {"title": def_titles[3], "body": ""})
    s3_title = s3.get("title") or def_titles[3]
    s3_body = s3.get("body") or ""
    s3_content_html = clean_body_html(s3_body, is_dark, "#8B5CF6")

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; box-shadow: {card_shadow};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #8B5CF6; display: flex; align-items: center; justify-content: center; font-size: 0.88rem; font-weight: 800; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 6px rgba(139, 92, 246, 0.35);">3</div>
                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 8px; background: rgba(139, 92, 246, 0.12); display: flex; align-items: center; justify-content: center; color: #8B5CF6; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.08rem; font-weight: 800; color: {text_primary}; margin: 0;">{s3_title}</h3>
            </div>
            <span style="background: {'rgba(139, 92, 246, 0.20)' if is_dark else 'rgba(139, 92, 246, 0.10)'}; color: {'#C4B5FD' if is_dark else '#7C3AED'}; border: 1px solid rgba(139, 92, 246, 0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px;">PATIENT IMPACT</span>
        </div>
        <div>{s3_content_html}</div>
    </div>
    """)

    # CARD 4: Actionable Diet & Nutrition Plan
    s4 = sec_dict.get(4, {"title": def_titles[4], "body": ""})
    s4_title = s4.get("title") or def_titles[4]
    s4_raw = s4.get("body") or ""
    s4_intro, s4_consume, s4_avoid = parse_sub_cards(s4_raw, [
        r'(?:-\s*)?Foods to Consume\s*:?|क्या खाएं\s*:?',
        r'(?:-\s*)?Foods (?:and Habits )?to Avoid\s*:?|क्या न खाएं\s*:?'
    ])
    s4_intro_html = clean_body_html(s4_intro, is_dark, "#F97316")
    consume_bullets = format_bullets_to_html(s4_consume if s4_consume else s4_raw, "#10B981", is_dark)
    avoid_bullets = format_bullets_to_html(s4_avoid if s4_avoid else "Avoid heavily processed foods, high sodium, excess sugars, and eating immediately before bedtime.", "#EF4444", is_dark)

    sub4_consume_bg = "rgba(16, 185, 129, 0.08)" if is_dark else "#F0FDF4"
    sub4_consume_border = "rgba(16, 185, 129, 0.30)" if is_dark else "#BBF7D0"
    sub4_avoid_bg = "rgba(239, 68, 68, 0.08)" if is_dark else "#FEF2F2"
    sub4_avoid_border = "rgba(239, 68, 68, 0.30)" if is_dark else "#FECACA"

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; box-shadow: {card_shadow};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #F97316; display: flex; align-items: center; justify-content: center; font-size: 0.88rem; font-weight: 800; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 6px rgba(249, 115, 22, 0.35);">4</div>
                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 8px; background: rgba(249, 115, 22, 0.12); display: flex; align-items: center; justify-content: center; color: #F97316; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"></path>
                        <path d="M10 2c1 .5 2 2 2 5"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.08rem; font-weight: 800; color: {text_primary}; margin: 0;">{s4_title}</h3>
            </div>
            <span style="background: {'rgba(245, 158, 11, 0.20)' if is_dark else 'rgba(245, 158, 11, 0.12)'}; color: {'#FCD34D' if is_dark else '#D97706'}; border: 1px solid rgba(245, 158, 11, 0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px;">LIFESTYLE GUIDANCE</span>
        </div>
        <div>{s4_intro_html}</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 14px;">
            <div style="background: {sub4_consume_bg}; border: 1.2px solid {sub4_consume_border}; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: {'#34D399' if is_dark else '#059669'}; margin-bottom: 10px; display: flex; align-items: center; gap: 7px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span>Foods to Consume:</span>
                </div>
                {consume_bullets}
            </div>
            <div style="background: {sub4_avoid_bg}; border: 1.2px solid {sub4_avoid_border}; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: {'#F87171' if is_dark else '#DC2626'}; margin-bottom: 10px; display: flex; align-items: center; gap: 7px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
                    </svg>
                    <span>Foods and Habits to Avoid:</span>
                </div>
                {avoid_bullets}
            </div>
        </div>
    </div>
    """)

    # CARD 5: Medical Precautions & Red Flags
    s5 = sec_dict.get(5, {"title": def_titles[5], "body": ""})
    s5_title = s5.get("title") or def_titles[5]
    s5_raw = s5.get("body") or ""
    s5_intro, s5_steps, s5_flags = parse_sub_cards(s5_raw, [
        r'(?:-\s*)?Next Steps\s*:?|अगले कदम\s*:?|डॉक्टर से परामर्श\s*:?',
        r'(?:-\s*)?Red Flags[^\n:]*\s*:?|खतरे के लक्षण[^\n:]*\s*:?|सावधानियां[^\n:]*\s*:?'
    ])
    s5_intro_html = clean_body_html(s5_intro, is_dark, "#EF4444")
    steps_bullets = format_bullets_to_html(s5_steps if s5_steps else s5_raw, "#3B82F6", is_dark)
    flags_bullets = format_bullets_to_html(s5_flags if s5_flags else "Severe or sudden pain, persistent high fever with chills, acute breathlessness, or dizziness requires prompt physician review.", "#EF4444", is_dark)

    sub5_next_bg = "rgba(37, 99, 235, 0.08)" if is_dark else "#EFF6FF"
    sub5_next_border = "rgba(59, 130, 246, 0.30)" if is_dark else "#BFDBFE"
    sub5_flag_bg = "rgba(239, 68, 68, 0.08)" if is_dark else "#FEF2F2"
    sub5_flag_border = "rgba(239, 68, 68, 0.35)" if is_dark else "#FECACA"

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px 22px; margin-bottom: 18px; box-shadow: {card_shadow};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 28px; height: 28px; min-width: 28px; border-radius: 8px; background: #EF4444; display: flex; align-items: center; justify-content: center; font-size: 0.88rem; font-weight: 800; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 6px rgba(239, 68, 68, 0.35);">5</div>
                <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 8px; background: rgba(239, 68, 68, 0.12); display: flex; align-items: center; justify-content: center; color: #EF4444; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.08rem; font-weight: 800; color: {text_primary}; margin: 0;">{s5_title}</h3>
            </div>
            <span style="background: {'rgba(239, 68, 68, 0.20)' if is_dark else 'rgba(239, 68, 68, 0.10)'}; color: {'#FCA5A5' if is_dark else '#DC2626'}; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 10px; border-radius: 6px; font-size: 0.70rem; font-weight: 800; letter-spacing: 0.5px;">IMPORTANT</span>
        </div>
        <div>{s5_intro_html}</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 14px;">
            <div style="background: {sub5_next_bg}; border: 1.2px solid {sub5_next_border}; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: {'#60A5FA' if is_dark else '#2563EB'}; margin-bottom: 10px; display: flex; align-items: center; gap: 7px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path>
                        <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path>
                        <circle cx="20" cy="10" r="2"></circle>
                    </svg>
                    <span>Next Steps:</span>
                </div>
                {steps_bullets}
            </div>
            <div style="background: {sub5_flag_bg}; border: 1.2px solid {sub5_flag_border}; border-left: 4px solid #EF4444; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: {'#F87171' if is_dark else '#DC2626'}; margin-bottom: 10px; display: flex; align-items: center; gap: 7px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <span>Red Flags (Seek Immediate Medical Attention):</span>
                </div>
                {flags_bullets}
            </div>
        </div>
    </div>
    """)

    # =========================================================================
    # 5. DETAILED PARAMETER BREAKDOWN TABLE (IMAGE 4 FIX)
    # =========================================================================
    render_html(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin: 22px 0 10px 0;">
        <div style="color: #3B82F6; display: flex; align-items: center;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
        </div>
        <b style="font-size: 1.12rem; color: {text_primary}; font-weight: 800;">Detailed Parameter Breakdown</b>
    </div>
    """)

    th_bg = "rgba(30, 41, 59, 0.75)" if is_dark else "#F8FAFC"
    tr_border = "rgba(255, 255, 255, 0.07)" if is_dark else "#F1F5F9"
    td_val_c = text_primary

    table_rows_html = ""
    if report_category == "prescription":
        for m in findings:
            info = m.get("info", {})
            name = m.get("extracted_name", "Medication")
            dose = m.get("frequency", "As directed")
            timing = m.get("timing", "With water")
            gen = info.get("generic_name") or info.get("active_ingredient") or m.get("generic_name") or "Prescribed Entity"
            purp = info.get("purpose", "Prescribed for therapy")
            warn = info.get("warnings", "Take as directed.")
            table_rows_html += f"""<tr style="border-bottom: 1px solid {tr_border};">
<td style="padding: 12px 14px; color: {text_primary};"><strong>{name}</strong></td>
<td style="padding: 12px 14px; font-weight: 700; color: #3B82F6;">{dose}</td>
<td style="padding: 12px 14px; color: {text_secondary};">{timing}</td>
<td style="padding: 12px 14px;"><span style="background: rgba(16, 185, 129, 0.14); color: {'#34D399' if is_dark else '#059669'}; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; padding: 3px 9px; font-weight: 700; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 4px;">{gen}</span></td>
<td style="padding: 12px 14px; color: {text_secondary};">{purp}</td>
<td style="padding: 12px 14px; color: {text_secondary};">{warn}</td>
</tr>"""
        th_html = f"""<tr style="border-bottom: 1.5px solid {card_border};">
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Medication Name</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Dosage & Frequency</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Timing</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Generic Formulation</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Indication / Purpose</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Safety & Precautions</th>
</tr>"""
    elif report_category == "radiology":
        for item in findings:
            name = item.get("finding_name", item.get("english_name", "Observation"))
            modality = item.get("modality", "Radiology Imaging")
            sev = item.get("severity", "Normal")
            is_crit = sev in ["High", "Emergency"]
            pill_c = "#F87171" if (is_crit and is_dark) else ("#DC2626" if is_crit else ("#34D399" if is_dark else "#059669"))
            pill_bg_c = "rgba(239, 68, 68, 0.15)" if is_crit else "rgba(16, 185, 129, 0.15)"
            pill_bd_c = "rgba(239, 68, 68, 0.35)" if is_crit else "rgba(16, 185, 129, 0.35)"
            exp = item.get("explanation", "Standard anatomical finding.")
            rec = item.get("recommendation", "Clinical correlation recommended.")
            table_rows_html += f"""<tr style="border-bottom: 1px solid {tr_border};">
<td style="padding: 12px 14px; color: {text_primary};"><strong>{name}</strong></td>
<td style="padding: 12px 14px; color: {text_secondary};">{modality}</td>
<td style="padding: 12px 14px;"><span style="background: {pill_bg_c}; color: {pill_c}; border: 1px solid {pill_bd_c}; border-radius: 9999px; padding: 3px 9px; font-weight: 700; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 4px;">{sev.upper()}</span></td>
<td style="padding: 12px 14px; color: {text_secondary};">{exp}</td>
<td colspan="2" style="padding: 12px 14px; color: {text_secondary};">{rec}</td>
</tr>"""
        th_html = f"""<tr style="border-bottom: 1.5px solid {card_border};">
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Finding / Anatomy</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Modality</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Severity Status</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Clinical Explanation</th>
<th colspan="2" style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Clinical Advice / Recommendation</th>
</tr>"""
    else:
        # Standard Clinical Lab Report Table (Matching Screenshot)
        for item in findings:
            name = item.get("test_name", "Parameter")
            val = str(item.get("value", ""))
            unit = item.get("unit", "")
            val_display = f"{val} {unit}".strip()
            ref = item.get("reference_range", "Standard")
            status = item.get("status", "Normal")
            is_normal = status.lower() == "normal"
            val_c = "#34D399" if (is_normal and is_dark) else ("#059669" if is_normal else ("#F87171" if is_dark else "#EF4444"))
            pill_c = val_c
            pill_bg_c = "rgba(16, 185, 129, 0.15)" if is_normal else "rgba(239, 68, 68, 0.15)"
            pill_bd_c = "rgba(16, 185, 129, 0.35)" if is_normal else "rgba(239, 68, 68, 0.35)"
            icon_svg = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>' if is_normal else '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
            exp = item.get("explanation", "Within reference range")
            advice = item.get("action_advice", "Continue routine health monitoring.")

            table_rows_html += f"""<tr style="border-bottom: 1px solid {tr_border};">
<td style="padding: 12px 14px; color: {text_primary};"><strong>{name}</strong></td>
<td style="padding: 12px 14px;"><span style="font-weight: 700; color: {val_c};">{val_display}</span></td>
<td style="padding: 12px 14px; color: {text_secondary};">{ref}</td>
<td style="padding: 12px 14px;"><span style="background: {pill_bg_c}; color: {pill_c}; border: 1px solid {pill_bd_c}; border-radius: 9999px; padding: 3px 9px; font-weight: 700; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 4px;">{icon_svg} {status.upper()}</span></td>
<td style="padding: 12px 14px; color: {text_secondary};">{exp}</td>
<td style="padding: 12px 14px; color: {text_secondary};">{advice}</td>
</tr>"""
        th_html = f"""<tr style="border-bottom: 1.5px solid {card_border};">
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Parameter</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Your Value</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Reference Range</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Status</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Interpretation</th>
<th style="padding: 11px 14px; font-weight: 700; color: {text_secondary}; font-size: 0.72rem; text-transform: uppercase;">Clinical Advice</th>
</tr>"""

    render_html(f"""
    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; overflow: hidden; box-shadow: {card_shadow}; margin-top: 10px; margin-bottom: 20px;">
        <div style="overflow-x: auto; width: 100%;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; min-width: 650px;">
                <thead style="background: {th_bg};">
                    {th_html}
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """)

    # =========================================================================
    # 6. CLINICAL ADVISORY BANNER
    # =========================================================================
    advisory_bg = "rgba(234, 88, 12, 0.10)" if is_dark else "rgba(234, 88, 12, 0.06)"
    advisory_border = "rgba(234, 88, 12, 0.35)"

    render_html(f"""
    <div style="background: {advisory_bg}; border: 1.2px solid {advisory_border}; border-left: 4px solid #EA580C; border-radius: 10px; padding: 12px 16px; margin: 18px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <b style="color: #EA580C; font-size: 0.86rem; letter-spacing: 0.04em; text-transform: uppercase;">CLINICAL ADVISORY</b>
        </div>
        <p style="margin: 0; font-size: 0.82rem; color: {text_primary}; line-height: 1.5;">
            DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.
        </p>
    </div>
    """)

    # =========================================================================
    # 7. THREE ACTION BUTTONS ROW
    # =========================================================================
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
            "Deep Analyze with AI\nGet advanced health insights",
            icon=":material/psychology:",
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
            "New Scan / Upload Another Document\nAnalyze a different report",
            icon=":material/upload_file:",
            key="btn_p2_new_scan_action",
            use_container_width=True
        ):
            st.session_state["p2_step"] = 1
            st.session_state["p2_cached_doc_key"] = None
            st.session_state["p2_cached_doc_text"] = ""
            st.session_state["p2_deep_ai_chat"] = []
            st.session_state["p2_doc_text_stream"] = ""
            st.session_state["p2_doc_name"] = "Medical Document"
            st.session_state["p2_uploader_version"] = st.session_state.get("p2_uploader_version", 0) + 1
            st.session_state.pop("p2_doc_uploader", None)
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("p2_breakdown_") or k.startswith("p2_saved_")]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()

    with b_col3:
        st.download_button(
            label="Download Report (PDF)\nSave complete analysis",
            icon=":material/download:",
            data=pdf_buf.getvalue(),
            file_name=pdf_filename,
            mime="application/pdf",
            key="btn_p2_download_pdf",
            use_container_width=True
        )
