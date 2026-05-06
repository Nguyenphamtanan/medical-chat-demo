from typing import List

from pydantic import BaseModel

class MedicalRequest(BaseModel):
    symptoms: str


class MedicalResponse(BaseModel):
    summary: str
    possible_related_systems: List[str]
    possible_explanations: List[str]
    red_flags: List[str]
    missing_questions: List[str]
    recommendation: str
    severity: str
    model_status: str
    disclaimer: str
