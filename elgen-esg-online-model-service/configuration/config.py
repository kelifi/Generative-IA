from pydantic import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    APP_HOST = Field(env="APP_HOST", default="localhost")
    APP_PORT = Field(env="APP_PORT", default=8033)
    APP_ENV = Field(env="APP_ENV", default="prod")


class OpenAIConfig(BaseSettings):
    MODEL_NAME = Field(env='OPENAI_MODEL_NAME', default="gpt-3.5-turbo")
    API_KEY = Field(env="OPENAI_API_KEY", default="")
    API_URL = Field(env='OPEN_AI_API_URL', default="https://api.openai.com/v1/chat/completions")
