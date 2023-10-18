from typing import Optional, List

from chromadb import Client
from chromadb.errors import DuplicateIDError
from loguru import logger

from configuration.config import VectorDBConfig
from source.exceptions.service_exceptions import DataLayerError, DBRuntimeError
from source.helpers.embedding_helpers import get_embedding_function


class VectorCollection:
    # TODO make this an abstract class, then implement specific chroma interface
    def __init__(self, client: Client,
                 config: VectorDBConfig,
                 ):
        self.client = client
        self.config = config

        self.collection = self.client.get_or_create_collection(
            name=self.config.DEFAULT_COLLECTION_NAME,
            embedding_function=get_embedding_function(embedding_function_name=self.config.EMBEDDING_FUNCTION_NAME))

    def __len__(self) -> int:
        return self.collection.count()

    def head(self, limit: int = 10):
        return self.collection.peek(limit=limit)

    def update_collection(self, name: Optional[str] = None, **kwargs):
        self.collection.modify(name, kwargs)

    def add_documents(self, ids: List[str],
                      documents: Optional[List[str]] = None,
                      embeddings: Optional[List[List[float]]] = None,
                      metadatas: Optional[List[dict]] = None):

        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except (ValueError, DuplicateIDError) as error:
            # DuplicateIDError, when two ids are the same, catch it in any case, so if it happens, we revise it
            # ValueError for not identical order, for ex len(documents) != len(ids), usually should not happen
            # value error for empty embedder, when the embedding is missing
            logger.error(error)
            raise DataLayerError("Internal Error!") from error

    def get_similar_documents_by_text(self, query_texts: List[str],
                                      n_results: int = 4, where_document=None,
                                      where_metdata_fields=None,
                                      ):

        try:
            return self.collection.query(
                n_results=n_results,
                query_texts=query_texts,
                where=where_metdata_fields,
                where_document=where_document,
                include=["documents", "metadatas"],
            )
        except RuntimeError as error:
            # I randomly made this exception, I don't know yet why it did happen, but will catch it regardless
            logger.error(error)
            raise DBRuntimeError()
