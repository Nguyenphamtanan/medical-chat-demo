import re
import unicodedata
from typing import Any, Dict, List, Optional

from .medgemma_service import MedGemmaService


DISCLAIMER = (
    "Thông tin này chỉ hỗ trợ tham khảo, không thay thế chẩn đoán hoặc điều trị của bác sĩ."
)

HEADING_ALIASES = {
    "summary": {"TOM TAT"},
    "systems": {"HE CO QUAN", "HE CO QUAN LIEN QUAN"},
    "red_flags": {"DAU HIEU CANH BAO"},
    "missing_data": {"THONG TIN CON THIEU"},
    "recommendation": {"KHUYEN NGHI"},
    "note": {"LUU Y"},
}


def _strip_accents(text: str) -> str:
    source = str(text or "").replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", source)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _searchable(text: str) -> str:
    text = _strip_accents(text).upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _append_unique(items: List[str], values: List[str]) -> None:
    seen = {_searchable(item) for item in items}
    for value in values:
        clean = str(value or "").strip()
        key = _searchable(clean)
        if clean and key and key not in seen:
            items.append(clean)
            seen.add(key)


def _contains_any(text: str, keywords: List[str]) -> bool:
    haystack = _searchable(text)
    return any(_searchable(keyword) in haystack for keyword in keywords)


def _number_after(label: str, text: str) -> Optional[float]:
    pattern = rf"{re.escape(label)}\s*[:=]?\s*(\d+(?:[.,]\d+)?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _find_first_valid_section(text: str) -> Optional[int]:
    offset = 0
    for line in str(text or "").splitlines(keepends=True):
        if _canonical_heading(line) in {"summary", "systems"}:
            return offset
        offset += len(line)
    return None


def clean_medgemma_output(text: str) -> str:
    cleaned = str(text or "").strip()
    has_thought_marker = bool(re.search(r"<unused\d+>\s*thought", cleaned, flags=re.IGNORECASE))
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")

    first_section = _find_first_valid_section(cleaned)
    if has_thought_marker:
        if first_section is not None:
            cleaned = cleaned[first_section:]
        else:
            cleaned = re.sub(
                r"(?is)^.*?<unused\d+>\s*thought\s*.*?(?:\n\s*\n|$)",
                "",
                cleaned,
                count=1,
            )
    elif first_section is not None:
        cleaned = cleaned[first_section:]

    cleaned = re.sub(r"<unused\d+>\s*thought", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?is)<thought>.*?</thought>", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*(thought|analysis|reasoning)\s*:.*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if _find_first_valid_section(cleaned) is None:
        return cleaned[:1200].strip()

    return cleaned[:1600].strip()


def _normalize_system_items(items: List[str]) -> List[str]:
    mapping = {
        "TIM MACH": "tim mạch",
        "THAN": "thận",
        "HO HAP": "hô hấp",
        "TIEU HOA": "tiêu hóa",
        "GAN MAT": "gan mật",
        "NOI TIET": "nội tiết",
        "THAN KINH": "thần kinh",
    }
    normalized = []
    for item in items:
        key = _searchable(item)
        normalized.append(mapping.get(key, item))
    deduped: List[str] = []
    _append_unique(deduped, normalized)
    return deduped


def _canonical_heading(line: str) -> Optional[str]:
    clean = _searchable(line.split(":", 1)[0])
    for section, aliases in HEADING_ALIASES.items():
        if clean in aliases:
            return section
    return None


def _split_sections(text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = None

    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = _canonical_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            after_colon = line.split(":", 1)[1].strip() if ":" in line else ""
            if after_colon:
                sections[current].append(after_colon)
            continue

        if current:
            sections.setdefault(current, []).append(line)

    return sections


def _lines_to_items(lines: List[str]) -> List[str]:
    items = []
    for line in lines:
        clean = re.sub(r"^\s*[-*•]\s*", "", line).strip()
        if clean:
            items.append(clean)
    return items


def _section_text(lines: List[str]) -> str:
    items = _lines_to_items(lines)
    return " ".join(items).strip()


def _has_specific_content(text: str) -> bool:
    return len(str(text or "").strip()) >= 30


def _augment_medical_safety(result: Dict[str, Any], source_text: str) -> None:
    text = source_text or ""
    searchable = _searchable(text)
    red_flags = result["red_flags"]
    systems = result["likely_systems"]

    potassium = _number_after("potassium", text) or _number_after("kali", text)
    creatinine = _number_after("creatinine", text)
    egfr = _number_after("egfr", text)
    bnp = _number_after("bnp", text)

    heart_or_fluid = (
        (bnp is not None and bnp >= 400)
        or _contains_any(text, ["khó thở khi nằm", "kho tho khi nam", "phù chân", "phu chan", "phù hai chân", "dịch màng phổi", "dich mang phoi"])
    )
    kidney_risk = (
        (creatinine is not None and creatinine >= 2)
        or (egfr is not None and egfr <= 30)
        or _contains_any(text, ["tiểu ít", "tieu it", "bệnh thận mạn", "benh than man"])
    )
    respiratory_risk = _contains_any(
        text,
        ["khó thở", "kho tho", "thâm nhiễm đáy phổi", "tham nhiem day phoi", "dịch màng phổi", "dich mang phoi"],
    )

    if heart_or_fluid:
        _append_unique(systems, ["tim mạch"])
        _append_unique(
            red_flags,
            [
                "Khó thở khi nằm, phù chân, BNP cao hoặc dịch màng phổi có thể gợi ý suy tim/quá tải dịch và cần được đánh giá sớm.",
            ],
        )

    if kidney_risk:
        _append_unique(systems, ["thận"])
        _append_unique(
            red_flags,
            [
                "Tiểu ít kèm creatinine cao hoặc eGFR thấp có thể là bệnh thận nặng hơn hoặc tổn thương thận cấp trên nền bệnh thận mạn.",
            ],
        )

    if respiratory_risk:
        _append_unique(systems, ["hô hấp"])

    if potassium is not None and potassium >= 5.5:
        _append_unique(
            red_flags,
            [
                "Tăng kali máu là dấu hiệu nguy hiểm, đặc biệt nếu có yếu liệt, hồi hộp, đau ngực, ngất hoặc mệt lả.",
            ],
        )

    if _contains_any(text, ["đau ngực", "dau nguc", "tức ngực", "tuc nguc"]):
        _append_unique(red_flags, ["Đau hoặc tức ngực, nhất là khi tăng lên hoặc đi kèm khó thở, cần được đánh giá khẩn."])

    if _contains_any(text, ["khó thở khi nghỉ", "kho tho khi nghi", "tím môi", "tim moi", "ngất", "ngat", "lú lẫn", "lu lan"]):
        _append_unique(
            red_flags,
            ["Khó thở khi nghỉ, tím môi, ngất hoặc lú lẫn là dấu hiệu cần đi cấp cứu ngay."],
        )

    if heart_or_fluid and kidney_risk and potassium is not None and potassium >= 5.5:
        _append_unique(
            red_flags,
            [
                "Nên đi khám cấp cứu hoặc khám trong ngày, đặc biệt nếu khó thở tăng, đau ngực, yếu liệt, hồi hộp hoặc ngất.",
            ],
        )

    if "BNP 780" in searchable or (bnp is not None and bnp >= 700):
        _append_unique(result["missing_data"], ["Dấu hiệu sinh tồn, SpO2, ECG, troponin, điện giải lặp lại và mức độ đáp ứng với lợi tiểu."])

    result["likely_systems"] = _normalize_system_items(result["likely_systems"])


def parse_fast_chat_text(text: str, model_status: str = "medgemma_fast_text_parsed") -> Dict[str, Any]:
    cleaned = clean_medgemma_output(text)
    sections = _split_sections(cleaned)
    found_any_section = bool(sections)

    summary = _section_text(sections.get("summary", []))
    recommendation = _section_text(sections.get("recommendation", []))
    answer = " ".join(part for part in [summary, recommendation] if part).strip()

    if not found_any_section:
        print("[FAST_CHAT] Parser fallback used.")
        answer = cleaned[:700].strip()

    if not _has_specific_content(answer):
        answer = cleaned[:700].strip()

    result = {
        "answer": answer,
        "red_flags": _lines_to_items(sections.get("red_flags", [])) if found_any_section else [],
        "missing_data": _lines_to_items(sections.get("missing_data", [])) if found_any_section else [],
        "likely_systems": _lines_to_items(sections.get("systems", [])) if found_any_section else [],
        "confidence_note": _section_text(sections.get("note", []))
        if found_any_section
        else "Không tách được đầy đủ cấu trúc, hiển thị phản hồi đã làm sạch từ MedGemma.",
        "model_status": model_status if found_any_section else "medgemma_fast_text_fallback",
        "disclaimer": DISCLAIMER,
    }

    if not result["confidence_note"]:
        result["confidence_note"] = DISCLAIMER

    _augment_medical_safety(result, cleaned)
    return result


def _history_text(history) -> str:
    if not history:
        return "Không có."

    lines = []
    for item in history[-5:]:
        role = "Người dùng" if item.role == "user" else "Trợ lý"
        lines.append(f"{role}: {item.content.strip()[:500]}")
    return "\n".join(lines)


def build_fast_prompt(message: str, history) -> str:
    return f"""
Bạn là trợ lý phân loại y tế an toàn, không xưng là bác sĩ.
Trả lời tiếng Việt ngắn gọn theo đúng các mục dưới đây, không dùng code block, không giải thích suy luận dài.
Nội dung chỉ hỗ trợ tham khảo, không thay thế chẩn đoán của bác sĩ.

Lịch sử gần đây:
{_history_text(history)}

Người dùng:
{message}

TÓM TẮT:

HỆ CƠ QUAN LIÊN QUAN:
-

DẤU HIỆU CẢNH BÁO:
-

THÔNG TIN CÒN THIẾU:
-

KHUYẾN NGHỊ:

LƯU Ý:
""".strip()


def _local_unavailable_response(message: str, model_status: str) -> Dict[str, Any]:
    text = f"""
TÓM TẮT:
{message[:500]}

HỆ CƠ QUAN LIÊN QUAN:
- Cần đánh giá theo triệu chứng và dữ liệu người dùng cung cấp

DẤU HIỆU CẢNH BÁO:
- Nếu khó thở, đau ngực, ngất, lú lẫn, tím môi hoặc triệu chứng xấu đi nhanh thì cần đi cấp cứu.

THÔNG TIN CÒN THIẾU:
- Thời điểm khởi phát, dấu hiệu sinh tồn, mức độ nặng, bệnh nền, thuốc đang dùng và kết quả xét nghiệm liên quan.

KHUYẾN NGHỊ:
MedGemma chưa sẵn sàng trong môi trường hiện tại, nên chỉ hiển thị tóm tắt đầu vào và các cảnh báo an toàn dựa trên dữ liệu đã nhập.

LƯU Ý:
{DISCLAIMER}
""".strip()
    return parse_fast_chat_text(text, model_status)


class FastChatService:
    def __init__(self):
        self.med = MedGemmaService()

    def chat(self, request):
        clean_message = request.message.strip()
        prompt = build_fast_prompt(clean_message, request.history[-5:])
        raw = self.med.generate(prompt, max_new_tokens=220)

        if "error" in raw:
            return _local_unavailable_response(
                clean_message,
                raw.get("status", "ai_service_unavailable"),
            )

        raw_text = raw.get("text", "")
        cleaned = clean_medgemma_output(raw_text)

        print("========== CLEANED MEDGEMMA OUTPUT ==========")
        print(cleaned)
        print("=============================================")

        parsed = parse_fast_chat_text(
            cleaned,
            raw.get("status", "medgemma_fast_text_parsed"),
        )
        parsed["model_status"] = (
            "medgemma_fast_text_parsed"
            if parsed["model_status"] != "medgemma_fast_text_fallback"
            else parsed["model_status"]
        )
        return parsed

    def health(self):
        self.med._refresh_env()
        return {
            "model_loaded": self.med.pipe is not None,
            "model_status": self.med.status,
        }
