"""
DocMindX AI - Multilingual Conversational Healthcare Assistant
Powered by Groq API (Primary) and Gemini AI (Fallback) with clinical knowledge
guardrails, context-aware personalized guidance, and dynamic question generation.
"""
import json
import os
import re

import requests

from config.settings import GEMINI_API_KEY, GROQ_API_KEY


def generate_dynamic_patient_questions(clinical_context: dict = None, lang_code: str = "en") -> list:
    """
    Generates contextual guided questions in the user's preferred language,
    tailored to the exact symptoms, condition, and medicines currently in session.
    """
    clinical_context = clinical_context or {}
    symptoms = clinical_context.get("symptoms", [])
    top_disease = clinical_context.get("top_disease", "")
    medicines = clinical_context.get("medicines", [])
    
    sym_name = symptoms[0] if symptoms else ""
    disease_name = top_disease if top_disease else "my condition"
    med_name = ""
    if medicines:
        first_m = medicines[0]
        if isinstance(first_m, dict):
            med_name = first_m.get("medicine_name") or first_m.get("name", "")
        else:
            med_name = str(first_m)
        med_name = med_name.split("(")[0].strip() or "Medication"
    else:
        med_name = "Prescribed Medicines"

    symptom_text = ", ".join(symptoms) if symptoms else (top_disease or "your current health concern")

    if lang_code == "hi":
        return [
            {"label": f"{symptom_text} को सरल भाषा में समझाएं", "query": f"मेरे लक्षणों ({symptom_text}) का सरल अर्थ और संभावित कारण समझाएं।"},
            {"label": f"{med_name} कब और कैसे लें?", "query": f"{med_name} की खुराक, भोजन का समय और सावधानियां बताएं।"},
            {"label": f"{disease_name} में क्या खाएं?", "query": f"{disease_name} में कौन सा भोजन लाभदायक है और किन चीजों से परहेज करें?"},
            {"label": "खतरे के संकेत कौन से हैं?", "query": f"{symptom_text} में कौन से red flags होने पर तुरंत अस्पताल जाना चाहिए?"},
            {"label": "दवा के दुष्प्रभाव बताएं", "query": f"{med_name} के सामान्य और गंभीर दुष्प्रभाव तथा उनसे बचने की सावधानियां बताएं।"},
            {"label": "दवाओं का आपसी असर समझाएं", "query": f"मेरी दवाओं ({med_name}) के बीच drug interaction या allergy risk समझाएं।"},
            {"label": "रिपोर्ट का अर्थ कैसे समझें?", "query": "मेरी medical report के abnormal values को आसान भाषा में कैसे समझें?"},
            {"label": "कौन से टेस्ट जरूरी हो सकते हैं?", "query": f"{disease_name} और {symptom_text} के लिए डॉक्टर से कौन से tests discuss करने चाहिए?"},
            {"label": "ठीक होने में कितना समय लगेगा?", "query": f"{disease_name} या {symptom_text} में सामान्य recovery timeline और सुधार के संकेत बताएं।"},
            {"label": "घर पर क्या सावधानी रखें?", "query": f"{symptom_text} के दौरान घर पर सुरक्षित self-care और monitoring steps बताएं।"},
            {"label": "योग और lifestyle guidance", "query": f"{disease_name} में सुरक्षित yoga, rest और lifestyle guidance बताएं।"},
            {"label": "अगला clinical step क्या है?", "query": f"{disease_name} के लिए मेरा अगला सुरक्षित clinical step और doctor follow-up कब होना चाहिए?"}
        ]
    elif lang_code == "gu":
        return [
            {"label": f"{symptom_text} સરળ ભાષામાં સમજાવો", "query": f"મારા લક્ષણો ({symptom_text}) નો સરળ અર્થ અને સંભવિત કારણ સમજાવો."},
            {"label": f"{med_name} ક્યારે અને કેવી રીતે લેવી?", "query": f"{med_name} ની માત્રા, જમવાનો સમય અને સાવચેતી સમજાવો."},
            {"label": f"{disease_name} માં શું ખાવું?", "query": f"{disease_name} માં કયો આહાર લાભદાયક છે અને કઈ વસ્તુઓથી પરહેજ કરવો?"},
            {"label": "ખતરાના સંકેતો કયા છે?", "query": f"{symptom_text} માં કયા red flags જણાય તો તરત હોસ્પિટલ જવું જોઈએ?"},
            {"label": "દવાની આડઅસર સમજાવો", "query": f"{med_name} ની સામાન્ય અને ગંભીર આડઅસર તથા સાવચેતી સમજાવો."},
            {"label": "દવાઓ વચ્ચેની અસર સમજાવો", "query": f"મારી દવાઓ ({med_name}) વચ્ચે drug interaction અથવા allergy risk સમજાવો."},
            {"label": "રિપોર્ટનો અર્થ કેવી રીતે સમજવો?", "query": "મારી medical report ના abnormal values સરળ ભાષામાં સમજાવો."},
            {"label": "કયા ટેસ્ટની જરૂર પડી શકે?", "query": f"{disease_name} અને {symptom_text} માટે કયા tests અંગે doctor સાથે ચર્ચા કરવી?"},
            {"label": "સાજા થવામાં કેટલો સમય?", "query": f"{disease_name} અથવા {symptom_text} માટે સામાન્ય recovery timeline સમજાવો."},
            {"label": "ઘરે કઈ સાવચેતી રાખવી?", "query": f"{symptom_text} દરમિયાન ઘરે સુરક્ષિત self-care અને monitoring steps આપો."},
            {"label": "યોગ અને lifestyle guidance", "query": f"{disease_name} માટે સુરક્ષિત yoga, rest અને lifestyle guidance આપો."},
            {"label": "આગળનું clinical step શું છે?", "query": f"{disease_name} માટે આગળનું સુરક્ષિત clinical step અને doctor follow-up ક્યારે કરવો?"}
        ]
    else:
        return [
            {"label": f"Explain {symptom_text} in plain terms", "query": f"Explain the meaning and possible causes of my symptoms ({symptom_text}) in simple terms."},
            {"label": f"When and how to take {med_name}?", "query": f"Explain the dosage, food timing, and precautions for {med_name}."},
            {"label": f"What foods help with {disease_name}?", "query": f"What foods may help with {disease_name}, and what should I avoid?"},
            {"label": "What are the danger signs?", "query": f"What red flags related to {symptom_text} require immediate hospital care?"},
            {"label": "Explain medicine side effects", "query": f"What common and serious side effects should I watch for with {med_name}?"},
            {"label": "Check medicine interactions", "query": f"Explain possible drug interactions or allergy risks involving {med_name}."},
            {"label": "How should I read my report?", "query": "Explain the abnormal values in my medical report in plain language."},
            {"label": "Which tests may be needed?", "query": f"Which tests should I discuss with my doctor for {disease_name} and {symptom_text}?"},
            {"label": "How long may recovery take?", "query": f"What is the usual recovery timeline and improvement signs for {disease_name}?"},
            {"label": "What care is safe at home?", "query": f"Give safe home-care and monitoring steps for {symptom_text}."},
            {"label": "Yoga and lifestyle guidance", "query": f"Suggest safe yoga, rest, and lifestyle guidance for {disease_name}."},
            {"label": "What is the next clinical step?", "query": f"What is the next safe clinical step and doctor follow-up plan for {disease_name}?"}
        ]


def detect_redirect_action(text: str, lang_code: str = "en"):
    """
    Detects if user query or assistant reply pertains to a specific DocMindX module
    and returns target panel info for rendering interactive redirect buttons in the chat.
    """
    if not text:
        return None
    t = text.lower()
    
    # 1. Medical Report Scanner / Prescription / Radiology / Blood Test
    if any(w in t for w in [
        "lab report", "blood report", "medical report", "scan report", "upload report", "report scan", 
        "x-ray", "mri", "ct scan", "radiology", "prescription", "percha", "parcha", 
        "रिपोर्ट", "परचा", "खून की जांच", "रक्त परीक्षण",
        "પ્રિસ્ક્રિપ્શન", "લેબ રિપોર્ટ", "રિપોર્ટ", "સ્કેન"
    ]):
        labels = {
            "en": "Go to Medical Report Scanner",
            "hi": "मेडिकल रिपोर्ट स्कैनर खोलें",
            "gu": "મેડિકલ રિપોર્ટ સ્કેનર ખોલો"
        }
        return {"panel": "Medical Report", "label": labels.get(lang_code, labels["en"])}
        
    # 2. Nearby Healthcare / Hospital / Clinic / Doctor Locator
    elif any(w in t for w in [
        "hospital", "clinic", "doctor", "nearby", "dispensary", "emergency room", "locate hospital", "find doctor",
        "अस्पताल", "डॉक्टर", "दवाखाना", "क्लिनिक", "नजदीकी अस्पताल",
        "નજીકની હોસ્પિટલ", "હોસ્પિટલ", "દાક્તર", "દવાખાનું"
    ]):
        labels = {
            "en": "Find Nearby Hospitals & Clinics",
            "hi": "पास के अस्पताल व क्लिनिक खोजें",
            "gu": "નજીકના હોસ્પિટલ અને ક્લિનિક શોધો"
        }
        return {"panel": "Nearby Healthcare", "label": labels.get(lang_code, labels["en"])}
        
    # 3. Symptom Assessment & Triage
    elif any(w in t for w in [
        "symptom check", "triage", "start assessment", "check symptoms", "health assessment", "symptom triage",
        "लक्षण जांच", "जांच शुरू करें", "लक्षण विश्लेषण",
        "લક્ષણો તપાસ", "તપાસ શરૂ કરો", "લક્ષણ વિશ્લેષણ"
    ]):
        labels = {
            "en": "Start Health & Symptom Assessment",
            "hi": "स्वास्थ्य व लक्षण जांच शुरू करें",
            "gu": "આરોગ્ય અને લક્ષણ તપાસ શરૂ કરો"
        }
        return {"panel": "Health Assessment", "label": labels.get(lang_code, labels["en"])}
        
    # 4. Health Records / History
    elif any(w in t for w in [
        "health record", "saved report", "my history", "past record", "medical history",
        "रिकॉर्ड", "इतिहास", "पुराने रिकॉर्ड",
        "ઇતિહાસ", "રેકોર્ડ", "જૂના રિપોર્ટ"
    ]):
        labels = {
            "en": "View My Health Records",
            "hi": "स्वास्थ्य रिकॉर्ड देखें",
            "gu": "હેલ્થ રેકોર્ડ જુઓ"
        }
        return {"panel": "Health Records", "label": labels.get(lang_code, labels["en"])}

    # 5. National Command
    elif any(w in t for w in [
        "supply chain", "phc", "command center", "stockout", "shortage", "redistribution", "bed capacity", 
        "workforce", "national health", "daskroi", "sanand", "bavla", "olpad", "insulin stock",
        "सप्लाई चेन", "कमान केंद्र", "दवा की कमी", "पुनर्वितरण", "पीएचसी", "बेड उपलब्धता",
        "સપ્લાય ચેઈન", "કમાન્ડ સેન્ટર", "દવા અછત", "રીડિસ્ટ્રિબ્યુશન", "બેડ ઉપલબ્ધતા"
    ]):
        labels = {
            "en": "Open National Command",
            "hi": "राष्ट्रीय कमान केंद्र खोलें",
            "gu": "રાષ્ટ્રીય કમાન્ડ સેન્ટર ખોલો"
        }
        return {"panel": "National Command", "label": labels.get(lang_code, labels["en"])}

    return None


def ask_DocMindX_ai(user_message: str, chat_history: list = None, clinical_context: dict = None, lang_code: str = "en") -> str:
    """
    Advanced Multilingual Clinical AI Chatbot.
    Uses Live Groq API as the primary conversational engine with Gemini as fallback
    and full patient demographic & clinical context to deliver real, comprehensive answers.
    Refuses non-medical queries politely. Emits NO emojis.
    """
    if not user_message or not user_message.strip():
        msg_map = {
            "hi": "कृपया अपने स्वास्थ्य, लक्षणों या दवाओं से संबंधित कोई प्रश्न पूछें।",
            "gu": "કૃપા કરીને તમારા સ્વાસ્થ્ય, લક્ષણો અથવા દવાઓ સંબંધિત કોઈ પ્રશ્ન પૂછો.",
            "en": "Please ask a question regarding your health, symptoms, medicines, or medical reports."
        }
        return msg_map.get(lang_code, msg_map["en"])

    chat_history = chat_history or []
    clinical_context = clinical_context or {}

    # Extract Patient Clinical Profile
    symptoms = clinical_context.get("symptoms", [])
    top_disease = clinical_context.get("top_disease", "")
    medicines = clinical_context.get("medicines", [])
    age_group = clinical_context.get("age", clinical_context.get("age_group", "Adult"))
    gender = clinical_context.get("gender", "Unspecified")
    location = clinical_context.get("location", "India")
    conditions = clinical_context.get("conditions", clinical_context.get("pre_existing", []))
    conditions_str = ", ".join(conditions) if isinstance(conditions, list) else str(conditions)
    current_meds = clinical_context.get("current_meds", clinical_context.get("medications", "None"))
    allergies = clinical_context.get("allergies", "None")
    report_text = clinical_context.get("report_text", "")
    report_type = clinical_context.get("report_type", "")

    meds_summary = []
    for m in medicines:
        if isinstance(m, dict):
            name = m.get("medicine_name") or m.get("name", "")
            dosage = m.get("dosage", "")
            timing = m.get("food_timing", "")
            duration = m.get("course_duration", "")
            meds_summary.append(f"{name} ({dosage}, {timing}, {duration})")
        else:
            meds_summary.append(str(m))
    meds_str = "; ".join(meds_summary) if meds_summary else "None specified"

    report_context_section = f"\n- Extracted Medical Report / Prescription ({report_type}):\n{report_text[:1200]}\n" if report_text else ""

    lang_desc = "Gujarati (ગુજરાતી)" if lang_code == "gu" else ("Hindi (हिंदी)" if lang_code == "hi" else "English")

    system_prompt = f"""You are DocMindX AI — a state-of-the-art Clinical AI Healthcare Assistant and Patient Medical Copilot.
Your job is to provide real, scientifically accurate, clinically detailed, and empathetic medical answers to patients.

PATIENT PROFILE & CURRENT ASSESSMENT CONTEXT:
- Demographics: Age Group: {age_group}, Biological Gender: {gender}, Location: {location}
- Clinical Symptoms: {', '.join(symptoms) if symptoms else 'General Clinical Consultation'}
- Primary Assessed Condition: {top_disease or 'Under Clinical Evaluation'}
- Current Prescribed/Suggested Medications: {meds_str}
- Pre-existing Medical Conditions: {conditions_str}
- Ongoing Regular Medications: {current_meds}
- Known Drug & Food Allergies: {allergies}{report_context_section}

CRITICAL RULES & OPERATIONAL INSTRUCTIONS:
1. LANGUAGE CONSISTENCY:
   - You MUST answer strictly in {lang_desc}.
   - If the user asks in Gujarati or Gujarati is selected, reply entirely in natural, clear Gujarati.
   - If Hindi is selected, reply in clear, professional Hindi.
   - If English is selected, reply in clear, empathetic English.
   - Match the user's language and tone seamlessly.

2. REAL, SUBSTANTIVE CLINICAL ANSWERS:
   - Give direct, comprehensive, and actionable answers to the user's specific question.
   - If asked about medications (e.g. Dolo 650, Pan 40, Augmentin): explain exact mechanism, dosage guidance, whether to take before/after food, course duration, and safety precautions.
   - If asked about symptoms or disease: explain the underlying biological cause, stages of recovery, and self-care steps.
   - If asked about diet: give specific foods to consume and foods to strictly avoid.
   - If asked about lab tests: explain what normal vs abnormal values indicate.
   - If asked what DocMindX AI is: explain that it is an enterprise healthcare suite providing AI symptom triage, lab report OCR analysis, prescription digitization, and nearby 24/7 hospital locator.

3. ZERO EMOJIS POLICY:
   - Strictly DO NOT use any emojis in your response. Keep the response clean and clinically professional.

4. SAFETY & RED FLAGS:
   - Always highlight danger warning signs (such as high persistent fever >103°F, acute shortness of breath, severe chest pain, or sudden confusion) where immediate emergency medical evaluation is necessary.
   - Conclude with a brief standard clinical advisory reminding the patient that this is AI guidance and they should confirm treatment with their treating doctor."""

    # Normal chatbot conversations use Groq first.
    if GROQ_API_KEY:
        groq_messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history[-6:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content", "").strip()
            if content:
                groq_messages.append({"role": role, "content": content})
        groq_messages.append({"role": "user", "content": user_message})

        for groq_model in ["qwen/qwen3.6-27b", "llama-3.3-70b-versatile"]:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": groq_model,
                    "messages": groq_messages,
                    "temperature": 0.3,
                    "max_tokens": 900
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=5)
                if res.status_code == 200:
                    raw_ans = res.json()["choices"][0]["message"]["content"]
                    if "</think>" in raw_ans:
                        ans = raw_ans.split("</think>")[-1].strip()
                    else:
                        ans = re.sub(r"<think>.*?</think>", "", raw_ans, flags=re.DOTALL).strip()
                    if ans:
                        return ans
            except Exception as e:
                print(f"Groq {groq_model} chat notice: {e}")

    # Gemini is retained only as a fallback for normal chat outages.
    if GEMINI_API_KEY:
        gemini_contents = []
        for msg in chat_history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "").strip()
            if content:
                gemini_contents.append({"role": role, "parts": [{"text": content}]})
        gemini_contents.append({"role": "user", "parts": [{"text": user_message}]})

        for gem_model in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": gemini_contents,
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
                }
                res = requests.post(url, json=payload, timeout=9)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and parts[0].get("text"):
                            ans = parts[0]["text"].strip()
                            if ans:
                                return ans
            except Exception as e:
                print(f"Gemini {gem_model} chat fallback notice: {e}")

    # 3. Dynamic Patient-Context Knowledge Fallback (If APIs are temporarily unreachable)
    q_lower = user_message.lower()
    
    # Non-medical filter
    non_med = ["cricket", "movie", "film", "cinema", "song", "python", "code", "java", "math", "politics", "crypto", "stock"]
    if any(k in q_lower for k in non_med):
        if lang_code == "hi":
            return "DocMindX AI विशेष रूप से स्वास्थ्य, लक्षण, दवाओं और क्लिनिकल मार्गदर्शन के लिए है। कृपया स्वास्थ्य से जुड़ा कोई प्रश्न पूछें।"
        elif lang_code == "gu":
            return "DocMindX AI ફક્ત સ્વાસ્થ્ય, લક્ષણો, દવાઓ અને ક્લિનિકલ માર્ગદર્શન માટે છે. કૃપા કરીને આરોગ્ય સંબંધિત પ્રશ્ન પૂછો."
        else:
            return "DocMindX AI is dedicated exclusively to healthcare, symptoms, medications, and clinical triage. Please ask a health-related question."

    # DocMindX Overview
    if "DocMindX" in q_lower or "kya hai" in q_lower or "kaya che" in q_lower or "what is" in q_lower:
        if lang_code == "hi":
            return f"DocMindX AI एक उन्नत मल्टीलिंगुअल हेल्थकेयर AI प्लेटफॉर्म है जो मरीजों को उनकी भाषा में सटीक स्वास्थ्य मार्गदर्शन देता है। यह {top_disease or 'लक्षणों'} की जांच, दवाओं की सही खुराक व समय, खून की रिपोर्ट का विश्लेषण, और नजदीकी 24/7 अस्पतालों को खोजने की सुविधा प्रदान करता है।"
        elif lang_code == "gu":
            return f"DocMindX AI એ એક આધુનિક હેલ્થકેર AI પ્લેટફોર્મ છે જે દર્દીઓને પોતાની ભાષામાં સચોટ માર્ગદર્શન આપે છે. તે {top_disease or 'લક્ષણો'}નું વિશ્લેષણ, સાચી દવા અને ડોઝની માહિતી, લેબ બ્લડ રિપોર્ટ એનાલિસિસ અને નજીકની હોસ્પિટલ શોધવાની સુવિધા પૂરી પાડે છે."
        else:
            return f"DocMindX AI is an intelligent healthcare platform providing personalized symptom triage, medication verification, laboratory report analysis, and nearby hospital GIS navigation tailored for conditions like {top_disease or 'acute illnesses'}."

    # Condition-tailored response
    if lang_code == "gu":
        return f"""ક્લિનિકલ વિશ્લેષણ:
તમારા પ્રશ્ન: "{user_message}" ના સંદર્ભમાં {top_disease or 'લક્ષણો'} માટે નીચે મુજબ માર્ગદર્શન છે:
- દવાઓ: ડૉક્ટરની સલાહ મુજબ નિયત સમયે લો અને ડોઝ જાતે ન બદલો.
- આહાર અને હાઇડ્રેશન: સરળતાથી પચી જાય તેવો હળવો પૌષ્ટિક આહાર લો અને દિવસમાં 2.5 થી 3 લિટર પાણી/પ્રવાહીનું સેવન કરો.
- સાવચેતી: જો તાવ ૧૦૩°F થી વધે અથવા શ્વાસમાં તકલીફ જણાય, તો તુરંત નજીકની હોસ્પિટલનો સંપર્ક કરવો.
(આ માહિતી માર્ગદર્શન માટે છે, ઔપચારિક સારવાર માટે ડૉક્ટરની સલાહ લેવી જરૂરી છે.)"""
    elif lang_code == "hi":
        return f"""क्लिनिकल विश्लेषण:
आपके प्रश्न: "{user_message}" के संदर्भ में {top_disease or 'लक्षणों'} हेतु मार्गदर्शन:
- दवाएं: डॉक्टर के निर्देशानुसार समय पर लें और खुराक खुद से न बदलें।
- आहार व जलयोजन: सुपाच्य पौष्टिक भोजन लें और पर्याप्त मात्रा में गुनगुना पानी या तरल पदार्थ पिएं।
- सावधानी: यदि बुखार 103°F से अधिक रहे या सांस लेने में परेशानी हो, तो तुरंत डॉक्टर से संपर्क करें।
(यह जानकारी मार्गदर्शन के लिए है, औपचारिक उपचार हेतु डॉक्टर से परामर्श लें। )"""
    else:
        return f"""Clinical Guidance:
Regarding your query: "{user_message}" in the context of {top_disease or 'reported symptoms'}:
- Medications: Follow prescribed dosages strictly at scheduled food timings.
- Nutrition & Hydration: Maintain nutrient-dense light meals and drink 2.5 - 3.0 liters of fluids daily.
- Red Flags: Seek emergency care if you experience persistent high fever exceeding 103°F, shortness of breath, or chest pain.
(This guidance is for informational triage support. Consult a licensed physician for diagnosis and treatment.)"""


# Backward compatibility aliases
ask_DocMindX_ai = ask_DocMindX_ai = ask_docmindx_ai = ask_DocMindX_ai
