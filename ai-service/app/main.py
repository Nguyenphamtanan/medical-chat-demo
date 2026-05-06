from fastapi import FastAPI
from app.schemas import MedicalRequest, MedicalResponse
from app.services.orchestrator import MedicalOrchestrator

app = FastAPI(title="Medical Chat AI Service")
orchestrator = MedicalOrchestrator()

@app.get("/")
def root():
    return {"status": "AI service running"}

@app.post("/ai/analyze", response_model=MedicalResponse)
def analyze(data: MedicalRequest):
    return orchestrator.run(data.symptoms)
