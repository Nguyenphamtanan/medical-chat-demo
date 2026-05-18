from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

class MedicalRequest(BaseModel):
    symptoms: str = Field(..., min_length=1, max_length=3000)

    @validator("symptoms")
    def symptoms_must_not_be_blank(cls, value):
        clean = value.strip()
        if not clean:
            raise ValueError("symptoms must not be empty")
        return clean


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


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=3000)

    @validator("content")
    def content_must_not_be_blank(cls, value):
        clean = value.strip()
        if not clean:
            raise ValueError("history content must not be empty")
        return clean


class FastChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000)
    history: List[ChatHistoryMessage] = Field(default_factory=list, max_items=8)
    patientContext: Optional[Dict] = None

    @validator("message")
    def message_must_not_be_blank(cls, value):
        clean = value.strip()
        if not clean:
            raise ValueError("message must not be empty")
        return clean


class FastChatResponse(BaseModel):
    answer: str
    red_flags: List[str]
    missing_data: List[str]
    likely_systems: List[str]
    confidence_note: str
    model_status: str
    disclaimer: str
