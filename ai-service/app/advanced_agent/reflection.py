from typing import Dict


def reflect(case_text: str, specialist_outputs: Dict, medgemma_result: Dict) -> Dict:
    warnings = set()
    missing = set()
    for output in specialist_outputs.values():
        warnings.update(output.get("red_flags", []))
        missing.update(output.get("missing_data", []))

    fallback = not medgemma_result.get("reasoning")
    return {
        "safety_checks": [
            "KhÃ´ng Ä‘Æ°a ra cháº©n Ä‘oÃ¡n cháº¯c cháº¯n.",
            "KhÃ´ng kÃª Ä‘Æ¡n thuá»‘c.",
            "Æ¯u tiÃªn dáº¥u hiá»‡u cáº£nh bÃ¡o vÃ  dá»¯ liá»‡u cÃ²n thiáº¿u.",
        ],
        "model_fallback_used": fallback,
        "warnings": sorted(warnings),
        "missing_data": sorted(missing),
        "confidence_note": (
            "Äá»™ tin cáº­y phá»¥ thuá»™c vÃ o dá»¯ liá»‡u nháº­p; cáº§n khÃ¡m trá»±c tiáº¿p vÃ  xÃ©t nghiá»‡m bá»• sung."
        ),
    }
