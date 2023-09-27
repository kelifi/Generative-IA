import logging

import requests
from fastapi import status
from pydantic import ValidationError
from requests import Response

from configuration.config import OpenAIConfig
from source.exceptions.model_exception_handler import OpenAIRequestError, ResultParsingPredictionError
from source.schemas.llm_models_schemas import OpenAIDataSchema, OpenAIRoleSchema, OpenAIRoles
from source.schemas.model_answer_schema import ModelAnswer
from source.services.abstract import OnlineModelAPI

logger = logging.getLogger(__name__)


class OpenAIService(OnlineModelAPI):

    def __init__(self, config: OpenAIConfig) -> None:
        super().__init__(config=config)
        self.config = config
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.API_KEY}'
        }

    def _parse_answer(self, response: Response) -> ModelAnswer:
        try:
            model_answer = {
                "inference_time": response.elapsed.total_seconds(),
                "model_name": self.config.MODEL_NAME
            }
            answers = response.json().get('choices')
            model_answer["response"] = answers[0].get('message').get('content')
            return ModelAnswer(**model_answer)
        except (KeyError, IndexError, ValidationError) as error:
            logger.error(error)
            raise ResultParsingPredictionError(
                detail=f"Failed to parse the results of {self.config.MODEL_NAME} service!",
            ) from error

    def generate_answer(self, prompt: str) -> ModelAnswer:
        """
        Generates an answer from the Online LLM API given a prompt.
        Args:
            prompt: A text prompt upon which to generate an answer.

        Returns:
            ModelAnswer: the actual answer of the Online LLM API and the inference time.
        """

        try:
            open_ai_call_data = OpenAIDataSchema(model=self.config.MODEL_NAME, messages=[
                OpenAIRoleSchema(role=OpenAIRoles.SYSTEM,
                                 content="You are a helpful assistant."),
                OpenAIRoleSchema(role=OpenAIRoles.USER, content=prompt)])

            response = requests.post(
                self.config.API_URL, headers=self.headers, json=open_ai_call_data.dict())

            if response.status_code != status.HTTP_200_OK:
                raise OpenAIRequestError(
                    detail='Failed to get results from online service'
                )

        except requests.exceptions.RequestException as error:
            logger.error(error)

            raise OpenAIRequestError(
                detail='An error occurred when calling the online service'
            ) from error

        return self._parse_answer(response)
