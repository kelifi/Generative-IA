import logging

import numpy as np
from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch, AuthenticationException, BadRequestError

from configuration.config import ElasticSearchConfig
from source.schema.schemas import Query, Script, QueryScriptScore, QueryBool, QueryMatchAll, QueryTerm


class EmbeddingIndexerHelper:
    def __init__(self, elasticsearch_config: ElasticSearchConfig) -> None:
        self.config = elasticsearch_config
        self.es = self.create_connection()

    def create_connection(self) -> Elasticsearch:
        """

        Returns: The connection instance to elasticsearch

        """
        try:
            elastic_search = Elasticsearch(
                [{'host': self.config.HOST, 'port': int(self.config.PORT), 'scheme': 'http'}])
            logging.info("Successfully connected to elastic search!")
            return elastic_search
        except AuthenticationException as e:
            raise ConnectionError(f"Error creating Elasticsearch connection: {e}")

    def create_index(self, workspace_id: str = '', dimension: int = 768) -> None:
        """

        Returns: None
        Creates the index if it doesnt exist
        """
        index_name = f"{self.config.INDEX_NAME}{workspace_id}"
        if not self.es.indices.exists(index=index_name):
            index_mapping = {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": dimension
                        },
                        "file_name": {"type": "keyword"},
                        "file_id": {"type": "keyword"},
                        "es_id": {"type": "keyword"},
                        "workspace_id": {"type": "keyword"},
                        "text": {"type": "text"}
                    }
                }
            }
            try:
                self.es.indices.create(index=index_name, body=index_mapping)
            except BadRequestError as e:
                raise ConnectionError(f"Error creating index: {e}")

    def store_data(self, entity: dict) -> ObjectApiResponse:
        """

        Args:
            entity: the dict to be stored in the es index

        Returns: The es api response

        """
        try:
            return self.es.index(index=f"{self.config.INDEX_NAME}{entity['workspace_id']}", body=entity)
        except BadRequestError as e:
            raise ConnectionError(f"Error storing data: {e}")

    def search_vector(self, query_embedding: np.ndarray, n_results: int, workspace_id: str) -> ObjectApiResponse:
        """

        Args:
            query_embedding: The embedded vector to search
            n_results: The top results to return
            workspace_id: workspace of user

        Returns:

        """
        try:
            search_body = {"query":
                               {"script_score": QueryScriptScore(
                                   query=Query(
                                       bool=QueryBool(
                                           must=[
                                               QueryMatchAll(match_all={}).dict(),
                                               QueryTerm(term={
                                                   "workspace_id": workspace_id
                                               }).dict()
                                           ]
                                       )
                                   ),
                                   script=Script(
                                       source="cosineSimilarity(params.queryVector, 'embedding') + 1.0",
                                       params={"queryVector": query_embedding.tolist()}
                                   )
                               ).dict()},
                           "size": n_results,
                           "_source": ["file_name", "file_id", "es_id", "text", "score"]
                           }
            return self.es.search(index=f"{self.config.INDEX_NAME}{workspace_id}", body=search_body)
        except BadRequestError as e:
            raise ConnectionError(f"Error searching data data: {e}")

    def search_by_file_name(self, file_name: str, workspace_id: str) -> ObjectApiResponse:
        """

        Args:
            file_name: The file name to check if exits

        Returns: The es api response

        """
        search_body = {
            "query": {
                "term": {
                    "file_name.keyword": file_name
                }
            }
        }
        try:
            return self.es.search(index=f"{self.config.INDEX_NAME}{workspace_id}", body=search_body, size=1)
        except BadRequestError as e:
            raise ConnectionError(f"Error checking existing data: {e}")

    def get_files_count(self, workspace_id: str) -> ObjectApiResponse:
        """count the number of unique files names in the index of elastic search of vector service
        """
        search_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"workspace_id": workspace_id}}
                    ]
                }
            },
            "aggs": {
                "unique_file_names": {
                    "cardinality": {
                        "field": "file_name",
                        "precision_threshold": 1  # treat similar file_name values as a single unique value
                    }
                }
            }
        }

        try:
            return self.es.search(index=f"{self.config.INDEX_NAME}{workspace_id}", body=search_query)
        except BadRequestError as error:
            raise ConnectionError(f"Error checking existing data: {error}")
