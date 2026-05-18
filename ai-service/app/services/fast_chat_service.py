import re
import unicodedata
from typing import Any, Dict, List, Optional

from .medgemma_service import MedGemmaService


DISCLAIMER = (
    "Thông tin này chỉ hỗ trợ tham khảo, không thay thế chẩn đoán hoặc điều trị của bác sĩ."
)

CASE_TYPES = {
    "upper_respiratory": {
        "keywords": ["ho", "đau họng", "rát cổ", "khàn tiếng", "sore throat", "cough", "throat", "larynx"],
        "systems": ["hô hấp", "tai mũi họng"],
        "red_flags": ["khó thở", "sốt cao kéo dài", "đau ngực", "nuốt khó", "ho ra máu", "triệu chứng nặng dần"],
        "missing_data": ["thời gian triệu chứng", "có sốt không", "có khó thở không", "có đờm/ho ra máu không"],
    },
    "hepatobiliary": {
        "keywords": ["vàng da", "jaundice", "bilirubin", "nước tiểu sẫm", "phân bạc màu", "ngứa toàn thân"],
        "systems": ["gan mật", "tiêu hóa"],
        "red_flags": ["vàng da tăng nhanh", "đau bụng dữ dội", "sốt", "lơ mơ", "nôn nhiều", "nước tiểu sẫm màu"],
        "missing_data": ["thời gian vàng da", "màu nước tiểu/phân", "đau hạ sườn phải", "sốt", "xét nghiệm AST/ALT/bilirubin"],
    },
    "cardiorespiratory": {
        "keywords": ["khó thở", "đau ngực", "tức ngực", "phù chân", "orthopnea", "BNP", "dịch màng phổi"],
        "systems": ["tim mạch", "hô hấp"],
        "red_flags": ["khó thở khi nghỉ", "đau ngực", "tím môi", "ngất", "phù tăng nhanh", "SpO2 thấp"],
        "missing_data": ["SpO2", "huyết áp", "mạch", "ECG", "troponin", "BNP", "X-quang"],
    },
    "renal": {
        "keywords": ["tiểu ít", "creatinine", "eGFR", "potassium", "kali", "phù", "bệnh thận"],
        "systems": ["thận"],
        "red_flags": ["tiểu rất ít/vô niệu", "tăng kali máu", "yếu liệt", "hồi hộp", "ngất", "phù tăng"],
        "missing_data": ["lượng nước tiểu", "creatinine/eGFR", "kali", "thuốc đang dùng", "huyết áp"],
    },
    "neuro_emergency": {
        "keywords": ["méo miệng", "yếu liệt", "nói khó", "lú lẫn", "đột ngột", "stroke", "seizure"],
        "systems": ["thần kinh", "tim mạch"],
        "red_flags": ["méo miệng", "yếu liệt", "nói khó", "lú lẫn", "đau đầu dữ dội đột ngột"],
        "missing_data": ["thời điểm khởi phát", "yếu bên nào", "nói khó không", "huyết áp", "thuốc chống đông"],
    },
    "gastrointestinal": {
        "keywords": ["đau bụng", "buồn nôn", "nôn", "tiêu chảy", "phân đen", "đau thượng vị", "melena"],
        "systems": ["tiêu hóa"],
        "red_flags": ["đau bụng dữ dội", "nôn liên tục", "phân đen", "nôn ra máu", "sốt cao", "mất nước"],
        "missing_data": ["vị trí đau", "thời gian", "sốt", "phân", "nôn", "thuốc đang dùng"],
    },
    "general": {
        "keywords": [],
        "systems": [],
        "red_flags": ["triệu chứng nặng dần", "ngất", "khó thở", "đau ngực", "lú lẫn"],
        "missing_data": ["tuổi", "thời gian triệu chứng", "bệnh nền", "thuốc đang dùng", "mức độ nặng"],
    },
}

HEADING_ALIASES = {
    "summary": ("TOM TAT",),
    "systems": ("HE CO QUAN", "HE CO QUAN LIEN QUAN"),
    "red_flags": ("DAU HIEU CANH BAO",),
    "missing_data": ("THONG TIN CON THIEU", "THONG TIN CON THIE"),
    "recommendation": ("KHUYEN NGHI",),
    "note": ("LUU Y",),
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
    for keyword in keywords:
        needle = _searchable(keyword)
        if not needle:
            continue
        pattern = rf"(?<![A-Z0-9]){re.escape(needle)}(?![A-Z0-9])"
        if re.search(pattern, haystack):
            return True
    return False


def _context_text(message: str, patient_context: Optional[Dict[str, Any]] = None) -> str:
    if not patient_context:
        return message or ""
    context_parts = [message or ""]
    for key, value in patient_context.items():
        if isinstance(value, (str, int, float, bool)):
            context_parts.append(f"{key}: {value}")
        elif isinstance(value, list):
            context_parts.append(f"{key}: " + ", ".join(str(item) for item in value))
    return "\n".join(part for part in context_parts if str(part).strip())


def detect_case_types(message: str, patient_context: Optional[Dict[str, Any]] = None) -> List[str]:
    text = _context_text(message, patient_context)
    detected = [
        case_type
        for case_type, spec in CASE_TYPES.items()
        if case_type != "general" and _contains_any(text, spec["keywords"])
    ]
    return detected or ["general"]


def _taxonomy_values(case_types: List[str], field: str) -> List[str]:
    values: List[str] = []
    for case_type in case_types:
        _append_unique(values, CASE_TYPES.get(case_type, CASE_TYPES["general"]).get(field, []))
    return values


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
        if any(heading_key == alias or heading_key.startswith(alias) for alias in aliases):
            return section
    return None


def _find_first_valid_section(text: str) -> Optional[int]:
    offset = 0
    for line in str(text or "").splitlines(keepends=True):
        if _canonical_heading(line):
            return offset
        offset += len(line)
    return None


def clean_medgemma_output(text: str) -> str:
    cleaned = str(text or "").strip()
    has_thought_marker = bool(re.search(r"<unused\d+>\s*thought", cleaned, flags=re.IGNORECASE))
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE).replace("```", "")

    first_section = _find_first_valid_section(cleaned)
    if first_section is not None:
        cleaned = cleaned[first_section:]
    elif has_thought_marker:
        cleaned = re.sub(
            r"(?is)^.*?<unused\d+>\s*thought\s*.*?(?:\n\s*\n|$)",
            "",
            cleaned,
            count=1,
        )

    cleaned = re.sub(r"<unused\d+>\s*thought", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?is)<thought>.*?</thought>", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*(thought|analysis|reasoning)\s*:.*$", "", cleaned)
    cleaned = cleaned.replace("**", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:1600].strip() if _find_first_valid_section(cleaned) is not None else cleaned[:1200].strip()


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
        clean = re.sub(r"^\s*[-*•]\s*", "", _remove_line_prefix(line)).strip()
        if clean:
            items.append(clean)
    return items


def _section_text(lines: List[str]) -> str:
    return " ".join(_lines_to_items(lines)).strip()


def _build_answer_from_sections(sections: Dict[str, List[str]]) -> str:
    summary = _section_text(sections.get("summary", []))
    recommendation = _section_text(sections.get("recommendation", []))
    if summary or recommendation:
        return " ".join(part for part in [summary, recommendation] if part).strip()
    pieces = [_section_text(sections.get(key, [])) for key in ["systems", "red_flags", "missing_data", "note"]]
    return " ".join(piece for piece in pieces if piece).strip()


def _system_relevance_map() -> Dict[str, List[str]]:
    relevance: Dict[str, List[str]] = {}
    for case_type, spec in CASE_TYPES.items():
        if case_type == "general":
            continue
        for system in spec["systems"]:
            relevance.setdefault(system, []).append(case_type)
    return relevance


def _filter_relevant_systems(systems: List[str], case_types: List[str]) -> List[str]:
    if "general" in case_types:
        return systems
    relevance = _system_relevance_map()
    filtered = []
    for system in systems:
        key = system.strip()
        relevant_cases = relevance.get(key, [])
        if any(case_type in relevant_cases for case_type in case_types):
            filtered.append(system)
    return filtered


def _domain_terms_for_cases(case_types: List[str]) -> List[str]:
    terms: List[str] = []
    for case_type in case_types:
        spec = CASE_TYPES.get(case_type, CASE_TYPES["general"])
        _append_unique(terms, spec["keywords"] + spec["systems"])
    return terms


def validate_answer_consistency(answer: str, case_types: List[str], message: str) -> bool:
    if not answer.strip() or "general" in case_types:
        return True

    answer_domains = set(detect_case_types(answer))
    current_domains = set(case_types)
    if answer_domains != {"general"} and answer_domains.isdisjoint(current_domains):
        return False

    current_terms = _domain_terms_for_cases(case_types)
    answer_has_current_signal = _contains_any(answer, current_terms)
    message_has_current_signal = _contains_any(message, current_terms)
    return answer_has_current_signal or not message_has_current_signal


def _neutral_answer(case_types: List[str]) -> str:
    systems = _taxonomy_values(case_types, "systems")
    system_text = ", ".join(systems) if systems else "các hệ cơ quan liên quan"
    return (
        f"Triệu chứng bạn mô tả có thể liên quan đến: {system_text}. "
        "Cần đánh giá thêm dựa trên thời gian xuất hiện, mức độ nặng, bệnh nền, thuốc đang dùng và dấu hiệu cảnh báo."
    )


def repair_response_if_needed(parsed: Dict[str, Any], case_types: List[str], message: str) -> Dict[str, Any]:
    repaired = {
        **parsed,
        "red_flags": list(parsed.get("red_flags", [])),
        "missing_data": list(parsed.get("missing_data", [])),
        "likely_systems": list(parsed.get("likely_systems", [])),
    }

    mismatch = not validate_answer_consistency(repaired.get("answer", ""), case_types, message)
    if mismatch:
        repaired["answer"] = _neutral_answer(case_types)
        repaired["model_status"] = f"{repaired.get('model_status', 'unknown')}_domain_repaired"

    _append_unique(repaired["likely_systems"], _taxonomy_values(case_types, "systems"))
    repaired["likely_systems"] = _filter_relevant_systems(repaired["likely_systems"], case_types)
    _append_unique(repaired["red_flags"], _taxonomy_values(case_types, "red_flags"))
    _append_unique(repaired["missing_data"], _taxonomy_values(case_types, "missing_data"))
    repaired["disclaimer"] = DISCLAIMER
    return repaired


def parse_fast_chat_text(
    text: str,
    model_status: str = "medgemma_fast_text_parsed",
) -> Dict[str, Any]:
    cleaned = clean_medgemma_output(text)
    sections = _split_sections(cleaned)
    found_any_section = bool(sections)
    answer = _build_answer_from_sections(sections) if found_any_section else cleaned[:700].strip()

    if not found_any_section:
        print("[FAST_CHAT] Parser fallback used.")

    return {
        "answer": answer,
        "red_flags": _lines_to_items(sections.get("red_flags", [])) if found_any_section else [],
        "missing_data": _lines_to_items(sections.get("missing_data", [])) if found_any_section else [],
        "likely_systems": _lines_to_items(sections.get("systems", [])) if found_any_section else [],
        "confidence_note": _section_text(sections.get("note", [])) if found_any_section else "Không tách được đầy đủ cấu trúc, hiển thị phản hồi đã làm sạch từ MedGemma.",
        "model_status": model_status if found_any_section else "medgemma_fast_text_fallback",
        "disclaimer": DISCLAIMER,
    }


def _history_text(history) -> str:
    if not history:
        return "Không có."
    lines = []
    for item in history[-5:]:
        role = "Người dùng" if item.role == "user" else "Trợ lý"
        lines.append(f"{role}: {item.content.strip()[:500]}")
    return "\n".join(lines)


def build_prompt(message: str, history, case_types: List[str]) -> str:
    systems = ", ".join(_taxonomy_values(case_types, "systems")) or "chưa rõ"
    red_flags = ", ".join(_taxonomy_values(case_types, "red_flags")[:6])
    missing_data = ", ".join(_taxonomy_values(case_types, "missing_data")[:6])
    return f"""
Bạn là trợ lý phân loại y tế an toàn, không xưng là bác sĩ.
Trả lời tiếng Việt ngắn gọn theo đúng các mục dưới đây.
Không viết chain-of-thought, không dùng code block, không trả JSON.
Tập trung vào ca hiện tại; lịch sử chỉ để hiểu ngữ cảnh, không thay thế triệu chứng hiện tại.

Nhóm ca gợi ý: {", ".join(case_types)}
Hệ cần cân nhắc: {systems}
Dấu hiệu cảnh báo cần kiểm tra: {red_flags}
Dữ liệu còn thiếu thường cần hỏi: {missing_data}

Lịch sử gần đây:
{_history_text(history)}

Ca hiện tại:
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


def build_fast_prompt(message: str, history) -> str:
    return build_prompt(message, history, detect_case_types(message))


def _local_unavailable_response(message: str, case_types: List[str], model_status: str) -> Dict[str, Any]:
    parsed = {
        "answer": _neutral_answer(case_types),
        "red_flags": [],
        "missing_data": [],
        "likely_systems": [],
        "confidence_note": "MedGemma chưa sẵn sàng trong môi trường hiện tại, phản hồi này chỉ là guard rails an toàn dựa trên triệu chứng hiện tại.",
        "model_status": model_status,
        "disclaimer": DISCLAIMER,
    }
    return repair_response_if_needed(parsed, case_types, message)


class FastChatService:
    def __init__(self):
        self.med = MedGemmaService()

    def chat(self, request):
        clean_message = request.message.strip()
        case_types = detect_case_types(clean_message, request.patientContext)
        prompt = build_prompt(clean_message, request.history[-5:], case_types)

        print("[FAST_CHAT] Current message:", clean_message)
        print("[FAST_CHAT] Detected case_types:", case_types)

        raw = self.med.generate(prompt, max_new_tokens=160)

        if "error" in raw:
            parsed = _local_unavailable_response(
                clean_message,
                case_types,
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

        parsed = parse_fast_chat_text(cleaned, raw.get("status", "medgemma_fast_text_parsed"))
        parsed = repair_response_if_needed(parsed, case_types, clean_message)
        if parsed["model_status"] != "medgemma_fast_text_fallback" and "domain_repaired" not in parsed["model_status"]:
            parsed["model_status"] = "medgemma_fast_text_parsed"

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
