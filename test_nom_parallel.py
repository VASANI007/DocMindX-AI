import requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed

keywords = [
    "hospital", "multispeciality hospital", "general hospital", "medical center",
    "civil hospital", "trauma center", "maternity hospital", "children hospital",
    "orthopedic hospital", "eye hospital", "cardiac hospital", "surgical hospital",
    "nursing home", "clinic", "polyclinic", "dispensary", "health center",
    "ayurvedic hospital", "private hospital", "government hospital"
]

lat, lon = 23.0225, 72.5714
t0 = time.time()
results = {}

def search_kw(kw):
    url = f"https://nominatim.openstreetmap.org/search?q={kw}+near+{lat},{lon}&format=json&limit=50&addressdetails=1"
    headers = {"User-Agent": "DocMindXAI-HealthSearch/3.0"}
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

with ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(search_kw, kw) for kw in keywords]
    for f in as_completed(futs):
        for item in f.result():
            name = item.get("name") or item.get("display_name", "").split(",")[0]
            if name and name not in results:
                results[name] = item

print(f"Discovered {len(results)} facilities in {round(time.time() - t0, 2)}s!")
