"""
    Google Geocoding Service - Convert typed addresses & landmarks to geographic coordinates.
Includes robust fallback for high-availability.
"""
import os
import requests
from config.settings import GOOGLE_MAPS_API_KEY

def geocode_address(address: str):
    """
    Geocodes an address or landmark string using Google Maps Geocoding API.
    Returns a dictionary with latitude, longitude, and formatted_address.
    """
    if not address or not address.strip():
        return None

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
            print(f"Reverse geocode error: {e}")

    return f"Location ({latitude:.4f}, {longitude:.4f})"
