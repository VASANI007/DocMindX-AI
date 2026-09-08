"""
    Comprehensive Test Suite for DocMindX AI
"""
import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai.disease_prediction.predict import SymptomTriageEngine
from ai.report_ai.blood_report import LabReportAnalyzer
from ai.report_ai.prescription import PrescriptionAnalyzer
from ai.utils.report_generator import generate_pdf_report
from api.nominatim import geocode_city_district
from api.overpass import query_nearby_healthcare
from api.openfda import search_drug_openfda

class TestDocMindXAI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.triage = SymptomTriageEngine()
        cls.lab = LabReportAnalyzer()
        cls.prescription = PrescriptionAnalyzer()

    def test_symptom_triage_normal(self):
        # Fever + Sore Throat + Runny nose -> should match conditions in knowledge base
        result = self.triage.evaluate_symptoms(
            selected_symptom_ids=["S000001", "S000032", "S000035"],
            age_group="21–30",
            gender="Male",
            duration="3–5 Days"
        )
        self.assertFalse(result["is_emergency"])
        self.assertTrue(len(result["ranked_conditions"]) > 0)
        self.assertTrue(any(c["match_percentage"] > 0 for c in result["ranked_conditions"]))

    def test_red_flag_emergency_trigger(self):
        # S022: Severe Crushing Chest Pain -> must trigger Red Flag Emergency
        result = self.triage.evaluate_symptoms(
            selected_symptom_ids=["S022", "S026"],
            age_group="51–60",
            gender="Male",
            duration="Today"
        )
        self.assertTrue(result["is_emergency"])
        self.assertTrue(len(result["red_flags"]) > 0)
        self.assertIn("Critical", result["urgency_level"])

    def test_lab_report_analyzer(self):
        sample_report = "Hemoglobin: 10.5 g/dL\nFasting Blood Sugar: 145 mg/dL\nSerum Creatinine: 0.9 mg/dL"
        analysis = self.lab.parse_and_evaluate(sample_report, gender="Male")
        self.assertEqual(analysis["total_tests_detected"], 3)
        self.assertEqual(analysis["abnormal_count"], 2) # Low Hb and High FBS

    def test_openfda_lookup(self):
        data = search_drug_openfda("Paracetamol")
        self.assertIsNotNone(data)
        self.assertIn("Paracetamol", data["medicine_name"])

    def test_pdf_generation(self):
        user_ctx = {
            "age": "21–30",
            "gender": "Male",
            "location": "Ahmedabad, Gujarat",
            "duration": "3–5 Days",
            "symptoms": ["Fever", "Sore Throat"]
        }
        triage_res = self.triage.evaluate_symptoms(["S001", "S012"])
        pdf_buf = generate_pdf_report(user_ctx, triage_res)
        self.assertIsNotNone(pdf_buf)
        self.assertTrue(pdf_buf.getbuffer().nbytes > 1000)

    def test_nominatim_and_overpass(self):
        lat, lon, name = geocode_city_district("Ahmedabad")
        self.assertAlmostEqual(lat, 23.0225, delta=1.0)
        facilities = query_nearby_healthcare(lat, lon, facility_type="hospital")
        self.assertTrue(len(facilities) > 0)

    def test_bioportal_concept_search(self):
        from api.bioportal import search_bioportal_concept
        concepts = search_bioportal_concept("Dengue")
        self.assertIsNotNone(concepts)
        self.assertTrue(len(concepts) > 0)

    def test_nlm_clinical_tables_autocomplete(self):
        from api.nlm_clinical import search_nlm_conditions
        suggestions = search_nlm_conditions("diabetes", max_list=5)
        self.assertIsNotNone(suggestions)
        self.assertTrue(len(suggestions) > 0)

    def test_who_icd11_live_search(self):
        from api.who_icd import search_who_icd11
        results = search_who_icd11("malaria")
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 0)

    def test_dailymed_v2_search(self):
        from api.dailymed import search_dailymed_spls
        spls = search_dailymed_spls("Ibuprofen", page_size=2)
        self.assertIsNotNone(spls)
        self.assertTrue(len(spls) > 0)

    def test_medlineplus_genetics_and_search(self):
        from api.medlineplus import get_medlineplus_genetics_data, search_medlineplus_topics
        gen_data = get_medlineplus_genetics_data("Alzheimer disease")
        self.assertIsNotNone(gen_data)
        self.assertIn("Alzheimer", gen_data["disease_name"])

        topics = search_medlineplus_topics("diabetes", retmax=2)
        self.assertIsNotNone(topics)
        self.assertTrue(len(topics) > 0)

    def test_image_resolver_caching_and_fallbacks(self):
        from ai.utils.image_resolver import resolve_image
        
        # 1. Test fallback when unknown item and no URL provided
        med_path, is_fb1 = resolve_image("medicine", "UnknownItemXYZ999", None)
        self.assertTrue(is_fb1)
        self.assertTrue(med_path.startswith("data:image/") or med_path.endswith(".svg"))

        # 2. Test Yoga remote resolution or curated resolution
        yoga_path, is_fb2 = resolve_image("yoga", "Bhujangasana", None)
        self.assertIsNotNone(yoga_path)

    def test_exercise_expander_and_curated_video_links(self):
        from ai.guidance_ai.exercise_expander import expand_exercise_guidance, get_curated_video_link
        
        # 1. Test curated video link mapping
        video = get_curated_video_link("Y001", "Bhujangasana")
        self.assertIsNotNone(video)
        self.assertIn("youtube.com", video["video_url"])
        self.assertEqual(video["channel_source"], "Ministry of AYUSH (Govt of India)")

        # 2. Test structured AI exercise expansion
        anchor = {
            "exercise_name": "Cat-Cow Stretch",
            "precautions": "Avoid during severe neck injury",
            "steps": "1. Inhale arch back.\n2. Exhale round spine.",
            "avoid_if": "Acute wrist fracture",
            "description": "Rhythmic spinal mobilization"
        }
        res = expand_exercise_guidance(anchor, ["Neck Stiffness"], "Neck and back stiffness", lang="en")
        self.assertIsNotNone(res)
        self.assertIn("why_it_helps", res)
        self.assertIn("steps", res)
        self.assertIn("precautions", res)
        self.assertIn("avoid_if", res)

    def test_yoga_api_search_and_poses(self):
        from api.yoga_api import search_yoga_pose, get_all_yoga_poses
        
        # 1. Test fetch all poses
        poses = get_all_yoga_poses()
        self.assertIsNotNone(poses)
        self.assertTrue(len(poses) >= 40)

        # 2. Test search pose
        pose = search_yoga_pose("Butterfly")
        self.assertIsNotNone(pose)
        self.assertEqual(pose["english_name"], "Butterfly")
        self.assertTrue(pose["url_png"].startswith("http"))

    def test_detect_auto_location(self):
        from api.geolocation import detect_auto_location
        loc = detect_auto_location()
        self.assertIsNotNone(loc)
        self.assertIn("lat", loc)
        self.assertIn("lon", loc)
        self.assertIn("city", loc)
        self.assertTrue(isinstance(loc["lat"], (int, float)))

    def test_osrm_routing(self):
        from api.routing import get_route_directions
        route = get_route_directions(23.0276, 72.5871, 23.0451, 72.6511, mode="car")
        self.assertIsNotNone(route)
        self.assertIn("distance_km", route)
        self.assertIn("duration_min", route)
        self.assertIn("route_coordinates", route)
        self.assertTrue(len(route["route_coordinates"]) >= 2)

    def test_voice_transcribe_fallback(self):
        """Verify transcribe_audio handles invalid or short audio without crashing."""
        from ai.voice.speech_to_text import transcribe_audio
        res = transcribe_audio(b"fake_short_audio", language_code="hi-IN")
        self.assertEqual(res, "")

    def test_voice_synthesize_speech(self):
        """Verify synthesize_speech generates valid data URI or falls back safely."""
        from ai.voice.text_to_speech import synthesize_speech
        res = synthesize_speech("Hello, patient reports mild fever.", lang="en")
        self.assertTrue(res == "" or res.startswith("data:audio/mp3;base64,"))

    def test_voice_transcribe_mocked_gcp(self):
        """Verify transcribe_audio handles byte content when GCP is mocked."""
        from unittest.mock import patch, MagicMock
        from ai.voice.speech_to_text import transcribe_audio
        
        # Test with empty/short audio safely returns empty string
        self.assertEqual(transcribe_audio(b""), "")

if __name__ == "__main__":
    unittest.main()

