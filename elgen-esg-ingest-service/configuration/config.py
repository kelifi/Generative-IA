from pydantic import BaseSettings, Field

from source.schema.base import AppEnv


class AppConfig(BaseSettings):
    APP_HOST = Field(env="APP_HOST", default="localhost")
    APP_PORT = Field(env="APP_PORT", default=8015)
    APP_ENV = Field(env="APP_ENV", default=AppEnv.PROD)
    WORKERS_COUNT: int = Field(env="WORKERS_COUNT", default=1)
    PROJECT_NAME: str = Field(env="PROJECT_NAME", default="EL-GEN-ingest-service")
    ROOT_PATH: str = Field(env="ROOT_PATH", default="/api")


class DocumentsConfig(BaseSettings):
    SOURCE_DIRECTORY = Field(env="SOURCE_DIRECTORY", default="artifacts")


class ElasticSearchConfig(BaseSettings):
    HOST = Field(env='ES_HOST', default='localhost')
    PORT = Field(env='ES_PORT', default=9201)
    INGESTION_INDEX = Field(env='INGESTION_INDEX', default='documents')
    TASK_INDEX = Field(env='TASK_INDEX', default='tasks')
    FIELD_NAME = Field(env='ES_FIELD_NAME', default='doc_field')
    PIPELINE_NAME = Field(env='ES_PIPELINE_NAME', default='attachment')

    @property
    def ES_URL(self):
        return f'http://{self.HOST}:{self.PORT}'


class TextProcessingConfig(BaseSettings):
    CHUNK_SIZE: int = Field(env="CHUNK_SIZE", default=150)
    CHUNK_OVERLAP: int = Field(env="CHUNK_OVERLAP", default=30)
    TARGET_SOURCE_CHUNKS = Field(env="TARGET_SOURCE_CHUNKS", default=8)


class VectorStoreApiConfig(BaseSettings):
    HOST = Field(env='VEC_HOST', default='localhost')
    PORT = Field(env='VEC_PORT', default=8004)
    STORE_ENDPOINT = Field(env="VEC_STORE_ENDPOINT", default="milvus/store-data")

    @property
    def VEC_URL(self):
        return f"http://{self.HOST}:{self.PORT}"

    @property
    def VEC_STORE_URL(self):
        return f"{self.VEC_URL}/{self.STORE_ENDPOINT}"


app_config = AppConfig()
doc_config = DocumentsConfig()

text_proc_config = TextProcessingConfig()

es_config = ElasticSearchConfig()

vec_api_config = VectorStoreApiConfig()
