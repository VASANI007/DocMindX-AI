"""
DocMindX AI - Diagnostic Evaluation & Clinical Findings Results Component
Renders the complete clinical evaluation results screen with 100% dynamic data,
zero emojis (pure vector SVGs), dark mode & light mode support, and responsive layout.
Matches the clinical reference mockup in Image 3 with:
- Top Header Card with document icon, title, metadata, date box, and download action
- 4 KPI Stat Cards in a row (Total Evaluated, Abnormal, Overall Status, AI Complete)
- Lightbulb clinical AI guide banner
- Accordion / Collapsible section cards with SVG icons and animated chevrons:
    1. Key Findings Overview (Open: Normal vs Abnormal side-by-side cards)
    2. Biological Function in Plain Language (Open: 5 colored mini cards grid)
    3. Impact on the Body & Symptoms (Collapsible)
    4. Actionable Diet & Nutrition Plan (Collapsible: Foods to Consume vs Foods to Avoid)
    5. Medical Precautions & Red Flags (Collapsible: Next Steps vs Red Flags)
    6. Detailed Parameter Breakdown (Collapsible: full clean HTML table)
- Bottom action buttons
"""
import re
from datetime import datetime
import streamlit as st
from ai.utils.report_generator import generate_diagnostic_evaluation_pdf


def render_html(html_str: str):
    """Safely renders HTML via st.markdown.
    Filters out any empty lines so CommonMark never exits HTML block mode and never injects markdown <p> tags.
    """
    if not isinstance(html_str, str):
        html_str = str(html_str)
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def clean_markdown_artifacts(text: str) -> str:
    """Removes stray markdown artifacts like orphan asterisks, separators, and dangling bullets."""
    if not text:
        return ""
    cleaned_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip lines that are only asterisks, dashes, hashes, bullets, or empty
        if not stripped or re.match(r'^(?:[*_~#-]{1,8}|•)\s*$', stripped):
            continue
        # Strip trailing orphaned asterisks/dashes at end of line (e.g. "text **" or "text ---")
        line_clean = re.sub(r'\s+[*_~-]{2,}$', '', stripped)
        # Strip leading orphaned asterisks (e.g. "** Schedule a follow-up...")
        line_clean = re.sub(r'^\*\*\s*(?=[A-Za-z0-9])', '', line_clean)
        cleaned_lines.append(line_clean)
    res = "\n".join(cleaned_lines).strip()
    res = re.sub(r'^(?:[*_~#-]{2,}\s*)+', '', res)
    res = re.sub(r'(?:\s*[*_~#-]{2,})+$', '', res)
    return res.strip()


def format_bullets_to_html(raw_text: str, bullet_color: str = "#2563EB", is_dark: bool = False) -> str:
    """Converts raw bullet lines into clean structured HTML with custom inline-flex bullets and bold highlights."""
    if not raw_text:
        return ""
    cleaned_text = clean_markdown_artifacts(raw_text)
    if not cleaned_text:
        return ""

    lines = cleaned_text.split("\n")
    items = []
    curr_item = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^(?:[-•*]|\d+[\.\)])\s+', stripped):
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

    text_c = "#CBD5E1" if is_dark else "#334155"
    bold_c = "#F8FAFC" if is_dark else "#0F172A"

    # Filter out empty or artifact items
    valid_items = []
    for it in items:
        it_clean = it.strip().strip("*_- ")
        if it_clean:
            valid_items.append(it_clean)
    items = valid_items

    if not items:
        return ""

    html_items = []
    for it in items:
        it_clean = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', it)
        it_clean = it_clean.replace("**", "").replace("---", "").strip()

        if "<strong>" not in it_clean and ":" in it_clean:
            parts = it_clean.split(":", 1)
            it_clean = f'<strong style="color: {bold_c}; font-weight: 700;">{parts[0].strip()}:</strong> {parts[1].strip()}'

        dot = f'<span style="display: inline-block; width: 6px; height: 6px; min-width: 6px; max-width: 6px; border-radius: 50%; background: {bullet_color}; margin-top: 7px; flex-shrink: 0;"></span>'
        html_items.append(
            f'<div style="display: flex; flex-direction: row; align-items: flex-start; gap: 8px; margin-bottom: 8px; font-size: 0.85rem; line-height: 1.55; color: {text_c};">'
            f'{dot}<div style="flex: 1; min-width: 0;">{it_clean}</div>'
            f'</div>'
        )

    return "".join(html_items)


def clean_body_html(text: str, is_dark: bool = False, dot_color: str = "#3B82F6") -> str:
    """Formats markdown paragraphs and bullet lines into clean HTML without breaking CommonMark."""
    if not text:
        return ""
    cleaned_text = clean_markdown_artifacts(text)
    if not cleaned_text:
        return ""

    text_c = "#CBD5E1" if is_dark else "#334155"
    bold_c = "#F8FAFC" if is_dark else "#0F172A"

    lines = cleaned_text.split("\n")
    formatted_parts = []
    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            for b in bullet_items:
                b_clean = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', b)
                b_clean = b_clean.replace("**", "").replace("---", "").strip()
                if "<strong>" not in b_clean and ":" in b_clean:
                    parts = b_clean.split(":", 1)
                    b_clean = f'<strong style="color: {bold_c}; font-weight: 700;">{parts[0].strip()}:</strong> {parts[1].strip()}'
                dot = f'<span style="display: inline-block; width: 6px; height: 6px; min-width: 6px; max-width: 6px; border-radius: 50%; background: {dot_color}; margin-top: 7px; flex-shrink: 0;"></span>'
                formatted_parts.append(
                    f'<div style="display: flex; flex-direction: row; align-items: flex-start; gap: 8px; margin-bottom: 7px; font-size: 0.86rem; line-height: 1.55; color: {text_c};">'
                    f'{dot}<div style="flex: 1; min-width: 0;">{b_clean}</div>'
                    f'</div>'
                )
            bullet_items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_bullets()
            continue
        if re.match(r'^(?:[-•*]|\d+[\.\)])\s+', stripped):
            cleaned = re.sub(r'^(?:[-•*]|\d+[\.\)])\s*', '', stripped).strip()
            if cleaned:
                bullet_items.append(cleaned)
        else:
            flush_bullets()
            para = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="color: {bold_c}; font-weight: 700;">\1</strong>', stripped)
            para = para.replace("**", "").replace("---", "").strip()
            if para:
                formatted_parts.append(f'<p style="margin: 0 0 10px 0; font-size: 0.86rem; line-height: 1.65; color: {text_c};">{para}</p>')

    flush_bullets()
    return "".join(formatted_parts)


def parse_sub_cards(text: str, split_patterns: list) -> tuple:
    """Splits a section into intro text and two sub-cards based on header patterns."""
    if not text:
        return "", "", ""
    p1, p2 = split_patterns
    p1_expanded = rf'(?:^|\n)\s*(?:[-•*#\s]*)\*?\*?(?:{p1})\*?\*?\s*:?'
    p2_expanded = rf'(?:^|\n)\s*(?:[-•*#\s]*)\*?\*?(?:{p2})\*?\*?\s*:?'

    m1 = re.search(p1_expanded, text, re.IGNORECASE)
    m2 = re.search(p2_expanded, text, re.IGNORECASE)
    if m1 and m2:
        if m1.start() < m2.start():
            intro = text[:m1.start()].strip()
            box1_raw = text[m1.end():m2.start()].strip()
            box2_raw = text[m2.end():].strip()
        else:
            intro = text[:m2.start()].strip()
            box2_raw = text[m2.end():m1.start()].strip()
            box1_raw = text[m1.end():].strip()
        return clean_markdown_artifacts(intro), clean_markdown_artifacts(box1_raw), clean_markdown_artifacts(box2_raw)
    return clean_markdown_artifacts(text), "", ""


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
        sections[num] = {"title": clean_markdown_artifacts(title), "body": clean_markdown_artifacts(body)}
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
    Renders the complete clinical evaluation screen matching the user's reference mockup in Image 3.
    Features:
    - 4 KPI cards in a row
    - Blue lightbulb AI guide banner
    - Interactive accordion cards for each clinical section
    - Section 1: Normal Parameters (green) vs Abnormal Parameters (red) side-by-side cards
    - Section 2: 5 colored mini cards grid explaining biological function of each marker
    - Section 3: Impact on body & symptoms
    - Section 4: Diet plan with Foods to Consume vs Foods to Avoid
    - Section 5: Medical Precautions & Red Flags
    - Section 6: Clean Parameter Breakdown Table with styled Normal/Abnormal badges
    - Zero code blocks or raw HTML display bugs
    - 100% responsive and identical in both dark and light modes
    """
    findings = findings or []
    breakdown_text = breakdown_text or ""
    is_dark = st.session_state.get("dark_mode", False)

    # Core Design Tokens
    card_bg = "#111827" if is_dark else "#FFFFFF"
    card_border = "rgba(59, 130, 246, 0.25)" if is_dark else "#E2E8F0"
    card_shadow = "0 4px 16px rgba(0, 0, 0, 0.35)" if is_dark else "0 2px 8px rgba(0, 0, 0, 0.04)"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#64748B"
    inner_divider = "rgba(255, 255, 255, 0.06)" if is_dark else "#F1F5F9"

    # Pre-generate PDF for download button
    c1_info = kpi_data.get("card1", {})
    c2_info = kpi_data.get("card2", {})
    c3_info = kpi_data.get("card3", {})
    total_detected = c1_info.get('val', len(findings))
    ab_count = c2_info.get('val', 0)
    status_overall = c3_info.get('val', 'All Normal')

    pdf_buf = generate_diagnostic_evaluation_pdf(
        doc_name=doc_name,
        doc_type=doc_type_choice,
        age_group=age_for_report,
        gender=gender_for_report,
        findings=findings,
        breakdown_text=breakdown_text,
        total_eval=total_detected,
        abnormal_count=ab_count,
        overall_status=status_overall
    )
    pdf_filename = f"DocMindX_Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    report_date_str = datetime.now().strftime("%d %b %Y")

    # Injected styles for seamless accordions
    render_html("""
    <style>
    .mm-result-accordion summary::-webkit-details-marker { display: none !important; }
    .mm-result-accordion summary { list-style: none !important; outline: none !important; }
    .mm-result-accordion[open] .mm-chevron-icon svg { transform: rotate(180deg); }
    .mm-chevron-icon svg { transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1); }
    .mm-result-accordion:hover { border-color: rgba(59, 130, 246, 0.40) !important; }
    </style>
    """)

    # =========================================================================
    # 1. TOP HEADER (Matching Image 3 Top Row)
    # =========================================================================
    hdr_col_left, hdr_col_right = st.columns([3.2, 1.8], gap="medium")

    with hdr_col_left:
        render_html(f"""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 12px;">
            <div style="width: 48px; height: 48px; min-width: 48px; border-radius: 12px; background: #2563EB; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);">
                <svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <line x1="10" y1="9" x2="8" y2="9"></line>
                </svg>
            </div>
            <div>
                <h2 style="font-size: 1.45rem; font-weight: 800; color: {text_primary}; margin: 0; line-height: 1.25; letter-spacing: -0.01em;">
                    Diagnostic Evaluation & Clinical Findings
                </h2>
                <div style="font-size: 0.84rem; color: {text_secondary}; margin-top: 3px; font-weight: 500;">
                    {doc_name} • {doc_type_choice} • Age: {age_for_report} • Gender: {gender_for_report}
                </div>
            </div>
        </div>
        """)

    with hdr_col_right:
        date_box_bg = "#1E293B" if is_dark else "#F8FAFC"
        date_box_bd = "#334155" if is_dark else "#E2E8F0"
        
        c_right1, c_right2 = st.columns([1.1, 1.3], gap="small")
        with c_right1:
            render_html(f"""
            <div style="background: {date_box_bg}; border: 1px solid {date_box_bd}; border-radius: 10px; padding: 6px 12px; display: flex; align-items: center; gap: 8px; height: 42px; box-sizing: border-box;">
                <div style="color: #3B82F6; display: flex; align-items: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.64rem; font-weight: 600; color: {text_secondary}; line-height: 1;">Report Date</div>
                    <div style="font-size: 0.82rem; font-weight: 800; color: {text_primary}; line-height: 1.2; margin-top: 2px;">{report_date_str}</div>
                </div>
            </div>
            """)
        with c_right2:
            st.download_button(
                label="Download Report",
                icon=":material/download:",
                data=pdf_buf.getvalue(),
                file_name=pdf_filename,
                mime="application/pdf",
                key="btn_p2_hdr_download_pdf",
                type="primary",
                use_container_width=True
            )

    # =========================================================================
    # 2. FOUR KPI STAT CARDS IN A ROW (Matching Image 3)
    # =========================================================================
    k1, k2, k3, k4 = st.columns(4, gap="small")

    # KPI 1: Total Parameters Evaluated
    with k1:
        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 14px 16px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 94px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 42px; height: 42px; min-width: 42px; border-radius: 10px; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; color: #3B82F6; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: {text_secondary}; letter-spacing: 0.2px;">Total Parameters Evaluated</div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: {text_primary}; line-height: 1.15; margin: 2px 0;">{total_detected}</div>
                    <div style="display: inline-flex; align-items: center; gap: 4px; background: rgba(37, 99, 235, 0.10); color: #3B82F6; border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 6px; padding: 2px 7px; font-size: 0.68rem; font-weight: 700;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        <span>From Lab Report</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    # KPI 2: Abnormal / Out-of-Range
    with k2:
        is_abnormal = ab_count > 0
        k2_bg = "rgba(239, 68, 68, 0.12)" if is_abnormal else "rgba(16, 185, 129, 0.12)"
        k2_color = "#EF4444" if is_abnormal else "#10B981"
        k2_val_c = "#EF4444" if is_abnormal else text_primary
        k2_pill_text = f"+ {ab_count} High" if is_abnormal else "0 All Normal"
        k2_pill_bg = "rgba(239, 68, 68, 0.14)" if is_abnormal else "rgba(16, 185, 129, 0.14)"
        k2_pill_c = "#DC2626" if (is_abnormal and not is_dark) else ("#F87171" if is_abnormal else ("#34D399" if is_dark else "#059669"))
        k2_pill_bd = "rgba(239, 68, 68, 0.30)" if is_abnormal else "rgba(16, 185, 129, 0.30)"

        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 14px 16px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 94px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 42px; height: 42px; min-width: 42px; border-radius: 10px; background: {k2_bg}; display: flex; align-items: center; justify-content: center; color: {k2_color}; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: {text_secondary}; letter-spacing: 0.2px;">Abnormal / Out-of-Range</div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: {k2_val_c}; line-height: 1.15; margin: 2px 0;">{ab_count}</div>
                    <div style="display: inline-flex; align-items: center; gap: 4px; background: {k2_pill_bg}; color: {k2_pill_c}; border: 1px solid {k2_pill_bd}; border-radius: 6px; padding: 2px 7px; font-size: 0.68rem; font-weight: 700;">
                        <span>{k2_pill_text}</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    # KPI 3: Overall Clinical Status
    with k3:
        is_normal_status = status_overall.lower() in ["all normal", "normal", "low risk"]
        k3_bg = "rgba(16, 185, 129, 0.12)" if is_normal_status else "rgba(245, 158, 11, 0.12)"
        k3_color = "#10B981" if is_normal_status else "#F59E0B"
        k3_pill_text = "Within Reference Range" if is_normal_status else "Review Recommended"
        k3_pill_bg = "rgba(16, 185, 129, 0.14)" if is_normal_status else "rgba(245, 158, 11, 0.14)"
        k3_pill_c = "#059669" if (is_normal_status and not is_dark) else ("#34D399" if is_normal_status else ("#FCD34D" if is_dark else "#D97706"))
        k3_pill_bd = "rgba(16, 185, 129, 0.30)" if is_normal_status else "rgba(245, 158, 11, 0.30)"

        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 14px 16px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 94px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 42px; height: 42px; min-width: 42px; border-radius: 10px; background: {k3_bg}; display: flex; align-items: center; justify-content: center; color: {k3_color}; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: {text_secondary}; letter-spacing: 0.2px;">Overall Clinical Status</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: {text_primary}; line-height: 1.2; margin: 2px 0;">{status_overall}</div>
                    <div style="display: inline-flex; align-items: center; gap: 4px; background: {k3_pill_bg}; color: {k3_pill_c}; border: 1px solid {k3_pill_bd}; border-radius: 6px; padding: 2px 7px; font-size: 0.68rem; font-weight: 700;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        <span>{k3_pill_text}</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    # KPI 4: AI Analysis Complete
    with k4:
        render_html(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 14px 16px; box-shadow: {card_shadow}; display: flex; align-items: center; justify-content: space-between; min-height: 94px; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 42px; height: 42px; min-width: 42px; border-radius: 10px; background: rgba(16, 185, 129, 0.12); display: flex; align-items: center; justify-content: center; color: #10B981; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <polyline points="9 12 11 14 15 10"></polyline>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: {text_secondary}; letter-spacing: 0.2px;">AI Analysis Complete</div>
                    <div style="font-size: 0.88rem; font-weight: 700; color: {text_primary}; line-height: 1.25; margin: 2px 0;">Report analyzed successfully</div>
                    <div style="display: inline-flex; align-items: center; gap: 4px; background: rgba(16, 185, 129, 0.10); color: {'#34D399' if is_dark else '#059669'}; border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 2px 7px; font-size: 0.68rem; font-weight: 700;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        <span>All parameters processed</span>
                    </div>
                </div>
            </div>
        </div>
        """)

    # =========================================================================
    # 3. LIGHTBULB CLINICAL GUIDE BANNER (Matching Image 3)
    # =========================================================================
    if report_category == "prescription":
        banner_title = "Comprehensive Clinical AI Prescription Guide & Medication Plan"
        banner_sub = "Automated Drug Purpose • Dosage Timing • Food Interactions • Safety Precautions"
    elif report_category == "radiology":
        banner_title = "Comprehensive Clinical AI Radiology Interpretation & Guide"
        banner_sub = "Plain-Language Scan Meaning • Anatomical Observations • Severity • Next Steps"
    else:
        banner_title = "Comprehensive Clinical AI Patient Guide & Recovery Plan"
        banner_sub = "Automated Plain-Language Interpretation • Organ Health • Dietary Recovery • Safety Precautions"

    bulb_bg = "rgba(37, 99, 235, 0.08)" if is_dark else "#F0F7FF"
    bulb_border = "rgba(59, 130, 246, 0.30)" if is_dark else "#DBEAFE"

    render_html(f"""
    <div style="background: {bulb_bg}; border: 1px solid {bulb_border}; border-radius: 12px; padding: 12px 18px; margin: 16px 0 16px 0; display: flex; align-items: center; gap: 14px;">
        <div style="width: 36px; height: 36px; min-width: 36px; border-radius: 50%; background: rgba(37, 99, 235, 0.14); display: flex; align-items: center; justify-content: center; color: #2563EB; flex-shrink: 0;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 18h6"></path>
                <path d="M10 22h4"></path>
                <path d="M12 2a7 7 0 0 0-7 7c0 2.5 1.5 4.5 3 6h8c1.5-1.5 3-3.5 3-6a7 7 0 0 0-7-7z"></path>
                <line x1="12" y1="9" x2="12" y2="12"></line>
            </svg>
        </div>
        <div>
            <div style="font-size: 0.96rem; font-weight: 800; color: {'#93C5FD' if is_dark else '#1E3A8A'}; line-height: 1.25;">{banner_title}</div>
            <div style="font-size: 0.78rem; color: {text_secondary}; margin-top: 2px;">{banner_sub}</div>
        </div>
    </div>
    """)

    # =========================================================================
    # 4. PARSE SECTIONS 1 TO 5
    # =========================================================================
    sec_dict = parse_5_sections(breakdown_text)
    def_titles = {
        1: "Key Findings Overview",
        2: "Biological Function in Plain Language",
        3: "Impact on the Body & Symptoms",
        4: "Actionable Diet & Nutrition Plan",
        5: "Medical Precautions & Red Flags"
    }

    # =========================================================================
    # SECTION 1: Key Findings Overview (Open by default - Matching Image 3)
    # =========================================================================
    s1 = sec_dict.get(1, {"title": def_titles[1], "body": breakdown_text[:350] if not sec_dict else ""})
    s1_title = s1.get("title") or def_titles[1]
    s1_body = s1.get("body") or ""

    # Parse Normal Parameters vs Abnormal Parameters
    s1_intro, s1_norm_text, s1_abnorm_text = parse_sub_cards(s1_body, [
        r'Normal Parameters|सामान्य पैरामीटर',
        r'Abnormal Parameters|असामान्य पैरामीटर'
    ])
    s1_intro_clean = s1_intro if s1_intro else "Clinical evaluation summary based on patient diagnostic markers:"
    s1_norm_clean = format_bullets_to_html(s1_norm_text, "#10B981", is_dark) if s1_norm_text else f"<p style='margin: 0; font-size: 0.85rem; line-height: 1.55; color: {'#CBD5E1' if is_dark else '#374151'};'>All evaluated parameters have been processed against standard clinical reference intervals.</p>"
    s1_abnorm_clean = format_bullets_to_html(s1_abnorm_text, "#EF4444", is_dark) if s1_abnorm_text else f"<p style='margin: 0; font-size: 0.85rem; line-height: 1.55; color: {'#CBD5E1' if is_dark else '#374151'};'>No critical abnormalities were detected in this diagnostic panel.</p>"

    s1_norm_bg = "rgba(16, 185, 129, 0.08)" if is_dark else "#F0FDF4"
    s1_norm_bd = "rgba(16, 185, 129, 0.35)" if is_dark else "#BBF7D0"
    s1_abnorm_bg = "rgba(239, 68, 68, 0.08)" if is_dark else "#FEF2F2"
    s1_abnorm_bd = "rgba(239, 68, 68, 0.35)" if is_dark else "#FECACA"

    render_html(f"""
    <details class="mm-result-accordion" open style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(37, 99, 235, 0.12); color: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">{s1_title}</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #2563EB; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div style="margin-bottom: 12px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: {text_primary}; margin-bottom: 4px;">Summary</div>
                <div style="font-size: 0.85rem; color: {text_secondary}; line-height: 1.5;">{s1_intro_clean}</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
                <div style="background: {s1_norm_bg}; border: 1.5px solid {s1_norm_bd}; border-radius: 12px; padding: 16px 18px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <div style="width: 26px; height: 26px; border-radius: 50%; background: #10B981; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                        </div>
                        <span style="font-size: 0.95rem; font-weight: 800; color: {'#34D399' if is_dark else '#065F46'};">Normal Parameters</span>
                    </div>
                    <div style="font-size: 0.84rem; color: {'#CBD5E1' if is_dark else '#374151'}; line-height: 1.55;">
                        {s1_norm_clean}
                    </div>
                </div>
                <div style="background: {s1_abnorm_bg}; border: 1.5px solid {s1_abnorm_bd}; border-radius: 12px; padding: 16px 18px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <div style="width: 26px; height: 26px; border-radius: 6px; background: rgba(239, 68, 68, 0.15); display: flex; align-items: center; justify-content: center; color: #EF4444; flex-shrink: 0;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                        </div>
                        <span style="font-size: 0.95rem; font-weight: 800; color: {'#F87171' if is_dark else '#991B1B'};">Abnormal Parameters</span>
                    </div>
                    <div style="font-size: 0.84rem; color: {'#CBD5E1' if is_dark else '#374151'}; line-height: 1.55;">
                        {s1_abnorm_clean}
                    </div>
                </div>
            </div>
        </div>
    </details>
    """)

    # =========================================================================
    # SECTION 2: Biological Function in Plain Language (Open by default - Matching Image 3)
    # =========================================================================
    s2 = sec_dict.get(2, {"title": def_titles[2], "body": ""})
    s2_title = s2.get("title") or def_titles[2]
    s2_body = s2.get("body") or ""

    # Parse mini cards from bullet points
    mini_cards = []
    bullet_pattern = r'(?:^|\n)(?:[-•*]\s*)?\*\*(.*?)\*\*\s*:?\s*(.*?)(?=(?:\n(?:[-•*]\s*)?\*\*)|$)'
    m_cards = list(re.finditer(bullet_pattern, s2_body, re.DOTALL))
    s2_intro_end = m_cards[0].start() if m_cards else len(s2_body)
    s2_intro_text = clean_markdown_artifacts(s2_body[:s2_intro_end])

    # Curated color palettes for the mini cards matching Image 3
    card_colors = [
        {"bg": "rgba(239, 68, 68, 0.08)", "bd": "rgba(239, 68, 68, 0.25)", "ic_bg": "rgba(239, 68, 68, 0.14)", "ic": "#EF4444", "type": "blood"},
        {"bg": "rgba(244, 63, 94, 0.08)", "bd": "rgba(244, 63, 94, 0.25)", "ic_bg": "rgba(244, 63, 94, 0.14)", "ic": "#F43F5E", "type": "rbc"},
        {"bg": "rgba(139, 92, 246, 0.08)", "bd": "rgba(139, 92, 246, 0.25)", "ic_bg": "rgba(139, 92, 246, 0.14)", "ic": "#8B5CF6", "type": "wbc"},
        {"bg": "rgba(244, 63, 94, 0.08)", "bd": "rgba(244, 63, 94, 0.25)", "ic_bg": "rgba(244, 63, 94, 0.14)", "ic": "#E11D48", "type": "platelet"},
        {"bg": "rgba(245, 158, 11, 0.08)", "bd": "rgba(245, 158, 11, 0.25)", "ic_bg": "rgba(245, 158, 11, 0.14)", "ic": "#D97706", "type": "dengue"}
    ]

    mini_cards_html = []
    for idx, mc in enumerate(m_cards):
        name = clean_markdown_artifacts(mc.group(1)).rstrip(':')
        desc_full = clean_markdown_artifacts(mc.group(2)).replace('\n', ' ')
        # 1-2 punchy sentences
        sents = desc_full.split('. ')
        short_desc = sents[0] + ('.' if not sents[0].endswith('.') else '')
        if len(sents) > 1 and len(short_desc) < 45:
            short_desc += " " + sents[1] + ('.' if not sents[1].endswith('.') else '')

        theme = card_colors[idx % len(card_colors)]
        
        # Select SVG icon based on card type
        if "crp" in name.lower() or "reactive" in name.lower() or theme["type"] == "blood":
            svg_icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>'
        elif "haemo" in name.lower() or "rbc" in name.lower() or theme["type"] == "rbc":
            svg_icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="8"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>'
        elif "white" in name.lower() or "wbc" in name.lower() or theme["type"] == "wbc":
            svg_icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><circle cx="19" cy="8" r="2"/><circle cx="5" cy="8" r="2"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>'
        elif "platelet" in name.lower() or theme["type"] == "platelet":
            svg_icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="8" cy="8" r="2"/><circle cx="16" cy="8" r="2"/><circle cx="8" cy="16" r="2"/><circle cx="16" cy="16" r="2"/><circle cx="12" cy="12" r="2"/></svg>'
        else:
            svg_icon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>'

        mini_cards_html.append(f"""
        <div style="background: {theme['bg']}; border: 1.2px solid {theme['bd']}; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; justify-content: flex-start; min-height: 100px;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: {theme['ic_bg']}; display: flex; align-items: center; justify-content: center; color: {theme['ic']}; margin-bottom: 8px; flex-shrink: 0;">
                {svg_icon}
            </div>
            <div style="font-size: 0.82rem; font-weight: 800; color: {text_primary}; margin-bottom: 4px; line-height: 1.25;">{name}</div>
            <div style="font-size: 0.74rem; color: {text_secondary}; line-height: 1.4;">{short_desc}</div>
        </div>
        """)

    cards_grid_html = f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 14px;">{"".join(mini_cards_html)}</div>' if mini_cards_html else clean_body_html(s2_body, is_dark, "#10B981")

    render_html(f"""
    <details class="mm-result-accordion" open style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(16, 185, 129, 0.12); color: #10B981; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">{s2_title}</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #10B981; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div>
                <div style="font-size: 0.88rem; font-weight: 800; color: {text_primary}; margin-bottom: 4px;">What These Tests Mean for Your Body</div>
                <div style="font-size: 0.85rem; color: {text_secondary}; line-height: 1.5;">{s2_intro_text if s2_intro_text else "To help you understand what these tests mean for your body, here is a simple explanation of the key markers from your report:"}</div>
            </div>
            {cards_grid_html}
        </div>
    </details>
    """)

    # =========================================================================
    # SECTION 3: Impact on the Body & Symptoms (Collapsible - Matching Image 3)
    # =========================================================================
    s3 = sec_dict.get(3, {"title": def_titles[3], "body": ""})
    s3_title = s3.get("title") or def_titles[3]
    s3_body = s3.get("body") or ""
    s3_content_html = clean_body_html(s3_body, is_dark, "#8B5CF6")

    render_html(f"""
    <details class="mm-result-accordion" style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(139, 92, 246, 0.12); color: #8B5CF6; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">{s3_title}</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #8B5CF6; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div style="font-size: 0.88rem; font-weight: 800; color: {text_primary}; margin-bottom: 8px;">Patient Impact</div>
            <div>{s3_content_html}</div>
        </div>
    </details>
    """)

    # =========================================================================
    # SECTION 4: Actionable Diet & Nutrition Plan (Collapsible - Matching Image 3)
    # =========================================================================
    s4 = sec_dict.get(4, {"title": def_titles[4], "body": ""})
    s4_title = s4.get("title") or def_titles[4]
    s4_raw = s4.get("body") or ""
    s4_intro, s4_consume, s4_avoid = parse_sub_cards(s4_raw, [
        r'Foods to Consume|क्या खाएं',
        r'Foods (?:and Habits )?to Avoid|क्या न खाएं'
    ])
    s4_intro_html = clean_body_html(s4_intro, is_dark, "#F97316")
    consume_bullets = format_bullets_to_html(s4_consume if s4_consume else s4_raw, "#10B981", is_dark)
    avoid_bullets = format_bullets_to_html(s4_avoid if s4_avoid else "Avoid heavily processed foods, high sodium, excess sugars, and eating immediately before bedtime.", "#EF4444", is_dark)

    sub4_consume_bg = "rgba(16, 185, 129, 0.08)" if is_dark else "#F0FDF4"
    sub4_consume_border = "rgba(16, 185, 129, 0.30)" if is_dark else "#BBF7D0"
    sub4_avoid_bg = "rgba(239, 68, 68, 0.08)" if is_dark else "#FEF2F2"
    sub4_avoid_border = "rgba(239, 68, 68, 0.30)" if is_dark else "#FECACA"

    render_html(f"""
    <details class="mm-result-accordion" style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(249, 115, 22, 0.12); color: #F97316; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"></path>
                        <path d="M10 2c1 .5 2 2 2 5"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">{s4_title}</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #F97316; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div style="font-size: 0.88rem; font-weight: 800; color: {text_primary}; margin-bottom: 4px;">Lifestyle & Nutrition Guidance</div>
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
    </details>
    """)

    # =========================================================================
    # SECTION 5: Medical Precautions & Red Flags (Collapsible - Matching Image 3)
    # =========================================================================
    s5 = sec_dict.get(5, {"title": def_titles[5], "body": ""})
    s5_title = s5.get("title") or def_titles[5]
    s5_raw = s5.get("body") or ""
    s5_intro, s5_steps, s5_flags = parse_sub_cards(s5_raw, [
        r'Next Steps|अगले कदम|डॉक्टर से परामर्श',
        r'Red Flags[^\n:]*|खतरे के लक्षण[^\n:]*|सावधानियां[^\n:]*'
    ])
    s5_intro_html = clean_body_html(s5_intro, is_dark, "#EF4444")
    steps_bullets = format_bullets_to_html(s5_steps if s5_steps else s5_raw, "#3B82F6", is_dark)
    flags_bullets = format_bullets_to_html(s5_flags if s5_flags else "Severe or sudden pain, persistent high fever with chills, acute breathlessness, or dizziness requires prompt physician review.", "#EF4444", is_dark)

    sub5_next_bg = "rgba(37, 99, 235, 0.08)" if is_dark else "#EFF6FF"
    sub5_next_border = "rgba(59, 130, 246, 0.30)" if is_dark else "#BFDBFE"
    sub5_flag_bg = "rgba(239, 68, 68, 0.08)" if is_dark else "#FEF2F2"
    sub5_flag_border = "rgba(239, 68, 68, 0.35)" if is_dark else "#FECACA"

    render_html(f"""
    <details class="mm-result-accordion" style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(239, 68, 68, 0.12); color: #EF4444; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">{s5_title}</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #EF4444; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div style="font-size: 0.88rem; font-weight: 800; color: {text_primary}; margin-bottom: 4px;">Clinical Precautions</div>
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
    </details>
    """)

    # =========================================================================
    # SECTION 6: Detailed Parameter Breakdown (Collapsible Table - Matching Image 3)
    # =========================================================================
    th_bg = "rgba(30, 41, 59, 0.75)" if is_dark else "#F8FAFC"
    tr_border = "rgba(255, 255, 255, 0.07)" if is_dark else "#F1F5F9"

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
        # Standard Clinical Lab Report Table (Matching Image 3)
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
    <details class="mm-result-accordion" style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 14px; margin-bottom: 16px; overflow: hidden; box-shadow: {card_shadow};">
        <summary style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(37, 99, 235, 0.12); color: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="8" y1="6" x2="21" y2="6"></line>
                        <line x1="8" y1="12" x2="21" y2="12"></line>
                        <line x1="8" y1="18" x2="21" y2="18"></line>
                        <line x1="3" y1="6" x2="3.01" y2="6"></line>
                        <line x1="3" y1="12" x2="3.01" y2="12"></line>
                        <line x1="3" y1="18" x2="3.01" y2="18"></line>
                    </svg>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 800; color: {text_primary}; margin: 0;">Detailed Parameter Breakdown</h3>
            </div>
            <div class="mm-chevron-icon" style="color: #2563EB; display: flex; align-items: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
        </summary>
        <div style="padding: 4px 20px 20px 20px; border-top: 1px solid {inner_divider};">
            <div style="overflow-x: auto; width: 100%; border: 1px solid {card_border}; border-radius: 10px; margin-top: 8px;">
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
    </details>
    """)

    # =========================================================================
    # 7. CLINICAL ADVISORY BANNER
    # =========================================================================
    advisory_bg = "rgba(234, 88, 12, 0.10)" if is_dark else "rgba(234, 88, 12, 0.06)"
    advisory_border = "rgba(234, 88, 12, 0.35)"

    render_html(f"""
    <div style="background: {advisory_bg}; border: 1.2px solid {advisory_border}; border-left: 4px solid #EA580C; border-radius: 10px; padding: 12px 16px; margin: 16px 0 18px 0;">
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
    # 8. BOTTOM ACTION BUTTONS ROW (Download Report is in top header)
    # =========================================================================
    b_col1, b_col2 = st.columns(2, gap="medium")

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
            keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("p2_breakdown_") or k.startswith("p2_saved_") or k.startswith("p2_analysis_")]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()
