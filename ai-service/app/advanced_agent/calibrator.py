import math
from functools import lru_cache
from typing import Dict


class TinyScoreCalibrator:
    """Small deterministic calibrator loaded once per process."""

    def __init__(self):
        self.bias = -1.15
        self.weights = {
            "bm25": 0.55,
            "lab": 0.9,
            "symptom": 0.65,
            "history": 0.35,
            "red_flag": 0.75,
        }

    def predict(self, features: Dict[str, float]) -> float:
        z = self.bias
        for name, weight in self.weights.items():
            z += weight * float(features.get(name, 0.0))
        return round(1 / (1 + math.exp(-z)), 4)


@lru_cache(maxsize=1)
def get_calibrator() -> TinyScoreCalibrator:
    return TinyScoreCalibrator()
