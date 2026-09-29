"""
DocMindX AI — CyberMind-Style Animated 10-Second Floating Toast Popup System
Faithfully replicating CyberMind-AI's dark glassmorphic floating toast notification:
- 10-second auto-countdown timer
- Animated moving progress bar (move-line from 100% to 0%)
- Top-right screen anchor with position: fixed
- Pure Streamlit direct DOM rendering via st.markdown (NO sandboxed iframes)
- Zero document layout space reserved
- Interactive dismiss button (×)
- Supports: success, warning, error, info
"""
import time
import html
import streamlit as st


def trigger_popup(title: str, message: str, status_type: str = "success"):
    """
    Triggers an animated 10-second floating toast notification.
    status_type: 'success' | 'warning' | 'error' | 'info'
    """
    st.session_state["_cyber_toast_data"] = {
        "title": title,
        "msg": message,
        "kind": status_type,
        "time": time.time(),
    }


# Convenient alias matching CyberMind-AI
show_cyber_toast = trigger_popup


def check_and_render_pending_popup():
    """
    Renders the pending 10-second CyberMind floating toast notification.
    Uses st.markdown with fixed positioning and a moving progress line.
    """
    toast_data = st.session_state.get("_cyber_toast_data")
    if not toast_data:
        return

    toast_time = toast_data.get("time", 0)
    elapsed = time.time() - toast_time

    # Dismiss after 10.5 seconds
    if elapsed > 10.5:
        st.session_state.pop("_cyber_toast_data", None)
        return

    # Guard: only render once per script run
    run_token = f"{toast_time}_{st.session_state.get('_turn_counter', 0)}"
    if st.session_state.get("_last_rendered_toast_token") == run_token:
        return
    st.session_state["_last_rendered_toast_token"] = run_token

    kind = toast_data.get("kind", "success").lower()
    title = html.escape(str(toast_data.get("title", "Notice")))
    msg = html.escape(str(toast_data.get("msg", "")))

    if kind == "error":
        icon_img = "https://cdn-icons-png.flaticon.com/512/564/564619.png"
        icon_svg = (
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#EF4444' stroke-width='2.5' "
            "stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle>"
            "<line x1='15' y1='9' x2='9' y2='15'></line><line x1='9' y1='9' x2='15' y2='15'></line></svg>"
        )
        border_color = "rgba(239, 68, 68, 0.55)"
        left_accent  = "#EF4444"
        shadow_color = "rgba(239, 68, 68, 0.35)"
        grad_bar     = "linear-gradient(90deg, #EF4444, #F97316)"
    elif kind == "warning":
        icon_img = "https://cdn-icons-png.flaticon.com/512/564/564619.png"
        icon_svg = (
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#FFAA00' stroke-width='2.5' "
            "stroke-linecap='round' stroke-linejoin='round'><path d='m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z'></path>"
            "<line x1='12' y1='9' x2='12' y2='13'></line><line x1='12' y1='17' x2='12.01' y2='17'></line></svg>"
        )
        border_color = "rgba(255, 170, 0, 0.55)"
        left_accent  = "#FFAA00"
        shadow_color = "rgba(255, 170, 0, 0.30)"
        grad_bar     = "linear-gradient(90deg, #FFAA00, #FF5500)"
    elif kind == "info":
        icon_img = "https://cdn-icons-png.flaticon.com/512/6532/6532060.png"
        icon_svg = (
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#00D2FF' stroke-width='2.5' "
            "stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle>"
            "<line x1='12' y1='16' x2='12' y2='12'></line><line x1='12' y1='8' x2='12.01' y2='8'></line></svg>"
        )
        border_color = "rgba(0, 210, 255, 0.55)"
        left_accent  = "#00D2FF"
        shadow_color = "rgba(0, 210, 255, 0.30)"
        grad_bar     = "linear-gradient(90deg, #00D2FF, #0055FF)"
    else:  # success
        icon_img = "https://cdn-icons-png.flaticon.com/512/6532/6532060.png"
        icon_svg = (
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#22C55E' stroke-width='2.5' "
            "stroke-linecap='round' stroke-linejoin='round'><path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'></path>"
            "<polyline points='22 4 12 14.01 9 11.01'></polyline></svg>"
        )
        border_color = "rgba(34, 197, 94, 0.55)"
        left_accent  = "#22C55E"
        shadow_color = "rgba(34, 197, 94, 0.30)"
        grad_bar     = "linear-gradient(90deg, #22C55E, #00D2FF)"

    remaining_sec = max(0.1, 10.0 - elapsed)
    toast_id = int(toast_time * 1000)

    # Dark glassmorphic toast with Flaticon img + inline SVG fallback, close button, and moving line
    toast_html = f"""
    <div id="cyber-toast-{toast_id}" class="st-cyber-toast-box-{toast_id}">
        <div style="display: flex; align-items: flex-start; gap: 12px; padding-right: 10px; flex: 1; min-width: 0;">
            <span style="display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px;">
                <img src="{icon_img}" style="width:22px; height:22px; object-fit:contain;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';" />
                <span style="display: none;">{icon_svg}</span>
            </span>
            <div style="flex: 1; min-width: 0;">
                <div style="font-weight: 700; font-size: 14px; color: #FFFFFF; margin-bottom: 3px; letter-spacing: -0.2px;">{title}</div>
                <div style="font-weight: 400; font-size: 12.5px; color: rgba(255, 255, 255, 0.88); line-height: 1.45; word-break: break-word;">{msg}</div>
            </div>
        </div>
        <button class="st-cyber-toast-close-{toast_id}" onclick="var el=document.getElementById('cyber-toast-{toast_id}'); if(el) el.remove();" title="Dismiss">✕</button>
        <div class="st-cyber-toast-progress-{toast_id}"></div>
    </div>

    <style>
    /* Zero out host markdown element height so no empty whitespace is created */
    div.element-container:has(> .st-cyber-toast-box-{toast_id}),
    div[data-testid="stElementContainer"]:has(.st-cyber-toast-box-{toast_id}) {{
        position: absolute !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        pointer-events: none !important;
        overflow: visible !important;
    }}

    .st-cyber-toast-box-{toast_id} {{
        position: fixed !important;
        top: 24px !important;
        right: 24px !important;
        z-index: 2147483647 !important;
        display: flex !important;
        align-items: flex-start !important;
        justify-content: space-between !important;
        min-width: 320px !important;
        max-width: 440px !important;
        padding: 14px 18px 18px 18px !important;
        background: rgba(18, 24, 38, 0.96) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1px solid {border_color} !important;
        border-left: 4px solid {left_accent} !important;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.5), 0 0 22px {shadow_color} !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        line-height: 1.4 !important;
        overflow: hidden !important;
        pointer-events: auto !important;
        animation: 
            slideInCyberToast_{toast_id} 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards,
            slideOutCyberToast_{toast_id} 0.4s cubic-bezier(0.16, 1, 0.3, 1) {remaining_sec:.2f}s forwards !important;
    }}

    .st-cyber-toast-close-{toast_id} {{
        background: transparent !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.60) !important;
        font-size: 15px !important;
        font-weight: bold !important;
        cursor: pointer !important;
        padding: 2px 6px !important;
        margin-left: 6px !important;
        border-radius: 6px !important;
        transition: all 0.18s ease !important;
        line-height: 1 !important;
        flex-shrink: 0 !important;
    }}

    .st-cyber-toast-close-{toast_id}:hover {{
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.16) !important;
    }}

    .st-cyber-toast-progress-{toast_id} {{
        position: absolute !important;
        bottom: 0 !important;
        left: 0 !important;
        height: 3.5px !important;
        width: 100% !important;
        background: {grad_bar} !important;
        transform-origin: left center !important;
        animation: cyberToastProgressAnimation_{toast_id} {remaining_sec:.2f}s linear forwards !important;
    }}

    @keyframes slideInCyberToast_{toast_id} {{
        from {{ transform: translateX(120%); opacity: 0; }}
        to   {{ transform: translateX(0);    opacity: 1; }}
    }}

    @keyframes slideOutCyberToast_{toast_id} {{
        from {{ transform: translateX(0);    opacity: 1; }}
        to   {{ transform: translateX(120%); opacity: 0; }}
    }}

    @keyframes cyberToastProgressAnimation_{toast_id} {{
        0%   {{ transform: scaleX(1); }}
        100% {{ transform: scaleX(0); }}
    }}
    </style>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


# Convenient alias
render_cyber_toast = check_and_render_pending_popup
