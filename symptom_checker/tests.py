from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from django.urls import reverse
import json
from symptom_checker.services import analyze_symptoms, _parse_response

class SymptomCheckerServicesTests(TestCase):
    
    @patch('requests.post')
    def test_analyze_symptoms_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "content": '{"conditions": [{"name": "Common Cold", "likelihood": "High", "description": "Matches symptoms"}], "severity": "Low", "next_steps": ["Rest", "Drink fluids"]}'
            }
        }
        mock_post.return_value = mock_response

        # Call service
        result = analyze_symptoms("I have a runny nose and cough.")

        # Assertions
        self.assertFalse(result.get("error"))
        self.assertEqual(result.get("severity"), "Low")
        self.assertEqual(len(result.get("conditions")), 1)
        self.assertEqual(result["conditions"][0]["name"], "Common Cold")
        self.assertEqual(len(result.get("next_steps")), 2)

    @patch('requests.post')
    def test_analyze_symptoms_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError()

        result = analyze_symptoms("test")
        self.assertTrue(result.get("error"))
        self.assertEqual(result.get("severity"), "unknown")
        self.assertIn("Cannot connect to Ollama", result.get("message"))

    def test_parse_response_with_markdown(self):
        raw_text = "```json\n{\"conditions\": [], \"severity\": \"Low\", \"next_steps\": []}\n```"
        parsed = _parse_response(raw_text)
        self.assertFalse(parsed.get("error"))

    def test_parse_response_invalid_json_fallback(self):
        raw_text = "I think you have a mild cold. Rest is recommended."
        parsed = _parse_response(raw_text)
        self.assertEqual(parsed.get("severity"), "Unknown")
        self.assertEqual(len(parsed.get("conditions")), 1)
        self.assertEqual(parsed["conditions"][0]["name"], "Analysis Result")

class SymptomCheckerViewsTests(TestCase):
    
    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        response = self.client.get(reverse('symptom_checker:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'symptom_checker/index.html')

    @patch('symptom_checker.views.analyze_symptoms')
    def test_analyze_view_success(self, mock_analyze):
        mock_analyze.return_value = {
            "conditions": [], "severity": "Low", "next_steps": [], "error": False
        }
        
        response = self.client.post(
            reverse('symptom_checker:analyze'),
            data=json.dumps({"symptoms": "I have been feeling very tired and have a mild headache."}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get("severity"), "Low")

    def test_analyze_view_missing_symptoms(self):
        response = self.client.post(
            reverse('symptom_checker:analyze'),
            data=json.dumps({"symptoms": ""}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue(data.get("error"))
        self.assertIn("Please provide", data.get("message"))

    def test_analyze_view_short_symptoms(self):
        response = self.client.post(
            reverse('symptom_checker:analyze'),
            data=json.dumps({"symptoms": "short"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertTrue(data.get("error"))
        self.assertIn("more detailed description", data.get("message"))
