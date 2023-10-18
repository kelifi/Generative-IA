from dependency_injector import containers, providers

import source
from configuration.config import AppConfig, MilvusDatabaseConfig, MilvusCollectionConfig, ElasticSearchConfig
from source.helpers.elasticsearch_helper import EmbeddingIndexerHelper
from source.helpers.milvus_helpers import MilvusHelper
from source.services.elasticsearch_service import EmbeddingIndexerService
from source.services.milvus_service import MilvusService


class DependencyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[source])

    app_settings = providers.Singleton(AppConfig)


    milvus_db_settings = providers.Singleton(MilvusDatabaseConfig)
    milvus_collection_settings = providers.Singleton(MilvusCollectionConfig)
    es_config = providers.Singleton(ElasticSearchConfig)
    milvus_helper = providers.Singleton(MilvusHelper, milvus_database_configuration=milvus_db_settings,
                                        milvus_collection_config=milvus_collection_settings)
    milvus_service = providers.Factory(MilvusService, milvus_collection_config=milvus_collection_settings,
                                       milvus_helper=milvus_helper)
    es_helper = providers.Singleton(EmbeddingIndexerHelper, elasticsearch_config =es_config)
    es_service = providers.Factory(EmbeddingIndexerService, helper=es_helper)
