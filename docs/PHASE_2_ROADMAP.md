#  DocMindX AI — Phase 2 Architecture & Feature Roadmap

> **Status:** Architectural Specification & Wireframes (Pending User Confirmation Before Implementation)  
> **Target Release:** Phase 2  
> **Core Principle:** Apple-Level Simplicity + Enterprise Healthcare SaaS + Clinical Safety First

---

## 1. Executive Summary & Master Wireframe

Phase 2 expands DocMindX AI from a 3-panel clinical triage engine into a full-featured personal health operating system.

### Master Navigation Layout
```
┌────────────────────────────────────────────────────────────────────────┐
│  DocMindX AI                     ● System Ready    English [v]    │
├──────────────────────┬─────────────────────────────────────────────────┤
│                      │                                                 │
│  [ ACTIVE MODULES ]  │   Good Afternoon, Alex                          │
│   Home Dashboard   │   How can DocMindX AI assist your health today? │
│   Symptom Triage   │                                                 │
│   Report Analyzer  │  ┌───────────────┐ ┌───────────────┐            │
│   Nearby Care      │  │  Symptoms   │ │  Reports    │            │
│                      │  │ Live Triage   │ │ OCR Analysis  │            │
│  [ PHASE 2 MODULES ] │  └───────────────┘ └───────────────┘            │
│   Medicine Intel   │  ┌───────────────┐ ┌───────────────┐            │
│   Health Progress  │  │  Medicine   │ │  Emergency  │            │
│   Reminders        │  │ Safety/SPL    │ │ 24/7 Overpass │            │
│   Family Profiles  │  └───────────────┘ └───────────────┘            │
│                      │                                                 │
│   Emergency SOS    │    Recent Vitals Trend                        │
│                      │   [BP: 120/80] [Sugar: 98] [SpO2: 99%]          │
└──────────────────────┴─────────────────────────────────────────────────┘
```

---

## 2. Module Specifications & Implementation Plan

###  2.1 Home Dashboard
- **Greeting & Context**: Time-aware greeting (`"Good morning / afternoon / evening"`), quick vital status chips, and primary action grid.
- **4 Primary Hub Cards**:
  1. *AI Health & Symptom Analysis* (Panel 1)
  2. *Diagnostic Report & Prescription Analyzer* (Panel 2)
  3. *Medicine Intelligence & Drug Safety* (Panel 4)
  4. *Nearby Healthcare & Emergency Finder* (Panel 3)
- **Background Aesthetics**: Subtle, non-distracting medical ECG / neural network watermark with clean `#F7F8FA` background.

---

###  2.2 Medicine Intelligence & Identification Panel
- **Dual Input Modes**:
  1. *Text / Voice Search*: Instant autocomplete via DailyMed `/drugnames` and OpenFDA.
  2. *Camera / Image Upload*: Image OCR + vision model text extraction.
- **3-Tier Image Fallback Pipeline**:
  ```
  Uploaded Image / Search Name
             │
             ├────────► 1. Exact Match from DailyMed SPL / OpenFDA
             │
             ├────────► 2. Curated Local Medicine Asset (`assets/images/medicine/`)
             │
             └────────► 3. Clinical Fallback Card:
                           "Image not available from verified data sources.
                            Please verify the medicine packaging before use."
  ```
- **Information Card Structure**:
  - Brand & Generic Names, Active Ingredients, Dosage Form, Manufacturer.
  - Clinical Indications (What it treats).
  - Side Effects, Black Box Warnings, Food & Drug Interactions.
  - Low-confidence safety notice: *"Medicine identification is uncertain. Please verify the medicine name and packaging before use."*

---

###  2.3 Health Progress & Longitudinal Vitals
- **Tracked Parameters**:
  - Blood Pressure (Systolic / Diastolic)
  - Blood Glucose (Fasting / Post-Prandial / HbA1c)
  - Resting Heart Rate & Pulse
  - Blood Oxygen Saturation ($SpO_2$)
  - Body Temperature ($^\circ\text{F} / ^\circ\text{C}$)
- **Timeframe Selector**: 7 Days, 30 Days, 90 Days, 1 Year.
- **Visuals**: Clean interactive charts with normal reference threshold bands (green zone for normal, amber for borderline, red for out-of-range).

---

###  2.4 Medicine Reminders & Adherence Tracking
- **Features**:
  - Medication Name, Dosage, Timing (Morning / Afternoon / Night / Meal relative).
  - Daily checklist with *Taken / Snooze / Skipped* status.
  - Weekly adherence score percentage.
- **Storage**: SQLite `DocMindX.db` table `medicine_reminders`.

---

###  2.5 Multi-User Family Profiles
- **Profile Switching**: Allows switching between profiles (e.g. *Self, Spouse, Father, Mother, Child*).
- **Independent Records**: Each profile maintains their own symptom triage history, lab report archive, active medications, and chronic conditions.

---

###  2.6 Multilingual AI Voice Assistant
- **Supported Languages**: English, हिन्दी (Hindi), ગુજરાતી (Gujarati).
- **Interface**: Floating bottom-right mic button with animated pulse waveform when active.
- **Capabilities**: Voice-assisted symptom entry, automated translation, hands-free navigation.

---

###  2.7 Emergency SOS Protocol
- **Non-Intrusive Trigger**: Red SOS button in sidebar and top header.
- **Explicit Two-Step Confirmation Screen**:
  - *"Are you experiencing an acute medical emergency?"*
  - **Action 1**:  Call 108 / 112 National Ambulance (Device prompt, never auto-dialed silently).
  - **Action 2**:  One-Click Route to Nearest Emergency Hospital (Opens OSM / Google Maps navigation).
  - **Action 3**:  Cancel / Return to Triage.

---

## 3. Local Image Asset Architecture

```
assets/
└── images/
    ├── yoga/
    │   ├── bhujangasana.jpg
    │   ├── cat_cow_pose.jpg
    │   ├── balasana.jpg
    │   ├── setu_bandhasana.jpg
    │   └── anulom_vilom.jpg
    ├── physiotherapy/
    │   ├── chin_tucks.jpg
    │   ├── pelvic_tilt.jpg
    │   ├── shoulder_blade_squeeze.jpg
    │   ├── knee_extension.jpg
    │   └── wall_angels.jpg
    ├── medicine/
    │   ├── paracetamol_tablet.jpg
    │   ├── amoxicillin_capsule.jpg
    │   ├── metformin_500mg.jpg
    │   └── generic_medicine_icon.svg
    └── icons/
        ├── caduceus.svg
        ├── emergency_alert.svg
        └── verified_shield.svg
```

### Exercise Dataset Column Schema:
| Column | Type | Example |
|---|---|---|
| `exercise_id` | String | `Y001` |
| `exercise_name` | String | `Bhujangasana (Cobra Pose)` |
| `image_path` | String | `assets/images/yoga/bhujangasana.jpg` |
| `target_conditions` | String | `D0005, D0012` |
| `steps` | String | `Lie flat on stomach...` |
| `precautions` | String | `Avoid during active pregnancy or acute disc herniation.` |
| `contraindications` | String | `Severe back injury, spinal stenosis` |
| `safety_notice` | String | `Stop immediately if pain or sharp discomfort occurs.` |

---

## 4. Phase 2 Database Schema Additions

```sql
-- Family Profiles Table
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    relation TEXT DEFAULT 'Self',
    age_group TEXT,
    gender TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medicine Reminders Table
CREATE TABLE IF NOT EXISTS medicine_reminders (
    reminder_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    schedule_time TEXT NOT NULL,
    is_taken INTEGER DEFAULT 0,
    FOREIGN KEY(profile_id) REFERENCES user_profiles(profile_id)
);

-- Longitudinal Vitals Log
CREATE TABLE IF NOT EXISTS vitals_log (
    log_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    vital_type TEXT NOT NULL, -- 'bp', 'glucose', 'spo2', 'temp'vital_value TEXT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES user_profiles(profile_id)
);
```

---

## 5. Summary of Phase 1 vs Phase 2 Readiness

| Component | Phase 1 (Completed) | Phase 2 (Roadmapped) |
|---|---|---|
| **Clinical Red Design System** |  Rebuilt & Active |  Standardized |
| **Panel 1: AI Health Triage** |  100% Operational | Maintained |
| **Panel 2: Lab & Prescription OCR** |  100% Operational | Maintained |
| **Panel 3: Nearby Care & Maps** |  100% Operational | Maintained |
| **Home Dashboard Hub** | Omitted (Clean) | <img src="https://cdn-icons-png.flaticon.com/512/4861/4861406.png" width="16" height="16" style="vertical-align: middle;"/> Awaiting Approval |
| **Medicine Intel & Image OCR** | OpenFDA + DailyMed Live | <img src="https://cdn-icons-png.flaticon.com/512/4861/4861406.png" width="16" height="16" style="vertical-align: middle;"/> 3-Tier Image Fallback |
| **Vitals & Progress Charts** | N/A | <img src="https://cdn-icons-png.flaticon.com/512/4861/4861406.png" width="16" height="16" style="vertical-align: middle;"/> Chart Layer |
| **Medicine Reminders & SOS** | N/A | <img src="https://cdn-icons-png.flaticon.com/512/4861/4861406.png" width="16" height="16" style="vertical-align: middle;"/> Safety Dialog & Reminders |
