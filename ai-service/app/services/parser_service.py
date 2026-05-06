import json
import re
from typing import Any, Dict, List, Optional


DISCLAIMER = "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."


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


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def _lower(text: str) -> str:
    return (text or "").strip().lower()


def _strip_thought_blocks(text: str) -> str:
    cleaned = str(text or "").strip()

    cleaned = re.sub(r"<unused\d+>\s*thought", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?i)^thought\s*", "", cleaned).strip()

    return cleaned


def detect_symptom_profile(symptoms: str) -> Dict[str, Any]:
    s = _lower(symptoms)

    if any(x in s for x in ["vàng da", "vàng mắt", "mắt vàng", "nước tiểu sẫm", "phân bạc màu"]):
        return {
            "summary": (
                f"Bạn mô tả có dấu hiệu vàng da/vàng mắt: {symptoms}. "
                "Đây là triệu chứng cần được đánh giá sớm vì có thể liên quan đến gan, mật hoặc đường mật."
            ),
            "possible_related_systems": ["gan", "mật", "đường mật", "tiêu hóa"],
            "possible_explanations": [
                "Vàng da có thể liên quan đến tăng bilirubin do vấn đề ở gan, túi mật hoặc đường mật.",
                "Một số nguyên nhân có thể gồm viêm gan, tắc mật, sỏi mật, tác dụng phụ thuốc hoặc bệnh lý gan mật khác.",
                "Cũng cần phân biệt với vàng da do chế độ ăn nhiều beta-carotene, nhưng thường không làm vàng mắt.",
            ],
            "red_flags": [
                "Vàng da kèm sốt, đau bụng vùng hạ sườn phải, rét run hoặc nôn nhiều.",
                "Nước tiểu sẫm màu, phân bạc màu, ngứa nhiều, mệt lả hoặc vàng da tăng nhanh.",
                "Lơ mơ, chảy máu bất thường, đau bụng dữ dội hoặc tình trạng xấu đi nhanh.",
            ],
            "missing_questions": [
                "Bạn bị vàng da từ khi nào?",
                "Mắt có vàng không, nước tiểu có sẫm màu không, phân có bạc màu không?",
                "Có đau bụng vùng hạ sườn phải, sốt, buồn nôn, ngứa da hoặc mệt nhiều không?",
                "Gần đây có uống rượu, dùng thuốc mới, thực phẩm chức năng hoặc từng mắc viêm gan không?",
            ],
            "recommendation": (
                "Bạn nên đi khám sớm để được xét nghiệm bilirubin, men gan và đánh giá gan mật. "
                "Nếu có sốt, đau bụng nhiều, lơ mơ, nôn nhiều, nước tiểu rất sẫm hoặc vàng da tăng nhanh "
                "thì cần đi khám/cấp cứu ngay."
            ),
            "severity": "moderate",
        }

    if any(x in s for x in ["khó thở", "thở gấp", "tím môi", "đau ngực"]):
        return {
            "summary": f"Bạn mô tả triệu chứng có thể liên quan hô hấp hoặc tim mạch: {symptoms}.",
            "possible_related_systems": ["hô hấp", "tim mạch"],
            "possible_explanations": [
                "Khó thở hoặc đau ngực có thể liên quan đến nhiễm trùng hô hấp, hen, vấn đề tim mạch hoặc nguyên nhân khác.",
                "Cần hỏi thêm mức độ, thời gian xuất hiện và triệu chứng đi kèm để phân loại nguy cơ.",
            ],
            "red_flags": [
                "Khó thở nặng, tím môi, đau ngực dữ dội, ngất hoặc lú lẫn.",
                "Triệu chứng tăng nhanh hoặc khó thở cả khi nghỉ.",
            ],
            "missing_questions": [
                "Bạn có khó thở khi nghỉ không?",
                "Có đau ngực, sốt cao, ho ra máu hoặc tím môi không?",
                "Triệu chứng bắt đầu từ khi nào và có nặng dần không?",
            ],
            "recommendation": (
                "Nếu khó thở nặng, đau ngực dữ dội, tím môi, ngất hoặc lú lẫn thì cần đi cấp cứu ngay. "
                "Nếu triệu chứng nhẹ hơn nhưng kéo dài hoặc nặng dần, nên đi khám sớm."
            ),
            "severity": "high",
        }

    if any(x in s for x in ["sốt", "ho", "đau họng", "sổ mũi", "nghẹt mũi"]):
        return {
            "summary": f"Bạn mô tả triệu chứng giống nhiễm trùng hô hấp hoặc tai mũi họng: {symptoms}.",
            "possible_related_systems": ["hô hấp", "tai mũi họng", "toàn thân"],
            "possible_explanations": [
                "Sốt, ho, đau họng có thể gặp trong cảm lạnh, cúm, viêm họng, COVID-19 hoặc nhiễm trùng hô hấp khác.",
                "Cần hỏi thêm sốt bao nhiêu độ, thời gian kéo dài và có khó thở hay không.",
            ],
            "red_flags": [
                "Khó thở, đau ngực, tím môi, lơ mơ hoặc sốt cao không hạ.",
                "Triệu chứng kéo dài nhiều ngày, nặng dần hoặc người bệnh có bệnh nền/suy giảm miễn dịch.",
            ],
            "missing_questions": [
                "Bạn sốt bao nhiêu độ và kéo dài bao lâu?",
                "Có khó thở, đau ngực, ho ra máu hoặc mệt lả không?",
                "Có tiếp xúc người bệnh, test COVID/cúm chưa?",
            ],
            "recommendation": (
                "Theo dõi nhiệt độ, nghỉ ngơi và uống đủ nước nếu phù hợp. "
                "Nếu khó thở, đau ngực, sốt cao kéo dài hoặc triệu chứng nặng dần thì nên đi khám."
            ),
            "severity": "low_to_moderate",
        }

    if any(x in s for x in ["đau bụng", "buồn nôn", "nôn", "tiêu chảy", "phân đen", "nôn ra máu"]):
        return {
            "summary": f"Bạn mô tả triệu chứng có thể liên quan hệ tiêu hóa: {symptoms}.",
            "possible_related_systems": ["tiêu hóa"],
            "possible_explanations": [
                "Triệu chứng có thể liên quan rối loạn tiêu hóa, nhiễm trùng tiêu hóa, viêm dạ dày-ruột hoặc nguyên nhân khác.",
                "Phân đen hoặc nôn ra máu là dấu hiệu cảnh báo cần đi khám khẩn.",
            ],
            "red_flags": [
                "Đau bụng dữ dội, bụng cứng, nôn liên tục, mất nước nặng.",
                "Phân đen, nôn ra máu, sốt cao hoặc lơ mơ.",
            ],
            "missing_questions": [
                "Đau bụng ở vị trí nào và mức độ đau ra sao?",
                "Có sốt, nôn, tiêu chảy, phân đen hoặc nôn ra máu không?",
                "Triệu chứng kéo dài bao lâu?",
            ],
            "recommendation": (
                "Nếu đau bụng dữ dội, nôn liên tục, mất nước, phân đen hoặc nôn ra máu thì cần đi khám/cấp cứu. "
                "Nếu triệu chứng nhẹ nhưng kéo dài, nên đi khám để tìm nguyên nhân."
            ),
            "severity": "low_to_moderate",
        }

    if any(x in s for x in ["tiểu buốt", "tiểu rắt", "tiểu máu", "đau lưng", "tiểu ít", "phù chân"]):
        return {
            "summary": f"Bạn mô tả triệu chứng có thể liên quan tiết niệu hoặc thận: {symptoms}.",
            "possible_related_systems": ["thận", "tiết niệu"],
            "possible_explanations": [
                "Tiểu buốt, tiểu rắt hoặc tiểu máu có thể liên quan nhiễm trùng tiết niệu, sỏi hoặc nguyên nhân khác.",
                "Tiểu ít hoặc phù chân có thể cần đánh giá chức năng thận và tình trạng giữ nước.",
            ],
            "red_flags": [
                "Sốt cao, đau hông lưng nhiều, tiểu máu rõ, tiểu rất ít hoặc phù tăng nhanh.",
                "Lú lẫn, mệt lả, khó thở hoặc đau dữ dội.",
            ],
            "missing_questions": [
                "Có sốt hoặc đau hông lưng không?",
                "Nước tiểu có máu, đục, mùi lạ hoặc tiểu rất ít không?",
                "Triệu chứng kéo dài bao lâu?",
            ],
            "recommendation": (
                "Nên đi khám nếu triệu chứng kéo dài, có sốt, đau hông lưng, tiểu máu hoặc tiểu ít. "
                "Nếu mệt lả, khó thở, phù nhiều hoặc đau dữ dội thì cần đi khám khẩn."
            ),
            "severity": "low_to_moderate",
        }

    return {
        "summary": f"Bạn đã mô tả: {symptoms}",
        "possible_related_systems": ["chưa xác định"],
        "possible_explanations": [
            "Cần thêm thông tin để đánh giá sơ bộ.",
            "Triệu chứng có thể liên quan nhiễm trùng, viêm, mất nước, tác dụng phụ thuốc hoặc nguyên nhân khác.",
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
            "Theo dõi triệu chứng và liên hệ nhân viên y tế nếu triệu chứng kéo dài, nặng hơn hoặc có dấu hiệu cảnh báo."
        ),
        "severity": "unknown",
    }


def build_stub_response(symptoms: str, model_status: str = "stub_response_no_medgemma_called") -> Dict[str, Any]:
    profile = detect_symptom_profile(symptoms)

    return {
        "summary": profile["summary"],
        "possible_related_systems": profile["possible_related_systems"],
        "possible_explanations": profile["possible_explanations"],
        "red_flags": profile["red_flags"],
        "missing_questions": profile["missing_questions"],
        "recommendation": profile["recommendation"],
        "severity": profile["severity"],
        "model_status": model_status,
        "disclaimer": DISCLAIMER,
    }


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text or not str(text).strip():
        return None

    cleaned = _strip_thought_blocks(text)

    cleaned = re.sub(r"^\s*```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    json_candidates = re.findall(r"\{[\s\S]*\}", cleaned)

    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate.strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

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
    model_status: str = "real_medgemma_response",
) -> Dict[str, Any]:
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
        normalized[key] = _as_list(normalized.get(key, []))

    severity = str(normalized.get("severity", "unknown")).strip().lower()
    allowed = {"low", "low_to_moderate", "moderate", "high", "emergency", "unknown"}
    normalized["severity"] = severity if severity in allowed else "unknown"

    normalized["model_status"] = normalized.get("model_status") or model_status
    normalized["disclaimer"] = normalized.get("disclaimer") or DISCLAIMER

    return normalized


def build_non_json_medgemma_response(symptoms: str, raw_text: str) -> Dict[str, Any]:
    profile = detect_symptom_profile(symptoms)
    clean_raw = _strip_thought_blocks(raw_text or "").strip()

    summary = profile["summary"]

    if clean_raw:
        summary = (
            profile["summary"]
            + " MedGemma đã phản hồi nhưng không trả JSON hợp lệ, nên hệ thống dùng phân loại an toàn theo triệu chứng."
        )

    return {
        "summary": summary,
        "possible_related_systems": profile["possible_related_systems"],
        "possible_explanations": profile["possible_explanations"],
        "red_flags": profile["red_flags"],
        "missing_questions": profile["missing_questions"],
        "recommendation": profile["recommendation"],
        "severity": profile["severity"],
        "model_status": "real_medgemma_response_json_parse_failed",
        "disclaimer": DISCLAIMER,
    }