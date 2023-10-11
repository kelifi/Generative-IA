from datetime import datetime
from uuid import UUID

from sqlalchemy import Row, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, DatabaseIntegrityError
from source.helpers.db_helpers import DBHelper
from source.models.model_table import Model
from source.models.workspace_models import Workspace
from source.schemas.common import ModelTypes, WorkspaceType
from source.schemas.models_schema import ModelInputSchema, ModelSourcesUpdateSchema


class ModelRepository:
    def __init__(self, database_helper: DBHelper) -> None:
        self.__database_helper = database_helper

    def get_models_for_chat_by_workspace_id(self, workspace_id: UUID, only_chat_flag: bool) -> list[Row]:
        """get the list of all available models from the database, if the only_chat_flag is set to true than only chat
        models information is returned """
        with self.__database_helper.session() as session:
            try:
                workspace_allowed_models = (
                    session.query(Workspace.available_model_codes).filter(Workspace.id == workspace_id).first())
                return session.query(Model).filter(
                    Model.type == ModelTypes.CHAT,
                    Model.available,
                    Model.code.in_(code.strip() for code in
                                   workspace_allowed_models[0].split(','))).all() if only_chat_flag else session.query(
                    Model).filter(Model.available).all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened when retrieving the list of available models {error}')
                raise DatabaseConnectionError(f"A database connection error has occurred")

    def get_models(self, only_chat_flag: bool) -> list[Row]:
        """get the list of all available models from the database, if the only_chat_flag is set to true than only chat
        models information is returned """
        with self.__database_helper.session() as session:
            try:
                return session.query(Model).filter(
                    Model.type == ModelTypes.CHAT,
                    Model.available).all() if only_chat_flag else session.query(
                    Model).filter(Model.available).all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened when retrieving the list of available models {error}')
                raise DatabaseConnectionError(f"A database connection error has occurred")

    def add_model(self, model_input: ModelInputSchema) -> Model:
        """Add a model to the DB"""
        with self.__database_helper.session() as session:
            model_object = Model(**model_input.dict())
            model_object.creation_date = datetime.now()
            session.add(model_object)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseIntegrityError(
                    message=f'An integrity error happened when creating new model with code: {model_input.code}')
            except SQLAlchemyError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseConnectionError(message='Cannot add model')
            return model_object

    def patch_model_source_configurations(self, model_sources_config: ModelSourcesUpdateSchema) -> Model:
        """Update a model sources' configurations"""
        with self.__database_helper.session() as session:
            model = session.query(Model).filter(Model.code == model_sources_config.code).first()

            if not model:
                logger.error(
                    f"Could not patch model with code {model_sources_config.code} since it does not exist in the db")
                raise NoResultFound

            model.max_doc = model_sources_config.max_doc
            model.max_web = model_sources_config.max_web
            try:
                session.commit()
            except SQLAlchemyError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseConnectionError(message='Cannot add model')

            session.refresh(model)
            return model

    def get_classification_model(self) -> Model:
        """Get the first found classification model"""
        with self.__database_helper.session() as session:
            try:
                model = session.query(Model).filter(Model.type == ModelTypes.CLASSIFICATION).first()
            except SQLAlchemyError as error:
                logger.error(error)
                raise DatabaseConnectionError(f"A database connection error has occurred")
            if not model:
                logger.error(f"Could not find a classification model with type {ModelTypes.CLASSIFICATION}")
                raise NoResultFound

            return model

    def get_model_per_code(self, model_code: str) -> Model:
        with self.__database_helper.session() as session:
            try:
                model = session.query(Model).filter(Model.code == model_code).first()
            except SQLAlchemyError as error:
                logger.error(error)
                raise DatabaseConnectionError(f"A database connection error has occurred")
            if not model:
                logger.error(f"Could not find a model with code {model_code}")
                raise NoResultFound
            return model

    def get_models_per_workspace_type(self, workspace_type: str) -> list[Row]:
        """Get the models corresponding to the workspace type"""
        with self.__database_helper.session() as session:
            try:
                models = session.query(Model).filter(or_(
                    Model.type == ModelTypes.CHAT,
                    Model.type == ModelTypes.CLASSIFICATION)).all() if workspace_type == WorkspaceType.CHAT else session.query(
                    Model).all()
            except SQLAlchemyError as error:
                logger.error(
                    f'A data error happened when retrieving the list of the models corresponding to the workspace type {error}')
                raise DatabaseConnectionError(f"A database connection error has occurred")
            if not models:
                logger.error("No model found")
                raise NoResultFound
            return models
