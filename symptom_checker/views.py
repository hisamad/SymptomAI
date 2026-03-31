"""
Views for the symptom checker application.
Handles both the frontend page rendering and the API endpoint.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import analyze_symptoms


def index(request):
    """Render the main symptom checker page."""
    return render(request, 'symptom_checker/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """
    API endpoint: Accept symptoms text and return AI-powered analysis.

    POST /api/analyze/
    Body: {"symptoms": "description of symptoms"}
    Returns: JSON with conditions, next_steps, severity, disclaimer
    """
    try:
        body = json.loads(request.body)
        symptoms = body.get('symptoms', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse(
            {'error': True, 'message': 'Invalid request body. Send JSON with a "symptoms" field.'},
            status=400,
        )

    if not symptoms:
        return JsonResponse(
            {'error': True, 'message': 'Please provide a description of your symptoms.'},
            status=400,
        )

    if len(symptoms) < 10:
        return JsonResponse(
            {'error': True, 'message': 'Please provide a more detailed description (at least 10 characters).'},
            status=400,
        )

    result = analyze_symptoms(symptoms)

    if result.get('error'):
        return JsonResponse(result, status=503)

    return JsonResponse(result)
