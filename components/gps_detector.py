"""
DocMindX AI - Native Device GPS Detector Component
Uses Streamlit custom component postMessage API to securely acquire
real client-side device GPS sensor coordinates with high accuracy and standard accuracy fallback.
"""
import os
import streamlit as st
import streamlit.components.v1 as components

_COMPONENT_PATH = os.path.join(os.path.dirname(__file__), "gps_button")
_gps_button_func = components.declare_component("docmindx_gps_button", path=_COMPONENT_PATH)


def render_gps_detector(key: str = "docmindx_live_gps_button"):
    """
    Renders the live GPS detector component.
    Returns:
        dict with status ('SUCCESS' or 'ERROR') and lat, lon, accuracy if SUCCESS.
        None if not clicked or idle.
    """
    return _gps_button_func(key=key)
