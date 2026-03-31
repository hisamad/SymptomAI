import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from symptom_checker.services import analyze_symptoms, _parse_response

start_time = time.time()
result = analyze_symptoms("I have sore throat and cough for the past 2 days")
end_time = time.time()
print(result)
print(f"Time taken: {end_time - start_time} seconds")