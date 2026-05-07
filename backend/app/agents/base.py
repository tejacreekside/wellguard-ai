from __future__ import annotations

from typing import Generic, TypeVar

from app.core.logging import get_logger


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(Generic[InputT, OutputT]):
    name = "Agent"
    default_confidence_score = 75.0

    def run(self, payload: InputT) -> OutputT:
        raise NotImplementedError

    def log(self, message: str) -> None:
        get_logger(self.name).info(message)
