"""
    DocMindX AI - Generative AI Layer (Gemini & Groq with Offline Clinical Fallback)
"""
import os
import requests
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

def generate_health_summary_ai(symptoms_list, top_condition, user_context, lang="en"):
    """
    Generate an empathetic, clinical-safety compliant health summary using Gemini or Groq API.
    Falls back cleanly to structured clinical knowledge base if API key is not set or network fails.
    """
    lang_name = "English" if lang == "en" else "Hindi" if lang == "hi" else "Gujarati"
    
    prompt = f"""
    You are DocMindX AI, a compassionate and clinically objective healthcare triage assistant.
    The user is experiencing the following symptoms: {', '.join(symptoms_list)}.
    Primary matched condition for discussion with a doctor: {top_condition}.
    User Context: Age: {user_context.get('age', 'Adult')}, Gender: {user_context.get('gender', 'Not specified')}, Duration: {user_context.get('duration', 'Few days')}.
    
    Instructions:
    1. Write a 2-3 paragraph empathetic explanation in {lang_name}.
    2. Explain what these symptoms generally indicate in simple, easy-to-understand terms.
    3. Emphasize that this is triage guidance and recommend consulting a qualified doctor.
    4. Avoid prescribing specific prescription medications.
    5. Be reassuring and clear.
    """

    # 1. Try Gemini REST API
    if GEMINI_API_KEY:
        for gemini_model in ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 600
                    }
                }
                headers = {"Content-Type": "application/json"}
                res = requests.post(gemini_url, headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
            except Exception as e:
                print(f"Gemini {gemini_model} note: {e}")

    # 2. Try Groq
    if GROQ_API_KEY:
        for groq_model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "qwen/qwen3.6-27b", "groq/compound"]:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": "You are a professional medical triage communicator."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 500
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"Groq {groq_model} note: {e}")

    # 3. High-Quality Offline Clinical Fallback
    if lang == "hi":
        return f"""
आपके द्वारा बताए गए लक्षण ({', '.join(symptoms_list)}) मुख्य रूप से **{top_condition}** जैसी सामान्य स्वास्थ्य स्थिति से मेल खाते हैं। 
यह स्थिति अक्सर मौसम के बदलाव, वायरल संक्रमण या शारीरिक तनाव के कारण हो सकती है। सामान्यतः पर्याप्त आराम, तरल पदार्थों का नियमित सेवन और पौष्टिक आहार से शरीर को स्वस्थ होने में मदद मिलती है।
**महत्वपूर्ण सलाह:** कृपया ध्यान दें कि यह विश्लेषण केवल सामान्य जानकारी और प्राथमिक मार्गदर्शन के लिए है। यदि लक्षण 3-5 दिनों से अधिक समय तक बने रहें या सांस लेने में परेशानी जैसे कोई नए लक्षण दिखें, तो बिना देरी किए किसी योग्य डॉक्टर से संपर्क करें।
        """.strip()
    elif lang == "gu":
        return f"""
તમે જણાવેલા લક્ષણો ({', '.join(symptoms_list)}) મુખ્યત્વે **{top_condition}** જેવી સામાન્ય સ્થિતિ તરફ નિર્દેશ કરે છે.
આ લક્ષણો વાયરલ ચેપ, ઋતુ બદલાવ અથવા શારીરિક થાકને કારણે ઉદ્ભવી શકે છે. પૂરતો આરામ લેવો, ગરમ પાણી અને પ્રવાહી વધુ પીવું તેમજ પૌષ્ટિક આહાર લેવો શરીરને સ્વસ્થ થવામાં મદદ કરે છે.
**સુરક્ષા સલાહ:** આ માહિતી ફક્ત માર્ગદર્શન માટે છે. જો લક્ષણો વધુ સમય સુધી ચાલુ રહે અથવા તકલીફ વધે, તો સચોટ નિદાન માટે નજીકના નિષ્ણાત ડૉક્ટરની મુલાકાત લો.
        """.strip()
    else:
        return f"""
Based on the symptoms you reported ({', '.join(symptoms_list)}), the clinical pattern aligns primarily with **{top_condition}**.
These symptoms commonly occur during viral fluctuations, seasonal transitions, or transient physiological strain. In most uncomplicated instances, ensuring adequate hydration, restorative rest, and a balanced diet facilitates steady recovery.
**Important Guidance:** This assessment serves as educational triage context. If symptoms persist beyond several days or if you experience any worsening discomfort, please consult a qualified healthcare professional promptly.
        """.strip()
