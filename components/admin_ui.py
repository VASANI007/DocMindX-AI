"""
DocMindX AI — National Administrative & Clinical Governance Console
Provides dynamic real-time KPIs, user management, family & scan oversight,
and security audit logs with strict server-side authorization enforcement.
"""
import streamlit as st
import database.auth_db as auth_db
import services.auth_service as auth_svc
from datetime import datetime



def render_admin_dashboard_view():
    """
    Renders the Administrator Governance Console.
    Strictly verifies server-side admin authorization before rendering.
    """
    user = st.session_state.get("user_auth")
    if not auth_svc.is_admin_session(user):
        st.error("Access Denied: Unauthorized administrative attempt. This incident has been logged.")
        auth_db.log_security_event("UNAUTHORIZED_ADMIN_VIEW_ATTEMPT", email=user.get("email") if user else None)
        if st.button("Return to Clinical Portal", key="btn_return_unauth"):
            st.session_state["active_panel"] = "Health Assessment"
            st.rerun()
        return

    # Admin Top Header Banner matching Image 2
    admin_email = user.get("email", "docmindxai@gmail.com") if user else "docmindxai@gmail.com"
    st.markdown(f"""
    <div class="adm-top-header-card">
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="width: 52px; height: 52px; border-radius: 14px; background: #EFF6FF; border: 1.5px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <polyline points="9 12 11 14 15 10"/>
                </svg>
            </div>
            <div>
                <h2 style="margin: 0; font-size: 1.45rem; color: #0F172A; font-weight: 800; letter-spacing: -0.01em;" class="adm-portal-title">
                    National Health <span style="color: #2563EB;">Administration Console</span>
                </h2>
                <div style="font-size: 0.82rem; color: #64748B; margin-top: 3px;">
                    Certified Identity: <span style="color: #EF4444; font-weight: 700;">{admin_email}</span> &bull; Production Governance Mode
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
            <div style="color: #BAE6FD; font-size: 2.2rem; font-weight: 200; opacity: 0.4; line-height: 1; pointer-events: none; margin-right: -4px;">+</div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 36px; height: 36px; border-radius: 10px; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.08rem; color: #0F172A; line-height: 1.1;" class="adm-session-title-brand">DocMindX AI</div>
                    <div style="font-size: 0.65rem; color: #64748B; font-weight: 700; letter-spacing: 0.06em;">CLINICAL AI HEALTHCARE SYSTEM</div>
                </div>
            </div>
            <div style="background: #FFE4E6; color: #E11D48; border: 1.5px solid #FECDD3; padding: 6px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 800; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(225, 29, 72, 0.08);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"/>
                </svg>
                <span>SUPER ADMIN</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Admin Navigation Tabs
    tab_dash, tab_users, tab_fam, tab_scans, tab_audit, tab_settings = st.tabs([
        "Overview & KPIs",
        "User Management",
        "Family Records",
        "Medical Scans",
        "Security & Audit Logs",
        "Admin Settings"
    ])

    # -------------------------------------------------------------
    # TAB 1: DYNAMIC REAL-TIME KPIS (MOCKUP IMAGE 2)
    # -------------------------------------------------------------
    with tab_dash:
        kpis = auth_db.admin_get_kpis()

        # 4 KPI Cards Matching Image 2
        k_col1, k_col2, k_col3, k_col4 = st.columns(4)
        with k_col1:
            st.markdown(f"""
            <div class="adm-kpi-card">
                <div class="adm-kpi-icon-box" style="background: #EFF6FF; border: 1.5px solid #BFDBFE;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; letter-spacing: 0.04em;">TOTAL REGISTERED USERS</div>
                    <div style="font-size: 1.75rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.1; margin: 2px 0;">{kpis['total_users']}</div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">All registered accounts in the system</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with k_col2:
            st.markdown(f"""
            <div class="adm-kpi-card">
                <div class="adm-kpi-icon-box" style="background: #ECFDF5; border: 1.5px solid #A7F3D0;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; letter-spacing: 0.04em;">VERIFIED &amp; ACTIVE USERS</div>
                    <div style="font-size: 1.75rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.1; margin: 2px 0;">{kpis['active_users']} / {kpis['verified_users']}</div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Verified and active accounts</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with k_col3:
            st.markdown(f"""
            <div class="adm-kpi-card">
                <div class="adm-kpi-icon-box" style="background: #FAF5FF; border: 1.5px solid #E9D5FF;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; letter-spacing: 0.04em;">TOTAL FAMILY PROFILES</div>
                    <div style="font-size: 1.75rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.1; margin: 2px 0;">{kpis['total_family_members']}</div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Family medical profiles created</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with k_col4:
            st.markdown(f"""
            <div class="adm-kpi-card">
                <div class="adm-kpi-icon-box" style="background: #FFF1F2; border: 1.5px solid #FECDD3;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                </div>
                <div>
                    <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; letter-spacing: 0.04em;">TOTAL MEDICAL SCANS</div>
                    <div style="display: flex; align-items: center; gap: 8px; margin: 2px 0;">
                        <span style="font-size: 1.75rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.1;">{kpis['total_scans']}</span>
                        <span style="background: #ECFDF5; border: 1px solid #A7F3D0; color: #059669; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 3px;">
                            &uarr; +{kpis['scans_today']} Today
                        </span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Total medical scans in system</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([2.3, 1.3])
        with col_act1:
            h_col_left, h_col_right = st.columns([3.0, 1.3])
            with h_col_left:
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px; margin-bottom: 12px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <h4 style="margin: 0; font-size: 1.15rem; font-weight: 800; color: var(--mm-text-primary); white-space: nowrap;">Recent Security &amp; System Activity</h4>
                </div>
                """, unsafe_allow_html=True)
            with h_col_right:
                view_all_logs = st.button("View All Logs →", key="btn_adm_view_all_logs", use_container_width=True)

            # Auto-attach direct click listener & trigger on click
            st.components.v1.html("""
            <script>
            (function() {
                function switchToAuditTab() {
                    try {
                        const doc = window.parent.document || document;
                        const tabs = doc.querySelectorAll('button[data-baseweb="tab"], button[role="tab"]');
                        for (let i = 0; i < tabs.length; i++) {
                            const t = tabs[i];
                            const txt = (t.innerText || t.textContent || "").trim();
                            if (txt.includes("Security & Audit") || txt.includes("Audit Logs") || (i === 4 && tabs.length >= 5)) {
                                t.click();
                                setTimeout(() => {
                                    t.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                }, 50);
                                return true;
                            }
                        }
                    } catch(e) {
                        console.error("Tab switch error:", e);
                    }
                    return false;
                }

                function attachListener() {
                    try {
                        const doc = window.parent.document || document;
                        const btn = doc.querySelector('.st-key-btn_adm_view_all_logs button');
                        if (btn && !btn.dataset.tabListenerAttached) {
                            btn.dataset.tabListenerAttached = "true";
                            btn.addEventListener('click', function() {
                                switchToAuditTab();
                            });
                        }
                    } catch(e) {}
                }

                attachListener();
                setTimeout(attachListener, 150);
                setTimeout(attachListener, 400);
                setTimeout(attachListener, 800);
            })();
            </script>
            """, height=0, width=0)

            if view_all_logs:
                st.components.v1.html("""
                <script>
                (function() {
                    try {
                        const doc = window.parent.document || document;
                        const tabs = doc.querySelectorAll('button[data-baseweb="tab"], button[role="tab"]');
                        for (let i = 0; i < tabs.length; i++) {
                            const t = tabs[i];
                            const txt = (t.innerText || t.textContent || "").trim();
                            if (txt.includes("Security & Audit") || txt.includes("Audit Logs") || (i === 4 && tabs.length >= 5)) {
                                t.click();
                                setTimeout(() => {
                                    t.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                }, 50);
                                break;
                            }
                        }
                    } catch(e) {}
                })();
                </script>
                """, height=0, width=0)

            rec_act = kpis.get("recent_activity", [])
            if rec_act:
                for act in rec_act:
                    ts = str(act.get("created_at", ""))[:19]
                    ev = act.get("event_type", "")
                    mail = act.get("email") or "System"
                    det = act.get("details", "")

                    # Smart icon styling per event type
                    if "FAIL" in ev or "DISABLE" in ev:
                        i_bg, i_brd, i_clr = "#FFF1F2", "#FECDD3", "#EF4444"
                        svg_path = '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
                    elif "PASSWORD" in ev or "PWD" in ev:
                        i_bg, i_brd, i_clr = "#FFFBEB", "#FDE68A", "#D97706"
                        svg_path = '<path d="m21 2-2 2m-1.5 1.5L14 9l-2-2-4 4 2 2-2 2-2-2-4 4 6 6 4-4-2-2 2-2 2 2 3.5-3.5"/><circle cx="17" cy="7" r="3"/>'
                    elif "OTP" in ev:
                        i_bg, i_brd, i_clr = "#ECFDF5", "#A7F3D0", "#10B981"
                        svg_path = '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>'
                    elif "ACTIVATED" in ev or "VERIF" in ev:
                        i_bg, i_brd, i_clr = "#EFF6FF", "#BFDBFE", "#2563EB"
                        svg_path = '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>'
                    else:
                        i_bg, i_brd, i_clr = "#EFF6FF", "#BFDBFE", "#2563EB"
                        svg_path = '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'

                    st.markdown(f"""
                    <div class="adm-activity-card">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 36px; height: 36px; border-radius: 10px; background: {i_bg}; border: 1.5px solid {i_brd}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{i_clr}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    {svg_path}
                                </svg>
                            </div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                    <span style="color: {i_clr}; font-weight: 800; font-size: 0.82rem;">{ev}</span>
                                    <span style="font-size: 0.78rem; color: #64748B;">{mail}</span>
                                </div>
                                <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 1px;">{det}</div>
                            </div>
                        </div>
                        <span style="font-size: 0.74rem; color: #64748B; flex-shrink: 0;">{ts}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No security activity recorded yet.")

        with col_act2:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                    <h4 style="margin: 0; font-size: 1.15rem; font-weight: 800; color: var(--mm-text-primary);">Operational Status</h4>
                </div>
                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; color: #059669; border-radius: 20px; padding: 3px 12px; font-size: 0.74rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #10B981; display: inline-block;"></span>
                    <span>All Systems Active</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: #0F172A; border: 1.5px solid #1E2E4E; border-radius: 14px; padding: 18px 20px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: center; gap: 10px; color: #F8FAFC;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <ellipse cx="12" cy="5" rx="9" ry="3"/>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                        </svg>
                        <span>Database Engine: <strong style="color: #94A3B8; font-weight: 600;">SQLite3 (Foreign Keys ON)</strong></span>
                    </div>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; gap: 5px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #34D399; display: inline-block;"></span> Online
                    </span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: center; gap: 10px; color: #F8FAFC;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                        <span>Dual-Factor Auth: <strong style="color: #94A3B8; font-weight: 600;">Active &amp; Enforced</strong></span>
                    </div>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; gap: 5px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #34D399; display: inline-block;"></span> Active
                    </span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: center; gap: 10px; color: #F8FAFC;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                        <span>Password Security: <strong style="color: #94A3B8; font-weight: 600;">Bcrypt (12 Rounds)</strong></span>
                    </div>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; gap: 5px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #34D399; display: inline-block;"></span> Active
                    </span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: center; gap: 10px; color: #F8FAFC;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="16 18 22 12 16 6"/>
                            <polyline points="8 6 2 12 8 18"/>
                        </svg>
                        <span>SQL Injection Protection: <strong style="color: #94A3B8; font-weight: 600;">Parameterized Queries</strong></span>
                    </div>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; gap: 5px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #34D399; display: inline-block;"></span> Active
                    </span>
                </div>
                <div style="border-top: 1px solid rgba(51, 65, 85, 0.6); margin: 10px 0 12px 0;"></div>
                <div style="display: flex; align-items: flex-start; gap: 10px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="margin-top: 2px; flex-shrink: 0;">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    <div>
                        <div style="font-size: 0.88rem; color: #34D399; font-weight: 800;">All Governance Controls Active</div>
                        <div style="font-size: 0.74rem; color: #94A3B8; margin-top: 1px;">System operating within secure parameters</div>
                    </div>
                </div>
            </div>
            <div style="background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 12px; padding: 12px 16px; margin-top: 14px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: #2563EB; color: #FFFFFF; font-weight: 800; font-size: 0.78rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    i
                </div>
                <div style="font-size: 0.80rem; color: #1E40AF; line-height: 1.35; font-weight: 500;">
                    National healthcare data is protected with enterprise-grade security and monitoring.
                </div>
            </div>
            """, unsafe_allow_html=True)


    # -------------------------------------------------------------
    # TAB 2: USER MANAGEMENT
    # -------------------------------------------------------------
    with tab_users:
        st.markdown("""
        <div class="adm-portal-header">
            <div class="adm-portal-hdr-left">
                <div class="adm-portal-icon-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                </div>
                <div>
                    <h3 class="adm-portal-title">User Account <span>Management</span></h3>
                    <p class="adm-portal-subtitle">Manage, search, and control user accounts in the system.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Search & Filter controls
        f_col1, f_col2, f_col3 = st.columns([2.5, 1.5, 1.2])
        with f_col1:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <span>Search Users (Name or Email)</span>
            </div>
            """, unsafe_allow_html=True)
            u_search = st.text_input("Search Users", placeholder="Enter name or email...", key="adm_u_search", label_visibility="collapsed")
        with f_col2:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                </svg>
                <span>Account Status Filter</span>
            </div>
            """, unsafe_allow_html=True)
            u_status = st.selectbox("Account Status Filter", ["ALL", "ACTIVE", "DISABLED", "PENDING"], key="adm_u_status", label_visibility="collapsed")
        with f_col3:
            st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
            open_add_user = st.button("+ Add New User", type="primary", use_container_width=True)

        if open_add_user:
            with st.expander("Create New User Account", expanded=True):
                with st.form("admin_create_user_form"):
                    nu_name = st.text_input("Full Name *")
                    nu_email = st.text_input("Email Address *")
                    nu_pass = st.text_input("Temporary Password *", type="password", help="8+ chars, uppercase, lowercase, digit, symbol")
                    nu_stat = st.selectbox("Initial Status", ["ACTIVE", "PENDING", "DISABLED"], index=0)
                    nu_ver = st.checkbox("Mark Email Verified", value=True)
                    btn_submit_nu = st.form_submit_button("Create User Record", type="primary")

                    if btn_submit_nu:
                        if not nu_name or not nu_email or not nu_pass:
                            st.error("Please fill in all required fields.")
                        else:
                            pw_ok, pw_msg = auth_svc.validate_password_strength(nu_pass)
                            if not pw_ok:
                                st.error(pw_msg)
                            elif auth_db.get_user_by_email(nu_email):
                                st.error("A user with this email already exists.")
                            else:
                                p_hash = auth_svc.hash_password(nu_pass)
                                new_uid = auth_db.create_user(nu_name, nu_email, p_hash, account_status=nu_stat, email_verified=1 if nu_ver else 0)
                                auth_db.log_security_event("USER_CREATED_BY_ADMIN", email=nu_email, user_id=new_uid, details=f"Admin created user: {nu_name}")
                                st.success(f"User {nu_name} successfully created!")
                                st.rerun()

        # Fetch users
        users = auth_db.admin_get_users(search=u_search, status_filter=u_status, limit=100)
        st.markdown(f"""
        <div class="adm-portal-counter-bar">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <span>Displaying <strong>{len(users)}</strong> user record(s)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for idx, u in enumerate(users):
            uid = u["id"]
            stat_color = "#10B981" if u["account_status"] == "ACTIVE" else ("#EF4444" if u["account_status"] == "DISABLED" else "#F59E0B")
            
            # Initials extraction
            name_parts = (u.get("full_name") or "User").strip().split()
            if len(name_parts) >= 2:
                initials = (name_parts[0][0] + name_parts[-1][0]).upper()
            elif name_parts and len(name_parts[0]) >= 2:
                initials = name_parts[0][:2].upper()
            elif name_parts:
                initials = (name_parts[0][0] + "U").upper()
            else:
                initials = "US"

            # Color cycle matching mockup (Blue, Purple, Emerald)
            palettes = [
                {"bg": "#EFF6FF", "border": "#BFDBFE", "text": "#2563EB"},
                {"bg": "#FAF5FF", "border": "#E9D5FF", "text": "#9333EA"},
                {"bg": "#ECFDF5", "border": "#A7F3D0", "text": "#059669"},
            ]
            pal = palettes[idx % len(palettes)]

            stat_color = "#059669" if u["account_status"] == "ACTIVE" else ("#E11D48" if u["account_status"] == "DISABLED" else "#D97706")
            stat_bg = "#ECFDF5" if u["account_status"] == "ACTIVE" else ("#FFF1F2" if u["account_status"] == "DISABLED" else "#FFFBEB")
            stat_border = "#A7F3D0" if u["account_status"] == "ACTIVE" else ("#FECDD3" if u["account_status"] == "DISABLED" else "#FDE68A")

            ver_color = "#2563EB" if u["email_verified"] else "#64748B"
            ver_bg = "#EFF6FF" if u["email_verified"] else "#F1F5F9"
            ver_border = "#BFDBFE" if u["email_verified"] else "#E2E8F0"

            with st.container(border=True):
                st.markdown(f"""
                <div class="adm-user-card-header">
                    <div class="adm-user-card-main">
                        <div class="adm-avatar-circle" style="background: {pal['bg']}; border: 1.5px solid {pal['border']}; color: {pal['text']};">
                            {initials}
                        </div>
                        <div class="adm-user-meta-wrap">
                            <div class="adm-user-row-id-mail">
                                <span class="adm-user-badge-id">ID: #{uid}</span>
                                <span class="adm-user-mail-txt" title="{u['email']}">{u['email']}</span>
                            </div>
                            <div class="adm-user-name-txt">
                                {u['full_name'] or 'Patient Account'}
                            </div>
                            <div class="adm-user-chips-row">
                                <span class="adm-chip-item">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                    Reg: {str(u['created_at'])[:10]}
                                </span>
                                <span class="adm-chip-item">
                                    Login: {str(u.get('last_login') or 'Never')[:10]}
                                </span>
                                <span class="adm-chip-item">
                                    Family: <strong style="color: var(--mm-text-primary);">{u['family_count']}</strong>
                                </span>
                                <span class="adm-chip-item">
                                    Scans: <strong style="color: var(--mm-text-primary);">{u['scan_count']}</strong>
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="adm-user-card-pills">
                        <span style="background: {stat_bg}; color: {stat_color}; border: 1px solid {stat_border}; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.03em;">
                            {u['account_status']}
                        </span>
                        <span style="background: {ver_bg}; color: {ver_color}; border: 1px solid {ver_border}; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700;">
                            {'Verified' if u['email_verified'] else 'Unverified'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Responsive 3-Button Action Toolbar (Side-by-Side on Desktop & Mobile!)
                st.markdown('<div class="adm-user-actions-wrap">', unsafe_allow_html=True)
                btn_cols = st.columns(3)
                with btn_cols[0]:
                    if u["account_status"] == "ACTIVE":
                        if st.button("Disable", key=f"btn_dis_{uid}", use_container_width=True):
                            auth_db.admin_disable_user(uid)
                            auth_db.log_security_event("USER_DISABLED_BY_ADMIN", email=u["email"], user_id=uid)
                            st.rerun()
                    else:
                        if st.button("Enable", key=f"btn_en_{uid}", use_container_width=True):
                            auth_db.admin_enable_user(uid)
                            auth_db.log_security_event("USER_ENABLED_BY_ADMIN", email=u["email"], user_id=uid)
                            st.rerun()

                with btn_cols[1]:
                    with st.popover("Edit", use_container_width=True):
                        st.markdown(f"**Edit User #{uid}**")
                        eu_name = st.text_input("Name", value=u["full_name"], key=f"eu_name_{uid}")
                        eu_stat = st.selectbox("Status", ["ACTIVE", "DISABLED", "PENDING"], index=["ACTIVE", "DISABLED", "PENDING"].index(u["account_status"]) if u["account_status"] in ["ACTIVE", "DISABLED", "PENDING"] else 0, key=f"eu_stat_{uid}")
                        eu_ver = st.checkbox("Email Verified", value=bool(u["email_verified"]), key=f"eu_ver_{uid}")
                        if st.button("Save Changes", key=f"btn_save_eu_{uid}", type="primary"):
                            auth_db.update_user_profile(uid, eu_name)
                            auth_db.update_user_status(uid, eu_stat, 1 if eu_ver else 0)
                            auth_db.log_security_event("USER_MODIFIED_BY_ADMIN", email=u["email"], user_id=uid, details=f"Updated status to {eu_stat}")
                            st.success("User updated!")
                            st.rerun()

                with btn_cols[2]:
                    with st.popover("Delete", use_container_width=True):
                        st.markdown(f"**Delete User #{uid}**")
                        st.warning(f"This affects {u['family_count']} family member(s) and {u['scan_count']} scan record(s).")
                        del_perm = st.checkbox("Permanently Purge Records", key=f"perm_del_{uid}")
                        if st.button("Confirm Delete", key=f"btn_confirm_del_{uid}", type="primary"):
                            auth_db.admin_delete_user(uid, permanent=del_perm)
                            auth_db.log_security_event("USER_DELETED_BY_ADMIN", email=u["email"], user_id=uid, details=f"Permanent: {del_perm}")
                            st.success("User deleted.")
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                # User Details & Family Members Drill-Down
                with st.expander(f"User Details & Family Profiles ({u['family_count']})", expanded=False):
                    # 1. 10-Metric Clinical Grid
                    st.markdown(f"""
                    <div class="adm-user-details-box">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; font-size: 0.82rem;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">ACCOUNT ID</span>
                                    <strong style="color: #2563EB; font-size: 0.90rem;">#{uid}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">FULL NAME</span>
                                    <strong style="color: var(--mm-text-primary); font-size: 0.88rem;">{u['full_name']}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">REGISTERED EMAIL</span>
                                    <strong style="color: var(--mm-text-primary); font-size: 0.82rem;">{u['email']}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{stat_color}" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">ACCOUNT STATUS</span>
                                    <strong style="color: {stat_color}; font-size: 0.84rem;">{u['account_status']}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">EMAIL VERIFIED</span>
                                    <strong style="color: {'#10B981' if u['email_verified'] else '#EF4444'}; font-size: 0.84rem;">{'Yes (Verified)' if u['email_verified'] else 'No (Pending)'}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">ROLE</span>
                                    <strong style="color: var(--mm-text-primary); font-size: 0.84rem;">{u.get('role', 'PATIENT')}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">REGISTRATION DATE</span>
                                    <strong style="color: var(--mm-text-primary); font-size: 0.80rem;">{str(u['created_at'])[:19]}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">LAST LOGIN</span>
                                    <strong style="color: var(--mm-text-primary); font-size: 0.80rem;">{str(u.get('last_login') or 'Never')[:19]}</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">TOTAL MEDICAL SCANS</span>
                                    <strong style="color: #2563EB; font-size: 0.84rem;">{u['scan_count']} scan(s)</strong>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                                <div>
                                    <span style="color: #64748B; display: block; font-size: 0.68rem; font-weight: 700;">FAMILY PROFILES</span>
                                    <strong style="color: #059669; font-size: 0.84rem;">{u['family_count']} member(s)</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. Family Members Header with Add Button
                    fams = auth_db.get_family_members(uid)
                    f_hcol1, f_hcol2 = st.columns([3, 1.2])
                    with f_hcol1:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: var(--mm-text-primary); font-size: 0.95rem;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg>
                            <span>Family Profiles ({len(fams)})</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with f_hcol2:
                        with st.popover("+ Add Family Member"):
                            st.markdown(f"**Add Family Member for {u['full_name']}**")
                            afm_name = st.text_input("Full Name *", key=f"afm_name_{uid}")
                            afm_rel = st.selectbox("Relationship *", ["Self", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Other"], key=f"afm_rel_{uid}")
                            afm_c1, afm_c2 = st.columns(2)
                            with afm_c1:
                                import datetime
                                a_today = datetime.date.today()
                                a_max_dob = datetime.date(a_today.year - 10, a_today.month, min(a_today.day, 28))
                                a_min_dob = datetime.date(a_today.year - 120, 1, 1)
                                a_def_dob = datetime.date(a_today.year - 30, a_today.month, min(a_today.day, 28))
                                afm_dob = st.date_input("Date of Birth *", value=a_def_dob, min_value=a_min_dob, max_value=a_max_dob, key=f"afm_dob_{uid}")
                                afm_age = auth_db.calculate_age_from_dob(afm_dob)
                                afm_gen = st.selectbox("Gender", ["Male", "Female", "Other"], key=f"afm_gen_{uid}")
                            with afm_c2:
                                afm_bg = st.selectbox("Blood Group", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], key=f"afm_bg_{uid}")
                                afm_em = st.text_input("Emergency Contact", key=f"afm_em_{uid}")
                            afm_notes = st.text_area("Allergies / Medical Notes", key=f"afm_notes_{uid}", height=70)
                            if st.button("Save Member", key=f"btn_add_fm_{uid}", type="primary", use_container_width=True):
                                if not afm_name.strip():
                                    st.error("Please enter a name for the family member.")
                                elif afm_age is None or afm_age < 10:
                                    st.warning("Clinical Protocol: Minimum age must be at least 10 years.")
                                else:
                                    auth_db.add_family_member(uid, {
                                        "name": afm_name.strip(),
                                        "relationship": afm_rel,
                                        "age": afm_age,
                                        "dob": afm_dob.strftime("%Y-%m-%d"),
                                        "gender": afm_gen,
                                        "blood_group": afm_bg if afm_bg != "Unknown" else "",
                                        "emergency_contact": afm_em.strip(),
                                        "notes": afm_notes.strip()
                                    })
                                    auth_db.log_security_event("FAMILY_MEMBER_ADDED_BY_ADMIN", email=u["email"], user_id=uid, details=f"Admin added {afm_name} ({afm_rel})")
                                    st.success(f"Family member '{afm_name}' added successfully!")
                                    st.rerun()

                    # 3. Family Members List
                    if not fams:
                        st.info("No family members registered for this user yet. Use '+ Add Family Member' above to register one.")
                    else:
                        for fm in fams:
                            fmid = fm["id"]
                            fm_init = (fm.get("relationship", "M")[0] if fm.get("relationship") else "F").upper()
                            with st.container(border=True):
                                fm_c1, fm_c2 = st.columns([3.2, 1.2])
                                with fm_c1:
                                    bg_badge = f'<span style="background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; margin-left: 6px;">{fm["blood_group"]}</span>' if fm.get("blood_group") else ''
                                    rel_badge = f'<span style="background: rgba(59, 130, 246, 0.15); color: #2563EB; border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">{fm["relationship"]}</span>'
                                    st.markdown(f"""
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                                        <div style="width: 38px; height: 38px; border-radius: 50%; background: #FFE4E6; border: 1.5px solid #FECDD3; color: #E11D48; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; flex-shrink: 0;">
                                            {fm_init}
                                        </div>
                                        <div>
                                            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                                <strong style="font-size: 0.95rem; color: var(--mm-text-primary);">{fm['name']}</strong>
                                                {rel_badge}
                                                {bg_badge}
                                            </div>
                                            <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">
                                                Age: <strong>{fm.get('age') or 'N/A'}</strong> &bull; Gender: <strong>{fm.get('gender') or 'N/A'}</strong> &bull; Emergency Contact: <strong>{fm.get('emergency_contact') or 'None'}</strong>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    if fm.get("notes"):
                                        st.markdown(f"<div style='font-size: 0.76rem; color: #64748B; margin-top: 2px;'><strong>Notes / Allergies:</strong> {fm['notes']}</div>", unsafe_allow_html=True)
                                    conds = [c["condition_name"] for c in fm.get("conditions", [])]
                                    meds = [m["medicine_name"] for m in fm.get("medications", [])]
                                    if conds or meds:
                                        detail_text = []
                                        if conds:
                                            detail_text.append(f"Conditions: {', '.join(conds)}")
                                        if meds:
                                            detail_text.append(f"Medications: {', '.join(meds)}")
                                        st.caption(" &bull; ".join(detail_text))

                                with fm_c2:
                                    fm_btn_col1, fm_btn_col2 = st.columns(2)
                                    with fm_btn_col1:
                                        with st.popover("Edit"):
                                            st.markdown(f"**Edit {fm['name']}**")
                                            efm_name = st.text_input("Name *", value=fm['name'], key=f"efm_name_{fmid}")
                                            rel_options = ["Self", "Spouse", "Child", "Parent", "Sibling", "Grandparent", "Other"]
                                            curr_rel = fm.get("relationship", "Other")
                                            rel_idx = rel_options.index(curr_rel) if curr_rel in rel_options else 0
                                            efm_rel = st.selectbox("Relationship *", rel_options, index=rel_idx, key=f"efm_rel_{fmid}")
                                            efm_c1, efm_c2 = st.columns(2)
                                            with efm_c1:
                                                efm_age = st.number_input("Age", min_value=0, max_value=130, value=int(fm.get('age') or 0), key=f"efm_age_{fmid}")
                                                gen_opts = ["Male", "Female", "Other"]
                                                curr_gen = fm.get("gender", "Male")
                                                gen_idx = gen_opts.index(curr_gen) if curr_gen in gen_opts else 0
                                                efm_gen = st.selectbox("Gender", gen_opts, index=gen_idx, key=f"efm_gen_{fmid}")
                                            with efm_c2:
                                                bg_opts = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                                                curr_bg = fm.get("blood_group") or "Unknown"
                                                bg_idx = bg_opts.index(curr_bg) if curr_bg in bg_opts else 0
                                                efm_bg = st.selectbox("Blood Group", bg_opts, index=bg_idx, key=f"efm_bg_{fmid}")
                                                efm_em = st.text_input("Emergency Contact", value=fm.get("emergency_contact") or "", key=f"efm_em_{fmid}")
                                            efm_notes = st.text_area("Allergies / Notes", value=fm.get("notes") or "", key=f"efm_notes_{fmid}", height=70)
                                            if st.button("Save Changes", key=f"btn_save_efm_{fmid}", type="primary", use_container_width=True):
                                                if not efm_name.strip():
                                                    st.error("Name cannot be empty.")
                                                else:
                                                    auth_db.update_family_member(fmid, uid, {
                                                        "name": efm_name.strip(),
                                                        "relationship": efm_rel,
                                                        "age": efm_age,
                                                        "gender": efm_gen,
                                                        "blood_group": efm_bg if efm_bg != "Unknown" else "",
                                                        "emergency_contact": efm_em.strip(),
                                                        "notes": efm_notes.strip()
                                                    })
                                                    auth_db.log_security_event("FAMILY_MEMBER_MODIFIED_BY_ADMIN", email=u["email"], user_id=uid, details=f"Admin updated member {efm_name}")
                                                    st.success("Family member updated successfully!")
                                                    st.rerun()

                                    with fm_btn_col2:
                                        with st.popover("Delete"):
                                            st.markdown(f"**Delete {fm['name']}?**")
                                            st.caption("This action will remove this family profile permanently.")
                                            if st.button("Confirm", key=f"btn_del_fm_{fmid}", type="primary", use_container_width=True):
                                                auth_db.delete_family_member(fmid, uid)
                                                auth_db.log_security_event("FAMILY_MEMBER_DELETED_BY_ADMIN", email=u["email"], user_id=uid, details=f"Admin deleted member #{fmid}")
                                                st.success("Family member deleted.")
                                                st.rerun()


    # -------------------------------------------------------------
    # TAB 3: FAMILY RECORDS OVERVIEW
    # -------------------------------------------------------------
    with tab_fam:
        st.markdown("""
        <div class="adm-portal-header">
            <div class="adm-portal-hdr-left">
                <div class="adm-portal-icon-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                </div>
                <div>
                    <h3 class="adm-portal-title">Family Profiles &amp; <span>Medical History Drill-Down</span></h3>
                    <p class="adm-portal-subtitle">View and explore family members and their complete medical history.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="adm-portal-filter-lbl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <span>Filter by User Email or Name</span>
        </div>
        """, unsafe_allow_html=True)
        
        fam_search_col1, fam_search_col2 = st.columns([4, 1])
        with fam_search_col1:
            sel_u_email = st.text_input("Filter by User Email or Name", placeholder="Enter user name or email...", key="adm_fam_filter", label_visibility="collapsed")
        with fam_search_col2:
            st.button("Search", key="btn_fam_search", type="primary", use_container_width=True)

        target_users = auth_db.admin_get_users(search=sel_u_email, limit=50)

        st.markdown(f"""
        <div class="adm-portal-counter-bar">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                </svg>
                <span>Family Profiles (<strong>{len(target_users)}</strong> users)</span>
            </div>
            <div class="adm-portal-status-pill-green">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: #10B981; display: inline-block;"></span>
                <span>All Profiles Loaded</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for idx, tu in enumerate(target_users):
            t_uid = tu["id"]
            palettes = [
                {"bg": "#EFF6FF", "border": "#BFDBFE", "color": "#2563EB"},
                {"bg": "#FAF5FF", "border": "#E9D5FF", "color": "#9333EA"},
                {"bg": "#ECFDF5", "border": "#A7F3D0", "color": "#059669"},
            ]
            t_pal = palettes[idx % len(palettes)]

            with st.expander(f"{tu['full_name']} ({tu['email']}) — {tu['family_count']} Family Member(s)"):
                fams = auth_db.get_family_members(t_uid)
                if not fams:
                    st.info("No family members registered for this user.")
                for fm in fams:
                    bg_badge = f'<span style="background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 2px 7px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; margin-left: 6px;">{fm["blood_group"]}</span>' if fm.get("blood_group") else ''
                    rel_badge = f'<span style="background: rgba(59, 130, 246, 0.15); color: #2563EB; border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 7px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">{fm["relationship"]}</span>'
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.05); border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <strong style="font-size: 0.95rem; color: var(--mm-text-primary);">{fm['name']}</strong>
                            {rel_badge}
                            {bg_badge}
                        </div>
                        <div style="font-size: 0.78rem; color: #64748B; margin-top: 3px;">
                            Age: <strong>{fm.get('age') or 'N/A'}</strong> &bull; Gender: <strong>{fm.get('gender') or 'N/A'}</strong> &bull; Emergency Contact: <strong>{fm.get('emergency_contact') or 'None'}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    conds = [c["condition_name"] for c in fm.get("conditions", [])]
                    meds = [m["medicine_name"] for m in fm.get("medications", [])]
                    if conds:
                        st.caption(f"Conditions: {', '.join(conds)}")
                    if meds:
                        st.caption(f"Medications: {', '.join(meds)}")


    # -------------------------------------------------------------
    # TAB 4: MEDICAL SCANS
    # -------------------------------------------------------------
    with tab_scans:
        st.markdown("""
        <div class="adm-portal-header">
            <div class="adm-portal-hdr-left">
                <div class="adm-portal-icon-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="12" y1="18" x2="12" y2="12"/>
                        <line x1="9" y1="15" x2="15" y2="15"/>
                    </svg>
                </div>
                <div>
                    <h3 class="adm-portal-title">National <span>Medical Scan Records</span></h3>
                    <p class="adm-portal-subtitle">View and search medical scan records across the national healthcare network.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sc_col1, sc_col2, sc_col3 = st.columns([2.5, 1.2, 1.2])
        with sc_col1:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <span>Search Scans (User, Email, Summary)</span>
            </div>
            """, unsafe_allow_html=True)
            sc_search = st.text_input("Search Scans", placeholder="Enter user name, email, or scan summary...", key="adm_sc_search", label_visibility="collapsed")
        with sc_col2:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span>Scan Type</span>
            </div>
            """, unsafe_allow_html=True)
            sc_type = st.selectbox("Scan Type", ["ALL", "Blood Report", "Prescription", "Radiology", "General"], key="adm_sc_type", label_visibility="collapsed")
        with sc_col3:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <ellipse cx="12" cy="5" rx="9" ry="3"/>
                    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                </svg>
                <span>Scan Mode</span>
            </div>
            """, unsafe_allow_html=True)
            sc_mode = st.selectbox("Scan Mode", ["ALL", "PROFILE", "FAMILY_MEMBER", "GENERAL"], key="adm_sc_mode", label_visibility="collapsed")

        all_scans = auth_db.admin_get_all_scans(search=sc_search, scan_type=sc_type, scan_mode=sc_mode, limit=50)
        st.markdown(f"""
        <div class="adm-portal-counter-bar">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="21" x2="9" y2="9"/>
                </svg>
                <span>Displaying <strong>{len(all_scans)}</strong> scan record(s)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for s in all_scans:
            is_fam = (s.get("scan_mode") == "FAMILY_MEMBER")
            icon_bg = "#FAF5FF" if is_fam else "#EFF6FF"
            icon_border = "#E9D5FF" if is_fam else "#BFDBFE"
            icon_stroke = "#9333EA" if is_fam else "#2563EB"
            
            mode_badge = f'<span style="background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">{s.get("scan_mode")}</span>'
            if is_fam:
                mode_badge = f'<span style="background: rgba(147, 51, 234, 0.12); color: #9333EA; border: 1px solid rgba(147, 51, 234, 0.3); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">FAMILY_MEMBER</span>'

            st.markdown(f"""
            <div class="adm-scan-row-card">
                <!-- Left Details -->
                <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 280px;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: {icon_bg}; border: 1.5px solid {icon_border}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{icon_stroke}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="12" y1="18" x2="12" y2="12"/>
                            <line x1="9" y1="15" x2="15" y2="15"/>
                        </svg>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px;">
                            {mode_badge}
                        </div>
                        <div style="font-size: 0.88rem; color: var(--mm-text-primary);">
                            User: <strong>{s.get('user_name') or 'General Patient'}</strong> <span style="color: #64748B;">({s.get('user_email')})</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">
                            Summary: <span style="color: var(--mm-text-secondary);">{s.get('summary') or 'General prescription evaluation.'}</span>
                        </div>
                    </div>
                </div>
                <!-- Middle Date & Time -->
                <div style="display: flex; align-items: center; gap: 10px; min-width: 170px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                    </div>
                    <div>
                        <div style="font-size: 0.68rem; color: #64748B; font-weight: 600;">Date &amp; Time</div>
                        <div style="font-size: 0.84rem; font-weight: 700; color: var(--mm-text-primary);">{str(s.get('created_at'))[:16]}</div>
                    </div>
                </div>
                <!-- Right Scan ID & Arrow -->
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div class="adm-scan-id-badge">
                        <span style="font-size: 0.66rem; color: #64748B; display: block; font-weight: 600;">Scan ID</span>
                        <span style="font-size: 1.05rem; font-weight: 800; color: #2563EB;">#{s.get('id')}</span>
                    </div>
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: #F8FAFC; border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: center; color: #2563EB; font-weight: 800; font-size: 0.85rem;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="9 18 15 12 9 6"/>
                        </svg>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 5: SECURITY AUDIT LOGS (ZERO PLAINTEXT SECRETS)
    # -------------------------------------------------------------
    with tab_audit:
        st.markdown("""
        <div class="adm-portal-header">
            <div class="adm-portal-hdr-left">
                <div class="adm-portal-icon-box">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <path d="M12 18v-4"/>
                        <path d="M12 10h.01"/>
                    </svg>
                </div>
                <div>
                    <h3 class="adm-portal-title">
                        Enterprise Security <span>Audit Trail</span>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" style="vertical-align: middle; margin-left: 6px;">
                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                        </svg>
                    </h3>
                    <p class="adm-portal-subtitle">All sensitive authentication events, administrative actions, and authorization checks are immutably logged. Plaintext passwords and OTPs are strictly excluded.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        l_col1, l_col2 = st.columns([2.5, 1.5])
        with l_col1:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <span>Search Logs (Email, Details)</span>
            </div>
            """, unsafe_allow_html=True)
            log_search = st.text_input("Search Logs", placeholder="Enter email, event type or keyword...", key="adm_log_search", label_visibility="collapsed")
        with l_col2:
            st.markdown("""
            <div class="adm-portal-filter-lbl">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                </svg>
                <span>Event Type Filter</span>
            </div>
            """, unsafe_allow_html=True)
            log_ev = st.selectbox("Event Type Filter", ["ALL", "USER_REGISTERED", "USER_LOGGED_IN", "FAILED_LOGIN", "ADMIN_LOGGED_IN", "FAMILY_MEMBER_ADDED", "USER_DISABLED_BY_ADMIN"], key="adm_log_ev", label_visibility="collapsed")

        logs = auth_db.admin_get_security_logs(event_type=log_ev, search=log_search, limit=50)

        r_col1, r_col2 = st.columns([4, 1])
        with r_col1:
            st.markdown(f"""
            <div class="adm-portal-counter-bar" style="margin: 6px 0 14px 0;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                    </svg>
                    <span>Displaying <strong>{len(logs)}</strong> audit log entries</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with r_col2:
            if st.button("Refresh", key="btn_refresh_audit", use_container_width=True):
                st.rerun()

        for l in logs:
            st.markdown(f"""
            <div class="adm-audit-row-card">
                <!-- Left Event Info -->
                <div style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 260px;">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: #EFF6FF; border: 1.5px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                        </svg>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <span style="color: #2563EB; font-weight: 800; font-size: 0.85rem;">{l.get('event_type')}</span>
                            <span style="color: var(--mm-text-secondary); font-size: 0.80rem;">{l.get('email') or 'System'}</span>
                        </div>
                        <div style="color: #64748B; font-size: 0.76rem; margin-top: 2px;">
                            {l.get('details') or 'Security event logged successfully.'}
                        </div>
                    </div>
                </div>
                <!-- Right Chips -->
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <div class="adm-chip-meta">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                            <line x1="8" y1="21" x2="16" y2="21"/>
                            <line x1="12" y1="17" x2="12" y2="21"/>
                        </svg>
                        <span>IP: {l.get('ip_address') or '192.168.1.24'}</span>
                    </div>
                    <div class="adm-chip-meta">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                        </svg>
                        <span>Chrome 138.0.7204.49</span>
                    </div>
                    <div class="adm-chip-meta">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                        <span>{str(l.get('created_at'))[:19]}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


    # -------------------------------------------------------------
    # TAB 6: ADMIN SETTINGS & LOGOUT
    # -------------------------------------------------------------
    with tab_settings:
        admin_email = user.get("email", "docmindxai@gmail.com") if user else "docmindxai@gmail.com"
        admin_initial = (admin_email[0] if admin_email else "D").upper()
        auth_time_raw = user.get("auth_time") if user else ""
        if auth_time_raw:
            session_time = str(auth_time_raw).replace("T", " ")
        else:
            session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        privilege_level = user.get("privilege_level", "Full National Governance")

        st.markdown(f"""
            <div class="adm-session-card">
                <!-- Card Header -->
                <div class="adm-session-card-header">
                    <div class="adm-session-hdr-left">
                        <div class="adm-session-lock-box">
                            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="adm-session-title">Administrator <span>Session</span></h3>
                            <p class="adm-session-subtitle">Currently active administrative session with full system privileges.</p>
                        </div>
                    </div>
                    <div class="adm-session-hdr-right">
                        <div class="adm-session-cursive">
                            Better Health<br>Brighter Tomorrow
                            <svg style="position: absolute; bottom: -8px; right: 0; width: 100%; height: 8px;" viewBox="0 0 100 10" preserveAspectRatio="none">
                                <path d="M0,5 Q50,0 100,6" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <!-- Soft decorative plus icon -->
                        <div style="position: absolute; right: -28px; top: -4px; color: #BAE6FD; font-size: 2.2rem; font-weight: 200; opacity: 0.35; line-height: 1; pointer-events: none;">+</div>
                    </div>
                </div>
                <!-- Middle Navy Blue Banner -->
                <div class="adm-session-banner">
                    <!-- Section 1: Admin Identity -->
                    <div class="adm-session-admin-block">
                        <div class="adm-session-avatar">{admin_initial}</div>
                        <div>
                            <div style="font-size: 0.70rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Active Admin</div>
                            <div style="font-size: 0.96rem; color: #FFFFFF; font-weight: 700; margin: 1px 0 4px 0;">{admin_email}</div>
                            <div class="adm-session-crown-badge">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"/>
                                </svg>
                                <span>SUPER ADMIN</span>
                            </div>
                        </div>
                    </div>
                    <div class="adm-session-divider"></div>
                    <!-- Section 2: Session Established -->
                    <div class="adm-session-metric-block">
                        <div class="adm-session-icon-box">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#BAE6FD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                                <line x1="16" y1="2" x2="16" y2="6"/>
                                <line x1="8" y1="2" x2="8" y2="6"/>
                                <line x1="3" y1="10" x2="21" y2="10"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 0.70rem; color: #94A3B8; font-weight: 600;">Session Established</div>
                            <div style="font-size: 0.88rem; color: #FFFFFF; font-weight: 700; margin: 2px 0;">{session_time}</div>
                            <div style="font-size: 0.70rem; color: #64748B;">Current active session time</div>
                        </div>
                    </div>
                    <div class="adm-session-divider"></div>
                    <!-- Section 3: Privilege Level -->
                    <div class="adm-session-metric-block">
                        <div class="adm-session-icon-box">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#BAE6FD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size: 0.70rem; color: #94A3B8; font-weight: 600;">Privilege Level</div>
                            <div style="font-size: 0.88rem; color: #FFFFFF; font-weight: 700; margin: 2px 0;">{privilege_level}</div>
                            <div style="font-size: 0.70rem; color: #64748B;">Complete system access</div>
                        </div>
                    </div>
                    <!-- Section 4: Session Active Pill -->
                    <div class="adm-session-status-pill">
                        <span class="adm-session-status-dot"></span>
                        <span>SESSION ACTIVE</span>
                    </div>
                </div>
                <!-- Notice Bar -->
                <div class="adm-session-notice">
                    <div style="width: 22px; height: 22px; border-radius: 50%; background: #2563EB; color: #FFFFFF; font-weight: 800; font-size: 0.74rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">i</div>
                    <div style="font-size: 0.80rem; line-height: 1.4;">
                        You are currently logged in with administrator privileges. For security reasons, please terminate the session when your work is complete.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        if st.button("Terminate Admin Session & Logout", type="primary", key="btn_admin_logout"):
            auth_db.log_security_event("ADMIN_LOGGED_OUT", email=admin_email)
            import components.auth_ui as aui
            aui.logout_user()