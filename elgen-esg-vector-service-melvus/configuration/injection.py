import chromadb
from chromadb.config import Settings
from dependency_injector import containers, providers

import source
from configuration.config import AppConfig, VectorDBConfig, MilvusDatabaseConfig, MilvusCollectionConfig
from source.helpers.milvus_helpers import MilvusHelper
from source.repositories.collections import VectorCollection
from source.services.chroma_db_services import ChromaDBVectorService
from source.services.milvus_service import MilvusService


class DependencyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[source])

    app_settings = providers.Singleton(AppConfig)

    vector_db_settings = providers.Singleton(VectorDBConfig)

    chroma_settings = providers.Singleton(Settings,
                                          chroma_db_impl="duckdb+parquet",
                                          persist_directory=vector_db_settings.provided.PERSIST_DIRECTORY,
                                          anonymized_telemetry=False
                                          )
    chroma_client = providers.Singleton(chromadb.Client, settings=chroma_settings)

    vector_collection = providers.Singleton(VectorCollection, config=vector_db_settings,
                                            client=chroma_client,
                                            )

    vector_service = providers.Factory(ChromaDBVectorService, collection=vector_collection)

    milvus_db_settings = providers.Singleton(MilvusDatabaseConfig)
    milvus_collection_settings = providers.Singleton(MilvusCollectionConfig)
    milvus_helper = providers.Singleton(MilvusHelper, milvus_database_configuration=milvus_db_settings,
                                        milvus_collection_config=milvus_collection_settings)
    milvus_service = providers.Factory(MilvusService, milvus_collection_config=milvus_collection_settings,
                                       milvus_helper=milvus_helper)
