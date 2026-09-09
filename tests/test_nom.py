import requests

keywords = [
    "hospital", "multispeciality hospital", "clinic", "dispensary", "nursing home",
    "maternity home", "eye hospital", "orthopedic hospital", "ent hospital",
    "dental clinic", "pediatric hospital", "surgical hospital", "health center",
    "trauma center", "cardiac hospital", "diagnostic center", "pathology laboratory",
    "apollo", "care hospital", "city hospital", "civil hospital", "ayurvedic hospital"
]

results = []
seen = set()
lat, lon = 23.0225, 72.5714

for kw in keywords[:8]:
    url = f"https://nominatim.openstreetmap.org/search?q={kw}+near+{lat},{lon}&format=json&limit=50&addressdetails=1"
    headers = {"User-Agent": "DocMindXAI-Dev/2.0"}
    try:
        r = requests.get(url, headers=headers, timeout=3)
        data = r.json()
        for d in data:
            name = d.get("name") or d.get("display_name", "").split(",")[0]
            if name not in seen:
                seen.add(name)
                results.append(name)
    except Exception as e:
        print("Err:", e)

print(f"Total unique facilities found via Nominatim: {len(results)}")
print("First 10:", results[:10])
