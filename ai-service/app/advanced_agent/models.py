from typing import Dict, List, Optional

from pydantic import BaseModel, Field


DISCLAIMER = "ThÃ´ng tin chá»‰ mang tÃ­nh tham kháº£o, khÃ´ng thay tháº¿ bÃ¡c sÄ©."


class LabResult(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None


class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None


class ImagingReport(BaseModel):
    modality: Optional[str] = None
    body_site: Optional[str] = None
    report_text: str
    timestamp: Optional[str] = None


class ClinicalNote(BaseModel):
    title: Optional[str] = None
    text: str
    timestamp: Optional[str] = None


class AdvancedCaseRequest(BaseModel):
    case_id: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=130)
    sex: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list)
    labs: List[LabResult] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    imaging_reports: List[ImagingReport] = Field(default_factory=list)
    notes: List[ClinicalNote] = Field(default_factory=list)
    query: Optional[str] = None


class FullAgentResponse(BaseModel):
    case_id: str
    mode: str = "full_agent"
    plan: List[str]
    selected_specialties: List[str]
    fused_probabilities: Dict[str, float]
    pre_specialist_summary: Dict
    specialist_outputs: Dict
    reflection: Dict
    safe_summary: str
    medgemma_status: str
    disclaimer: str = DISCLAIMER


def case_to_text(case: AdvancedCaseRequest) -> str:
    labs = [
        (
            f"{lab.name}: {lab.value} {lab.unit or ''} "
            f"(ref {lab.reference_low if lab.reference_low is not None else '?'}-"
            f"{lab.reference_high if lab.reference_high is not None else '?'})"
        )
        for lab in case.labs
    ]
    medications = [
        " ".join(part for part in [med.name, med.dose, med.frequency] if part)
        for med in case.medications
    ]
    imaging = [
        " ".join(
            part
            for part in [
                report.modality,
                report.body_site,
                report.report_text,
                report.timestamp,
            ]
            if part
        )
        for report in case.imaging_reports
    ]
    notes = [
        " ".join(part for part in [note.title, note.text, note.timestamp] if part)
        for note in case.notes
    ]
    chunks = [
        f"age: {case.age}" if case.age is not None else "",
        f"sex: {case.sex}" if case.sex else "",
        "symptoms: " + ", ".join(case.symptoms),
        "history: " + ", ".join(case.history),
        "labs: " + "; ".join(labs),
        "medications: " + "; ".join(medications),
        "imaging: " + "; ".join(imaging),
        "notes: " + "; ".join(notes),
        "query: " + (case.query or ""),
    ]
    return "\n".join(chunk for chunk in chunks if chunk.strip())
