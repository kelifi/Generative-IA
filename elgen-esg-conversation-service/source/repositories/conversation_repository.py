from datetime import datetime
from typing import Tuple
from uuid import UUID

from sqlalchemy import desc, Row, asc
from sqlalchemy.exc import NoResultFound, DataError, SQLAlchemyError, IntegrityError
from sqlalchemy.orm import scoped_session

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, DatabaseIntegrityError, \
    ResourceOwnershipException
from source.helpers.db_helpers import DBHelper
from source.models.conversations_models import Conversation, Answer, Question, SourceDocument, SourceWeb, \
    AnswerAnalytics
from source.models.workspace_models import Workspace
from source.schemas.conversation_schema import ConversationSchema
from source.schemas.models_schema import ModelServiceAnswer


class ConversationRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_conversations_by_user(self, user_id: UUID, workspace_id: UUID) -> list[Row]:
        """For a certain user id, return the list of all conversation ids"""
        with self.database_helper.session() as session:
            try:
                return session.query(Conversation).filter(Conversation.user_id == user_id,
                                                          Conversation.workspace_id == workspace_id,
                                                          Conversation.deleted == False).order_by(
                    desc(Conversation.creation_date)).all()
            except SQLAlchemyError as e:
                logger.error(f'A data error happened on get conversation by id conversation {e}')
                raise DatabaseConnectionError(f"Database connection error: {e}")

    def create_conversation(self, conversation_title: str, user_id: UUID, workspace_id: UUID) -> UUID:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            conversation = Conversation()
            conversation.user_id = user_id
            conversation.workspace_id = workspace_id
            conversation.title = conversation_title
            session.add(conversation)
            session.commit()
            return conversation.id

    def update_conversation_title(self, new_conversation_title: str, conversation_id: UUID) -> ConversationSchema:
        """Update a conversation's title bases on its id"""
        with self.database_helper.session() as session:
            if conversation := session.query(Conversation).get(conversation_id):
                conversation.title = new_conversation_title
                conversation.update_date = datetime.now()
                logger.info(f"Updating conversation with id {conversation_id}")
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'A data error happened on update conversation {ex}')
                    raise DatabaseConnectionError(f'Cannot create source documents {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update conversation {ex}')
                    raise DatabaseConnectionError(f'Cannot create source documents {ex}')
                session.refresh(conversation)
                return ConversationSchema.from_orm(conversation)
            raise NoResultFound

    def delete_conversation(self, conversation_id: UUID) -> None:
        """Delete a conversation based on its id(Hard delete)"""
        with self.database_helper.session() as session:
            if conversation := session.query(Conversation).get(conversation_id):
                conversation.deleted = True
                logger.info(f"Deleting conversation with id {conversation_id}")
                try:
                    session.commit()
                except DataError as ex:
                    session.rollback()
                    logger.error(f'An error happened on update conversation for conversation_id {conversation_id} {ex}')
                    raise DatabaseConnectionError(f'Cannot create source documents {ex}')
                except SQLAlchemyError as ex:
                    logger.error(f'An error happened on update conversation for conversation_id {conversation_id} {ex}')
                    raise DatabaseConnectionError(f'Cannot create source documents {ex}')
                session.refresh(conversation)
                return None
            raise NoResultFound

    def get_conversation_by_id(self, conversation_id: UUID) -> list[Row]:
        with self.database_helper.session() as session:
            conversation_exists = session.query(Conversation.id).filter(
                Conversation.id == conversation_id,
                Conversation.deleted == False
            ).exists()

            if not session.query(conversation_exists).scalar():
                raise NoResultFound(f'No result found for conversation {conversation_id}')
            query = session.query(Conversation.id.label("conv_id"), Question.id.label("quest_id"),
                                  Question.content.label("quest_content"),
                                  Question.creation_date.label("quest_date"),
                                  Question.skip_doc.label('skip_doc'),
                                  Question.skip_web.label('skip_web'),
                                  Question.is_specific.label("is_specific"),
                                  Answer.id.label("answer_id"),
                                  Answer.content.label("answer_content"),
                                  Answer.creation_date.label("answer_date"),
                                  Answer.rating.label("rating"),
                                  Answer.edited.label("edited"),
                                  Answer.update_date.label("update_date")
                                  ) \
                .join(Question, Conversation.id == Question.conversation_id) \
                .join(Answer, Question.id == Answer.question_id, isouter=True).filter(
                Conversation.id == conversation_id, Question.deleted == False,
                Conversation.deleted == False).order_by(
                asc(Question.creation_date))
            return query.all()

    def get_conversation_by_question_id(self, question_id: UUID) -> Tuple[str, list[Row]]:
        with self.database_helper.session() as session:
            conversation_id = session.query(Question.conversation_id).filter(Question.id == question_id).one_or_none()
        if not conversation_id:
            raise NoResultFound(f'Result not found for conversation {conversation_id}')
        return conversation_id[0], self.get_conversation_by_id(conversation_id[0])

    def get_question_by_id(self, question_id: UUID) -> Row:
        """For a certain user id, return the list of all conversation ids"""
        try:
            with self.database_helper.session() as session:
                return session.query(Question).filter(Question.id == question_id,
                                                      Question.deleted == False).one_or_none()
        except SQLAlchemyError as ex:
            logger.error(f'An error happened on get question by id for question_id {question_id} {ex}')
            raise DatabaseConnectionError(f'Cannot create source documents {ex}')

    @staticmethod
    def _validate_user_conversation_ownership(user_id: UUID,
                                              conversation_id: UUID,
                                              session: scoped_session) -> None:
        user_owns_conversation = session.query(Conversation).filter(
            Conversation.id == str(conversation_id),
            Conversation.user_id == str(user_id)
        ).first()

        if not user_owns_conversation:
            session.rollback()
            session.close()
            logger.error(f"User {user_id} not allowed to use conversation {conversation_id}")
            raise ResourceOwnershipException("User not allowed to use this resource!")

    @staticmethod
    def _validate_workspace_conversation_ownership(workspace_id: UUID,
                                                   conversation_id: UUID,
                                                   session: scoped_session) -> Workspace:
        workspace_contains_conversation = session.query(Workspace) \
            .join(Conversation, Conversation.workspace_id == Workspace.id) \
            .filter(Conversation.id == str(conversation_id),
                    Workspace.id == workspace_id) \
            .first()

        if not workspace_contains_conversation:
            session.rollback()
            session.close()
            logger.error(f"User {conversation_id} does not belong to {workspace_id}!")
            raise ResourceOwnershipException("An Error occured while checking this conversation and this workspace!")

        return workspace_contains_conversation

    def create_question(self, question: str,
                        conversation_id: UUID,
                        workspace_id: UUID,
                        user_id: UUID,
                        skip_doc: bool = False,
                        skip_web: bool = False,
                        is_specific: bool = True
                        ) -> Question:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:

            self._validate_user_conversation_ownership(user_id=user_id,
                                                       conversation_id=conversation_id,
                                                       session=session)

            self._validate_workspace_conversation_ownership(conversation_id=conversation_id,
                                                            workspace_id=workspace_id,
                                                            session=session)

            question_object = Question()
            question_object.content = question
            question_object.conversation_id = conversation_id
            question_object.skip_doc = skip_doc
            question_object.skip_web = skip_web
            question_object.is_specific = is_specific
            session.add(question_object)
            try:
                session.commit()
            except IntegrityError as ex:
                logger.error(f'Cannot create new question for conversation {conversation_id} {ex}')
                raise DatabaseIntegrityError(
                    f'An integrity error happened when creating new question for conversation {conversation_id}'
                ) from ex
            except SQLAlchemyError as ex:
                logger.error(f'An error happened on create question for conversation {conversation_id} {ex}')
                raise DatabaseConnectionError(f'Cannot create question {ex}') from ex
            return question_object

    def _create_answer_analytics_object(self, answer_response: ModelServiceAnswer, answer_id: UUID,
                                        model_code: str) -> AnswerAnalytics:
        """
        Parse the response from model services into a proper answer analytics object for database
        """

        answer_analytics_object = AnswerAnalytics()
        answer_analytics_object.answer_id = str(answer_id)
        answer_analytics_object.inference_time = answer_response.inference_time
        answer_analytics_object.prompt_length = answer_response.prompt_length
        answer_analytics_object.prompt = answer_response.prompt
        answer_analytics_object.model_code = model_code
        answer_analytics_object.model_name = answer_response.model_name

        # empty dict is because online service does not include metadata,
        metadata = answer_response.metadata or {}
        answer_analytics_object.load_in_4bit = metadata.get('load_in_4bit')
        answer_analytics_object.load_in_8bit = metadata.get('load_in_8bit')
        answer_analytics_object.max_new_tokens = metadata.get('max_new_tokens')
        answer_analytics_object.no_repeat_ngram_size = metadata.get('no_repeat_ngram_size')
        answer_analytics_object.repetition_penalty = metadata.get('repetition_penalty')
        return answer_analytics_object

    def create_answer(self, answer: ModelServiceAnswer, question_id: UUID) -> Row:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            try:
                answer_object = Answer()

                answer_object.content = answer.response
                answer_object.question_id = question_id

                session.add(answer_object)
                session.commit()
                session.refresh(answer_object)

                answer_analytics_object = self._create_answer_analytics_object(
                    answer_response=answer,
                    answer_id=answer_object.id,
                    model_code=answer.model_code
                )
                session.add(answer_analytics_object)
                session.commit()
                return answer_object

            except SQLAlchemyError as ex:
                session.rollback()
                # Delete the answer_object if it was created
                logger.error(f'An error happened on create answer for question_id {question_id} {ex}')
                raise DatabaseConnectionError(f'Cannot create answer {ex}')

    def get_sources_by_question_id(self, question_id: UUID) -> list[Row]:
        try:
            with self.database_helper.session() as session:
                return session.query(SourceDocument).filter(SourceDocument.question_id == question_id,
                                                            SourceDocument.deleted == False).all()
        except SQLAlchemyError as ex:
            logger.error(f'An error happened on get sources by question by id for question_id {question_id} {ex}')

            raise DatabaseConnectionError(f'Cannot create source documents {ex}')

    def create_source_document(self, question_id: UUID, file_name: str, content: str, document_type: str,
                               document_id: UUID) -> Row:
        with self.database_helper.session() as session:
            source_object = SourceDocument()
            source_object.question_id = str(question_id)
            source_object.document_path = file_name
            source_object.content = content
            source_object.document_id = document_id
            source_object.document_type = document_type or 'pdf'
            session.add(source_object)
            try:
                session.commit()
            except DataError as ex:
                session.rollback()
                logger.error(
                    f'An error happened on create sources by question by id for question_id {question_id} {ex}')

                raise DatabaseConnectionError(f'Cannot create source documents {ex}')
            except SQLAlchemyError as ex:
                logger.error(
                    f'An error happened on create sources by question by id for question_id {question_id} {ex}')

                raise DatabaseConnectionError(f'Cannot create source documents {ex}')
            return source_object

    def create_web_source(self, question_id: UUID, url: str, description: str, title: str, paragraphs: str) -> Row:
        with self.database_helper.session() as session:
            source_object = SourceWeb()
            source_object.question_id = str(question_id)
            source_object.url = url
            source_object.description = description
            source_object.title = title
            source_object.paragraphs = paragraphs
            session.add(source_object)
            try:
                session.commit()
            except DataError as ex:
                session.rollback()
                logger.error(
                    f'An error happened on create web sources by question by id for question_id {question_id} {ex}')
                raise DatabaseConnectionError(f'Cannot create source documents {ex}')
            except SQLAlchemyError as ex:
                logger.error(
                    f'An error happened on create web sources by question by id for question_id {question_id} {ex}')

                raise DatabaseConnectionError(f'Cannot create source documents {ex}')
            return source_object

    def get_web_sources_by_question_id(self, question_id: UUID) -> list[Row]:
        try:
            with self.database_helper.session() as session:
                return session.query(SourceWeb).filter(SourceWeb.question_id == question_id,
                                                       SourceWeb.deleted == False).all()
        except SQLAlchemyError as ex:
            logger.error(f'An error happened on get web sources by question by id for question_id {question_id} {ex}')

            raise DatabaseConnectionError(f'Cannot get source documents {ex}')

    def create_conversation_mock(self, conversation_title: str, user_id: str, conversation_id: str,
                                 workspace_id: str) -> str:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            conversation = Conversation()
            conversation.user_id = user_id
            conversation.id = conversation_id
            conversation.workspace_id = workspace_id
            conversation.title = conversation_title
            session.add(conversation)
            session.commit()
            return conversation.id
