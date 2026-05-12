from functools import lru_cache

from fastapi import APIRouter

from app.advanced_agent.full_agent_service import FullAgentService
from app.advanced_agent.models import AdvancedCaseRequest, FullAgentResponse


router = APIRouter(prefix="/ai", tags=["full-agent"])


@lru_cache(maxsize=1)
def get_full_agent_service() -> FullAgentService:
    return FullAgentService()


@router.post("/full-agent", response_model=FullAgentResponse)
def analyze_full_agent(data: AdvancedCaseRequest):
    return get_full_agent_service().analyze(data)
