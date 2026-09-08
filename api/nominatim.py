"""
    OpenStreetMap Nominatim Geocoding and Reverse Geocoding Client
"""
import requests
import urllib.parse

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "DocMindXAI-HealthcareApp/2.0 (contact: support@DocMindX.ai)"}

def geocode_city_district(query):
    """
    Convert a district/city/state name into (latitude, longitude, display_name).
    """
    if not query or not query.strip():
        return 23.0225, 72.5714, "Ahmedabad, Gujarat, India" # Default fallback
        
    try:
        params = {
            "q": f"{query.strip()}, India",
            "format": "json",
            "limit": 1
        }
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                name = results[0].get("display_name", query)
                return lat, lon, name
    except Exception as e:
        print(f"Nominatim Geocoding note: {e}")
        
    return 23.0225, 72.5714, f"{query}, India"
def reverse_geocode(lat, lon):
    """
    Convert coordinates into a readable address string.
    """
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        response = requests.get(REVERSE_URL, params=params, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", f"Location ({lat:.4f}, {lon:.4f})")
    except Exception as e:
        print(f"Reverse geocode note: {e}")
    return f"Location ({lat:.4f}, {lon:.4f})"
