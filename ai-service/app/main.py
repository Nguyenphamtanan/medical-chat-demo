from fastapi import FastAPI
from app.routers.full_agent_router import router as full_agent_router
from app.schemas import FastChatRequest, FastChatResponse, MedicalRequest, MedicalResponse
from app.services.fast_chat_service import FastChatService
from app.services.orchestrator import MedicalOrchestrator

app = FastAPI(title="Medical Chat AI Service")
orchestrator = MedicalOrchestrator()
fast_chat_service = FastChatService()
app.include_router(full_agent_router)

@app.get("/")
def root():
    return {"status": "AI service running"}

@app.get("/health")
def health():
    fast_health = fast_chat_service.health()
    return {
        "status": "ok",
        "model_loaded": fast_health["model_loaded"],
        "mode": "medgemma-only",
        "model_status": fast_health["model_status"],
    }

@app.post("/ai/analyze", response_model=MedicalResponse)
def analyze(data: MedicalRequest):
    return orchestrator.run(data.symptoms)

@app.post("/ai/chat", response_model=FastChatResponse)
def chat(data: FastChatRequest):
    return fast_chat_service.chat(data)
