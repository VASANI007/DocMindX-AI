"""
    DocMindX AI - UI, Translations & Components Test Suite
"""
import unittest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.language import load_translations, get_text
from config.constants import SUPPORTED_LANGUAGES, AGE_GROUPS

class TestUI(unittest.TestCase):
    
    def test_translations_loaded(self):
        t_en = load_translations("en")
        t_hi = load_translations("hi")
        t_gu = load_translations("gu")
        self.assertIsNotNone(t_en)
        self.assertIsNotNone(t_hi)
        self.assertIsNotNone(t_gu)

    def test_get_text_fallback(self):
        t_en = load_translations("en")
        val = get_text(t_en, "non_existent_key", "Default Fallback")
        self.assertEqual(val, "Default Fallback")

    def test_constants_definitions(self):
        self.assertIn("en", SUPPORTED_LANGUAGES)
        self.assertIn("hi", SUPPORTED_LANGUAGES)
        self.assertIn("gu", SUPPORTED_LANGUAGES)
        self.assertGreater(len(AGE_GROUPS), 0)

if __name__ == "__main__":
    unittest.main()
