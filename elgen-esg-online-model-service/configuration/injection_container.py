from dependency_injector import containers, providers
from dependency_injector.providers import Configuration

from configuration.config import AppConfig, OpenAIConfig
from source.services.model_service import OpenAIService


class DependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    wiring_config = containers.WiringConfiguration(packages=["source"])

    app_config = Configuration(pydantic_settings=[AppConfig()])

    open_ai_config = providers.Singleton(OpenAIConfig)

    open_ai_model = providers.Singleton(OpenAIService, config=open_ai_config)

