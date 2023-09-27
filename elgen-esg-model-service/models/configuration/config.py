import logging

from pydantic import BaseSettings, Field, validator

logger = logging.getLogger(__name__)


class AppConfig(BaseSettings):
    APP_HOST = Field(env="APP_HOST", default="localhost")
    APP_PORT = Field(env="APP_PORT", default=8003)

    MODEL_NAME = Field(env='MODEL_NAME', default="tiiuae/falcon-7b-instruct")
    MODEL_DIRECTORY = Field(env='MODEL_DIRECTORY', default="models_checkpoints")
    PROJECT_NAME: str = Field(env="PROJECT_NAME", default="ELGEN Model Service")
    ROOT_PATH: str = Field(env="ROOT_PATH", default="")
    HUGGINGFACE_TOKEN = Field(env='HUGGINGFACE_TOKEN', default="hf_token")


class OfflineServiceConfig(BaseSettings):
    MAX_NEW_TOKENS = Field(env='MODEL_MAX_NEW_TOKENS', default=256)
    DEVICE_MAP = Field(env='MODEL_DEVICE_MAP', default='auto')
    MAX_PROMPT_TOKEN_LENGTH = Field(env="MAX_PROMPT_TOKEN_LENGTH", default=2048)
    EIGHT_BIT_LLM_QUANTIZATION: int = Field(env="EIGHT_BIT_LLM_QUANTIZATION", default=True)
    FOUR_BIT_LLM_QUANTIZATION: int = Field(env="FOUR_BIT_LLM_QUANTIZATION", default=False)
    REPETITION_PENALTY: float = Field(env="REPETITION_PENALTY", default=2.0)
    NO_REPEAT_NGRAM_SIZE: int = Field(env="NO_REPEAT_NGRAM_SIZE", default=3)
    @validator("MAX_PROMPT_TOKEN_LENGTH", always=True)
    @classmethod
    def validate_max_prompt_token_length(cls, value):
        if value > 2048:
            logger.warning("Cannot exceed a maximum tokenized prompt length of 2048."
                           "Setting MAX_PROMPT_TOKEN_LENGTH to 2048")
            return 2048
        return value


class BlobStorageConfiguration(BaseSettings):
    """
       Class for azure blob storage configurations
       This is the expected Blob Container structure:
       elgen/
       ├── models/
       ├── ... 
       """
    DOWNLOAD_FROM_BLOB_STORAGE: int = Field(
        env="DOWNLOAD_FROM_BLOB_STORAGE",
        default=False,
        description="Whether or not to use Azure Blob Storage for model acquisition. "
                    "If disabled, will default to downloading models from HuggingFace."
    )
    BLOB_STORAGE_CONNECTION_STRING: str = Field(env="BLOB_STORAGE_CONNECTION_STRING", default="dummy_connection_string")
    CONTAINER: str = Field(default="elgen", env="CONTAINER")
    BLOB_STORAGE_MODELS_DIRECTORY: str = Field(
        default="models",
        env="MODELS_DIRECTORY",
        description="Directory in the container where the models are expected to be saved."
    )


app_config = AppConfig()
offline_service_config = OfflineServiceConfig()
blob_storage_configuration = BlobStorageConfiguration()
