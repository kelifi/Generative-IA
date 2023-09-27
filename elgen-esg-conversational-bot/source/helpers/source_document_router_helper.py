import logging
from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session
from sqlalchemy.exc import  ProgrammingError, SQLAlchemyError

from source.exceptions.service_exceptions import InternalDataBaseError, UnvalidQueryError
from source.models.db_models import SourceDocument


class DocumentHighlightHelper:

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory

    def get_file_by_source_id(self, source_id_document: str):
        with self.session_factory() as session:
            try:
                data = session.query(SourceDocument.document_path, SourceDocument.content.label('text')).filter(
                    SourceDocument.id == source_id_document).first()
            except ProgrammingError as exc:
                logging.error(f'Internal Database Error: {exc.__str__()}')
                raise UnvalidQueryError()
            except SQLAlchemyError  as exc:
                logging.error(f'Internal Database Error: {exc.__str__()}')
                raise InternalDataBaseError()

        return data
