# Medical Chat Demo

Mini medical chat stack:

- React frontend
- Node.js / Express backend
- MongoDB chat history
- Python FastAPI AI service
- MedGemma support for a capable remote/Colab runtime
- Stub mode for local testing without loading MedGemma

## Response Shape

Every AI path returns this safe structured JSON:

```json
{
  "summary": "",
  "possible_related_systems": [],
  "possible_explanations": [],
  "red_flags": [],
  "missing_questions": [],
  "recommendation": "",
  "severity": "unknown",
  "model_status": "unknown",
  "disclaimer": ""
}
```

The assistant is not a diagnosis tool. It is for educational triage support only.

## Backend Environment

Create or edit `backend/.env`:

```env
PORT=5000
MONGO_URI=mongodb://127.0.0.1:27017/medical_chat_demo
JWT_SECRET=change_this_secret

AI_MODE=stub
LOCAL_AI_URL=http://127.0.0.1:8000
COLAB_AI_URL=
```

Modes:

- `AI_MODE=stub`: backend returns a local structured stub response. No Python service and no MedGemma are required.
- `AI_MODE=local`: backend calls `LOCAL_AI_URL/ai/analyze`.
- `AI_MODE=colab`: backend calls `COLAB_AI_URL/ai/analyze`, usually a public ngrok URL from Colab.

## AI Service Environment

Create or edit `ai-service/.env`:

```env
USE_MEDGEMMA=false
MEDGEMMA_MODEL_ID=google/medgemma-1.5-4b-it
HF_TOKEN=
```

Keep `USE_MEDGEMMA=false` on low-resource local machines. Set it to `true` only in Colab or another runtime that can load MedGemma.

## Run Locally In Stub Mode

Start MongoDB locally first.

Backend:

```bash
cd backend
npm install
npm run dev
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, register/login, then chat. In stub mode, the backend saves chat history to MongoDB and never calls MedGemma.

## Run With Local FastAPI Stub

Set `backend/.env`:

```env
AI_MODE=local
LOCAL_AI_URL=http://127.0.0.1:8000
```

Start the AI service with MedGemma disabled:

```bash
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn python-dotenv
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

This still does not run real MedGemma. It returns the same structured safe stub shape from FastAPI.

## Run Real MedGemma From Colab

In Colab:

1. Upload or clone the `ai-service` folder.
2. Install dependencies for FastAPI, ngrok, Hugging Face, Transformers, Torch, and Accelerate.
3. Set environment variables:

```env
USE_MEDGEMMA=true
HF_TOKEN=your_huggingface_token
```

4. Start FastAPI on port `8000`.
5. Expose it with ngrok and copy the public HTTPS URL.

On your local backend, set:

```env
AI_MODE=colab
COLAB_AI_URL=https://your-ngrok-url.ngrok-free.app
```

Restart the backend. The flow is:

```text
React -> Express /api/chat/ask -> Colab ngrok /ai/analyze -> MedGemma -> MongoDB history
```

## API Flow

Frontend sends:

```http
POST /api/chat/ask
Authorization: Bearer <token>
Content-Type: application/json

{ "symptoms": "fever and cough for 2 days" }
```

Backend returns:

```json
{
  "message": "AI response received.",
  "data": {
    "chat": {},
    "aiResponse": {}
  }
}
```

Chat history is available at:

```http
GET /api/chat/history
```
