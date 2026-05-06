import json
import re
from typing import Any, Dict, List, Optional


DISCLAIMER = "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        # Nếu model trả một chuỗi dài, vẫn ép thành list 1 phần tử.
        return [value.strip()]

    return []


def build_stub_response(symptoms: str, status: str = "ai_service_stub_fallback") -> Dict[str, Any]:
    return {
        "summary": f"Bạn đã mô tả: {symptoms}",
        "possible_related_systems": ["chưa xác định"],
        "possible_explanations": [
            "Cần thêm thông tin để đánh giá sơ bộ.",
            "Triệu chứng có thể liên quan nhiễm trùng, viêm, mất nước, dị ứng hoặc nguyên nhân khác.",
        ],
        "red_flags": [
            "Đau ngực dữ dội, khó thở nặng, ngất, lú lẫn, tím môi hoặc yếu liệt.",
            "Sốt cao kéo dài, mất nước nặng, đau bụng dữ dội hoặc triệu chứng xấu đi nhanh.",
        ],
        "missing_questions": [
            "Bạn bao nhiêu tuổi?",
            "Triệu chứng kéo dài bao lâu?",
            "Có sốt cao, khó thở, đau ngực, nôn ói, chảy máu hoặc bệnh nền không?",
        ],
        "recommendation": (
            "Theo dõi triệu chứng, nghỉ ngơi và uống đủ nước nếu phù hợp. "
            "Liên hệ nhân viên y tế nếu triệu chứng kéo dài, nặng hơn hoặc có dấu hiệu cảnh báo."
        ),
        "severity": "unknown" if "failed" in status else "low_to_moderate",
        "model_status": status,
        "disclaimer": DISCLAIMER,
    }


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from raw MedGemma output.
    MedGemma sometimes returns:
    - pure JSON
    - ```json ... ```
    - text before/after JSON
    - Python-like quotes, because apparently valid JSON was too peaceful
    """
    if not text or not str(text).strip():
        return None

    cleaned = str(text).strip()

    # Remove markdown fences anywhere around output.
    cleaned = re.sub(r"^\s*```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # 1. Try direct parse.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 2. Try greedy JSON object extraction.
    greedy_match = re.search(r"\{[\s\S]*\}", cleaned)
    if greedy_match:
        candidate = greedy_match.group(0).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 3. Try extracting JSON from common labels.
    # Example: "Here is the JSON:\n{...}"
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return None


def normalize_medical_response(
    data: Dict[str, Any],
    status: str = "real_medgemma_response",
) -> Dict[str, Any]:
    severity = str(data.get("severity", "unknown")).strip().lower()

    allowed = {
        "low",
        "low_to_moderate",
        "moderate",
        "high",
        "emergency",
        "unknown",
    }

    if severity not in allowed:
        severity = "unknown"

    # Ưu tiên status từ raw MedGemma, nhưng nếu JSON có model_status thì giữ loại readable hơn.
    model_status = str(data.get("model_status") or status or "real_medgemma_response").strip()

    return {
        "summary": str(data.get("summary", "")).strip() or "Chưa có tóm tắt phù hợp.",
        "possible_related_systems": _as_list(data.get("possible_related_systems", [])),
        "possible_explanations": _as_list(data.get("possible_explanations", [])),
        "red_flags": _as_list(data.get("red_flags", [])),
        "missing_questions": _as_list(data.get("missing_questions", [])),
        "recommendation": str(data.get("recommendation", "")).strip()
        or "Nên theo dõi triệu chứng và liên hệ nhân viên y tế nếu triệu chứng kéo dài hoặc nặng hơn.",
        "severity": severity,
        "model_status": model_status,
        "disclaimer": str(data.get("disclaimer", DISCLAIMER)).strip() or DISCLAIMER,
    }