"""
DocMindX AI — Family Medical Profiles & Clinical Context Component
Enables management of family members, extensible structured medical conditions,
medication logs, profile management, and dynamic scan context selection.
"""
import streamlit as st

import database.auth_db as auth_db
import services.auth_service as auth_svc
from config.language import get_text

RELATIONSHIP_OPTIONS = [
    "Self", "Mother", "Father", "Spouse", "Son", "Daughter",
    "Brother", "Sister", "Grandfather", "Grandmother", "Uncle", "Aunt", "Other"
]

BLOOD_GROUP_OPTIONS = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]

COMMON_CONDITIONS = [
    "Diabetes / Sugar",
    "Hypertension / Blood Pressure",
    "Cholesterol / Dyslipidemia",
    "Heart Disease / CAD",
    "Asthma / Respiratory Illness",
    "Thyroid Disorder",
    "Kidney Disease",
    "Arthritis / Joint Pain",
    "Allergies",
    "Other Chronic Condition"
]

def format_member_date(dt_val) -> str:
    """Safely format database timestamp/date into clean 'DD Mon YYYY' format."""
    if not dt_val:
        import datetime
        return datetime.date.today().strftime("%d %b %Y")
    try:
        if isinstance(dt_val, str):
            clean_str = dt_val.replace("T", " ").split(".")[0].strip()
            if "-" in clean_str:
                parts = clean_str.split(" ")[0].split("-")
                if len(parts) == 3:
                    import datetime
                    d = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    return d.strftime("%d %b %Y")
        return str(dt_val)[:10]
    except Exception:
        return str(dt_val)[:10]

INDIAN_STATES = [
    "Select State",
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi (NCT)",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand",
    "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Other / International"
]

def render_safe_html(html_str: str):
    """Safely renders HTML in Streamlit by stripping all line indents, preventing markdown code-block conversion."""
    compact = " ".join([l.strip() for l in html_str.strip().splitlines() if l.strip()])
    st.markdown(compact, unsafe_allow_html=True)

@st.dialog("Profile Actions", width="small")
def render_profile_actions_dialog(m_id: int, m_name: str, user_id: int):
    """
    Renders the Profile Actions modal dialog.
    Clean, compact tabbed layout: Edit Profile, Conditions, Medicines, Delete.
    Eliminates stacked double cards and provides a sleek, space-efficient popup.
    """
    member = auth_db.get_family_member_by_id(m_id, user_id)
    if not member:
        st.error("Profile not found.")
        return

    # ── Profile Actions Dialog: Centered, compact, no ghost card ──
    st.markdown("""
    <style>
    /* ── 1. Backdrop: full-screen dark overlay, flex-centered ── */
    div[data-testid="stDialog"],
    div[data-modal-container="true"] {
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        max-width: none !important;
        background: rgba(15, 23, 42, 0.70) !important;
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 9999 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }

    /* ── 2. Kill ghost card: Streamlit's border wrappers INSIDE dialog ── */
    div[data-testid="stDialog"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stDialog"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stDialog"] > [data-testid],
    div[data-modal-container="true"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-modal-container="true"] > div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        max-width: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 0 !important;
    }

    /* ── 3. Actual dialog box: scoped only to div[role="dialog"] ── */
    div[data-testid="stDialog"] div[role="dialog"],
    div[data-modal-container="true"] div[role="dialog"] {
        position: relative !important;
        width: min(480px, 92vw) !important;
        max-width: min(480px, 92vw) !important;
        min-width: unset !important;
        margin: auto !important;
        left: unset !important;
        right: unset !important;
        top: unset !important;
        transform: none !important;
        border-radius: 18px !important;
        padding: 1.25rem 1.4rem !important;
        background: var(--mm-card-bg, #FFFFFF) !important;
        border: 1.5px solid var(--mm-border-color, #E2E8F0) !important;
        box-shadow: 0 24px 56px -8px rgba(15, 23, 42, 0.34),
                    0 8px 20px -4px rgba(15, 23, 42, 0.16) !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* ── 4. Inner vertical block spacing ── */
    div[data-testid="stDialog"] [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }

    /* ── 5. Dialog title header ── */
    div[data-testid="stDialog"] header,
    div[data-testid="stDialog"] [data-testid="stDialogHeader"] {
        padding: 0 0 8px 0 !important;
        margin-bottom: 4px !important;
        border-bottom: 1px solid var(--mm-border-color, #E2E8F0) !important;
    }

    /* ── 6. Profile card header row ── */
    .profile-action-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--mm-border-color, #E2E8F0);
    }
    .profile-action-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #EFF6FF;
        border: 1.5px solid #DBEAFE;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    /* ── 7. Dark mode ── */
    [data-theme="dark"] div[data-testid="stDialog"],
    [data-theme="dark"] div[data-modal-container="true"] {
        background: rgba(2, 8, 23, 0.80) !important;
    }
    [data-theme="dark"] div[data-testid="stDialog"] div[role="dialog"],
    [data-theme="dark"] div[data-modal-container="true"] div[role="dialog"] {
        background: #1E293B !important;
        border-color: #334155 !important;
        box-shadow: 0 24px 56px -8px rgba(0, 0, 0, 0.55),
                    0 8px 20px -4px rgba(0, 0, 0, 0.35) !important;
    }
    [data-theme="dark"] .profile-action-avatar {
        background: rgba(37, 99, 235, 0.12) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }
    [data-theme="dark"] .profile-action-header {
        border-bottom-color: #334155 !important;
    }

    /* ── 8. Mobile ── */
    @media (max-width: 600px) {
        div[data-testid="stDialog"] div[role="dialog"],
        div[data-modal-container="true"] div[role="dialog"] {
            width: 96vw !important;
            max-width: 96vw !important;
            padding: 1rem 0.9rem !important;
            border-radius: 14px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Header: Compact Avatar + Member Name + Subtitle
    m_rel = member.get("relationship", "Member")
    render_safe_html(f"""
    <div class="profile-action-header">
        <div class="profile-action-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        </div>
        <div style="min-width: 0; flex: 1;">
            <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1.2;">
                {m_name} <span style="font-size: 0.74rem; font-weight: 600; color: #2563EB; background: #EFF6FF; border: 1px solid #DBEAFE; padding: 1px 8px; border-radius: 12px; vertical-align: middle;">{m_rel}</span>
            </div>
            <div style="font-size: 0.75rem; color: var(--mm-text-secondary, #64748B); margin-top: 1px;">Manage details, conditions & medications</div>
        </div>
    </div>
    """)

    # Compact Tabbed Navigation (Zero double cards, compact dialog height)
    tab_edit, tab_cond, tab_med, tab_del = st.tabs(["Edit Profile", "Conditions", "Medicines", "Delete"])

    # TAB 1: EDIT PROFILE & STATE
    with tab_edit:
        e_name = st.text_input("Full Name *", value=member.get("name", ""), key=f"dlg_e_name_{m_id}")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            import datetime
            m_today = datetime.date.today()
            m_max_dob = datetime.date(m_today.year - 10, m_today.month, min(m_today.day, 28))
            m_min_dob = datetime.date(m_today.year - 120, 1, 1)
            
            existing_dob_str = str(member.get("dob", "") or "").strip()
            init_dob = None
            if existing_dob_str:
                try:
                    p = [int(x) for x in existing_dob_str.split("-")]
                    if len(p) == 3:
                        init_dob = datetime.date(p[0], p[1], p[2])
                except Exception:
                    init_dob = None
            if not init_dob:
                curr_age = int(member.get("age") or 45)
                init_dob = datetime.date(m_today.year - curr_age, m_today.month, min(m_today.day, 28))
            
            init_dob = min(max(init_dob, m_min_dob), m_max_dob)
            st.markdown("""<div style="font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 3px;">Date of Birth (DOB) *</div>""", unsafe_allow_html=True)
            e_dob = st.date_input("Date of Birth (DOB) *", value=init_dob, min_value=m_min_dob, max_value=m_max_dob, key=f"dlg_e_dob_{m_id}", label_visibility="collapsed")
            calc_e_age = auth_db.calculate_age_from_dob(e_dob)
            st.markdown(
                f"<div style='display:inline-flex; align-items:center; gap:5px; "
                f"font-size:0.72rem; font-weight:700; color:#2563EB; "
                f"background:rgba(37,99,235,0.08); border:1px solid rgba(37,99,235,0.18); "
                f"border-radius:6px; padding:2px 8px; margin-top:5px; margin-bottom:2px;'>"
                f"&#128197; Age: {calc_e_age} yrs&nbsp;<span style='font-weight:500;color:#64748B;'>(Live)</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with e_col2:
            curr_gen = member.get("gender") or "Female"
            gen_idx = ["Female", "Male", "Other"].index(curr_gen) if curr_gen in ["Female", "Male", "Other"] else 0
            st.markdown("""<div style="font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 3px;">Gender *</div>""", unsafe_allow_html=True)
            e_gen = st.selectbox("Gender *", ["Female", "Male", "Other"], index=gen_idx, key=f"dlg_e_gen_{m_id}", label_visibility="collapsed")

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        e_col3, e_col4 = st.columns(2)
        with e_col3:
            curr_bg = member.get("blood_group") or ""
            bg_idx = BLOOD_GROUP_OPTIONS.index(curr_bg) if curr_bg in BLOOD_GROUP_OPTIONS else 0
            st.markdown("""<div style="font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 3px;">Blood Group</div>""", unsafe_allow_html=True)
            e_bg = st.selectbox("Blood Group", BLOOD_GROUP_OPTIONS, index=bg_idx, key=f"dlg_e_bg_{m_id}", label_visibility="collapsed")
        with e_col4:
            curr_state = member.get("state") or "Select State"
            state_idx = INDIAN_STATES.index(curr_state) if curr_state in INDIAN_STATES else 0
            st.markdown("""<div style="font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 3px;">State / Region</div>""", unsafe_allow_html=True)
            e_state = st.selectbox("State / Region", INDIAN_STATES, index=state_idx, key=f"dlg_e_state_{m_id}", label_visibility="collapsed")

        e_col5, e_col6 = st.columns(2)
        with e_col5:
            e_ht = st.text_input("Height (cm)", value=str(member.get("height") or ""), key=f"dlg_e_ht_{m_id}")
        with e_col6:
            e_wt = st.text_input("Weight (kg)", value=str(member.get("weight") or ""), key=f"dlg_e_wt_{m_id}")

        st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
        if st.button("Update Profile Details", key=f"dlg_btn_update_{m_id}", type="primary", use_container_width=True):
            if not e_name or not e_name.strip():
                st.error("Please enter a valid name.")
            elif calc_e_age is None or calc_e_age < 10:
                st.warning("DocMindX AI Clinical Protocol: Family member age must be at least 10 years for standard clinical profile assessment. Pediatric profiles (< 10 years) require specialized pediatric consultation.")
            else:
                updated_dict = {
                    "name": e_name.strip(),
                    "relationship": member.get("relationship", ""),
                    "age": calc_e_age,
                    "dob": e_dob.strftime("%Y-%m-%d"),
                    "gender": e_gen,
                    "blood_group": e_bg,
                    "height": e_ht.strip(),
                    "weight": e_wt.strip(),
                    "state": e_state if e_state != "Select State" else "",
                    "notes": member.get("notes", ""),
                    "emergency_contact": member.get("emergency_contact", "")
                }
                auth_db.update_family_member(m_id, user_id, updated_dict)
                st.toast("Profile details updated successfully!")
                st.rerun()

    # TAB 2: MEDICAL CONDITIONS
    with tab_cond:
        conds = member.get("conditions", [])
        if conds:
            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #475569; margin-bottom: 6px;'>Active Conditions:</div>", unsafe_allow_html=True)
            for c in conds:
                c_c1, c_c2 = st.columns([0.82, 0.18], vertical_alignment="center")
                with c_c1:
                    render_safe_html(f"""
                    <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 5px 10px; font-size: 0.80rem; font-weight: 600; color: #D97706; margin-bottom: 4px;">
                        {c['condition_name']}
                    </div>
                    """)
                with c_c2:
                    if st.button("✕", key=f"del_c_{c['id']}", help="Remove condition", type="secondary"):
                        auth_db.delete_medical_condition(c["id"], user_id)
                        st.toast("Condition removed.")
                        st.rerun()
            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

        new_c = st.text_input("Add Condition Name", placeholder="e.g. Diabetes, Hypertension, Asthma...", key=f"dlg_cond_input_{m_id}")
        if st.button("＋ Save Condition", key=f"dlg_btn_cond_{m_id}", type="primary", use_container_width=True):
            if new_c and new_c.strip():
                auth_db.add_medical_condition(m_id, user_id, new_c.strip())
                st.toast("Medical condition added successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid condition name.")

    # TAB 3: MEDICINES
    with tab_med:
        meds = member.get("medications", [])
        if meds:
            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #475569; margin-bottom: 6px;'>Current Medications:</div>", unsafe_allow_html=True)
            for m_item in meds:
                m_c1, m_c2 = st.columns([0.82, 0.18], vertical_alignment="center")
                with m_c1:
                    dos_text = f" ({m_item['dosage']})" if m_item.get("dosage") else ""
                    render_safe_html(f"""
                    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 5px 10px; font-size: 0.80rem; font-weight: 600; color: #059669; margin-bottom: 4px;">
                        {m_item['medicine_name']}{dos_text}
                    </div>
                    """)
                with m_c2:
                    if st.button("✕", key=f"del_m_{m_item['id']}", help="Remove medicine", type="secondary"):
                        auth_db.delete_medication(m_item["id"], user_id)
                        st.toast("Medication removed.")
                        st.rerun()
            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

        new_m = st.text_input("Medicine Name *", placeholder="e.g. Metformin, Amlodipine...", key=f"dlg_med_input_{m_id}")
        new_m_dos = st.text_input("Dosage", placeholder="e.g. 500mg, 1 tablet, 5ml...", key=f"dlg_dos_input_{m_id}")
        if st.button("＋ Save Medicine", key=f"dlg_btn_med_{m_id}", type="primary", use_container_width=True):
            if new_m and new_m.strip():
                auth_db.add_medication(m_id, user_id, new_m.strip(), dosage=new_m_dos.strip() if new_m_dos else "")
                st.toast("Medication added successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid medicine name.")

    # TAB 4: DELETE PROFILE
    with tab_del:
        render_safe_html("""
        <div style="background: rgba(239, 68, 68, 0.06); border: 1.2px solid #FECACA; border-radius: 10px; padding: 12px 14px; margin-bottom: 12px;">
            <div style="font-size: 0.88rem; font-weight: 800; color: #DC2626; margin-bottom: 4px;">Delete Family Profile</div>
            <div style="font-size: 0.76rem; color: #64748B; line-height: 1.4;">Permanently delete this profile and all associated medical data? This action cannot be undone.</div>
        </div>
        """)
        if st.button("🗑 Delete Profile Permanently", key=f"dlg_btn_del_{m_id}", type="secondary", use_container_width=True):
            auth_db.delete_family_member(m_id, user_id)
            auth_db.log_security_event("FAMILY_MEMBER_DELETED", user_id=user_id, details=f"Deleted member ID {m_id}")
            st.toast("Profile permanently removed.")
            st.rerun()

    # Subtle Compact Footer
    render_safe_html("""
    <div style="border-top: 1px solid var(--mm-border, #E2E8F0); padding-top: 8px; margin-top: 12px; display: flex; align-items: center; justify-content: space-between; font-size: 0.68rem; color: #64748B;">
        <span>🔒 Encrypted • Private • Secure</span>
        <span>DocMindX <strong>AI</strong></span>
    </div>
    """)

def render_family_management_view(user: dict):
    """Renders the comprehensive My Profile and Family Profiles Management Panel."""
    if not user:
        st.warning("Please sign in to view your family medical profiles.")
        return

    user_id = user.get("id") or user.get("user_id")
    db_user = auth_db.get_user_by_id(user_id) or user

    user_display_name = db_user.get("full_name") or "Patient Profile"
    user_initial = user_display_name.strip()[0].upper() if user_display_name.strip() else "P"
    user_email = db_user.get("email", "")

    # 1. Top Branding Header Bar (DocMindX AI + Trust Badge)

    # If administrator is viewing, provide quick switch back to Admin Console
    if auth_svc.is_admin_session(user):
        adm_bar_c1, adm_bar_c2 = st.columns([3, 1])
        with adm_bar_c1:
            st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 8px 14px; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #EF4444;"></span>
                <span style="font-size: 0.78rem; font-weight: 700; color: #DC2626;">Administrator Mode Active</span>
                <span style="font-size: 0.74rem; color: #64748B;">— You are viewing patient family profiles with administrative privileges.</span>
            </div>
            """, unsafe_allow_html=True)
        with adm_bar_c2:
            if st.button("← Admin Console", key="fam_btn_go_admin", use_container_width=True):
                st.session_state["active_panel"] = "Admin Panel"
                st.rerun()

    # 2. Patient Hero Card (Image 2 Design with Avatar Initial, Real Data, ECG line, and Verified Badge)
    if st.session_state.get("family_settings_open", False):
        with st.expander("Account Settings", expanded=True):
            st.markdown("<div style='font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-bottom: 8px;'>Use the Account Profile and Change Password sections to update your identity and security details.</div>", unsafe_allow_html=True)
            settings_cols = st.columns(2)
            with settings_cols[0]:
                if st.button("Open Account Profile", key="family_settings_profile_btn", use_container_width=True):
                    st.session_state["family_settings_open"] = False
                    st.rerun()
            with settings_cols[1]:
                if st.button("Open Change Password", key="family_settings_password_btn", use_container_width=True):
                    st.session_state["family_settings_open"] = False
                    st.rerun()

    st.markdown(f"""
    <div class="patient-hero-card" style="position: relative; overflow: hidden; background: linear-gradient(135deg, rgba(239, 246, 255, 0.85) 0%, rgba(255, 255, 255, 0.95) 60%, rgba(240, 249, 255, 0.9) 100%); border: 1.5px solid #DBEAFE; border-radius: 18px; padding: 22px 26px; margin-bottom: 22px; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.06);">
        <!-- Subtle ECG Waveform Background -->
        <div style="position: absolute; right: 260px; top: 50%; transform: translateY(-50%); opacity: 0.25; pointer-events: none; z-index: 1;">
            <svg width="220" height="60" viewBox="0 0 220 60" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M0 30h40l8-18 12 36 10-22 8 8h30l6-14 8 28 8-18 6 4h74"/>
            </svg>
        </div>
        <div style="position: relative; z-index: 2; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
            <div style="display: flex; align-items: center; gap: 18px;">
                <!-- Avatar Circle with Initial -->
                <div style="width: 62px; height: 62px; border-radius: 50%; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); display: flex; align-items: center; justify-content: center; font-size: 1.65rem; font-weight: 800; color: #FFFFFF; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35); flex-shrink: 0; border: 3px solid #EFF6FF;">
                    {user_initial}
                </div>
                <div>
                    <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; letter-spacing: -0.2px;">{user_display_name}</h2>
                    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 4px; font-size: 0.84rem; color: #64748B;">
                        <span>{user_email}</span>
                        <span style="color: #CBD5E1;">|</span>
                        <span style="display: inline-flex; align-items: center; gap: 5px; color: #16A34A; font-weight: 700;">
                            <span style="width: 8px; height: 8px; border-radius: 50%; background: #16A34A; display: inline-block;"></span>
                            Active Patient Account
                        </span>
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 18px; flex-wrap: wrap;">
                <div style="font-family: cursive, 'Segoe Script', 'Brush Script MT', sans-serif; font-size: 0.96rem; color: #3B82F6; font-weight: 600; text-align: right; transform: rotate(-2deg); line-height: 1.25;">
                    Better Health<br/><span style="font-size: 0.90rem; color: #2563EB;">Brighter Tomorrow</span>
                </div>
                <div style="background: rgba(240, 253, 244, 0.9); border: 1.5px solid #BBF7D0; border-radius: 24px; padding: 6px 14px; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(22, 163, 74, 0.08);">
                    <div style="width: 16px; height: 16px; border-radius: 50%; background: #16A34A; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    </div>
                    <span style="color: #15803D; font-size: 0.78rem; font-weight: 800;">Email Verified</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_family, tab_add, tab_profile, tab_security = st.tabs([
        "My Family Members",
        "Add Family Member",
        "Account Profile",
        "Change Password"
    ])

    # -------------------------------------------------------------
    # TAB 1: MY FAMILY MEMBERS
    # -------------------------------------------------------------
    with tab_family:
        family_members = auth_db.get_family_members(user_id)
        
        # Section Header: Icon + Title + Count + Add Button
        col_fh1, col_fh2 = st.columns([3, 1.2])
        with col_fh1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(37, 99, 235, 0.1); border: 1.2px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                </div>
                <div>
                    <h3 style="margin: 0; font-size: 1.22rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">My Family Members</h3>
                    <div style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 1px;">You have <strong>{len(family_members)}</strong> saved family medical profile(s).</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_fh2:
            st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
            if st.button("+ Add New Family Member", key="btn_add_family_hero", use_container_width=True):
                st.session_state["active_family_tab"] = "add"
                st.rerun()

        if not family_members:
            st.markdown("""
            <div class="dmx-empty-family-banner" style="background: rgba(37, 99, 235, 0.08); border: 1.5px dashed rgba(59, 130, 246, 0.35); border-radius: 12px; padding: 18px 20px; display: flex; align-items: center; gap: 14px; margin-top: 10px; margin-bottom: 16px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                </div>
                <div style="font-size: 0.88rem; color: var(--mm-text-primary, #1E293B); font-weight: 600; line-height: 1.4;">
                    No family members added yet. Click <strong>'+ Add New Family Member'</strong> above to create a profile for your parents, children, or spouse.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for m in family_members:
                m_id = m["id"]
                m_name = m.get("name") or "Family Member"
                m_rel = m.get("relationship") or "Relative"
                m_initial = m_name.strip()[0].upper() if m_name.strip() else "M"

                # Dynamic gender / relationship styling
                rel_lower = m_rel.lower()
                gen_lower = (m.get("gender") or "").lower()
                is_female = gen_lower == "female" or rel_lower in [
                    "mother",
                    "daughter",
                    "sister",
                    "grandmother",
                    "aunt",
                    "wife",
                ]

                avatar_bg = "#FEE2E2" if is_female else "#DCFCE7"
                avatar_color = "#DC2626" if is_female else "#16A34A"
                gender_glyph = "♀" if is_female else "♂"
                date_str = format_member_date(m.get("created_at"))

                # Blood group badge
                blood_badge = ""
                if m.get("blood_group"):
                    blood_badge = f"""<span style="background: #FEF2F2; color: #DC2626; border: 1px solid #FEE2E2; padding: 2px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="#DC2626"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg> Blood: {m.get('blood_group')}</span>"""

                # Dynamic details list (Age, DOB, Gender, Height, Weight, Date)
                details = []
                if m.get("age") is not None:
                    details.append(f"Age: <strong>{m.get('age')} yrs</strong>")
                if m.get("dob"):
                    details.append(f"DOB: <strong>{format_member_date(m.get('dob'))}</strong>")
                if m.get("gender"):
                    details.append(f"Gender: <strong>{m.get('gender')}</strong>")
                if m.get("height"):
                    details.append(f"Height: <strong>{m.get('height')} cm</strong>")
                if m.get("weight"):
                    details.append(f"Weight: <strong>{m.get('weight')} kg</strong>")

                details.append(f'<span style="display: inline-flex; align-items: center; gap: 4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> Added on: {date_str}</span>')

                details_html = " <span style='color: #CBD5E1;'>|</span> ".join(details)

                m_state = m.get("state")
                state_badge = f"""<span style="background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; padding: 2px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> {m_state}</span>""" if m_state else ""
                if m_state:
                    details.append(f"State: <strong>{m_state}</strong>")

                # Member Card: Enclose BOTH info and Manage button INSIDE the card border container!
                with st.container(border=True):
                    col_info, col_btn = st.columns([0.83, 0.17], gap="small", vertical_alignment="center")
                    with col_info:
                        card_html = (
                            f'<div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">'
                            f'<div style="width: 48px; height: 48px; border-radius: 50%; background: {avatar_bg}; color: {avatar_color}; display: flex; align-items: center; justify-content: center; font-size: 1.35rem; font-weight: 800; flex-shrink: 0;">{m_initial}</div>'
                            f'<div style="min-width: 0; flex: 1;">'
                            f'<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 4px;">'
                            f'<span style="font-size: 1.08rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">{m_name}</span>'
                            f'<span style="background: #EFF6FF; color: #2563EB; border: 1px solid #DBEAFE; padding: 2px 10px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><span>{gender_glyph}</span>{m_rel}</span>'
                            f'{blood_badge}'
                            f'{state_badge}'
                            f'</div>'
                            f'<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.80rem; color: var(--mm-text-secondary, #64748B);">{details_html}</div>'
                            f'</div>'
                            f'</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

                        # Conditions & medications badges (inside card container)
                        conds = m.get("conditions", [])
                        meds  = m.get("medications", [])
                        if conds or meds or m.get("notes"):
                            if conds:
                                cond_badges = " ".join([
                                    f"<span style='background: rgba(245,158,11,0.12); color: #D97706; border: 1px solid rgba(245,158,11,0.3); padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; margin-right: 4px; display: inline-block; margin-bottom: 4px;'>{c['condition_name']}</span>"
                                    for c in conds
                                ])
                                st.markdown(f"<div style='font-size:0.76rem; margin: 6px 0 2px 0;'><strong style='color:#475569;'>Conditions:</strong> {cond_badges}</div>", unsafe_allow_html=True)
                            if meds:
                                med_badges = " ".join([
                                    f"<span style='background: rgba(16,185,129,0.12); color: #059669; border: 1px solid rgba(16,185,129,0.3); padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; margin-right: 4px; display: inline-block; margin-bottom: 4px;'>{med['medicine_name']}{(' ('+med['dosage']+')') if med.get('dosage') else ''}</span>"
                                    for med in meds
                                ])
                                st.markdown(f"<div style='font-size:0.76rem; margin: 2px 0;'><strong style='color:#475569;'>Medications:</strong> {med_badges}</div>", unsafe_allow_html=True)
                            if m.get("notes"):
                                st.markdown(f"<div style='font-size: 0.76rem; color: #64748B; font-style: italic; margin-top: 2px;'>Notes: {m.get('notes')}</div>", unsafe_allow_html=True)

                    with col_btn:
                        if st.button("⚙ Manage", key=f"btn_manage_card_{m_id}", use_container_width=True):
                            render_profile_actions_dialog(m_id, m_name, user_id)

                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        # Bottom Info Banner (Image 2 Design)
        st.markdown("""
        <div style="background: rgba(239, 246, 255, 0.85); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 16px 20px; margin-top: 22px; margin-bottom: 22px; display: flex; align-items: center; gap: 16px;">
            <div style="width: 38px; height: 38px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
            </div>
            <div>
                <div style="font-size: 0.95rem; font-weight: 800; color: #1D4ED8;">Manage Family Profiles</div>
                <div style="font-size: 0.80rem; color: #475569; margin-top: 2px;">You can view, edit, or delete family medical profiles. Keep your family health information updated for better care.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Footer Trust Row (Image 2 Design)

    # -------------------------------------------------------------
    # TAB 2: ADD FAMILY MEMBER (IMAGE 2 DESIGN: 4 SUB-CARDS, FULL FORM)
    # -------------------------------------------------------------
    with tab_add:
        st.markdown("""
        <div class="account-settings-card" style="background: var(--mm-card-bg, #FFFFFF); border: 1.5px solid #E2E8F0; border-radius: 18px; padding: 24px 28px; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 18px; margin-bottom: 22px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); border: 1.5px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                            <circle cx="9" cy="7" r="4"></circle>
                            <line x1="19" y1="8" x2="19" y2="14"></line>
                            <line x1="22" y1="11" x2="16" y2="11"></line>
                        </svg>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.32rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); letter-spacing: -0.2px;">Add New <span style="color: #2563EB;">Family Profile</span></h3>
                        <div style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 2px;">Saved medical profiles are automatically loaded during scans and health evaluations.</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 32px; height: 32px; border-radius: 8px; background: #2563EB; display: flex; align-items: center; justify-content: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                                <path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h4.78"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 0.95rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1;">DocMindX <span style="color: #2563EB;">AI</span></div>
                            <div style="font-size: 0.62rem; color: var(--mm-text-secondary, #64748B); font-weight: 700; letter-spacing: 0.3px;">CLINICAL AI HEALTHCARE SYSTEM</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: #15803D; font-weight: 600; border-left: 1px solid #E2E8F0; padding-left: 14px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>
                        Better Health<br/>Brighter Tomorrow
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form(key="add_family_member_form"):
            # Section 1: Personal Information Sub-Card
            st.markdown("""
            <div class="form-subcard">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Personal Information</div>
                        <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">Basic details about your family member.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_f1, c_f2 = st.columns(2, gap="medium")
            with c_f1:
                # Full Name *
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    <span>Full Name <strong style="color: #DC2626;">*</strong></span>
                </div>""", unsafe_allow_html=True)
                fam_name = st.text_input("Full Name *", placeholder="e.g. Member Name*", label_visibility="collapsed")

                # Relationship *
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                    <span>Relationship <strong style="color: #DC2626;">*</strong></span>
                </div>""", unsafe_allow_html=True)
                fam_rel = st.selectbox("Relationship *", RELATIONSHIP_OPTIONS, index=1, label_visibility="collapsed")

                # Date of Birth (DOB) *
                st.markdown("""<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 10px; margin-bottom: 5px;">
                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B);">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        <span>Date of Birth (DOB) <strong style="color: #DC2626;">*</strong></span>
                    </div>
                    <span style="font-size: 0.70rem; color: #64748B;">Min 10 Years</span>
                </div>""", unsafe_allow_html=True)
                import datetime
                fam_today = datetime.date.today()
                fam_max_dob = datetime.date(fam_today.year - 10, fam_today.month, min(fam_today.day, 28))
                fam_min_dob = datetime.date(fam_today.year - 120, 1, 1)
                fam_default_dob = datetime.date(fam_today.year - 45, fam_today.month, min(fam_today.day, 28))
                fam_dob = st.date_input("Date of Birth (DOB) *", value=fam_default_dob, min_value=fam_min_dob, max_value=fam_max_dob, label_visibility="collapsed")
                fam_calc_age = auth_db.calculate_age_from_dob(fam_dob)
                st.markdown(f"""<div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 2px; margin-bottom: 6px;">
                    <span style="font-size: 0.74rem; font-weight: 700; color: #2563EB; background: #EFF6FF; border: 1px solid #DBEAFE; padding: 2px 8px; border-radius: 12px;">
                        Age: {fam_calc_age if fam_calc_age is not None else '--'} yrs (Auto-increments)
                    </span>
                </div>""", unsafe_allow_html=True)

                # Gender *
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"></path></svg>
                    <span>Gender <strong style="color: #DC2626;">*</strong></span>
                </div>""", unsafe_allow_html=True)
                fam_gender = st.selectbox("Gender *", ["Female", "Male", "Other"], index=0, label_visibility="collapsed")

                # Blood Group
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="#DC2626"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                    <span>Blood Group</span>
                </div>""", unsafe_allow_html=True)
                fam_bg = st.selectbox("Blood Group", BLOOD_GROUP_OPTIONS, index=3, label_visibility="collapsed")

            with c_f2:
                # State / Region
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    <span>State / Region</span>
                </div>""", unsafe_allow_html=True)
                fam_state = st.selectbox("State / Region", INDIAN_STATES, index=0, label_visibility="collapsed")

                # Height (cm)
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path></svg>
                    <span>Height (cm)</span>
                </div>""", unsafe_allow_html=True)
                fam_height = st.text_input("Height (cm)", placeholder="165", label_visibility="collapsed")

                # Weight (kg)
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
                    <span>Weight (kg)</span>
                </div>""", unsafe_allow_html=True)
                fam_weight = st.text_input("Weight (kg)", placeholder="68", label_visibility="collapsed")

                # Emergency Contact
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 10px; margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                    <span>Emergency Contact</span>
                </div>""", unsafe_allow_html=True)
                fam_emg = st.text_input("Emergency Contact", placeholder="+91 98765 43210", label_visibility="collapsed")

            st.markdown("</div>", unsafe_allow_html=True)

            # Section 2: Existing Diseases / Medical Conditions Sub-Card
            st.markdown("""
            <div class="form-subcard">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                            <path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h4.78"/>
                        </svg>
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Existing Diseases / Medical Conditions</div>
                        <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">Select known conditions and add any other relevant medical condition.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_c1, c_c2 = st.columns(2, gap="medium")
            with c_c1:
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path><circle cx="20" cy="10" r="2"></circle></svg>
                    <span>Select known conditions</span>
                </div>""", unsafe_allow_html=True)
                selected_conds = st.multiselect("Select known conditions", COMMON_CONDITIONS, placeholder="Choose options", label_visibility="collapsed")
            with c_c2:
                st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                    <span>Other Custom Medical Condition (optional)</span>
                </div>""", unsafe_allow_html=True)
                custom_cond = st.text_input("Other Custom Medical Condition (optional)", placeholder="e.g. Migraine, Glaucoma", label_visibility="collapsed")

            st.markdown("</div>", unsafe_allow_html=True)

            # Section 3: Current Medications Sub-Card
            st.markdown("""
            <div class="form-subcard">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path><path d="m8.5 8.5 7 7"></path></svg>
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Current Medications</div>
                        <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">List all current medications (one per line or comma separated).</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                <span>Medications &amp; Dosages</span>
            </div>""", unsafe_allow_html=True)
            fam_meds = st.text_area("Medications & Dosages", placeholder="e.g. Metformin 500mg (twice daily)\nAtorvastatin 10mg (night)", label_visibility="collapsed")

            st.markdown("</div>", unsafe_allow_html=True)

            # Section 4: Allergies / Special Medical Notes Sub-Card
            st.markdown("""
            <div class="form-subcard">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                    <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect width="8" height="4" x="8" y="2" rx="1" ry="1"></rect></svg>
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Allergies / Special Medical Notes</div>
                        <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">Mention any allergies, intolerances or other important notes.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                <span>Allergies / Special Medical Notes</span>
            </div>""", unsafe_allow_html=True)
            fam_notes = st.text_area("Allergies / Special Medical Notes", placeholder="e.g. Penicillin allergy, mild lactose intolerance", label_visibility="collapsed")

            st.markdown("</div>", unsafe_allow_html=True)

            # Submit Button (Image 2 Design: Full width blue button with save icon)
            btn_save_member = st.form_submit_button("Save Family Member Profile", type="primary", use_container_width=True)

            if btn_save_member:
                if not fam_name or not fam_name.strip():
                    st.error("Please enter the family member's name.")
                elif fam_calc_age is None or fam_calc_age < 10:
                    st.warning("⚠️ DocMindX AI Clinical Protocol: Family member age must be at least 10 years for independent clinical assessment. Pediatric profiles (< 10 years) require direct in-person consultation with a certified pediatrician.")
                else:
                    cond_list = list(selected_conds)
                    if custom_cond.strip():
                        cond_list.append(custom_cond.strip())

                    med_list = [m.strip() for m in fam_meds.replace("\n", ",").split(",") if m.strip()]

                    fam_dob_str = fam_dob.strftime("%Y-%m-%d") if fam_dob else ""
                    member_data = {
                        "name": fam_name.strip(),
                        "relationship": fam_rel,
                        "age": fam_calc_age,
                        "dob": fam_dob_str,
                        "gender": fam_gender,
                        "blood_group": fam_bg,
                        "height": fam_height,
                        "weight": fam_weight,
                        "state": fam_state if fam_state != "Select State" else "",
                        "notes": fam_notes,
                        "emergency_contact": fam_emg,
                        "conditions": cond_list,
                        "medications": med_list
                    }
                    new_id = auth_db.add_family_member(user_id, member_data)
                    auth_db.log_security_event("FAMILY_MEMBER_ADDED", user_id=user_id, details=f"Added member: {fam_name} ({fam_rel})")
                    st.success(f"Successfully added {fam_name} to your family profile!")
                    st.rerun()

        # Bottom Trust Bar
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; gap: 32px; flex-wrap: wrap; padding-top: 18px; border-top: 1.5px solid #F1F5F9; margin-top: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.74rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                <div><strong>Secure &amp; Encrypted</strong><br/><span style="color: #94A3B8; font-size: 0.68rem;">Your data is protected</span></div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.74rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                <div><strong>HIPAA &amp; WHO Compliant</strong><br/><span style="color: #94A3B8; font-size: 0.68rem;">Global healthcare standards</span></div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.74rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                <div><strong>Trusted Healthcare</strong><br/><span style="color: #94A3B8; font-size: 0.68rem;">Built for a healthier tomorrow</span></div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: ACCOUNT PROFILE (IMAGE 4 DESIGN: 2 COLUMNS, ICONS, LOGOUT)
    # -------------------------------------------------------------
    with tab_profile:
        # Card Header: Gear SVG + Title + Subtitle + DocMindX AI Branding
        st.markdown("""
        <div class="account-settings-card" style="background: var(--mm-card-bg, #FFFFFF); border: 1.5px solid #E2E8F0; border-radius: 18px; padding: 24px 28px; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 18px; margin-bottom: 22px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); border: 1.5px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.32rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); letter-spacing: -0.2px;">Account Settings</h3>
                        <div style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 2px;">View and manage your account information and security settings.</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 32px; height: 32px; border-radius: 8px; background: #2563EB; display: flex; align-items: center; justify-content: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                                <path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h4.78"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 0.95rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1;">DocMindX <span style="color: #2563EB;">AI</span></div>
                            <div style="font-size: 0.62rem; color: var(--mm-text-secondary, #64748B); font-weight: 700; letter-spacing: 0.3px;">CLINICAL AI HEALTHCARE SYSTEM</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: #15803D; font-weight: 600; border-left: 1px solid #E2E8F0; padding-left: 14px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>
                        Better Health<br/>Brighter Tomorrow
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_acc1, col_acc2 = st.columns(2)
        
        # --- Left Column: Personal Information ---
        with col_acc1:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Personal Information</div>
                    <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">Your basic account details.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Registered Email
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>
                <span>Registered Email</span>
            </div>""", unsafe_allow_html=True)
            st.text_input("Registered Email", value=db_user.get("email", ""), disabled=True, key="panel_prof_email", label_visibility="collapsed")
            st.markdown("<div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 12px;'>This is your registered email address.</div>", unsafe_allow_html=True)

            # Full Name
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                <span>Full Name</span>
            </div>""", unsafe_allow_html=True)
            new_p_name = st.text_input("Full Name", value=db_user.get("full_name", ""), key="panel_prof_name", label_visibility="collapsed")
            st.markdown("<div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 12px;'>Your full name as per your profile.</div>", unsafe_allow_html=True)

            # Date of Birth (DOB)
            st.markdown("""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B);">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    <span>Date of Birth (DOB)</span>
                </div>
                <span style="font-size: 0.70rem; color: #64748B;">Min 10 Years</span>
            </div>""", unsafe_allow_html=True)
            import datetime
            p_today = datetime.date.today()
            p_max_dob = datetime.date(p_today.year - 10, p_today.month, min(p_today.day, 28))
            p_min_dob = datetime.date(p_today.year - 120, 1, 1)
            u_dob_str = str(db_user.get("dob") or "").strip()
            u_init_dob = None
            if u_dob_str:
                try:
                    p = [int(x) for x in u_dob_str.split("-")]
                    if len(p) == 3:
                        u_init_dob = datetime.date(p[0], p[1], p[2])
                except Exception:
                    pass
            if not u_init_dob:
                u_init_dob = datetime.date(p_today.year - 25, p_today.month, min(p_today.day, 28))
            u_init_dob = min(max(u_init_dob, p_min_dob), p_max_dob)
            new_p_dob = st.date_input("Date of Birth", value=u_init_dob, min_value=p_min_dob, max_value=p_max_dob, key="panel_prof_dob", label_visibility="collapsed")
            u_live_age = auth_db.calculate_age_from_dob(new_p_dob)
            st.markdown(f"<div style='font-size: 0.72rem; color: #2563EB; font-weight: 600; margin-top: 2px; margin-bottom: 12px;'>Current Age: <strong>{u_live_age} years</strong> (Auto-increments every year)</div>", unsafe_allow_html=True)

            # State / Region
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span>State / Region</span>
            </div>""", unsafe_allow_html=True)
            user_curr_st = db_user.get("state") or "Select State"
            u_st_idx = INDIAN_STATES.index(user_curr_st) if user_curr_st in INDIAN_STATES else 0
            new_p_state = st.selectbox("State / Region", INDIAN_STATES, index=u_st_idx, key="panel_prof_state", label_visibility="collapsed")
            st.markdown("<div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 16px;'>Your registered clinical state or geographic territory.</div>", unsafe_allow_html=True)

            if st.button("Update Profile Information", key="btn_update_prof_name", type="primary"):
                if new_p_name.strip():
                    st_val = new_p_state if new_p_state != "Select State" else ""
                    auth_db.update_user_profile(user_id, new_p_name.strip(), state=st_val, dob=new_p_dob.strftime("%Y-%m-%d"))
                    if "user_auth" in st.session_state and isinstance(st.session_state["user_auth"], dict):
                        st.session_state["user_auth"]["full_name"] = new_p_name.strip()
                        st.session_state["user_auth"]["state"] = st_val
                        st.session_state["user_auth"]["dob"] = new_p_dob.strftime("%Y-%m-%d")
                        st.session_state["user_auth"]["age"] = u_live_age
                    st.success("Profile updated successfully!")
                    st.rerun()

        # --- Right Column: Account Details ---
        with col_acc2:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px;">
                <div style="width: 36px; height: 36px; border-radius: 9px; background: rgba(22, 163, 74, 0.1); border: 1px solid rgba(22, 163, 74, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
                </div>
                <div>
                    <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary, #0F172A);">Account Details</div>
                    <div style="font-size: 0.76rem; color: var(--mm-text-secondary, #64748B);">Your account status and activity information.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Account Status
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
                <span>Account Status</span>
            </div>""", unsafe_allow_html=True)
            status_val = db_user.get("account_status", "ACTIVE")
            st.markdown(f"""
            <div class="dmx-account-status-card" style="border-radius: 10px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="width: 10px; height: 10px; border-radius: 50%; background: #16A34A; display: inline-block;"></span>
                    <strong class="dmx-status-txt" style="font-size: 0.90rem; letter-spacing: 0.5px;">{status_val}</strong>
                </div>
                <span class="dmx-status-pill" style="border-radius: 20px; font-size: 0.72rem; font-weight: 800; padding: 2px 10px;">&#10004; Active Account</span>
            </div>
            <div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 12px;'>Status of your DocMindX AI clinical account.</div>
            """, unsafe_allow_html=True)

            # Last Login
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>Last Login</span>
            </div>""", unsafe_allow_html=True)
            last_log_val = db_user.get("last_login") or "Recent"
            st.text_input("Last Login", value=str(last_log_val), disabled=True, key="panel_prof_last_login", label_visibility="collapsed")
            st.markdown("<div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 12px;'>Your most recent login time.</div>", unsafe_allow_html=True)

            # Member Since
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span>Member Since</span>
            </div>""", unsafe_allow_html=True)
            mem_since_val = str(db_user.get("created_at") or "")[:10]
            st.text_input("Member Since", value=mem_since_val, disabled=True, key="panel_prof_member_since", label_visibility="collapsed")
            st.markdown("<div style='font-size: 0.72rem; color: #94A3B8; margin-top: 2px; margin-bottom: 14px;'>The date you joined DocMindX AI.</div>", unsafe_allow_html=True)

        # Card Footer: Sign Out / Logout + Trust Badges
        st.markdown("<div style='border-top: 1.5px solid #F1F5F9; margin-top: 20px; padding-top: 16px;'></div>", unsafe_allow_html=True)
        col_foot_act, col_foot_trust = st.columns([1, 2])
        with col_foot_act:
            if st.button("Sign Out / Logout", key="btn_prof_logout_main", type="secondary"):
                import components.auth_ui as aui
                aui.logout_user()
        with col_foot_trust:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 16px; flex-wrap: wrap; height: 100%; padding-top: 2px;">
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
                    <div><strong>Secure &amp; Encrypted</strong><br/><span style="color: #94A3B8; font-size: 0.65rem;">Your data is protected</span></div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                    <div><strong>HIPAA &amp; WHO Compliant</strong><br/><span style="color: #94A3B8; font-size: 0.65rem;">Global healthcare standards</span></div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--mm-text-secondary, #475569); font-weight: 600;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                    <div><strong>Trusted Healthcare</strong><br/><span style="color: #94A3B8; font-size: 0.65rem;">Built for a healthier tomorrow</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        
        # Bottom Copyright bar


    # -------------------------------------------------------------
    # TAB 4: CHANGE PASSWORD (IMAGE 4 DESIGN: ENHANCED CARD, CHECKLIST, TRUST)
    # -------------------------------------------------------------
    with tab_security:
        st.markdown("""
        <div class="account-settings-card" style="background: var(--mm-card-bg, #FFFFFF); border: 1.5px solid #E2E8F0; border-radius: 18px; padding: 24px 28px; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 18px; margin-bottom: 22px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); border: 1.5px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.32rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); letter-spacing: -0.2px;">Change <span style="color: #2563EB;">Password</span></h3>
                        <div style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 2px;">Password updates require your current password and will invalidate previous sessions for security.</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 32px; height: 32px; border-radius: 8px; background: #2563EB; display: flex; align-items: center; justify-content: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                                <path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h4.78"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 0.95rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1;">DocMindX <span style="color: #2563EB;">AI</span></div>
                            <div style="font-size: 0.62rem; color: var(--mm-text-secondary, #64748B); font-weight: 700; letter-spacing: 0.3px;">CLINICAL AI HEALTHCARE SYSTEM</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: #15803D; font-weight: 600; border-left: 1px solid #E2E8F0; padding-left: 14px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>
                        Better Health<br/>Brighter Tomorrow
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form(key="change_password_form"):
            # Current Password *
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                <span>Current Password <strong style="color: #DC2626;">*</strong></span>
            </div>""", unsafe_allow_html=True)
            curr_pass = st.text_input("Current Password *", type="password", placeholder="Enter your current password", label_visibility="collapsed")

            # New Password *
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 12px; margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                <span>New Password <strong style="color: #DC2626;">*</strong></span>
            </div>""", unsafe_allow_html=True)
            new_pass = st.text_input("New Password *", type="password", placeholder="Enter a new password", label_visibility="collapsed")

            # Confirm New Password *
            st.markdown("""<div style="display: flex; align-items: center; gap: 7px; font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary, #1E293B); margin-top: 12px; margin-bottom: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                <span>Confirm New Password <strong style="color: #DC2626;">*</strong></span>
            </div>""", unsafe_allow_html=True)
            conf_pass = st.text_input("Confirm New Password *", type="password", placeholder="Re-enter your new password", label_visibility="collapsed")

            # Password Requirements Callout Box (Themed)
            st.markdown("""
            <div class="dmx-pwd-req-card" style="border-radius: 12px; padding: 14px 18px; margin-top: 16px; margin-bottom: 18px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 26px; height: 26px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    </div>
                    <span class="dmx-pwd-req-title" style="font-size: 0.88rem; font-weight: 800;">Password Requirements</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px 24px; padding-left: 4px;">
                    <div class="dmx-pwd-req-item" style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; font-weight: 600;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="10"/><path fill="#FFFFFF" d="m9 12 2 2 4-4"/></svg>
                        <span>At least 8 characters</span>
                    </div>
                    <div class="dmx-pwd-req-item" style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; font-weight: 600;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="10"/><path fill="#FFFFFF" d="m9 12 2 2 4-4"/></svg>
                        <span>Include numbers (0-9)</span>
                    </div>
                    <div class="dmx-pwd-req-item" style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; font-weight: 600;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="10"/><path fill="#FFFFFF" d="m9 12 2 2 4-4"/></svg>
                        <span>Include letters (A-Z, a-z)</span>
                    </div>
                    <div class="dmx-pwd-req-item" style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; font-weight: 600;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#16A34A"><circle cx="12" cy="12" r="10"/><path fill="#FFFFFF" d="m9 12 2 2 4-4"/></svg>
                        <span>Include a special character (e.g. ! @ # $)</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Bottom Action Bar: Cancel and Update Password
            col_pact1, col_pact2 = st.columns([1, 1.4])
            with col_pact1:
                btn_cancel = st.form_submit_button("Cancel", key="btn_cancel_change_pwd")
            with col_pact2:
                btn_cp = st.form_submit_button("Update Password", type="primary", key="btn_update_pwd_submit")

            if btn_cancel:
                st.rerun()

            if btn_cp:
                ok, msg = auth_svc.change_user_password(user_id, curr_pass, new_pass, conf_pass)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        
# ============================================================
# SCAN PROFILE CONTEXT SELECTOR
# ============================================================

def render_scan_patient_selector(user: dict, key_prefix: str = "assessment") -> dict:
    """
    Renders 'Select Patient / Family Profile' selector inside the clinical assessment workflow.
    Loads dynamic options: My Profile, Saved Family Members, General Assessment.
    Uses clean dropdown (st.selectbox), zero emojis, and automatically returns patient context.
    """
    if not user:
        # Unauthenticated: General mode
        st.markdown("""
        <div style="background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 0.84rem; color: #94A3B8;">
                <span style="color: #60A5FA; font-weight: 700;">Assessment Mode: General</span> (Sign in to attach assessment to your Family Medical Vault)
            </div>
        </div>
        """, unsafe_allow_html=True)
        return {"mode": "GENERAL", "member_id": None, "name": "General Assessment", "context": {}}

    user_id = user.get("id") or user.get("user_id")
    family_members = auth_db.get_family_members(user_id)

    # Build dynamic options list with guaranteed uniqueness (General Assessment is default at index 0)
    my_profile_label = f"My Profile ({user.get('full_name', 'Patient')})"
    options = ["General Assessment", my_profile_label]
    member_by_label = {}

    seen_labels = set(["General Assessment", my_profile_label])
    for m in family_members:
        base_label = f"{m['name']} ({m['relationship']})"
        label = base_label
        idx = 2
        while label in seen_labels:
            label = f"{base_label} #{idx}"
            idx += 1
        seen_labels.add(label)
        options.append(label)
        member_by_label[label] = m

    choice = st.selectbox(
        "Select Patient / Family Profile for Assessment",
        options=options,
        index=0,
        key=f"{key_prefix}_patient_choice",
        help="Select which family member or profile this clinical assessment belongs to."
    )

    if choice == "General Assessment":
        st.markdown("""
        <div style="background: rgba(100, 116, 139, 0.1); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;">
            <span style="color: #94A3B8; font-weight: 700; font-size: 0.80rem;">GENERAL ASSESSMENT MODE</span>
            <span style="font-size: 0.78rem; color: #94A3B8; margin-left: 8px;">Results will not be linked to a specific family profile.</span>
        </div>
        """, unsafe_allow_html=True)
        return {"mode": "GENERAL", "member_id": None, "name": "General Assessment", "context": {}}

    elif choice == my_profile_label or choice.startswith("My Profile"):
        # Check if user has a 'Self' profile in family members
        self_m = next((mem for mem in family_members if str(mem.get("relationship", "")).strip().lower() == "self"), None)
        s_conds = [c["condition_name"] for c in self_m.get("conditions", [])] if self_m else []
        s_meds = [med["medicine_name"] for med in self_m.get("medications", [])] if self_m else []

        ctx_summary = []
        if self_m:
            if self_m.get("age"):
                ctx_summary.append(f"Age: {self_m['age']}")
            if self_m.get("gender"):
                ctx_summary.append(f"Gender: {self_m['gender']}")
            if self_m.get("blood_group"):
                ctx_summary.append(f"Blood Group: {self_m['blood_group']}")
            if self_m.get("height"):
                ctx_summary.append(f"Height: {self_m['height']} cm")
            if self_m.get("weight"):
                ctx_summary.append(f"Weight: {self_m['weight']} kg")
            if s_conds:
                ctx_summary.append(f"Conditions: {', '.join(s_conds[:3])}")
            if s_meds:
                ctx_summary.append(f"Medicines: {', '.join(s_meds[:3])}")

        st.markdown(f"""
        <div style="background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.35); border-left: 4px solid #3B82F6; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="color: #60A5FA; font-weight: 700; font-size: 0.84rem;">SELECTED PATIENT: {user.get('full_name', 'My Profile')}</span>
                    <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 2px;">
                        {' &bull; '.join(ctx_summary) if ctx_summary else 'Personal Medical Profile'}
                    </div>
                </div>
                <span style="font-size: 0.72rem; background: rgba(59, 130, 246, 0.2); color: #60A5FA; padding: 2px 8px; border-radius: 10px; font-weight: 700;">Context Loaded</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return {
            "mode": "PROFILE",
            "member_id": self_m["id"] if self_m else None,
            "name": user.get("full_name", "My Profile"),
            "relationship": "Self",
            "age": self_m.get("age") if self_m else None,
            "gender": self_m.get("gender") if self_m else None,
            "blood_group": self_m.get("blood_group") if self_m else None,
            "height": self_m.get("height") if self_m else None,
            "weight": self_m.get("weight") if self_m else None,
            "conditions": s_conds,
            "medications": s_meds,
            "raw_conditions": self_m.get("conditions", []) if self_m else [],
            "raw_medications": self_m.get("medications", []) if self_m else [],
            "context": {
                "patient_type": "SELF",
                "name": user.get("full_name", ""),
                "relationship": "Self",
                "age": self_m.get("age") if self_m else None,
                "gender": self_m.get("gender") if self_m else None,
                "blood_group": self_m.get("blood_group") if self_m else None,
                "height": self_m.get("height") if self_m else None,
                "weight": self_m.get("weight") if self_m else None,
                "existing_conditions": s_conds,
                "current_medicines": s_meds
            }
        }

    else:
        m = member_by_label.get(choice)
        if not m:
            return {"mode": "GENERAL", "member_id": None, "name": "General Scan", "context": {}}

        # Extract conditions & medications
        cond_names = [c["condition_name"] for c in m.get("conditions", [])]
        med_names = [med["medicine_name"] for med in m.get("medications", [])]

        ctx_summary = []
        if m.get("age"):
            ctx_summary.append(f"Age: {m['age']}")
        if m.get("gender"):
            ctx_summary.append(f"Gender: {m['gender']}")
        if m.get("blood_group"):
            ctx_summary.append(f"Blood Group: {m['blood_group']}")
        if m.get("height") and str(m['height']).strip():
            ctx_summary.append(f"Height: {m['height']} cm")
        if m.get("weight") and str(m['weight']).strip():
            ctx_summary.append(f"Weight: {m['weight']} kg")
        if cond_names:
            ctx_summary.append(f"Conditions: {', '.join(cond_names[:3])}")
        if med_names:
            ctx_summary.append(f"Medicines: {', '.join(med_names[:3])}")

        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-left: 4px solid #10B981; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.84rem;">SELECTED PATIENT / MEMBER: {m['name']} ({m['relationship']})</span>
                    <div style="font-size: 0.78rem; color: #CBD5E1; margin-top: 2px;">
                        {' &bull; '.join(ctx_summary) if ctx_summary else 'No prior conditions recorded'}
                    </div>
                </div>
                <span style="font-size: 0.72rem; background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 2px 8px; border-radius: 10px; font-weight: 700;">Context Loaded</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        return {
            "mode": "FAMILY_MEMBER",
            "member_id": m["id"],
            "name": m["name"],
            "relationship": m.get("relationship", ""),
            "age": m.get("age"),
            "gender": m.get("gender"),
            "blood_group": m.get("blood_group"),
            "height": m.get("height"),
            "weight": m.get("weight"),
            "conditions": cond_names,
            "medications": med_names,
            "raw_conditions": m.get("conditions", []),
            "raw_medications": m.get("medications", []),
            "context": {
                "name": m["name"],
                "relationship": m.get("relationship", ""),
                "age": m.get("age"),
                "gender": m.get("gender"),
                "blood_group": m.get("blood_group"),
                "height": m.get("height"),
                "weight": m.get("weight"),
                "existing_conditions": cond_names,
                "current_medicines": med_names
            }
        }
