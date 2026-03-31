"""
Ollama integration service for symptom analysis.
Sends symptom descriptions to the Qwen 3.5:2B model and parses structured responses.
"""

import json
import requests
from django.conf import settings


def analyze_symptoms(symptoms_text: str) -> dict:
    """
    Analyze symptoms using the Ollama LLM and return structured health predictions.

    Args:
        symptoms_text: Free-text description of symptoms from the user.

    Returns:
        A dict with keys: conditions, next_steps, severity, disclaimer, raw_response
    """
    prompt = _build_prompt(symptoms_text)

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": symptoms_text}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
            timeout=1200,
        )
        response.raise_for_status()
        result = response.json()
        raw_text = result.get("message", {}).get("content", "")
        print("Raw response from the model:")
        print(raw_text)
        parsed = _parse_response(raw_text)
        parsed["raw_response"] = raw_text
        return parsed

    except requests.ConnectionError:
        return {
            "error": True,
            "message": "Cannot connect to Ollama. Please make sure Ollama is running on localhost:11434.",
            "conditions": [],
            "next_steps": [],
            "severity": "unknown",
            "disclaimer": _get_disclaimer(),
        }
    except requests.Timeout:
        return {
            "error": True,
            "message": "The request to Ollama timed out. The model may be loading. Please try again.",
            "conditions": [],
            "next_steps": [],
            "severity": "unknown",
            "disclaimer": _get_disclaimer(),
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"An unexpected error occurred: {str(e)}",
            "conditions": [],
            "next_steps": [],
            "severity": "unknown",
            "disclaimer": _get_disclaimer(),
        }


def _build_prompt(symptoms_text: str) -> str:
    """Build the LLM system prompt for symptom analysis."""
    return """You are a medical analysis assistant. 
Analyze the user's symptoms and provide:

1. A list of probable health conditions (up to 5), each with:
   - Name of the condition
   - Likelihood (High, Medium, or Low)
   - A brief description of why this condition matches

2. A severity assessment (Low, Medium, or High) based on urgency

3. Recommended next steps (up to 5 actionable items)

IMPORTANT: You MUST respond ONLY with valid JSON in exactly this format, no other text:
{
    "conditions": [
        {
            "name": "Condition Name",
            "likelihood": "High|Medium|Low",
            "description": "Brief explanation"
        }
    ],
    "severity": "Low|Medium|High",
    "next_steps": [
        "Step 1 description",
        "Step 2 description"
    ]
}"""


def _parse_response(raw_text: str) -> dict:
    """Parse the LLM response text into structured data."""
    # Try to extract JSON from the response
    text = raw_text.strip()

    # If the text has markdown blocks anywhere, extract inside them
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Try to find JSON object in the text
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1

    if start_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx]
        try:
            data = json.loads(json_str)
            
            # Extract conditions (handling various formats the model might invent)
            conditions = data.get("conditions", [])
            if not conditions and "analysis" in data and isinstance(data["analysis"], dict):
                likely = data["analysis"].get("likely_conditions", [])
                if isinstance(likely, list):
                    for item in likely:
                        if isinstance(item, str):
                            conditions.append({"name": item, "likelihood": "Medium", "description": "Predicted by AI"})
                        elif isinstance(item, dict):
                            conditions.append(item)
            
            if not conditions and isinstance(data, dict):
                # if there is literally anything else but no conditions, just wrap it
                for k, v in data.items():
                    if "condition" in k.lower():
                        if isinstance(v, list) and v:
                            if isinstance(v[0], str):
                                conditions = [{"name": c, "likelihood": "Unknown", "description": ""} for c in v]
            
            return {
                "conditions": conditions,
                "next_steps": data.get("next_steps", data.get("recommendations", [])),
                "severity": data.get("severity", data.get("assessment_risk", "Unknown")),
                "disclaimer": _get_disclaimer(),
                "error": False,
            }
        except json.JSONDecodeError:
            pass

    # Fallback: return the raw text as a single condition
    return {
        "conditions": [
            {
                "name": "Analysis Result",
                "likelihood": "N/A",
                "description": raw_text[:500] if raw_text else "No response received.",
            }
        ],
        "next_steps": [
            "Consult a healthcare professional for proper diagnosis.",
            "Provide more specific symptoms for a better analysis.",
        ],
        "severity": "Unknown",
        "disclaimer": _get_disclaimer(),
        "error": False,
    }


def _get_disclaimer() -> str:
    return (
        "This analysis is generated by an AI model for informational purposes only. "
        "It is NOT a medical diagnosis. Always consult a qualified healthcare professional "
        "for proper medical advice, diagnosis, and treatment."
    )
