import requests

servers = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

query = """
[out:json][timeout:15];
(
  node["amenity"="hospital"](around:5000,23.0225,72.5714);
);
out center;
"""

headers = {
    "User-Agent": "DocMindXAI-Healthcare/2.0",
    "Accept": "*/*"
}

for s in servers:
    print(f"Trying {s} ...", flush=True)
    try:
        r = requests.get(s, params={"data": query}, headers=headers, timeout=6)
        print(f"  GET {s} -> status {r.status_code}, length {len(r.content)}", flush=True)
        if r.status_code == 200:
            data = r.json()
            print(f"  Elements: {len(data.get('elements', []))}", flush=True)
            break
    except Exception as e:
        print(f"  GET {s} failed: {e}", flush=True)

    try:
        r = requests.post(s, data={"data": query}, headers=headers, timeout=6)
        print(f"  POST {s} -> status {r.status_code}, length {len(r.content)}", flush=True)
        if r.status_code == 200:
            data = r.json()
            print(f"  Elements: {len(data.get('elements', []))}", flush=True)
            break
    except Exception as e:
        print(f"  POST {s} failed: {e}", flush=True)
