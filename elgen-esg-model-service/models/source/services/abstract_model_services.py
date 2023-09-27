from abc import ABC, abstractmethod
from typing import Any

from source.schemas.model_answer_schema import ModelAnswer


class LLMFactory(ABC):
    def __init__(self, qa: Any = None):
        self.qa = qa

    @abstractmethod
    def predict(self, prompt: str, **kwargs):
        """

        :param prompt: The prompt to be used by the model for text generation task
        :param kwargs:
        :return:
        """
        raise NotImplementedError

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

    @abstractmethod
    def is_loaded_correctly(self) -> bool:
        """
        Checks if the model is loaded as expected
        Returns: bool
        """
        raise NotImplementedError
