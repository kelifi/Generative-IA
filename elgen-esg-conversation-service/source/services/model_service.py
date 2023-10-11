from uuid import UUID
import requests
from fastapi import status
from pydantic import ValidationError
from requests import RequestException, Response
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from configuration.config import ModelsConfig
from configuration.logging_setup import logger
from source.exceptions.service_exceptions import ChatModelDiscoveryError, ModelServiceConnectionError, \
    DatabaseIntegrityError, DatabaseConnectionError, ModelCreationError, ModelUpdateError, ModelRetrievalError, \
    ClassificationModelRetrievalError
from source.exceptions.validation_exceptions import GenericValidationError
from source.repositories.model_repository import ModelRepository
from source.schemas.chat_schema import QuestionPurposeResponse
from source.schemas.models_schema import ModelSchema, ModelServiceAnswer, PromptInputSchema, \
    QuestionClassificationSchema, ModelOutputSchema, ModelInputSchema, ModelSourcesUpdateSchema, \
    AvailableModelsOutputSchema


class ModelService:

    def __init__(self, model_repository: ModelRepository, models_config: ModelsConfig) -> None:
        self._model_repository = model_repository
        self.__request_application_header = "application/json"
        self._models_config = models_config

    def get_models_for_chat_by_workspace_id(self, workspace_id: UUID,
                                            only_chat_flag: bool = True) -> AvailableModelsOutputSchema:
        """Return all the available models allowed for the user's workspace in a list of model schemas, if the only_chat_flag variable is set to true we
       will only retrieve models that are only for chat purposes"""
        try:
            return AvailableModelsOutputSchema(
                models=[ModelSchema.from_orm(model) for model in
                        self._model_repository.get_models_for_chat_by_workspace_id(workspace_id=workspace_id,
                                                                                   only_chat_flag=only_chat_flag)])
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelSchema.__name__)
        except DatabaseConnectionError as error:
            raise ModelRetrievalError(message=error.message)

    def get_models(self, only_chat_flag: bool = True) -> list[ModelSchema]:
        """Return all the available models in a list of model schemas, if the only_chat_flag variable is set to true we
        will only retrieve models that are only for chat purposes"""
        try:
            return [ModelSchema.from_orm(model) for model in
                    self._model_repository.get_models(only_chat_flag=only_chat_flag)]
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelSchema.__name__)
        except DatabaseConnectionError as error:
            raise ModelRetrievalError(message=error.message)

    def get_model_per_code(self, model_code: str) -> str:
        return self.__get_model_per_code(model_code=model_code)

    def get_model_info_per_model_code(self, model_code: str) -> ModelSchema:
        try:
            return ModelSchema.from_orm(self._model_repository.get_model_per_code(model_code=model_code))
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelSchema.__name__)
        except DatabaseConnectionError as error:
            raise ModelRetrievalError(message=error.message)
        except NoResultFound:
            raise ModelRetrievalError(message=f"No model found with code {model_code}")

    def get_models_per_workspace_type(self, workspace_type: str) -> list[ModelSchema]:
        """Get all models corresponding to the workspace type"""
        try:
            return [ModelSchema.from_orm(model) for model in
                    self._model_repository.get_models_per_workspace_type(workspace_type=workspace_type)]
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelSchema.__name__)
        except DatabaseConnectionError as error:
            raise ModelRetrievalError(message=error.message)
        except NoResultFound:
            raise ModelRetrievalError(message="No model found")

    def __get_model_mapping(self) -> dict:
        """Get the mapping between all model codes and routes"""
        return {model.code: model.route for model in self.get_models(only_chat_flag=False)}

    def __get_model_per_code(self, model_code: str) -> str:
        """Get the model per model_code"""
        model_route_to_use = self.__get_model_mapping().get(model_code)
        if not model_route_to_use:
            logger.error(f"Could not find the route corresponding to model code: {model_code}")
            raise ChatModelDiscoveryError(model_code=model_code)
        return model_route_to_use

    def request_model_service_per_code(self, text: str, model_code: str) -> ModelServiceAnswer:
        headers = {
            'accept': self.__request_application_header,
            'Content-Type': self.__request_application_header
        }
        discovered_model_route = self.__get_model_per_code(model_code=model_code)
        try:
            response = requests.post(
                url=f"{discovered_model_route}{self._models_config.GENERATIVE_MODEL_INFERENCE_ENDPOINT}",
                headers=headers,
                json=PromptInputSchema(prompt=text).dict())

        except requests.exceptions.RequestException as error:
            logger.error(f"Connection error with model code {model_code}: {error}")
            raise ModelServiceConnectionError(
                f'Connection to model service with code {model_code} and route {discovered_model_route} failed'
            ) from error

        logger.info(
            f'Request to model service: {discovered_model_route} has status code {response.status_code}')

        if response.status_code != 200:
            raise ModelServiceConnectionError(
                f'Connection to model service failed with status code {response.status_code}')
        return ModelServiceAnswer(**response.json(), model_code=model_code)

    def request_question_classification_model(self, question: str) -> QuestionPurposeResponse:
        headers = {
            'accept': self.__request_application_header,
            'Content-Type': self.__request_application_header
        }
        try:
            discovered_classification_model_route = self._model_repository.get_classification_model().route
        except (SQLAlchemyError, NoResultFound):
            raise ClassificationModelRetrievalError

        try:
            response = requests.post(
                url=f"{discovered_classification_model_route}{self._models_config.TOPIC_CLASSIFICATION_ENDPOINT}",
                headers=headers,
                json=QuestionClassificationSchema(content=question).dict())

        except requests.exceptions.RequestException as error:
            logger.error(f"Connection error with classification model: {error}")
            raise ModelServiceConnectionError(
                f'Connection to classification model failed') from error

        logger.info(
            f'Request to model service: {discovered_classification_model_route} has status code {response.status_code}')

        if response.status_code != 200:
            logger.error("Could not classify question")
            raise ModelServiceConnectionError(
                f'Connection to model service failed with status code {response.status_code}')
        try:
            return QuestionPurposeResponse(**response.json())
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=QuestionPurposeResponse.__name__)

    def add_model(self, model_input: ModelInputSchema) -> ModelOutputSchema:
        """Add a new model to the DB"""
        try:
            return ModelOutputSchema.from_orm(self._model_repository.add_model(model_input=model_input))
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelOutputSchema.__name__)
        except (DatabaseIntegrityError, DatabaseConnectionError) as error:
            raise ModelCreationError(message=error.message)

    def patch_model_configuration(self, model_sources_config: ModelSourcesUpdateSchema) -> ModelOutputSchema:
        """Alter an existing models configuration for the sources"""
        try:
            return ModelOutputSchema.from_orm(
                self._model_repository.patch_model_source_configurations(model_sources_config=model_sources_config))
        except ValidationError as error:
            logger.error(error)
            raise GenericValidationError(model_name=ModelOutputSchema.__name__)

        except DatabaseConnectionError as error:
            raise ModelUpdateError(message=error.message)

    def request_model_service_per_code_by_streaming(self, text: str,
                                                    model_code: str) -> Response | None:
        headers = {
            'accept': self.__request_application_header,
            'Content-Type': self.__request_application_header
        }
        discovered_model_route = self.__get_model_per_code(model_code=model_code)
        try:
            response = requests.post(
                url=f"{discovered_model_route}{self._models_config.STREAMING_GENERATIVE_MODEL_INFERENCE_ENDPOINT}",
                headers=headers,
                json=PromptInputSchema(prompt=text).dict(),
                stream=True
            )

            if response.status_code != status.HTTP_200_OK:
                logger.error(f"Error response: {response.json()}")
                raise ModelServiceConnectionError('Connection to classification model failed')

            return response

        except RequestException as error:
            logger.error(f"Connection error with model code {model_code}: {error}")
            raise ModelServiceConnectionError(
                f'Connection to model service with code {model_code} and route {discovered_model_route} failed'
            ) from error
