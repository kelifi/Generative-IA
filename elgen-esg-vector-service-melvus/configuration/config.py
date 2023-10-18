from pydantic import BaseSettings, Field
from pymilvus import FieldSchema, DataType

from source.schema.base import AppEnv


class AppConfig(BaseSettings):
    APP_HOST = Field(env="APP_HOST", default="localhost")
    APP_PORT = Field(env="APP_PORT", default=8004)
    APP_ENV = Field(env="APP_ENV", default=AppEnv.prod)
    WORKERS_COUNT: int = Field(env="WORKERS_COUNT", default=1)
    PROJECT_NAME: str = Field(env="PROJECT_NAME", default="EL-GEN-vector-service")
    ROOT_PATH: str = Field(env="ROOT_PATH", default="/api")


class VectorDBConfig(BaseSettings):
    EMBEDDING_FUNCTION_NAME = Field(env="EMBEDDINGS_MODEL_NAME", default="all-distilroberta-v1")
    TOP_K = Field(env="TOP_K", default=2,
                  description="How many source documents to use in the query input for the model")

    PERSIST_DIRECTORY = Field(env='PERSIST_DIRECTORY', default="db")

    SOURCE_DIRECTORY = Field(env="SOURCE_DIRECTORY", default="artifacts/source_documents/")
    TARGET_SOURCE_CHUNKS = Field(env="TARGET_SOURCE_CHUNKS", default=8)

    DEFAULT_COLLECTION_NAME: str = Field(env="DEFAULT_COLLECTION_NAME", default="vectors")


class MilvusDatabaseConfig(BaseSettings):
    MILVUS_HOST: str = Field(env="MILVUS_HOST", default='localhost')
    MILVUS_PORT: str = Field(env="MILVUS_PORT", default='19530')
    MILVUS_PASSWORD: str = Field(env="MILVUS_PASSWORD", default='password')
    MILVUS_USER: str = Field(env="MILVUS_USER", default='username')
    MILVUS_ALIAS: str = Field(env="MILVUS_ALIAS", default='my_session')
    MILVUS_DB_NAME: str = Field(env="MILVUS_DB_NAME", default="elgen_milvus_database")


class MilvusCollectionConfig(BaseSettings):
    COLLECTION_NAME: str = Field(env="COLLECTION_NAME", default="elgen_mivus_collection2",
                                 description="the milvus collection name")
    TEXT_VECTOR_FIELD: str = Field(env="TEXT_VECTOR_FIELD", default="text_vector",
                                   description="the field name for the embedding vector")
    RAW_TEXT_FIELD: str = Field(env="RAW_TEXT_FIELD", default="text",
                                description="the field name for the raw text data")
    RAW_TEXT_MAX_LENGTH: int = Field(env="RAW_TEXT_MAX_LENGTH", default=10000,
                                     description="the maximum length the raw text data can be")
    FILE_NAME_FIELD: str = Field(env="FILE_NAME_FIELD", default="file_name",
                                 description="the file name")
    FILE_NAME_FIELD_MAX_LENGTH: int = Field(env="FILE_NAME_FIELD_MAX_LENGTH", default=100,
                                            description="the maximum length of the file name")
    FILE_ID_FIELD: str = Field(env="FILE_ID_FIELD+", default="file_id",
                               description="the file id")
    FILE_ID_FIELD_MAX_LENGTH: int = Field(env="FILE_ID_FIELD_MAX_LENGTH", default=100,
                                          description="the maximum length of the file_id")
    ELASTICSEARCH_ID_FIELD: str = Field(env="ELASTICSEARCH_ID_FIELD", default="es_id",
                                        description="the path to the source file, usually it is the name of the pdf file")
    ELASTICSEARCH_ID_FIELD_MAX_LENGTH: int = Field(env="ELASTICSEARCH_ID_FIELD_MAX_LENGTH", default=100,
                                                   description="the maximum length of the es_id")
    ID_FIELD: str = Field(env="SOURCE_FIELD_MAX_LENGTH", default="id")
    TEXT_VECTOR_FIELD_DIMENSION: int = Field(env="SOURCE_FIELD_MAX_LENGTH",
                                             default=768,
                                             description="the embedding dimension of the vectors in milvus")  # TODO change this to be a dynamic value using for example embedding_size = model.get_sentence_embedding_dimension()
    SIMILARITY_METRIC: str = Field(env="SIMILARITY_METRIC", default="L2",
                                   description="The metric used to compare two embedding vectors in Milvus DB")

    @property
    def fields_schema(self) -> list[FieldSchema]:
        """Create the milvus collection schema"""
        return [
            FieldSchema(name=self.TEXT_VECTOR_FIELD, dtype=DataType.FLOAT_VECTOR,
                        dim=self.TEXT_VECTOR_FIELD_DIMENSION),
            FieldSchema(name=self.RAW_TEXT_FIELD, dtype=DataType.VARCHAR, max_length=self.RAW_TEXT_MAX_LENGTH),
            FieldSchema(name=self.ID_FIELD, dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name=self.FILE_NAME_FIELD, dtype=DataType.VARCHAR, max_length=self.FILE_NAME_FIELD_MAX_LENGTH),
            FieldSchema(name=self.FILE_ID_FIELD, dtype=DataType.VARCHAR, max_length=self.FILE_ID_FIELD_MAX_LENGTH),
            FieldSchema(name=self.ELASTICSEARCH_ID_FIELD, dtype=DataType.VARCHAR,
                        max_length=self.ELASTICSEARCH_ID_FIELD_MAX_LENGTH)
        ]


app_config = AppConfig()
vector_db_config = VectorDBConfig()
milvus_database_config = MilvusDatabaseConfig()
milvus_collection_config = MilvusCollectionConfig()
