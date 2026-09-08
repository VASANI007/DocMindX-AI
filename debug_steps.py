import traceback
from api.overpass import query_photon_healthcare, query_nearby_healthcare

print("Testing query_photon_healthcare directly...")
try:
    p_res = query_photon_healthcare(23.0225, 72.5714, "hospital", 5000)
    print("query_photon_healthcare returned:", len(p_res))
except Exception as e:
    print("Error in query_photon_healthcare:")
    traceback.print_exc()

print("Testing query_nearby_healthcare directly...")
try:
    all_res = query_nearby_healthcare(23.0225, 72.5714, "hospital", 5000)
    print("query_nearby_healthcare returned:", len(all_res))
except Exception as e:
    print("Error in query_nearby_healthcare:")
    traceback.print_exc()
