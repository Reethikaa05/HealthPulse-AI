import requests
import json
import os

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

def predict_health(glucose, haemoglobin, cholesterol):
    """
    Uses Claude AI to predict health conditions based on blood test results.
    Falls back to rule-based prediction if API is unavailable.
    """
    try:
        if ANTHROPIC_API_KEY:
            return _predict_with_claude(glucose, haemoglobin, cholesterol)
        else:
            return _rule_based_prediction(glucose, haemoglobin, cholesterol)
    except Exception as e:
        print(f"AI prediction error: {e}")
        return _rule_based_prediction(glucose, haemoglobin, cholesterol)


def _predict_with_claude(glucose, haemoglobin, cholesterol):
    prompt = f"""You are a medical AI assistant. Analyze these blood test results and provide a health assessment.

Patient Blood Test Results:
- Glucose: {glucose} mg/dL (Normal: 70-100 mg/dL fasting)
- Haemoglobin: {haemoglobin} g/dL (Normal: Men 13.5-17.5, Women 12.0-15.5 g/dL)
- Cholesterol: {cholesterol} mg/dL (Desirable: <200 mg/dL)

Respond ONLY with a JSON object (no markdown, no extra text):
{{
  "risk_level": "Low|Moderate|High|Critical",
  "risk_score": <number 0-100>,
  "conditions": ["list of possible conditions"],
  "remarks": "2-3 sentence professional medical summary with specific findings and recommendations"
}}"""

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 300,
            'messages': [{'role': 'user', 'content': prompt}]
        },
        timeout=15
    )

    if response.status_code == 200:
        data = response.json()
        text = data['content'][0]['text'].strip()
        # Clean up JSON if wrapped in markdown
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        result = json.loads(text)
        return {
            'risk_level': result.get('risk_level', 'Unknown'),
            'risk_score': float(result.get('risk_score', 50)),
            'remarks': result.get('remarks', 'Analysis complete. Consult your physician.')
        }

    return _rule_based_prediction(glucose, haemoglobin, cholesterol)


def _rule_based_prediction(glucose, haemoglobin, cholesterol):
    """Intelligent rule-based health prediction as fallback."""
    issues = []
    risk_points = 0

    # Glucose analysis
    if glucose < 70:
        issues.append("hypoglycemia (low blood sugar)")
        risk_points += 30
    elif 70 <= glucose <= 99:
        pass  # Normal
    elif 100 <= glucose <= 125:
        issues.append("pre-diabetes risk (impaired fasting glucose)")
        risk_points += 25
    elif 126 <= glucose <= 200:
        issues.append("diabetes mellitus Type 2 (elevated fasting glucose)")
        risk_points += 45
    else:
        issues.append("severe hyperglycemia requiring immediate attention")
        risk_points += 70

    # Haemoglobin analysis
    if haemoglobin < 8:
        issues.append("severe anemia")
        risk_points += 50
    elif 8 <= haemoglobin < 12:
        issues.append("moderate anemia")
        risk_points += 30
    elif 12 <= haemoglobin <= 17.5:
        pass  # Normal range
    else:
        issues.append("polycythemia (elevated haemoglobin)")
        risk_points += 25

    # Cholesterol analysis
    if cholesterol < 200:
        pass  # Desirable
    elif 200 <= cholesterol <= 239:
        issues.append("borderline high cholesterol")
        risk_points += 20
    elif 240 <= cholesterol <= 300:
        issues.append("high cholesterol (hypercholesterolemia)")
        risk_points += 40
    else:
        issues.append("very high cholesterol with elevated cardiovascular risk")
        risk_points += 60

    # Determine risk level
    risk_score = min(risk_points, 100)
    if risk_score == 0:
        risk_level = 'Low'
    elif risk_score <= 30:
        risk_level = 'Low'
    elif risk_score <= 55:
        risk_level = 'Moderate'
    elif risk_score <= 75:
        risk_level = 'High'
    else:
        risk_level = 'Critical'

    # Generate remarks
    if not issues:
        remarks = (
            f"All blood parameters are within normal ranges — glucose {glucose} mg/dL, "
            f"haemoglobin {haemoglobin} g/dL, and cholesterol {cholesterol} mg/dL. "
            "The patient appears to be in good metabolic health. Routine annual screening is recommended."
        )
    else:
        condition_str = ", ".join(issues)
        remarks = (
            f"Analysis indicates {condition_str}. "
            f"Key values: glucose {glucose} mg/dL, haemoglobin {haemoglobin} g/dL, cholesterol {cholesterol} mg/dL. "
            f"Risk score: {risk_score}/100 ({risk_level}). Prompt consultation with a physician is strongly advised for further evaluation and management."
        )

    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'remarks': remarks
    }
