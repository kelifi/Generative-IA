from loguru import logger
from pymilvus import connections, CollectionSchema, Collection, MilvusException
from pymilvus.orm import db

from configuration.config import MilvusDatabaseConfig, MilvusCollectionConfig


class MilvusHelper:
    def __init__(self, milvus_database_configuration: MilvusDatabaseConfig,
                 milvus_collection_config: MilvusCollectionConfig) -> None:
        self.milvus_database_configuration = milvus_database_configuration
        self.milvus_collection_config = milvus_collection_config
        self.connect_to_milvus()
        self.create_milvus_database()
        self.collection = self.create_collection_from_schema()

    def connect_to_milvus(self) -> None:
        """Connect to a running milvus instance, if no running instance was found the application will not run!"""
        logger.info(
            f"Connecting to Milvus on {self.milvus_database_configuration.MILVUS_HOST}:{self.milvus_database_configuration.MILVUS_PORT}")
        try:
            connections.connect(host=self.milvus_database_configuration.MILVUS_HOST,
                                port=self.milvus_database_configuration.MILVUS_PORT)
        except MilvusException as milvus_error:
            logger.error(
                f"Milvus raised an error with code {milvus_error.code} for the following error {milvus_error.message}")
            exit(123)

    def create_collection_from_schema(self) -> Collection:
        """Create a collection from the specified documents_schema and its index"""
        documents_schema = CollectionSchema(fields=self.milvus_collection_config.fields_schema,
                                            collection_name=self.milvus_collection_config.COLLECTION_NAME)
        collection = Collection(name=self.milvus_collection_config.COLLECTION_NAME, schema=documents_schema)

        collection.create_index(self.milvus_collection_config.TEXT_VECTOR_FIELD,
                                {"index_type": "FLAT", "metric_type": self.milvus_collection_config.SIMILARITY_METRIC,
                                 "params": {}})
        return collection

    def create_milvus_database(self) -> None:
        """Login to milvus and create a database to store collections inside"""
        # Must connect to the running milvus instance at before invoking this function
        try:
            db.create_database(self.milvus_database_configuration.MILVUS_DB_NAME)
            logger.info(f"Milvus DB {self.milvus_database_configuration.MILVUS_DB_NAME} was created with success")
        except MilvusException as error:
            logger.error(f"DB creation failed with code {error.code}, for the following reason: {error.message}")
