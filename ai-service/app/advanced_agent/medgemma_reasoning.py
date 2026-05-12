import json
from functools import lru_cache
from typing import Dict

from app.services.medgemma_service import MedGemmaService

from .models import AdvancedCaseRequest, case_to_text


@lru_cache(maxsize=1)
def get_medgemma_service() -> MedGemmaService:
    return MedGemmaService()


class MedGemmaReasoner:
    def __init__(self):
        self.medgemma = get_medgemma_service()

    def reason(self, case: AdvancedCaseRequest, route_result: Dict) -> Dict:
        prompt = self._build_prompt(case, route_result)
        raw = self.medgemma.generate(prompt)
        if "error" in raw:
            return {
                "status": raw.get("status", "medgemma_unavailable_fallback"),
                "reasoning": "",
                "structured": {},
            }

        text = raw.get("text", "").strip()
        return {
            "status": raw.get("status", "real_medgemma_response"),
            "reasoning": text,
            "structured": self._try_parse_json(text),
        }

    def _build_prompt(self, case: AdvancedCaseRequest, route_result: Dict) -> str:
        return f"""
Return ONLY concise Vietnamese clinical reasoning for advanced case analysis.
Do not diagnose definitively. Do not prescribe medication.

Case:
{case_to_text(case)}

Selected specialties: {", ".join(route_result.get("selected_specialties", []))}
Knowledge hits: {json.dumps(route_result.get("knowledge_hits", []), ensure_ascii=False)}

Focus on likely organ systems, warning signs, missing data, and next safe clinical steps.
""".strip()

    def _try_parse_json(self, text: str) -> Dict:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        except Exception:
            return {}
        return {}
