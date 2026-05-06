import os

from dotenv import load_dotenv

load_dotenv()


class MedGemmaService:
    def __init__(self):
        self.model_id = os.getenv("MEDGEMMA_MODEL_ID", "google/medgemma-1.5-4b-it")
        self.token = os.getenv("HF_TOKEN", "").strip()
        self.use_medgemma = os.getenv("USE_MEDGEMMA", "false").lower() == "true"
        self.pipe = None
        self.status = "disabled_stub_mode"

    def _load_model(self):
        if not self.use_medgemma:
            self.status = "disabled_stub_mode"
            return

        if self.pipe is not None:
            return

        if not self.token:
            self.status = "missing_hf_token"
            return

        try:
            import torch
            from huggingface_hub import login
            from transformers import pipeline

            login(token=self.token, add_to_git_credential=False)

            device = 0 if torch.cuda.is_available() else -1
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            self.pipe = pipeline(
                "image-text-to-text",
                model=self.model_id,
                token=self.token,
                device=device,
                torch_dtype=dtype,
            )

            self.status = "loaded_successfully"
        except Exception as exc:
            self.status = f"load_failed: {type(exc).__name__}: {exc}"

    def generate(self, prompt: str):
        self._load_model()

        if self.pipe is None:
            return {
                "error": "MedGemma is not loaded",
                "status": self.status,
            }

        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ]

            outputs = self.pipe(
                messages,
                max_new_tokens=512,
                do_sample=False,
            )

            if isinstance(outputs, list) and outputs:
                generated = outputs[0].get("generated_text", "")

                if isinstance(generated, list) and generated:
                    last = generated[-1]
                    if isinstance(last, dict):
                        return {
                            "text": last.get("content", ""),
                            "status": "real_medgemma_response",
                        }

                if isinstance(generated, str):
                    return {
                        "text": generated,
                        "status": "real_medgemma_response",
                    }

                return {
                    "text": str(generated),
                    "status": "real_medgemma_response",
                }

            return {
                "error": "Empty MedGemma output",
                "status": "empty_medgemma_output",
            }
        except Exception as exc:
            return {
                "error": f"{type(exc).__name__}: {exc}",
                "status": "real_medgemma_call_failed",
            }
