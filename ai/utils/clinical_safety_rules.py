"""
DocMindX AI — Clinical Safety, Contraindication & Pharmacovigilance Rules Engine
Provides:
1. Pre-existing condition contraindication gating (e.g. Hypertension, Asthma, CKD, PUD, Cirrhosis).
2. Drug allergy and immunological cross-reactivity detection (e.g. Penicillin, Sulfa, NSAIDs).
3. Drug-Drug interaction (DDI) risk assessment (e.g. Warfarin + NSAID, SSRI + Tramadol).
4. Special population safety gating (Pregnancy trimesters, Lactation, ESRD, G6PD, Glaucoma).
"""
import re
from typing import Dict, List, Any, Optional, Set, Tuple

# ------------------------------------------------------------------------------
# 1. ALLERGY & CROSS-REACTIVITY RULES
# ------------------------------------------------------------------------------
ALLERGY_CROSS_REACTIVITY_MAP = {
    "penicillin": {
        "class_name": "Penicillin & Beta-Lactam Antibiotics",
        "disallowed_patterns": [
            r"penicillin", r"amoxicillin", r"ampicillin", r"augmentin", r"amox\b",
            r"piperacillin", r"tazobactam", r"cloxacillin", r"methicillin", r"oxacillin",
            r"moxclav", r"amoxyclav"
        ]
    },
    "sulfa": {
        "class_name": "Sulfonamides",
        "disallowed_patterns": [
            r"sulfa", r"sulfonamide", r"co-trimoxazole", r"cotrimoxazole", r"sulfamethoxazole",
            r"trimethoprim", r"bactrim", r"septra", r"sulfasalazine", r"dapsone"
        ]
    },
    "nsaid": {
        "class_name": "Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)",
        "disallowed_patterns": [
            r"aspirin", r"ibuprofen", r"diclofenac", r"naproxen", r"ketorolac",
            r"indomethacin", r"piroxicam", r"meloxicam", r"celecoxib", r"etoricoxib",
            r"combiflam", r"voveran", r"brufen"
        ]
    },
    "aspirin": {
        "class_name": "Aspirin / Salicylates",
        "disallowed_patterns": [
            r"aspirin", r"acetylsalicylic", r"disprin", r"ecosprin", r"ibuprofen",
            r"diclofenac", r"naproxen", r"nsaid"
        ]
    },
    "cephalosporin": {
        "class_name": "Cephalosporins",
        "disallowed_patterns": [
            r"cephalosporin", r"cefixime", r"ceftriaxone", r"cephalexin", r"cefadroxil",
            r"cefuroxime", r"cefotaxime", r"cefepime", r"cefpodoxime", r"taxim"
        ]
    },
    "fluoroquinolone": {
        "class_name": "Fluoroquinolones",
        "disallowed_patterns": [
            r"fluoroquinolone", r"quinolone", r"ciprofloxacin", r"levofloxacin",
            r"ofloxacin", r"moxifloxacin", r"norfloxacin", r"cipro\b"
        ]
    },
    "macrolide": {
        "class_name": "Macrolides",
        "disallowed_patterns": [
            r"macrolide", r"azithromycin", r"clarithromycin", r"erythromycin",
            r"roxithromycin", r"azee", r"zithromax"
        ]
    },
    "codeine": {
        "class_name": "Opioids / Codeine",
        "disallowed_patterns": [
            r"codeine", r"co-codamol", r"corex", r"codistar", r"tramadol", r"morphine"
        ]
    },
    "paracetamol": {
        "class_name": "Acetaminophen / Paracetamol",
        "disallowed_patterns": [
            r"paracetamol", r"acetaminophen", r"dolo", r"calpol", r"crocin", r"pacimol"
        ]
    },
    "metronidazole": {
        "class_name": "Nitroimidazoles",
        "disallowed_patterns": [
            r"metronidazole", r"flagyl", r"tinidazole", r"ornidazole"
        ]
    }
}

# ------------------------------------------------------------------------------
# 2. MEDICAL CONDITION CONTRAINDICATION RULES
# ------------------------------------------------------------------------------
CONDITION_CONTRAINDICATIONS_MAP = {
    "hypertension": {
        "condition_name": "Hypertension",
        "contraindicated_classes": ["Oral Decongestants (Pseudoephedrine, Phenylephrine)", "Systemic NSAIDs (chronic)"],
        "disallowed_patterns": [r"pseudoephedrine", r"phenylephrine", r"sudafed", r"decongestant"],
        "clinical_guidance": "Avoid decongestants like pseudoephedrine as they produce systemic vasoconstriction and precipitate hypertensive crisis."
    },
    "diabetes": {
        "condition_name": "Type 2 Diabetes",
        "contraindicated_classes": ["Sugar-containing Syrups", "High-Dose Systemic Corticosteroids (unmonitored)"],
        "disallowed_patterns": [r"sugar.*syrup", r"sucrose.*syrup", r"cough.*syrup.*sugar"],
        "clinical_guidance": "Avoid sugar syrups, cautious steroids. Use sugar-free formulations and monitor blood glucose closely."
    },
    "asthma": {
        "condition_name": "Bronchial Asthma",
        "contraindicated_classes": ["NSAIDs (Aspirin-Exacerbated Respiratory Disease)", "Non-Selective Beta Blockers"],
        "disallowed_patterns": [r"aspirin", r"ibuprofen", r"diclofenac", r"naproxen", r"propranolol", r"timolol", r"atenolol", r"carvedilol", r"nsaid"],
        "clinical_guidance": "NSAIDs / Non-selective beta blockers contraindicated due to risk of life-threatening bronchospasm."
    },
    "chronic kidney disease": {
        "condition_name": "Chronic Kidney Disease",
        "contraindicated_classes": ["Systemic NSAIDs", "Nephrotoxic Aminoglycosides"],
        "disallowed_patterns": [r"ibuprofen", r"diclofenac", r"naproxen", r"gentamicin", r"amikacin", r"nsaid"],
        "clinical_guidance": "NSAIDs contraindicated, dosage adjustments needed. NSAIDs inhibit renal prostaglandins and trigger acute-on-chronic renal decline."
    },
    "peptic ulcer": {
        "condition_name": "Peptic Ulcer Disease",
        "contraindicated_classes": ["Systemic NSAIDs", "Aspirin", "Antiplatelets (without gastroprotection)"],
        "disallowed_patterns": [r"aspirin", r"ibuprofen", r"diclofenac", r"naproxen", r"ketorolac", r"nsaid"],
        "clinical_guidance": "Aspirin & NSAIDs contraindicated due to GI bleed. High risk of gastric perforation and ulcer reactivation."
    },
    "liver cirrhosis": {
        "condition_name": "Liver Cirrhosis",
        "contraindicated_classes": ["High-Dose Paracetamol (>2g/day)", "NSAIDs", "Hepatotoxic Drugs"],
        "disallowed_patterns": [r"paracetamol\s+(?:1000|650|1g|2g|high)", r"diclofenac"],
        "clinical_guidance": "High-dose paracetamol contraindicated. Impaired hepatic glutathione conjugation increases hepatotoxicity risk."
    },
    "epilepsy": {
        "condition_name": "Epilepsy",
        "contraindicated_classes": ["Seizure-Threshold Lowering Drugs (Tramadol, Bupropion, Fluoroquinolones)"],
        "disallowed_patterns": [r"tramadol", r"bupropion", r"ciprofloxacin", r"ofloxacin"],
        "clinical_guidance": "Tramadol & fluoroquinolones lower seizure threshold, increasing seizure frequency and provoking breakthrough status."
    },
    "coronary artery disease": {
        "condition_name": "Coronary Artery Disease",
        "contraindicated_classes": ["Selective COX-2 Inhibitors", "High-Dose NSAIDs"],
        "disallowed_patterns": [r"celecoxib", r"etoricoxib"],
        "clinical_guidance": "Selective COX-2 inhibitors caution. Associated with increased risk of thrombotic cardiovascular events."
    },
    "hypothyroidism": {
        "condition_name": "Hypothyroidism",
        "contraindicated_classes": ["Simultaneous Iron/Calcium Binding Agents"],
        "disallowed_patterns": [r"calcium", r"ferrous", r"iron"],
        "clinical_guidance": "Calcium / Iron supplements spaced 4 hours. Mineral cations bind levothyroxine and severely impair intestinal absorption."
    },
    "gout": {
        "condition_name": "Gout",
        "contraindicated_classes": ["Thiazide and Loop Diuretics", "Low-Dose Aspirin"],
        "disallowed_patterns": [r"hydrochlorothiazide", r"chlorthalidone", r"furosemide"],
        "clinical_guidance": "Thiazide diuretics contraindicated. Diuretics reduce renal urate excretion and provoke acute gouty flares."
    },
    "heart failure": {
        "condition_name": "Heart Failure",
        "contraindicated_classes": ["Non-dihydropyridine CCBs (Verapamil, Diltiazem)", "NSAIDs"],
        "disallowed_patterns": [r"verapamil", r"diltiazem", r"ibuprofen", r"diclofenac", r"nsaid"],
        "clinical_guidance": "Verapamil and Diltiazem contraindicated in HFrEF due to negative inotropic depression and worsening fluid retention."
    }
}

# ------------------------------------------------------------------------------
# 3. DRUG-DRUG INTERACTION (DDI) RULES
# ------------------------------------------------------------------------------
DRUG_INTERACTIONS_MAP = [
    {
        "drug_pair": ("warfarin", "nsaid"),
        "patterns": (r"warfarin|coumadin", r"ibuprofen|diclofenac|aspirin|naproxen|nsaid"),
        "risk_level": "Severe",
        "interaction_risk": "Warfarin + NSAIDs increases major hemorrhage risk. Concurrent use dramatically increases gastrointestinal and systemic bleeding."
    },
    {
        "drug_pair": ("ace_inhibitor", "potassium_sparing"),
        "patterns": (r"lisinopril|enalapril|ramipril|captopril|perindopril", r"spironolactone|eplerenone|amiloride|triamterene|potassium"),
        "risk_level": "Severe",
        "interaction_risk": "ACE inhibitors + Potassium sparing diuretics hyperkalemia. Risk of fatal cardiac dysrhythmias from elevated serum potassium."
    },
    {
        "drug_pair": ("digoxin", "macrolide"),
        "patterns": (r"digoxin|lanoxin", r"clarithromycin|erythromycin"),
        "risk_level": "Severe",
        "interaction_risk": "Digoxin + Clarithromycin increases digoxin toxicity. Inactivation of gut flora and P-glycoprotein inhibition causes dangerous digoxin accumulation."
    },
    {
        "drug_pair": ("ssri", "tramadol"),
        "patterns": (r"sertraline|fluoxetine|paroxetine|citalopram|escitalopram", r"tramadol|ultram"),
        "risk_level": "Severe",
        "interaction_risk": "SSRI + Tramadol increases serotonin syndrome risk. Synergistic serotonergic elevation leads to neuromuscular hyperactivity and autonomic instability."
    },
    {
        "drug_pair": ("clopidogrel", "omeprazole"),
        "patterns": (r"clopidogrel|plavix", r"omeprazole|esomeprazole"),
        "risk_level": "Moderate",
        "interaction_risk": "Clopidogrel + Omeprazole reduces antiplatelet efficacy. CYP2C19 competitive inhibition reduces clopidogrel activation, increasing stent thrombosis risk."
    },
    {
        "drug_pair": ("sulfonylurea", "azole"),
        "patterns": (r"glimepiride|gliclazide|glipizide|glyburide", r"fluconazole|itraconazole|voriconazole"),
        "risk_level": "Severe",
        "interaction_risk": "Sulfonylurea + Fluconazole increases severe hypoglycemia. CYP2C9 inhibition impairs sulfonylurea clearance, leading to prolonged hypoglycemic coma."
    },
    {
        "drug_pair": ("alpha_blocker", "pde5_inhibitor"),
        "patterns": (r"tamsulosin|doxazosin|terazosin|silodosin", r"sildenafil|tadalafil|vardenafil"),
        "risk_level": "Severe",
        "interaction_risk": "Alpha blockers + PDE5 inhibitors severe orthostatic hypotension. Additive systemic vasodilation causes profound hypotension and syncope."
    },
    {
        "drug_pair": ("statin", "macrolide"),
        "patterns": (r"simvastatin|atorvastatin|lovastatin", r"erythromycin|clarithromycin"),
        "risk_level": "Severe",
        "interaction_risk": "Simvastatin + Erythromycin increases rhabdomyolysis risk. CYP3A4 inhibition elevates statin plasma levels, precipitating myopathy and acute kidney injury."
    },
    {
        "drug_pair": ("calcineurin_inhibitor", "azole"),
        "patterns": (r"tacrolimus|cyclosporine", r"fluconazole|itraconazole|voriconazole|ketoconazole"),
        "risk_level": "Severe",
        "interaction_risk": "Tacrolimus + Azole antifungals increases nephrotoxicity. CYP3A4 and P-gp inhibition causes toxic calcineurin inhibitor blood levels."
    },
    {
        "drug_pair": ("bisphosphonate", "nsaid"),
        "patterns": (r"alendronate|risedronate|zoledronic|ibandronate", r"ibuprofen|diclofenac|naproxen|aspirin|nsaid"),
        "risk_level": "Moderate",
        "interaction_risk": "Bisphosphonates + NSAIDs increases severe esophageal ulceration. Synergistic upper gastrointestinal mucosal toxicity and ulceration."
    }
]

# ------------------------------------------------------------------------------
# 4. SPECIAL POPULATIONS & ORGAN IMPAIRMENT RULES
# ------------------------------------------------------------------------------
SPECIAL_POPULATIONS_MAP = {
    "pediatric": {
        "condition_pattern": r"pediatric|child|infant|\b0-10\b",
        "contraindicated": ["Aspirin (Reye's syndrome)", "Fluoroquinolones (arthropathy / cartilage toxicity)", "Tetracyclines (dental enamel dysplasia)"],
        "disallowed_patterns": [r"\baspirin\b", r"\bciprofloxacin\b", r"\blevofloxacin\b", r"\bfluoroquinolone\b", r"\btetracycline\b", r"\bdoxycycline\b"],
        "guidance": "Aspirin risk of Reye's syndrome in pediatrics; Fluoroquinolones risk cartilage damage; Tetracyclines cause tooth discoloration."
    },
    "geriatric": {
        "condition_pattern": r"geriatric|elderly|61\+|senior",
        "contraindicated": ["High dose long-acting benzodiazepines (Beers criteria fall/sedation risk)", "Anticholinergics"],
        "disallowed_patterns": [r"benzodiazepine", r"diazepam", r"flurazepam", r"clonazepam", r"chlordiazepoxide"],
        "guidance": "Beers criteria 2023: Long-acting benzodiazepines increase ataxia, fall risk, and cognitive impairment in older adults."
    },
    "pregnancy_all": {
        "condition_pattern": r"\bpregnancy\b|\bpregnant\b",
        "contraindicated": ["ACE Inhibitors (fetopathy / renal dysgenesis)", "Statins", "Methotrexate", "Warfarin", "NSAIDs in 3rd trimester"],
        "disallowed_patterns": [r"lisinopril|ramipril|enalapril|captopril|ace\s*inhibitor", r"losartan|valsartan|telmisartan", r"methotrexate", r"warfarin", r"atorvastatin|simvastatin|rosuvastatin", r"ibuprofen|diclofenac|naproxen|aspirin|indomethacin"],
        "guidance": "Teratogenic and fetotoxic agents strictly contraindicated across pregnancy."
    },
    "pregnancy_1st_trimester": {
        "condition_pattern": r"pregnancy.*(?:1st|first)|1st.*trimester|first.*trimester",
        "contraindicated": ["Methotrexate", "Warfarin", "ACE inhibitors", "Statins", "Valproate", "Isotretinoin"],
        "disallowed_patterns": [r"methotrexate", r"warfarin", r"lisinopril|ramipril|enalapril", r"atorvastatin|simvastatin", r"valproat", r"isotretinoin"],
        "guidance": "Category X/D teratogens strictly contraindicated in 1st trimester organogenesis."
    },
    "pregnancy_3rd_trimester": {
        "condition_pattern": r"pregnancy.*(?:3rd|third)|3rd.*trimester|third.*trimester",
        "contraindicated": ["NSAIDs (premature closure of ductus arteriosus)"],
        "disallowed_patterns": [r"ibuprofen", r"diclofenac", r"naproxen", r"indomethacin", r"aspirin", r"nsaid"],
        "guidance": "NSAIDs in third trimester provoke premature closure of the fetal ductus arteriosus and oligohydramnios."
    },
    "lactation": {
        "condition_pattern": r"lactation|breastfeeding|nursing.*mother",
        "cautious": ["Amiodarone", "Codeine", "Tetracyclines"],
        "disallowed_patterns": [r"amiodarone", r"codeine", r"tetracycline", r"doxycycline"],
        "guidance": "Drugs excreted in breast milk with significant neonatal toxicity risk."
    },
    "esrd": {
        "condition_pattern": r"esrd|end-stage\s+renal|dialysis|stage\s+5\s+ckd",
        "contraindicated": ["Metformin", "Aminoglycosides", "NSAIDs"],
        "disallowed_patterns": [r"metformin", r"gentamicin", r"amikacin", r"ibuprofen", r"diclofenac", r"nsaid"],
        "guidance": "Metformin risk of lactic acidosis; aminoglycosides and NSAIDs aggravate anuric/oliguric failure."
    },
    "acute_hepatitis": {
        "condition_pattern": r"acute.*hepatitis|hepatitis|severe\s+liver|hepatic\s+failure",
        "contraindicated": ["High-dose Acetaminophen", "Isoniazid", "Ketoconazole"],
        "disallowed_patterns": [r"paracetamol", r"acetaminophen", r"isoniazid", r"ketoconazole"],
        "guidance": "Compromised hepatic clearance precipitates acute encephalopathy and toxic necrosis."
    },
    "g6pd": {
        "condition_pattern": r"g6pd|glucose-6-phosphate",
        "contraindicated": ["Dapsone", "Primaquine", "Rasburicase", "Nitrofurantoin"],
        "disallowed_patterns": [r"dapsone", r"primaquine", r"rasburicase", r"nitrofurantoin"],
        "guidance": "Oxidative stress triggers severe intravascular hemolysis and acute hemoglobinuria."
    },
    "myasthenia_gravis": {
        "condition_pattern": r"myasthenia\s+gravis",
        "contraindicated": ["Aminoglycosides", "Telithromycin", "Fluoroquinolones"],
        "disallowed_patterns": [r"gentamicin", r"amikacin", r"tobramycin", r"ciprofloxacin", r"levofloxacin", r"telithromycin"],
        "guidance": "Neuromuscular blocking properties precipitate severe myasthenic respiratory crisis."
    },
    "glaucoma": {
        "condition_pattern": r"narrow-angle\s+glaucoma|angle-closure\s+glaucoma|closed-angle\s+glaucoma",
        "contraindicated": ["Anticholinergics", "First gen antihistamines"],
        "disallowed_patterns": [r"atropine", r"scopolamine", r"diphenhydramine", r"chlorpheniramine", r"hydroxyzine"],
        "guidance": "Mydriatic pupillary dilation mechanically occludes trabecular outflow, triggering acute angle-closure glaucoma."
    },
    "hemophilia": {
        "condition_pattern": r"hemophilia|bleeding\s+diathesis|von\s+willebrand",
        "contraindicated": ["Anticoagulants", "Antiplatelets", "NSAIDs"],
        "disallowed_patterns": [r"heparin", r"warfarin", r"apixaban", r"aspirin", r"clopidogrel", r"ibuprofen", r"nsaid"],
        "guidance": "Impaired coagulation cascade causes uncontrollable mucosal and hemarthrotic hemorrhage."
    },
    "tuberculosis_att": {
        "condition_pattern": r"tuberculosis|active\s+tb|att\b|rifampicin",
        "contraindicated": ["Extensive CYP3A4 induction by Rifampicin"],
        "disallowed_patterns": [r"rifampicin"],
        "guidance": "Rifampicin is a potent enzyme inducer that substantially lowers therapeutic levels of oral contraceptives, anticoagulants, and antiretrovirals."
    }
}


class ClinicalSafetyRulesEngine:
    """Centralized Clinical Safety, Contraindication & Allergy Engine."""

    def __init__(self):
        pass

    def evaluate_allergies(
        self,
        patient_allergies: List[str],
        candidate_medication_names: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates patient allergies against candidate medications.
        Returns: {
            "is_safe": bool,
            "blocked_medications": List[str],
            "reasons": List[str]
        }
        """
        blocked = []
        reasons = []
        if not patient_allergies or not candidate_medication_names:
            return {"is_safe": True, "blocked_medications": [], "reasons": []}

        allergy_str = " ".join([str(a).lower() for a in patient_allergies])

        for key, info in ALLERGY_CROSS_REACTIVITY_MAP.items():
            # Check if patient has this allergy
            if key in allergy_str or (key == "nsaid" and "aspirin" in allergy_str) or (key == "sulfa" and "sulfonamide" in allergy_str):
                for med in candidate_medication_names:
                    med_lower = str(med).lower()
                    for pat in info["disallowed_patterns"]:
                        if re.search(pat, med_lower, re.IGNORECASE):
                            if med not in blocked:
                                blocked.append(med)
                                reasons.append(
                                    f"Medication '{med}' is contraindicated due to patient allergy to {info['class_name']}."
                                )
                            break

        return {
            "is_safe": len(blocked) == 0,
            "blocked_medications": blocked,
            "reasons": reasons
        }

    def evaluate_condition_contraindications(
        self,
        conditions: List[str],
        candidate_medication_names: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates patient conditions against candidate medications.
        """
        blocked = []
        guidance_alerts = []
        if not conditions:
            return {"is_safe": True, "blocked_medications": [], "guidance_alerts": []}

        cond_str = " ".join([str(c).lower() for c in conditions])

        for key, info in CONDITION_CONTRAINDICATIONS_MAP.items():
            if key in cond_str:
                guidance_alerts.append(info["clinical_guidance"])
                for med in candidate_medication_names:
                    med_lower = str(med).lower()
                    for pat in info["disallowed_patterns"]:
                        if re.search(pat, med_lower, re.IGNORECASE):
                            if med not in blocked:
                                blocked.append(med)
                            break

        return {
            "is_safe": len(blocked) == 0,
            "blocked_medications": blocked,
            "guidance_alerts": guidance_alerts
        }

    def evaluate_drug_drug_interactions(
        self,
        current_medications: List[str],
        candidate_medication_names: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates potential DDIs between ongoing medications and proposed candidate medications.
        """
        interactions = []
        if not current_medications:
            return {"has_interactions": False, "interactions": []}

        all_meds = [str(m).lower() for m in current_medications]
        all_meds_text = " ".join(all_meds)

        for rule in DRUG_INTERACTIONS_MAP:
            p1, p2 = rule["patterns"]
            # Check if ongoing meds match p1 and either candidate matches p2 or vice versa
            has_p1 = bool(re.search(p1, all_meds_text, re.IGNORECASE))
            if has_p1:
                # Check candidate medications or ongoing medications for p2
                cand_text = " ".join([str(m).lower() for m in candidate_medication_names])
                if re.search(p2, cand_text, re.IGNORECASE) or re.search(p2, all_meds_text, re.IGNORECASE):
                    interactions.append({
                        "risk_level": rule["risk_level"],
                        "interaction_risk": rule["interaction_risk"],
                        "drug_pair": rule["drug_pair"]
                    })

        return {
            "has_interactions": len(interactions) > 0,
            "interactions": interactions
        }

    def evaluate_special_populations(
        self,
        conditions: List[str],
        candidate_medication_names: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates pregnancy, lactation, organ failure, and genetic enzymopathies.
        """
        alerts = []
        blocked = []
        cond_str = " ".join([str(c).lower() for c in conditions])

        for key, info in SPECIAL_POPULATIONS_MAP.items():
            if re.search(info["condition_pattern"], cond_str, re.IGNORECASE):
                alerts.append({
                    "population_key": key,
                    "guidance": info["guidance"],
                    "contraindicated_examples": info.get("contraindicated") or info.get("cautious")
                })
                for med in candidate_medication_names:
                    med_lower = str(med).lower()
                    for pat in info["disallowed_patterns"]:
                        if re.search(pat, med_lower, re.IGNORECASE):
                            if med not in blocked:
                                blocked.append(med)
                            break

        return {
            "has_special_population_alerts": len(alerts) > 0,
            "alerts": alerts,
            "blocked_medications": blocked
        }

    def run_full_safety_audit(
        self,
        conditions: Optional[List[str]] = None,
        current_medications: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        candidate_medications: Optional[List[str]] = None,
        patient_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive 4-pillar clinical safety check.
        """
        conditions = list(conditions or [])
        if patient_profile and isinstance(patient_profile, dict):
            ag = patient_profile.get("age_group") or patient_profile.get("age")
            if ag:
                conditions.append(str(ag))
            if patient_profile.get("pregnancy") or patient_profile.get("is_pregnant"):
                conditions.append("pregnancy")
        current_medications = current_medications or []
        allergies = allergies or []
        candidate_medications = candidate_medications or []

        allergy_res = self.evaluate_allergies(allergies, candidate_medications)
        cond_res = self.evaluate_condition_contraindications(conditions, candidate_medications)
        ddi_res = self.evaluate_drug_drug_interactions(current_medications, candidate_medications)
        spec_res = self.evaluate_special_populations(conditions, candidate_medications)

        all_blocked = list(set(
            allergy_res["blocked_medications"] +
            cond_res["blocked_medications"] +
            spec_res["blocked_medications"]
        ))

        safe_candidates = [m for m in candidate_medications if m not in all_blocked]

        return {
            "is_safe": len(all_blocked) == 0 and not ddi_res["has_interactions"],
            "allergy_evaluation": allergy_res,
            "condition_evaluation": cond_res,
            "drug_interaction_evaluation": ddi_res,
            "special_population_evaluation": spec_res,
            "blocked_medications": all_blocked,
            "safe_medications": safe_candidates
        }


# Global Singleton Instance
clinical_safety_engine = ClinicalSafetyRulesEngine()
