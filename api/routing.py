"""
    OSRM Routing & Turn-by-Turn Navigation Engine for DocMindX AI
Provides road path geometries, estimated travel times (ETA), and distance calculation for Car, Bike, and Walk modes.
"""
import requests

OSRM_URL = "http://router.project-osrm.org/route/v1"

def get_route_directions(start_lat: float, start_lon: float, end_lat: float, end_lon: float, mode: str = "car") -> dict:
    """
    Fetch exact road route from start (user) to end (facility) using OSRM.
    Modes:
      - 'car' / 'driving': car driving route
      - 'bike' / 'motorcycle': bike driving route
      - 'walk' / 'foot': walking pedestrian route
    Returns:
      {
        "distance_km": float,
        "duration_min": float,
        "route_coordinates": [[lat, lon], [lat, lon], ...],
        "mode": str,
        "status": "success" | "error"
      }
    """
    profile = "driving"
    if mode in ["walk", "foot", "walking"]:
        profile = "foot"
    elif mode in ["bike", "motorcycle", "bicycle"]:
        profile = "driving" # OSRM public server supports driving & foot

    url = f"{OSRM_URL}/{profile}/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("routes"):
                best_route = data["routes"][0]
                dist_km = round(best_route.get("distance", 0) / 1000, 2)
                dur_sec = best_route.get("duration", 0)
                
                # Adjust duration based on vehicle mode
                if mode in ["bike", "motorcycle"]:
                    dur_min = max(1, round((dist_km / 35.0) * 60)) # ~35 km/h avg in Indian city traffic
                elif mode in ["walk", "foot", "walking"]:
                    dur_min = max(1, round((dist_km / 4.5) * 60)) # ~4.5 km/h avg walking speed
                else:
                    dur_min = max(1, round(dur_sec / 60))
                
                # Convert GeoJSON [lon, lat] coordinates to Folium [lat, lon]
                geojson_coords = best_route.get("geometry", {}).get("coordinates", [])
                folium_coords = [[coord[1], coord[0]] for coord in geojson_coords]

                return {
                    "distance_km": dist_km,
                    "duration_min": dur_min,
                    "route_coordinates": folium_coords,
                    "mode": mode,
                    "status": "success"
                }
    except Exception as e:
        print(f"Routing lookup notice: {e}")

    # Straight-line fallback polyline if routing server is unreachable
    return {
        "distance_km": round(((start_lat - end_lat)**2 + (start_lon - end_lon)**2)**0.5 * 111, 2),
        "duration_min": 15,
        "route_coordinates": [[start_lat, start_lon], [end_lat, end_lon]],
        "mode": mode,
        "status": "fallback"
    }
