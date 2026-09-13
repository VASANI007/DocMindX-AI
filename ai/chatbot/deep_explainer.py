"""
    Deep Clinical Explanation & Assessment Follow-Up Q&A Engine
Powered by Gemini & Groq AI. Provides in-depth medical rationale, drug synergy analysis,
and interactive question-answering tailored to the patient's exact assessment results.
"""
import json

import requests

from config.settings import GEMINI_API_KEY, GROQ_API_KEY


def generate_deep_explanation(
    symptoms: list,
    user_context: dict,
    top_condition: str,
    ranked_conditions: list,
    medicines: list,
    yoga_recs: list,
    lang: str = "en"
) -> str:
    """
    Generates a structured, comprehensive, patient-friendly clinical deep explanation.
    """
    lang_name = "English" if lang == "en" else "Hindi (हिंदी)" if lang == "hi" else "Gujarati (ગુજરાતી)"
    
    med_names = [m.get("name", "") for m in (medicines or []) if isinstance(m, dict)]
    yoga_names = [y.get("name", "") for y in (yoga_recs or []) if isinstance(y, dict)]
    cond_names = [c.get("name", "") for c in (ranked_conditions or []) if isinstance(c, dict)]

    prompt = f"""You are DocMindX AI — Senior Clinical Healthcare & Diagnostic Consultant.
    Provide an exhaustive, transparent, and comforting Clinical Deep Explanation of this patient's assessment findings.

PATIENT PROFILE:
- Reported Symptoms: {', '.join(symptoms) if symptoms else 'General Symptoms'}
- Duration: {user_context.get('duration', '1 - 3 Days')}
- Severity: {user_context.get('severity', 'Moderate')}
- Age Group: {user_context.get('age', 'Adult')}, Gender: {user_context.get('gender', 'Male')}
- Existing Medical Conditions: {', '.join(user_context.get('conditions', ['None']))}
- Primary Assessed Condition: {top_condition}
- Ranked Conditions Evaluated: {', '.join(cond_names[:3])}
- Recommended Medications: {', '.join(med_names)}
- Supportive Yoga & Mobility: {', '.join(yoga_names)}

INSTRUCTIONS:
Write a comprehensive, beautifully structured clinical explanation strictly in {lang_name}. Do NOT use emojis.
Include the following clear sections with Markdown headings:

### 1. Diagnostic Rationale (Why These Conditions Were Identified)
Explain in simple, empathetic terms how the specific combination of symptoms ({', '.join(symptoms)}) aligns with {top_condition} and related diagnostic pathways.

### 2. Medication Strategy & Biochemical Synergy
Explain why each prescribed medicine was chosen and how they work together as a team (e.g. pain relief + stomach protection + rehydration). Mention why taking them at the right time (before vs after food) is vital.

### 3. Holistic Recovery (Yoga, Hydration & Dietary Science)
Explain the physiological benefits of the recommended restorative yoga poses and dietary guidelines in speeding up natural cellular recovery.

### 4. Red Flags & Urgent Care Advice
Clear clinical advice on when symptoms require immediate in-person medical evaluation.

Write in a reassuring, professional, and clear tone in {lang_name}."""

    # Deep clinical explanations use Gemini first.
    if GEMINI_API_KEY:
        for model in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
                }
                headers = {"Content-Type": "application/json"}
                res = requests.post(url, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    candidates = res.json().get("candidates", [])
                    if candidates:
                        txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if txt and len(txt.strip()) > 100:
                            return txt.strip()
            except Exception as e:
                print(f"Deep explanation Gemini notice: {e}")

    # Groq remains only as a fallback for deep explanation outages.
    if GROQ_API_KEY:
        for model in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": f"You are DocMindX AI. Write clear clinical explanations in {lang_name}. Do not use emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
                if res.status_code == 200:
                    txt = res.json()["choices"][0]["message"]["content"]
                    if txt and len(txt.strip()) > 100:
                        return txt.strip()
            except Exception as e:
                print(f"Deep explanation Groq fallback notice: {e}")

    # Local fallback (Clean, no emojis)
    if lang == "hi":
        return f"""### 1. यह स्वास्थ्य स्थिति क्यों पाई गई
आपके द्वारा बताए गए लक्षण (**{', '.join(symptoms)}**) मुख्य रूप से **{top_condition}** के पैटर्न से मेल खाते हैं। इस स्थिति में शरीर की रोग प्रतिरोधक प्रणाली सक्रिय हो जाती है जिससे सिरदर्द, बदन दर्द या थकावट महसूस हो सकती है।

### 2. दवाओं का संयोजन और प्रभाव
- बुखार और दर्द निवारक: शरीर के तापमान और मांसपेशियों के दर्द को नियंत्रित करने के लिए।
- पेट की सुरक्षा (Gastric Shield): एसिडिटी और पेट में जलन से बचाव के लिए इसे खाली पेट लेने की सलाह दी गई है।
- हाइड्रेशन (ORS): शरीर में तरल और आवश्यक इलेक्ट्रोलाइट्स की भरपाई के लिए।

### 3. योग और आहार द्वारा स्वास्थ्य लाभ
विश्रामदायक योगासन मांसपेशियों के तनाव को कम करते हैं और रक्त प्रवाह को बढ़ाते हैं। हल्का और सुपाच्य भोजन (जैसे खिचड़ी, दलिया, सूप) जल्दी ठीक होने में मदद करता है।

### 4. डॉक्टर से परामर्श
यदि 3 दिन से अधिक तेज बुखार बना रहे या सांस लेने में कठिनाई हो, तो तुरंत चिकित्सक से परामर्श लें।"""
    elif lang == "gu":
        return f"""### 1. આ સ્થિતિનું નિદાન કેમ થયું
તમે જણાવેલા લક્ષણો (**{', '.join(symptoms)}**) મુખ્યત્વે **{top_condition}** સાથે મેળ ખાય છે.

### 2. દવાઓનું આયોજન
- તાવ અને દુખાવાની દવા: શરીરનું તાપમાન ઘટાડવા અને દુખાવો ઓછો કરવા માટે.
- પેટની સુરક્ષા: એસિડિટીથી બચવા માટે ખાલી પેટે લેવી.
- હાઇડ્રેશન (ORS): શરીરમાં પાણી અને ક્ષારોનું સંતુલન જાળવવા.

### 3. યોગ અને આહાર
યોગાસનો સ્નાયુઓનો તણાવ દૂર કરે છે અને પૌષ્ટિક આહાર ઝડપી સ્વસ્થતા આપે છે."""
    else:
        return f"""### 1. Clinical Assessment Rationale
Your reported symptoms (**{', '.join(symptoms)}**) closely correspond to the clinical presentation of **{top_condition}**. The body's inflammatory response to this condition creates localized fatigue, discomfort, and physiological strain.

### 2. Medication Teamwork & Synergy
- Symptom Relief & Antipyretic: Directly addresses elevated temperature and acute pain.
- Gastric Protection (PPI): Protects the gastric lining against acidity when taking other medications.
- Cellular Rehydration (ORS): Replenishes vital electrolytes (Sodium, Potassium) to combat dizziness and dehydration.

### 3. Restorative Yoga & Dietary Protocol
Gentle mobility postures relieve muscle stiffness and improve oxygen circulation, while nutrient-dense foods (warm soups, light meals) accelerate healing without burdening the digestive tract.

### 4. Red Flags
Seek immediate medical consultation if symptoms worsen, high fever persists beyond 3 days, or breathing difficulty occurs."""


def answer_assessment_question(
    user_question: str,
    symptoms: list,
    user_context: dict,
    top_condition: str,
    medicines: list,
    lang: str = "en"
) -> str:
    """
    Answers any follow-up question regarding the patient's assessment and medications.
    """
    lang_name = "English" if lang == "en" else "Hindi (हिंदी)" if lang == "hi" else "Gujarati (ગુજરાતી)"
    med_summary = ", ".join([f"{m.get('name')} ({m.get('food_timing', 'After Food')})"
        for m in (medicines or []) if isinstance(m, dict)])

    prompt = f"""You are DocMindX AI Clinical Consultation Assistant.
    Answer the following patient question regarding their current health assessment and medications.

PATIENT CONTEXT:
- Symptoms: {', '.join(symptoms)}
- Assessed Condition: {top_condition}
- Prescribed Medicines: {med_summary}
- Demographics: Age {user_context.get('age', 'Adult')}, Gender {user_context.get('gender', 'Male')}

PATIENT'S QUESTION:
"{user_question}"

INSTRUCTIONS:
1. Provide a direct, compassionate, scientifically accurate answer strictly in {lang_name}.
2. Explain clearly in 2-4 concise paragraphs with practical advice.
3. If they ask about taking medicines together, food timings, side effects, or recovery, provide exact clinical guidance.
4. Conclude with a warm safety reminder."""

    if GEMINI_API_KEY:
        for model in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                if res.status_code == 200:
                    candidates = res.json().get("candidates", [])
                    if candidates:
                        txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if txt and len(txt.strip()) > 20:
                            return txt.strip()
            except Exception as e:
                print(f"Q&A Gemini notice: {e}")

    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"You are DocMindX AI. Answer patient questions clinically in {lang_name}."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Q&A Groq notice: {e}")

    return f"Based on your assessment for {top_condition}, please follow the prescribed dosage and food timing instructions carefully. If symptoms persist or cause discomfort, consult a doctor immediately."


def generate_medical_report_comprehensive_breakdown(
    report_type: str,
    doc_text: str,
    findings: list = None,
    age_group: str = "Adult",
    gender: str = "Male",
    lang: str = "en"
) -> str:
    """
    Generates an automated, highly detailed, patient-friendly clinical interpretation
    for ANY uploaded medical report (Blood, Prescription, or Radiology).
    Directly explains:
    - What each detected parameter/medicine is in plain language
    - What happens to the body when it is low or high
    - Actionable diet & lifestyle changes (foods to eat, foods to avoid)
    - Precautions & Red flags
    Emits NO emojis.
    """
    lang_name = "English" if lang == "en" else "Hindi (हिंदी)" if lang == "hi" else "Gujarati (ગુજરાતી)"
    findings = findings or []

    # Summarize findings for prompt
    findings_lines = []
    for f in findings[:15]:
        if isinstance(f, dict):
            name = f.get("test_name") or f.get("extracted_name") or f.get("finding_name") or f.get("english_name", "")
            val = f.get("value", "")
            unit = f.get("unit", "")
            status = f.get("status") or f.get("severity", "")
            ref = f.get("reference_range", "")
            freq = f.get("frequency", "")
            timing = f.get("timing", "")
            if val:
                findings_lines.append(f"- {name}: {val} {unit} (Reference: {ref}) [{status}]")
            elif freq:
                findings_lines.append(f"- {name} (Dose/Freq: {freq}, Timing: {timing})")
            else:
                findings_lines.append(f"- {name} [{status}]")

    findings_summary = "\n".join(findings_lines) if findings_lines else "General findings extracted from report."

    prompt = f"""You are DocMindX AI — Senior Clinical Pathologist & Patient Health Advisor.
Analyze this medical document and produce an exhaustive, patient-friendly clinical guide.

REPORT TYPE: {report_type}
PATIENT DEMOGRAPHICS: Age Group: {age_group}, Biological Gender: {gender}

EXTRACTED PARAMETERS & FINDINGS:
{findings_summary}

RAW EXTRACTED TEXT EXCERPT:
\"\"\"{doc_text[:1200]}\"\"\"

CRITICAL INSTRUCTIONS:
1. Write strictly in {lang_name}.
2. Do NOT use any emojis.
3. Provide deep, clear, empathetic explanation so the patient fully understands their health without medical jargon.
4. Structure the response into these 5 clear markdown sections:

### 1. रिपोर्ट का मुख्य सारांश (Key Findings Overview)
Summarize which parameters are within safe normal limits and which ones require attention or are abnormal.

### 2. यह पैरामीटर / टेस्ट क्या है और शरीर में इसका क्या कार्य है? (Biological Function in Plain Language)
Explain in simple, everyday words what each key test or medicine actually is (e.g. what Hemoglobin is, what Creatinine is, what WBC is, etc.).

### 3. शरीर पर असर और इसके लक्षण (Impact on the Body & Symptoms)
Explain what happens to the patient's body, energy, and organs when these values are abnormal (e.g. fatigue, breathlessness, dizziness, weakness, fluid retention, etc.).

### 4. इसे सुधारने के लिए क्या खाएं और क्या न खाएं? (Actionable Diet & Nutrition Plan)
Provide specific, actionable dietary guidance:
- Exactly which foods to consume to improve this condition (e.g. iron-rich items, Vitamin C, leafy greens, proteins, hydration).
- Exactly which foods or habits to avoid (e.g. tea/coffee immediately after meals, junk food, high sodium, etc.).

### 5. सावधानियां व डॉक्टर से परामर्श (Medical Precautions & Red Flags)
Explain next steps, which specialist physician to consult, and highlight danger signs (Red Flags) where urgent medical attention is required."""

    # 1. Gemini AI (Primary)
    if GEMINI_API_KEY:
        for model in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1800}
                }
                headers = {"Content-Type": "application/json"}
                res = requests.post(url, json=payload, headers=headers, timeout=12)
                if res.status_code == 200:
                    candidates = res.json().get("candidates", [])
                    if candidates:
                        txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if txt and len(txt.strip()) > 80:
                            return txt.strip()
            except Exception as e:
                print(f"Report breakdown Gemini notice ({model}): {e}")

    # 2. Groq AI (Fallback)
    if GROQ_API_KEY:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": f"You are DocMindX AI Senior Clinical Pathologist. Write comprehensive patient guides in {lang_name}. Do NOT use emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1600
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=10)
                if res.status_code == 200:
                    txt = res.json()["choices"][0]["message"]["content"]
                    if txt and len(txt.strip()) > 80:
                        return txt.strip()
            except Exception as e:
                print(f"Report breakdown Groq notice ({model}): {e}")

    # 3. Local Rule-Based Fallback
    if lang == "hi":
        return f"""### 1. रिपोर्ट का मुख्य सारांश
आपकी इस रिपोर्ट में {len(findings)} मुख्य पैरामीटर्स का विश्लेषण किया गया है। कुछ मान सामान्य सीमा से बाहर हो सकते हैं जिन पर ध्यान देने की आवश्यकता है।

### 2. यह पैरामीटर क्या है और शरीर में इसका क्या कार्य है?
रक्त परीक्षण के घटक (जैसे हीमोग्लोबिन, श्वेत रक्त कोशिकाएं आदि) शरीर के विभिन्न अंगों के सुचारू संचालन, ऑक्सीजन परिवहन और रोग प्रतिरोधक क्षमता को बनाए रखने का काम करते हैं।

### 3. शरीर पर असर और इसके लक्षण
पैरामीटर्स में असंतुलन होने पर सामान्य थकान, ऊर्जा में कमी, हल्का सिरदर्द या कमजोरी जैसे लक्षण महसूस हो सकते हैं।

### 4. आहार व जीवनशैली सुधार
- पोषक तत्वों से भरपूर ताजे फल, हरी पत्तेदार सब्जियां, दालें और पर्याप्त पानी का सेवन करें।
- भोजन के तुरंत बाद चाय या कॉफी पीने से बचें ताकि पोषक तत्वों का अवशोषण ठीक से हो सके।

### 5. चिकित्सीय सलाह
इस रिपोर्ट के विस्तृत विश्लेषण और उचित उपचार के लिए अपने डॉक्टर से अवश्य परामर्श लें।"""
    elif lang == "gu":
        return f"""### 1. રિપોર્ટનો મુખ્ય સારાંશ
તમારા રિપોર્ટમાં {len(findings)} પેરામીટર્સ તપાસવામાં આવ્યા છે.

### 2. આ પરિણામોનું મહત્વ
શરીરમાં જરૂરી પોષક તત્વો અને રક્તકણોનું યોગ્ય સ્તર સ્વાસ્થ્ય માટે અનિવાર્ય છે.

### 3. આહાર અને કાળજી
લીલા શાકભાજી, તાજા ફળો અને પૂરતું પાણી લેવું હિતાવહ છે. ચા-કોફીનું સેવન ઘટાડો.

### 4. ડૉક્ટરની સલાહ
ચોક્કસ નિદાન માટે તમારા ફિઝિશિયનનો સંપર્ક કરવો જરૂરી છે."""
    else:
        return f"""### 1. Key Findings Overview
Evaluated {len(findings)} clinical parameters from your report. Certain values require clinical attention.

### 2. Biological Function
Blood and diagnostic indicators measure organ health, oxygen transport, metabolic balance, and immune activity.

### 3. Impact on the Body
Out-of-range parameters can manifest as fatigue, reduced physical stamina, lightheadedness, or localized discomfort.

### 4. Nutrition & Recovery
- Consume a balanced, micronutrient-dense diet with leafy greens, fresh seasonal fruits, lean protein, and optimal hydration.
- Avoid consuming tea or coffee immediately after meals to ensure optimal nutrient absorption.

### 5. Clinical Next Steps
Discuss these findings with your physician for confirmatory correlation and targeted therapy."""
