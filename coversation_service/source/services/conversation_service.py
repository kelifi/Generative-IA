import re
from typing import List
from uuid import UUID

from configuration.logging_setup import logger
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

from source.exceptions.service_exceptions import DatabaseConnectionError, \
    ConversationFetchDataError, ConversationValidationError, ConversationNotFoundError, SourceDocumentsFetchDataError, \
    SourceDocumentsValidationError, DatabaseIntegrityError
from source.repositories.conversation_repository import ConversationRepository
from source.schemas.conversation_schema import ConversationSchema, AnswerSchema, QuestionSchema, ChatSchema, \
    ConversationIdSchema, SourceSchema, WebSourceSchema
from source.schemas.models_schema import ModelServiceAnswer
from source.services.model_service import ModelService


class ConversationService:
    """
    Service class for managing conversations.
    """

    def __init__(self, conversation_repository: ConversationRepository, model_discovery_service: ModelService):
        """
        Initialize the ConversationService.

        Args:
            conversation_repository (ConversationRepository): The conversation repository to use.
        """
        self.conversation_repository = conversation_repository
        self.model_discovery_service = model_discovery_service

    def get_conversations_per_user(self, user_id: UUID, workspace_id: UUID) -> list[ConversationSchema]:
        """
        Get conversations associated with a user.

        Args:
            user_id (UUID): The ID of the user.
            workspace_id (UUID): The ID of the workspace.

        Returns:
            List[ConversationSchema]: A list of conversation schemas.
        """
        try:
            conversations = self.conversation_repository.get_conversations_by_user(user_id=user_id,
                                                                                   workspace_id=workspace_id)
        except DatabaseConnectionError as exc:
            logger.error(f'Failed to get conversation by id due to database issue {user_id} {exc}')

            raise ConversationFetchDataError(f'Unable to get conversation for user {user_id}')
        try:
            return [ConversationSchema.from_orm(conversation) for conversation in conversations]
        except ValidationError as exc:
            logger.error(f'Failed to parse data {user_id} {exc}')

            raise ConversationValidationError('not valid valid passed for ConversationSchema model')

    def get_conversation_by_id(self, conversation_id: UUID) -> ChatSchema:
        """
        Get a conversation by its ID.

        Args:
            conversation_id (UUID): The ID of the conversation.

        Returns:
            ChatSchema: The conversation schema.
        """
        questions_list = []
        try:
            conversations = self.conversation_repository.get_conversation_by_id(conversation_id=conversation_id)
        except NoResultFound:
            logger.error(f'Conversation {conversation_id} is not found')
            raise ConversationNotFoundError(f'Conversation {conversation_id} is not found')
        except DatabaseConnectionError:
            logger.error(f'Cant fetch conversation data conversation_id {conversation_id}')
            raise ConversationFetchDataError('Unable to fetch conversations data')
        if not conversations:
            return ChatSchema(id=conversation_id, questions=questions_list)
        for conversation in conversations:
            try:
                local_sources = self.conversation_repository.get_sources_by_question_id(
                    question_id=conversation.quest_id)
                web_sources = self.conversation_repository.get_web_sources_by_question_id(
                    question_id=conversation.quest_id,
                )
                answer = AnswerSchema(
                    id=conversation.answer_id,
                    content=conversation.answer_content,
                    creation_date=conversation.answer_date,
                    rating=conversation.rating,
                    edited=conversation.edited,
                    update_date=conversation.update_date
                ) if conversation.answer_id else None
            except ValidationError:
                raise ConversationValidationError("Invalid Answer schema !")
            try:
                questions_list.append(
                    QuestionSchema(
                        id=conversation.quest_id,
                        content=conversation.quest_content,
                        creation_date=conversation.quest_date,
                        answer=answer,
                        skip_doc=conversation.skip_doc,
                        skip_web=conversation.skip_web,
                        local_sources=local_sources,
                        web_sources=web_sources,
                    )
                )
            except ValidationError:
                raise ConversationValidationError("Invalid Question schema !")

        try:
            return ChatSchema(id=conversation_id, questions=questions_list)
        except ValidationError:
            logger.error(f'Invalid schema for conversation id {conversation_id}')

            raise ConversationValidationError("Invalid chat schema !")

    def get_web_sources_by_question_id(self, question_id: UUID) -> list[WebSourceSchema]:
        try:
            return [WebSourceSchema.from_orm(data) for data in
                    self.conversation_repository.get_web_sources_by_question_id(question_id)]
        except DatabaseConnectionError:
            raise SourceDocumentsFetchDataError(f'Unable to fetch web sources for question_id: {question_id}')

    def get_conversation_by_question_id(self, question_id: UUID) -> ChatSchema:
        """
        Get a conversation by its ID.

        Args:
            question_id (UUID): The ID of the question.

        Returns:
            ChatSchema: The conversation schema.
        """
        questions_list = []
        try:
            conversation_id, conversations = self.conversation_repository.get_conversation_by_question_id(
                question_id=question_id)
        except NoResultFound:
            raise ConversationNotFoundError(f"Cannot find a conversation for question {question_id}")
        except DatabaseConnectionError:
            raise ConversationFetchDataError('Unable to fetch conversations data')

        for conversation in conversations:
            try:
                answer = AnswerSchema(
                    id=conversation.answer_id,
                    content=conversation.answer_content,
                    creation_date=conversation.answer_date,
                ) if conversation.answer_id else None
            except ValidationError:
                raise ConversationValidationError("Invalid Answer schema !")
            try:
                questions_list.append(
                    QuestionSchema(
                        id=conversation.quest_id,
                        content=conversation.quest_content,
                        creation_date=conversation.quest_date,
                        answer=answer,
                        local_sources=self.conversation_repository.get_sources_by_question_id(
                            question_id=conversation.quest_id),
                        web_sources=self.conversation_repository.get_web_sources_by_question_id(
                            question_id=conversation.quest_id)
                    )
                )
            except ValidationError:
                raise ConversationValidationError("Invalid Question schema !")

        try:
            return ChatSchema(id=conversation_id, questions=questions_list)
        except ValidationError:
            raise ConversationValidationError("Invalid chat schema !")

    def create_conversation(self, conversation_title: str, user_id: UUID, workspace_id: UUID) -> ConversationIdSchema:
        """
        Create a new conversation.

        Args:
            conversation_title (str): The title of the conversation.
            user_id (UUID): The ID of the user.

        Returns:
            ConversationIdSchema: The ID of the created conversation.
        """
        return ConversationIdSchema(
            id=self.conversation_repository.create_conversation(conversation_title=conversation_title, user_id=user_id,
                                                                workspace_id=workspace_id)
        )

    def update_conversation_title(self, new_conversation_title: str, conversation_id: UUID) -> ConversationSchema:
        """
        Update the title of a conversation.

        Args:
            new_conversation_title (str): The new title for the conversation.
            conversation_id (UUID): The ID of the conversation.

        Returns:
            ConversationSchema: The updated conversation schema.
        """
        try:
            return self.conversation_repository.update_conversation_title(
                conversation_id=conversation_id,
                new_conversation_title=new_conversation_title
            )
        except NoResultFound:
            raise ConversationNotFoundError(f'No conversation with id {conversation_id}')
        except DatabaseConnectionError:
            raise ConversationFetchDataError('Unable to update conversations data')

    def delete_conversation(self, conversation_id: UUID) -> None:
        """
        Delete a conversation.

        Args:
            conversation_id (UUID): The ID of the conversation.
        """
        try:
            self.conversation_repository.delete_conversation(conversation_id=conversation_id)
        except DatabaseConnectionError:
            raise ConversationFetchDataError('Unable to fetch conversations data')
        except NoResultFound:
            raise ConversationNotFoundError(f"Cannot delete conversation {conversation_id} as it doesn't exists")

    def get_question_by_id(self, question_id: UUID) -> QuestionSchema:
        """
        Get a question by its ID.

        Args:
            question_id (UUID): The ID of the question.

        Returns:
            QuestionSchema: The question schema.
        """
        try:
            return QuestionSchema.from_orm(self.conversation_repository.get_question_by_id(question_id))
        except DatabaseConnectionError:
            raise ConversationFetchDataError(f'Failed to fetch question data for question_id: {question_id}!')

    async def create_question(self, question: str, conversation_id: UUID, skip_doc: bool,
                              skip_web: bool) -> QuestionSchema:
        """
        Create a new question in a conversation.

        Args:
            question (str): The content of the question.
            conversation_id (UUID): The ID of the conversation.
            skip_doc (bool): The flag for source documents
            skip_web (bool): The flag for web sources

        Returns:
            QuestionSchema: The created question schema.
        """

        try:
            saved_question = QuestionSchema.from_orm(
                self.conversation_repository.create_question(question, conversation_id, skip_doc, skip_web))
        except (DatabaseIntegrityError, DatabaseConnectionError):
            raise ConversationFetchDataError(f'Failed to create a question for conversation {conversation_id}')

        if not self.model_discovery_service.request_question_classification_model(
                question=question).is_specific:
            skip_doc, skip_web = True, True

        try:
            return QuestionSchema.from_orm(
                self.conversation_repository.update_question_sources(saved_question.id, skip_doc, skip_web))
        except (DatabaseConnectionError, NoResultFound):
            raise ConversationFetchDataError(
                f'Failed to update the question {question} for conversation {conversation_id}')
        except ValidationError:
            raise ConversationValidationError('Failed to map data into Question Schema')

    def create_answer(self, question_id: UUID, answer: ModelServiceAnswer) -> AnswerSchema:
        """
        Create an answer for a question.

        Args:
            question_id (UUID): The ID of the question.
            answer (str): The content of the answer.
            model_code (str): the code of the model to be saved in the analytics object

        Returns:
            AnswerSchema: The created answer schema.
        """
        try:
            answer.response = self.post_process_model_answer(answer.response)
            return AnswerSchema.from_orm(self.conversation_repository.create_answer(answer, question_id))
        except DatabaseConnectionError:
            raise ConversationFetchDataError(f'Failed to create answer for question_id: {question_id}')

    def get_source_documents(self, question_id: UUID) -> List[SourceSchema]:
        """
        Get the source documents associated with a question.

        Args:
            question_id (UUID): The ID of the question.

        Returns:
            List[SourceSchema]: A list of source document schemas.
        """
        try:
            return [SourceSchema.from_orm(data) for data in
                    self.conversation_repository.get_sources_by_question_id(question_id)]
        except DatabaseConnectionError:
            raise SourceDocumentsFetchDataError(f'Failed to fetch source docs for question_id {question_id}')

    def create_source_documents(self, question_id: UUID, source_documents: List[SourceSchema]) -> List[SourceSchema]:
        """
        Create source documents for a question.

        Args:
            question_id (UUID): The ID of the question.
            source_documents (List[SourceSchema]): A list of source document schemas.

        Returns:
            List[SourceSchema]: The created source document schemas.
        """

        try:
            return [SourceSchema.from_orm(
                self.conversation_repository.create_source_document(question_id, source_document.file_name,
                                                                    source_document.content,
                                                                    source_document.document_type,
                                                                    source_document.document_id))
                for source_document in source_documents]
        except DatabaseConnectionError:
            raise SourceDocumentsFetchDataError('Failed to create new source documents because of db connection error')
        except ValidationError:
            raise SourceDocumentsValidationError('Failed to validate source documents schema')

    def create_web_sources(self, question_id: UUID, web_sources: List[WebSourceSchema]) -> List[WebSourceSchema]:
        """
        Create source documents for a question.

        Args:
            question_id (UUID): The ID of the question.
            web_sources (List[WebSourceSchema]): A list of source from the web schemas.

        Returns:
            List[WebSourceSchema]: The created source document schemas.
        """
        try:
            return [WebSourceSchema.from_orm(
                self.conversation_repository.create_web_source(question_id=question_id, url=web_source.url,
                                                               description=web_source.description,
                                                               title=web_source.title,
                                                               paragraphs=web_source.paragraphs))
                for web_source in web_sources]
        except DatabaseConnectionError:
            raise SourceDocumentsFetchDataError('Failed to create new source documents because of db connection error')
        except ValidationError:
            raise SourceDocumentsValidationError('Failed to validate source documents schema')

    @staticmethod
    def post_process_model_answer(answer: str) -> str:
        """
        Remove from model answer successive occurrences of the newline character
        Args:
            answer: answer generated by model

        Returns:
            answer post-processed
        """
        return re.sub(r'\n+', '\n', answer)
