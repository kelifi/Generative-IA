from datetime import datetime
from typing import Type
from uuid import UUID

from configuration.logging_setup import logger
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from source.exceptions.service_exceptions import DataLayerError, AnswerNotFoundException
from source.helpers.db_helpers import DBHelper
from source.models.conversations_models import Answer, VersionedAnswer
from source.schemas.answer_schema import AnswerRatingEnum


class AnswerRepository:
    def __init__(self, database_helper: DBHelper, data_model: Type[Answer],
                 versioning_data_model: Type[VersionedAnswer]) -> None:
        self._database_helper = database_helper
        self.data_model = data_model
        self.versioning_data_model = versioning_data_model

    def update_rating_for_answer(self, answer_id: UUID, rating: AnswerRatingEnum) -> int:
        """
        Method to update an answer with a rating value
        """
        try:
            with self._database_helper.session() as session:
                result = session.query(self.data_model).filter(self.data_model.id == str(answer_id)).update({
                    "rating": str(rating)
                })
                session.commit()

                return result

        except SQLAlchemyError as error:
            session.rollback()
            logger.error(error)
            raise DataLayerError(message='Unexpected Error!') from error

    def get_latest_versioned_answer(self, answer_id: UUID):
        """
        Given an answer, get its latest older version
        """
        try:
            with self._database_helper.session() as session:
                target_table = self.versioning_data_model
                return session.query(target_table).filter(target_table.answer_id == str(answer_id)).order_by(
                    desc(self.versioning_data_model.creation_date)).first()

        except SQLAlchemyError as error:
            logger.error(error)
            raise DataLayerError(message='Unexpected Error!') from error

    def update_answer_with_versioning(self, answer_id: UUID, content: str) -> Answer:
        """
        Update an answer with new content and save the old one as an entry in versioned answer table
        """
        try:
            with self._database_helper.session() as session:
                answer = session.query(self.data_model).filter(self.data_model.id == str(answer_id)).first()

                if not answer:
                    raise AnswerNotFoundException()
                old_answer = self.versioning_data_model(
                    content=answer.content,
                    rating=answer.rating,
                    edited=answer.edited,
                    creation_date=answer.creation_date,
                    update_date=datetime.now(),
                    author=answer.author,
                    answer_id=answer.id
                )
                session.add(old_answer)
                answer.content = content
                answer.rating = None
                answer.edited = True
                session.commit()
                session.refresh(answer)
                return answer

        except SQLAlchemyError as error:
            logger.error(error)
            raise DataLayerError(message='Unexpected Error!') from error
