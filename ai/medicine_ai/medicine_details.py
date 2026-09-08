"""
    Medicine Compound & Clinical Pharmacological Information Engine
Provides comprehensive chemical compound breakdowns, active pharmaceutical ingredients (APIs),
therapeutic mechanisms, indications, contraindications, and safety guidance for medications.
"""
import re

# Comprehensive Clinical Compound Database
MEDICINE_COMPOUND_DATABASE = {
    "paracetamol": {
        "generic_name": "Paracetamol / Acetaminophen IP",
        "brand_names": ["Dolo 650", "Calpol 650", "Crocin 650", "Pacimol", "P-650"],
        "active_compounds": [
            {
                "compound_name": "Paracetamol (Acetaminophen)",
                "molecular_formula": "C8H9NO2",
                "strength": "650 mg per tablet",
                "role": "Active Antipyretic & Analgesic Agent"
            }
        ],
        "therapeutic_category": "Non-Opioid Analgesic & Central Antipyretic",
        "mechanism_of_action": "Inhibits prostaglandin synthesis in the Central Nervous System (CNS) by blocking COX enzyme pathways. Selectively acts on the hypothalamic heat-regulating center to produce peripheral vasodilation and sweating, effectively lowering elevated body temperature.",
        "primary_indications": [
            "Fever and pyrexia of varied etiologies",
            "Mild to moderate tension headaches & migraines",
            "Body aches, myalgia, and joint discomfort",
            "Post-vaccination or viral fever management"
        ],
        "dosage_administration": "1 tablet (650mg) orally every 6 to 8 hours with water after meals. Maximum daily limit: 3000mg in 24 hours.",
        "contraindications": [
            "Severe active hepatic impairment or acute liver failure",
            "Known hypersensitivity to paracetamol",
            "Chronic alcoholism or heavy alcohol consumption"
        ],
        "side_effects": {
            "common": ["Generally well tolerated at therapeutic doses", "Mild nausea"],
            "rare": ["Skin rash, urticaria", "Elevated hepatic transaminases (with chronic high dosage)"]
        },
        "drug_interactions": "Avoid concurrent use with other paracetamol-containing cold/cough formulations. Consult physician if on warfarin or cholestyramine."
    },
    "ibuprofen": {
        "generic_name": "Ibuprofen IP",
        "brand_names": ["Brufen 400", "Ibugesic 400", "Combiflam (with Paracetamol)", "Advil", "Nurofen"],
        "active_compounds": [
            {
                "compound_name": "Ibuprofen (Propionic acid derivative)",
                "molecular_formula": "C13H18O2",
                "strength": "400 mg per tablet",
                "role": "Non-Steroidal Anti-Inflammatory Drug (NSAID)"
            }
        ],
        "therapeutic_category": "NSAID (Anti-inflammatory, Analgesic, Antipyretic)",
        "mechanism_of_action": "Non-selectively inhibits Cyclooxygenase-1 (COX-1) and Cyclooxygenase-2 (COX-2) enzymes, reducing the biosynthesis of pro-inflammatory prostaglandins and thromboxanes responsible for pain, localized swelling, and inflammatory cascades.",
        "primary_indications": [
            "Inflammatory tension headaches & acute migraines",
            "Musculoskeletal pain, neck stiffness, and sprains",
            "Joint pain, arthritis, and dental discomfort",
            "Fever associated with acute inflammatory conditions"
        ],
        "dosage_administration": "1 tablet (400mg) orally 2 to 3 times daily immediately after meals or with milk to prevent gastric irritation.",
        "contraindications": [
            "Active peptic ulcer disease or history of GI bleeding",
            "Severe renal impairment (GFR < 30 mL/min)",
            "Third trimester of pregnancy",
            "Aspirin-induced asthma or bronchospasm"
        ],
        "side_effects": {
            "common": ["Gastric discomfort, heartburn, acidity", "Mild dyspepsia", "Nausea"],
            "rare": ["Gastric ulceration", "Fluid retention", "Renal stress"]
        },
        "drug_interactions": "Do not co-administer with other systemic NSAIDs, oral anticoagulants, or systemic corticosteroids without gastroprotective shield (PPI)."
    },
    "pantoprazole": {
        "generic_name": "Pantoprazole Sodium IP",
        "brand_names": ["Pan 40", "Pantocid 40", "Pantodac", "Protium", "Pan-D (with Domperidone)"],
        "active_compounds": [
            {
                "compound_name": "Pantoprazole Sodium Sesquihydrate",
                "molecular_formula": "C16H14F2N3NaO4S · 1.5H2O",
                "strength": "40 mg (equivalent to Pantoprazole)",
                "role": "Gastric Proton Pump Inhibitor (PPI)"
            }
        ],
        "therapeutic_category": "Proton Pump Inhibitor (Gastric Acid Suppressant)",
        "mechanism_of_action": "Irreversibly binds and inhibits the H+/K+-ATPase enzyme system (the proton pump) in the parietal cells of the stomach, blocking the final shared pathway of basal and stimulated gastric hydrochloric acid secretion.",
        "primary_indications": [
            "Gastric mucosal protection against NSAID-induced acidity",
            "Gastroesophageal Reflux Disease (GERD) & heartburn",
            "Peptic, gastric, and duodenal ulcers",
            "Zollinger-Ellison syndrome & hypersecretory states"
        ],
        "dosage_administration": "1 tablet (40mg) swallowed whole with a glass of water in the morning, 30 to 60 minutes before breakfast on an empty stomach.",
        "contraindications": [
            "Known hypersensitivity to substituted benzimidazoles",
            "Co-administration with rilpivirine or atazanavir"
        ],
        "side_effects": {
            "common": ["Mild headache", "Diarrhea or mild constipation", "Abdominal flatulence"],
            "rare": ["Hypomagnesemia (with prolonged multi-year therapy)", "Vitamin B12 deficiency"]
        },
        "drug_interactions": "May reduce absorption of pH-dependent medications such as ketoconazole, iron salts, and atazanavir."
    },
    "ors": {
        "generic_name": "Oral Rehydration Salts (WHO Formula) IP",
        "brand_names": ["Electral", "WHO-ORS", "Walyte", "Reliance ORS", "Enerzal"],
        "active_compounds": [
            {
                "compound_name": "Sodium Chloride IP",
                "molecular_formula": "NaCl",
                "strength": "2.60 g per sachet",
                "role": "Essential Extracellular Electrolyte"
            },
            {
                "compound_name": "Potassium Chloride IP",
                "molecular_formula": "KCl",
                "strength": "1.50 g per sachet",
                "role": "Essential Intracellular Electrolyte & Cardiac Stabilizer"
            },
            {
                "compound_name": "Sodium Citrate Dihydrate IP",
                "molecular_formula": "C6H5Na3O7 · 2H2O",
                "strength": "2.90 g per sachet",
                "role": "Systemic Alkalinizing Agent against Acidosis"
            },
            {
                "compound_name": "Dextrose Anhydrous IP",
                "molecular_formula": "C6H12O6",
                "strength": "13.50 g per sachet",
                "role": "Sodium Co-transport Glucose Driver"
            }
        ],
        "therapeutic_category": "Electrolyte Replenisher & Rehydration Solution",
        "mechanism_of_action": "Utilizes the active sodium-glucose co-transport mechanism in the small intestinal brush border. Even during diarrheal or febrile illness, glucose promotes equimolar coupled absorption of sodium and water into systemic circulation, rapidly restoring intravascular volume.",
        "primary_indications": [
            "Dehydration and electrolyte depletion caused by fever, heat exhaustion, or vomiting",
            "Dizziness, lightheadedness, and weakness due to fluid loss",
            "Supportive rehydration during acute gastrointestinal infections"
        ],
        "dosage_administration": "Dissolve entire sachet in exactly 1 Litre (1000 mL) of boiled and cooled drinking water. Sip continuously throughout the day.",
        "contraindications": [
            "Intractable persistent vomiting requiring IV rehydration",
            "Severe intestinal obstruction (paralytic ileus)",
            "Severe acute anuria or renal failure"
        ],
        "side_effects": {
            "common": ["Safe and physiological when reconstituted in exact water proportions"],
            "rare": ["Hypernatremia (only if mixed with inadequate water)"]
        },
        "drug_interactions": "None significant. Do not mix with juices or carbonated sodas as osmotic balance will be altered."
    },
    "levocetirizine": {
        "generic_name": "Levocetirizine Dihydrochloride IP",
        "brand_names": ["Levocet 5", "Xyzal 5", "1-AL 5", "L-Hist", "Vozet"],
        "active_compounds": [
            {
                "compound_name": "Levocetirizine Dihydrochloride",
                "molecular_formula": "C21H25ClN2O3 · 2HCl",
                "strength": "5 mg per tablet",
                "role": "Selective H1-Receptor Antagonist (Active R-Enantiomer of Cetirizine)"
            }
        ],
        "therapeutic_category": "Second-Generation Non-Sedating Antihistamine",
        "mechanism_of_action": "Potent, highly selective competitive antagonist of peripheral H1 histamine receptors. Inhibits histamine-mediated capillary permeability, mucosal edema, pruritus, and allergic sneezing with significantly reduced blood-brain barrier penetration.",
        "primary_indications": [
            "Allergic rhinitis, sneezing, runny nose, and watery eyes",
            "Upper respiratory tract irritation and allergic cough",
            "Chronic idiopathic urticaria and skin allergic rashes"
        ],
        "dosage_administration": "1 tablet (5mg) orally once daily at bedtime with water, with or without food.",
        "contraindications": [
            "End-stage renal disease (CrCl < 10 mL/min)",
            "Known hypersensitivity to cetirizine or hydroxyzine"
        ],
        "side_effects": {
            "common": ["Mild somnolence / drowsiness (at night)", "Dry mouth", "Fatigue"],
            "rare": ["Transient headache", "Mild asthenia"]
        },
        "drug_interactions": "Additive CNS depression when combined with sedatives or alcohol. Avoid driving if feeling drowsy."
    },
    "azithromycin": {
        "generic_name": "Azithromycin Dihydrate IP",
        "brand_names": ["Azee 500", "Azithral 500", "Zithromax", "Azimax"],
        "active_compounds": [
            {
                "compound_name": "Azithromycin Dihydrate",
                "molecular_formula": "C38H72N2O12 · 2H2O",
                "strength": "500 mg per tablet",
                "role": "Broad-Spectrum Azalide (Macrolide) Antibacterial"
            }
        ],
        "therapeutic_category": "Macrolide Antibiotic",
        "mechanism_of_action": "Binds reversibly to the 50S ribosomal subunit of susceptible microorganisms, inhibiting transpeptidation and protein synthesis, resulting in bacteriostatic and bactericidal action.",
        "primary_indications": [
            "Bacterial upper and lower respiratory tract infections",
            "Bacterial pharyngitis, tonsillitis, and acute sinusitis",
            "Community-acquired pneumonia and bronchopulmonary infections"
        ],
        "dosage_administration": "1 tablet (500mg) once daily for 3 consecutive days, taken 1 hour before or 2 hours after meals.",
        "contraindications": [
            "History of cholestatic jaundice or hepatic dysfunction associated with prior azithromycin use",
            "Known prolonged cardiac QT interval or severe arrhythmia"
        ],
        "side_effects": {
            "common": ["Nausea, abdominal cramps", "Diarrhea", "Mild headache"],
            "rare": ["QT prolongation", "Transient liver enzyme elevation"]
        },
        "drug_interactions": "Antacids containing aluminum or magnesium reduce peak serum concentrations; separate doses by at least 2 hours."
    }
}

def get_medicine_details(medicine_name: str) -> dict:
    """
    Retrieves rich pharmacological profile for a given medicine.
    Falls back to dynamically synthesized clinical structure if not in static catalog.
    """
    med_lower = (medicine_name or "").lower().strip()
    
    # Check matching key
    for key, data in MEDICINE_COMPOUND_DATABASE.items():
        if key in med_lower or any(b.lower() in med_lower for b in data.get("brand_names", [])):
            return data

    # Dynamic clinical fallback synthesis
    clean_name = re.sub(r'[\(\)\d\+mg\/]', '', medicine_name).strip()
    return {
        "generic_name": f"{clean_name} Formulation",
        "brand_names": [medicine_name],
        "active_compounds": [
            {
                "compound_name": clean_name or "Therapeutic Active Agent",
                "molecular_formula": "Standard Pharmacopeial Formulation",
                "strength": "Standard Clinical Strength",
                "role": "Active Therapeutic Agent"
            }
        ],
        "therapeutic_category": "Standard Clinical Therapeutic Formulation",
        "mechanism_of_action": f"Pharmacologically formulated active compound designed for targeted symptomatic relief and clinical stabilization under medical direction.",
        "primary_indications": [
            f"Indicated for clinical symptom management as assessed in your triage session.",
            "Restores physiological balance and supports recovery."
        ],
        "dosage_administration": "Take strictly as prescribed on packaging or advised by consulting physician.",
        "contraindications": [
            "Known drug hypersensitivity",
            "Consult physician if pregnant or having pre-existing renal/hepatic conditions."
        ],
        "side_effects": {
            "common": ["Mild gastrointestinal discomfort if taken on empty stomach"],
            "rare": ["Allergic hypersensitivity (discontinue if rash occurs)"]
        },
        "drug_interactions": "Always inform your doctor of all ongoing medications before starting new treatments."
    }
