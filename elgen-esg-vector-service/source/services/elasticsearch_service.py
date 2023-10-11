import logging

import numpy as np
from elasticsearch import NotFoundError
from pydantic import ValidationError

from configuration.config import vector_db_config
from source.exceptions.service_exceptions import ElasticsearchStoreDataError, ElasticsearchFetchDataError, \
    ServiceOutputValidationError, ElasticSearchCountError
from source.helpers.elasticsearch_helper import EmbeddingIndexerHelper
from source.schema.requests import StoreDocumentsRequest, SimilarDocumentsOutput
from source.schema.response import DocumentCountResult
from source.schema.schemas import ESDocumentCountSchema
from source.services.abstract import VectorStoreService
from source.utils.common import log_validation_error
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
        workspace_id = entities[0]['workspace_id']
        dimension = len(entities[0]['embedding'])
        self.helper.create_index(workspace_id, dimension)

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

    def check_file_ingested(self, file_name: str, workspace_id: str) -> bool:
        """

        Args:
            file_name: The file name to check if exists in es index

        Returns: A boolean indicating if the file exists

        """
        try:
            response = self.helper.search_by_file_name(file_name, workspace_id)
        except ConnectionError as e:
            logging.error(f'Failed to search similar docs for {file_name}: {e}')
            raise ElasticsearchFetchDataError(f'Failed to search similar docs for {file_name}')

        except NotFoundError as e:
            logging.warning(str(e))
            logging.warning('index was not created for this workspace yet')
            return False
        try:
            return response['hits']['total']['value']
        except KeyError as e:
            logging.error(f'Failed To check existence of file {file_name}: {e}')
            raise ElasticsearchFetchDataError(f'Failed To check existence of file {e}')

    def get_similar_documents(self, query: str, n_results: int, workspace_id: str) -> SimilarDocumentsOutput:
        """

        Args:
            query: The query on which we'll search similar documents
            n_results: The number of similar results to display
            workspace_id: workspace id of the user

        Returns: The similar docs

        """
        query_embedding = embed_text(query, vector_db_config.OPENAI_EMBEDDING_TOGGLE)
        try:
            response = self.helper.search_vector(query_embedding=query_embedding,
                                                 n_results=n_results,
                                                 workspace_id=workspace_id)
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
        documents: list[str] = [single_document.document for single_document in data_to_insert.data]
        vectors: list[np.ndarray] = [embed_text(text=document, openai=vector_db_config.OPENAI_EMBEDDING_TOGGLE) for
                                     document in documents]
        file_names: list[str] = [single_document.metadata.get("file_name") for
                                 single_document in data_to_insert.data]
        file_ids: list[str] = [single_document.metadata.get("file_id") for single_document in data_to_insert.data]
        workspace_ids: list[str] = [single_document.metadata.get("workspace_id") for single_document in
                                    data_to_insert.data]
        es_ids: list[str] = [single_document.metadata.get("es_id") for single_document in data_to_insert.data]

        existing_file_names = [file_name for file_name, workspace_id in list(zip(file_names, workspace_ids)) if
                               self.check_file_ingested(file_name, workspace_id)]

        # Take into account only those with no file names already in Milvus
        data = [
            {"embedding": vector,
             "file_name": file_name,
             "file_id": file_id,
             "workspace_id": workspace_id,
             "es_id": es_id,
             "text": text
             }
            for vector, text, file_name, file_id, workspace_id, es_id in
            zip(vectors, documents, file_names, file_ids, workspace_ids, es_ids) if
            file_name not in existing_file_names
        ]

        if not data:
            return []
        return data

    def count_ingested_documents(self, workspace_id: str) -> ESDocumentCountSchema:
        """Count how many unique files are ingested into Elastic search"""
        try:
            count = self.helper.get_files_count(workspace_id)['aggregations']['unique_file_names']['value']
            logging.info(f"Number of documents is {count}")
            return ESDocumentCountSchema(count=count)

        except KeyError as error:
            logging.error(error)
            raise ElasticSearchCountError(
                detail=f"Could not extract the count key from the count response of elastic search")

        except ConnectionError as error:
            logging.error(error)
            raise ElasticSearchCountError(
                detail="A connection error was encountered while counting the ingested files in elastic search")
        except NotFoundError as e:
            logging.warning(str(e))
            logging.warning('index was not created for this workspace yet')
            return ESDocumentCountSchema(count=0)
        except ValidationError as error:
            logging.error(error)
            raise ElasticSearchCountError(detail=log_validation_error(validation_error=error))
