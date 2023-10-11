from dependency_injector import containers, providers

from configuration.config import DataBaseConfig, AppConfig, SummarizationConfig, ModelsConfig, StreamingResponseConfig, \
    SQLGenerationConfig
from source.helpers.db_helpers import DBHelper
from source.helpers.streaming_helpers import LLMStreamer
from source.models.conversations_models import Answer, VersionedAnswer
from source.repositories.answer_repository import AnswerRepository
from source.repositories.chat_suggestions_repository import ChatSuggestionsRepository
from source.repositories.conversation_repository import ConversationRepository
from source.repositories.model_repository import ModelRepository
from source.repositories.sources_repository import SourceRepository
from source.repositories.sql_source_repository import SQLSourceRepository
from source.repositories.workspace_repository import WorkspaceRepository
from source.repositories.workspace_type_repository import WorkspaceTypeRepository
from source.services.chat_service import ChatService
from source.services.chat_suggestions_service import ChatSuggestionsService
from source.services.conversation_service import ConversationService
from source.services.llm_chains.sql_llm_chains import SQLQueryChain, FullSQLChain
from source.services.model_service import ModelService
from source.services.source_service import SourceService
from source.services.workspace_service import WorkspaceService


class DependencyContainer(containers.DeclarativeContainer):
    """Container class for dependency injection"""
    wiring_config = containers.WiringConfiguration(packages=["source"])

    app_config = providers.Singleton(AppConfig)

    streaming_response_config = providers.Singleton(StreamingResponseConfig)

    sql_generation_config = providers.Singleton(SQLGenerationConfig)

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

    sql_source_repository = providers.Factory(SQLSourceRepository, database_helper=db_helpers)

    models_config = providers.Singleton(ModelsConfig)

    model_service = providers.Factory(ModelService,
                                      model_repository=model_repository,
                                      models_config=models_config
                                      )

    conversation_repository = providers.Factory(ConversationRepository, database_helper=db_helpers)

    conversation_service = providers.Factory(ConversationService, conversation_repository=conversation_repository,
                                             model_discovery_service=model_service)
    streamer_handler = providers.Factory(LLMStreamer,
                                         streaming_config=streaming_response_config,
                                         conversation_service=conversation_service)

    summarization_config = providers.Singleton(SummarizationConfig)
    answer_service = providers.Factory(ChatService,
                                       conversation_service=conversation_service,
                                       answer_repository=answer_repository,
                                       model_discovery_service=model_service,
                                       summarization_config=summarization_config,
                                       streaming_handler=streamer_handler
                                       )
    workspace_repository = providers.Factory(WorkspaceRepository, database_helper=db_helpers)
    workspace_type_repository = providers.Factory(WorkspaceTypeRepository, database_helper=db_helpers)

    source_repository = providers.Factory(SourceRepository, database_helper=db_helpers)
    source_service = providers.Factory(SourceService,
                                       source_repository=source_repository,
                                       workspace_type_repository=workspace_type_repository,
                                       config=app_config)

    workspace_service = providers.Factory(WorkspaceService,
                                          workspace_repository=workspace_repository,
                                          workspace_type_repository=workspace_type_repository,
                                          source_service=source_service)
    chat_suggestion_repository = providers.Factory(ChatSuggestionsRepository,
                                                   database_helper=db_helpers)

    chat_suggestion_service = providers.Factory(ChatSuggestionsService,
                                                chat_suggestions_repository=chat_suggestion_repository)

    sql_llm_service = providers.Factory(SQLQueryChain, model_registry_service=model_service,
                                        conversation_repository=conversation_repository,
                                        sql_generation_config=sql_generation_config,
                                        sql_source_repository=sql_source_repository,
                                        source_service=source_service
                                        )

    full_sql_chain_service = providers.Factory(FullSQLChain,
                                               streamer_handler=streamer_handler,
                                               llm_sql_query_chain=sql_llm_service,
                                               conversation_service=conversation_service,
                                               model_discovery_service=model_service
                                               )
