from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch, AuthenticationException, BadRequestError
import numpy as np

from configuration.config import ElasticSearchConfig


class EmbeddingIndexerHelper:
    def __init__(self, elasticsearch_config: ElasticSearchConfig) -> None:
        self.config = elasticsearch_config
        self.es = self.create_connection()
        self.create_index()

    def create_connection(self) -> Elasticsearch:
        """
        
        Returns: The connection instance to elasticsearch

        """
        try:
            return Elasticsearch([{'host': self.config.HOST, 'port': int(self.config.PORT), 'scheme': 'http'}])
        except AuthenticationException as e:
            raise ConnectionError(f"Error creating Elasticsearch connection: {e}")

    def create_index(self) -> None:
        """
        
        Returns: None 
        Creates the index if it doesnt exist
        """
        if not self.es.indices.exists(index=self.config.INDEX_NAME):
            index_mapping = {
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 768
                        },
                        "file_name": {"type": "keyword"},
                        "file_id": {"type": "keyword"},
                        "es_id": {"type": "keyword"},
                        "text": {"type": "text"}
                    }
                }
            }
            try:
                self.es.indices.create(index=self.config.INDEX_NAME, body=index_mapping)
            except BadRequestError as e:
                raise ConnectionError(f"Error creating index: {e}")

    def store_data(self, entity: dict) -> ObjectApiResponse:
        """
        
        Args:
            entity: the dict to be stored in the es index

        Returns: The es api response

        """
        try:
            return self.es.index(index=self.config.INDEX_NAME, body=entity)
        except BadRequestError as e:
            raise ConnectionError(f"Error storing data: {e}")

    def search_vector(self, query_embedding: np.ndarray, n_results: int) -> ObjectApiResponse:
        """

        Args:
            query_embedding: The embedded vector to search
            n_results: The top results to return

        Returns:

        """
        try:
            search_body = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.queryVector, 'embedding') + 1.0",
                            "params": {"queryVector": query_embedding.tolist()}
                        }
                    }
                },
                "size": n_results,
                "_source": ["file_name", "file_id", "es_id", "text", "score"]
            }
            return self.es.search(index=self.config.INDEX_NAME, body=search_body)
        except BadRequestError as e:
            raise ConnectionError(f"Error searching data data: {e}")

    def search_by_file_name(self, file_name: str) -> ObjectApiResponse:
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
            return self.es.search(index=self.config.INDEX_NAME, body=search_body, size=1)
        except BadRequestError as e:
            raise ConnectionError(f"Error checking existing data: {e}")
