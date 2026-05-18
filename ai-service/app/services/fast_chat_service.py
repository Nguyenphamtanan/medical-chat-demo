import re
import unicodedata
from typing import Any, Dict, List, Optional

from .medgemma_service import MedGemmaService


DISCLAIMER = (
    "Thông tin này chỉ hỗ trợ tham khảo, không thay thế chẩn đoán hoặc điều trị của bác sĩ."
)

HEADING_ALIASES = {
    "summary": ("TOM TAT",),
    "systems": ("HE CO QUAN", "HE CO QUAN LIEN QUAN"),
    "red_flags": ("DAU HIEU CANH BAO",),
    "missing_data": ("THONG TIN CON THIEU", "THONG TIN CON THIE"),
    "recommendation": ("KHUYEN NGHI",),
    "note": ("LUU Y",),
}

SYSTEM_KEYWORDS = [
    (
        ["ho", "rat co", "dau hong", "sore throat", "throat", "larynx", "cough"],
        ["hô hấp / tai mũi họng"],
    ),
    (["kho tho", "dyspnea"], ["hô hấp", "tim mạch"]),
    (["dau nguc", "tuc nguc", "chest tightness", "chest pain"], ["tim mạch", "hô hấp"]),
    (["phu chan", "bnp", "orthopnea", "kho tho khi nam"], ["tim mạch"]),
    (["creatinine", "egfr", "potassium", "kali", "tieu it"], ["thận"]),
]


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


def _remove_line_prefix(line: str) -> str:
    clean = str(line or "").strip()
    clean = re.sub(r"^\s*(?:[-*•]\s*)?(?:\d+[\.)]\s*)?", "", clean)
    clean = clean.replace("**", "")
    return clean.strip()


def _canonical_heading(line: str) -> Optional[str]:
    clean_line = _remove_line_prefix(line)
    heading_part = clean_line.split(":", 1)[0]
    heading_key = _searchable(heading_part)

    for section, aliases in HEADING_ALIASES.items():
        for alias in aliases:
            if heading_key == alias or heading_key.startswith(alias):
                return section

    return None


def _find_first_valid_section(text: str) -> Optional[int]:
    offset = 0
    for line in str(text or "").splitlines(keepends=True):
        if _canonical_heading(line) in {"summary", "systems", "red_flags", "missing_data", "recommendation"}:
            return offset
        offset += len(line)
    return None


def clean_medgemma_output(text: str) -> str:
    cleaned = str(text or "").strip()
    has_thought_marker = bool(re.search(r"<unused\d+>\s*thought", cleaned, flags=re.IGNORECASE))

    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")

    first_section = _find_first_valid_section(cleaned)
    if has_thought_marker and first_section is not None:
        cleaned = cleaned[first_section:]
    elif has_thought_marker:
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
    cleaned = cleaned.replace("**", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if _find_first_valid_section(cleaned) is None:
        return cleaned[:1200].strip()

    return cleaned[:1600].strip()


def _normalize_system_items(items: List[str]) -> List[str]:
    mapping = {
        "TIM MACH": "tim mạch",
        "THAN": "thận",
        "HO HAP": "hô hấp",
        "TAI MUI HONG": "tai mũi họng",
        "HO HAP TAI MUI HONG": "hô hấp / tai mũi họng",
        "TIEU HOA": "tiêu hóa",
        "GAN MAT": "gan mật",
        "NOI TIET": "nội tiết",
        "THAN KINH": "thần kinh",
    }
    normalized = []
    for item in items:
        key = _searchable(item)
        inferred = _infer_systems_from_keywords(item)
        if inferred:
            normalized.extend(inferred)
        else:
            normalized.append(mapping.get(key, item))
    deduped: List[str] = []
    _append_unique(deduped, normalized)
    return deduped


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
            clean_line = _remove_line_prefix(line)
            after_colon = clean_line.split(":", 1)[1].strip() if ":" in clean_line else ""
            if after_colon:
                sections[current].append(after_colon)
            continue

        if current:
            sections.setdefault(current, []).append(line)

    return sections


def _lines_to_items(lines: List[str]) -> List[str]:
    items = []
    for line in lines:
        clean = _remove_line_prefix(line)
        clean = re.sub(r"^\s*[-*•]\s*", "", clean).strip()
        if clean:
            items.append(clean)
    return items


def _section_text(lines: List[str]) -> str:
    items = _lines_to_items(lines)
    return " ".join(items).strip()


def _infer_systems_from_keywords(text: str) -> List[str]:
    systems: List[str] = []
    for keywords, values in SYSTEM_KEYWORDS:
        if _contains_any(text, keywords):
            _append_unique(systems, values)
    return systems


def _default_red_flags_for_systems(systems: List[str]) -> List[str]:
    joined = _searchable(" ".join(systems))
    flags: List[str] = []
    if "HO HAP" in joined or "TAI MUI HONG" in joined:
        _append_unique(
            flags,
            [
                "Theo dõi và đi khám sớm nếu xuất hiện khó thở, sốt cao kéo dài, đau ngực, nuốt khó, khàn tiếng tăng nhanh hoặc triệu chứng nặng dần.",
            ],
        )
    if "TIM MACH" in joined:
        _append_unique(flags, ["Đau ngực, khó thở tăng, hồi hộp, ngất hoặc phù tăng nhanh là dấu hiệu cần đánh giá khẩn."])
    if "THAN" in joined:
        _append_unique(flags, ["Tiểu ít, phù tăng, mệt lả hoặc kali máu cao là dấu hiệu cần đi khám sớm."])
    return flags


def _fallback_answer_from_keywords(source_text: str, systems: List[str]) -> str:
    searchable = _searchable(source_text)
    if "HO" in searchable or "RAT CO" in searchable or "DAU HONG" in searchable or "SORE THROAT" in searchable:
        return (
            "Triệu chứng ho và rát/đau cổ họng trong vài ngày thường liên quan đến đường hô hấp trên hoặc tai mũi họng. "
            "Bạn nên theo dõi thêm sốt, khó thở, đau ngực, nuốt khó hoặc triệu chứng nặng dần."
        )
    if systems:
        return f"Các thông tin bạn cung cấp gợi ý cần chú ý đến: {', '.join(systems)}. Nên theo dõi dấu hiệu cảnh báo và đi khám nếu triệu chứng nặng lên."
    return ""


def _build_answer_from_sections(sections: Dict[str, List[str]]) -> str:
    summary = _section_text(sections.get("summary", []))
    recommendation = _section_text(sections.get("recommendation", []))
    if summary or recommendation:
        return " ".join(part for part in [summary, recommendation] if part).strip()

    pieces = []
    for key in ["systems", "red_flags", "missing_data", "note"]:
        text = _section_text(sections.get(key, []))
        if text:
            pieces.append(text)
    return " ".join(pieces).strip()


def _augment_medical_safety(
    result: Dict[str, Any],
    source_text: str,
    system_source_text: str = "",
) -> None:
    text = source_text or ""
    system_text = system_source_text or text
    searchable = _searchable(text)
    red_flags = result["red_flags"]
    systems = result["likely_systems"]

    _append_unique(systems, _infer_systems_from_keywords(system_text))

    potassium = _number_after("potassium", text) or _number_after("kali", text)
    creatinine = _number_after("creatinine", text)
    egfr = _number_after("egfr", text)
    bnp = _number_after("bnp", text)

    heart_or_fluid = (
        (bnp is not None and bnp >= 400)
        or _contains_any(text, ["khó thở khi nằm", "kho tho khi nam", "phù chân", "phu chan", "phù hai chân", "dịch màng phổi", "dich mang phoi", "orthopnea"])
    )
    kidney_risk = (
        (creatinine is not None and creatinine >= 2)
        or (egfr is not None and egfr <= 30)
        or _contains_any(text, ["tiểu ít", "tieu it", "bệnh thận mạn", "benh than man"])
    )

    if heart_or_fluid:
        _append_unique(systems, ["tim mạch"])
        _append_unique(red_flags, ["Khó thở khi nằm, phù chân, BNP cao hoặc dịch màng phổi có thể gợi ý suy tim/quá tải dịch và cần được đánh giá sớm."])

    if kidney_risk:
        _append_unique(systems, ["thận"])
        _append_unique(red_flags, ["Tiểu ít kèm creatinine cao hoặc eGFR thấp có thể là bệnh thận nặng hơn hoặc tổn thương thận cấp trên nền bệnh thận mạn."])

    if potassium is not None and potassium >= 5.5:
        _append_unique(red_flags, ["Tăng kali máu là dấu hiệu nguy hiểm, đặc biệt nếu có yếu liệt, hồi hộp, đau ngực, ngất hoặc mệt lả."])

    if _contains_any(text, ["đau ngực", "dau nguc", "tức ngực", "tuc nguc", "chest pain", "chest tightness"]):
        _append_unique(red_flags, ["Đau hoặc tức ngực, nhất là khi tăng lên hoặc đi kèm khó thở, cần được đánh giá khẩn."])

    if _contains_any(text, ["khó thở khi nghỉ", "kho tho khi nghi", "tím môi", "tim moi", "ngất", "ngat", "lú lẫn", "lu lan"]):
        _append_unique(red_flags, ["Khó thở khi nghỉ, tím môi, ngất hoặc lú lẫn là dấu hiệu cần đi cấp cứu ngay."])

    if heart_or_fluid and kidney_risk and potassium is not None and potassium >= 5.5:
        _append_unique(red_flags, ["Nên đi khám cấp cứu hoặc khám trong ngày, đặc biệt nếu khó thở tăng, đau ngực, yếu liệt, hồi hộp hoặc ngất."])

    if "BNP 780" in searchable or (bnp is not None and bnp >= 700):
        _append_unique(result["missing_data"], ["Dấu hiệu sinh tồn, SpO2, ECG, troponin, điện giải lặp lại và mức độ đáp ứng với lợi tiểu."])

    if not red_flags:
        _append_unique(red_flags, _default_red_flags_for_systems(systems))

    result["likely_systems"] = _normalize_system_items(result["likely_systems"])


def parse_fast_chat_text(
    text: str,
    model_status: str = "medgemma_fast_text_parsed",
    source_context: str = "",
) -> Dict[str, Any]:
    cleaned = clean_medgemma_output(text)
    combined_context = f"{cleaned}\n{source_context}".strip()
    sections = _split_sections(cleaned)
    found_any_section = bool(sections)

    section_system_text = _section_text(sections.get("systems", []))
    likely_systems = _lines_to_items(sections.get("systems", [])) if found_any_section else []
    _append_unique(likely_systems, _infer_systems_from_keywords(f"{section_system_text}\n{source_context}"))

    answer = _build_answer_from_sections(sections) if found_any_section else ""

    if found_any_section and "summary" not in sections and "recommendation" not in sections:
        answer = _fallback_answer_from_keywords(
            f"{section_system_text}\n{source_context}",
            likely_systems,
        ) or answer

    if not answer:
        answer = _fallback_answer_from_keywords(combined_context, likely_systems)

    fallback_used = False
    if not answer:
        fallback_used = True
        print("[FAST_CHAT] Parser fallback used.")
        answer = cleaned[:700].strip()

    result = {
        "answer": answer,
        "red_flags": _lines_to_items(sections.get("red_flags", [])) if found_any_section else [],
        "missing_data": _lines_to_items(sections.get("missing_data", [])) if found_any_section else [],
        "likely_systems": likely_systems,
        "confidence_note": _section_text(sections.get("note", [])) if found_any_section else "",
        "model_status": "medgemma_fast_text_fallback" if fallback_used else model_status,
        "disclaimer": DISCLAIMER,
    }

    if not result["confidence_note"]:
        result["confidence_note"] = (
            "Phản hồi được chuẩn hóa từ nội dung MedGemma và các dấu hiệu an toàn trong đầu vào."
        )

    _augment_medical_safety(
        result,
        combined_context,
        system_source_text=f"{section_system_text}\n{source_context}",
    )
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
    return parse_fast_chat_text(text, model_status, source_context=message)


class FastChatService:
    def __init__(self):
        self.med = MedGemmaService()

    def chat(self, request):
        clean_message = request.message.strip()
        prompt = build_fast_prompt(clean_message, request.history[-5:])
        raw = self.med.generate(prompt, max_new_tokens=160)

        if "error" in raw:
            parsed = _local_unavailable_response(
                clean_message,
                raw.get("status", "ai_service_unavailable"),
            )
            print("========== PARSED FAST CHAT OUTPUT ==========")
            print(parsed)
            print("=============================================")
            return parsed

        raw_text = raw.get("text", "")
        cleaned = clean_medgemma_output(raw_text)

        print("========== CLEANED MEDGEMMA OUTPUT ==========")
        print(cleaned)
        print("=============================================")

        parsed = parse_fast_chat_text(
            cleaned,
            raw.get("status", "medgemma_fast_text_parsed"),
            source_context=clean_message,
        )
        parsed["model_status"] = (
            "medgemma_fast_text_parsed"
            if parsed["model_status"] != "medgemma_fast_text_fallback"
            else parsed["model_status"]
        )

        print("========== PARSED FAST CHAT OUTPUT ==========")
        print(parsed)
        print("=============================================")
        return parsed

    def health(self):
        self.med._refresh_env()
        return {
            "model_loaded": self.med.pipe is not None,
            "model_status": self.med.status,
        }
