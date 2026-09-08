import traceback
from api.overpass import query_nominatim_facilities

try:
    res = query_nominatim_facilities(23.0225, 72.5714, "hospital", radius_meters=5000)
    print("Nominatim returned:", len(res))
    if res:
        print("First 3:", [r["name"] for r in res[:3]])
except Exception as e:
    print("Exception in query_nominatim_facilities:")
    traceback.print_exc()
