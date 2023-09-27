from dependency_injector import containers, providers

import source
from configuration.config import AppConfig, es_config, doc_config, text_proc_config, vec_api_config, app_config
from source.services.document_ingestion_service import DocumentsIngestionService


class DependencyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[source])

    app_settings = providers.Singleton(AppConfig)
    documents_ingetion_service = providers.Factory(DocumentsIngestionService, elastic_search_config=es_config, doc_config=doc_config,
                                         text_proc_config=text_proc_config, vec_api_config=vec_api_config,
                                         app_config=app_config)


