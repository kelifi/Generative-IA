from dependency_injector import containers, providers

from configuration.config import DataBaseConfig, AppConfig, SummarizationConfig, ModelsConfig, StreamingResponseConfig
from source.helpers.db_helpers import DBHelper
from source.models.conversations_models import Answer, VersionedAnswer
from source.repositories.answer_repository import AnswerRepository
from source.repositories.conversation_repository import ConversationRepository
from source.repositories.model_repository import ModelRepository
from source.repositories.workspace_repository import WorkspaceRepository
from source.services.chat_service import ChatService
from source.services.conversation_service import ConversationService
from source.services.model_service import ModelService
from source.services.workspace_service import WorkspaceService


class DependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    wiring_config = containers.WiringConfiguration(packages=["source"])

    app_config = providers.Singleton(AppConfig)

    streaming_response_config = providers.Singleton(StreamingResponseConfig)

    database_config = providers.Singleton(DataBaseConfig)
    db_helpers = providers.Singleton(DBHelper, db_url=database_config.provided.db_url)

    answer_repository = providers.Factory(AnswerRepository,
                                          database_helper=db_helpers,
                                          data_model=Answer,
                                          versioning_data_model=VersionedAnswer
                                          )
    model_repository = providers.Factory(ModelRepository,
                                         database_helper=db_helpers
                                         )

    models_config = providers.Singleton(ModelsConfig)

    model_service = providers.Factory(ModelService,
                                      model_repository=model_repository,
                                      models_config=models_config
                                      )

    conversation_repository = providers.Factory(ConversationRepository, database_helper=db_helpers)

    conversation_service = providers.Factory(ConversationService, conversation_repository=conversation_repository,
                                             model_discovery_service=model_service)
    summarization_config = providers.Singleton(SummarizationConfig)
    answer_service = providers.Factory(ChatService,
                                       conversation_service=conversation_service,
                                       answer_repository=answer_repository,
                                       model_discovery_service=model_service,
                                       summarization_config=summarization_config,
                                       streaming_response_config=streaming_response_config
                                       )
    workspace_repository = providers.Factory(WorkspaceRepository, database_helper=db_helpers)
    workspace_service = providers.Factory(WorkspaceService, workspace_repository=workspace_repository)
