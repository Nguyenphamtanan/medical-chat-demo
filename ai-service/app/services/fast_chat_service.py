import json
import re
from typing import Any, Dict, List, Optional

from .medgemma_service import MedGemmaService
from .parser_service import build_stub_response


DISCLAIMER = "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ. Tôi không phải là bác sĩ và nội dung này không thay thế việc thăm khám trực tiếp."

DEFAULT_RESPONSE = {
    "answer": "",
    "red_flags": [],
    "missing_data": [],
    "likely_systems": [],
    "confidence_note": "",
    "model_status": "unknown",
    "disclaimer": DISCLAIMER,
}


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def _extract_balanced_json(text: str) -> Optional[Dict[str, Any]]:
    clean = str(text or "").strip()
    clean = re.sub(r"(?im)^\s*```(?:json)?\s*", "", clean)
    clean = re.sub(r"(?im)\s*```\s*$", "", clean)

    try:
        parsed = json.loads(clean)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = None
    depth = 0
    in_string = False
    escaped = False
    candidates = []

    for index, char in enumerate(clean):
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
                candidates.append(clean[start : index + 1])
                start = None

    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

    return None


def _history_text(history) -> str:
    if not history:
        return "Không có lịch sử trước đó."

    lines = []
    for item in history[-8:]:
        role = "Người dùng" if item.role == "user" else "Trợ lý"
        lines.append(f"{role}: {item.content.strip()[:700]}")
    return "\n".join(lines)


def build_fast_prompt(message: str, history) -> str:
    return f"""
Return ONLY one valid JSON object. Do not use markdown. Do not reveal reasoning.
Answer in friendly Vietnamese. You are a medical triage assistant, not a doctor.
Keep the answer concise and safe.

Recent conversation:
{_history_text(history)}

Current user message:
{message}

JSON schema:
{{
  "answer": "2-5 câu tóm tắt ngắn, thân thiện, không chẩn đoán chắc chắn.",
  "red_flags": ["dấu hiệu cần đi khám/cấp cứu ngay nếu có"],
  "missing_data": ["câu hỏi cần hỏi thêm"],
  "likely_systems": ["hệ cơ quan có thể liên quan"],
  "confidence_note": "ghi chú ngắn về độ chắc chắn và giới hạn thông tin",
  "model_status": "medgemma_fast_json",
  "disclaimer": "{DISCLAIMER}"
}}
""".strip()


def normalize_fast_chat(data: Dict[str, Any], model_status: str) -> Dict[str, Any]:
    normalized = DEFAULT_RESPONSE.copy()

    if isinstance(data, dict):
        for key in normalized:
            if key in data:
                normalized[key] = data[key]

    normalized["answer"] = str(normalized.get("answer") or "").strip()
    normalized["red_flags"] = _as_list(normalized.get("red_flags"))
    normalized["missing_data"] = _as_list(normalized.get("missing_data"))
    normalized["likely_systems"] = _as_list(normalized.get("likely_systems"))
    normalized["confidence_note"] = str(normalized.get("confidence_note") or "").strip()
    normalized["model_status"] = str(normalized.get("model_status") or model_status).strip()
    normalized["disclaimer"] = DISCLAIMER

    if not normalized["answer"]:
        normalized["answer"] = (
            "Mình cần thêm thông tin để định hướng an toàn hơn. "
            "Bạn hãy cho biết triệu chứng bắt đầu khi nào, mức độ nặng ra sao và có dấu hiệu bất thường nào đi kèm không."
        )

    return normalized


def _stub_to_fast(message: str, model_status: str) -> Dict[str, Any]:
    stub = build_stub_response(message, model_status)
    return normalize_fast_chat(
        {
            "answer": " ".join(
                part
                for part in [stub.get("summary"), stub.get("recommendation")]
                if part
            ),
            "red_flags": stub.get("red_flags", []),
            "missing_data": stub.get("missing_questions", []),
            "likely_systems": stub.get("possible_related_systems", []),
            "confidence_note": "Câu trả lời dựa trên mô tả ngắn, cần thêm thông tin và thăm khám nếu triệu chứng đáng lo.",
            "model_status": model_status,
        },
        model_status,
    )


class FastChatService:
    def __init__(self):
        self.med = MedGemmaService()

    def chat(self, request):
        clean_message = request.message.strip()
        prompt = build_fast_prompt(clean_message, request.history)
        raw = self.med.generate(prompt, max_new_tokens=320)

        if "error" in raw:
            return _stub_to_fast(clean_message, raw.get("status", "ai_service_stub_fallback"))

        parsed = _extract_balanced_json(raw.get("text", ""))
        if parsed:
            return normalize_fast_chat(parsed, raw.get("status", "medgemma_fast_response"))

        return _stub_to_fast(clean_message, "medgemma_fast_non_json_fallback")

    def health(self):
        self.med._refresh_env()
        return {
            "model_loaded": self.med.pipe is not None,
            "model_status": self.med.status,
        }
