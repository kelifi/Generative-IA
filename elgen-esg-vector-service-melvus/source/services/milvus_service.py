import logging
from typing import List

import numpy as np
from pymilvus import Collection, SearchResult, MilvusException

from configuration.config import MilvusCollectionConfig
from source.exceptions.service_exceptions import EmptyMilvusCollection, MilvusNotFoundError, \
    MilvusSimilaritySearchError, ExistenceCheckError, DataAlreadyInMilvusError
from source.helpers.milvus_helpers import MilvusHelper
from source.schema.requests import StoreDocumentsRequest, SimilarDocumentsOutput
from source.services.abstract import VectorStoreService
from source.utils.embedder_utils import embed_text


class MilvusService(VectorStoreService):

    def __init__(self, milvus_helper: MilvusHelper, milvus_collection_config: MilvusCollectionConfig) -> None:
        self.milvus_collection_config = milvus_collection_config
        self.helper = milvus_helper

    def store_documents(self, data_to_insert: StoreDocumentsRequest) -> int:
        """Insert documents into the milvus collection, create the index on the text_vector, flush the changes and
        return how many records where inserted """

        self.helper.collection.load()
        entities = self.parse_data_object(data_to_insert=data_to_insert)
        logging.info(f'Trying to store the following documents {data_to_insert}')
        result = self.helper.collection.insert(entities)

        self.helper.collection.flush()  # Seal all segments in the collection.
        return result.insert_count

    def get_similar_documents(self, query: str, n_results: int) -> SimilarDocumentsOutput:
        """Get similar document to a certain query as follows:
        - embed the query
        - search for the top_k (also limit) most similar vectors using the L2 distance and get their ids
        - return the documents by their ids
        The returned list is as such [{'text': 'text', 'source': 'file.pdf', 'id': "442692342347989459"}, ...]"""
        # In case the collection is empty, we cannot get any similar docs
        if self.get_total_documents_count() == 0:
            raise EmptyMilvusCollection
        logging.info("Loading data into memory")

        self.helper.collection.load()
        search_param = {
            "data": [embed_text(text=query)],
            "anns_field": self.milvus_collection_config.TEXT_VECTOR_FIELD,
            "param": {"metric_type": self.milvus_collection_config.SIMILARITY_METRIC},
            "limit": n_results,
        }
        logging.info("Searching in Milvus!")
        search_res: SearchResult = self.helper.collection.search(**search_param)

        try:
            ids = search_res[0].ids
        except IndexError:
            raise MilvusSimilaritySearchError

        logging.info("Fetching needed data from results")
        result = []
        for document_id in ids:
            result.append(self.get_data_by_id(document_id))
        self.helper.collection.release()
        logging.info("releasing loaded collection from memory")

        # The id field is a big int and might cause problems when viewing on swagger, for that reason it should be
        # cast into a string type!
        return SimilarDocumentsOutput(data=[{k: str(v) if k == 'id' else v for k, v in d.items()} for d in result],
                                      detail="success")

    def get_data_by_id(self, document_id: int) -> dict:
        """return the record based on the id, the response is a list of 1 element as such:
        {'text': 'text', 'file_name': 'file.pdf', 'file_id' : 'file_id', 'es_id': 'es_id', 'id': 442692342347989459}"""
        expression = f"id=={document_id}"
        query_result = self.helper.collection.query(expression, output_fields=[self.milvus_collection_config.ID_FIELD,
                                                                          self.milvus_collection_config.RAW_TEXT_FIELD,
                                                                          self.milvus_collection_config.FILE_NAME_FIELD,
                                                                          self.milvus_collection_config.FILE_ID_FIELD,
                                                                          self.milvus_collection_config.ELASTICSEARCH_ID_FIELD])
        try:
            return query_result[0]
        except IndexError:
            raise MilvusNotFoundError(detail=f"resource with id {document_id} was not found!")

    def check_existence_by_field(self, field_name: str, field_value) -> bool:
        """Check if data exist in Milvus according to a certain value"""
        checking_expression = f'{field_name}=="{field_value}"'

        try:

            self.helper.collection.load()
            result = bool(self.helper.collection.query(expr=checking_expression))
            self.helper.collection.release()
            return result
        except MilvusException as error:
            raise ExistenceCheckError(expression=checking_expression, milvus_error=error.message)



    def parse_data_object(self, data_to_insert: StoreDocumentsRequest) -> list[dict]:
        """Parse the store document request object into the expected format by the insert function of pymilvus,
         the function will also check if the data rows you are trying to insert are already in milvus and will be ignored"""
        # TODO refactor this function, AA
        documents: List[str] = [single_document.document for single_document in data_to_insert.data]
        vectors: List[np.ndarray] = [embed_text(text=document) for document in documents]
        file_names: List[str] = [single_document.metadata.get("file_name") for single_document in data_to_insert.data]
        file_ids: List[str] = [single_document.metadata.get("file_id") for single_document in data_to_insert.data]
        es_ids: List[str] = [single_document.metadata.get("es_id") for single_document in data_to_insert.data]

        # Take into account only those with no file names already in Milvus
        data = [
            {self.milvus_collection_config.TEXT_VECTOR_FIELD: vector,
             self.milvus_collection_config.RAW_TEXT_FIELD: text,
             self.milvus_collection_config.FILE_NAME_FIELD: file_name,
             self.milvus_collection_config.FILE_ID_FIELD: file_id,
             self.milvus_collection_config.ELASTICSEARCH_ID_FIELD: es_id
             }
            for vector, text, file_name, file_id, es_id in zip(vectors, documents, file_names, file_ids, es_ids) if not
            self.check_existence_by_field(field_name=self.milvus_collection_config.FILE_NAME_FIELD,
                                          field_value=file_name)
        ]

        if not data:
            raise DataAlreadyInMilvusError
        return data

    def get_total_documents_count(self) -> int:
        """Count the number of records in the milvus collection"""
        return self.helper.collection.num_entities
