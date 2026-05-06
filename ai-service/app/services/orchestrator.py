from .medgemma_service import MedGemmaService
from .parser_service import (
    build_non_json_medgemma_response,
    build_stub_response,
    extract_json,
    normalize_medical_response,
)
from .prompt_service import build_prompt


class MedicalOrchestrator:
    def __init__(self):
        self.med = MedGemmaService()

    def run(self, symptoms: str):
        clean_symptoms = (symptoms or "").strip()

        if not clean_symptoms:
            return build_stub_response(
                "Không có triệu chứng được nhập.",
                "empty_symptoms",
            )

        prompt = build_prompt(clean_symptoms)
        raw = self.med.generate(prompt)

        # MedGemma disabled/load failed/call failed.
        if "error" in raw:
            return build_stub_response(
                clean_symptoms,
                raw.get("status", "ai_service_stub_fallback"),
            )

        text = raw.get("text", "")
        parsed = extract_json(text)

        # MedGemma returned valid JSON.
        if parsed:
            result = normalize_medical_response(
                parsed,
                raw.get("status", "real_medgemma_response"),
            )
            result["model_status"] = "medgemma_real_json"
            return result

        # MedGemma ran but returned non-JSON/thought.
        # Do NOT call repair_json here because it is too slow for web requests
        # and causes backend/frontend timeout on Colab T4.
        return build_non_json_medgemma_response(
            clean_symptoms,
            text,
        )
