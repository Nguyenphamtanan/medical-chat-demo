import json
import re
from typing import Any, Dict, List, Optional


DISCLAIMER = "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."

ALLOWED_SEVERITIES = {
    "low",
    "low_to_moderate",
    "moderate",
    "high",
    "emergency",
    "unknown",
}

PLACEHOLDER_PHRASES = [
    "Tóm tắt ngắn triệu chứng và hướng liên quan",
    "hệ/cơ quan có thể liên quan",
    "khả năng giải thích phù hợp",
    "dấu hiệu nguy hiểm cần đi khám/cấp cứu",
    "câu hỏi cần hỏi thêm",
    "Khuyến nghị an toàn, không kê thuốc",
    "Nội dung cụ thể",
    "Viết tóm tắt cụ thể dựa trên triệu chứng người dùng",
    "Liệt kê hệ/cơ quan cụ thể",
    "Liệt kê khả năng giải thích cụ thể",
    "Liệt kê dấu hiệu nguy hiểm cụ thể",
    "Liệt kê câu hỏi cụ thể",
    "Viết khuyến nghị an toàn cụ thể",
]

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


def _lower(text: str) -> str:
    return str(text or "").strip().lower()


def _contains_any(text: str, words: List[str]) -> bool:
    lowered = _lower(text)
    return any(word in lowered for word in words)


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def _strip_markdown_and_thought(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"<unused\d+>\s*thought", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?is)<thought>.*?</thought>", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*(thought|analysis)\s*:\s*", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"(?im)\s*```\s*$", "", cleaned)
    return cleaned.strip()


def _extract_balanced_json_objects(text: str) -> List[str]:
    candidates = []
    start = None
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(text[start : index + 1])
                start = None

    return candidates


def is_placeholder_response(data: Dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return True

    required_keys = [
        "summary",
        "possible_related_systems",
        "possible_explanations",
        "red_flags",
        "missing_questions",
        "recommendation",
    ]

    for key in required_keys:
        value = data.get(key)

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, list):
            values = [str(item) for item in value]
        else:
            values = []

        if not values or not any(item.strip() for item in values):
            return True

        joined = " ".join(values)
        if any(phrase.lower() in joined.lower() for phrase in PLACEHOLDER_PHRASES):
            return True

    return False


def detect_symptom_profile(symptoms: str) -> Dict[str, Any]:
    text = _lower(symptoms)

    if _contains_any(
        text,
        [
            "vàng da",
            "vang da",
            "vàng mắt",
            "vang mat",
            "mắt vàng",
            "mat vang",
            "nước tiểu sẫm",
            "nuoc tieu sam",
            "nước tiểu đậm",
            "phân bạc màu",
            "phan bac mau",
            "bilirubin",
        ],
    ):
        return {
            "summary": (
                f"Bạn mô tả triệu chứng vàng da hoặc vàng mắt: {symptoms}. "
                "Triệu chứng này thường cần đánh giá sớm vì có thể liên quan đến tăng bilirubin, gan, túi mật hoặc đường mật."
            ),
            "possible_related_systems": ["gan", "mật", "đường mật", "máu", "tiêu hóa"],
            "possible_explanations": [
                "Tăng bilirubin do vấn đề ở gan, túi mật hoặc đường mật.",
                "Tắc mật hoặc sỏi mật có thể gây vàng da, nước tiểu sẫm màu và phân bạc màu.",
                "Viêm gan, tổn thương gan do rượu, thuốc, thực phẩm chức năng hoặc nhiễm virus cũng cần được loại trừ.",
                "Một số rối loạn máu gây tan máu cũng có thể làm bilirubin tăng.",
            ],
            "red_flags": [
                "Vàng da kèm sốt, rét run hoặc đau vùng hạ sườn phải.",
                "Nước tiểu sẫm màu, phân bạc màu, ngứa nhiều hoặc vàng da tăng nhanh.",
                "Lơ mơ, nôn nhiều, đau bụng dữ dội, chảy máu bất thường hoặc mệt lả.",
            ],
            "missing_questions": [
                "Bạn bị vàng da từ khi nào và có vàng mắt không?",
                "Nước tiểu có sẫm màu hoặc phân có bạc màu không?",
                "Có đau bụng vùng hạ sườn phải, sốt, ngứa da, buồn nôn hoặc mệt nhiều không?",
                "Gần đây có uống rượu, dùng thuốc mới, thực phẩm chức năng hoặc từng mắc viêm gan không?",
            ],
            "recommendation": (
                "Bạn nên đi khám sớm để được xét nghiệm bilirubin, men gan và đánh giá gan mật. "
                "Nếu có sốt, đau bụng nhiều, lơ mơ, nôn nhiều, nước tiểu rất sẫm, phân bạc màu hoặc vàng da tăng nhanh thì cần đi khám/cấp cứu ngay."
            ),
            "severity": "moderate",
        }

    if _contains_any(text, ["khó thở", "kho tho", "tím môi", "tim moi", "đau ngực", "dau nguc", "thở gấp"]):
        return {
            "summary": f"Bạn mô tả triệu chứng có thể liên quan đến hô hấp hoặc tim mạch: {symptoms}.",
            "possible_related_systems": ["hô hấp", "tim mạch"],
            "possible_explanations": [
                "Khó thở hoặc đau ngực có thể liên quan đến nhiễm trùng hô hấp, hen, vấn đề tim mạch hoặc nguyên nhân khác.",
                "Cần hỏi thêm mức độ, thời điểm xuất hiện và triệu chứng đi kèm để phân loại nguy cơ.",
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

    if _contains_any(text, ["sốt", "sot", "ho", "đau họng", "dau hong", "sổ mũi", "nghẹt mũi"]):
        return {
            "summary": f"Bạn mô tả triệu chứng gợi ý vấn đề hô hấp hoặc tai mũi họng: {symptoms}.",
            "possible_related_systems": ["hô hấp", "tai mũi họng", "toàn thân"],
            "possible_explanations": [
                "Cảm lạnh, cúm, COVID-19, viêm họng hoặc nhiễm trùng hô hấp trên có thể gây các triệu chứng này.",
                "Cần biết nhiệt độ sốt, thời gian kéo dài và có khó thở hay đau ngực không.",
            ],
            "red_flags": [
                "Khó thở, đau ngực, tím môi, lơ mơ hoặc sốt cao không hạ.",
                "Triệu chứng kéo dài nhiều ngày, nặng dần hoặc người bệnh có bệnh nền/suy giảm miễn dịch.",
            ],
            "missing_questions": [
                "Bạn sốt bao nhiêu độ và kéo dài bao lâu?",
                "Có khó thở, đau ngực, ho ra máu hoặc mệt lả không?",
                "Có tiếp xúc người bệnh hoặc đã test COVID/cúm chưa?",
            ],
            "recommendation": (
                "Theo dõi nhiệt độ, nghỉ ngơi và uống đủ nước nếu phù hợp. "
                "Nếu khó thở, đau ngực, sốt cao kéo dài hoặc triệu chứng nặng dần thì nên đi khám."
            ),
            "severity": "low_to_moderate",
        }

    if _contains_any(text, ["đau bụng", "dau bung", "buồn nôn", "nôn", "tiêu chảy", "phân đen", "nôn ra máu"]):
        return {
            "summary": f"Bạn mô tả triệu chứng có thể liên quan đến hệ tiêu hóa: {symptoms}.",
            "possible_related_systems": ["tiêu hóa", "dạ dày", "ruột", "gan mật"],
            "possible_explanations": [
                "Rối loạn tiêu hóa, nhiễm trùng tiêu hóa, viêm dạ dày-ruột hoặc vấn đề gan mật có thể gây khó chịu đường tiêu hóa.",
                "Phân đen hoặc nôn ra máu là dấu hiệu cảnh báo cần đi khám khẩn.",
            ],
            "red_flags": [
                "Đau bụng dữ dội, bụng cứng, nôn liên tục hoặc mất nước nặng.",
                "Phân đen, nôn ra máu, sốt cao hoặc lơ mơ.",
            ],
            "missing_questions": [
                "Đau bụng ở vị trí nào và mức độ đau ra sao?",
                "Có sốt, nôn, tiêu chảy, phân đen hoặc nôn ra máu không?",
                "Triệu chứng kéo dài bao lâu và có liên quan bữa ăn không?",
            ],
            "recommendation": (
                "Nếu đau bụng dữ dội, nôn liên tục, mất nước, phân đen hoặc nôn ra máu thì cần đi khám/cấp cứu. "
                "Nếu triệu chứng nhẹ nhưng kéo dài, nên đi khám để tìm nguyên nhân."
            ),
            "severity": "low_to_moderate",
        }

    if _contains_any(text, ["tiểu buốt", "tiểu rắt", "tiểu máu", "đau lưng", "tiểu ít", "phù chân"]):
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
                "Nước tiểu có máu, đục, mùi lạ hoặc lượng tiểu rất ít không?",
                "Triệu chứng kéo dài bao lâu?",
            ],
            "recommendation": (
                "Nên đi khám nếu triệu chứng kéo dài, có sốt, đau hông lưng, tiểu máu hoặc tiểu ít. "
                "Nếu mệt lả, khó thở, phù nhiều hoặc đau dữ dội thì cần đi khám khẩn."
            ),
            "severity": "low_to_moderate",
        }

    return {
        "summary": f"Bạn mô tả: {symptoms}. Cần thêm thông tin để định hướng mức độ nguy cơ và hệ cơ quan liên quan.",
        "possible_related_systems": ["chưa xác định rõ", "toàn thân"],
        "possible_explanations": [
            "Triệu chứng có thể liên quan nhiễm trùng, viêm, mất nước, tác dụng phụ thuốc hoặc nguyên nhân khác.",
            "Cần hỏi thêm thời gian, mức độ nặng, bệnh nền và dấu hiệu đi kèm để phân loại an toàn hơn.",
        ],
        "red_flags": [
            "Đau ngực dữ dội, khó thở nặng, ngất, lú lẫn, tím môi hoặc yếu liệt.",
            "Sốt cao kéo dài, mất nước nặng, đau bụng dữ dội, chảy máu bất thường hoặc triệu chứng xấu đi nhanh.",
        ],
        "missing_questions": [
            "Bạn bao nhiêu tuổi?",
            "Triệu chứng bắt đầu khi nào và đang nặng lên hay giảm đi?",
            "Có sốt cao, khó thở, đau ngực, nôn ói, chảy máu hoặc bệnh nền không?",
        ],
        "recommendation": (
            "Theo dõi triệu chứng và liên hệ nhân viên y tế nếu triệu chứng kéo dài, nặng hơn hoặc có dấu hiệu cảnh báo. "
            "Nếu xuất hiện dấu hiệu nguy hiểm, cần đi khám/cấp cứu ngay."
        ),
        "severity": "unknown",
    }


def build_stub_response(symptoms: str, model_status: str = "stub_response_no_medgemma_called") -> Dict[str, Any]:
    profile = detect_symptom_profile(symptoms)
    return {
        **profile,
        "model_status": model_status,
        "disclaimer": DISCLAIMER,
    }


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text or not str(text).strip():
        return None

    cleaned = _strip_markdown_and_thought(text)

    candidates = []

    try:
        direct = json.loads(cleaned)
        if isinstance(direct, dict):
            candidates.append(direct)
    except Exception:
        pass

    for candidate_text in reversed(_extract_balanced_json_objects(cleaned)):
        try:
            parsed = json.loads(candidate_text)
            if isinstance(parsed, dict):
                candidates.append(parsed)
        except Exception:
            continue

    for candidate in candidates:
        if not is_placeholder_response(candidate):
            return candidate

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
    normalized["severity"] = severity if severity in ALLOWED_SEVERITIES else "unknown"
    normalized["summary"] = str(normalized.get("summary") or "").strip()
    normalized["recommendation"] = str(normalized.get("recommendation") or "").strip()
    normalized["model_status"] = str(normalized.get("model_status") or model_status).strip()
    normalized["disclaimer"] = str(normalized.get("disclaimer") or DISCLAIMER).strip()

    return normalized


def build_non_json_medgemma_response(symptoms: str, raw_text: str) -> Dict[str, Any]:
    profile = detect_symptom_profile(symptoms)

    return {
        **profile,
        "summary": profile["summary"],
        "model_status": "medgemma_non_json_rule_based_backup",
        "disclaimer": DISCLAIMER,
    }
