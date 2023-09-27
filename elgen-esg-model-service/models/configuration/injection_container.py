from dependency_injector import containers, providers
from dependency_injector.providers import Configuration
from transformers import AutoModelForCausalLM, AutoTokenizer

from configuration.config import AppConfig, BlobStorageConfiguration, OfflineServiceConfig
from source.services.model_service import LLMFactoryHuggingFace


class DependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    wiring_config = containers.WiringConfiguration(packages=["source"])

    app_config = Configuration(pydantic_settings=[AppConfig()])

    model_config = providers.Singleton(OfflineServiceConfig)
    blob_storage_configuration = Configuration(pydantic_settings=[BlobStorageConfiguration()])

    model = providers.Singleton(LLMFactoryHuggingFace, model_name=app_config.MODEL_NAME, config=model_config,
                                model_directory=app_config.MODEL_DIRECTORY, model_class=AutoModelForCausalLM,
                                tokenizer_class=AutoTokenizer)
