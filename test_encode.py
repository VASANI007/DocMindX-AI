import requests

# Test with literal + vs space
kw1 = "multispeciality+hospital"
url1 = f"https://nominatim.openstreetmap.org/search?q={kw1}+near+23.0225,72.5714&format=json&limit=10"
r1 = requests.get(url1, headers={"User-Agent": "TestDocMind/1.0"})
print("URL1:", r1.url, "Results:", len(r1.json()))

kw2 = "multispeciality hospital"
url2 = f"https://nominatim.openstreetmap.org/search"
r2 = requests.get(url2, params={"q": f"{kw2} near 23.0225, 72.5714", "format": "json", "limit": 10}, headers={"User-Agent": "TestDocMind/1.0"})
print("URL2:", r2.url, "Results:", len(r2.json()))
