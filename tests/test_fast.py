import requests, time

lat, lon = 23.0225, 72.5714
t0 = time.time()
from test_engine import fetch_live_healthcare

res = fetch_live_healthcare(lat, lon, "hospital", 10000)
print(f"Discovered {len(res)} hospitals within 10KM in {round(time.time() - t0, 2)}s")
