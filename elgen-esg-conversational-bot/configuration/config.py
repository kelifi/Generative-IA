import os

from chromadb.config import Settings
from pydantic import BaseSettings, Field

from source.schemas.common_schema import AppEnv


class AppConfig(BaseSettings):
    APP_HOST = Field(env="APP_HOST", default="localhost")
    APP_PORT = Field(env="APP_PORT", default=7777)
    APP_ENV = Field(env="APP_ENV", default=AppEnv.prod)
    WORKERS_COUNT: int = Field(env="WORKERS_COUNT", default=5)
    embeddings_model_name = Field(env="EMBEDDINGS_MODEL_NAME", default="all-distilroberta-v1")
    TOP_K = Field(env="TOP_K", default=2,
                  description="How many source documents to use in the query input for the model")

    PERSIST_DIRECTORY = Field(env='PERSIST_DIRECTORY', default="db")

    model_type = Field(env='MODEL_TYPE', default="GPT4ALL")
    model_url = Field(env='MODEL_URL', default="https://huggingface.co/orel12/ggml-gpt4all-j-v1.3-groovy/"
                                               "resolve/main/ggml-gpt4all-j-v1.3-groovy.bin")
    model_path = Field(env='MODEL_PATH', default="artifacts/ggml-gpt4all-j-v1.3-groovy.bin")
    model_n_ctx = Field(env='MODEL_N_CTX', default=1000)

    SOURCE_DIRECTORY = Field(env="SOURCE_DIRECTORY", default="artifacts/source_documents/")
    TARGET_SOURCE_CHUNKS = Field(env="TARGET_SOURCE_CHUNKS", default=8)
    FALCON_MODEL_PATH = Field(env='FALCON_MODEL_PATH', default="tiiuae/falcon-7b-instruct")
    LOCAL_FALCON_MODEL_PATH = Field(env='LOCAL_FALCON_MODEL_PATH', default="artifacts/models/falcon/")
    OPENAI_API_KEY = Field(env="OPENAI_API_KEY", default="")
    OPENAI_MODEL_NAME = Field(env="OPENAI_MODEL_NAME", default="gpt-3.5-turbo")


class ReportGenerationConfig(BaseSettings):
    tmp_file_path = os.path.join(os.getcwd(), "report.pdf")


class DataBaseConfig(BaseSettings):
    """Configuration class for connecting to the accompanying database"""
    DB_HOST: str = Field(env='DB_HOST', default='localhost', description="Host for running the database instance")
    DB_PORT: int = Field(env='DB_PORT', default=5433, description="Port for running the database instance")
    DB_NAME: str = Field(env='DB_NAME', default='elgen_esg_cb_database', description="Database name")
    DB_USER: str = Field(env='DB_USER', default='root', description="Username to access the database")
    DB_PASSWORD: str = Field(env='DB_PASSWORD', default='root', description="Account password")

    @property
    def db_url(self):
        return f"postgresql://{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}" \
               f"?user={self.DB_USER}&password={self.DB_PASSWORD}"


class MongoBaseConfig(BaseSettings):
    """Configuration class for connecting to mongo database"""
    HOST = Field(env='MONGO_DB_HOST', default='localhost')
    PORT = Field(env='MONGO_DB_PORT', default=27018)
    USER = Field(env='MONGO_INITDB_ROOT_USERNAME', default='root')
    PASSWORD = Field(env='MONGO_INITDB_ROOT_PASSWORD', default='root')
    DATABASE = Field(env='MONGO_INITDB_DATABASE', default='elgen_mongo_db')
    ID_COLLECTION = Field(env='MONGO_ID_COLLECTION', default='Reports')
    URI = Field(env='MONGO_URI', default=f'mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}/?authSource={DATABASE}')


class ElasticSearchConfig(BaseSettings):
    HOST = Field(env='ES_HOST', default='localhost')
    PORT = Field(env='ES_PORT', default=9201)
    INGESTION_INDEX = Field(env='INGESTION_INDEX', default='ingested_docs')
    FIELD_NAME = Field(env='ES_FIELD_NAME', default='doc_field')
    PIPELINE_NAME = Field(env='ES_PIPELINE_NAME', default='attachment')

    @property
    def ES_URL(self):
        return f'http://{self.HOST}:{self.PORT}'


class EmbedderSettings(BaseSettings):
    CHUNK_SIZE: int = Field(env="CHUNK_SIZE", default=350)
    CHUNK_OVERLAP: int = Field(env="CHUNK_OVERLAP", default=50)
    IGNORE_TOKEN_LENGTH:  int = Field(env="IGNORE_TOKEN_LENGTH", default=30)


app_config = AppConfig()
es_config = ElasticSearchConfig()
embedder_settings = EmbedderSettings()

db_config = DataBaseConfig()

CHROMA_SETTINGS = Settings(
    chroma_db_impl='duckdb+parquet',
    persist_directory=app_config.PERSIST_DIRECTORY,
    anonymized_telemetry=False
)
