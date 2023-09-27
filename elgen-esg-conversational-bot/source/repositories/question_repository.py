from typing import List
from uuid import UUID

from sqlalchemy import Row

from source.helpers.db_helpers import DBHelper
from source.models.db_models import Question


class QuestionRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_question_by_id(self, question_id: UUID) -> Row:
        """For a certain user id, return the list of all conversation ids"""
        with self.database_helper.session() as session:
            return session.query(Question).filter(Question.id == question_id).one_or_none()

    def create_question(self, question: str, conversation_id: UUID) -> Row:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            question_object = Question()
            question_object.content = question
            question_object.conversation_id = conversation_id
            session.add(question_object)
            session.commit()
            return question_object
