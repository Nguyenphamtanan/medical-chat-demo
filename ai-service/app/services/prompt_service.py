def build_prompt(symptoms: str) -> str:
    return f"""
Return ONLY one valid JSON object.
The first character must be {{ and the last character must be }}.
Do not output thoughts.
Do not output analysis.
Do not use markdown.
Do not use ```json.
Do not write anything before or after the JSON.
Answer in Vietnamese.

User symptoms: {symptoms}

Required JSON:
{{
  "summary": "",
  "possible_related_systems": [],
  "possible_explanations": [],
  "red_flags": [],
  "missing_questions": [],
  "recommendation": "",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}
""".strip()


def build_json_repair_prompt(symptoms: str, raw_output: str) -> str:
    return f"""
Convert the medical content below into ONE valid JSON object.
The first character must be {{ and the last character must be }}.
Do not output thoughts.
Do not output analysis.
Do not use markdown.
Answer in Vietnamese.

User symptoms: {symptoms}

Raw model output:
{raw_output[:2000]}

Required JSON:
{{
  "summary": "",
  "possible_related_systems": [],
  "possible_explanations": [],
  "red_flags": [],
  "missing_questions": [],
  "recommendation": "",
  "severity": "low_to_moderate",
  "model_status": "medgemma_real_repaired_json",
  "disclaimer": "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ."
}}
""".strip()