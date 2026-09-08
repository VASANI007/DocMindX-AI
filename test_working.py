import requests

candidates = [
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

q = """
[out:json][timeout:25];
(
  node["amenity"~"hospital|clinic|doctors|nursing_home"](around:5000,23.0225,72.5714);
  way["amenity"~"hospital|clinic|doctors|nursing_home"](around:5000,23.0225,72.5714);
  node["healthcare"](around:5000,23.0225,72.5714);
  way["healthcare"](around:5000,23.0225,72.5714);
);
out center;
"""

for c in candidates:
    try:
        r = requests.post(c, data={"data": q}, headers={"User-Agent": "DocMindXAI-Healthcare/2.0"}, timeout=15)
        print(f"{c} POST -> {r.status_code}, elements: {len(r.json().get('elements', []))}", flush=True)
    except Exception as e:
        print(f"{c} POST ERROR -> {e}", flush=True)
