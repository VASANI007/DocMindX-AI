"""
    DocMindX AI - Day/Night Theme Toggle Switch Component
Native Streamlit toggle switch connecting directly into session state.
Eliminates dynamic module import iframe errors completely.
"""
import streamlit as st


def theme_toggle_switch(is_dark: bool = False, key: str = "theme_toggle_switch") -> bool:
    """
    Renders the Theme Toggle Switch and returns the boolean dark mode state directly.
    """
    label = "Dark Mode" if is_dark else "Light Mode"
    return st.toggle(label, value=is_dark, key=key)
