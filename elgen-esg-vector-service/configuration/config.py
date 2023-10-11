from pydantic import BaseSettings, Field

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
    OPENAI_EMBEDDING_TOGGLE: int = Field(env="OPENAI_EMBEDDING_TOGGLE", default=1)
    OPENAI_KEY: str = Field(env="OPENAI_KEY", default="my secret key")


class ElasticSearchConfig(BaseSettings):
    HOST = Field(env="ELASTICSEARCH_HOST", default="localhost")
    PORT = Field(env="ELASTICSEARCH_PORT", default="9201")
    INDEX_NAME = Field(env="ELASTICSEARCH_INDEX_NAME", default="localhost24")


app_config = AppConfig()
vector_db_config = VectorDBConfig()
es_config = ElasticSearchConfig()
