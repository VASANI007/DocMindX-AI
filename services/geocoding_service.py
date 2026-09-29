"""
    Google Geocoding Service - Convert typed addresses & landmarks to geographic coordinates.
Includes robust fallback for high-availability.
"""
import os
import requests
import streamlit as st
from config.settings import GOOGLE_MAPS_API_KEY

_DEFAULT_GEO_CACHE = {
    "ahmedabad, gujarat": {"latitude": 23.0225, "longitude": 72.5714, "formatted_address": "Ahmedabad, Gujarat, India", "place_id": "ahmedabad_default", "source": "DocMindX Static Geo Index"},
    "ahmedabad": {"latitude": 23.0225, "longitude": 72.5714, "formatted_address": "Ahmedabad, Gujarat, India", "place_id": "ahmedabad_default", "source": "DocMindX Static Geo Index"},
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "formatted_address": "New Delhi, Delhi, India", "place_id": "delhi_default", "source": "DocMindX Static Geo Index"},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "formatted_address": "Mumbai, Maharashtra, India", "place_id": "mumbai_default", "source": "DocMindX Static Geo Index"}
}

@st.cache_data(ttl=86400, show_spinner=False)
def geocode_address(address: str):
    """
    Geocodes an address or landmark string using Google Maps Geocoding API with caching and fast lookup.
    Returns a dictionary with latitude, longitude, and formatted_address.
    """
    if not address or not address.strip():
        return None

    clean_key = address.strip().lower()
    if clean_key in _DEFAULT_GEO_CACHE:
        return _DEFAULT_GEO_CACHE[clean_key]

    api_key = GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")

    if api_key:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": address,
                "key": api_key
            }
            response = requests.get(url, params=params, timeout=12)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    return {
                        "latitude": float(location["lat"]),
                        "longitude": float(location["lng"]),
                        "formatted_address": result.get("formatted_address", address),
                        "place_id": result.get("place_id", ""),
                        "source": "Google Geocoding API"
                    }
                elif data.get("status") == "ZERO_RESULTS":
                    print(f"Google Geocoding: ZERO_RESULTS for '{address}'")
                else:
                    print(f"Google Geocoding status: {data.get('status')}")
        except Exception as e:
            print(f"Google Geocoding request error: {e}")

    # Fallback to OpenStreetMap / Nominatim if Google fails
    try:
        nom_url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "DocMindXAI/2.0"}
        nom_params = {"q": address, "format": "json", "limit": 1}
        resp = requests.get(nom_url, params=nom_params, headers=headers, timeout=8)
        if resp.status_code == 200 and resp.json():
            item = resp.json()[0]
            return {
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
                "formatted_address": item.get("display_name", address),
                "place_id": item.get("place_id", ""),
                "source": "OpenStreetMap Nominatim (Fallback)"
            }
    except Exception as e:
        print(f"Nominatim fallback error: {e}")

    return None

def reverse_geocode(latitude: float, longitude: float):
    """
    Converts latitude & longitude into a human-readable street/city address.
    """
    api_key = GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
    if api_key:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": api_key
            }
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "OK" and data.get("results"):
                    return data["results"][0].get("formatted_address", f"{latitude:.4f}, {longitude:.4f}")
        except Exception as e:
            pass

    # Fallback to OpenStreetMap Nominatim reverse geocoding
    try:
        from api.geolocation import get_detailed_address
        det = get_detailed_address(latitude, longitude)
        if det and det.get("display_name"):
            city_part = det.get("city") or det.get("suburb") or ""
            road_part = det.get("road") or ""
            parts = [p for p in [road_part, city_part] if p]
            if parts:
                return ", ".join(parts) + f" ({latitude:.4f}, {longitude:.4f})"
            return det["display_name"]
    except Exception as e:
        print(f"Nominatim reverse geocode fallback error: {e}")

    return f"Location ({latitude:.4f}, {longitude:.4f})"
