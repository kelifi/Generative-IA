import logging
from typing import List

import numpy as np
from pydantic import ValidationError

from source.exceptions.service_exceptions import ElasticsearchStoreDataError, ElasticsearchFetchDataError, \
    ServiceOutputValidationError
from source.helpers.elasticsearch_helper import EmbeddingIndexerHelper
from source.schema.requests import StoreDocumentsRequest, SimilarDocumentsOutput
from source.schema.response import DocumentCountResult
from source.services.abstract import VectorStoreService
from source.utils.embedder_utils import embed_text


class EmbeddingIndexerService(VectorStoreService):
    def __init__(self, helper: EmbeddingIndexerHelper) -> None:
        self.helper = helper

    def store_documents(self, data_to_insert: StoreDocumentsRequest) -> DocumentCountResult:
        """

        Args:
            data_to_insert: The data that will be parsed and stored into es

        Returns: The count of the data

        """
        entities = self.parse_data_object(data_to_insert=data_to_insert)
        for entity in entities:
            try:
                self.helper.store_data(entity)
            except ConnectionError as e:
                logging.error(f'failed to store data into elasticsearch {e}')
                raise ElasticsearchStoreDataError(f'Failed to store data into ElasticSearch {e}')
        try:
            return DocumentCountResult(count=len(entities))
        except ValidationError as e:
            logging.error(f'failed to fit data in the schema {e}')
            raise ServiceOutputValidationError(f'Failed to parse data for stored documents {e}')

    def check_file_ingested(self, file_name: str) -> bool:
        """

        Args:
            file_name: The file name to check if exists in es index

        Returns: A boolean indicating if the file exists

        """
        try:
            response = self.helper.search_by_file_name(file_name)
        except ConnectionError as e:
            logging.error(f'Failed to search similar docs for {file_name}: {e}')
            raise ElasticsearchFetchDataError(f'Failed to search similar docs for {file_name}')
        try:
            return response['hits']['total']['value']
        except KeyError as e:
            logging.error(f'Failed To check existence of file {file_name}: {e}')
            raise ElasticsearchFetchDataError(f'Failed To check existence of file {e}')

    def get_similar_documents(self, query: str, n_results: int) -> SimilarDocumentsOutput:
        """

        Args:
            query: The query on which we'll search similar documents
            n_results: The number of similar results to display

        Returns: The similar docs

        """
        query_embedding = embed_text(query)
        try:
            response = self.helper.search_vector(query_embedding, n_results)
        except ConnectionError as e:
            logging.error(f'Failed to search similar docs for {query}: {e}')
            raise ElasticsearchFetchDataError(f'Failed to search similar docs for {query}')

        hits = response.get("hits", {}).get("hits", [])
        try:
            return SimilarDocumentsOutput(
                data=[{"score": hit.get("_score", 0.0), **hit.get("_source", {})} for hit in hits],
                detail="success")
        except ValidationError as e:
            logging.error(f'failed to fit data in the schema {e}')
            raise ServiceOutputValidationError(f'Failed to parse data for fetched documents {e}')

    def parse_data_object(self, data_to_insert: StoreDocumentsRequest) -> list[dict]:

        """Parse the store document request object into the expected format by the insert function of pymilvus,
         the function will also check if the data rows you are trying to insert are already in milvus and will be ignored"""
        """"""
        documents: List[str] = [single_document.document for single_document in data_to_insert.data]
        vectors: List[np.ndarray] = [embed_text(text=document) for document in documents]
        file_names: List[str] = [single_document.metadata.get("file_name") for single_document in data_to_insert.data]
        file_ids: List[str] = [single_document.metadata.get("file_id") for single_document in data_to_insert.data]
        es_ids: List[str] = [single_document.metadata.get("es_id") for single_document in data_to_insert.data]

        existing_file_names = [file_name for file_name in list(set(file_names)) if self.check_file_ingested(file_name)]

        # Take into account only those with no file names already in Milvus
        data = [
            {"embedding": vector,
             "file_name": file_name,
             "file_id": file_id,
             "es_id": es_id,
             "text": text
             }
            for vector, text, file_name, file_id, es_id in zip(vectors, documents, file_names, file_ids, es_ids) if
            file_name not in existing_file_names
        ]

        if not data:
            return []
        return data
