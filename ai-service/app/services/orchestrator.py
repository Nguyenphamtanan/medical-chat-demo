from .medgemma_service import MedGemmaService
from .parser_service import build_stub_response, extract_json, normalize_medical_response
from .prompt_service import build_prompt


class MedicalOrchestrator:
    def __init__(self):
        self.med = MedGemmaService()

    def run(self, symptoms: str):
        clean_symptoms = symptoms.strip()
        prompt = build_prompt(clean_symptoms)
        raw = self.med.generate(prompt)

        if "error" in raw:
            return build_stub_response(clean_symptoms, raw.get("status", "ai_service_stub_fallback"))

        text = raw.get("text", "")
        parsed = extract_json(text)

        if not parsed:
            return build_stub_response(clean_symptoms, "medgemma_json_parse_failed")

        return normalize_medical_response(
            parsed,
            raw.get("status", "real_medgemma_response"),
        )
