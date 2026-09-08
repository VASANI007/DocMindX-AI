import requests, time, math
from concurrent.futures import ThreadPoolExecutor, as_completed

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return round(2 * R * math.asin(math.sqrt(a)), 2)

lat, lon = 23.0225, 72.5714
radius_km = 10.0

keywords = [
    "hospital", "clinic", "multispeciality hospital", "nursing home",
    "maternity hospital", "eye hospital", "orthopedic hospital", "ent hospital",
    "pediatric hospital", "dental clinic", "trauma center", "cardiac hospital",
    "cancer hospital", "surgical hospital", "ayurvedic hospital", "dispensary",
    "health center", "civil hospital", "care hospital", "apollo hospital"
]

t0 = time.time()
results = {}

def query_photon(kw):
    url = f"https://photon.komoot.io/api/?q={kw}&lat={lat}&lon={lon}&limit=100"
    headers = {"User-Agent": "DocMindXAI/2.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("features", [])
    except Exception as e:
        pass
    return []

with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(query_photon, kw) for kw in keywords]
    for f in as_completed(futs):
        for feat in f.result():
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                f_lon, f_lat = coords[0], coords[1]
                name = props.get("name", "").strip()
                if not name or name.lower() in ["hospital", "clinic", "dispensary"]:
                    continue
                dist = haversine(lat, lon, f_lat, f_lon)
                if dist <= radius_km:
                    if name not in results:
                        results[name] = {
                            "name": name,
                            "lat": f_lat,
                            "lon": f_lon,
                            "dist": dist,
                            "district": props.get("district", props.get("city", "")),
                            "postcode": props.get("postcode", "")
                        }

print(f"Total REAL UNIQUE facilities found: {len(results)} in {round(time.time() - t0, 2)}s!")
print("First 15:")
for k, v in list(results.items())[:15]:
    print(f" - {v['name']} ({v['dist']} km) - {v['district']} {v['postcode']}")
