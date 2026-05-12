from fastapi import FastAPI
from app.routers.full_agent_router import router as full_agent_router
from app.schemas import MedicalRequest, MedicalResponse
from app.services.orchestrator import MedicalOrchestrator

app = FastAPI(title="Medical Chat AI Service")
orchestrator = MedicalOrchestrator()
app.include_router(full_agent_router)

@app.get("/")
def root():
    return {"status": "AI service running"}

@app.post("/ai/analyze", response_model=MedicalResponse)
def analyze(data: MedicalRequest):
    return orchestrator.run(data.symptoms)
