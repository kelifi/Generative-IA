from datetime import datetime
from uuid import UUID
from sqlalchemy import Row

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, NoResultFound

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, DatabaseIntegrityError
from source.helpers.db_helpers import DBHelper
from source.models.workspace_models import ChatSuggestions
from source.schemas.conversation_schema import QuestionInputSchema


class ChatSuggestionsRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def create_chat_suggestion(self, workspace_id: UUID, suggestion: QuestionInputSchema) -> ChatSuggestions:
        """
        Create new suggestion for specific workspace
        """
        new_suggestion = ChatSuggestions(content=suggestion.question,
                                         workspace_id=workspace_id,
                                         available=True)
        with self.database_helper.session() as session:
            session.add(new_suggestion)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseIntegrityError(
                    message='An integrity error happened when creating new suggestion')
            except SQLAlchemyError as error:
                session.rollback()
                logger.error(error)
                raise DatabaseConnectionError(message='Cannot add suggestion')
            session.refresh(new_suggestion)
            return new_suggestion

    def get_suggestions_by_workspace(self, workspace_id: UUID) -> list[Row]:
        """
        Get list of suggested questions by workspace_id
        """
        with self.database_helper.session() as session:
            try:
                return session.query(ChatSuggestions).filter(
                    ChatSuggestions.workspace_id == workspace_id, ChatSuggestions.available == True,
                    ChatSuggestions.deleted == False
                ).all()
            except SQLAlchemyError as error:
                logger.error(f'A data error happened on get suggestions by workspace-id {error}')
                raise DatabaseConnectionError(f"Database connection error: {error}")

    def delete_suggestion_by_id(self, suggestion_id: UUID) -> None:
        """
        Delete suggestion by id
        """
        with self.database_helper.session() as session:
            if suggestion := session.query(ChatSuggestions).get(suggestion_id):
                suggestion.deleted = True
                suggestion.available = False
                suggestion.update_date = datetime.now()
                logger.info(f"Deleting suggestion with id {suggestion_id}")
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'An error happened on update suggestion for suggestion_id {suggestion_id}: {ex}')
                    raise DatabaseConnectionError(f'Database connection error: {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update suggestion for suggestion_id {suggestion_id}: {ex}')
                    raise DatabaseConnectionError(f'Database connection error: {ex}')
                session.refresh(suggestion)
                return None
            raise NoResultFound

    def update_suggestion_by_id(self, suggestion_id: UUID, new_suggestion: QuestionInputSchema) -> None:
        """
        Update suggestion by id
        """
        with self.database_helper.session() as session:
            if suggestion_to_update := session.query(ChatSuggestions).get(suggestion_id):
                logger.info(f"Updating suggestion with id {suggestion_id}")
                suggestion_to_update.content = new_suggestion.question
                suggestion_to_update.update_date = datetime.now()
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'A data error happened on update suggestion {suggestion_id}: {ex}')
                    raise DatabaseConnectionError(f'Cannot update suggestion {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update suggestion {suggestion_id}: {ex}')
                    raise DatabaseConnectionError(f'Cannot update workspace {ex}')
                session.refresh(suggestion_to_update)
                return None
            raise NoResultFound
