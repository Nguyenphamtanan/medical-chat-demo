from uuid import uuid4

from .fusion import adaptive_fusion
from .medgemma_reasoning import MedGemmaReasoner
from .models import AdvancedCaseRequest, FullAgentResponse, case_to_text
from .reflection import reflect
from .router import CaseRouter
from .specialists import SpecialistPanel


class FullAgentService:
    def __init__(self):
        self.router = CaseRouter()
        self.reasoner = MedGemmaReasoner()
        self.specialists = SpecialistPanel()

    def analyze(self, case: AdvancedCaseRequest) -> FullAgentResponse:
        case_id = case.case_id or str(uuid4())
        route_result = self.router.route(case)
        medgemma_result = self.reasoner.reason(case, route_result)
        fused = adaptive_fusion(route_result["router_probabilities"], medgemma_result)
        selected = [
            specialty
            for specialty in route_result["selected_specialties"]
            if specialty in fused
        ]
        if selected:
            selected = sorted(selected, key=lambda specialty: fused[specialty], reverse=True)
        specialist_outputs = self.specialists.analyze(case, selected)
        reflection = reflect(case_to_text(case), specialist_outputs, medgemma_result)
        pre_summary = {
            "case_text": case_to_text(case),
            "knowledge_hits": route_result["knowledge_hits"],
            "router_probabilities": route_result["router_probabilities"],
            "medgemma_reasoning": medgemma_result.get("reasoning", ""),
        }
        safe_summary = self._safe_summary(case, selected, reflection)
        return FullAgentResponse(
            case_id=case_id,
            plan=route_result["plan"],
            selected_specialties=selected,
            fused_probabilities=fused,
            pre_specialist_summary=pre_summary,
            specialist_outputs=specialist_outputs,
            reflection=reflection,
            safe_summary=safe_summary,
            medgemma_status=medgemma_result.get("status", "unknown"),
        )

    def _safe_summary(self, case: AdvancedCaseRequest, selected, reflection) -> str:
        symptoms = ", ".join(case.symptoms) if case.symptoms else "triá»‡u chá»©ng Ä‘Ã£ nháº­p"
        specialties = ", ".join(selected) if selected else "Ä‘a chuyÃªn khoa"
        warnings = reflection.get("warnings", [])
        warning_text = f" Cáº£nh bÃ¡o chÃ­nh: {warnings[0]}" if warnings else ""
        return (
            f"Ca bá»‡nh vá»›i {symptoms} nÃªn Ä‘Æ°á»£c phÃ¢n tÃ­ch theo hÆ°á»›ng {specialties}. "
            f"Káº¿t quáº£ gá»£i Ã½ cÃ¡c cÆ¡ quan/há»‡ liÃªn quan vÃ  dá»¯ liá»‡u cáº§n bá»• sung, "
            f"nhÆ°ng cáº§n bÃ¡c sÄ© khÃ¡m trá»±c tiáº¿p Ä‘á»ƒ káº¿t luáº­n.{warning_text}"
        )
