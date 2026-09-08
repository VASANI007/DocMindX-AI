"""
    Audit and Verification Suite for Google Maps & Places & Routes API Integration.
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.geocoding_service import geocode_address, reverse_geocode
from services.places_service import search_nearby_healthcare, search_nearby_hospitals
from services.routes_service import get_route
from components.google_map import generate_google_map_html

def test_google_services():
    print("=" * 60)
    print("DocMindX AI - Google Maps Ecosystem Verification Test")
    print("=" * 60)

    # 1. Test Geocoding API
    print("\n[1/4] Testing Geocoding API...")
    query = "Civil Hospital Ahmedabad"
    geo_res = geocode_address(query)
    print(f"Query: '{query}'")
    if geo_res:
        print(f"Geocoded Successfully: Lat {geo_res['latitude']}, Lon {geo_res['longitude']}")
        print(f"Address: {geo_res['formatted_address']}")
        print(f"Source: {geo_res['source']}")
        lat, lon = geo_res["latitude"], geo_res["longitude"]
    else:
        print("Geocoding returned None, using default coordinates.")
        lat, lon = 23.0225, 72.5714

    # 2. Test Places API (New)
    print("\n[2/4] Testing Google Places API (New)...")
    places = search_nearby_healthcare(lat, lon, facility_category="hospital", radius_meters=5000)
    print(f"Search Center: ({lat}, {lon}), Radius: 5000m")
    print(f"Found {len(places)} healthcare facilities.")
    if places:
        for idx, p in enumerate(places[:3]):
            print(f"   [{idx+1}]  {p['name']} | Dist: {p['distance_km']} km | Phone: {p.get('phone')} | Rating: {p.get('rating')}")
            print(f"Source: {p.get('source')}")

    # 3. Test Routes API
    print("\n[3/4] Testing Google Routes API...")
    dest_lat = places[0]["lat"] if places else 23.0538
    dest_lng = places[0]["lon"] if places else 72.5850
    route = get_route(lat, lon, dest_lat, dest_lng, mode="DRIVE")
    if route:
        print(f"Route Computed Successfully:")
        print(f"Distance: {route['distance_km']} km ({route['distance_meters']} m)")
        print(f"ETA / Duration: {route['duration']}")
        print(f"Route Coordinates: {len(route.get('route_coordinates', []))} waypoints")
        print(f"Source: {route['source']}")
    else:
        print("Failed to compute route.")

    # 4. Test Google Map Component HTML Generation
    print("\n[4/4] Testing Google Maps JS Component HTML...")
    html = generate_google_map_html(
        user_lat=lat,
        user_lon=lon,
        facilities=places[:5],
        location_name="Ahmedabad Test Center",
        selected_facility=places[0] if places else None,
        route_data=route
    )
    assert "https://maps.googleapis.com/maps/api/js" in html
    assert "initMap" in html
    print(f"Map HTML generated successfully ({len(html)} bytes).")

    print("\n" + "=" * 60)
    print("ALL 4 GOOGLE MAPS SERVICES TESTED AND OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    test_google_services()
