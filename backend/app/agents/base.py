from __future__ import annotations

from typing import Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(Generic[InputT, OutputT]):
    name = "Agent"

    def run(self, payload: InputT) -> OutputT:
        raise NotImplementedError
