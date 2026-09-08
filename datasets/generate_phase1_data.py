"""
    DocMindX AI Dataset Generator - Phase 1 Core Knowledge Base
Generates:
1. datasets/symptoms/symptoms_master.csv
2. datasets/disease/disease_master.csv
3. datasets/disease/disease_symptom_mapping.csv
4. datasets/symptoms/emergency_red_flags.csv
"""
import os
import pandas as pd

def ensure_dirs():
    os.makedirs("datasets/symptoms", exist_ok=True)
    os.makedirs("datasets/disease", exist_ok=True)
    os.makedirs("datasets/diet", exist_ok=True)
    os.makedirs("datasets/yoga", exist_ok=True)
    os.makedirs("datasets/physiotherapy", exist_ok=True)
    os.makedirs("datasets/blood_report", exist_ok=True)
    os.makedirs("datasets/medical_terms", exist_ok=True)
    os.makedirs("translations", exist_ok=True)

def generate_symptoms_master():
    symptoms = [
        # General & Constitutional
        ("S001", "Fever", "बुखार", "તાવ", "General", "Constitutional", "Moderate", 0, "Elevated body temperature above 37.5°C"),
        ("S002", "High Fever (>103°F)", "तेज़ बुखार", "ખૂબ તાવ", "General", "Constitutional", "High", 1, "Very high body temperature requiring prompt management"),
        ("S003", "Chills and Rigors", "कंपकंपी और ठंड लगना", "ઠંડી અને ધ્રુજારી", "General", "Constitutional", "Moderate", 0, "Feeling of coldness with involuntary shivering"),
        ("S004", "Fatigue & Weakness", "थकान और कमजोरी", "થાક અને નબળાઈ", "General", "Constitutional", "Low", 0, "Persistent feeling of tiredness or low energy"),
        ("S005", "Unexplained Weight Loss", "बिना कारण वजन कम होना", "અજાણતાં વજન ઘટવું", "General", "Constitutional", "Moderate", 0, "Noticeable reduction in body weight without dieting"),
        ("S006", "Night Sweats", "रात को पसीना आना", "રાત્રે પરસેવો થવો", "General", "Constitutional", "Moderate", 0, "Drenching sweating during sleep"),
        ("S007", "Loss of Appetite", "भूख न लगना", "ભૂખ ન લાગવી", "General", "Constitutional", "Low", 0, "Reduced desire to eat food"),
        ("S008", "Generalized Body Ache", "पूरे शरीर में दर्द", "આખા શરીરમાં દુખાવો", "General", "Musculoskeletal", "Low", 0, "Diffuse muscular discomfort across body"),
        ("S009", "Dizziness / Lightheadedness", "चक्कर आना", "ચક્કર આવવા", "Neurological", "Neurological", "Moderate", 0, "Sensation of unsteadiness, spinning or feeling faint"),
        
        # Respiratory System
        ("S010", "Dry Cough", "सूखी खांसी", "સૂકી ખાંસી", "Respiratory", "Respiratory", "Low", 0, "Non-productive cough without phlegm"),
        ("S011", "Productive Wet Cough", "कफ वाली खांसी", "કફ વાળી ખાંસી", "Respiratory", "Respiratory", "Moderate", 0, "Cough accompanied by mucus or sputum"),
        ("S012", "Sore Throat", "गले में खराश / दर्द", "ગળામાં દુખાવો / ખરાશ", "Respiratory", "ENT", "Low", 0, "Irritation, itchiness or pain in throat"),
        ("S013", "Shortness of Breath (Mild/Moderate)", "सांस लेने में हल्की तकलीफ", "શ્વાસ લેવામાં તકલીફ", "Respiratory", "Respiratory", "High", 0, "Difficulty or discomfort while breathing during exertion"),
        ("S014", "Severe Shortness of Breath at Rest", "आराम करते समय भी गंभीर सांस फूलना", "આરામમાં પણ ગંભીર શ્વાસ ચઢવો", "Respiratory", "Respiratory", "Emergency", 1, "Sudden severe respiratory distress at rest"),
        ("S015", "Runny Nose / Rhinorrhea", "नाक बहना", "નાક વહેવું", "Respiratory", "ENT", "Low", 0, "Excess nasal discharge/mucus"),
        ("S016", "Nasal Congestion / Blocked Nose", "नाक बंद होना", "નાક બંધ થવું", "Respiratory", "ENT", "Low", 0, "Stuffy feeling caused by swollen nasal membranes"),
        ("S017", "Sneezing", "छींक आना", "છીંક આવવી", "Respiratory", "ENT", "Low", 0, "Involuntary convulsive expulsions of air from nose"),
        ("S018", "Wheezing Sound in Chest", "छाती में सीटी जैसी आवाज", "છાતીમાં સીટી જેવો અવાજ", "Respiratory", "Respiratory", "Moderate", 0, "High-pitched whistling sound during breathing"),
        ("S019", "Coughing up Blood (Hemoptysis)", "खांसी में खून आना", "ખાંસીમાં લોહી આવવું", "Respiratory", "Respiratory", "Emergency", 1, "Expectorating blood or blood-tinged sputum"),
        ("S020", "Loss of Smell (Anosmia)", "सूंघने की शक्ति जाना", "સુગંધ ન આવવી", "Respiratory", "ENT", "Low", 0, "Partial or complete loss of sense of smell"),
        ("S021", "Loss of Taste (Ageusia)", "स्वाद न आना", "સ્વાદ ન આવવો", "Respiratory", "ENT", "Low", 0, "Inability to perceive sweet, sour, bitter or salty tastes"),

        # Cardiovascular System
        ("S022", "Severe Crushing Chest Pain", "छाती में तीव्र भारीपन या असहनीय दर्द", "છાતીમાં તીવ્ર દબાણ કે અસહ્ય દુખાવો", "Cardiovascular", "Cardiovascular", "Emergency", 1, "Heavy pressure, squeezing pain in center of chest possibly radiating to arm or jaw"),
        ("S023", "Mild Chest Discomfort / Heartburn", "हल्की छाती में जलन / एसिडिटी", "છાતીમાં બળતરા / એસિડિટી", "Cardiovascular", "Gastrointestinal", "Low", 0, "Burning sensation in upper chest related to meals"),
        ("S024", "Palpitations / Rapid Heartbeat", "दिल की धड़कन तेज होना", "હૃદયના ધબકારા વધવા", "Cardiovascular", "Cardiovascular", "Moderate", 0, "Sensation of pounding, fluttering or rapid pulse"),
        ("S025", "Swelling in Feet / Ankles (Edema)", "पैरों या टखनों में सूजन", "પગ કે ઘૂંટીમાં સોજો", "Cardiovascular", "Cardiovascular", "Moderate", 0, "Fluid retention causing swelling in lower extremities"),
        ("S026", "Cold Sweats with Chest Tightness", "छाती में खिंचाव के साथ ठंडा पसीना", "છાતીમાં ખેંચાણ સાથે ઠંડો પરસેવો", "Cardiovascular", "Cardiovascular", "Emergency", 1, "Profuse cold perspiration accompanied by chest pressure"),

        # Neurological & Head
        ("S027", "Mild to Moderate Headache", "सिरदर्द", "માથાનો દુખાવો", "Neurological", "Neurological", "Low", 0, "Aching discomfort in cranial region"),
        ("S028", "Sudden Worst Headache of Life (Thunderclap)", "अचानक असहनीय भयंकर सिरदर्द", "અચાનક અત્યંત તીવ્ર માથાનો દુખાવો", "Neurological", "Neurological", "Emergency", 1, "Abrupt onset of excruciating headache peaking within seconds"),
        ("S029", "One-Sided Facial Droop / Weakness", "चेहरे का एक तरफ झुकना या कमजोरी", "મોંનું એક તરફ વળી જવું કે નબળાઈ", "Neurological", "Neurological", "Emergency", 1, "Acute facial asymmetry or loss of muscle control on one side (Stroke sign)"),
        ("S030", "Arm / Leg Weakness on One Side", "एक तरफ के हाथ या पैर में अचानक कमजोरी", "એક તરફના હાથ કે પગમાં અચાનક નબળાઈ", "Neurological", "Neurological", "Emergency", 1, "Sudden hemiparesis or inability to raise one arm (Stroke sign)"),
        ("S031", "Slurred Speech / Difficulty Speaking", "बोलने में लड़खड़ाहट या शब्द न निकलना", "બોલવામાં જીભ લથડવી કે શબ્દો ન નીકળવા", "Neurological", "Neurological", "Emergency", 1, "Acute dysarthria or aphasia (Stroke sign)"),
        ("S032", "Loss of Consciousness / Fainting (Syncope)", "बेहोशी या चक्कर खाकर गिरना", "બેભાન થઈ જવું કે ચક્કર આવીને પડી જવું", "Neurological", "Neurological", "Emergency", 1, "Transient loss of consciousness and postural tone"),
        ("S033", "Seizures / Fits / Convulsions", "दौरे पड़ना / मिरगी", "આંચકી / ખેંચ આવવી", "Neurological", "Neurological", "Emergency", 1, "Sudden uncontrollable muscle spasms and jerking"),
        ("S034", "Stiff Neck with High Fever and Photophobia", "गर्दन में तेज अकड़न, बुखार और रोशनी से तकलीफ", "ડોકમાં અકડાઈ, તાવ અને પ્રકાશથી આંખો અંજાવી", "Neurological", "Neurological", "Emergency", 1, "Meningeal irritation signs (suspected meningitis)"),
        ("S035", "Tremors / Shaking Hands", "हाथों में कंपन", "હાથ ધ્રૂજવા", "Neurological", "Neurological", "Moderate", 0, "Involuntary rhythmic muscle contraction in hands"),
        ("S036", "Numbness or Tingling in Hands/Feet", "हाथ-पैरों में सुन्नपन या झनझनाहट", "હાથ-પગમાં ખાલી ચડવી કે ઝણઝણાટી", "Neurological", "Neurological", "Low", 0, "Paresthesia, pins and needles sensation in extremities"),

        # Gastrointestinal System
        ("S037", "Nausea", "जी मिचलाना", "ઉબકા આવવા", "Gastrointestinal", "Gastrointestinal", "Low", 0, "Uneasy feeling in stomach with urge to vomit"),
        ("S038", "Vomiting", "उल्टी होना", "ઉલ્ટી થવી", "Gastrointestinal", "Gastrointestinal", "Moderate", 0, "Forceful expulsion of stomach contents"),
        ("S039", "Frequent Watery Diarrhea", "बार-बार दस्त / पतले दस्त", "વારંવાર પાતળા ઝાડા", "Gastrointestinal", "Gastrointestinal", "Moderate", 0, "Loose, liquid bowel movements more than 3 times a day"),
        ("S040", "Severe Abdominal Pain", "पेट में असहनीय या तेज दर्द", "પેટમાં અસહ્ય કે તીવ્ર દુખાવો", "Gastrointestinal", "Gastrointestinal", "High", 0, "Acute severe pain localized or generalized in abdomen"),
        ("S041", "Constipation", "कब्ज", "કબજિયાત", "Gastrointestinal", "Gastrointestinal", "Low", 0, "Infrequent or difficult bowel evacuation"),
        ("S042", "Abdominal Bloating & Gas", "पेट फूलना और गैस", "પેટ ફૂલવું અને ગેસ", "Gastrointestinal", "Gastrointestinal", "Low", 0, "Feeling of fullness or distension in abdomen"),
        ("S043", "Acidity & Burning in Stomach", "पेट में जलन और खट्टी डकारें", "પેટમાં બળતરા અને ખાટા ઓડકાર", "Gastrointestinal", "Gastrointestinal", "Low", 0, "Hyperacidity and epigastric discomfort"),
        ("S044", "Yellowish Skin and Eyes (Jaundice)", "आंखों और त्वचा का पीला पड़ना (पीलिया)", "આંખો અને ચામડી પીળી થવી (કમળો)", "Gastrointestinal", "Hepatic", "High", 0, "Icterus indicating elevated bilirubin / liver issue"),
        ("S045", "Black Tarry Stool / Blood in Stool", "मल में खून या काला मल", "ઝાડામાં લોહી કે કાળો મળ", "Gastrointestinal", "Gastrointestinal", "Emergency", 1, "Melena or hematochezia indicating gastrointestinal bleeding"),
        ("S046", "Severe Dehydration (Dry Mouth, sunken eyes)", "गंभीर निर्जलीकरण / सूखा मुंह और प्यास", "ગંભીર ડીહાઈડ્રેશન / સૂકું મોં અને અત્યંત તરસ", "Gastrointestinal", "Constitutional", "High", 0, "Severe loss of body water requiring urgent rehydration"),

        # Musculoskeletal & Joint
        ("S047", "Joint Pain (Knee, Wrist, etc.)", "जोड़ों में दर्द", "સાંધાનો દુખાવો", "Musculoskeletal", "Musculoskeletal", "Low", 0, "Arthralgia in single or multiple joints"),
        ("S048", "Joint Swelling, Redness & Warmth", "जोड़ों में सूजन, लाली और गर्माहट", "સાંધામાં સોજો, લાલાશ અને ગરમી", "Musculoskeletal", "Musculoskeletal", "Moderate", 0, "Active arthritis or inflammation in joints"),
        ("S049", "Lower Back Pain", "कमर / पीठ के निचले हिस्से में दर्द", "કમરનો / પીઠનો દુખાવો", "Musculoskeletal", "Musculoskeletal", "Low", 0, "Lumbago, muscular strain or disc related back pain"),
        ("S050", "Neck Stiffness & Muscle Spasm", "गर्दन में जकड़न और दर्द", "ડોકમાં અકડાઈ અને દુખાવો", "Musculoskeletal", "Musculoskeletal", "Low", 0, "Cervical muscle tightness or postural strain"),
        ("S051", "Morning Joint Stiffness > 30 mins", "सुबह उठने पर जोड़ों में 30 मिनट से ज्यादा जकड़न", "સવારે સાંધામાં 30 મિનિટથી વધુ અકડાઈ", "Musculoskeletal", "Musculoskeletal", "Moderate", 0, "Prolonged morning stiffness suggestive of inflammatory arthritis"),

        # Skin & Allergies
        ("S052", "Skin Rash / Red Patches", "त्वचा पर लाल चकत्ते / दाने", "ચામડી પર લાલ ચકામા / ફોલ્લીઓ", "Dermatological", "Dermatological", "Low", 0, "Erythematous eruption or lesions on skin"),
        ("S053", "Severe Itching (Pruritus)", "तेज खुजली", "તીવ્ર ખંજવાળ", "Dermatological", "Dermatological", "Low", 0, "Intense desire to scratch skin"),
        ("S054", "Sudden Swelling of Lips, Tongue or Throat (Anaphylaxis)", "होठों, जीभ या गले में अचानक तेज सूजन", "હોઠ, જીભ કે ગળામાં અચાનક સોજો", "Dermatological", "Immunological", "Emergency", 1, "Angioedema and anaphylactic risk with airway threat"),
        ("S055", "Hives / Wheals (Urticaria)", "पित्ती / शरीर पर उभरे हुए लाल निशान", "શીળસ / શરીર પર લાલ ઊપસેલા ડાઘ", "Dermatological", "Immunological", "Moderate", 0, "Transient itchy wheals and flares on skin"),

        # Urinary & Renal
        ("S056", "Burning Sensation During Urination (Dysuria)", "पेशाब में जलन", "પેશાબમાં બળતરા", "Urinary", "Urinary", "Moderate", 0, "Painful or stinging micturition suggestive of UTI"),
        ("S057", "Frequent Urination (Day and Night)", "बार-बार पेशाब आना", "વારંવાર પેશાબ જવું", "Urinary", "Urinary", "Low", 0, "Increased frequency of urination"),
        ("S058", "Blood in Urine (Hematuria)", "पेशाब में खून आना", "પેશાબમાં લોહી આવવું", "Urinary", "Urinary", "High", 0, "Red or tea-colored urine indicating urinary tract bleeding"),
        ("S059", "Inability to Pass Urine (Urinary Retention)", "पेशाब बिल्कुल न उतरना / बंद होना", "પેશાબ સાવ બંધ થઈ જવો", "Urinary", "Urinary", "Emergency", 1, "Acute urinary retention causing painful bladder distension"),
        ("S060", "Severe Flank / Side Back Pain Radiating to Groin", "कमर के किनारे से पेट के निचले भाग में असहनीय दर्द", "કમરની બાજુમાંથી પેડુ તરફ જતો તીવ્ર દુખાવો", "Urinary", "Urinary", "High", 0, "Colicky flank pain characteristic of renal calculus / kidney stone"),

        # Endocrine & Metabolic
        ("S061", "Excessive Thirst (Polydipsia)", "अत्यधिक प्यास लगना", "ખૂબ તરસ લાગવી", "Endocrine", "Endocrine", "Low", 0, "Abnormally intense and persistent thirst"),
        ("S062", "Excessive Hunger (Polyphagia)", "बहुत ज्यादा भूख लगना", "ખૂબ ભૂખ લાગવી", "Endocrine", "Endocrine", "Low", 0, "Increased appetite and food craving"),
        ("S063", "Cold Intolerance & Dry Skin", "ठंड बर्दाश्त न होना और रूखी त्वचा", "ઠંડી સહન ન થવી અને સૂકી ત્વચા", "Endocrine", "Endocrine", "Low", 0, "Sensitivity to cold environments suggestive of hypothyroidism"),
        ("S064", "Heat Intolerance & Excessive Sweating", "गर्मी बर्दाश्त न होना और अत्यधिक पसीना", "ગરમી સહન ન થવી અને વધુ પડતો પરસેવો", "Endocrine", "Endocrine", "Low", 0, "Hyper-metabolic symptoms suggestive of hyperthyroidism"),

        # Eye & Ear
        ("S065", "Redness and Discharge in Eyes (Conjunctivitis)", "आंखों में लाली और कीचड़ / पानी", "આંખો લાલ થવી અને ચીકાશ / પાણી", "Sensory", "Ophthalmic", "Low", 0, "Inflammation of conjunctiva with pinkish hue and discharge"),
        ("S066", "Sudden Loss of Vision or Severe Eye Pain", "अचानक रोशनी जाना या आंख में तेज दर्द", "અચાનક દ્રષ્ટિ ગુમાવવી કે આંખમાં તીવ્ર દુખાવો", "Sensory", "Ophthalmic", "Emergency", 1, "Acute vision impairment or acute glaucoma symptom"),
        ("S067", "Earache / Discharge from Ear", "कान में दर्द या मवाद बहना", "કાનમાં દુખાવો કે પરુ વહેવું", "Sensory", "ENT", "Low", 0, "Otitis media or external ear canal inflammation"),
        
        # Mental Health & Sleep
        ("S068", "Insomnia / Difficulty Sleeping", "नींद न आना / अनिद्रा", "ઊંઘ ન આવવી / અનિદ્રા", "Psychological", "Psychological", "Low", 0, "Persistent problems falling and staying asleep"),
        ("S069", "Excessive Anxiety / Panic Attacks", "अत्यधिक घबराहट और बेचैनी", "અતિશય ગભરામણ અને બેચેની", "Psychological", "Psychological", "Moderate", 0, "Acute episodes of overwhelming anxiety and physical tension")
    ]
    
    df = pd.DataFrame(symptoms, columns=[
        "symptom_id", "symptom_name", "symptom_name_hi", "symptom_name_gu",
        "body_system", "symptom_category", "severity_level", "emergency_flag", "description"
    ])
    df["source"] = "WHO ICD-11 & MedlinePlus Clinical Taxonomy"
    df.to_csv("datasets/symptoms/symptoms_master.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df)} primary master symptoms in datasets/symptoms/symptoms_master.csv")

def generate_disease_master():
    diseases = [
        ("D001", "Common Cold / Viral Rhinitis", "सामान्य सर्दी-जुकाम / वायरल राइनिटिस", "સામાન્ય શરદી-સળેખમ", "J00", "Respiratory", "Mild viral infection of upper respiratory tract", "Respiratory"),
        ("D002", "Influenza (Flu)", "इन्फ्लूएंजा (फ्लू)", "ઇન્ફલ્યુએન્ઝા (ફ્લૂ)", "J10", "Infectious", "Acute contagious viral infection with high fever and muscle aches", "Respiratory"),
        ("D003", "Acute Bronchitis", "एक्यूट ब्रोंकाइटिस", "એક્યુટ બ્રોન્કાઇટિસ", "J20", "Respiratory", "Inflammation of bronchial airway tubes causing cough and mucus", "Respiratory"),
        ("D004", "Pneumonia", "निमोनिया", "ન્યુમોનિયા", "J18", "Respiratory", "Infection inflaming air sacs in one or both lungs with fluid/pus", "Respiratory"),
        ("D005", "Bronchial Asthma (Exacerbation)", "दमा / अस्थमा", "દમ / અસ્થમા", "J45", "Respiratory", "Chronic inflammatory disorder of airways causing wheezing and dyspnea", "Respiratory"),
        ("D006", "Acute Viral Gastroenteritis (Stomach Flu)", "पेट का वायरल संक्रमण / गैस्ट्रोएंटेराइटिस", "પેટનો વાયરલ ચેપ / ઝાડા-ઉલ્ટી", "A08", "Gastrointestinal", "Inflammation of stomach and intestines leading to diarrhea and vomiting", "Gastrointestinal"),
        ("D007", "Gastroesophageal Reflux Disease (GERD / Acidity)", "एसिडिटी / जीईआरडी", "એસિડિટી / જીઈઆરડી", "K21", "Gastrointestinal", "Stomach acid repeatedly flowing back into the esophagus", "Gastrointestinal"),
        ("D008", "Peptic Ulcer Disease", "पेट का छाला / अल्सर", "પેટનું ચાંદું / અલ્સર", "K27", "Gastrointestinal", "Sores developing on the lining of stomach, lower esophagus or small intestine", "Gastrointestinal"),
        ("D009", "Acute Appendicitis", "अपेंडिसाइटिस", "એપેન્ડીસાઈટિસ", "K35", "Gastrointestinal", "Acute inflammation of the appendix requiring prompt surgical evaluation", "Gastrointestinal"),
        ("D010", "Acute Viral Hepatitis / Jaundice", "वायरल हेपेटाइटिस / पीलिया", "વાયરલ હિપેટાઇટિસ / કમળો", "B15", "Hepatic", "Liver inflammation caused by viral infection causing yellow discoloration", "Hepatic"),
        ("D011", "Urinary Tract Infection (UTI / Cystitis)", "मूत्र मार्ग संक्रमण (यूटीआई)", "પેશાબનો ચેપ (યુટીઆઈ)", "N39.0", "Urinary", "Bacterial infection in kidneys, ureters, bladder or urethra", "Urinary"),
        ("D012", "Renal Calculi (Kidney Stones)", "गुर्दे की पथरी (किडनी स्टोन)", "કિડનીની પથરી", "N20", "Urinary", "Hard mineral deposits formed inside kidneys causing severe colicky pain", "Urinary"),
        ("D013", "Hypertension (High Blood Pressure)", "उच्च रक्तचाप (हाई बीपी)", "હાઈ બ્લડ પ્રેશર (હાઈ બીપી)", "I10", "Cardiovascular", "Long-term medical condition in which blood pressure in arteries is persistently elevated", "Cardiovascular"),
        ("D014", "Acute Coronary Syndrome / Myocardial Infarction", "दिल का दौरा / हार्ट अटैक", "હૃદયરોગનો હુમલો / હાર્ટ એટેક", "I21", "Cardiovascular", "Critical reduction of blood flow to heart muscle requiring immediate emergency care", "Cardiovascular"),
        ("D015", "Congestive Heart Failure", "हार्ट फेलियर / दिल की कमजोरी", "હાર્ટ ફેલિયર", "I50", "Cardiovascular", "Chronic condition where heart does not pump blood as well as it should", "Cardiovascular"),
        ("D016", "Acute Ischemic Stroke / Cerebrovascular Accident", "ब्रेन स्ट्रोक / लकवा", "બ્રેઇન સ્ટ્રોક / લકવો", "I63", "Neurological", "Interruption of blood supply to brain causing sudden focal neurological deficits", "Neurological"),
        ("D017", "Migraine Headache", "माइग्रेन / आधासीसी का सिरदर्द", "આધાશીશી / માઇગ્રેન", "G43", "Neurological", "Recurrent pulsating headache disorder often accompanied by nausea and light sensitivity", "Neurological"),
        ("D018", "Tension Type Headache", "तनाव सिरदर्द", "ટેન્શન માથાનો દુખાવો", "G44.2", "Neurological", "Diffuse, mild to moderate aching pain in head associated with muscle contraction", "Neurological"),
        ("D019", "Acute Meningitis", "मेनिनजाइटिस (दिमागी बुखार)", "મેનિન્જાઇટિસ (મગજનો તાવ)", "G03", "Neurological", "Inflammation of protective membranes covering brain and spinal cord", "Neurological"),
        ("D020", "Type 2 Diabetes Mellitus (Hyperglycemia)", "टाइप 2 मधुमेह (शुगर की बीमारी)", "ટાઇપ 2 ડાયાબિટીસ (શુગર)", "E11", "Endocrine", "Metabolic disorder characterized by elevated blood glucose and insulin resistance", "Endocrine"),
        ("D021", "Hypothyroidism", "हाइपोथायरायडिज्म (थायराइड की कमी)", "હાઇપોથાઇરોઇડિઝમ", "E03.9", "Endocrine", "Underactive thyroid gland failing to produce enough thyroid hormones", "Endocrine"),
        ("D022", "Hyperthyroidism", "हाइपरथायरायडिज्म", "હાઇપરથાઇરોઇડિઝમ", "E05.9", "Endocrine", "Overactive thyroid gland producing excessive thyroid hormones", "Endocrine"),
        ("D023", "Osteoarthritis / Degenerative Joint Disease", "ऑस्टियोआर्थराइटिस (जोड़ों का घिसना)", "ઓસ્ટિઓઆર્થરાઇટિસ (સાંધાનો ઘસારો)", "M19", "Musculoskeletal", "Degenerative wear and tear of protective cartilage cushioning joint bones", "Musculoskeletal"),
        ("D024", "Rheumatoid Arthritis", "रुमेटॉइड आर्थराइटिस (गठिया)", "સંધિવા / રૂમેટોઇડ આર્થરાઇટિસ", "M06.9", "Musculoskeletal", "Autoimmune chronic inflammatory disorder affecting joints symmetrically", "Musculoskeletal"),
        ("D025", "Acute Lumbar Muscle Strain (Back Pain)", "कमर में मोच / खिंचाव", "કમરનો દુખાવો / સ્નાયુ ખેંચાણ", "M54.5", "Musculoskeletal", "Stretching or tearing of lumbar muscle or ligament fibers from strain", "Musculoskeletal"),
        ("D026", "Allergic Rhinitis (Seasonal Allergies)", "एलर्जी राइनाइटिस (मौसमी एलर्जी)", "એલર્જીક રહાઈનાઇટિસ (મોસમી એલર્જી)", "J30.1", "Immunological", "Allergic reaction in nose to airborne particles like pollen, dust or pet dander", "Respiratory"),
        ("D027", "Acute Anaphylaxis / Severe Allergy", "एनाफिलेक्सिस (गंभीर एलर्जी अटैक)", "એનાફિલેક્સિસ (ગંભીર એલર્જીક હુમલો)", "T78.2", "Immunological", "Severe, life-threatening generalized allergic reaction requiring instant epinephrine", "Immunological"),
        ("D028", "Dengue Fever", "डेंगू बुखार", "ડેન્ગ્યુ તાવ", "A90", "Infectious", "Mosquito-borne viral infection causing high fever, severe headache, retro-orbital pain and body aches", "Infectious"),
        ("D029", "Malaria", "मलेरिया", "મેલેરિયા", "B54", "Infectious", "Parasitic infection transmitted by female Anopheles mosquitoes with cyclical chills and fever", "Infectious"),
        ("D030", "Typhoid Fever (Enteric Fever)", "टाइफाइड (मियादी बुखार)", "ટાઇફોઇડ તાવ", "A01.0", "Infectious", "Systemic bacterial infection caused by Salmonella Typhi with step-ladder fever and GI symptoms", "Infectious")
    ]
    df = pd.DataFrame(diseases, columns=[
        "disease_id", "disease_name", "disease_name_hi", "disease_name_gu",
        "icd_code", "category", "description", "body_system"
    ])
    df["source"] = "WHO International Classification of Diseases (ICD-11/10)"
    df.to_csv("datasets/disease/disease_master.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df)} curated master diseases in datasets/disease/disease_master.csv")

def generate_disease_symptom_mapping():
    mappings = [
        # D001: Common Cold
        ("D001", "S010", 8, "No"),  # Dry cough
        ("D001", "S012", 9, "Yes"), # Sore throat
        ("D001", "S015", 10, "Yes"),# Runny nose
        ("D001", "S016", 9, "No"),  # Blocked nose
        ("D001", "S017", 9, "No"),  # Sneezing
        ("D001", "S001", 5, "No"),  # Mild fever
        ("D001", "S027", 5, "No"),  # Headache

        # D002: Flu
        ("D002", "S001", 10, "Yes"), # High fever
        ("D002", "S003", 9, "No"),   # Chills
        ("D002", "S008", 10, "Yes"), # Body ache
        ("D002", "S004", 9, "Yes"),  # Fatigue
        ("D002", "S010", 8, "No"),   # Dry cough
        ("D002", "S012", 7, "No"),   # Sore throat
        ("D002", "S027", 8, "No"),   # Headache

        # D003: Acute Bronchitis
        ("D003", "S011", 10, "Yes"), # Productive cough
        ("D003", "S018", 7, "No"),   # Wheezing
        ("D003", "S012", 6, "No"),   # Sore throat
        ("D003", "S001", 6, "No"),   # Low fever
        ("D003", "S004", 7, "No"),   # Fatigue

        # D004: Pneumonia
        ("D004", "S002", 10, "Yes"), # High fever
        ("D004", "S011", 9, "Yes"),  # Productive cough
        ("D004", "S013", 9, "Yes"),  # Shortness of breath
        ("D004", "S003", 8, "No"),   # Chills
        ("D004", "S004", 9, "No"),   # Fatigue
        ("D004", "S019", 7, "No"),   # Hemoptysis (emergency)

        # D005: Asthma
        ("D005", "S013", 10, "Yes"), # Shortness of breath
        ("D005", "S018", 10, "Yes"), # Wheezing
        ("D005", "S010", 8, "No"),   # Dry cough
        ("D005", "S023", 5, "No"),   # Chest tightness

        # D006: Gastroenteritis
        ("D006", "S039", 10, "Yes"), # Diarrhea
        ("D006", "S038", 9, "Yes"),  # Vomiting
        ("D006", "S037", 8, "No"),   # Nausea
        ("D006", "S040", 7, "No"),   # Abdominal pain
        ("D006", "S001", 6, "No"),   # Fever
        ("D006", "S046", 8, "No"),   # Dehydration

        # D007: GERD
        ("D007", "S023", 10, "Yes"), # Heartburn
        ("D007", "S043", 10, "Yes"), # Acidity
        ("D007", "S042", 7, "No"),   # Bloating
        ("D007", "S037", 6, "No"),   # Nausea
        ("D007", "S010", 5, "No"),   # Chronic cough

        # D008: Peptic Ulcer
        ("D008", "S040", 9, "Yes"),  # Abdominal pain
        ("D008", "S043", 9, "Yes"),  # Burning stomach
        ("D008", "S037", 7, "No"),   # Nausea
        ("D008", "S007", 6, "No"),   # Loss of appetite
        ("D008", "S045", 8, "No"),   # Black stool

        # D009: Appendicitis
        ("D009", "S040", 10, "Yes"), # Severe abdominal pain
        ("D009", "S037", 8, "Yes"),  # Nausea
        ("D009", "S038", 8, "No"),   # Vomiting
        ("D009", "S001", 7, "No"),   # Fever
        ("D009", "S007", 8, "No"),   # Loss of appetite

        # D010: Viral Hepatitis
        ("D010", "S044", 10, "Yes"), # Jaundice (yellow eyes/skin)
        ("D010", "S004", 9, "Yes"),  # Fatigue
        ("D010", "S007", 9, "Yes"),  # Loss of appetite
        ("D010", "S037", 8, "No"),   # Nausea
        ("D010", "S040", 7, "No"),   # Right upper abdominal discomfort
        ("D010", "S001", 6, "No"),   # Low fever

        # D011: UTI
        ("D011", "S056", 10, "Yes"), # Burning urination
        ("D011", "S057", 9, "Yes"),  # Frequent urination
        ("D011", "S001", 6, "No"),   # Fever
        ("D011", "S040", 6, "No"),   # Lower abdominal pain
        ("D011", "S058", 7, "No"),   # Hematuria

        # D012: Kidney Stone
        ("D012", "S060", 10, "Yes"), # Flank pain radiating to groin
        ("D012", "S056", 7, "No"),   # Burning urination
        ("D012", "S058", 8, "No"),   # Blood in urine
        ("D012", "S037", 7, "No"),   # Nausea
        ("D012", "S038", 7, "No"),   # Vomiting

        # D013: Hypertension
        ("D013", "S027", 8, "No"),   # Occipital headache
        ("D013", "S009", 7, "No"),   # Dizziness
        ("D013", "S024", 6, "No"),   # Palpitations
        ("D013", "S004", 5, "No"),   # Fatigue

        # D014: Acute Coronary Syndrome (Heart Attack)
        ("D014", "S022", 10, "Yes"), # Crushing chest pain
        ("D014", "S026", 10, "Yes"), # Cold sweats with chest tightness
        ("D014", "S014", 9, "No"),   # Shortness of breath
        ("D014", "S024", 8, "No"),   # Palpitations
        ("D014", "S009", 7, "No"),   # Dizziness / fainting

        # D015: Heart Failure
        ("D015", "S013", 10, "Yes"), # Dyspnea on exertion / orthopnea
        ("D015", "S025", 10, "Yes"), # Swelling in feet / ankles
        ("D015", "S004", 9, "Yes"),  # Fatigue
        ("D015", "S010", 6, "No"),   # Nocturnal cough

        # D016: Stroke
        ("D016", "S029", 10, "Yes"), # Facial droop
        ("D016", "S030", 10, "Yes"), # One-sided arm/leg weakness
        ("D016", "S031", 10, "Yes"), # Slurred speech
        ("D016", "S028", 8, "No"),   # Sudden severe headache
        ("D016", "S009", 7, "No"),   # Severe unsteadiness

        # D017: Migraine
        ("D017", "S027", 10, "Yes"), # Throbbing headache
        ("D017", "S037", 8, "Yes"),  # Nausea
        ("D017", "S009", 6, "No"),   # Dizziness
        ("D017", "S068", 6, "No"),   # Sleep disturbance

        # D018: Tension Headache
        ("D018", "S027", 10, "Yes"), # Dull ache
        ("D018", "S050", 8, "No"),   # Neck stiffness / strain
        ("D018", "S004", 6, "No"),   # Fatigue

        # D019: Meningitis
        ("D019", "S034", 10, "Yes"), # Stiff neck with high fever
        ("D019", "S002", 10, "Yes"), # High fever
        ("D019", "S028", 9, "Yes"),  # Severe headache
        ("D019", "S038", 8, "No"),   # Vomiting
        ("D019", "S032", 8, "No"),   # Altered mental status / fainting

        # D020: Type 2 Diabetes
        ("D020", "S061", 10, "Yes"), # Polydipsia (thirst)
        ("D020", "S057", 9, "Yes"),  # Frequent urination
        ("D020", "S062", 8, "No"),   # Polyphagia (hunger)
        ("D020", "S004", 8, "No"),   # Fatigue
        ("D020", "S005", 7, "No"),   # Weight loss
        ("D020", "S036", 7, "No"),   # Tingling in feet

        # D021: Hypothyroidism
        ("D021", "S063", 10, "Yes"), # Cold intolerance & dry skin
        ("D021", "S004", 9, "Yes"),  # Fatigue
        ("D021", "S041", 8, "No"),   # Constipation
        ("D021", "S008", 6, "No"),   # Muscle aches

        # D022: Hyperthyroidism
        ("D022", "S064", 10, "Yes"), # Heat intolerance
        ("D022", "S005", 9, "Yes"),  # Weight loss
        ("D022", "S024", 9, "Yes"),  # Palpitations
        ("D022", "S035", 8, "No"),   # Hand tremors
        ("D022", "S069", 7, "No"),   # Anxiety

        # D023: Osteoarthritis
        ("D023", "S047", 10, "Yes"), # Joint pain
        ("D023", "S048", 7, "No"),   # Joint swelling
        ("D023", "S051", 6, "No"),   # Mild stiffness

        # D024: Rheumatoid Arthritis
        ("D024", "S048", 10, "Yes"), # Symmetrical joint swelling
        ("D024", "S051", 10, "Yes"), # Morning stiffness > 30 mins
        ("D024", "S047", 9, "Yes"),  # Joint pain
        ("D024", "S004", 8, "No"),   # Fatigue
        ("D024", "S001", 6, "No"),   # Low fever

        # D025: Lumbar Strain
        ("D025", "S049", 10, "Yes"), # Lower back pain
        ("D025", "S008", 6, "No"),   # Muscle ache

        # D026: Allergic Rhinitis
        ("D026", "S017", 10, "Yes"), # Sneezing
        ("D026", "S015", 9, "Yes"),  # Runny nose
        ("D026", "S016", 8, "No"),   # Blocked nose
        ("D026", "S053", 7, "No"),   # Itching eyes/nose
        ("D026", "S065", 6, "No"),   # Conjunctival redness

        # D027: Anaphylaxis
        ("D027", "S054", 10, "Yes"), # Swelling of lips/tongue
        ("D027", "S014", 10, "Yes"), # Severe respiratory distress
        ("D027", "S055", 9, "Yes"),  # Generalized hives
        ("D027", "S009", 8, "No"),   # Dizziness / shock

        # D028: Dengue Fever
        ("D028", "S002", 10, "Yes"), # High fever
        ("D028", "S008", 10, "Yes"), # Severe breakbone body pain
        ("D028", "S027", 9, "Yes"),  # Retro-orbital / severe headache
        ("D028", "S052", 8, "No"),   # Petechial rash
        ("D028", "S037", 7, "No"),   # Nausea

        # D029: Malaria
        ("D029", "S003", 10, "Yes"), # Shivering chills & rigors
        ("D029", "S002", 10, "Yes"), # High fever spikes
        ("D029", "S006", 9, "Yes"),  # Profuse sweating
        ("D029", "S027", 8, "No"),   # Headache
        ("D029", "S037", 7, "No"),   # Nausea

        # D030: Typhoid
        ("D030", "S001", 10, "Yes"), # Step-ladder fever
        ("D030", "S027", 8, "Yes"),  # Headache
        ("D030", "S040", 8, "No"),   # Abdominal pain
        ("D030", "S004", 8, "No"),   # Severe weakness
        ("D030", "S041", 6, "No"),   # Constipation or pea-soup diarrhea
    ]
    df = pd.DataFrame(mappings, columns=["disease_id", "symptom_id", "weight", "required"])
    df.to_csv("datasets/disease/disease_symptom_mapping.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df)} weighted mappings in datasets/disease/disease_symptom_mapping.csv")

def generate_emergency_red_flags():
    red_flags = [
        ("RF001", "S022", "Severe Crushing Chest Pain", "Cardiac / Acute Coronary Syndrome", "Critical", "Immediate emergency evaluation at nearest hospital with ECG and cardiac resuscitation facility.", "Panel 3 Hospital Navigation"),
        ("RF002", "S014", "Severe Shortness of Breath at Rest", "Acute Respiratory Failure / Severe Asthma", "Critical", "Immediate supplemental oxygen and emergency medical assistance required.", "Panel 3 Hospital Navigation"),
        ("RF003", "S029", "One-Sided Facial Droop / Weakness", "Acute Cerebrovascular Stroke (FAST Sign)", "Critical", "Call emergency ambulance immediately. Golden hour thrombolysis window applies.", "Panel 3 Hospital Navigation"),
        ("RF004", "S030", "Arm / Leg Weakness on One Side", "Acute Cerebrovascular Stroke (FAST Sign)", "Critical", "Immediate hospital transfer for urgent brain CT/MRI evaluation.", "Panel 3 Hospital Navigation"),
        ("RF005", "S031", "Slurred Speech / Sudden Inability to Speak", "Acute Cerebrovascular Stroke (FAST Sign)", "Critical", "Immediate neurological emergency transfer.", "Panel 3 Hospital Navigation"),
        ("RF006", "S032", "Loss of Consciousness / Unresponsive", "Syncope / Neurological / Cardiovascular Collapse", "Critical", "Check airway and responsiveness, place in recovery position, urgent medical aid.", "Panel 3 Hospital Navigation"),
        ("RF007", "S033", "Active Seizures / Convulsions", "Status Epilepticus / Severe Neurological Episode", "Critical", "Protect head from trauma, do not insert anything in mouth, emergency transfer.", "Panel 3 Hospital Navigation"),
        ("RF008", "S034", "Stiff Neck with High Fever and Photophobia", "Acute Bacterial Meningitis", "Critical", "Urgent hospitalization for lumbar puncture and intravenous antimicrobial therapy.", "Panel 3 Hospital Navigation"),
        ("RF009", "S054", "Sudden Swelling of Lips, Tongue or Throat", "Severe Anaphylaxis / Airway Compromise", "Critical", "Urgent emergency room care; intramuscular epinephrine may be indicated.", "Panel 3 Hospital Navigation"),
        ("RF010", "S019", "Coughing up Significant Blood (Hemoptysis)", "Pulmonary Embolism / Cavitary Lung Disease", "Critical", "Immediate hospital evaluation for respiratory stabilization.", "Panel 3 Hospital Navigation"),
        ("RF011", "S045", "Black Tarry Stool or Vomiting Blood", "Acute Upper Gastrointestinal Hemorrhage", "Critical", "Urgent gastrointestinal evaluation, blood grouping and IV access.", "Panel 3 Hospital Navigation"),
        ("RF012", "S059", "Complete Inability to Pass Urine", "Acute Urinary Retention", "Critical", "Urgent hospital / clinic visit for bladder decompression and catheterization.", "Panel 3 Hospital Navigation"),
        ("RF013", "S066", "Sudden Loss of Vision or Acute Eye Pain", "Acute Angle-Closure Glaucoma / Retinal Detachment", "Critical", "Immediate ophthalmology emergency evaluation to prevent permanent vision loss.", "Panel 3 Hospital Navigation")
    ]
    df = pd.DataFrame(red_flags, columns=[
        "flag_id", "symptom_id", "symptom_name", "risk_category", "severity_tier", "immediate_action_protocol", "redirection_target"
    ])
    df.to_csv("datasets/symptoms/emergency_red_flags.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df)} emergency red flags in datasets/symptoms/emergency_red_flags.csv")

if __name__ == "__main__":
    ensure_dirs()
    generate_symptoms_master()
    generate_disease_master()
    generate_disease_symptom_mapping()
    generate_emergency_red_flags()
