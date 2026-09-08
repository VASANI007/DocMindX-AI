"""
    DocMindX AI - Comprehensive 9-Service Health Check & Live Audit
Tests each of the 9 services live and produces a verification scorecard.
"""
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.openfda import search_drug_openfda
from api.dailymed import search_dailymed_spls
from api.who_icd import search_who_icd11
from api.nlm_clinical import search_nlm_conditions
from api.medlineplus import get_medlineplus_genetics_data
from api.nominatim import geocode_city_district
from api.overpass import query_nearby_healthcare
from api.maps import render_healthcare_map
from ai.ocr.text_extractor import extract_text_from_file

def run_audit():
    print("=" * 80)
    print("DocMindX AI -- 9 SERVICES LIVE AUDIT & STATUS REPORT")
    print("=" * 80)

    scorecard = []

    # 1. OpenFDA
    t0 = time.time()
    try:
        res1 = search_drug_openfda("Ibuprofen")
        dt1 = round(time.time() - t0, 2)
        if res1 and res1.get("medicine_name"):
            scorecard.append((1, "OpenFDA", "Active / Working", f"Found '{res1['medicine_name']}' ({res1['source']})", f"{dt1}s", "PASS"))
        else:
            scorecard.append((1, "OpenFDA", "Error", "No data returned", f"{dt1}s", "FAIL"))
    except Exception as e:
        scorecard.append((1, "OpenFDA", "Error", str(e)[:40], "N/A", "FAIL"))

    # 2. DailyMed
    t0 = time.time()
    try:
        res2 = search_dailymed_spls("Paracetamol", page_size=2)
        dt2 = round(time.time() - t0, 2)
        if res2 and len(res2) > 0:
            scorecard.append((2, "DailyMed (NIH)", "Active / Working", f"Found {len(res2)} SPLs (SETID: {res2[0]['setid'][:8]}...)", f"{dt2}s", "PASS"))
        else:
            scorecard.append((2, "DailyMed (NIH)", "Error", "No SPL found", f"{dt2}s", "FAIL"))
    except Exception as e:
        scorecard.append((2, "DailyMed (NIH)", "Error", str(e)[:40], "N/A", "FAIL"))

    # 3. WHO ICD-11
    t0 = time.time()
    try:
        res3 = search_who_icd11("Malaria")
        dt3 = round(time.time() - t0, 2)
        if res3 and len(res3) > 0:
            scorecard.append((3, "WHO ICD-11", "Active / Working", f"Authenticated! Found: '{res3[0]['title']}' (Ch: {res3[0]['chapter']})", f"{dt3}s", "PASS"))
        else:
            scorecard.append((3, "WHO ICD-11", "Error", "Authentication or search failed", f"{dt3}s", "FAIL"))
    except Exception as e:
        scorecard.append((3, "WHO ICD-11", "Error", str(e)[:40], "N/A", "FAIL"))

    # 4. NLM Clinical Tables
    t0 = time.time()
    try:
        res4 = search_nlm_conditions("Diabetes", max_list=3)
        dt4 = round(time.time() - t0, 2)
        if res4 and len(res4) > 0:
            scorecard.append((4, "NLM Clinical Tables", "Active / Working", f"Autocomplete returned: {res4[:2]}", f"{dt4}s", "PASS"))
        else:
            scorecard.append((4, "NLM Clinical Tables", "Error", "No conditions returned", f"{dt4}s", "FAIL"))
    except Exception as e:
        scorecard.append((4, "NLM Clinical Tables", "Error", str(e)[:40], "N/A", "FAIL"))

    # 5. MedlinePlus Genetics
    t0 = time.time()
    try:
        res5 = get_medlineplus_genetics_data("Alzheimer disease")
        dt5 = round(time.time() - t0, 2)
        if res5 and res5.get("disease_name"):
            scorecard.append((5, "MedlinePlus Genetics", "Active / Working", f"Genes: {res5['related_genes'][:3]} | Synonyms: {len(res5['synonyms'])}", f"{dt5}s", "PASS"))
        else:
            scorecard.append((5, "MedlinePlus Genetics", "Error", "No genetics data found", f"{dt5}s", "FAIL"))
    except Exception as e:
        scorecard.append((5, "MedlinePlus Genetics", "Error", str(e)[:40], "N/A", "FAIL"))

    # 6. OpenStreetMap
    t0 = time.time()
    try:
        m = render_healthcare_map(23.0225, 72.5714, [{"name": "Test Hospital", "type": "Hospital", "distance_km": 1.2, "lat": 23.03, "lon": 72.58, "address": "City Center"}])
        dt6 = round(time.time() - t0, 2)
        if m and m._repr_html_():
            scorecard.append((6, "OpenStreetMap / Folium", "Active / Working", "Interactive Leaflet HTML map compiled", f"{dt6}s", "PASS"))
        else:
            scorecard.append((6, "OpenStreetMap / Folium", "Error", "Map render failed", f"{dt6}s", "FAIL"))
    except Exception as e:
        scorecard.append((6, "OpenStreetMap / Folium", "Error", str(e)[:40], "N/A", "FAIL"))

    # 7. Nominatim
    t0 = time.time()
    try:
        lat, lon, name = geocode_city_district("Ahmedabad")
        dt7 = round(time.time() - t0, 2)
        if lat and lon:
            scorecard.append((7, "Nominatim Geocoding", "Active / Working", f"Resolved coords: ({lat:.4f}, {lon:.4f})", f"{dt7}s", "PASS"))
        else:
            scorecard.append((7, "Nominatim Geocoding", "Error", "Geocoding failed", f"{dt7}s", "FAIL"))
    except Exception as e:
        scorecard.append((7, "Nominatim Geocoding", "Error", str(e)[:40], "N/A", "FAIL"))

    # 8. Overpass API
    t0 = time.time()
    try:
        facs = query_nearby_healthcare(23.0225, 72.5714, facility_type="hospital")
        dt8 = round(time.time() - t0, 2)
        if facs and len(facs) > 0:
            scorecard.append((8, "Overpass Healthcare API", "Active / Working", f"Found {len(facs)} facilities ({facs[0]['name']}, {facs[0]['distance_km']} km)", f"{dt8}s", "PASS"))
        else:
            scorecard.append((8, "Overpass Healthcare API", "Error", "No facilities found", f"{dt8}s", "FAIL"))
    except Exception as e:
        scorecard.append((8, "Overpass Healthcare API", "Error", str(e)[:40], "N/A", "FAIL"))

    # 9. Local Python / OCR Layer
    t0 = time.time()
    try:
        class DummyFile:
            name = "test_report.png"
        def read(self):
                return b"Test"
        text = extract_text_from_file(DummyFile())
        dt9 = round(time.time() - t0, 2)
        if text and len(text) > 0:
            scorecard.append((9, "Local OCR / Parsing", "Active / Working", f"Extracted {len(text)} chars without exceptions", f"{dt9}s", "PASS"))
        else:
            scorecard.append((9, "Local OCR / Parsing", "Error", "Extraction failed", f"{dt9}s", "FAIL"))
    except Exception as e:
        scorecard.append((9, "Local OCR / Parsing", "Error", str(e)[:40], "N/A", "FAIL"))

    # 10. Yoga API (REST Categories & Asanas)
    t0 = time.time()
    try:
        from api.yoga_api import search_yoga_pose
        p = search_yoga_pose("Butterfly")
        dt10 = round(time.time() - t0, 2)
        if p and p.get("url_png"):
            scorecard.append((10, "Yoga API (HappyYoga)", "Active / Working", f"Found '{p['english_name']}' ({p['sanskrit_name']})", f"{dt10}s", "PASS"))
        else:
            scorecard.append((10, "Yoga API (HappyYoga)", "Error", "Pose lookup failed", f"{dt10}s", "FAIL"))
    except Exception as e:
        scorecard.append((10, "Yoga API (HappyYoga)", "Error", str(e)[:40], "N/A", "FAIL"))

    # Print Table
    print("\n" + "="*80)
    print("DocMindX AI -- 10 SERVICES LIVE AUDIT & STATUS REPORT")
    print("="*80)
    print(f"{'#':<3} {'Service Name':<25} {'Status':<18} {'Latency':<8} {'Audit Result & Details'}")
    print("-" * 70)
    
    passed_count = 0
    for num, name, status, details, latency, result in scorecard:
        if result == "PASS":
            passed_count += 1
        print(f"{num:<3} {name:<25} {status:<18} {latency:<8} [{result}] {details}")

    print("="*80)
    print(f"FINAL AUDIT SCORE: {passed_count}/{len(scorecard)} SERVICES FULLY ACTIVE & WORKING ({int(passed_count/len(scorecard)*100)}% OPERATIONAL)")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_audit()
