import requests, time, math

lat, lon = 23.0225, 72.5714
radius_km = 10.0
# approx degree delta
delta_lat = radius_km / 111.0
delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

min_lon = lon - delta_lon
max_lon = lon + delta_lon
min_lat = lat - delta_lat
max_lat = lat + delta_lat

viewbox = f"{min_lon:.5f},{max_lat:.5f},{max_lon:.5f},{min_lat:.5f}"
print("Viewbox:", viewbox)

url = f"https://nominatim.openstreetmap.org/search?format=json&viewbox={viewbox}&bounded=0&q=hospital&limit=50&addressdetails=1"
r = requests.get(url, headers={"User-Agent": "DocMindXAI/3.0"})
print("Status:", r.status_code, "Results:", len(r.json()) if r.status_code == 200 else "Err")
