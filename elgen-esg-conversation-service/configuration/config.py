from pydantic import BaseSettings, Field, AnyUrl

from source.schemas.common import AppEnv


class AppConfig(BaseSettings):
    APP_HOST: str = Field(env="APP_HOST", default="localhost")
    APP_PORT: int = Field(env="APP_PORT", default=8001)
    APP_ENV: AppEnv = Field(env="APP_ENV", default=AppEnv.PROD)
    NB_OF_WORKERS: int = Field(env="NB_OF_WORKERS", default=3)

    PROJECT_NAME: str = Field(env="PROJECT_NAME", default="EL-GEN-conversation-service")
    ROOT_PATH: str = Field(env="ROOT_PATH", default="/api")

    # Source Service config
    SOURCE_SERVICE_HOST = Field(env="SOURCE_SERVICE_HOST", default='localhost')
    SOURCE_SERVICE_PORT = Field(env="SOURCE_SERVICE_PORT", default=8002)
    SOURCES_SERVICE_URL: str = Field(env="SOURCES_SERVICE_URL", default=None)
    SOURCE_SERVICE_PREDICT_URI = Field(env="SOURCE_SERVICE_PREDICT_URI", default='/sources/web')

    @property
    def source_service_url(self):
        return self.SOURCES_SERVICE_URL or f"https://{self.SOURCE_SERVICE_HOST}:{self.SOURCE_SERVICE_PORT}"


class ModelsConfig(BaseSettings):
    GENERATIVE_MODEL_INFERENCE_ENDPOINT = Field(env="GENERATIVE_MODEL_INFERENCE_ENDPOINT ", default="/inference",
                                                description="Append to the url from model "
                                                            "registry table to obtain full url")
    STREAMING_GENERATIVE_MODEL_INFERENCE_ENDPOINT = Field(env="GENERATIVE_MODEL_INFERENCE_ENDPOINT ",
                                                          default="/inference/stream",
                                                          description="Append to the url from model "
                                                                      "registry table to obtain full url")

    TOPIC_CLASSIFICATION_ENDPOINT = Field(env="TOPIC_CLASSIFICATION_ENDPOINT", default="/v1/topic/classification/")


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


class SummarizationConfig(BaseSettings):
    """Configuration class for summarization"""
    NUM_LINES: int = Field(env="NUM_LINES", default=5)


class StreamingResponseConfig(BaseSettings):
    STREAMING_CHUNK_SIZE: int = Field(env="STREAMING_CHUNK_SIZE",
                            description="streaming chunk size to be parsed at a time",
                            default=1024 * 4
                            )


class QuestionConfig(BaseSettings):
    """Configuration for question content size limits"""
    QUESTION_LENGTH_LIMIT: int = Field(env="LIMIT", default=500,
                                       description="A value indicating how many chars can be in a question")

class SQLGenerationConfig(BaseSettings):
    """Configuration class for summarization"""
    DEFAULT_SQL_LLM_MODEL_CODE: str = Field(env="DEFAULT_SQL_LLM_MODEL_CODE", default="M2")


class PactSettings(BaseSettings):
    PACT_BROKER_URL: AnyUrl = Field(default="http://localhost", env="PACT_BROKER_URL")
    PACT_BROKER_USERNAME: str = Field(default="pactbroker", env="PACT_BROKER_USERNAME")
    PACT_BROKER_PASSWORD: str = Field(default="pactbroker", env="PACT_BROKER_PASSWORD")
    PROVIDER_HOST: str = Field(default="localhost", env="PROVIDER_HOST")
    PROVIDER_PORT: int = Field(default=8001, env="PROVIDER_PORT")
    PUBLISH_VERSION: str = Field(default="5", env="PUBLISH_VERSION")
    PROVIDER_NAME: str = Field(default="ConversationService", env="PROVIDER_HOST")
    CONSUMER_NAME: str = Field(default="BFF", env="CONSUMER_NAME")
    BROKER_KEY: str = Field(default="cGFjdGJyb2tlcjpwYWN0YnJva2Vy", env="BROKER_KEY")

    @property
    def PROVIDER_URL(self) -> str:
        return f"https://{self.PROVIDER_HOST}:{self.PROVIDER_PORT}"


class MockServerConfig(BaseSettings):
    MOCK_SERVER_HOST: str = Field(default="127.0.0.1", env="MOCK_SERVER_HOST")
    MOCK_SERVER_PORT: int = Field(default=8881, env="MOCK_SERVER_PORT")

    @property
    def MOCKSERVER_URL(self) -> str:
        return f"http://{self.MOCK_SERVER_HOST}:{self.MOCK_SERVER_PORT}"


pact_config = PactSettings()
mock_server_data = MockServerConfig()

summarization_config = SummarizationConfig()
app_config = AppConfig()
db_config = DataBaseConfig()

question_config = QuestionConfig()
