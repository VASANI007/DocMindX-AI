import requests, time, math
from concurrent.futures import ThreadPoolExecutor, as_completed

lat, lon = 23.0225, 72.5714
radius_meters = 5000
radius_km = radius_meters / 1000.0

# Generate sub-points
delta_lat = (radius_km * 0.6) / 111.0
delta_lon = (radius_km * 0.6) / (111.0 * math.cos(math.radians(lat)))

sub_points = [
    (lat, lon),
    (lat + delta_lat, lon),
    (lat - delta_lat, lon),
    (lat, lon + delta_lon),
    (lat, lon - delta_lon),
    (lat + delta_lat * 0.7, lon + delta_lon * 0.7),
    (lat + delta_lat * 0.7, lon - delta_lon * 0.7),
    (lat - delta_lat * 0.7, lon + delta_lon * 0.7),
    (lat - delta_lat * 0.7, lon - delta_lon * 0.7),
]

keywords = ["hospital", "clinic", "multispeciality hospital", "nursing home", "trauma center"]

tasks = []
for p_lat, p_lon in sub_points:
    for kw in keywords:
        tasks.append((p_lat, p_lon, kw))

print(f"Total queries to dispatch: {len(tasks)}")

results = {}
t0 = time.time()

def query_nom(p_lat, p_lon, kw):
    url = f"https://nominatim.openstreetmap.org/search?q={kw}+near+{p_lat:.4f},{p_lon:.4f}&format=json&limit=50&addressdetails=1"
    headers = {"User-Agent": "DocMindXAI-MultiSearch/4.0"}
    try:
        r = requests.get(url, headers=headers, timeout=3.5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

with ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(query_nom, pt[0], pt[1], pt[2]) for pt in tasks]
    for f in as_completed(futs):
        items = f.result() or []
        for it in items:
            name = it.get("name") or it.get("display_name", "").split(",")[0]
            if name and name not in results:
                results[name] = it

print(f"Discovered {len(results)} distinct facilities across the perimeter in {round(time.time() - t0, 2)}s!")
