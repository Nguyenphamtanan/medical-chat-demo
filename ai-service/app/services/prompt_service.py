def build_prompt(symptoms: str) -> str:
    return f"""
Return ONLY one valid JSON object.
The first character must be {{ and the last character must be }}.
Do not output thoughts.
Do not output analysis.
Do not use markdown.
Do not write anything before or after JSON.
Answer in Vietnamese.

User symptoms: {symptoms}

Fill the JSON with SPECIFIC medical triage content based on the user symptoms.
Do NOT copy the field descriptions.
Do NOT use placeholder text.
Do NOT leave arrays generic.
Do NOT diagnose definitively.
Do NOT prescribe medication.

Required JSON keys:
{{
  "summary": "Viết tóm tắt cụ thể dựa trên triệu chứng người dùng.",
  "possible_related_systems": ["Liệt kê hệ/cơ quan cụ thể, ví dụ: hô hấp, tai mũi họng, gan, mật"],
  "possible_explanations": ["Liệt kê khả năng giải thích cụ thể, không chẩn đoán chắc chắn"],
  "red_flags": ["Liệt kê dấu hiệu nguy hiểm cụ thể cần đi khám/cấp cứu"],
  "missing_questions": ["Liệt kê câu hỏi cụ thể cần hỏi thêm"],
  "recommendation": "Viết khuyến nghị an toàn cụ thể, không kê thuốc.",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}

Example for symptoms "sốt, ho, đau họng 2 ngày":
{{
  "summary": "Bạn mô tả sốt, ho và đau họng trong 2 ngày, thường liên quan đến đường hô hấp hoặc tai mũi họng.",
  "possible_related_systems": ["hô hấp", "tai mũi họng", "toàn thân"],
  "possible_explanations": ["Nhiễm virus đường hô hấp trên", "Cúm hoặc COVID-19", "Viêm họng", "Kích ứng đường hô hấp"],
  "red_flags": ["Khó thở", "Đau ngực", "Sốt cao kéo dài", "Lơ mơ", "Tím môi", "Nuốt khó hoặc đau họng tăng nhanh"],
  "missing_questions": ["Bạn sốt bao nhiêu độ?", "Có khó thở hoặc đau ngực không?", "Có test COVID/cúm chưa?", "Có bệnh nền hoặc suy giảm miễn dịch không?"],
  "recommendation": "Nên nghỉ ngơi, uống đủ nước nếu phù hợp, theo dõi nhiệt độ và đi khám nếu sốt cao kéo dài, khó thở, đau ngực hoặc triệu chứng nặng dần.",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}

Now return ONLY the JSON object for the actual user symptoms.
""".strip()


def build_json_repair_prompt(symptoms: str, raw_output: str) -> str:
    return f"""
Convert the model response into ONE valid JSON object.
The first character must be {{ and the last character must be }}.
Do not output thoughts.
Do not output analysis.
Do not use markdown.
Answer in Vietnamese.

User symptoms: {symptoms}

Raw model output:
{raw_output[:2500]}

Create SPECIFIC content from the user symptoms and raw output.
Do NOT copy placeholder descriptions.
Do NOT use these phrases:
- "Tóm tắt ngắn triệu chứng và hướng liên quan"
- "hệ/cơ quan có thể liên quan"
- "khả năng giải thích phù hợp"
- "dấu hiệu nguy hiểm cần đi khám/cấp cứu"
- "câu hỏi cần hỏi thêm"
- "Khuyến nghị an toàn, không kê thuốc"
- "Nội dung cụ thể"

Required JSON:
{{
  "summary": "Nội dung cụ thể",
  "possible_related_systems": ["Nội dung cụ thể"],
  "possible_explanations": ["Nội dung cụ thể"],
  "red_flags": ["Nội dung cụ thể"],
  "missing_questions": ["Nội dung cụ thể"],
  "recommendation": "Nội dung cụ thể",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real_repaired_json",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}

Return ONLY the filled JSON object.
""".strip()
