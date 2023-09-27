from dependency_injector import containers, providers

from configuration.config import DataBaseConfig, AppConfig
from source.helpers.db_helpers import DBHelper
from source.models.conversations_models import Answer, VersionedAnswer
from source.repositories.answer_repository import AnswerRepository
from source.repositories.conversation_repository import ConversationRepository
from source.services.chat_service import ChatService
from source.services.conversation_service import ConversationService


class PactDependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    app_config = providers.Singleton(AppConfig)

    database_config = providers.Singleton(DataBaseConfig)
    db_helpers = providers.Singleton(DBHelper, db_url="sqlite://")

    answer_repository = providers.Factory(AnswerRepository,
                                          database_helper=db_helpers,
                                          data_model=Answer,
                                          versioning_data_model=VersionedAnswer
                                          )

    conversation_repository = providers.Factory(ConversationRepository, database_helper=db_helpers)

    conversation_service = providers.Factory(ConversationService, conversation_repository=conversation_repository)
    answer_service = providers.Factory(ChatService,
                                       conversation_service=conversation_service,
                                       answer_repository=answer_repository,
                                       online_default_model=app_config.provided.ONLINE_DEFAULT_MODEL
                                       )
