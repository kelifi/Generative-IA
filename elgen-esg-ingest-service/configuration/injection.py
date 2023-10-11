from dependency_injector import containers, providers

import source
from configuration.config import AppConfig, DocumentsConfig, TextProcessingConfig, ElasticSearchConfig, \
    VectorStoreApiConfig
from source.enums.extraction_methods import ExtractionMethods
from source.services.document_ingestion_service import DocumentsIngestionService
from source.services.pdf_extractor.pdf_extractor import PDFExtractor


class DependencyContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[source])

    app_settings = providers.Singleton(AppConfig)
    doc_config = providers.Singleton(DocumentsConfig)
    text_proc_config = providers.Singleton(TextProcessingConfig)
    es_config = providers.Singleton(ElasticSearchConfig)
    vec_api_config = providers.Singleton(VectorStoreApiConfig)
    pdf_extraction = providers.Factory(PDFExtractor)
    file_to_text_methods = providers.Dict(
        {ExtractionMethods.PDF: pdf_extraction})
    documents_ingestion_service = providers.Factory(DocumentsIngestionService, elastic_search_config=es_config,
                                                    doc_config=doc_config,
                                                    text_proc_config=text_proc_config, vec_api_config=vec_api_config,
                                                    app_config=app_settings,
                                                    file_to_text_methods=file_to_text_methods)
