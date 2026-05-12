from typing import Dict, List

from .models import AdvancedCaseRequest
from .translation import normalize_text


SPECIALIST_LABELS = {
    "hepatology": "Gan máº­t",
    "gastroenterology": "TiÃªu hÃ³a",
    "endocrinology": "Ná»™i tiáº¿t",
    "infectious_disease": "Truyá»n nhiá»…m",
    "cardiology": "Tim máº¡ch",
}


class SpecialistPanel:
    def analyze(self, case: AdvancedCaseRequest, specialties: List[str]) -> Dict:
        return {
            specialty: self._analyze_one(case, specialty)
            for specialty in specialties
        }

    def _analyze_one(self, case: AdvancedCaseRequest, specialty: str) -> Dict:
        text = normalize_text(" ".join([*case.symptoms, *case.history, case.query or ""]))
        labs = self._abnormal_labs(case)
        if specialty == "hepatology":
            focus = [
                "VÃ ng da, nÆ°á»›c tiá»ƒu sáº«m mÃ u vÃ  bilirubin tÄƒng gá»£i Ã½ cáº§n Ä‘Ã¡nh giÃ¡ trá»¥c gan-máº­t.",
                "Cáº§n phÃ¢n biá»‡t tá»•n thÆ°Æ¡ng táº¿ bÃ o gan, á»© máº­t/táº¯c máº­t vÃ  viÃªm Ä‘Æ°á»ng máº­t náº¿u cÃ³ sá»‘t hoáº·c Ä‘au háº¡ sÆ°á»n pháº£i.",
            ]
            missing = ["AST/ALT, ALP/GGT, bilirubin trá»±c tiáº¿p", "MÃ u phÃ¢n, Ä‘au háº¡ sÆ°á»n pháº£i, sá»‘t/rÃ©t run"]
        elif specialty == "gastroenterology":
            focus = [
                "SiÃªu Ã¢m bá»¥ng vÃ  triá»‡u chá»©ng tiÃªu hÃ³a giÃºp Ä‘á»‹nh hÆ°á»›ng gan, tÃºi máº­t, Ä‘Æ°á»ng máº­t hoáº·c tá»¥y.",
                "Gan to/gan nhiá»…m má»¡ cÃ³ thá»ƒ lÃ  bá»‡nh ná»n nhÆ°ng khÃ´ng tá»± giáº£i thÃ­ch toÃ n bá»™ vÃ ng da tiáº¿n triá»ƒn.",
            ]
            missing = ["Káº¿t quáº£ siÃªu Ã¢m Ä‘Æ°á»ng máº­t/tÃºi máº­t", "Äau bá»¥ng, nÃ´n Ã³i, sá»¥t cÃ¢n, phÃ¢n báº¡c mÃ u"]
        elif specialty == "endocrinology":
            focus = [
                "ÄÃ¡i thÃ¡o Ä‘Æ°á»ng vÃ  gan nhiá»…m má»¡ lÃ m tÄƒng nguy cÆ¡ bá»‡nh gan chuyá»ƒn hÃ³a.",
                "Cáº§n rÃ  soÃ¡t kiá»ƒm soÃ¡t Ä‘Æ°á»ng huyáº¿t vÃ  chá»©c nÄƒng tháº­n khi Ä‘ang dÃ¹ng metformin.",
            ]
            missing = ["Glucose/HbA1c gáº§n Ä‘Ã¢y", "Creatinine/eGFR", "CÃ¢n náº·ng vÃ  rÆ°á»£u"]
        elif specialty == "infectious_disease":
            focus = [
                "Náº¿u vÃ ng da Ä‘i kÃ¨m sá»‘t, rÃ©t run, lÆ¡ mÆ¡ hoáº·c tá»¥t huyáº¿t Ã¡p, cáº§n loáº¡i trá»« nhiá»…m trÃ¹ng náº·ng/viÃªm Ä‘Æ°á»ng máº­t.",
                "Cáº§n há»i yáº¿u tá»‘ phÆ¡i nhiá»…m viÃªm gan, du lá»‹ch, thá»±c pháº©m, thuá»‘c vÃ  tiáº¿p xÃºc ngÆ°á»i bá»‡nh.",
            ]
            missing = ["Nhiá»‡t Ä‘á»™, máº¡ch, huyáº¿t Ã¡p", "CÃ´ng thá»©c mÃ¡u, CRP", "Yáº¿u tá»‘ nguy cÆ¡ viÃªm gan"]
        elif specialty == "cardiology":
            focus = [
                "Tim máº¡ch khÃ´ng pháº£i hÆ°á»›ng chÃ­nh náº¿u khÃ´ng cÃ³ Ä‘au ngá»±c, khÃ³ thá»Ÿ, ngáº¥t hoáº·c phÃ¹.",
                "Dáº¥u hiá»‡u sá»‘c hoáº·c khÃ³ thá»Ÿ váº«n lÃ  cáº£nh bÃ¡o cáº§n xá»­ trÃ­ kháº©n.",
            ]
            missing = ["Äau ngá»±c, khÃ³ thá»Ÿ, ngáº¥t", "Máº¡ch, huyáº¿t Ã¡p, SpO2"]
        else:
            focus = ["Cáº§n Ä‘Ã¡nh giÃ¡ thÃªm theo bá»‘i cáº£nh lÃ¢m sÃ ng."]
            missing = ["Dáº¥u hiá»‡u sinh tá»“n", "Diá»…n tiáº¿n triá»‡u chá»©ng"]

        red_flags = self._red_flags(text)
        return {
            "label": SPECIALIST_LABELS.get(specialty, specialty),
            "key_findings": focus,
            "abnormal_labs": labs,
            "red_flags": red_flags,
            "missing_data": missing,
            "safe_next_steps": [
                "NÃªn Ä‘Æ°á»£c bÃ¡c sÄ© khÃ¡m trá»±c tiáº¿p Ä‘á»ƒ Ä‘á»‘i chiáº¿u triá»‡u chá»©ng, khÃ¡m thá»±c thá»ƒ vÃ  xÃ©t nghiá»‡m.",
                "Äi cáº¥p cá»©u náº¿u xuáº¥t hiá»‡n dáº¥u hiá»‡u cáº£nh bÃ¡o hoáº·c triá»‡u chá»©ng náº·ng nhanh.",
            ],
        }

    def _abnormal_labs(self, case: AdvancedCaseRequest) -> List[Dict]:
        abnormal = []
        for lab in case.labs:
            direction = None
            if lab.reference_high is not None and lab.value > lab.reference_high:
                direction = "high"
            if lab.reference_low is not None and lab.value < lab.reference_low:
                direction = "low"
            if direction:
                abnormal.append(
                    {
                        "name": lab.name,
                        "value": lab.value,
                        "unit": lab.unit,
                        "direction": direction,
                    }
                )
        return abnormal

    def _red_flags(self, text: str) -> List[str]:
        flags = [
            "Sá»‘t cao/rÃ©t run kÃ¨m vÃ ng da",
            "Äau bá»¥ng dá»¯ dá»™i hoáº·c Ä‘au háº¡ sÆ°á»n pháº£i tÄƒng",
            "LÆ¡ mÆ¡, tá»¥t huyáº¿t Ã¡p, ngáº¥t hoáº·c khÃ³ thá»Ÿ",
            "VÃ ng da tÄƒng nhanh, cháº£y mÃ¡u báº¥t thÆ°á»ng hoáº·c nÃ´n Ã³i khÃ´ng giá»¯ Ä‘Æ°á»£c nÆ°á»›c",
        ]
        if "khÃ³ thá»Ÿ" in text or "Ä‘au ngá»±c" in text:
            flags.append("Äau ngá»±c hoáº·c khÃ³ thá»Ÿ cáº§n Ä‘Ã¡nh giÃ¡ cáº¥p cá»©u.")
        return flags
