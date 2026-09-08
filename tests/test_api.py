"""
    DocMindX AI - API Test Suite
"""
import unittest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.openfda import search_drug_openfda
from api.dailymed import search_dailymed_spls
from api.nlm_clinical import search_nlm_conditions
from api.who_icd import search_who_icd11
from api.geolocation import detect_auto_location

class TestAPIs(unittest.TestCase):
    
    def test_openfda_fallback(self):
        res = search_drug_openfda("Paracetamol")
        self.assertIsNotNone(res)
        self.assertIn("medicine_name", res)

    def test_dailymed_search(self):
        res = search_dailymed_spls("Paracetamol", page_size=1)
        self.assertIsInstance(res, list)

    def test_nlm_clinical_conditions(self):
        res = search_nlm_conditions("Asthma")
        self.assertIsInstance(res, list)

    def test_who_icd(self):
        res = search_who_icd11("Fever")
        self.assertIsInstance(res, list)

    def test_geolocation(self):
        res = detect_auto_location()
        self.assertIn("lat", res)
        self.assertIn("lon", res)

if __name__ == "__main__":
    unittest.main()
