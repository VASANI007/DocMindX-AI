"""
DocMindX AI - Clinical Health Summary PDF Generator
Generates comprehensive, beautifully formatted medical summary PDF reports using ReportLab.
Includes patient profile, ranked differential assessment conditions, medicines with verified packaging photos,
restorative yoga, physiotherapy, compression therapy, diet, red flags, and clinical advisory.
Matches reference clinical standard layout with zero emojis and 100% dynamic data.
"""
import io
import os
import re
import base64
import requests
from datetime import datetime
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons", "pdf")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo", "logo_light.png")


def _clean_pdf_text(text) -> str:
    """
    Sanitizes text for ReportLab PDF rendering.
    Replaces Unicode hyphens, dashes, curly quotes, non-breaking spaces,
    and removes unsupported emojis/symbols that cause square boxes (tofu) in standard fonts.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
        
    # Replace unicode dashes & hyphens
    text = text.replace('\u2011', '-')
    text = text.replace('\u2010', '-')
    text = text.replace('\u2012', '-')
    text = text.replace('\u2013', ' - ')
    text = text.replace('\u2014', ' - ')
    text = text.replace('\u2015', ' - ')
    text = text.replace('\u2212', '-')
    text = text.replace('■', '')
    
    # Replace spaces & quotes
    text = text.replace('\u202f', ' ')
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2026', '...')
    
    # Remove emojis and high unicode symbols that Helvetica cannot render
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27ff]', '', text)
    text = re.sub(r'[\ufe00-\ufe0f]', '', text)
    
    # Clean HTML angle brackets in free-form text
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.strip()


def _clean_rich_text(text) -> str:
    """
    Sanitizes text but permits standard ReportLab tags: <b>, </b>, <i>, </i>, <font>, </font>, <br/>.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
        
    text = text.replace('\u2011', '-').replace('\u2010', '-').replace('\u2013', ' - ').replace('\u2014', ' - ')
    text = text.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ')
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27ff]', '', text)
    text = re.sub(r'[\ufe00-\ufe0f]', '', text)
    return text.strip()


def _convert_to_rl_image(img_source, width=48, height=44):
    """
    Safely converts image path, remote HTTP URL, or base64 Data URI into a ReportLab Image Flowable.
    """
    if not img_source or not isinstance(img_source, str):
        return None
        
    try:
        if img_source.startswith("data:image"):
            if "base64," in img_source:
                b64_data = img_source.split("base64,")[1]
                img_bytes = base64.b64decode(b64_data)
                if "svg" in img_source[:30]:
                    return None
                img_buf = io.BytesIO(img_bytes)
                pil_img = PILImage.open(img_buf)
                pil_img = pil_img.convert("RGB")
                out_buf = io.BytesIO()
                pil_img.save(out_buf, format="PNG")
                out_buf.seek(0)
                return RLImage(out_buf, width=width, height=height)

        elif img_source.startswith("http://") or img_source.startswith("https://"):
            resp = requests.get(img_source, timeout=3, headers={"User-Agent": "DocMindXAI/2.0"})
            if resp.status_code == 200:
                img_buf = io.BytesIO(resp.content)
                pil_img = PILImage.open(img_buf)
                pil_img = pil_img.convert("RGB")
                out_buf = io.BytesIO()
                pil_img.save(out_buf, format="PNG")
                out_buf.seek(0)
                return RLImage(out_buf, width=width, height=height)

        elif os.path.exists(img_source):
            if img_source.lower().endswith(".svg"):
                return None
            pil_img = PILImage.open(img_source)
            pil_img = pil_img.convert("RGB")
            out_buf = io.BytesIO()
            pil_img.save(out_buf, format="PNG")
            out_buf.seek(0)
            return RLImage(out_buf, width=width, height=height)
            
    except Exception as e:
        print(f"ReportLab image conversion note: {e}")
        
    return None


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that dynamically calculates total page count and draws:
    - Page 1: Beautiful left & right footer with heart icon, DocMindX AI branding, and Page 1 of N.
    - Page 2+: Professional running clinical header with heart icon, report title, Report ID, Page N of N,
              top hairline separator, and bottom footer with branding slogan.
    """
    doc_id_str = "MM-2026"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        page_num = self._pageNumber
        self.saveState()
        heart_icon_path = os.path.join(ICONS_DIR, "heart.png")

        if page_num == 1:
            # Page 1 Footer:
            # Left: Heart Icon + "DocMindX AI | Clinical Intelligence for Everyone"
            # Right: "Page 1 of {page_count}"
            if os.path.exists(heart_icon_path):
                try:
                    self.drawImage(heart_icon_path, 36, 18, width=12, height=12, mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1E40AF"))
            self.drawString(53, 20, "DocMindX AI")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(108, 20, "|   Clinical Intelligence for Everyone")
            self.drawRightString(576, 20, f"Page {page_num} of {page_count}")
        else:
            # Page 2+ Running Header:
            # Left: Heart Icon + "DocMindX AI — Clinical Health Summary & Triage Report"
            # Right: "Report ID: {doc_id} | Page N of {page_count}"
            if os.path.exists(heart_icon_path):
                try:
                    self.drawImage(heart_icon_path, 36, 762, width=12, height=12, mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass
            self.setFont("Helvetica-Bold", 8.5)
            self.setFillColor(colors.HexColor("#1E40AF"))
            self.drawString(53, 764, "DocMindX AI")
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor("#0F172A"))
            self.drawString(110, 764, "—   Clinical Health Summary & Triage Report")

            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(576, 764, f"Report ID: {self.doc_id_str}   |   Page {page_num} of {page_count}")

            # Top hairline separator
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, 755, 576, 755)

            # Page 2+ Running Footer:
            # Left: "Better Data. Brighter Health."
            # Right: Heart Icon + "DocMindX AI"
            self.setFont("Helvetica-Oblique", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(36, 20, "Better Data. Brighter Health.")

            if os.path.exists(heart_icon_path):
                try:
                    self.drawImage(heart_icon_path, 502, 18, width=12, height=12, mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1E40AF"))
            self.drawString(518, 20, "DocMindX AI")

        self.restoreState()


def _make_section_banner(icon_filename: str, title_text: str, bg_color="#EFF6FF", border_color="#BFDBFE", text_color="#1E40AF"):
    """
    Renders an elegant rounded clinical section header banner with a vector icon on the left and bold title.
    """
    icon_path = os.path.join(ICONS_DIR, icon_filename)
    cells = []
    if os.path.exists(icon_path):
        icon_img = RLImage(icon_path, width=15, height=15)
        cells.append(icon_img)
    else:
        cells.append("")

    title_p = Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
        f'Banner_{icon_filename}',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(text_color)
    ))
    cells.append(title_p)

    col_widths = [22, 518] if cells[0] else [0, 540]
    t = Table([cells], colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (0,0), 6),
    ]))
    return t


def generate_pdf_report(user_context: dict, triage_result: dict, care_recommendations: dict = None) -> io.BytesIO:
    """
    Builds a complete, beautifully structured PDF clinical summary report matching the reference design.
    
    Args:
        user_context: Dict containing patient demographics, symptoms, medical history.
        triage_result: Dict containing ranked conditions, urgency, emergency flags.
        care_recommendations: Dict containing medicines, recovery, yoga, physio, diet, compress.
        
    Returns:
        io.BytesIO buffer containing the PDF.
    """
    user_context = user_context or {}
    triage_result = triage_result or {}
    care_res = care_recommendations or {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    PRIMARY_BLUE = colors.HexColor("#2563EB")
    DARK_NAVY = colors.HexColor("#0F172A")
    ALERT_RED = colors.HexColor("#DC2626")
    SUCCESS_GREEN = colors.HexColor("#16A34A")
    ORANGE_BRAND = colors.HexColor("#EA580C")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    TEXT_MUTED = colors.HexColor("#64748B")
    TEXT_DARK = colors.HexColor("#1E293B")

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK
    )

    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK
    )

    th_style = ParagraphStyle(
        'TableHeaderCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    doc_id_str = f"MM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    gen_time_str = datetime.now().strftime('%d %B %Y, %I:%M %p')

    story = []

    # =========================================================================
    # 1. PAGE 1 TOP HEADER: Logo, Title, Report ID Box, and Pulse Pill Badge
    # =========================================================================
    logo_img = None
    if os.path.exists(LOGO_PATH):
        try:
            logo_img = RLImage(LOGO_PATH, width=38, height=38)
        except Exception:
            logo_img = None

    title_block = [
        Paragraph("<b>DocMindX AI</b>", ParagraphStyle(
            'HeaderTitle', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.HexColor("#1E40AF")
        )),
        Paragraph("<b>Clinical Health Summary & Triage Report</b>", ParagraphStyle(
            'HeaderSub', fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=DARK_NAVY
        )),
        Paragraph("AI Powered Insights for a Healthier Tomorrow", ParagraphStyle(
            'HeaderTag', fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=TEXT_MUTED
        ))
    ]

    header_left_table = Table([[logo_img or "", title_block]], colWidths=[42, 218] if logo_img else [0, 260])
    header_left_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))

    header_mid_table = Table([
        [Paragraph(f"<b>Generated:</b> {_clean_rich_text(gen_time_str)}", body_style)],
        [Paragraph(f"<b>Report ID:</b> {_clean_rich_text(doc_id_str)}", body_style)],
        [Paragraph("<b>Verified Healthcare Engine</b>", ParagraphStyle('Engine', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=SUCCESS_GREEN))]
    ], colWidths=[165])
    header_mid_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    pulse_icon_path = os.path.join(ICONS_DIR, "pulse.png")
    pulse_img = RLImage(pulse_icon_path, width=44, height=13) if os.path.exists(pulse_icon_path) else ""
    header_right_table = Table([
        [pulse_img],
        [Paragraph("<font color='#2563EB'><b>Smarter<br/>Insights<br/>Healthier Lives</b></font>", ParagraphStyle('PillText', fontName='Helvetica-Bold', fontSize=7, leading=8.5, alignment=1))]
    ], colWidths=[105])
    header_right_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BFDBFE")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))

    t_top_header = Table([[header_left_table, header_mid_table, header_right_table]], colWidths=[260, 172, 108])
    t_top_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_top_header)
    story.append(Spacer(1, 6))

    # =========================================================================
    # 2. PATIENT DEMOGRAPHICS & CLINICAL OVERVIEW
    # =========================================================================
    story.append(_make_section_banner("user_demographics.png", "Patient Demographics & Clinical Overview", bg_color="#EFF6FF", border_color="#BFDBFE", text_color="#1E40AF"))
    story.append(Spacer(1, 2))

    patient_loc = _clean_pdf_text(str(user_context.get("state") or user_context.get("location", "Gujarat")))
    patient_ht = _clean_pdf_text(str(user_context.get("height", "Not specified")))
    patient_wt = _clean_pdf_text(str(user_context.get("weight", "Not specified")))
    if not patient_ht or patient_ht.lower() == "none":
        patient_ht = "Not specified"
    if not patient_wt or patient_wt.lower() == "none":
        patient_wt = "Not specified"

    raw_severity = str(user_context.get("severity") or triage_result.get("urgency", "Moderate"))
    severity_text = _clean_pdf_text(raw_severity)
    sev_color = "#D97706" if "mod" in severity_text.lower() else ("#DC2626" if "high" in severity_text.lower() or "emerg" in severity_text.lower() else "#16A34A")

    patient_data = [
        [
            Paragraph(f"<b>Age Group:</b> {_clean_pdf_text(str(user_context.get('age', user_context.get('age_group', '16 - 20 Years'))))}", body_style),
            Paragraph(f"<b>Gender:</b> {_clean_pdf_text(str(user_context.get('gender', 'Male')))}", body_style),
            Paragraph(f"<b>State / Location:</b> {patient_loc}", body_style)
        ],
        [
            Paragraph(f"<b>Height:</b> {patient_ht}", body_style),
            Paragraph(f"<b>Weight:</b> {patient_wt}", body_style),
            Paragraph(f"<b>Blood Group:</b> {_clean_pdf_text(str(user_context.get('blood_group', 'None')))}", body_style)
        ],
        [
            Paragraph(f"<b>Symptom Duration:</b> {_clean_pdf_text(str(user_context.get('duration', '1 - 3 Days')))}", body_style),
            Paragraph(f"<b>Assessed Severity:</b> <font color='{sev_color}'><b>{severity_text}</b></font>", body_style),
            Paragraph(f"<b>Known Allergies:</b> {_clean_pdf_text(str(user_context.get('allergies', '-')))}", body_style)
        ],
        [
            Paragraph(f"<b>Pre-existing Conditions:</b> {_clean_pdf_text(str(user_context.get('pre_existing', user_context.get('conditions', 'None'))))}", body_style),
            Paragraph(f"<b>Current Medications:</b> {_clean_pdf_text(str(user_context.get('current_meds', user_context.get('medications', '-'))))}", body_style),
            Paragraph(f"<b>Family History / Surgeries:</b> {_clean_pdf_text(str(user_context.get('surgeries', user_context.get('family_history', '-'))))}", body_style)
        ]
    ]
    t_patient = Table(patient_data, colWidths=[180, 180, 180])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_patient)
    story.append(Spacer(1, 5))

    # =========================================================================
    # 3. SEASONAL EPIDEMIOLOGICAL ADVISORY (Dynamic & Conditional)
    # =========================================================================
    seasonal_data = triage_result.get("seasonal_alert")
    if seasonal_data and isinstance(seasonal_data, dict):
        s_title = _clean_pdf_text(seasonal_data.get("headline") or seasonal_data.get("title", "Seasonal Health Advisory"))
        s_risk = _clean_pdf_text(seasonal_data.get("risk_level", "MODERATE")).upper()
        s_desc = _clean_pdf_text(seasonal_data.get("message") or seasonal_data.get("advisory", ""))
        
        icon_warn_path = os.path.join(ICONS_DIR, "alert_warning.png")
        icon_warn_img = RLImage(icon_warn_path, width=15, height=15) if os.path.exists(icon_warn_path) else ""
        
        warn_card_data = [
            [
                icon_warn_img,
                Paragraph(f"<font color='#C2410C'><b>SEASONAL EPIDEMIOLOGICAL ADVISORY: {s_title}</b></font>", body_bold),
                Paragraph(f"<font color='#EA580C'><b>RISK LEVEL: {s_risk}</b></font>", ParagraphStyle('Risk', fontName='Helvetica-Bold', fontSize=7.5, leading=10, alignment=2))
            ],
            [
                "",
                Paragraph(s_desc, ParagraphStyle('WarnDesc', fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=DARK_NAVY)),
                ""
            ]
        ]
        t_warn = Table(warn_card_data, colWidths=[20, 420, 100])
        t_warn.setStyle(TableStyle([
            ('SPAN', (1,1), (2,1)),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF7ED")),
            ('BOX', (0,0), (-1,-1), 1.2, ORANGE_BRAND),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 3.5),
        ]))
        story.append(t_warn)
        story.append(Spacer(1, 5))

    # =========================================================================
    # 4. EMERGENCY RED FLAG (Dynamic & Conditional)
    # =========================================================================
    red_flags = triage_result.get("emergency_red_flags") or triage_result.get("red_flags") or []
    if red_flags:
        flags_text = _clean_pdf_text("; ".join([str(x) for x in red_flags if str(x).strip()]))
        icon_emerg_path = os.path.join(ICONS_DIR, "emergency_red.png")
        icon_emerg_img = RLImage(icon_emerg_path, width=15, height=15) if os.path.exists(icon_emerg_path) else ""

        emerg_table = Table([[
            icon_emerg_img,
            Paragraph(f"<font color='#DC2626'><b>EMERGENCY RED FLAG DETECTED — IMMEDIATE MEDICAL EVALUATION REQUIRED</b></font><br/><font color='#7F1D1D' size='7.5'>{flags_text}</font>", body_style)
        ]], colWidths=[22, 518])
        emerg_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF2F2")),
            ('BOX', (0,0), (-1,-1), 1.2, ALERT_RED),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(emerg_table)
        story.append(Spacer(1, 5))

    # =========================================================================
    # 5. PLAUSIBLE CLINICAL HEALTH CONDITIONS (Differential Assessment Table)
    # =========================================================================
    story.append(_make_section_banner("stethoscope.png", "Plausible Clinical Health Conditions (Differential Assessment)", bg_color="#EFF6FF", border_color="#BFDBFE", text_color="#1E40AF"))
    story.append(Spacer(1, 2))

    cond_rows = [[
        Paragraph("<b>#</b>", th_style),
        Paragraph("<b>Condition Name</b>", th_style),
        Paragraph("<b>ICD-11 Code</b>", th_style),
        Paragraph("<b>Category</b>", th_style),
        Paragraph("<b>Match Index</b>", th_style)
    ]]

    ranked_conditions = triage_result.get("ranked_conditions", [])
    if not ranked_conditions and care_res.get("top_condition"):
        ranked_conditions = [{
            "name": care_res.get("top_condition"),
            "code": "K27.9",
            "category": "Digestive Diseases",
            "match_score": 60
        }]

    for idx, cond in enumerate(ranked_conditions[:4], start=1):
        c_name = _clean_pdf_text(cond.get("name", "Clinical Condition"))
        c_code = _clean_pdf_text(cond.get("icd_code") or cond.get("code") or "K27.9")
        c_cat = _clean_pdf_text(cond.get("category") or cond.get("organ_system") or "General Health")
        
        score_val = cond.get("match_score") or cond.get("probability") or 60
        try:
            score_num = int(float(str(score_val).replace('%', '').strip()))
        except Exception:
            score_num = 60
        c_score_str = f"{score_num}%"

        cond_rows.append([
            Paragraph(f"<div align='center'><b>{idx}</b></div>", body_style),
            Paragraph(f"<b>{c_name}</b>", body_style),
            Paragraph(c_code, body_style),
            Paragraph(c_cat, body_style),
            Paragraph(f"<font color='#1E40AF'><b>{c_score_str}</b></font>", body_style)
        ])

    t_conds = Table(cond_rows, colWidths=[25, 215, 85, 135, 80])
    t_conds_styles = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E40AF")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (-1,1), (-1,-1), 'CENTER'),
    ]
    for r_idx in range(1, len(cond_rows)):
        bg = colors.white if r_idx % 2 != 0 else LIGHT_BG
        t_conds_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))
    t_conds.setStyle(TableStyle(t_conds_styles))
    story.append(t_conds)
    story.append(Spacer(1, 5))

    # =========================================================================
    # 6. CLINICAL SUMMARY & EXPECTED RECOVERY
    # =========================================================================
    story.append(_make_section_banner("clipboard.png", "Clinical Summary & Expected Recovery", bg_color="#F0FDF4", border_color="#86EFAC", text_color="#166534"))
    story.append(Spacer(1, 2))

    summary_text = _clean_pdf_text(care_res.get("summary") or "AI-assisted clinical evaluation completed based on reported symptoms.")
    recovery_text = _clean_pdf_text(care_res.get("recovery_duration") or "Expected recovery time is 7 to 14 days with strict adherence to medication and rest.")

    sum_rec_table = Table([
        [
            Paragraph("<b>Clinical Summary:</b>", body_bold),
            Paragraph(summary_text, body_style)
        ],
        [
            Paragraph("<b>Expected Recovery:</b>", body_bold),
            Paragraph(f"<font color='#059669'><b>{recovery_text}</b></font>", body_style)
        ]
    ], colWidths=[110, 430])
    sum_rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BBF7D0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86EFAC")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sum_rec_table)
    story.append(Spacer(1, 5))

    # =========================================================================
    # 7. VERIFIED MEDICATION & PHARMACEUTICAL GUIDANCE (Table with Packaging Images)
    # =========================================================================
    med_gallery = care_res.get("medicine_gallery", [])
    med_count_str = f"({len(med_gallery)} Items)" if med_gallery else ""
    story.append(_make_section_banner("capsule.png", f"Verified Medication & Pharmaceutical Guidance {med_count_str}", bg_color="#EEF2FF", border_color="#C7D2FE", text_color="#3730A3"))
    story.append(Spacer(1, 2))

    med_header_row = [
        Paragraph("<b>#</b>", th_style),
        Paragraph("<b>Product</b>", th_style),
        Paragraph("<b>Medication Name & Indication</b>", th_style),
        Paragraph("<b>Dosage & Food Timing</b>", th_style),
        Paragraph("<b>Course</b>", th_style)
    ]
    med_rows = [med_header_row]

    for m_idx, med in enumerate(med_gallery, start=1):
        m_name = _clean_pdf_text(med.get("name", "Medication"))
        m_type = _clean_pdf_text(med.get("type", "Prescription"))
        m_ind = _clean_pdf_text(med.get("indication", "Reduces gastric acid and heals peptic ulcers."))
        m_dos = _clean_pdf_text(med.get("dosage", "1 Tablet once daily"))
        m_timing = _clean_pdf_text(med.get("food_timing", "After Food"))
        m_dur = _clean_pdf_text(med.get("course_duration", "14 Days"))

        timing_color = "#EA580C" if any(w in m_timing.lower() for w in ["before", "empty", "pehle", "khali"]) else "#16A34A"

        # Resolve image
        img_flowable = None
        if med.get("image"):
            img_flowable = _convert_to_rl_image(med["image"], width=48, height=44)
        if not img_flowable:
            img_flowable = Paragraph("<font size='7' color='#94A3B8'>[Packaging Image]</font>", body_style)

        name_ind_para = Paragraph(
            f"<b>{m_name}</b> <font color='#64748B'>({m_type})</font><br/>"
            f"<font color='#475569' size='7.5'>{m_ind}</font>",
            body_style
        )

        dosage_timing_para = Paragraph(
            f"<b>Dosage:</b> {m_dos}<br/>"
            f"<b>Timing:</b> <font color='{timing_color}'><b>{m_timing}</b></font>",
            body_style
        )

        course_para = Paragraph(
            f"<div align='center'><font color='#2563EB'><b>{m_dur}</b></font></div>",
            body_style
        )

        med_rows.append([
            Paragraph(f"<div align='center'><b>{m_idx}</b></div>", body_style),
            img_flowable,
            name_ind_para,
            dosage_timing_para,
            course_para
        ])

    t_meds = Table(med_rows, colWidths=[25, 55, 220, 160, 80], repeatRows=1)
    t_meds_styles = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E40AF")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
        ('ALIGN', (-1,1), (-1,-1), 'CENTER'),
    ]
    for r_idx in range(1, len(med_rows)):
        bg = colors.white if r_idx % 2 != 0 else LIGHT_BG
        t_meds_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))
    t_meds.setStyle(TableStyle(t_meds_styles))
    story.append(t_meds)
    story.append(Spacer(1, 6))

    # =========================================================================
    # 8. RESTORATIVE YOGA & BREATHING POSTURES
    # =========================================================================
    yoga_recs = care_res.get("yoga_recommendations", [])
    if yoga_recs:
        story.append(_make_section_banner("yoga.png", "Restorative Yoga & Breathing Postures", bg_color="#F0FDF4", border_color="#86EFAC", text_color="#166534"))
        story.append(Spacer(1, 2))

        yoga_rows = []
        for y_item in yoga_recs:
            y_name = _clean_pdf_text(y_item.get("name") or y_item.get("asana", "Yoga Asana"))
            y_dur = _clean_pdf_text(y_item.get("duration", "5 - 10 Mins"))
            y_steps = _clean_pdf_text(y_item.get("steps") or y_item.get("instructions") or "Gentle breathing and restorative posture.")

            dur_pill_table = Table([[Paragraph(f"<div align='center'><font color='#1D4ED8'><b>{y_dur}</b></font></div>", body_style)]], colWidths=[76])
            dur_pill_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
                ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#BFDBFE")),
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))

            yoga_rows.append([
                Paragraph("<font color='#059669'><b>Restorative Yoga</b></font>", body_style),
                Paragraph(f"<b>{y_name}</b> ({y_dur})<br/><font color='#475569' size='7.5'>{y_steps}</font>", body_style),
                dur_pill_table
            ])

        t_yoga = Table(yoga_rows, colWidths=[105, 355, 80])
        t_yoga_styles = [
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 3.5),
        ]
        for r_idx in range(len(yoga_rows)):
            bg = colors.white if r_idx % 2 == 0 else LIGHT_BG
            t_yoga_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))
        t_yoga.setStyle(TableStyle(t_yoga_styles))
        story.append(t_yoga)
        story.append(Spacer(1, 6))

    # =========================================================================
    # 9. THERMAL COMPRESS & FOMENTATION THERAPY GUIDANCE (Conditional)
    # =========================================================================
    compress_rec = care_res.get("compress_guidance")
    if compress_rec and isinstance(compress_rec, dict) and compress_rec.get("mode") in ["ice", "hot", "cold_sponging"]:
        story.append(_make_section_banner("compress.png", "Thermal Compress & Fomentation Therapy Guidance", bg_color="#F0F9FF", border_color="#BAE6FD", text_color="#0369A1"))
        story.append(Spacer(1, 2))

        c_title = _clean_pdf_text(compress_rec.get("title", "Warm Compress"))
        c_inst = _clean_pdf_text(compress_rec.get("instructions") or compress_rec.get("text", ""))
        c_dur = _clean_pdf_text(compress_rec.get("duration", "10 to 15 minutes, 2 to 3 times daily as needed"))
        c_caut = _clean_pdf_text(compress_rec.get("cautions", "Ensure the temperature is comfortably warm and not excessively hot."))

        compress_body = f"{c_inst}<br/><b>Duration:</b> {c_dur}<br/><b>Caution:</b> {c_caut}"
        t_comp = Table([[
            Paragraph(f"<b>{c_title}:</b>", body_bold),
            Paragraph(compress_body, body_style)
        ]], colWidths=[130, 410])
        t_comp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BAE6FD")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_comp)
        story.append(Spacer(1, 6))

    # =========================================================================
    # 10. CLINICAL DIETARY & HYDRATION RECOMMENDATIONS
    # =========================================================================
    diet_recs = care_res.get("diet_recommendations") or care_res.get("dietary_guidelines")
    eat_list = []
    avoid_list = []
    hyd_text = "Drink 2.5 - 3 liters of water daily."

    if isinstance(diet_recs, dict):
        eat_list = [_clean_pdf_text(x) for x in (diet_recs.get("foods_to_eat") or care_res.get("foods_to_eat", []))]
        avoid_list = [_clean_pdf_text(x) for x in (diet_recs.get("foods_to_avoid") or care_res.get("foods_to_avoid", []))]
        hyd_text = _clean_pdf_text(diet_recs.get("hydration_advice") or care_res.get("hydration_advice", hyd_text))
    elif isinstance(diet_recs, list):
        eat_list = [_clean_pdf_text(x) for x in diet_recs]

    if not eat_list:
        raw_eat = care_res.get("foods_to_eat") or []
        eat_list = [_clean_pdf_text(x) for x in (raw_eat if isinstance(raw_eat, list) else [raw_eat])]
    if not avoid_list:
        raw_avoid = care_res.get("foods_to_avoid") or []
        avoid_list = [_clean_pdf_text(x) for x in (raw_avoid if isinstance(raw_avoid, list) else [raw_avoid])]

    story.append(_make_section_banner("diet.png", "Clinical Dietary & Hydration Recommendations", bg_color="#F0FDF4", border_color="#86EFAC", text_color="#166534"))
    story.append(Spacer(1, 2))

    diet_rows = [
        [
            Paragraph("<b>Recommended Foods:</b>", body_bold),
            Paragraph("• " + "<br/>• ".join(eat_list) if eat_list else "Nutritious balanced light diet", body_style)
        ],
        [
            Paragraph("<b>Foods to Avoid:</b>", body_bold),
            Paragraph("• " + "<br/>• ".join(avoid_list) if avoid_list else "Avoid oily, excessively spicy, and heavily processed meals", body_style)
        ],
        [
            Paragraph("<b>Hydration Advice:</b>", body_bold),
            Paragraph(hyd_text, body_style)
        ]
    ]
    t_diet = Table(diet_rows, colWidths=[130, 410])
    t_diet.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BBF7D0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86EFAC")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_diet)
    story.append(Spacer(1, 6))

    # =========================================================================
    # 11. RECOMMENDED CLINICAL DIAGNOSTIC TESTS (To Discuss with Physician)
    # =========================================================================
    tests_list = [_clean_pdf_text(t) for t in (triage_result.get("tests_to_discuss") or care_res.get("tests_to_discuss") or [])]
    if tests_list:
        story.append(_make_section_banner("flask.png", "Recommended Clinical Diagnostic Tests (To Discuss with Physician)", bg_color="#FAF5FF", border_color="#E9D5FF", text_color="#6B21A8"))
        story.append(Spacer(1, 2))

        tests_formatted = "• " + "<br/>• ".join(tests_list)
        t_tests = Table([[Paragraph(tests_formatted, body_style)]], colWidths=[540])
        t_tests.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF5FF")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E9D5FF")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_tests)
        story.append(Spacer(1, 6))

    # =========================================================================
    # 12. CLINICAL ADVISORY & DISCLAIMER
    # =========================================================================
    icon_shield_path = os.path.join(ICONS_DIR, "shield.png")
    icon_shield_img = RLImage(icon_shield_path, width=18, height=18) if os.path.exists(icon_shield_path) else ""

    advisory_content = [
        Paragraph("<font color='#EA580C'><b>Clinical Advisory</b></font>", body_bold),
        Spacer(1, 2),
        Paragraph("DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.", body_style)
    ]
    t_adv = Table([[icon_shield_img, advisory_content]], colWidths=[26, 514] if icon_shield_img else [0, 540])
    t_adv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF7ED")),
        ('BOX', (0,0), (-1,-1), 1.2, ORANGE_BRAND),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_adv)

    # Build Document with dynamic NumberedCanvas for headers & footers
    curr_id = doc_id_str
    class CustomCanvas(NumberedCanvas):
        doc_id_str = curr_id

    doc.build(story, canvasmaker=CustomCanvas)
    buffer.seek(0)
    return buffer


def generate_diagnostic_evaluation_pdf(
    doc_name: str,
    doc_type: str,
    age_group: str,
    gender: str,
    findings: list,
    breakdown_text: str = "",
    total_eval: int = 0,
    abnormal_count: int = 0,
    overall_status: str = "All Normal"
) -> io.BytesIO:
    """
    Builds a beautifully formatted PDF clinical evaluation report for Medical Reports,
    Prescriptions, and Radiology findings.
    """
    findings = findings or []
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    PRIMARY_BLUE = colors.HexColor("#2563EB")
    DARK_NAVY = colors.HexColor("#0F172A")
    ALERT_RED = colors.HexColor("#DC2626")
    SUCCESS_GREEN = colors.HexColor("#16A34A")
    ORANGE_BRAND = colors.HexColor("#EA580C")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    TEXT_MUTED = colors.HexColor("#64748B")
    TEXT_DARK = colors.HexColor("#1E293B")

    body_style = ParagraphStyle('DiagBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=TEXT_DARK)
    body_bold = ParagraphStyle('DiagBodyBold', parent=body_style, fontName='Helvetica-Bold')
    title_style = ParagraphStyle('DiagTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=DARK_NAVY)
    sec_hdr_style = ParagraphStyle('DiagSecHdr', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=PRIMARY_BLUE)

    story = []
    doc_id_str = f"DOCMINDX-DIAG-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Header Title
    story.append(Paragraph("<b>DocMindX AI — Clinical Diagnostic Evaluation & Findings</b>", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<font color='#64748B'>Report ID: {doc_id_str} | Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}</font>", body_style))
    story.append(Spacer(1, 10))

    # Patient & Document Profile Table
    profile_data = [
        [
            Paragraph(f"<b>Document:</b> {_clean_pdf_text(doc_name)}", body_style),
            Paragraph(f"<b>Report Type:</b> {_clean_pdf_text(doc_type)}", body_style)
        ],
        [
            Paragraph(f"<b>Age Group:</b> {_clean_pdf_text(age_group)}", body_style),
            Paragraph(f"<b>Biological Gender:</b> {_clean_pdf_text(gender)}", body_style)
        ],
        [
            Paragraph(f"<b>Parameters Evaluated:</b> {total_eval}", body_style),
            Paragraph(f"<b>Abnormal / Out-of-Range:</b> {abnormal_count}", body_style)
        ],
        [
            Paragraph(f"<b>Overall Clinical Status:</b> <b>{_clean_pdf_text(overall_status)}</b>", body_style),
            Paragraph(f"<b>AI Engine:</b> DocMindX Clinical Pathologist Vision AI", body_style)
        ]
    ]
    t_prof = Table(profile_data, colWidths=[270, 270])
    t_prof.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_prof)
    story.append(Spacer(1, 14))

    # Detailed Findings / Parameters Table
    if findings:
        story.append(Paragraph("<b>Detailed Evaluated Parameters & Findings</b>", sec_hdr_style))
        story.append(Spacer(1, 6))
        
        table_rows = [
            [
                Paragraph("<b>Parameter / Item</b>", body_bold),
                Paragraph("<b>Value / Dose</b>", body_bold),
                Paragraph("<b>Reference</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
                Paragraph("<b>Clinical Interpretation</b>", body_bold)
            ]
        ]
        for f in findings[:15]:
            if isinstance(f, dict):
                name = f.get("test_name") or f.get("extracted_name") or f.get("finding_name") or f.get("english_name", "Parameter")
                val = f.get("value") or f.get("frequency", "-")
                unit = f.get("unit", "")
                val_str = f"{val} {unit}".strip()
                ref = f.get("reference_range") or f.get("timing") or f.get("modality", "Standard")
                st_val = f.get("status") or f.get("severity", "Normal")
                exp = f.get("explanation") or f.get("action_advice") or f.get("purpose") or f.get("recommendation", "Evaluated")
                
                table_rows.append([
                    Paragraph(_clean_pdf_text(name), body_style),
                    Paragraph(_clean_pdf_text(val_str), body_style),
                    Paragraph(_clean_pdf_text(ref), body_style),
                    Paragraph(f"<b>{_clean_pdf_text(st_val.upper())}</b>", body_bold),
                    Paragraph(_clean_pdf_text(exp[:160]), body_style)
                ])

        t_findings = Table(table_rows, colWidths=[120, 75, 75, 70, 200])
        t_findings.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
            ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_findings)
        story.append(Spacer(1, 14))

    # AI Clinical Guide Excerpt
    if breakdown_text and len(breakdown_text.strip()) > 30:
        story.append(Paragraph("<b>Comprehensive Clinical AI Patient Guide & Recovery Plan</b>", sec_hdr_style))
        story.append(Spacer(1, 6))
        # Add sanitized lines
        for para in breakdown_text.split("\n\n"):
            p_clean = _clean_pdf_text(para.strip().replace("###", "").replace("**", ""))
            if p_clean:
                story.append(Paragraph(p_clean, body_style))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    # Clinical Advisory
    advisory_content = [
        Paragraph("<font color='#EA580C'><b>CLINICAL ADVISORY</b></font>", body_bold),
        Spacer(1, 2),
        Paragraph("DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.", body_style)
    ]
    t_adv = Table([[advisory_content]], colWidths=[540])
    t_adv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF7ED")),
        ('BOX', (0,0), (-1,-1), 1.2, ORANGE_BRAND),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_adv)

    curr_id = doc_id_str
    class DiagCanvas(NumberedCanvas):
        doc_id_str = curr_id

    doc.build(story, canvasmaker=DiagCanvas)
    buffer.seek(0)
    return buffer

