import requests, time

t0 = time.time()
q = """
[out:json][timeout:30];
(
  node["amenity"="hospital"](around:5000,23.0225,72.5714);
  way["amenity"="hospital"](around:5000,23.0225,72.5714);
  node["amenity"="clinic"](around:5000,23.0225,72.5714);
  way["amenity"="clinic"](around:5000,23.0225,72.5714);
);
out center;
"""
url = "https://overpass.kumi.systems/api/interpreter"
try:
    r = requests.post(url, data={"data": q}, headers={"User-Agent": "DocMindXAI/2.0"}, timeout=30)
    print("kumi status:", r.status_code, "time:", time.time() - t0, "elements:", len(r.json().get('elements', [])))
except Exception as e:
    print("kumi error:", e, "time:", time.time() - t0)

t0 = time.time()
url2 = "https://overpass.private.coffee/api/interpreter"
try:
    r = requests.post(url2, data={"data": q}, headers={"User-Agent": "DocMindXAI/2.0"}, timeout=30)
    print("coffee status:", r.status_code, "time:", time.time() - t0, "elements:", len(r.json().get('elements', [])))
except Exception as e:
    print("coffee error:", e, "time:", time.time() - t0)
