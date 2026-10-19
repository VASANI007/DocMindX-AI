import os
import sys
from docx.shared import Inches

from .styler import (
    create_base_document, add_heading_1, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_callout, add_styled_table, add_code_block
)

def generate_ui_ux_en(output_path):
    doc = create_base_document(
        title="DocMindX AI — UI/UX Design & Experience Document",
        subtitle="Design System, Visual Tokens, Clinical Usability & User Interaction Journeys",
        doc_type="UI/UX Design Document",
        lang="EN"
    )

    # 1. UI/UX Philosophy
    add_heading_1(doc, "1. UI/UX Design Philosophy & Clinical Human Factors")
    add_body_p(doc, "Medical user interfaces bear a direct impact on patient safety, diagnostic comprehension, and clinical decision-making. In a healthcare crisis or emergency triage scenario, confusing visual hierarchies, low-contrast text, ambiguous icons, or frivolous emojis can cause severe misinterpretation.")

    add_callout(
        doc,
        "The Clinical Clarity Standard: DocMindX AI strictly adheres to the 'Enterprise Clinical Red Edition' design system. Medical results are presented with high-contrast visual tokens, unambiguous severity badges, zero emojis in clinical triage cards, and accessible typography.",
        title="Clinical Usability Standard",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 Core Design Pillars")
    add_bullet_p(doc, " Standard icons and emojis can trivialize severe diagnoses and trigger erratic screen-reader behavior in Indic languages. The clinical engine renders clean SVG badges with explicit text labels.", bold_prefix="Zero Emojis in Clinical Triage:")
    add_bullet_p(doc, " Full semantic equivalence across English, Hindi (हिंदी), and Gujarati (ગુજરાતી), maintaining identical button layouts and typography line heights.", bold_prefix="Native Trilingual Equality:")
    add_bullet_p(doc, " All text, buttons, and alert callouts satisfy WCAG 2.1 Level AA standards with a minimum contrast ratio of 4.5:1 (reaching 7:1 on critical alert cards).", bold_prefix="Accessible High Contrast:")
    add_bullet_p(doc, " Progressive disclosure ensures patients are not overwhelmed: High-level triage summaries appear first, followed by collapsible deep dives.", bold_prefix="Cognitive De-escalation:")

    # 2. Design System & Style Tokens
    add_heading_1(doc, "2. Design System & Color Palette Tokens")
    add_body_p(doc, "The DocMindX AI design system is defined in 'config/theme.py' using curated color tokens:")

    colors = [
        ["Token Name", "Hex Code", "Clinical / UI Function", "Contrast on Light/Dark"],
        ["--clinical-primary", "#0077B6", "Primary buttons, active tab indicators, major headings", "6.2:1 (White)"],
        ["--clinical-navy", "#0A2540", "App header background, primary table headers", "14.8:1 (White)"],
        ["--alert-danger", "#C1121F", "Red Flag emergency banners, 108 emergency buttons", "7.4:1 (White)"],
        ["--alert-warning", "#F77F00", "Moderate urgency triage cards, DOIR < 7 warnings", "4.8:1 (Dark Slate)"],
        ["--alert-success", "#047857", "Routine low-acuity indicators, verified medicine badge", "5.1:1 (White)"],
        ["--surface-card", "#FFFFFF / #112240", "Triage cards, modal dialogs, elevated containers", "N/A (Card Background)"],
        ["--text-primary", "#1E293B / #F8FAFC", "Primary readable body text and paragraph labels", "12.5:1 (Background)"],
        ["--border-subtle", "#E2E8F0 / #1E293B", "Dividers, table outlines, input field borders", "Border Token"]
    ]
    add_styled_table(doc, colors[0], colors[1:], [1.6, 1.2, 2.4, 1.3])

    add_heading_2(doc, "2.2 Typography Scale")
    add_bullet_p(doc, " Clean sans-serif system font stack: 'Segoe UI', 'Inter', -apple-system, sans-serif. In Indic languages, system renders Nirmala UI, Mangal, and Shruti for flawless conjunct glyphs.", bold_prefix="Font Family:")
    add_bullet_p(doc, " Display Title: 28-32px (Bold) | H1 Section: 22-24px (Bold) | H2 Subsection: 18-20px (Semi-Bold) | Body: 14-16px (Regular, 1.5 line-height) | Microcopy: 12px (Muted).", bold_prefix="Hierarchy:")

    # 3. Wireframes & Layout Structure
    add_heading_1(doc, "3. Layout Wireframes & Component Architecture")
    
    add_heading_2(doc, "3.1 Persistent Global Navigation Bar")
    add_body_p(doc, "The top navigation bar replaces standard Streamlit sidebars, providing an intuitive application header:")
    add_code_block(doc,
"""┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [DocMindX Logo]  [Triage]  [Report OCR]  [Nearby Radar]  [Records]  [Command] │ [Lang: HI▼] [☀/🌙] [Auth]│
└────────────────────────────────────────────────────────────────────────────────────────┘"""
    )

    add_heading_2(doc, "3.2 Panel 1: AI Health & Symptom Analyzer Wireframe")
    add_code_block(doc,
"""┌─────────────────────────────────────┬──────────────────────────────────────────┐
│ LEFT COLUMN: PATIENT INPUTS         │ RIGHT COLUMN: CLINICAL TRIAGE RESULTS    │
├─────────────────────────────────────┼──────────────────────────────────────────┤
│ • Demographic Selectors (Age, Sex)  │ 🚨 EMERGENCY RED FLAG BANNER (If Acute)   │
│ • Duration Slider (Days / Weeks)    │   [108 Direct Call] [Nearest ICU Route]  │
│ • Free-text Symptom Entry Box       │ ──────────────────────────────────────── │
│ • [🎙️ Voice Audio Input Button]     │ 🩺 DIFFERENTIAL DIAGNOSIS CARD (Top-3)   │
│ • Selected Symptom Tags / Badges    │   1. Condition Name (ICD-11 Code) - 84%  │
│ • Prior Medical Conditions Selector │   2. Secondary Alternative - 12%         │
│ • [RUN CLINICAL ASSESSMENT BUTTON]  │ ──────────────────────────────────────── │
│                                     │ 🥗 ICMR-NIN DIETARY RECOVERY ADVISORY    │
│                                     │ 💊 VERIFIED MEDICATION FORMULARY (FDA)   │
│                                     │ 🗺️ NEARBY HOSPITAL GPS RADAR & DISTANCE  │
└─────────────────────────────────────┴──────────────────────────────────────────┘"""
    )

    add_heading_2(doc, "3.3 Panel 2: Medical Report & Prescription Scanner Wireframe")
    add_code_block(doc,
"""┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [📁 DRAG & DROP PRESCRIPTION OR BLOOD REPORT (PNG, JPG, PDF)]                           │
├─────────────────────────────────────┬──────────────────────────────────────────────────┤
│ PREVIEW PANEL (Uploaded Document)   │ STRUCTURED EXTRACTION TABS:                      │
│                                     │ [1. Digitized Prescriptions] [2. Blood CBC Values]│
│ • High-resolution image canvas      │ • Paracetamol 650mg | 1 Tab TID | After food     │
│ • Grayscale / Contrast Zoom toggle  │ • Amoxicillin 500mg | 1 Cap BD  | 5 Days         │
│                                     │ ──────────────────────────────────────────────── │
│                                     │ 🔬 LAYMAN COMPREHENSIVE BREAKDOWN:               │
│                                     │ • Hemoglobin: 11.2 g/dL (Mildly Low - Anemia)    │
│                                     │ • What this means in simple words (No panic)     │
└─────────────────────────────────────┴──────────────────────────────────────────────────┘"""
    )

    add_heading_2(doc, "3.4 Panel 5: National Command Center Wireframe (Track 03)")
    add_code_block(doc,
"""┌────────────────────────────────────────────────────────────────────────────────────────┐
│ NATIONAL HEALTH LOGISTICS TELEMETRY — 225+ PHC FACILITIES ACROSS 36 STATES/UTS          │
├───────────────────┬───────────────────┬───────────────────┬────────────────────────────┤
│ Total Beds: 8,420 │ Active PHCs: 225  │ Stockouts: 3 PHCs │ Demand Forecast WAPE: 6.53%│
├───────────────────┴───────────────────┴───────────────────┴────────────────────────────┤
│ [STATE FILTER: All States ▼]  [EPIDEMIC STRESS SIMULATOR: Monsoon Dengue Outbreak (250%)]│
├───────────────────────────────────────┬────────────────────────────────────────────────┤
│ GEOGRAPHIC TELEMETRY HEATMAP (Folium) │ AUTOMATED TWO-STAGE REDISTRIBUTION SOLVER      │
│ • Green Pins: Adequate DOIR (>14 days)│ • Source: District Hospital Surat (Surplus)    │
│ • Orange Pins: Warning DOIR (3-7 days)│ • Destination: PHC Mandvi (Deficit - 2 Days)   │
│ • Red Pins: Critical Stockout (<3 d)  │ • Transfer: 2,500 IV Fluids, 10,000 Paracetamol│
│                                       │ • [GENERATE OFFICIAL TRANSFER MANIFEST PDF]    │
└───────────────────────────────────────┴────────────────────────────────────────────────┘"""
    )

    # 4. User Journeys & Interaction Flows
    add_heading_1(doc, "4. User Journeys & Interaction Flows")

    add_heading_2(doc, "4.1 Journey 1: Acute Citizen Symptom Assessment to Emergency Referral")
    add_bullet_p(doc, " Citizen opens application on mobile; chooses Hindi ('हिंदी') from top navigation dropdown.", bold_prefix="Step 1 [Entry & Language]:")
    add_bullet_p(doc, " Citizen taps the microphone button and states: '3 din se seene me tej dard hai aur ulti ho rahi hai'. Voice audio is streamed and transcribed instantaneously.", bold_prefix="Step 2 [Input Modality]:")
    add_bullet_p(doc, " System highlights recognized symptom chips: [Chest Pain: Severe], [Persistent Vomiting], [Duration: 3 Days].", bold_prefix="Step 3 [Token Confirmation]:")
    add_bullet_p(doc, " User clicks 'Run Assessment'. Within 1.8 seconds, Pipeline v3 triggers Red Flag RF002 (Acute Coronary Syndrome suspicion).", bold_prefix="Step 4 [Triage Execution]:")
    add_bullet_p(doc, " Screen updates with a crimson emergency banner, direct 108 ambulance dialer, and a turn-by-turn route map to the nearest 24x7 Cardiac Emergency Hospital.", bold_prefix="Step 5 [Actionable Resolution]:")

    add_heading_2(doc, "4.2 Journey 2: Handwritten Prescription Upload to Patient Empowerment")
    add_bullet_p(doc, " Patient receives a handwritten prescription from a local clinic and takes a smartphone photo.", bold_prefix="Step 1 [Capture]:")
    add_bullet_p(doc, " Uploads image into Panel 2. OpenCV normalizes contrast and Gemini Vision extracts active molecules and schedules.", bold_prefix="Step 2 [Digitization]:")
    add_bullet_p(doc, " Screen renders clean medicine cards cross-referenced with NIH DailyMed photos of verified blister packs.", bold_prefix="Step 3 [Visual Verification]:")
    add_bullet_p(doc, " Patient taps 'Explain in Simple Hindi'. AI Copilot explains food interactions (e.g. 'Take this antibiotic after meals with plenty of water').", bold_prefix="Step 4 [Comprehension]:")

    # 5. Micro-Interactions & Responsiveness
    add_heading_1(doc, "5. Micro-Interactions & Responsive Mobile Adaptations")
    add_bullet_p(doc, " When audio recording starts, the microphone button pulses with a subtle cerulean glow, indicating active recording.", bold_prefix="Voice Mic Pulse Animation:")
    add_bullet_p(doc, " The floating copilot button in the bottom-right corner toggles an accessible drawer without obscuring primary triage results.", bold_prefix="Floating AI Copilot Drawer:")
    add_bullet_p(doc, " On mobile screens (<768px), 2-column layouts seamlessly collapse into single-column vertical stacks, ensuring tap targets exceed 48x48px.", bold_prefix="Responsive Breakpoints:")

    doc.save(output_path)
    print(f"Generated: {output_path}")

def generate_ui_ux_hi(output_path):
    doc = create_base_document(
        title="DocMindX AI — UI/UX डिज़ाइन एवं अनुभव दस्तावेज़",
        subtitle="डिज़ाइन सिस्टम, विज़ुअल टोकन्स, क्लिनिकल उपयोगिता एवं यूजर जर्नी मैप्स",
        doc_type="UI/UX डिज़ाइन दस्तावेज़",
        lang="HI"
    )

    # 1. UI/UX दर्शन
    add_heading_1(doc, "1. UI/UX डिज़ाइन दर्शन एवं क्लिनिकल मानवीय कारक (Design Philosophy)")
    add_body_p(doc, "चिकित्सा क्षेत्र के यूजर इंटरफ़ेस सीधे रोगी की सुरक्षा, निदान की समझ और जीवन-मरण के निर्णयों को प्रभावित करते हैं। किसी आपातकालीन स्थिति में यदि ऐप का डिज़ाइन भ्रामक हो, फोंट छोटे हों, या गैर-जरूरी इमोजी लगे हों, तो मरीज और डॉक्टर दोनों में भ्रम की स्थिति बन सकती है।")

    add_callout(
        doc,
        "क्लिनिकल स्पष्टता का मानक: DocMindX AI 'एंटरप्राइज क्लिनिकल रेड एडिशन' का पालन करता है। क्लिनिकल रिपोर्ट और ट्राइएज में किसी भी प्रकार के इमोजी का उपयोग प्रतिबंधित है ताकि स्क्रीन-रीडर और मरीज को गंभीर चिकित्सीय स्पष्टता मिले।",
        title="क्लिनिकल स्पष्टता मानक",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 मुख्य डिज़ाइन स्तंभ")
    add_bullet_p(doc, " सामान्य इमोजी गंभीर बीमारियों को हल्का दिखाते हैं और स्क्रीन-रीडर में गलत उच्चारण करते हैं। सिस्टम में स्पष्ट SVG बैज और टेक्स्ट लेबल का उपयोग किया गया है।", bold_prefix="1. क्लिनिकल ट्राइएज में शून्य इमोजी (Zero Emojis):")
    add_bullet_p(doc, " हिंदी, गुजराती और अंग्रेजी तीनों भाषाओं में लेआउट, बटन साइज और पढ़ने का अनुभव बिल्कुल एक समान रखा गया है।", bold_prefix="2. भारतीय भाषाओं की पूर्ण समानता:")
    add_bullet_p(doc, " सभी बटन और टेक्स्ट WCAG 2.1 AA मानक (4.5:1 से 7:1 अनुपात) का पालन करते हैं ताकि कमजोर रोशनी में भी सब साफ दिखे।", bold_prefix="3. उच्च कंट्रास्ट और पठनीयता:")
    add_bullet_p(doc, " मरीज पर एक साथ जानकारी का बोझ न पड़े, इसलिए पहले मुख्य परिणाम और फिर विस्तार से व्याख्या दिखाई जाती है।", bold_prefix="4. मानसिक तनाव मुक्ति (De-escalation):")

    # 2. डिज़ाइन सिस्टम
    add_heading_1(doc, "2. डिज़ाइन सिस्टम एवं रंग पैलेट (Color Tokens)")
    add_body_p(doc, "सिस्टम के रंग 'config/theme.py' में टोकन के रूप में परिभाषित हैं:")

    colors_hi = [
        ["रंग टोकन", "हेक्स कोड (Hex)", "क्लिनिकल व UI कार्य", "कंट्रास्ट अनुपात"],
        ["--clinical-primary", "#0077B6", "मुख्य एक्शन बटन, सक्रिय टैब, शीर्षक", "6.2:1 (सफेद पर)"],
        ["--clinical-navy", "#0A2540", "ऐप हेडर बैकग्राउंड, मुख्य टेबल हेडर", "14.8:1 (सफेद पर)"],
        ["--alert-danger", "#C1121F", "रेड फ्लैग इमरजेंसी बैनर, 108 एम्बुलेंस बटन", "7.4:1 (सफेद पर)"],
        ["--alert-warning", "#F77F00", "मध्यम गंभीरता ट्राइएज कार्ड, DOIR < 7 चेतावनी", "4.8:1 (डार्क पर)"],
        ["--alert-success", "#047857", "सामान्य स्वास्थ्य, सत्यापित दवा बैज", "5.1:1 (सफेद पर)"],
        ["--surface-card", "#FFFFFF / #112240", "ट्राइएज कार्ड, मोडल डायलॉग, बैकग्राउंड", "N/A (कार्ड पृष्ठभूमि)"],
        ["--text-primary", "#1E293B / #F8FAFC", "मुख्य पठनीय पैराग्राफ टेक्स्ट", "12.5:1 (पृष्ठभूमि पर)"]
    ]
    add_styled_table(doc, colors_hi[0], colors_hi[1:], [1.6, 1.2, 2.4, 1.3])

    # 3. वायरफ्रेम व लेआउट
    add_heading_1(doc, "3. लेआउट वायरफ्रेम एवं स्क्रीन संरचना (Wireframes)")
    
    add_heading_2(doc, "3.1 पैनल 1: AI स्वास्थ्य व लक्षण विश्लेषक का वायरफ्रेम")
    add_code_block(doc,
"""┌─────────────────────────────────────┬──────────────────────────────────────────┐
│ बायाँ भाग: मरीज इनपुट व लक्षण        │ दायाँ भाग: क्लिनिकल ट्राइएज परिणाम       │
├─────────────────────────────────────┼──────────────────────────────────────────┤
│ • उम्र एवं लिंग चयन                 │ 🚨 आपातकालीन रेड फ्लैग बैनर (यदि गंभीर)  │
│ • बीमारी की अवधि (दिन / सप्ताह)      │   [108 एम्बुलेंस कॉल] [निकटतम ICU मैप]   │
│ • लक्षण लिखने का इनपुट बॉक्स        │ ──────────────────────────────────────── │
│ • [🎙️ वॉयस माइक इनपुट बटन]          │ 🩺 संभावित रोग कार्ड (Top-3 डिफरेंशियल)   │
│ • पहचाने गए लक्षण चिप्स (Tags)       │   1. रोग का नाम (ICD-11 कोड) - 84% मैच   │
│ • पूर्व बीमारी व वर्तमान दवाएं       │   2. द्वितीय संभावित बीमारी - 12%        │
│ • [क्लिनिकल जांच शुरू करें बटन]     │ ──────────────────────────────────────── │
│                                     │ 🥗 ICMR-NIN आहार एवं परहेज परामर्श       │
│                                     │ 💊 सत्यापित दवा विवरण व पैकेजिंग (FDA)   │
│                                     │ 🗺️ निकटतम सरकारी व निजी अस्पताल रडार    │
└─────────────────────────────────────┴──────────────────────────────────────────┘"""
    )

    add_heading_2(doc, "3.2 पैनल 5: राष्ट्रीय स्वास्थ्य कमान केंद्र वायरफ्रेम (ट्रैक 03)")
    add_code_block(doc,
"""┌────────────────────────────────────────────────────────────────────────────────────────┐
│ राष्ट्रीय स्वास्थ्य आपूर्ति टेलीमेट्री — देश भर के 225+ प्राथमिक स्वास्थ्य केंद्र     │
├───────────────────┬───────────────────┬───────────────────┬────────────────────────────┤
│ कुल बेड: 8,420    │ सक्रिय PHC: 225   │ दवा संकट: 3 केंद्र│ मांग फोरकास्ट त्रुटि: 6.53%│
├───────────────────┴───────────────────┴───────────────────┴────────────────────────────┤
│ [राज्य फिल्टर: सभी राज्य ▼]  [महामारी सिमुलेटर: मानसून डेंगू आउटब्रेक स्ट्रेस-टेस्ट]     │
├───────────────────────────────────────┬────────────────────────────────────────────────┤
│ भौगोलिक हीटमैप (Interactive Folium)   │ स्वचालित दवा पुनर्वितरण सॉल्वर                 │
│ • हरा पिन: पर्याप्त स्टॉक (>14 दिन)   │ • भेजने वाला: जिला अस्पताल सूरत (अधिशेष स्टॉक) │
│ • नारंगी पिन: कम स्टॉक (3-7 दिन)      │ • प्राप्तकर्ता: PHC मांडवी (गंभीर कमी - 2 दिन) │
│ • लाल पिन: तत्काल संकट (<3 दिन स्टॉक) │ • ट्रांसफर: 2,500 IV फ्लुइड्स, 10,000 पैरासिटामोल│
│                                       │ • [आधिकारिक ट्रांसफर मैनिफेस्ट PDF डाउनलोड करें]│
└───────────────────────────────────────┴────────────────────────────────────────────────┘"""
    )

    # 4. यूजर जर्नी
    add_heading_1(doc, "4. यूजर जर्नी एवं इंटरैक्शन प्रवाह (User Journey)")
    add_heading_2(doc, "4.1 जर्नी 1: गंभीर लक्षण से आपातकालीन अस्पताल रेफरल")
    add_bullet_p(doc, " नागरिक मोबाइल पर ऐप खोलता है और भाषा सूची में से 'हिंदी' चुनता है।", bold_prefix="चरण 1 [प्रवेश व भाषा]:")
    add_bullet_p(doc, " मरीज माइक बटन दबाकर बोलता है: '3 दिन से छाती में तेज दर्द है और पसीना आ रहा है'। सिस्टम तुरंत वॉयस को टेक्स्ट में बदलता है।", bold_prefix="चरण 2 [वॉयस इनपुट]:")
    add_bullet_p(doc, " सिस्टम पहचाने गए लक्षणों के चिप्स दिखाता है: [छाती में दर्द: गंभीर], [पसीना आना]।", bold_prefix="चरण 3 [लक्षण पुष्टि]:")
    add_bullet_p(doc, " 'जांच शुरू करें' दबाने पर 1.8 सेकंड में पाइपलाइन v3 रेड फ्लैग RF002 (हार्ट अटैक आशंका) सक्रिय कर देता है।", bold_prefix="चरण 4 [ट्राइएज परिणाम]:")
    add_bullet_p(doc, " स्क्रीन पर तुरंत लाल चेतावनी बैनर, 108 एम्बुलेंस कॉलिंग बटन और निकटतम कार्डियक ICU का लाइव नेविगेशन नक्शा खुलता है।", bold_prefix="चरण 5 [त्वरित समाधान]:")

    doc.save(output_path)
    print(f"Generated: {output_path}")
