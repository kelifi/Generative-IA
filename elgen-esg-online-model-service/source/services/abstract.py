from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseSettings

from source.schemas.model_answer_schema import ModelAnswer


class OnlineModelAPI(ABC):
    def __init__(self, config:BaseSettings | None):
        self.config = config

    @abstractmethod
    def generate_answer(self, prompt: str) -> ModelAnswer:
        """
        Generates an answer from the LLM given a prompt.
        Args:
            prompt: A text prompt upon which to generate an answer.

        Returns:
            ModelAnswer: the actual answer of the LLM and the inference time.
        """
        raise NotImplementedError
