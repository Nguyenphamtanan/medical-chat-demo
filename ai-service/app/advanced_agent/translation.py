VN_TO_EN_TERMS = {
    "vÃ ng da": "jaundice",
    "má»‡t má»i": "fatigue",
    "nÆ°á»›c tiá»ƒu sáº«m mÃ u": "dark urine",
    "ngá»©a": "pruritus",
    "Ä‘au bá»¥ng": "abdominal pain",
    "sá»‘t": "fever",
    "khÃ³ thá»Ÿ": "dyspnea",
    "Ä‘au ngá»±c": "chest pain",
    "gan nhiá»…m má»¡": "fatty liver",
    "Ä‘Ã¡i thÃ¡o Ä‘Æ°á»ng": "diabetes mellitus",
    "gan to": "hepatomegaly",
    "bá»¥ng": "abdomen",
}


def normalize_text(text: str) -> str:
    lowered = (text or "").lower()
    for vi, en in VN_TO_EN_TERMS.items():
        lowered = lowered.replace(vi, f"{vi} {en}")
    return lowered
