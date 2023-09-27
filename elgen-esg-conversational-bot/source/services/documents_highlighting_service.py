from os.path import basename
from pathlib import Path

from pydantic import ValidationError

from configuration.config import app_config
from source.exceptions.service_exceptions import UnvalidQueryError, InternalDataBaseError, PostgresRetrievalError, \
    NoDataFound
from source.helpers.source_document_router_helper import DocumentHighlightHelper
from source.schemas.source_document_schemas import SourceDocumentOutputSchema
from source.utils.pdf_utils import highlight_file


class DocumentHighlightService:

    def __init__(self, db_helper: DocumentHighlightHelper):
        self._db_helper = db_helper

    def get_document_and_text(self, source_document_id: str) -> SourceDocumentOutputSchema:
        """

        @param source_document_id: The source document id, that will be looked for in the internal db
        @return: The Source documentOutputSchema containing the file path and the text
        """
        try:
            return SourceDocumentOutputSchema.from_orm(self._db_helper.get_file_by_source_id(source_document_id))
        except (UnvalidQueryError, InternalDataBaseError) as exc:
            raise PostgresRetrievalError(f"Unable to retrieve information from postgres : {exc.__str__()}")
        except ValidationError as exc:
            raise NoDataFound(f"No data found {exc.__str__()}")

    def get_annotated_file(self, elm: SourceDocumentOutputSchema) -> str or None:
        """

        @param elm: The element to be annotated, it contains the file path and the text to be highlighted
        @return: The path of the temp highlighted doc
        """
        file_path = str(Path(app_config.SOURCE_DIRECTORY, basename(elm.document_path)))
        return highlight_file(file_path, elm.text)
