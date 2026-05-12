from collections import defaultdict
from typing import Dict, List

from .calibrator import get_calibrator
from .knowledge_base import get_knowledge_base
from .models import AdvancedCaseRequest, case_to_text
from .translation import normalize_text


SPECIALTY_HINTS = {
    "hepatology": ["vÃ ng da", "bilirubin", "nÆ°á»›c tiá»ƒu sáº«m", "ngá»©a", "gan", "máº­t"],
    "gastroenterology": ["Ä‘au bá»¥ng", "bá»¥ng", "siÃªu Ã¢m", "gan to", "nÃ´n", "phÃ¢n báº¡c mÃ u"],
    "endocrinology": ["Ä‘Ã¡i thÃ¡o Ä‘Æ°á»ng", "metformin", "glucose", "gan nhiá»…m má»¡"],
    "infectious_disease": ["sá»‘t", "rÃ©t run", "nhiá»…m trÃ¹ng", "viÃªm gan"],
    "cardiology": ["Ä‘au ngá»±c", "khÃ³ thá»Ÿ", "ngáº¥t", "phÃ¹"],
}


class CaseRouter:
    def __init__(self):
        self.kb = get_knowledge_base()
        self.calibrator = get_calibrator()

    def route(self, case: AdvancedCaseRequest) -> Dict:
        text = normalize_text(case_to_text(case))
        hits = self.kb.search(text, top_k=5)
        bm25_by_specialty = defaultdict(float)
        for hit in hits:
            bm25_by_specialty[hit["specialty"]] += hit["score"]

        lab_signals = self._lab_signals(case)
        symptom_signals = self._keyword_signals(text)
        probabilities = {}
        for specialty in SPECIALTY_HINTS:
            features = {
                "bm25": min(bm25_by_specialty.get(specialty, 0.0) / 3.0, 1.5),
                "lab": lab_signals.get(specialty, 0.0),
                "symptom": symptom_signals.get(specialty, 0.0),
                "history": self._history_signal(case, specialty),
                "red_flag": self._red_flag_signal(text, specialty),
            }
            probabilities[specialty] = self.calibrator.predict(features)

        selected = [
            specialty
            for specialty, _ in sorted(
                probabilities.items(), key=lambda item: item[1], reverse=True
            )[:3]
            if probabilities[specialty] >= 0.25
        ]
        if not selected:
            selected = ["gastroenterology"]

        plan = [
            "Chuáº©n hÃ³a dá»¯ liá»‡u ca bá»‡nh cÃ³ cáº¥u trÃºc.",
            "Truy xuáº¥t tri thá»©c lÃ¢m sÃ ng liÃªn quan báº±ng BM25.",
            "Äá»‹nh tuyáº¿n chuyÃªn khoa vÃ  hiá»‡u chá»‰nh xÃ¡c suáº¥t báº±ng TinyScoreCalibrator.",
            "Tá»•ng há»£p láº­p luáº­n MedGemma náº¿u kháº£ dá»¥ng, sau Ä‘Ã³ cháº¡y phÃ¢n tÃ­ch chuyÃªn khoa.",
            "Pháº£n tÆ° an toÃ n, nÃªu cáº£nh bÃ¡o vÃ  cÃ¢u há»i cáº§n bá»• sung.",
        ]
        return {
            "plan": plan,
            "selected_specialties": selected,
            "knowledge_hits": hits,
            "router_probabilities": probabilities,
        }

    def _keyword_signals(self, text: str) -> Dict[str, float]:
        signals = {}
        for specialty, hints in SPECIALTY_HINTS.items():
            matches = sum(1 for hint in hints if hint in text)
            signals[specialty] = min(matches / 3.0, 1.0)
        return signals

    def _history_signal(self, case: AdvancedCaseRequest, specialty: str) -> float:
        history = normalize_text(" ".join(case.history))
        hints = SPECIALTY_HINTS.get(specialty, [])
        return 1.0 if any(hint in history for hint in hints) else 0.0

    def _red_flag_signal(self, text: str, specialty: str) -> float:
        common = ["lÆ¡ mÆ¡", "tá»¥t huyáº¿t Ã¡p", "Ä‘au dá»¯ dá»™i", "khÃ³ thá»Ÿ", "ngáº¥t"]
        hepatobiliary = ["sá»‘t", "rÃ©t run", "vÃ ng da", "Ä‘au háº¡ sÆ°á»n pháº£i"]
        terms: List[str] = common + (hepatobiliary if specialty in {"hepatology", "gastroenterology", "infectious_disease"} else [])
        return 1.0 if any(term in text for term in terms) else 0.0

    def _lab_signals(self, case: AdvancedCaseRequest) -> Dict[str, float]:
        signals = defaultdict(float)
        for lab in case.labs:
            name = lab.name.lower()
            high = (
                lab.reference_high is not None
                and lab.value is not None
                and lab.value > lab.reference_high
            )
            low = (
                lab.reference_low is not None
                and lab.value is not None
                and lab.value < lab.reference_low
            )
            abnormal = high or low
            if not abnormal:
                continue
            if any(term in name for term in ["bilirubin", "alt", "ast", "alp", "ggt"]):
                signals["hepatology"] = 1.0
                signals["gastroenterology"] = max(signals["gastroenterology"], 0.8)
            if any(term in name for term in ["glucose", "hba1c"]):
                signals["endocrinology"] = 1.0
            if any(term in name for term in ["wbc", "crp", "procalcitonin"]):
                signals["infectious_disease"] = 1.0
        return signals
