import requests
import concurrent.futures

endpoints = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://api.openstreetmap.fr/oapi/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter"
]

def test_endpoint(url):
    try:
        r = requests.get(url, params={"data": "[out:json];node(around:1000,23.0225,72.5714)[\"amenity\"=\"hospital\"];out count;"}, headers={"User-Agent": "DocMindXAI/2.0"}, timeout=4)
        return url, r.status_code, len(r.content)
    except Exception as e:
        return url, "ERROR", str(e)[:60]

with concurrent.futures.ThreadPoolExecutor(max_workers=9) as ex:
    futs = {ex.submit(test_endpoint, u): u for u in endpoints}
    for f in concurrent.futures.as_completed(futs):
        url, status, info = f.result()
        print(f"{url} -> {status} : {info}", flush=True)
