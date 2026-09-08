from api.overpass import query_nearby_healthcare, _fetch_overpass_server, OVERPASS_SERVERS, query_nominatim_facilities
import json

print("Testing Overpass API directly...")
overpass_query = """
[out:json][timeout:25];
(
  node["amenity"~"hospital|clinic|doctors|nursing_home"](around:5000,23.0225,72.5714);
  way["amenity"~"hospital|clinic|doctors|nursing_home"](around:5000,23.0225,72.5714);
  relation["amenity"~"hospital|clinic|doctors|nursing_home"](around:5000,23.0225,72.5714);
  node["healthcare"](around:5000,23.0225,72.5714);
  way["healthcare"](around:5000,23.0225,72.5714);
);
out center;
"""

for i, s in enumerate(OVERPASS_SERVERS):
    data = _fetch_overpass_server(s, overpass_query)
    elem_cnt = len(data.get("elements", [])) if data else "FAILED"
    print(f"Server {i} ({s}): {elem_cnt}")

nom = query_nominatim_facilities(23.0225, 72.5714, "hospital", limit=100)
print(f"Nominatim returned: {len(nom)}")

hospitals = query_nearby_healthcare(23.0225, 72.5714, "hospital", radius_meters=5000)
print(f"query_nearby_healthcare returned: {len(hospitals)}")
