from datetime import datetime
from typing import List
from uuid import UUID

from loguru import logger
from sqlalchemy import desc, Row, asc
from sqlalchemy.exc import NoResultFound

from source.helpers.db_helpers import DBHelper
from source.models.db_models import Conversation, Answer, Question, SourceDocument
from source.schemas.conversation_schema import ConversationSchema


class ConversationRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_conversations_by_user(self, user_id: UUID) -> List[Row]:
        """For a certain user id, return the list of all conversation ids"""
        with self.database_helper.session() as session:
            return session.query(Conversation).filter(Conversation.user_id == user_id).order_by(
                desc(Conversation.creation_date)).all()

    def create_conversation(self, conversation_title: str, user_id: UUID) -> UUID:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            conversation = Conversation()
            conversation.user_id = user_id
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
                session.commit()
                session.refresh(conversation)
                return ConversationSchema.from_orm(conversation)
            raise NoResultFound

    def delete_conversation(self, conversation_id: UUID) -> None:
        """Delete a conversation based on its id(Hard delete)"""
        with self.database_helper.session() as session:
            if conversation := session.query(Conversation).get(conversation_id):
                logger.info(f"Deleting conversation with id {conversation_id}")
                session.delete(conversation)
                session.commit()
                return None
            raise NoResultFound

    def get_conversation_by_id(self, conversation_id: UUID) -> List[Row]:
        with self.database_helper.session() as session:
            return session.query(Conversation.id.label("conv_id"), Question.id.label("quest_id"),
                                 Question.content.label("quest_content"),
                                 Question.creation_date.label("quest_date"),
                                 Answer.id.label("answer_id"),
                                 Answer.content.label("answer_content"),
                                 Answer.creation_date.label("answer_date")) \
                .join(Question, Conversation.id == Question.conversation_id) \
                .join(Answer, Question.id == Answer.question_id, isouter=True).filter(
                Conversation.id == conversation_id).order_by(
                asc(Question.creation_date)).all()

    def get_single_conversation_by_id(self, conversation_id: UUID) -> Conversation:
        with self.database_helper.session() as session:
            return session.query(Conversation.id == str(conversation_id)).first()

    def get_sources_by_answer_id(self, answer_id: UUID) -> List[Row]:
        with self.database_helper.session() as session:
            return session.query(SourceDocument).filter(SourceDocument.answer_id == answer_id).all()
