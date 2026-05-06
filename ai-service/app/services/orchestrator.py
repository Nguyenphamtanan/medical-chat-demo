from .medgemma_service import MedGemmaService
from .parser_service import (
    build_non_json_medgemma_response,
    build_stub_response,
    extract_json,
    normalize_medical_response,
)
from .prompt_service import build_json_repair_prompt, build_prompt


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

        # TẦNG 1 - lần 1: gọi MedGemma thật
        prompt = build_prompt(clean_symptoms)
        raw = self.med.generate(prompt)

        if "error" in raw:
            return build_stub_response(
                clean_symptoms,
                raw.get("status", "ai_service_stub_fallback"),
            )

        text = raw.get("text", "")
        parsed = extract_json(text)

        if parsed:
            result = normalize_medical_response(
                parsed,
                raw.get("status", "real_medgemma_response"),
            )
            result["model_status"] = "medgemma_real_json"
            return result

        # TẦNG 1 - lần 2: vẫn dùng MedGemma, nhưng yêu cầu convert raw output thành JSON
        repair_prompt = build_json_repair_prompt(clean_symptoms, text)
        repaired_raw = self.med.repair_json(repair_prompt)

        if "error" not in repaired_raw:
            repaired_text = repaired_raw.get("text", "")
            repaired_parsed = extract_json(repaired_text)

            if repaired_parsed:
                result = normalize_medical_response(
                    repaired_parsed,
                    repaired_raw.get("status", "real_medgemma_repair_response"),
                )
                result["model_status"] = "medgemma_real_repaired_json"
                return result

        # TẦNG 2 - backup thật sự
        return build_non_json_medgemma_response(
            clean_symptoms,
            text,
        )