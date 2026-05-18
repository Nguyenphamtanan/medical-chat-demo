import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


class MedGemmaService:
    def __init__(self):
        self.model_id = os.getenv("MEDGEMMA_MODEL_ID", "google/medgemma-1.5-4b-it")
        self.token = os.getenv("HF_TOKEN", "").strip()
        self.use_medgemma = os.getenv("USE_MEDGEMMA", "false").lower() == "true"
        self.pipe = None
        self.status = "disabled_stub_mode"

    def _refresh_env(self):
        self.model_id = os.getenv("MEDGEMMA_MODEL_ID", self.model_id)
        self.token = os.getenv("HF_TOKEN", "").strip()
        self.use_medgemma = os.getenv("USE_MEDGEMMA", "false").lower() == "true"

    def _load_model(self):
        self._refresh_env()

        if not self.use_medgemma:
            self.status = "disabled_stub_mode"
            return

        if self.pipe is not None:
            self.status = "loaded_successfully"
            return

        if not self.token:
            self.status = "missing_hf_token"
            return

        try:
            import torch
            from huggingface_hub import login
            from transformers import BitsAndBytesConfig, pipeline

            login(token=self.token, add_to_git_credential=False)

            if torch.cuda.is_available():
                dtype = torch.bfloat16
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                print("[MEDGEMMA] CUDA available:", torch.cuda.get_device_name(0))
            else:
                dtype = torch.float32
                quantization_config = None
                print("[MEDGEMMA] CUDA not available; 4-bit quantization is disabled.")

            print(f"[MEDGEMMA] Loading model: {self.model_id}")
            self.pipe = pipeline(
                "image-text-to-text",
                model=self.model_id,
                token=self.token,
                device_map="auto",
                model_kwargs={
                    "torch_dtype": dtype,
                    "quantization_config": quantization_config,
                },
            )
            self._clear_max_length_config()

            self.status = "loaded_successfully"
            print("[MEDGEMMA] Model loaded successfully.")
        except Exception as exc:
            self.pipe = None
            self.status = f"load_failed: {type(exc).__name__}: {exc}"
            print("[MEDGEMMA] Load failed:", self.status)

    def _extract_text(self, outputs: Any) -> str:
        if outputs is None:
            return ""

        if isinstance(outputs, list) and outputs:
            first = outputs[0]

            if isinstance(first, dict):
                generated = first.get("generated_text", "")

                if isinstance(generated, str):
                    return generated.strip()

                if isinstance(generated, list) and generated:
                    last = generated[-1]

                    if isinstance(last, dict):
                        content = last.get("content", "")

                        if isinstance(content, str):
                            return content.strip()

                        if isinstance(content, list):
                            chunks = []
                            for item in content:
                                if isinstance(item, dict):
                                    chunks.append(str(item.get("text", "")))
                                else:
                                    chunks.append(str(item))
                            return "\n".join([chunk for chunk in chunks if chunk]).strip()

                        return str(content).strip()

                    return str(last).strip()

                return str(generated).strip()

            return str(first).strip()

        return str(outputs).strip()

    def _clear_max_length_config(self):
        for target in [
            getattr(self.pipe, "generation_config", None),
            getattr(getattr(self.pipe, "model", None), "generation_config", None),
        ]:
            if target is None or not hasattr(target, "max_length"):
                continue
            try:
                target.max_length = None
            except Exception:
                pass

    def generate(self, prompt: str, max_new_tokens: int = 384) -> Dict[str, str]:
        self._load_model()

        if self.pipe is None:
            return {
                "error": "MedGemma is not loaded",
                "text": "",
                "status": self.status,
            }

        try:
            self._clear_max_length_config()
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

            print("[MEDGEMMA] Calling real model...")
            outputs = self.pipe(
                messages,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )

            text = self._extract_text(outputs)

            print("========== RAW MEDGEMMA OUTPUT ==========")
            print(text)
            print("=========================================")

            if not text:
                return {
                    "error": "Empty MedGemma output",
                    "text": "",
                    "status": "empty_medgemma_output",
                }

            return {
                "text": text,
                "status": "real_medgemma_response",
            }
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            print("[MEDGEMMA] Real call failed:", err)
            return {
                "error": err,
                "text": "",
                "status": "real_medgemma_call_failed",
            }

    def repair_json(self, prompt: str) -> Dict[str, str]:
        self._load_model()

        if self.pipe is None:
            return {
                "error": "MedGemma is not loaded",
                "text": "",
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

            print("[MEDGEMMA] Repairing non-JSON output into JSON...")
            outputs = self.pipe(
                messages,
                max_new_tokens=512,
                do_sample=False,
            )

            text = self._extract_text(outputs)

            print("========== RAW MEDGEMMA REPAIR OUTPUT ==========")
            print(text)
            print("================================================")

            if not text:
                return {
                    "error": "Empty MedGemma repair output",
                    "text": "",
                    "status": "empty_medgemma_repair_output",
                }

            return {
                "text": text,
                "status": "real_medgemma_repair_response",
            }
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            print("[MEDGEMMA] Repair call failed:", err)
            return {
                "error": err,
                "text": "",
                "status": "real_medgemma_repair_failed",
            }
