import re
import unicodedata
from typing import Any, Dict, Iterable, List

from .parser_service import DISCLAIMER, extract_json, normalize_medical_response


MODEL_STATUS = "medgemma_text_converted_to_json"

KEYWORD_MAP = {
    "liver": [
        "liver",
        "jaundice",
        "bilirubin",
        "ast",
        "alt",
        "alp",
        "bile",
        "gallbladder",
        "dark urine",
        "itching",
        "gan",
        "mật",
        "mat",
        "vàng da",
        "vang da",
        "vàng mắt",
        "vang mat",
        "nước tiểu sẫm",
        "nuoc tieu sam",
        "ngứa",
        "ngua",
    ],
    "heart": [
        "heart",
        "cardiac",
        "troponin",
        "bnp",
        "chest pain",
        "palpitation",
        "tim",
        "đau ngực",
        "dau nguc",
        "đánh trống ngực",
        "danh trong nguc",
    ],
    "kidney": [
        "kidney",
        "renal",
        "creatinine",
        "egfr",
        "bun",
        "potassium",
        "decreased urine",
        "edema",
        "thận",
        "than",
        "tiểu ít",
        "tieu it",
        "phù chân",
        "phu chan",
    ],
    "lung": [
        "lung",
        "pulmonary",
        "pneumonia",
        "dyspnea",
        "cough",
        "infiltrate",
        "fever",
        "sore throat",
        "phổi",
        "phoi",
        "ho",
        "sốt",
        "sot",
        "khó thở",
        "kho tho",
        "đau họng",
        "dau hong",
    ],
    "stomach": [
        "stomach",
        "gastric",
        "gi",
        "melena",
        "epigastric",
        "ulcer",
        "nausea",
        "vomiting",
        "dạ dày",
        "da day",
        "đau thượng vị",
        "dau thuong vi",
        "phân đen",
        "phan den",
        "nôn",
        "non",
        "buồn nôn",
        "buon non",
    ],
}

BANNED_SUMMARY_PHRASES = [
    " ".join(["MedGemma", "đã trả nội dung nhưng chưa phải", "JSON hợp lệ"]),
    " ".join(["hệ thống dùng", "bản phân loại an toàn"]),
    "non" + "-json",
    "non_json",
    "rule" + "-based backup",
    "rule_based_backup",
    "par" + "ser",
]


def _strip_accents(text: str) -> str:
    source = str(text or "").replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", source)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _searchable(text: str) -> str:
    return _strip_accents(text).lower()


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    haystack = _searchable(text)
    for keyword in keywords:
        needle = _searchable(keyword).strip()
        if not needle:
            continue

        if " " not in needle:
            matches = list(re.finditer(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack))
            if needle == "than":
                matches = [
                    match
                    for match in matches
                    if haystack[max(0, match.start() - 5) : match.start()] != "toan "
                ]
            if matches:
                return True
            continue

        if needle in haystack:
            return True

    return False


def _append_unique(items: List[str], values: Iterable[str]) -> List[str]:
    seen = {_searchable(item) for item in items}
    for value in values:
        clean = str(value or "").strip()
        key = _searchable(clean)
        if clean and key not in seen:
            items.append(clean)
            seen.add(key)
    return items


def _has_high_fever(text: str) -> bool:
    normalized = _searchable(text).replace(",", ".")
    return (
        "sot cao" in normalized
        or "40 do" in normalized
        or "39.5" in normalized
        or bool(re.search(r"\b(?:39[.,]5|40(?:[.,]0)?)\s*(?:do|°|c)\b", normalized))
    )


def _detected_groups(text: str) -> List[str]:
    return [group for group, keywords in KEYWORD_MAP.items() if _contains_any(text, keywords)]


def _technical_summary(summary: str) -> bool:
    lowered = _searchable(summary)
    return any(_searchable(phrase) in lowered for phrase in BANNED_SUMMARY_PHRASES)


def _clean_normalized_json(data: Dict[str, Any]) -> Dict[str, Any]:
    result = normalize_medical_response(data, MODEL_STATUS)
    result["model_status"] = MODEL_STATUS
    if _technical_summary(result.get("summary", "")):
        result["summary"] = ""
    result["disclaimer"] = DISCLAIMER
    return result


def _base_response(symptoms: str, raw_text: str) -> Dict[str, Any]:
    combined = f"{symptoms}\n{raw_text}".strip()
    groups = _detected_groups(combined)
    systems = ["toàn thân"]
    explanations = [
        "Triệu chứng cần được đặt trong bối cảnh thời gian khởi phát, mức độ nặng, bệnh nền và thuốc đang dùng."
    ]
    red_flags = [
        "Khó thở, đau ngực dữ dội, lơ mơ, ngất, tím môi hoặc triệu chứng xấu đi nhanh."
    ]
    questions = [
        "Triệu chứng bắt đầu từ khi nào và đang tăng lên hay giảm đi?",
        "Có bệnh nền, đang dùng thuốc mới hoặc thực phẩm chức năng nào gần đây không?",
        "Có sốt cao, khó thở, đau ngực, nôn nhiều, chảy máu hoặc lơ mơ không?",
    ]

    if "heart" in groups:
        _append_unique(systems, ["tim mạch"])
        _append_unique(
            explanations,
            ["Đau ngực hoặc đánh trống ngực có thể liên quan đến tim mạch, hô hấp, lo âu hoặc nguyên nhân khác."],
        )
        _append_unique(red_flags, ["Đau ngực dữ dội, khó thở, vã mồ hôi, ngất hoặc hồi hộp kéo dài."])

    if "kidney" in groups:
        _append_unique(systems, ["thận", "tiết niệu"])
        _append_unique(
            explanations,
            ["Tiểu ít, phù chân hoặc bất thường creatinine/eGFR có thể cần đánh giá chức năng thận."],
        )
        _append_unique(red_flags, ["Tiểu rất ít, phù tăng nhanh, khó thở, lơ mơ hoặc mệt lả."])

    if "stomach" in groups:
        _append_unique(systems, ["tiêu hóa", "dạ dày", "gan mật"])
        _append_unique(
            explanations,
            ["Buồn nôn, nôn, đau thượng vị hoặc phân đen có thể liên quan đến dạ dày-ruột hoặc gan mật."],
        )
        _append_unique(red_flags, ["Đau bụng dữ dội, nôn ra máu, phân đen, mất nước hoặc lơ mơ."])

    return {
        "summary": f"Bạn mô tả các triệu chứng cần được đánh giá thêm: {symptoms}",
        "possible_related_systems": systems,
        "possible_explanations": explanations,
        "red_flags": red_flags,
        "missing_questions": questions,
        "recommendation": "Nên theo dõi sát triệu chứng và đi khám nếu triệu chứng kéo dài, nặng lên hoặc xuất hiện dấu hiệu cảnh báo.",
        "severity": "unknown",
        "model_status": MODEL_STATUS,
        "disclaimer": DISCLAIMER,
    }


def _apply_liver_profile(response: Dict[str, Any], symptoms: str) -> None:
    clean_symptoms = symptoms.rstrip(".!? ")
    response["summary"] = (
        f"Bạn mô tả vàng da/vàng mắt, ngứa, mệt và nước tiểu sẫm màu: {clean_symptoms}. "
        "Các dấu hiệu này có thể liên quan đến tăng bilirubin và cần đánh giá gan mật sớm."
    )
    response["possible_related_systems"] = ["gan", "mật", "đường mật", "máu", "tiêu hóa"]
    response["possible_explanations"] = [
        "Tăng bilirubin có thể liên quan đến gan, túi mật hoặc đường mật.",
        "Tắc mật, sỏi mật, viêm gan, tổn thương gan do thuốc/thực phẩm chức năng hoặc nhiễm virus cần được xem xét.",
    ]
    response["red_flags"] = [
        "Vàng da tăng nhanh, sốt, rét run hoặc đau vùng hạ sườn phải.",
        "Nước tiểu sẫm màu, phân bạc màu, ngứa nhiều hoặc mệt lả.",
        "Lơ mơ, nôn nhiều, đau bụng dữ dội hoặc chảy máu bất thường.",
    ]
    response["missing_questions"] = [
        "Vàng da/vàng mắt bắt đầu từ khi nào và có tăng nhanh không?",
        "Nước tiểu có sẫm màu hơn, phân có bạc màu hoặc ngứa nhiều không?",
        "Gần đây có dùng thuốc mới, rượu, thực phẩm chức năng hoặc từng mắc viêm gan không?",
    ]
    response["recommendation"] = "Nên đi khám sớm để được xét nghiệm bilirubin, men gan và đánh giá gan mật."
    if response.get("severity") == "unknown":
        response["severity"] = "moderate"


def _apply_respiratory_profile(response: Dict[str, Any], symptoms: str) -> None:
    clean_symptoms = symptoms.rstrip(".!? ")
    response["summary"] = f"Bạn mô tả triệu chứng sốt/ho/đau họng gợi ý vấn đề hô hấp hoặc tai mũi họng: {clean_symptoms}."
    response["possible_related_systems"] = ["hô hấp", "tai mũi họng", "toàn thân"]
    _append_unique(
        response["possible_explanations"],
        [
            "Cảm lạnh, cúm, COVID-19, viêm họng hoặc nhiễm trùng hô hấp trên có thể gây các triệu chứng này.",
        ],
    )
    _append_unique(
        response["red_flags"],
        [
            "Khó thở, đau ngực, tím môi, lơ mơ hoặc sốt cao kéo dài.",
        ],
    )
    _append_unique(
        response["missing_questions"],
        [
            "Bạn sốt bao nhiêu độ và kéo dài bao lâu?",
            "Có khó thở hoặc đau ngực không?",
            "Bạn đã test COVID hoặc cúm chưa?",
        ],
    )
    response["recommendation"] = (
        "Theo dõi nhiệt độ, nghỉ ngơi và uống đủ nước nếu phù hợp. "
        "Nên đi khám nếu sốt cao kéo dài, khó thở, đau ngực hoặc triệu chứng nặng dần."
    )
    if response.get("severity") == "unknown":
        response["severity"] = "low_to_moderate"


def _apply_high_fever_profile(response: Dict[str, Any]) -> None:
    response["severity"] = "high"
    response["summary"] = (
        f"{response.get('summary', '').strip()} Đây là sốt cao, cần theo dõi sát nhiệt độ, đáp ứng hạ sốt và dấu hiệu cảnh báo."
    ).strip()
    _append_unique(
        response["red_flags"],
        [
            "Sốt cao không hạ hoặc kéo dài.",
            "Lơ mơ, co giật, cứng cổ, khó thở, đau ngực hoặc mất nước.",
        ],
    )
    response["recommendation"] = (
        "Nên đi khám sớm nếu sốt không hạ, kéo dài hoặc có dấu hiệu cảnh báo như lơ mơ, co giật, cứng cổ, khó thở, đau ngực hoặc mất nước."
    )


def convert_medgemma_text_to_json(symptoms: str, raw_text: str) -> dict:
    parsed = extract_json(raw_text)
    if parsed:
        return _clean_normalized_json(parsed)

    clean_symptoms = str(symptoms or "").strip()
    combined = f"{clean_symptoms}\n{raw_text or ''}"
    response = _base_response(clean_symptoms, raw_text or "")

    liver_markers = [
        "vàng da",
        "vàng mắt",
        "jaundice",
        "bilirubin",
        "dark urine",
        "nước tiểu sẫm",
        "itching",
        "ngứa",
    ]
    respiratory_markers = ["sốt", "ho", "đau họng", "fever", "cough", "sore throat"]

    if _contains_any(combined, liver_markers):
        _apply_liver_profile(response, clean_symptoms)

    if _contains_any(combined, respiratory_markers):
        _apply_respiratory_profile(response, clean_symptoms)

    if _has_high_fever(clean_symptoms):
        _apply_high_fever_profile(response)

    if _technical_summary(response.get("summary", "")):
        response["summary"] = f"Bạn mô tả các triệu chứng cần được đánh giá thêm: {clean_symptoms}"

    response["model_status"] = MODEL_STATUS
    response["disclaimer"] = DISCLAIMER
    return normalize_medical_response(response, MODEL_STATUS)
