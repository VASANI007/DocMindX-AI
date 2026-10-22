"""
    Deep Clinical Explanation & Assessment Follow-Up Q&A Engine
Powered by Gemini & Groq AI. Provides in-depth medical rationale, drug synergy analysis,
and interactive question-answering tailored to the patient's exact assessment results.
"""
import json
import re
import requests

from config.settings import GEMINI_API_KEY, GROQ_API_KEY, gemini_pool, GROQ_MODELS, DEFAULT_GEMINI_MODELS
from config.language import normalize_lang_code, is_valid_script_for_language


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
    lang = normalize_lang_code(lang)
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

    # Deep clinical explanations use Gemini first (Multi-Key Failover Pool).
    if gemini_pool.get_active_keys():
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
        }
        res_data, _, _ = gemini_pool.execute_with_failover(
            payload=payload,
            models=["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"],
            timeout=10
        )
        if res_data:
            candidates = res_data.get("candidates", [])
            if candidates:
                txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if txt and len(txt.strip()) > 100 and is_valid_script_for_language(txt, lang):
                    return txt.strip()

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
                    if txt and len(txt.strip()) > 100 and is_valid_script_for_language(txt, lang):
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
    lang = normalize_lang_code(lang)
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

    if gemini_pool.get_active_keys():
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
        }
        res_data, _, _ = gemini_pool.execute_with_failover(
            payload=payload,
            models=["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"],
            timeout=10
        )
        if res_data:
            candidates = res_data.get("candidates", [])
            if candidates:
                txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if txt and len(txt.strip()) > 20 and is_valid_script_for_language(txt, lang):
                    return txt.strip()

    if GROQ_API_KEY:
        for groq_model in GROQ_MODELS:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": f"You are DocMindX AI. Answer patient questions clinically in {lang_name}."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1000
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
                if res.status_code == 200:
                    ans = res.json()["choices"][0]["message"]["content"].strip()
                    if ans and is_valid_script_for_language(ans, lang):
                        return ans
            except Exception as e:
                print(f"Q&A Groq notice ({groq_model}): {e}")

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
    Emits NO emojis. Guaranteed to return in the selected language (en, hi, or gu).
    """
    findings = findings or []
    lang = normalize_lang_code(lang)

    if lang == "hi":
        lang_name = "Hindi (हिंदी)"
        lang_instruction = "Write 100% strictly in natural, patient-friendly Hindi (हिंदी). All headings, explanations, dietary advice, and cautions must be in Hindi. Do NOT write in English or Gujarati."
        sec_1 = """### 1. रिपोर्ट का मुख्य सारांश (Key Findings Overview)
मरीज के लिए एक स्पष्ट और समझने योग्य परिचयात्मक सारांश पैराग्राफ लिखें जिसमें बीमारी या परीक्षण का अवलोकन हो।
इसके बाद ठीक इसी प्रारूप में दो संरचित उप-खंड अनिवार्य रूप से प्रदान करें:
सामान्य पैरामीटर (Normal Parameters):
- सामान्य सीमा के सभी टेस्ट मान या सुरक्षित चिकित्सीय खुराक के अनुसार निर्धारित दवाओं का बिंदुवार विवरण।
असामान्य पैरामीटर (Abnormal Parameters):
- असामान्य मान या दवाओं से जुड़ी विशेष सावधानियां, संभावित दुष्प्रभाव, एलर्जी और ध्यान देने योग्य बातें।"""

        sec_2 = """### 2. यह पैरामीटर / टेस्ट क्या है और शरीर में इसका क्या कार्य है? (Biological Function in Plain Language)
एक संक्षिप्त परिचयात्मक वाक्य दें।
इसके बाद रिपोर्ट के प्रत्येक मुख्य टेस्ट या निर्धारित दवा के लिए (कम से कम 3 से 7 बिंदु):
- **[दवा या टेस्ट का नाम]:** [1-2 सरल वाक्यों में गहराई से समझाएं कि यह शरीर में क्या जैविक कार्य करती है और इसका क्या लाभ है।]"""

        sec_3 = """### 3. शरीर पर असर और इसके लक्षण (Impact on the Body & Symptoms)
गहराई से समझाएं कि इन टेस्ट मानों, बीमारी या दवाओं का मरीज के शरीर, ऊर्जा, मांसपेशियों और अंगों पर क्या प्रभाव पड़ता है:
- **[शारीरिक प्रभाव / लक्षण क्षेत्र]:** [विस्तृत विवरण जैसे दर्द, सुन्नपन, थकान, जोड़ों की जकड़न, सूजन, ऊर्जा स्तर या उपचार द्वारा सुधार की प्रक्रिया।]"""

        sec_4 = """### 4. इसे सुधारने के लिए क्या खाएं और क्या न खाएं? (Actionable Diet & Nutrition Plan)
मरीज के लिए एक विस्तृत और व्यावहारिक आहार मार्गदर्शन योजना दें:
क्या खाएं (Foods to Consume):
- **[पोषक तत्व / खाद्य वर्ग]:** [जैसे हरी पत्तेदार सब्जियां, साबुत अनाज, मेवे, बीज, फल, विटामिन युक्त आहार, पर्याप्त पानी और ये शरीर की रिकवरी में कैसे मदद करते हैं।]
क्या न खाएं (Foods to Avoid):
- **[परहेज योग्य वस्तुएं व आदतें]:** [जैसे अत्यधिक तला-भुना, प्रोसेस्ड व जंक फूड, भोजन के तुरंत बाद चाय/कॉफी, अतिरिक्त नमक/चीनी, और इनसे बचने का वैज्ञानिक कारण।]"""

        sec_5 = """### 5. सावधानियां व डॉक्टर से परामर्श (Medical Precautions & Red Flags)
मरीज की सुरक्षा और सही देखभाल के लिए महत्वपूर्ण निर्देश:
अगले कदम (Next Steps):
- [स्पष्ट बिंदु: किस विशेषज्ञ डॉक्टर (जैसे हड्डी रोग विशेषज्ञ, फिजिशियन, न्यूरोलॉजिस्ट) से फॉलो-अप लें, दवा का नियमित समय पर सेवन, और आवश्यक परीक्षण।]
खतरे के लक्षण (Red Flags):
- [गंभीर आपातकालीन खतरे के लक्षण जिन पर मरीज को तुरंत अस्पताल या इमरजेंसी विभाग में जाना चाहिए (जैसे अंगों में अचानक कमजोरी, अनियंत्रित सुन्नपन, सीने में तेज दर्द, सांस लेने में तकलीफ आदि)।]"""

    elif lang == "gu":
        lang_name = "Gujarati (ગુજરાતી)"
        lang_instruction = "Write 100% strictly in natural, patient-friendly Gujarati (ગુજરાતી). All headings, explanations, dietary advice, and cautions must be in Gujarati. Do NOT write in English or Hindi."
        sec_1 = """### 1. રિપોર્ટનો મુખ્ય સારાંશ (Key Findings Overview)
દર્દી માટે સ્પષ્ટ અને સરળ પ્રારંભિક સારાંશ પેરાગ્રાફ આપો જેમાં આ રિપોર્ટનું મૂલ્યાંકન હોય.
ત્યારબાદ બરાબર આ જ ફોર્મેટમાં બે પેટા-વિભાગો આપો:
સામાન્ય પરિણામો (Normal Parameters):
- સામાન્ય મર્યાદામાં રહેલા તમામ ટેસ્ટ પરિણામો અથવા સલામત સ્ટાન્ડર્ડ ડોઝ ધરાવતી દવાઓનું મુદ્દાસર વર્ણન.
અસામાન્ય પરિણામો (Abnormal Parameters):
- સામાન્યથી અલગ પરિણામો અથવા દવાઓ સંબંધિત સાવચેતીઓ, સંભવિત આડઅસરો અને ધ્યાન રાખવા જેવી બાબતો."""

        sec_2 = """### 2. આ પરિણામોનું મહત્વ અને શરીર પર અસર (Biological Function in Plain Language)
એક પ્રારંભિક વાક્ય આપો.
ત્યારબાદ દરેક મુખ્ય ટેસ્ટ અથવા નિર્ધારિત દવા માટે (ઓછામાં ઓછા 3 થી 7 મુદ્દા):
- **[દવા અથવા ટેસ્ટનું નામ]:** [1-2 સરળ વાક્યોમાં શરીરમાં તેની ભૂમિકા, કાર્ય અને ફાયદા ઊંડાણપૂર્વક સમજાવો.]"""

        sec_3 = """### 3. શરીર પર અસર અને લક્ષણો (Impact on the Body & Symptoms)
આ સ્થિતિ, રોગ અથવા ટેસ્ટ પરિણામોની શરીર, ઉર્જા અને દૈનિક જીવન પર શું અસર થાય છે તેની ઊંડાણપૂર્વક સમજૂતી:
- **[શારીરિક લક્ષણ / અસર વિસ્તાર]:** [જેમ કે દુખાવો, ઝણઝણાટી, થાક, જકડાઈ જવું, સોજો, માંસપેશીઓની નબળાઈ અને સારવારથી થતો સુધારો.]"""

        sec_4 = """### 4. આહાર અને જીવનશૈલીમાં સુધારો (Actionable Diet & Nutrition Plan)
ખોરાક અને પોષણ અંગે સ્પષ્ટ, વ્યવહારુ અને વિગતવાર માર્ગદર્શન:
કઈ વસ્તુઓ ખાવી (Foods to Consume):
- **[આહાર વર્ગ / પોષક તત્વ]:** [લીલા શાકભાજી, ફળો, બદામ, અખરોટ, પૂરતું પાણી, પૌષ્ટિક આહાર અને તેનાથી શરીરને થતા ચોક્કસ ફાયદા.]
કઈ વસ્તુઓનો પરહેજ કરવો (Foods to Avoid):
- **[ટાળવા જેવી વસ્તુઓ અને આદતો]:** [તળેલું, પ્રોસેસ્ડ ફૂડ, વધુ પડતી ખાંડ/મીઠું, જમ્યા પછી તરત ચા/કોફી અને તેનાથી થતા નુકસાન.]"""

        sec_5 = """### 5. તબીબી સાવચેતીઓ અને ડૉક્ટરની સલાહ (Medical Precautions & Red Flags)
આરોગ્ય સંભાળ અને સુરક્ષા અંગે મહત્વપૂર્ણ તબીબી સલાહ:
આગળનાં પગલાં (Next Steps):
- [ક્યા નિષ્ણાત ડૉક્ટર (જેમ કે ઓર્થોપેડિક, ફિઝિશિયન) નો ફોલો-અપ સંપર્ક કરવો, દવાઓનું સમયસર સેવન અને જરૂરી તપાસ.]
કટોકટીના લક્ષણો (Red Flags):
- [કયા ગંભીર લક્ષણોમાં તાત્કાલિક હોસ્પિટલ પહોંચવું જરૂરી છે (જેમ કે હાથ-પગમાં અચાનક અશક્તિ, અતિશય દુખાવો, શ્વાસ લેવામાં તકલીફ, ગંભીર એલર્જી વગેરે).]"""

    else:
        lang_name = "English"
        lang_instruction = "Write strictly and 100% in pure English. Do NOT write in Hindi, Devanagari, Gujarati, or any non-English script anywhere in your response. All headings, explanations, bullet points, and clinical summaries MUST be entirely in English."
        sec_1 = """### 1. Key Findings Overview
Provide an introductory summary paragraph synthesizing the medical evaluation and clinical diagnosis.
Then provide two structured sub-sections in this exact format:
Normal Parameters:
- Bullet points detailing all parameters within normal limits, or prescribed medications that follow safe, standard clinical therapeutic regimens.
Abnormal Parameters:
- Bullet points detailing any abnormal/out-of-range parameters, or key medication safety precautions, potential side-effects, interactions, or symptoms requiring careful monitoring."""

        sec_2 = """### 2. Biological Function in Plain Language
Provide an introductory sentence explaining the biological role of these findings.
Then for EACH individual test parameter or prescribed medication (provide 3 to 7 distinct items):
- **[Test Parameter or Medicine Name]:** [1-2 concise, patient-friendly sentences explaining exactly what it does inside the human body in everyday terms and how it supports recovery.]"""

        sec_3 = """### 3. Impact on the Body & Symptoms
Provide a deep, comprehensive explanation of how this clinical condition, out-of-range markers, or medications impact the patient's daily life, physical sensations, and organ health:
- **[Symptom / Body System]:** [Deep explanation of physiological effects such as pain, tingling, nerve irritation, fatigue, mobility restriction, muscle stiffness, inflammation, or recovery timeline.]"""

        sec_4 = """### 4. Actionable Diet & Nutrition Plan
Provide clear, practical, and comprehensive dietary guidance customized to these findings:
Foods to Consume:
- **[Food Group / Nutrient]:** [Specific recommended foods such as leafy greens, whole grains, nuts, specific vitamins, hydration, and how they actively aid tissue healing and metabolic balance.]
Foods and Habits to Avoid:
- **[Food / Habit to Avoid]:** [Specific items such as processed foods, excess refined sugars, alcohol, excess caffeine, heavy spice, or skipping meals, with clear medical reasons.]"""

        sec_5 = """### 5. Medical Precautions & Red Flags
Provide essential clinical follow-up advice and critical safety signs:
Next Steps:
- [Clear, actionable bullet points specifying which specialist physician to consult (e.g., Orthopedic Surgeon, Neurologist, General Physician), dosage adherence, follow-up tests, or physical therapy.]
Red Flags (Seek Immediate Medical Attention):
- [Clear bullet points highlighting emergency danger signs requiring immediate hospital or emergency room visit (e.g., sudden severe numbness, loss of bladder/bowel control, chest pain, acute shortness of breath, severe allergic reaction).]"
"""

    # Summarize findings for prompt
    findings_lines = []
    for f in findings[:15]:
        if isinstance(f, dict):
            name = re.sub(r'[*_~`#]', '', str(f.get("test_name") or f.get("extracted_name") or f.get("finding_name") or f.get("english_name", ""))).strip()
            val = f.get("value", "")
            unit = f.get("unit", "")
            status = f.get("status") or f.get("severity", "")
            ref = f.get("reference_range", "")
            freq = f.get("frequency", "")
            timing = f.get("timing", "")
            purp = f.get("purpose", "")
            if val:
                findings_lines.append(f"- {name}: {val} {unit} (Reference: {ref}) [{status}]")
            elif freq:
                extra = f", Purpose: {purp}" if purp else ""
                findings_lines.append(f"- {name} (Dose/Freq: {freq}, Timing: {timing}{extra})")
            else:
                findings_lines.append(f"- {name} [{status}]")

    findings_summary = "\n".join(findings_lines) if findings_lines else "General findings extracted from report."

    prompt = f"""You are DocMindX AI — Senior Clinical Pathologist & Patient Health Advisor.
Analyze this medical document and produce an exhaustive, deep, patient-friendly clinical guide.

REPORT TYPE: {report_type}
PATIENT DEMOGRAPHICS: Age Group: {age_group}, Biological Gender: {gender}

EXTRACTED PARAMETERS & FINDINGS:
{findings_summary}

RAW EXTRACTED TEXT EXCERPT:
\"\"\"{doc_text[:1400]}\"\"\"

CRITICAL INSTRUCTIONS:
1. {lang_instruction}
2. Do NOT use any emojis.
3. Provide deep, clear, empathetic explanation so the patient fully understands their health without medical jargon.
4. Structure the response into these 5 clear markdown sections with identical depth and exact sub-headers:

{sec_1}

{sec_2}

{sec_3}

{sec_4}

{sec_5}"""

    # 1. Gemini AI (Primary — Multi-Key Failover Pool)
    if gemini_pool.get_active_keys():
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2500}
        }
        res_data, _, _ = gemini_pool.execute_with_failover(
            payload=payload,
            models=["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"],
            timeout=14
        )
        if res_data:
            candidates = res_data.get("candidates", [])
            if candidates:
                txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if txt and len(txt.strip()) > 80:
                    if is_valid_script_for_language(txt, lang):
                        return txt.strip()
                    # If AI returned wrong script (e.g. English when Hindi/Gujarati was selected), repair via 1-shot translate
                    try:
                        trans_prompt = (
                            f"Translate this medical breakdown strictly into natural, fluent {lang_name}. "
                            f"Keep the exact 5 markdown sections (1 to 5) and all sub-headers intact without emojis:\n\n{txt}"
                        )
                        trans_payload = {
                            "contents": [{"parts": [{"text": trans_prompt}]}],
                            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2500}
                        }
                        t_data, _, _ = gemini_pool.execute_with_failover(
                            payload=trans_payload,
                            models=["gemini-3.6-flash", "gemini-3.5-flash-lite"],
                            timeout=10
                        )
                        if t_data:
                            t_cand = t_data.get("candidates", [])
                            if t_cand:
                                t_txt = t_cand[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                                if t_txt and is_valid_script_for_language(t_txt, lang):
                                    return t_txt
                    except Exception as trans_e:
                        print("Breakdown script repair notice:", trans_e)

    # 2. Groq AI (Fallback)
    if GROQ_API_KEY:
        for model in GROQ_MODELS:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": f"You are DocMindX AI Senior Clinical Pathologist. {lang_instruction} Do NOT use emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2200
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=10)
                if res.status_code == 200:
                    txt = res.json()["choices"][0]["message"]["content"]
                    if txt and len(txt.strip()) > 80 and is_valid_script_for_language(txt, lang):
                        return txt.strip()
            except Exception as e:
                print(f"Report breakdown Groq notice ({model}): {e}")

    # 3. Local Rule-Based Fallback with complete 5 sections and sub-headers
    med_or_param_lines = []
    for f in findings[:6]:
        if isinstance(f, dict):
            fn = re.sub(r'[*_~`#]', '', str(f.get("extracted_name") or f.get("test_name") or f.get("finding_name") or "Marker")).strip()
            fp = f.get("purpose") or "Supports cellular recovery and physiologic homeostasis."
            med_or_param_lines.append(f"- **{fn}:** {fp}")
    cards_text = "\n".join(med_or_param_lines) if med_or_param_lines else "- **Clinical Marker:** Essential indicator for physiological and metabolic balance."

    if lang == "hi":
        return f"""### 1. रिपोर्ट का मुख्य सारांश (Key Findings Overview)
आपकी इस रिपोर्ट में {len(findings)} मुख्य पैरामीटर्स और दवाओं का विस्तृत नैदानिक विश्लेषण किया गया है।

सामान्य पैरामीटर (Normal Parameters):
- अधिकांश प्रमुख मान और निर्धारित दवाएं सुरक्षित चिकित्सीय मानकों के अनुसार हैं।
- निर्धारित दवाएं लक्षण राहत और शारीरिक सुधार के लिए उपयुक्त हैं।

असामान्य पैरामीटर (Abnormal Parameters):
- कुछ मानों या लक्षणों पर विशेष निगरानी और सावधानी की आवश्यकता है।
- दवाओं का सेवन समय पर करें और किसी भी दुष्प्रभाव पर तुरंत डॉक्टर से संपर्क करें।

### 2. यह पैरामीटर / टेस्ट क्या है और शरीर में इसका क्या कार्य है? (Biological Function in Plain Language)
रिपोर्ट में शामिल घटकों और दवाओं की मुख्य जैविक भूमिका निम्नलिखित है:
{cards_text}

### 3. शरीर पर असर और इसके लक्षण (Impact on the Body & Symptoms)
- **शारीरिक ऊर्जा व कार्यप्रणाली:** असंतुलन या दर्द से थकान और कार्यक्षमता में कमी हो सकती है।
- **मांसपेशियां व तंत्रिकाएं:** तंत्रिका संवेदनशीलता या जोड़ों में जकड़न से दैनिक गतिविधियों में असुविधा महसूस हो सकती है।
- **पुનःप्राप्ति:** निर्धारित उपचार से सूजन में कमी और गतिशीलता में निरंतर सुधार होता है।

### 4. इसे सुधारने के लिए क्या खाएं और क्या न खाएं? (Actionable Diet & Nutrition Plan)
क्या खाएं (Foods to Consume):
- **पोषक तत्व युक्त आहार:** हरी पत्तेदार सब्जियां, मौसमी फल, साबुत अनाज और दालें खाएं।
- **हाइड्रेशन:** शरीर से विषाक्त पदार्थों को बाहर निकालने और जोड़ों के लचीलेपन के लिए पर्याप्त पानी पिएं।

क्या न खाएं (Foods to Avoid):
- **प्रोसेस्ड भोजन:** अत्यधिक तला-भुना, जंक फूड और भारी मसालेदार भोजन से बचें।
- **चाय व कॉफी:** भोजन के तुरंत बाद चाय या कॉफी न पिएं ताकि पोषक तत्वों का अवशोषण प्रभावित न हो।

### 5. सावधानियां व डॉक्टर से परामर्श (Medical Precautions & Red Flags)
अगले कदम (Next Steps):
- अपने डॉक्टर के निर्देशानुसार दवाओं का नियमित समय पर सेवन करें।
- लक्षणों की समीक्षा और उपचार की प्रगति के लिए विशेषज्ञ चिकित्सक से फॉलो-अप परामर्श लें।

खतरे के लक्षण (Red Flags):
- अचानक अंगों में गंभीर कमजोरी, तेज दर्द, सांस लेने में तकलीफ या सीने में दबाव महसूस होने पर तुरंत अस्पताल जाएं।"""

    elif lang == "gu":
        return f"""### 1. રિપોર્ટનો મુખ્ય સારાંશ (Key Findings Overview)
તમારા આ રિપોર્ટમાં {len(findings)} મુખ્ય પરિણામો અને દવાઓનું તબીબી વિશ્લેષણ કરવામાં આવ્યું છે.

સામાન્ય પરિણામો (Normal Parameters):
- મોટાભાગના પરિણામો અને સૂચવેલી દવાઓ સલામત ક્લિનિકલ ધોરણો મુજબ છે.
- દવાઓ શરીરમાં રાહત અને રોગનિવારણ માટે અસરકારક છે.

અસામાન્ય પરિણામો (Abnormal Parameters):
- અમુક લક્ષણો અથવા પરિણામો પર ધ્યાન આપવું જરૂરી છે.
- દવાનો યોગ્ય ડોઝ લો અને અસામાન્ય આડઅસર જણાય તો ડૉક્ટરનો સંપર્ક કરો.

### 2. આ પરિણામોનું મહત્વ અને શરીર પર અસર (Biological Function in Plain Language)
રિપોર્ટના મુખ્ય પરિમાણો અને દવાઓનું શરીરમાં કાર્ય:
{cards_text}

### 3. શરીર પર અસર અને લક્ષણો (Impact on the Body & Symptoms)
- **શારીરિક ઉર્જા:** અસંતુલન કે દુખાવાના કારણે થાક અને સ્ફૂર્તિમાં ઘટાડો થઈ શકે છે.
- **સ્નાયુઓ અને સાંધા:** જકડાઈ જવું, સોજો અથવા દુખાવો અનુભવાઈ શકે છે.
- **રિકવરી:** યોગ્ય સારવારથી સાંધા અને માંસપેશીઓમાં ધીમે ધીમે સુધારો થાય છે.

### 4. આહાર અને જીવનશૈલીમાં સુધારો (Actionable Diet & Nutrition Plan)
કઈ વસ્તુઓ ખાવી (Foods to Consume):
- **પૌષ્ટિક આહાર:** લીલા શાકભાજી, તાજા ફળો, બદામ-અખરોટ અને પૂરતું પાણી પીવો.
- **વિટામિન યુક્ત ખોરાક:** કેલ્શિયમ અને બી-વિટામિન સમૃદ્ધ આહાર લો.

કઈ વસ્તુઓનો પરહેજ કરવો (Foods to Avoid):
- **તળેલું અને પ્રોસેસ્ડ ફૂડ:** વધુ પડતું તળેલું અને જંક ફૂડ ખાવાનું ટાળો.
- **ચા અને કોફી:** જમ્યા પછી તરત ચા-કોફી પીવાનું ટાળો.

### 5. તબીબી સાવચેતીઓ અને ડૉક્ટરની સલાહ (Medical Precautions & Red Flags)
આગળનાં પગલાં (Next Steps):
- તમારા ડૉક્ટરની સલાહ મુજબ નિયમિત સમયે દવાઓ લો.
- લક્ષણોમાં સુધારાની સમીક્ષા માટે નિયત સમયે ડૉક્ટર સાથે ફોલો-અપ મુલાકાત લો.

કટોકટીના લક્ષણો (Red Flags):
- અચાનક હાથ-પગમાં અતિશય અશક્તિ, છાતીમાં દુખાવો, અથવા શ્વાસ લેવામાં તકલીફ જણાય તો તાત્કાલિક હોસ્પિટલ પહોંચો."""

    else:
        return f"""### 1. Key Findings Overview
Evaluated {len(findings)} clinical parameters and therapeutic markers from your uploaded medical report.

Normal Parameters:
- Core indicators and prescribed treatments align within safe standard clinical dosage guidelines.
- The therapeutic regimen actively targets symptom reduction, nutrient support, and musculoskeletal health.

Abnormal Parameters:
- Specific discomfort markers, nerve sensitivity, or physiological indicators require scheduled monitoring.
- Ensure strict adherence to prescribed medication schedules and report any adverse reactions promptly.

### 2. Biological Function in Plain Language
Simple explanations of the key diagnostic markers and medications detected in your report:
{cards_text}

### 3. Impact on the Body & Symptoms
- **Physical Stamina & Mobility:** Underlying irritation or inflammation may manifest as local stiffness, discomfort, or reduced stamina.
- **Neuromuscular Function:** Nerve sensitivity or muscle tightness can cause localized tingling or restricted range of motion.
- **Therapeutic Recovery:** Target medications systematically reduce tissue inflammation and restore joint comfort.

### 4. Actionable Diet & Nutrition Plan
Foods to Consume:
- **Nutrient-Dense Whole Foods:** Incorporate dark leafy greens, whole grains, nuts, seeds, and lean proteins.
- **Optimal Hydration:** Drink plenty of water throughout the day to support joint lubrication and metabolic cellular clearance.

Foods and Habits to Avoid:
- **Processed & High-Sugar Foods:** Minimize heavily fried items, refined sugars, and artificial additives that promote inflammation.
- **Post-Meal Stimulants:** Avoid drinking tea or coffee immediately following meals to preserve micronutrient absorption.

### 5. Medical Precautions & Red Flags
Next Steps:
- Follow your physician's prescribed medication schedule precisely and take medications after food as directed.
- Schedule a follow-up evaluation with your doctor to review symptom progression and therapy effectiveness.

Red Flags (Seek Immediate Medical Attention):
- Seek urgent emergency medical review if you experience sudden severe limb numbness, acute shortness of breath, chest tightness, or allergic swelling."""
