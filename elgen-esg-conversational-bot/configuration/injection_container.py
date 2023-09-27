from dependency_injector import containers, providers

from configuration.config import AppConfig, DataBaseConfig, ReportGenerationConfig, \
    MongoBaseConfig, ElasticSearchConfig
from source.helpers.db_helpers import DBHelper
from source.helpers.report_crud import MongoDatabaseCrud, MongoConnectionProvider
from source.helpers.source_document_router_helper import DocumentHighlightHelper
from source.repositories.answer_repository import AnswerRepository
from source.repositories.conversation_repository import ConversationRepository
from source.repositories.question_repository import QuestionRepository
from source.services.chat_service import ChatService
from source.services.conversation_service import ConversationService
from source.services.documents_highlighting_service import DocumentHighlightService
from source.services.reports_service import ReportService


class DependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    wiring_config = containers.WiringConfiguration(packages=["source"])

    app_config = providers.Configuration(pydantic_settings=[AppConfig()])
    database_config = providers.Singleton(DataBaseConfig)
    elasticsearch_config = providers.Singleton(ElasticSearchConfig)
    report_generation_config = providers.Singleton(ReportGenerationConfig)
    mongo_db_config = providers.Singleton(MongoBaseConfig)

    db_helpers = providers.Singleton(DBHelper, db_url=database_config.provided.db_url)

    mongo_connection_provider = providers.Singleton(MongoConnectionProvider, mongo_config=mongo_db_config)
    mongo_db_crud = providers.Factory(MongoDatabaseCrud, mongo_connection_provider=mongo_connection_provider)
    report_service = providers.Factory(ReportService, db_crud=mongo_db_crud)

    conversation_repository = providers.Factory(ConversationRepository, database_helper=db_helpers)
    conversation_service = providers.Factory(ConversationService, conversation_repository=conversation_repository)

    documents_highlight_helper = providers.Factory(DocumentHighlightHelper,
                                                   session_factory=db_helpers.provided.session)
    documents_highlight_service = providers.Factory(
        DocumentHighlightService,
        db_helper=documents_highlight_helper
    )

    question_repository = providers.Factory(QuestionRepository, database_helper=db_helpers)
    answer_repository = providers.Factory(AnswerRepository, database_helper=db_helpers)
    chat_service = providers.Factory(ChatService, question_repository=question_repository,
                                     answer_repository=answer_repository)
