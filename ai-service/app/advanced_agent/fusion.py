from typing import Dict


def adaptive_fusion(router_probabilities: Dict[str, float], medgemma_result: Dict) -> Dict[str, float]:
    fused = {}
    reasoning = (medgemma_result.get("reasoning") or "").lower()
    for specialty, probability in router_probabilities.items():
        boost = 0.0
        if specialty.replace("_", " ") in reasoning or specialty in reasoning:
            boost += 0.08
        if specialty == "hepatology" and any(term in reasoning for term in ["gan", "máº­t", "bilirubin", "vÃ ng da"]):
            boost += 0.12
        if specialty == "infectious_disease" and any(term in reasoning for term in ["nhiá»…m trÃ¹ng", "sá»‘t", "viÃªm"]):
            boost += 0.08
        fused[specialty] = round(min(max(probability + boost, 0.0), 0.99), 4)
    return dict(sorted(fused.items(), key=lambda item: item[1], reverse=True))
