from uuid import UUID

from sqlalchemy import Row

from source.helpers.db_helpers import DBHelper
from source.models.db_models import Answer, SourceDocument


class AnswerRepository:

    def __init__(self, database_helper: DBHelper):
        self.database_helper = database_helper

    def get_answer_by_id(self, answer_id: UUID) -> Row:
        """For a certain user id, return the list of all conversation ids"""
        with self.database_helper.session() as session:
            return session.query(Answer).filter(Answer.id == answer_id).one_or_none()

    def create_answer(self, answer: str, question_id: UUID) -> Row:
        """Create a conversation and return its id"""
        with self.database_helper.session() as session:
            answer_object = Answer()
            answer_object.content = answer
            answer_object.question_id = question_id
            session.add(answer_object)
            session.commit()
            return answer_object

    def create_source_document(self, answer_id: str, document_path: str, content: str, document_type: str) -> Row:
        with self.database_helper.session() as session:
            existing_source_document = session.query(SourceDocument).filter_by(answer_id=answer_id,
                                                                               document_path=document_path,
                                                                               content=content).first()
            if not existing_source_document:  # Check if the source document has already been added to this answer
                source_object = SourceDocument()
                source_object.answer_id = answer_id
                source_object.document_path = document_path
                source_object.content = content
                source_object.document_type = document_type
                session.add(source_object)
                session.commit()
                return source_object
            return existing_source_document
