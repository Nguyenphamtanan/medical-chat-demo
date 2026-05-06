def build_prompt(symptoms: str) -> str:
    return f"""
Bạn là trợ lý phân loại y tế an toàn.

Nhiệm vụ:
- Phân tích triệu chứng người dùng.
- Trả về DUY NHẤT một JSON object hợp lệ.
- Không viết suy nghĩ.
- Không viết phân tích ngoài JSON.
- Không dùng markdown.
- Không dùng ```json.
- Không chẩn đoán chắc chắn.
- Không kê thuốc.
- Trả lời bằng tiếng Việt.

Triệu chứng người dùng:
{symptoms}

JSON bắt buộc:
{{
  "summary": "Tóm tắt ngắn triệu chứng và hướng liên quan.",
  "possible_related_systems": ["hệ/cơ quan có thể liên quan"],
  "possible_explanations": ["khả năng giải thích phù hợp, không chẩn đoán chắc chắn"],
  "red_flags": ["dấu hiệu nguy hiểm cần đi khám/cấp cứu"],
  "missing_questions": ["câu hỏi cần hỏi thêm"],
  "recommendation": "Khuyến nghị an toàn, không kê thuốc.",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}

Allowed severity values:
low, low_to_moderate, moderate, high, emergency.

Chỉ trả JSON object. Không thêm bất kỳ chữ nào ngoài JSON.
""".strip()


def build_json_repair_prompt(symptoms: str, raw_output: str) -> str:
    return f"""
Bạn là bộ chuyển đổi kết quả y tế sang JSON.

Dưới đây là triệu chứng người dùng:
{symptoms}

Dưới đây là phản hồi thô từ mô hình:
{raw_output[:3000]}

Hãy chuyển nội dung trên thành DUY NHẤT một JSON object hợp lệ.
Không viết suy nghĩ.
Không dùng markdown.
Không thêm chữ ngoài JSON.
Trả lời bằng tiếng Việt.

JSON bắt buộc:
{{
  "summary": "Tóm tắt ngắn triệu chứng và hướng liên quan.",
  "possible_related_systems": ["hệ/cơ quan có thể liên quan"],
  "possible_explanations": ["khả năng giải thích phù hợp, không chẩn đoán chắc chắn"],
  "red_flags": ["dấu hiệu nguy hiểm cần đi khám/cấp cứu"],
  "missing_questions": ["câu hỏi cần hỏi thêm"],
  "recommendation": "Khuyến nghị an toàn, không kê thuốc.",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real_repaired_json",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}

Chỉ trả JSON object.
""".strip()