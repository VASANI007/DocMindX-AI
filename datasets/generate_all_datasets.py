"""
    DocMindX AI Comprehensive Dataset Generator - Phase 2, 3, 4 & Translations
Generates:
- datasets/diet/condition_guidance.csv
- datasets/yoga/yoga_guidance.csv
- datasets/physiotherapy/physiotherapy_guidance.csv
- datasets/blood_report/lab_test_reference.csv
- datasets/medical_terms/medical_test_dictionary.csv
- datasets/medical_terms/medical_findings_dictionary.csv
- datasets/india_geographic_master.csv
- translations/english.json, translations/hindi.json, translations/gujarati.json
"""
import os
import json
import pandas as pd

def generate_condition_guidance():
    guidance = [
        ("D001", "Rest adequately; stay hydrated with warm water/soups; use steam inhalation; gargle with warm saline water.",
         "Avoid cold drinks, smoking, strenuous exertion, and crowded areas.",
         "Warm ginger tea, clear vegetable/chicken broth, honey-lemon water, vitamin C rich citrus fruits.",
         "Cold refrigerated foods, deep-fried items, caffeine, dairy in excess if mucus feels thick.",
         "Warm steam inhalation twice daily; saline nasal drops.",
         "Symptoms generally resolve within 5–7 days. Seek medical review if high fever (>102°F) or breathing difficulty develops."),
        
        ("D002", "Complete bed rest; high fluid intake; isolate from vulnerable family members; monitor body temperature regularly.",
         "Avoid going to work/school while febrile, avoid self-medicating with aspirin in young individuals.",
         "Electrolyte drinks, clear broths, coconut water, soft khichdi, fresh fruit juices.",
         "Oily and spicy foods, alcohol, caffeinated sodas, processed snacks.",
         "Cold compresses on forehead for fever reduction; adequate sleep.",
         "Typical recovery is 7–10 days. Seek urgent hospital care if persistent chest pain, dyspnea or confusion occurs."),

        ("D003", "Rest and allow airway recovery; drink 2.5-3 liters of fluids daily; use warm mist humidifier.",
         "Avoid active and passive smoking, cold air exposure, air pollutants, and suppressing productive cough without medical advice.",
         "Warm herbal teas (tulsi/ginger), turmeric milk, warm soups, light porridge.",
         "Iced beverages, fried foods, dairy in heavy quantities if congestion worsens.",
         "Elevate head with pillows while sleeping; chest warm compress.",
         "Cough may linger for 2–3 weeks. Consult doctor if coughing up blood, high fever or wheezing develops."),

        ("D004", "Prescription compliance under physician care; absolute rest; track oxygen saturation (SpO2) with pulse oximeter.",
         "Avoid physical exertion, sudden temperature shifts, and delaying antibiotic/medical therapy.",
         "High-protein soft meals (dal khichdi, eggs, soups), plenty of warm water, antioxidant fruits.",
         "Heavy greasy meals, cold desserts, carbonated beverages.",
         "Deep breathing exercises (when stable); prone/semi-fowler positioning for comfortable breathing.",
         "Recovery takes 2–4 weeks. Immediate emergency care if SpO2 drops below 94% or severe chest pain occurs."),

        ("D005", "Keep quick-relief bronchodilator inhaler accessible; sit upright during episodes; identify and avoid personal allergens.",
         "Avoid smoke, dust mites, pet dander, cold drafts, vigorous exercise during flare-ups, and unprescribed beta-blockers/NSAIDs.",
         "Warm water, anti-inflammatory foods (ginger, turmeric, omega-3 rich seeds), light easily digestible meals.",
         "Sulfited foods, cold ice creams, excessive dairy, artificial food colorings.",
         "Pursed-lip breathing technique; maintaining a dust-free allergen-proof bedroom.",
         "Immediate medical emergency attention if rescue inhaler does not relieve breathing difficulty within 15 minutes."),

        ("D006", "Oral Rehydration Solutions (ORS) in small frequent sips; maintain fluid and electrolyte balance.",
         "Avoid solid heavy foods immediately, avoid dairy, spicy food, caffeine, and over-the-counter anti-motility drugs without doctor consultation.",
         "BRAT diet (Banana, Rice/Khichdi, Applesauce, Toast), ORS, light buttermilk, tender coconut water.",
         "Milk and cheese, deep-fried snacks, spicy curries, sugary drinks, alcohol.",
         "Rest; sip fluids 15-20 minutes after vomiting episode.",
         "Usually improves within 48–72 hours. Urgent medical visit if blood in stool, persistent vomiting or signs of severe dehydration appear."),

        ("D007", "Eat small frequent meals; remain upright for at least 2 hours after eating; elevate head of bed by 6 inches.",
         "Avoid lying down immediately after meals, tight abdominal clothing, late-night heavy snacking, and smoking.",
         "Oatmeal, bananas, melons, green vegetables, fennel water, almond milk.",
         "Spicy curries, citrus fruits on empty stomach, raw onions, tomatoes, chocolate, peppermint, coffee, carbonated drinks.",
         "Sip warm water; chew food thoroughly and unhurriedly.",
         "Lifestyle changes show benefit within 1–2 weeks. Seek consultation if swallowing difficulty or unexplained weight loss develops."),

        ("D008", "Follow prescribed acid suppressant / mucosal protectant regimen; maintain regular meal timings.",
         "Avoid skipping meals, avoid NSAID painkillers (like ibuprofen/diclofenac) without gastro-protective cover, avoid alcohol.",
         "Bland soft diet, steamed vegetables, boiled oats, cabbage juice, probiotic curd/yogurt.",
         "Extremely spicy food, chili powder, black pepper, coffee, alcohol, deep-fried fast food.",
         "Stress management; avoiding eating 3 hours before sleep.",
         "Medical review essential. Immediate emergency care if severe sudden abdominal pain or black/bloody stools occur."),

        ("D009", "Absolute emergency surgical/hospital evaluation required; keep fasting (NPO) until evaluated by doctor.",
         "DO NOT take pain killers, laxatives or heating pads on abdomen before doctor evaluation (may mask rupture signs).",
         "Nil by mouth (NPO) until assessed by general surgeon.",
         "All solid foods and oral fluids until surgeon clears.",
         "Seek immediate emergency room admission.",
         "Emergency condition. Immediate hospital visit required."),

        ("D010", "Adequate physical rest; high carbohydrate, easily digestible low-fat diet; avoid hepatotoxic substances.",
         "Avoid all forms of alcohol, unnecessary over-the-counter medications and herbal supplements without physician consent.",
         "Fresh sugarcane juice (hygienically prepared), glucose water, boiled rice, ripe papaya, tender coconut water.",
         "Oily, fatty and deep-fried dishes, spicy foods, alcohol, processed meat.",
         "Strict hand hygiene and water sanitation.",
         "Bilirubin and liver enzymes normalize over 4–8 weeks under medical supervision."),

        ("D011", "Drink plenty of water (2.5-3.5L daily); empty bladder frequently; maintain perineal hygiene.",
         "Avoid holding urine for long periods, avoid perfumed soaps/washes in genital area, avoid excess caffeine.",
         "Cranberry extract/juice (unsweetened), barley water, coconut water, vitamin C rich fruits.",
         "Excess coffee, alcohol, spicy pepper-heavy foods, artificial sweeteners.",
         "Apply warm heating pad to lower abdomen for pelvic discomfort.",
         "Symptoms should improve within 48 hours of starting doctor-prescribed antibiotics. Seek urgent help if high fever or back flank pain occurs."),

        ("D012", "Drink 3 to 4 liters of water daily to promote stone passage (if stone size permits); follow prescribed antispasmodics.",
         "Avoid excessive sodium/salt, avoid calcium or vitamin D supplements unless advised by nephrologist.",
         "Lemonade (citrate helps prevent crystallization), coconut water, high-fiber vegetables, adequate hydration.",
         "Spinach, beetroot, nuts, chocolate, excess tea (oxalate-rich), high-sodium processed foods, red meat.",
         "Gentle walking; warm compress on flank during mild pain.",
         "Urgent hospital visit if colicky pain is unbearable, fever develops, or inability to pass urine occurs."),

        ("D013", "DASH diet (Dietary Approaches to Stop Hypertension); reduce sodium intake (< 2g/day); engage in 30 mins moderate daily walking.",
         "Avoid table salt, pickles, papads, canned foods, smoking, excess alcohol, and sedentary lifestyle.",
         "Garlic, flaxseeds, leafy greens, potassium-rich foods (bananas, sweet potatoes), whole grains.",
         "Pickles, processed meats, salted snacks, deep-fried savories, energy drinks.",
         "Regular home blood pressure tracking; 15 mins daily pranayama/meditation.",
         "Lifelong lifestyle and medication adherence. Urgent emergency care if BP > 180/120 with headache or blurred vision."),

        ("D014", "Immediate emergency room care! Call ambulance; rest completely in half-sitting position.",
         "Do not delay seeking emergency help; do not drive oneself to hospital; avoid exertion.",
         "Strictly medical emergency (NPO until stabilized).",
         "All oral foods until stabilized.",
         "Keep calm; loosen tight clothing; follow emergency EMS instructions.",
         "Critical medical emergency. Time is muscle."),

        ("D015", "Strict fluid restriction (as advised by cardiologist, typically 1.2-1.5L/day); daily morning weight monitoring.",
         "Avoid excess fluid intake, avoid high-sodium meals, avoid sudden strenuous exertion.",
         "Low sodium, heart-healthy foods (oats, berries, walnuts, steamed vegetables).",
         "Salt, soup broths, pickles, canned vegetables, cheese, carbonated beverages.",
         "Elevate feet while resting to reduce edema; semi-upright sleeping.",
         "Consult cardiologist immediately if weight increases by >1.5 kg in 2 days or shortness of breath worsens."),

        ("D016", "Emergency! Call ambulance immediately. Note exact time of symptom onset for thrombolysis decision.",
         "Do not give any food, water or medication by mouth (aspiration risk); do not wait for symptoms to resolve on own.",
         "Nil by mouth in acute phase.",
         "All oral intake until hospital swallow assessment.",
         "Keep patient flat with head slightly elevated on side (recovery position) if vomiting.",
         "Critical emergency. Golden hour intervention saves lives."),

        ("D017", "Rest in a quiet, dark, well-ventilated room; apply cold ice pack to forehead or temples; maintain regular sleep schedule.",
         "Avoid skipping meals, avoid known triggers (bright flashing lights, loud noise, lack of sleep, stress).",
         "Ginger tea, magnesium-rich foods (spinach, pumpkin seeds, almonds), adequate water.",
         "Aged cheese, chocolate, monosodium glutamate (MSG), processed meats with nitrates, red wine, excessive caffeine.",
         "Acupressure on web between thumb and index finger; cold gel mask.",
         "Episodes last 4–72 hours. Seek emergency care if worst sudden headache occurs or neurological deficits accompany."),

        ("D018", "Neck and shoulder gentle stretching; ergonomic desk posture; take 5-minute screen breaks every hour.",
         "Avoid prolonged poor posture, prolonged screen squinting, and high stress.",
         "Herbal chamomile tea, light balanced diet, adequate hydration.",
         "Excess coffee, energy drinks, skipped meals.",
         "Warm shower or warm heating pad on neck muscles; progressive muscle relaxation.",
         "Typically relieves with rest, hydration and relaxation within hours."),

        ("D019", "Immediate emergency hospital admission! Intravenous antibiotics and intensive monitoring required.",
         "Do not delay hospitalization; avoid light exposure due to photophobia.",
         "Hospital IV fluids and prescribed inpatient nutrition.",
         "All self-treatment.",
         "Immediate emergency room presentation.",
         "Life-threatening infection requiring emergency inpatient medical management."),

        ("D020", "Monitor blood glucose levels regularly; take high-fiber complex carbohydrates; 30–45 mins daily walking.",
         "Avoid refined sugar, sweets, sweetened beverages, white bread, skipping meals, and sedentary habits.",
         "Bitter gourd (karela), fenugreek (methi) seeds, whole grains (jowar, bajra), oats, leafy vegetables, sprouts.",
         "Sugar, jaggery, honey, packaged fruit juices, sweets, maida (refined flour), fried snacks.",
         "Daily foot inspection for cuts or blisters; wear comfortable footwear.",
         "Target HbA1c < 7% under doctor guidance. Seek urgent help if glucose > 300 mg/dL with ketones or confusion."),

        ("D021", "Take thyroid medication (levothyroxine) on an empty stomach with plain water at least 30-60 mins before breakfast.",
         "Avoid taking calcium/iron supplements or soy within 4 hours of thyroid pill; avoid sedentary lifestyle.",
         "Iodized salt, selenium-rich seeds, whole grains, cooked cruciferous vegetables in moderation.",
         "Excess raw cabbage, cauliflower, broccoli, soy products taken near medication time.",
         "Gentle aerobic exercise to boost metabolic rate.",
         "Routine TSH monitoring every 6–12 weeks until stable under endocrinologist guidance."),

        ("D022", "Follow antithyroid medications as prescribed; stay in cool air-conditioned environment during heat waves.",
         "Avoid stimulants, energy drinks, excess dietary iodine (kelp/seaweed), and high-stress environments.",
         "Cruciferous vegetables (cabbage, broccoli), berries, complex carbs, adequate hydration.",
         "Iodine-enriched supplements, seaweed, seafood in excess, excess caffeine.",
         "Meditation and cooling pranayama (Sheetali/Sheetkari).",
         "Regular T3/T4/TSH monitoring with physician; report sudden high fever or severe agitation immediately."),

        ("D023", "Low-impact exercise (swimming, cycling, walking); maintain healthy body weight to reduce joint load.",
         "Avoid high-impact jumping, deep squats with heavy weights, and prolonged immobility.",
         "Anti-inflammatory foods (turmeric, ginger, olive oil, walnuts, fatty fish/flaxseed), calcium & vitamin D.",
         "Excess sugar, trans-fats, processed red meat, fried foods.",
         "Warm compress before exercise to loosen joints, cold pack after exertion if swollen.",
         "Chronic condition managed with lifestyle, physiotherapy, and doctor-prescribed symptom relief."),

        ("D024", "Take prescribed Disease-Modifying Anti-Rheumatic Drugs (DMARDs) consistently; gentle range-of-motion exercises.",
         "Avoid stopping prescribed DMARDs without rheumatologist consultation; avoid smoking; avoid high stress.",
         "Mediterranean-style anti-inflammatory diet (leafy greens, olive oil, berries, chia seeds, turmeric).",
         "Ultra-processed foods, refined sugars, deep-fried snacks, excessive saturated fats.",
         "Warm morning shower to relieve morning stiffness; joint protection techniques.",
         "Regular rheumatology follow-ups and inflammatory marker checks (CRP, ESR)."),

        ("D025", "Relative rest for 24–48 hours followed by gentle walking; use firm mattress; maintain proper lifting biomechanics.",
         "Avoid complete prolonged bed rest (>48 hrs), avoid heavy lifting and twisting waist simultaneously.",
         "Anti-inflammatory whole food diet, adequate water to keep spinal discs hydrated.",
         "Excess alcohol, processed junk food promoting systemic inflammation.",
         "Ice pack for first 48 hours (15 mins intervals), followed by gentle warm heat; lumbar support cushion.",
         "Acute muscular strains usually improve within 1–2 weeks. Consult doctor if pain radiates below knee with numbness."),

        ("D026", "Keep indoor air clean; use HEPA air purifier if possible; wash face and eyes with fresh water after outdoor exposure.",
         "Avoid rubbing eyes/nose vigorously, avoid dusting without mask, avoid keeping windows open during peak pollen hours.",
         "Warm herbal teas, honey, citrus fruits, vitamin C rich vegetables, probiotic foods.",
         "Very cold ice water, known food allergen triggers.",
         "Saline nasal spray/rinse (Neti pot with distilled saline) to clear allergens.",
         "Seasonal management with doctor-advised antihistamines / nasal sprays."),

        ("D027", "Immediate emergency room care! Administer auto-injector epinephrine (EpiPen) if prescribed and available.",
         "Never delay calling emergency ambulance; do not wait to see if reaction subsides.",
         "Emergency protocol (NPO).",
         "All foods until hospital clearance.",
         "Lie flat with legs elevated unless breathing is difficult, then sit upright.",
         "Life-threatening medical emergency."),

        ("D028", "High fluid intake (minimum 3–4 liters/day); monitor platelet count daily; complete physical rest; use mosquito netting.",
         "DO NOT take NSAIDs (Aspirin, Ibuprofen, Diclofenac, Mefenamic acid) as they increase bleeding risk! Use only paracetamol under medical advice.",
         "Papaya leaf extract (if tolerated), tender coconut water, pomegranate juice, kiwi, ORS, lentil soup.",
         "Oily, spicy foods, dark-colored foods that might disguise GI bleeding in vomit/stool.",
         "Tepid sponge baths for high fever; complete bed rest.",
         "Critical phase occurs on days 3–7 when fever subsides. Seek immediate hospitalization if persistent vomiting, abdominal pain or bleeding spots appear."),

        ("D029", "Complete full course of antimalarial medications prescribed by doctor; stay well hydrated; rest.",
         "Avoid stopping antimalarial pills early even if feeling better; avoid dehydration.",
         "Easily digestible high-carbohydrate meals (khichdi, porridge), citrus juices, coconut water, boiled vegetables.",
         "Greasy oily foods, heavy creams, raw uncooked foods.",
         "Tepid sponging during fever spikes; mosquito repellent usage to prevent further transmission.",
         "Fever should subside within 48–72 hours of starting antimalarials. Urgent hospital visit if dark urine or extreme jaundice occurs."),

        ("D030", "Take prescribed antibiotic course completely; drink only boiled/filtered water; eat clean home-cooked soft food.",
         "Avoid street food, raw salads, unpeeled fruits, iced drinks outside, and stopping antibiotics halfway.",
         "Boiled rice with light moong dal, boiled potatoes, toast, peeled bananas, coconut water, boiled water.",
         "Spicy dishes, rich gravies, raw unwashed vegetables, oily fried foods, unpasteurized milk.",
         "Strict hand hygiene before eating and after using restroom.",
         "Requires 10–14 days of medical antibiotic therapy. Report persistent vomiting or severe abdominal swelling to doctor.")
    ]
    df = pd.DataFrame(guidance, columns=[
        "condition_id", "what_to_do", "what_to_avoid", "diet_recommendation",
        "food_to_limit", "home_care", "monitoring_advice"
    ])
    df.to_csv("datasets/diet/condition_guidance.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df)} condition guidance entries in datasets/diet/condition_guidance.csv")

def generate_yoga_and_physio():
    yoga = [
        ("Y001", "D025", "Bhujangasana (Cobra Pose)", "Gentle backward bend that strengthens lumbar spine and relieves back stiffness.",
         "1. Lie prone on stomach with palms under shoulders.\n2. Inhale gently and lift chest upward keeping elbows slightly bent.\n3. Hold for 15-20 seconds with normal breathing.\n4. Exhale and lower slowly.",
         "Do not strain or hyperextend lower back. Keep pelvis grounded.", "Acute lumbar disc herniation with severe radiculopathy, severe pregnancy.", "assets/yoga/bhujangasana.png"),
        
        ("Y002", "D025", "Marjaryasana-Bitilasana (Cat-Cow Stretch)", "Rhythmic spinal mobilization enhancing flexibility and easing tension.",
         "1. Start on all fours with hands under shoulders and knees under hips.\n2. Inhale: arch back, look up (Cow).\n3. Exhale: round spine toward ceiling, tuck chin (Cat).\n4. Repeat 8-10 cycles smoothly.",
         "Perform movement gently without jerky motions.", "Severe wrist injury, acute unhealed spinal fracture.", "assets/yoga/cat_cow.png"),

        ("Y003", "D018", "Shavasana & Anulom Vilom Pranayama", "Deep relaxation and alternate nostril breathing for stress reduction and headache relief.",
         "1. Sit comfortably with spine straight.\n2. Close right nostril with thumb, inhale deeply through left nostril (4s).\n3. Close left nostril, exhale through right (4s).\n4. Inhale right (4s), exhale left (4s).\n5. Practice for 5-10 minutes.",
         "Maintain effortless gentle breathing without forceful retention.", "Severe acute respiratory distress requiring emergency oxygen.", "assets/yoga/anulom_vilom.png"),

        ("Y004", "D007", "Vajrasana (Thunderbolt Pose)", "Sitting posture that promotes healthy digestion and reduces post-meal acidity.",
         "1. Kneel on a yoga mat with knees together and big toes touching.\n2. Sit back on heels with spine straight and palms resting on knees.\n3. Breathe slowly and deeply for 5–10 minutes after light meals.",
         "Keep posture erect without slouching.", "Severe knee osteoarthritis, recent knee or ankle surgery.", "assets/yoga/vajrasana.png"),

        ("Y005", "D020", "Mandukasana (Frog Pose)", "Gentle abdominal compression supporting pancreatic circulation and digestive vitality.",
         "1. Sit in Vajrasana.\n2. Make fists with thumbs tucked inside, place beside navel.\n3. Inhale deeply, then exhale and bend forward touching chest to thighs while looking forward.\n4. Hold for 20-30 seconds with calm breathing.",
         "Do not press excessively hard on abdomen.", "Recent abdominal surgery, peptic ulcer exacerbation, hernia, pregnancy.", "assets/yoga/mandukasana.png"),

        ("Y006", "D013", "Bhramari Pranayama (Humming Bee Breath)", "Calming autonomic resonance breathing that reduces sympathetic tone and mild tension.",
         "1. Sit comfortably with eyes closed.\n2. Place index fingers lightly on ear tragus.\n3. Take a deep inhale through nose.\n4. Exhale while creating a steady, smooth humming bee sound ('Mmm').\n5. Repeat 6-8 times.",
         "Focus on soothing vibrations in cranial region.", "Severe active middle ear infection / discharge.", "assets/yoga/bhramari.png")
    ]
    df_yoga = pd.DataFrame(yoga, columns=[
        "exercise_id", "condition_id", "exercise_name", "description", "steps", "precautions", "avoid_if", "image_path"
    ])
    df_yoga.to_csv("datasets/yoga/yoga_guidance.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_yoga)} yoga routines in datasets/yoga/yoga_guidance.csv")

    physio = [
        ("P001", "D025", "Pelvic Bridging Exercise", "Core and gluteal activation to support lumbar stability and relieve lower back pain.",
         "1. Lie on back with knees bent and feet flat on floor hip-width apart.\n2. Engage abdominal core gently.\n3. Lift hips upward until knees, hips and shoulders form a straight line.\n4. Hold for 5 seconds, lower down slowly.\n5. Repeat 10-12 repetitions.",
         "Avoid hyperextending lower back at the top of the bridge.", "Severe acute spinal instability, unmanaged severe hernia.", "assets/physio/pelvic_bridge.png"),
        
        ("P002", "D018", "Cervical Isometric & Chin Tuck Stretches", "Relieves tension headaches and strengthens deep cervical neck flexors.",
         "1. Sit upright with shoulders relaxed.\n2. Look straight ahead, gently glide chin straight back (as if making a subtle double chin).\n3. Hold for 5 seconds without tilting head up or down.\n4. Relax and repeat 10 times.",
         "Movement should be pain-free and smooth.", "Acute cervical spine fracture or severe dizziness upon movement.", "assets/physio/chin_tuck.png"),

        ("P003", "D023", "Isometric Quadriceps Sets & Straight Leg Raises", "Strengthens thigh muscles to stabilize knee joint and reduce knee arthritis pain.",
         "1. Lie on back with one leg straight and the other knee bent.\n2. Tighten thigh muscle of straight leg pushing back of knee into bed.\n3. Lift straight leg 12 inches off surface.\n4. Hold 5 seconds, slowly lower.\n5. Perform 10 reps per leg.",
         "Do not hold breath while lifting leg.", "Acute severe knee effusion / acute ligament tear.", "assets/physio/quad_sets.png"),

        ("P004", "D024", "Gentle Active Hand & Finger Range of Motion", "Preserves joint mobility and decreases morning hand stiffness in arthritis.",
         "1. Sit comfortably with arms supported on table.\n2. Slowly open fingers wide, then gently curl fingers into a soft loose fist.\n3. Touch thumb to tip of each finger sequentially.\n4. Perform 10 gentle repetitions.",
         "Never force movement into sharp joint pain.", "Acute infected inflamed hot joint.", "assets/physio/hand_mobility.png")
    ]
    df_physio = pd.DataFrame(physio, columns=[
        "exercise_id", "condition_id", "exercise_name", "description", "steps", "precautions", "avoid_if", "image_path"
    ])
    df_physio.to_csv("datasets/physiotherapy/physiotherapy_guidance.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_physio)} physiotherapy routines in datasets/physiotherapy/physiotherapy_guidance.csv")

def generate_lab_and_medical_dictionaries():
    labs = [
        ("L001", "Hemoglobin (Hb)", "Complete Blood Count", "Adult", "Male", "g/dL", 13.5, 17.5, "Oxygen-carrying protein in red blood cells"),
        ("L002", "Hemoglobin (Hb)", "Complete Blood Count", "Adult", "Female", "g/dL", 12.0, 15.5, "Oxygen-carrying protein in red blood cells"),
        ("L003", "Total WBC Count", "Complete Blood Count", "Adult", "Both", "cells/mcL", 4000, 11000, "White blood cells fighting infection"),
        ("L004", "Platelet Count", "Complete Blood Count", "Adult", "Both", "lakh/mcL", 1.5, 4.5, "Cell fragments essential for blood clotting (150,000 - 450,000/mcL)"),
        ("L005", "RBC Count", "Complete Blood Count", "Adult", "Male", "million/mcL", 4.5, 5.9, "Red blood cell count"),
        ("L006", "RBC Count", "Complete Blood Count", "Adult", "Female", "million/mcL", 4.1, 5.1, "Red blood cell count"),
        ("L007", "Fasting Blood Sugar (FBS)", "Diabetes & Metabolism", "Adult", "Both", "mg/dL", 70.0, 99.0, "Blood glucose after 8 hours overnight fast (100-125: Prediabetes, >=126: Diabetes)"),
        ("L008", "Post Prandial Blood Sugar (PPBS)", "Diabetes & Metabolism", "Adult", "Both", "mg/dL", 70.0, 140.0, "Blood glucose 2 hours after meal (140-199: Prediabetes, >=200: Diabetes)"),
        ("L009", "HbA1c (Glycated Hemoglobin)", "Diabetes & Metabolism", "Adult", "Both", "%", 4.0, 5.6, "Average 3-month blood sugar indicator (5.7-6.4%: Prediabetes, >=6.5%: Diabetes)"),
        ("L010", "Serum Creatinine", "Kidney Function Test", "Adult", "Male", "mg/dL", 0.7, 1.3, "Waste product filtered by kidneys reflecting renal filtration"),
        ("L011", "Serum Creatinine", "Kidney Function Test", "Adult", "Female", "mg/dL", 0.5, 1.1, "Waste product filtered by kidneys reflecting renal filtration"),
        ("L012", "Blood Urea Nitrogen (BUN)", "Kidney Function Test", "Adult", "Both", "mg/dL", 7.0, 20.0, "Kidney metabolic waste parameter"),
        ("L013", "Serum Uric Acid", "Kidney & Metabolic", "Adult", "Male", "mg/dL", 3.5, 7.2, "Purine breakdown product relevant to gout and renal stones"),
        ("L014", "Serum Uric Acid", "Kidney & Metabolic", "Adult", "Female", "mg/dL", 2.6, 6.0, "Purine breakdown product relevant to gout and renal stones"),
        ("L015", "SGPT / ALT (Alanine Aminotransferase)", "Liver Function Test", "Adult", "Both", "U/L", 7.0, 56.0, "Key liver enzyme indicator of hepatocellular health"),
        ("L016", "SGOT / AST (Aspartate Aminotransferase)", "Liver Function Test", "Adult", "Both", "U/L", 10.0, 40.0, "Liver and muscle tissue enzyme"),
        ("L017", "Total Bilirubin", "Liver Function Test", "Adult", "Both", "mg/dL", 0.2, 1.2, "Bile pigment produced from RBC breakdown; elevated in jaundice"),
        ("L018", "Serum Total Cholesterol", "Lipid Profile", "Adult", "Both", "mg/dL", 125.0, 200.0, "Total circulating cholesterol in blood"),
        ("L019", "Serum Triglycerides", "Lipid Profile", "Adult", "Both", "mg/dL", 50.0, 150.0, "Main form of stored body fat in bloodstream"),
        ("L020", "Serum HDL Cholesterol ('Good')", "Lipid Profile", "Adult", "Both", "mg/dL", 40.0, 60.0, "High-density lipoprotein protecting cardiovascular health"),
        ("L021", "Serum LDL Cholesterol ('Bad')", "Lipid Profile", "Adult", "Both", "mg/dL", 50.0, 100.0, "Low-density lipoprotein linked to plaque formation"),
        ("L022", "Thyroid Stimulating Hormone (TSH)", "Thyroid Profile", "Adult", "Both", "uIU/mL", 0.4, 4.5, "Pituitary hormone controlling thyroid hormone production"),
        ("L023", "Serum Vitamin D3 (25-OH)", "Vitamins & Minerals", "Adult", "Both", "ng/mL", 30.0, 100.0, "Essential fat-soluble vitamin for bone and immune health"),
        ("L024", "Serum Vitamin B12", "Vitamins & Minerals", "Adult", "Both", "pg/mL", 200.0, 900.0, "Vital cofactor for nerve health and red blood cell creation")
    ]
    df_labs = pd.DataFrame(labs, columns=[
        "test_id", "test_name", "category", "age_group", "sex", "unit", "reference_min", "reference_max", "description"
    ])
    df_labs.to_csv("datasets/blood_report/lab_test_reference.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_labs)} lab reference records in datasets/blood_report/lab_test_reference.csv")

    terms = [
        ("T001", "Complete Blood Count", "CBC / Hemogram", "Hematology", "Assesses overall health and checks for anemia, infection, and clotting issues.", "Elevated WBC indicates infection; low Hb indicates anemia; low platelets indicate bleeding risk.", "MedlinePlus"),
        ("T002", "Lipid Profile", "Cholesterol Panel", "Cardiovascular", "Measures blood fats to evaluate cardiovascular risk.", "High LDL/Triglycerides increase heart disease risk; high HDL is protective.", "AHA Guidelines"),
        ("T003", "Liver Function Test", "LFT", "Hepatic", "Measures liver enzymes, proteins, and bilirubin.", "Elevated ALT/AST suggests liver irritation; high bilirubin causes jaundice.", "AASLD Guidelines"),
        ("T004", "Kidney Function Test", "KFT / RFT", "Renal", "Evaluates how effectively kidneys filter metabolic waste products.", "Elevated creatinine or BUN indicates impaired kidney filtration efficiency.", "NKF Guidelines"),
        ("T005", "Thyroid Profile", "TFT / TSH", "Endocrine", "Checks functioning of the thyroid gland.", "High TSH suggests hypothyroidism (underactive); Low TSH suggests hyperthyroidism.", "ATA Guidelines")
    ]
    df_terms = pd.DataFrame(terms, columns=[
        "test_id", "test_name", "short_name", "category", "description", "possible_interpretation_notes", "source"
    ])
    df_terms.to_csv("datasets/medical_terms/medical_test_dictionary.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_terms)} medical test dictionary entries in datasets/medical_terms/medical_test_dictionary.csv")

    findings = [
        ("F001", "Anemia", "एनीमिया (खून की कमी)", "એનીમિયા (લોહીની ઉણપ)", "Low red blood cells or hemoglobin, causing fatigue, pale skin and shortness of breath.", "Check iron, vitamin B12, and discuss dietary/iron supplementation with doctor."),
        ("F002", "Leukocytosis", "ल्यूकोसाइटोसिस (WBC बढ़ना)", "લ્યુકોસાઇટોસિસ (WBC વધવા)", "Elevated white blood cell count typically indicating an active bacterial/viral infection or inflammation.", "Identify source of infection and consult physician for appropriate treatment."),
        ("F003", "Thrombocytopenia", "थ्रोम्बोसाइटोपेनिया (प्लेटलेट कम होना)", "થ્રોમ્બોસાઇટોપેનિયા (પ્લેટલેટ ઘટવા)", "Low blood platelet count increasing the tendency to bruise or bleed.", "Carefully monitor for bleeding spots, avoid blood-thinning NSAIDs, consult doctor urgently if platelets < 50,000."),
        ("F004", "Hyperglycemia", "हाइपरग्लाइसीमिया (शुगर बढ़ना)", "હાઇપરગ્લાયકેમિઆ (શુગર વધવી)", "Elevated blood sugar level above normal physiological thresholds.", "Follow diabetic meal plan, stay active, monitor fasting/PPBS, and adjust medication with doctor."),
        ("F005", "Hyperlipidemia", "हाइपरलिपिडिमिया (कोलेस्ट्रॉल बढ़ना)", "હાઇપરલિપિડેમિઆ (કોલેસ્ટ્રોલ વધવું)", "Elevated cholesterol or triglycerides in bloodstream.", "Adopt heart-healthy low-oil diet, increase cardiovascular exercise, and follow lipid-lowering advice.")
    ]
    df_findings = pd.DataFrame(findings, columns=[
        "finding_id", "finding_name", "finding_name_hi", "finding_name_gu", "description", "patient_advice"
    ])
    df_findings.to_csv("datasets/medical_terms/medical_findings_dictionary.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_findings)} medical findings dictionary entries in datasets/medical_terms/medical_findings_dictionary.csv")

def generate_india_geo_master():
    geo = [
        ("Gujarat", "Ahmedabad", "Ahmedabad", 23.0225, 72.5714, "Semi-arid / Western", "Monsoon vector-borne risk (Dengue/Malaria), summer heat exhaustion"),
        ("Gujarat", "Surat", "Surat", 21.1702, 72.8311, "Coastal / Humid", "Seasonal viral flu, waterborne GI infections during rains"),
        ("Gujarat", "Vadodara", "Vadodara", 22.3072, 73.1812, "Semi-arid / Western", "Viral fevers, seasonal allergies"),
        ("Gujarat", "Rajkot", "Rajkot", 22.3039, 70.8022, "Semi-arid / Saurashtra", "Summer heat waves, water scarcity GI concerns"),
        ("Gujarat", "Bhavnagar", "Bhavnagar", 21.7645, 72.1519, "Coastal Saurashtra", "Allergic rhinitis, seasonal gastro"),
        ("Gujarat", "Gandhinagar", "Gandhinagar", 23.2156, 72.6369, "North Gujarat Plains", "Seasonal flu, viral fevers"),
        ("Maharashtra", "Mumbai", "Mumbai", 19.0760, 72.8777, "Tropical Coastal", "Monsoon Leptospirosis, Dengue, Malaria, humidity skin issues"),
        ("Maharashtra", "Pune", "Pune", 18.5204, 73.8567, "Plateau / Moderate", "Seasonal viral rhinitis, winter respiratory allergies"),
        ("Maharashtra", "Nagpur", "Nagpur", 21.1458, 79.0882, "Central / Extreme Summer", "Severe summer heat stroke risk, viral conjunctivitis"),
        ("Rajasthan", "Jaipur", "Jaipur", 26.9124, 75.7873, "Arid / Semi-arid", "Dust storm respiratory allergies, extreme summer dehydration"),
        ("Rajasthan", "Jodhpur", "Jodhpur", 26.2389, 73.0243, "Thar Desert Margin", "Heat exhaustion, seasonal fever"),
        ("Delhi", "New Delhi", "New Delhi", 28.6139, 77.2090, "North Subtropical / Continental", "Winter particulate air pollution (Asthma/Bronchitis), monsoon Dengue"),
        ("Karnataka", "Bengaluru", "Bengaluru", 12.9716, 77.5946, "Tropical Savanna", "Pollen allergy rhinitis, weather fluctuation respiratory symptoms"),
        ("Tamil Nadu", "Chennai", "Chennai", 13.0827, 80.2707, "Coastal / High Humidity", "Post-monsoon vector borne fevers, heat hydration needs"),
        ("Uttar Pradesh", "Lucknow", "Lucknow", 26.8467, 80.9462, "Gangetic Plains", "Winter fog respiratory triggers, monsoon enteric infections"),
        ("West Bengal", "Kolkata", "Kolkata", 22.5726, 88.3639, "Tropical Wet-and-Dry", "Monsoon Dengue, seasonal gastroenteritis")
    ]
    df_geo = pd.DataFrame(geo, columns=[
        "state", "district", "city", "latitude", "longitude", "climate_region", "season_context"
    ])
    df_geo.to_csv("datasets/india_geographic_master.csv", index=False, encoding="utf-8")
    print(f"[OK] Generated {len(df_geo)} geographic regions in datasets/india_geographic_master.csv")

def generate_translations():
    en = {
        "app_title": "DocMindX AI — Intelligent Healthcare Companion",
        "app_subtitle": "AI-Powered Multilingual Health, Medical Report Analysis & Nearby Healthcare Triage",
        "panel1_title": "AI Health & Symptom Analysis",
        "panel2_title": "Medical Report & Prescription Analyzer",
        "panel3_title": "Nearby Healthcare Finder",
        "lang_select": "Language / भाषा / ભાષા",
        "basic_info": "1. Basic Information & Demographics",
        "age_group": "Age Group",
        "gender": "Gender",
        "geo_context": "2. Geographic Health Context",
        "state": "State",
        "district": "City / District",
        "symptoms_header": "3. Select Symptoms & Health Issues",
        "symptom_search": "Search and select symptoms...",
        "duration_header": "4. Duration of Symptoms",
        "existing_conditions": "5. Existing Health Conditions",
        "bp": "Blood Pressure",
        "diabetes": "Diabetes / Sugar",
        "heart": "Heart Condition",
        "other_conditions": "Other Medical History / Conditions",
        "current_meds": "6. Current Medicines (for Interaction Checking)",
        "analyze_btn": "Analyze Health & Symptoms",
        "urgency_critical": "URGENT MEDICAL ATTENTION MAY BE NEEDED",
        "urgency_critical_sub": "One or more emergency red flag signs detected. Please proceed to the nearest emergency room or hospital immediately.",
        "find_hospital_btn": "Find Nearest Emergency Hospital",
        "possible_conditions": "Possible Health Conditions (AI Guidance)",
        "condition_note": "Probabilities are triage references based on clinical datasets and do not replace professional medical diagnosis.",
        "medicines_info": "Medicine & Safety Information",
        "medicine_disclaimer": "This information is for educational reference only. Never start, stop, or change any prescription without consulting a certified physician.",
        "diet_guidance": "Diet & Nutritional Guidance",
        "do_and_dont": "Suggested Self-Care & Things to Avoid",
        "yoga_physio": "Supportive Yoga & Physiotherapy Care",
        "pdf_download": "Download Complete PDF Health Report",
        "report_summary": "Report Summary & Key Findings",
        "report_normal": "Within Expected Reference Range",
        "report_warning": "Needs Medical Attention / Out of Range",
        "report_urgent": "Discuss Urgently with a Doctor",
        "nearby_search_btn": "Locate Nearby Healthcare Services",
        "pharmacy": "Pharmacies / Medical Stores",
        "hospital": "Hospitals & Clinics",
        "diagnostic": "Diagnostic & Pathology Labs",
        "blood_bank": "Blood Banks"
    }

    hi = {
        "app_title": "मेडीमाइंड एआई — आपका बुद्धिमान स्वास्थ्य साथी",
        "app_subtitle": "एआई-संचालित बहुभाषी स्वास्थ्य, मेडिकल रिपोर्ट विश्लेषण और नजदीकी चिकित्सा सेवा",
        "panel1_title": "एआई स्वास्थ्य एवं लक्षण विश्लेषण",
        "panel2_title": "मेडिकल रिपोर्ट एवं पर्ची विश्लेषक",
        "panel3_title": "नजदीकी चिकित्सा केंद्र खोजें",
        "lang_select": "भाषा चुनें",
        "basic_info": "1. सामान्य जानकारी एवं आयु वर्ग",
        "age_group": "आयु वर्ग (Age Group)",
        "gender": "लिंग (Gender)",
        "geo_context": "2. भौगोलिक स्वास्थ्य संदर्भ (स्थान)",
        "state": "राज्य (State)",
        "district": "जिला / शहर (City / District)",
        "symptoms_header": "3. अपने लक्षण चुनें",
        "symptom_search": "लक्षण खोजें और चुनें...",
        "duration_header": "4. लक्षण कितने समय से हैं? (Duration)",
        "existing_conditions": "5. पूर्व स्वास्थ्य स्थितियां (Medical History)",
        "bp": "रक्तचाप (Blood Pressure)",
        "diabetes": "मधुमेह (Diabetes / Sugar)",
        "heart": "हृदय संबंधी स्थिति (Heart Condition)",
        "other_conditions": "अन्य बीमारियां या स्वास्थ्य इतिहास",
        "current_meds": "6. वर्तमान में ली जा रही दवाइयां (Current Medicines)",
        "analyze_btn": "स्वास्थ्य एवं लक्षणों का विश्लेषण करें",
        "urgency_critical": "तत्काल चिकित्सा सहायता की आवश्यकता हो सकती है",
        "urgency_critical_sub": "गंभीर चेतावनी संकेत मिले हैं। कृपया तुरंत नजदीकी अस्पताल या आपातकालीन कक्ष में संपर्क करें।",
        "find_hospital_btn": "नजदीकी आपातकालीन अस्पताल खोजें",
        "possible_conditions": "संभावित स्वास्थ्य स्थितियां (एआई मार्गदर्शन)",
        "condition_note": "यह संभावना केवल प्राथमिक संदर्भ के लिए है। यह डॉक्टर के व्यक्तिगत निदान का विकल्प नहीं है।",
        "medicines_info": "दवा संबंधी सामान्य जानकारी एवं सुरक्षा",
        "medicine_disclaimer": "यह जानकारी केवल सामान्य ज्ञान के लिए है। बिना योग्य डॉक्टर या फार्मासिस्ट की सलाह के कोई भी दवा न लें।",
        "diet_guidance": "आहार एवं पोषण संबंधी सलाह",
        "do_and_dont": "क्या करें और किन बातों से बचें",
        "yoga_physio": "सहायक योग एवं फिजियोथेरेपी मार्गदर्शन",
        "pdf_download": "संपूर्ण पीडीएफ स्वास्थ्य रिपोर्ट डाउनलोड करें",
        "report_summary": "रिपोर्ट सारांश एवं मुख्य निष्कर्ष",
        "report_normal": "सामान्य संदर्भ सीमा के भीतर",
        "report_warning": "ध्यान देने योग्य / सीमा से बाहर",
        "report_urgent": "डॉक्टर से तत्काल चर्चा करें",
        "nearby_search_btn": "नजदीकी स्वास्थ्य सुविधाएं खोजें",
        "pharmacy": "दवा की दुकानें (मेडिकल स्टोर)",
        "hospital": "अस्पताल एवं क्लीनिक",
        "diagnostic": "पैथोलॉजी व डायग्नोस्टिक लैब",
        "blood_bank": "ब्लड बैंक"
    }

    gu = {
        "app_title": "મેડીમાઈન્ડ એઆઈ — તમારો બુદ્ધિશાળી હેલ્થકેર સાથી",
        "app_subtitle": "એઆઈ-સંચાલિત ત્રિભાષી આરોગ્ય, તબીબી રિપોર્ટ વિશ્લેષણ અને નજીકની આરોગ્ય સેવાઓ",
        "panel1_title": "એઆઈ આરોગ્ય અને લક્ષણ વિશ્લેષણ",
        "panel2_title": "મેડિકલ રિપોર્ટ અને પ્રિસ્ક્રિપ્શન વિશ્લેષક",
        "panel3_title": "નજીકની આરોગ્ય સુવિધાઓ શોધો",
        "lang_select": "ભાષા પસંદ કરો",
        "basic_info": "1. પ્રાથમિક વિગતો અને વય જૂથ",
        "age_group": "વય જૂથ (Age Group)",
        "gender": "જાતિ (Gender)",
        "geo_context": "2. ભૌગોલિક આરોગ્ય સંદર્ભ (સ્થાન)",
        "state": "રાજ્ય (State)",
        "district": "શહેર / જિલ્લો (City / District)",
        "symptoms_header": "3. લક્ષણો પસંદ કરો",
        "symptom_search": "લક્ષણો શોધો અને પસંદ કરો...",
        "duration_header": "4. લક્ષણો કેટલા સમયથી છે? (Duration)",
        "existing_conditions": "5. હાલની આરોગ્ય પરિસ્થિતિઓ (Medical History)",
        "bp": "બ્લડ પ્રેશર (BP)",
        "diabetes": "ડાયાબિટીસ / શુગર",
        "heart": "હૃદયની બીમારી (Heart Condition)",
        "other_conditions": "અન્ય કોઈ બીમારી કે હિસ્ટ્રી",
        "current_meds": "6. હાલમાં ચાલુ દવાઓ (Current Medicines)",
        "analyze_btn": "આરોગ્ય અને લક્ષણોનું વિશ્લેષણ કરો",
        "urgency_critical": "તાત્કાલિક તબીબી સારવારની જરૂર પડી શકે છે",
        "urgency_critical_sub": "ગંભીર ચેતવણી સંકેતો જણાયા છે. કૃપા કરીને તાત્કાલિક નજીકની હોસ્પિટલનો સંપર્ક કરો.",
        "find_hospital_btn": "નજીકની ઇમરજન્સી હોસ્પિટલ શોધો",
        "possible_conditions": "સંભવિત આરોગ્ય સ્થિતિઓ (એઆઈ માર્ગદર્શન)",
        "condition_note": "આ સંભાવના ફક્ત પ્રાથમિક માર્ગદર્શન માટે છે. આ ડૉક્ટરના સચોટ નિદાનનો વિકલ્પ નથી.",
        "medicines_info": "દવાઓ વિશે સામાન્ય માહિતી અને સુરક્ષા",
        "medicine_disclaimer": "આ માહિતી ફક્ત સામાન્ય જાણકારી માટે છે. ડૉક્ટરની સલાહ વગર કોઈ પણ નવી દવા શરૂ કે બંધ કરશો નહીં.",
        "diet_guidance": "ખોરાક અને પોષણ સંબંધિત માર્ગદર્શન",
        "do_and_dont": "શું કરવું અને શું ન કરવું (કાળજી)",
        "yoga_physio": "મદદરૂપ યોગાસન અને ફિઝિયોથેરાપી માર્ગદર્શન",
        "pdf_download": "સંપૂર્ણ પીડીએફ હેલ્થ રિપોર્ટ ડાઉનલોડ કરો",
        "report_summary": "રિપોર્ટ સારાંશ અને મુખ્ય તારણો",
        "report_normal": "સામાન્ય રેન્જમાં છે",
        "report_warning": "ધ્યાન આપવા જેવું / રેન્જ બહાર",
        "report_urgent": "ડૉક્ટર સાથે તાત્કાલિક ચર્ચા કરો",
        "nearby_search_btn": "નજીકની હોસ્પિટલ અને મેડિકલ શોધો",
        "pharmacy": "મેડિકલ સ્ટોર / ફાર્મસી",
        "hospital": "હોસ્પિટલ અને ક્લિનિક",
        "diagnostic": "પેથોલોજી અને લેબોરેટરી",
        "blood_bank": "બ્લડ બેંક"
    }

    with open("translations/english.json", "w", encoding="utf-8") as f:
        json.dump(en, f, ensure_ascii=False, indent=2)
    with open("translations/hindi.json", "w", encoding="utf-8") as f:
        json.dump(hi, f, ensure_ascii=False, indent=2)
    with open("translations/gujarati.json", "w", encoding="utf-8") as f:
        json.dump(gu, f, ensure_ascii=False, indent=2)
    print("[OK] Generated translations for English, Hindi, and Gujarati in translations/")

if __name__ == "__main__":
    generate_condition_guidance()
    generate_yoga_and_physio()
    generate_lab_and_medical_dictionaries()
    generate_india_geo_master()
    generate_translations()
