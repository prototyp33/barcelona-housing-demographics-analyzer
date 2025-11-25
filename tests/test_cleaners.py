"""
Unit tests for the HousingCleaner class in src/transform/cleaners.py.
"""

import json
import unittest
import pandas as pd
import pytest
from src.transform.cleaners import HousingCleaner

class TestHousingCleaner(unittest.TestCase):
    def setUp(self):
        """Set up the HousingCleaner instance for tests."""
        self.cleaner = HousingCleaner()

    def test_fix_mojibake(self):
        """Test that common encoding issues are fixed."""
        # Example: "Gòtic" encoded as latin-1 then decoded as utf-8 often results in something like "GÃ²tic"
        # Note: To create the mojibake string in Python source code without encoding issues can be tricky.
        # "Gòtic".encode('utf-8').decode('latin-1') -> "GÃ²tic"
        
        original = "Gòtic"
        mojibake = original.encode('utf-8').decode('latin-1')
        
        fixed = self.cleaner._fix_mojibake(mojibake)
        self.assertEqual(fixed, original)
        
        # Test that correct strings are left unchanged
        self.assertEqual(self.cleaner._fix_mojibake(original), original)
        
        # Test non-string input
        self.assertEqual(self.cleaner._fix_mojibake(123), 123)
        self.assertIsNone(self.cleaner._fix_mojibake(None))

    def test_normalize_neighborhoods(self):
        """Test neighborhood name normalization and standardization."""
        test_cases = [
            # Basic normalization
            ("El Raval", "elraval"),
            ("  Sant Andreu  ", "santandreu"),
            ("Sants-Montjuïc", "santsmontjuic"),
            
            # Removing patterns
            ("1. el Raval", "elraval"),
            ("01. el Raval", "elraval"),
            ("el Raval (1)", "elraval"),
            ("Barri Gòtic - AEI", "barrigotic"),
            
            # Overrides/Aliases
            ("Antiga Esquerra Eixample", "lantigaesquerradeleixample"),
            ("Trinitat Nova", "latrinitatnova"),
            
            # Handling None/Empty
            (None, ""),
            ("", ""),
        ]

        for raw, expected in test_cases:
            with self.subTest(raw=raw):
                result = self.cleaner.normalize_neighborhoods(raw)
                self.assertEqual(result, expected)

    def test_process_geometry_valid_json_string(self):
        """Test parsing of valid GeoJSON strings."""
        valid_geojson = '{"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 0]]]}'
        result = self.cleaner.process_geometry(valid_geojson)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], "Polygon")
        self.assertIn('coordinates', result)

    def test_process_geometry_valid_dict(self):
        """Test validation of valid geometry dictionaries."""
        valid_dict = {"type": "Point", "coordinates": [0, 0]}
        result = self.cleaner.process_geometry(valid_dict)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], "Point")

    def test_process_geometry_invalid_inputs(self):
        """Test handling of invalid inputs."""
        invalid_cases = [
            # Malformed JSON
            '{"type": "Polygon", "coordinates": [', 
            # Missing required fields
            '{"type": "Polygon"}', 
            '{"coordinates": []}',
            # Wrong types
            123,
            None,
            pd.NA
        ]

        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                result = self.cleaner.process_geometry(invalid)
                self.assertIsNone(result)

    def test_clean_data_orchestration(self):
        """Test the full clean_data pipeline on a DataFrame."""
        data = {
            'barrio_nombre': ['1. El Raval', 'GÃ²tic'],
            'geometry_json': [
                '{"type": "Point", "coordinates": [0, 0]}',
                'invalid json'
            ],
            'barrio_id': [1, 2]
        }
        df = pd.DataFrame(data)
        
        cleaned_df = self.cleaner.clean_data(df)
        
        # Check normalization
        self.assertIn('barrio_nombre_normalized', cleaned_df.columns)
        self.assertEqual(cleaned_df.iloc[0]['barrio_nombre_normalized'], 'elraval')
        
        # Check mojibake fix
        # GÃ²tic -> Gòtic -> gotic
        self.assertEqual(cleaned_df.iloc[1]['barrio_nombre_normalized'], 'gotic')
        
        # Check geometry processing
        self.assertIn('geometry_obj', cleaned_df.columns)
        self.assertIsInstance(cleaned_df.iloc[0]['geometry_obj'], dict)
        self.assertIsNone(cleaned_df.iloc[1]['geometry_obj'])

if __name__ == '__main__':
    unittest.main()

