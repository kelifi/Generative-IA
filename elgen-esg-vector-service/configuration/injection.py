from dependency_injector import containers, providers

import source
from configuration.config import AppConfig, ElasticSearchConfig
from source.helpers.elasticsearch_helper import EmbeddingIndexerHelper
from source.services.elasticsearch_service import EmbeddingIndexerService


class DependencyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[source])

    app_settings = providers.Singleton(AppConfig)

    es_config = providers.Singleton(ElasticSearchConfig)
    es_helper = providers.Singleton(EmbeddingIndexerHelper, elasticsearch_config=es_config)
    es_service = providers.Factory(EmbeddingIndexerService, helper=es_helper)
