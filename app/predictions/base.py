"""Prediction model interface.

Heuristic implementations live alongside this and satisfy the same contract, so a
trained ML model (sklearn, xgboost, a remote endpoint, …) can be dropped in later
by subclassing ``ModelService`` and swapping it into the service/registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelService(ABC):
    name: str
    version: str = "heuristic-v1"

    @abstractmethod
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Return a prediction dict (must include a ``confidence`` where relevant)."""
        raise NotImplementedError

    def explain(self, features: dict[str, Any]) -> dict[str, Any]:
        """Optional: return the drivers behind a prediction."""
        return {"model": self.name, "version": self.version, "inputs": features}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
