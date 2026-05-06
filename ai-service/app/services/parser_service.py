import json
import re


DISCLAIMER = (
    "This assistant is for educational triage support only and does not replace "
    "a licensed clinician. Seek urgent care for severe or worsening symptoms."
)


DEFAULT_RESPONSE = {
    "summary": "",
    "possible_related_systems": [],
    "possible_explanations": [],
    "red_flags": [],
    "missing_questions": [],
    "recommendation": "",
    "severity": "unknown",
    "model_status": "unknown",
    "disclaimer": DISCLAIMER,
}


def extract_json(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        return json.loads(match.group())
    except Exception:
        return None


def normalize_medical_response(data, model_status="unknown"):
    normalized = DEFAULT_RESPONSE.copy()

    if isinstance(data, dict):
        for key in normalized:
            if key in data:
                normalized[key] = data[key]

    for key in [
        "possible_related_systems",
        "possible_explanations",
        "red_flags",
        "missing_questions",
    ]:
        if not isinstance(normalized[key], list):
            normalized[key] = []

    normalized["model_status"] = normalized.get("model_status") or model_status
    normalized["disclaimer"] = normalized.get("disclaimer") or DISCLAIMER

    return normalized


def build_stub_response(symptoms, model_status="stub_response_no_medgemma_called"):
    return {
        "summary": f"You reported: {symptoms}",
        "possible_related_systems": ["general", "respiratory", "gastrointestinal"],
        "possible_explanations": [
            "A mild self-limited illness can cause overlapping symptoms.",
            "Infection, inflammation, stress, dehydration, or medication effects may contribute.",
        ],
        "red_flags": [
            "Chest pain, severe shortness of breath, fainting, confusion, blue lips, or severe weakness.",
            "High fever that persists, severe dehydration, severe abdominal pain, or symptoms that rapidly worsen.",
        ],
        "missing_questions": [
            "How long have the symptoms been present?",
            "What is your age and do you have pregnancy, chronic disease, or immune suppression?",
            "Do you have fever, pain severity, breathing trouble, vomiting, bleeding, or new medications?",
        ],
        "recommendation": (
            "Monitor symptoms, rest, hydrate if appropriate, and contact a healthcare professional "
            "if symptoms persist, worsen, or concern you. Seek emergency care immediately for any red flags."
        ),
        "severity": "low_to_moderate",
        "model_status": model_status,
        "disclaimer": DISCLAIMER,
    }
