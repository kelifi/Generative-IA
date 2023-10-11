import logging

from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import Configuration, Factory

import source
from configuration.config import BFFSettings, KeyCloakHelperConfiguration, KeyCloakServiceConfiguration
from source.services.chat_suggestions_service import ChatSuggestionsService
from source.services.chats_service import ChatService
from source.services.conversation_service import ConversationService
from source.services.ingestion_services import IngestionService
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService
from source.services.workspace_service import WorkspaceService

logger = logging.getLogger()


class InjectionContainer(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=[source])

    bff_configuration = Configuration(pydantic_settings=[BFFSettings()])

    conversation_service = Factory(
        ConversationService,
        config=bff_configuration
    )

    sources_service = Factory(
        SourceService,
        config=bff_configuration
    )

    ingestion_service = Factory(IngestionService, config=bff_configuration)

    keycloak_helper_configuration = Configuration(pydantic_settings=[KeyCloakHelperConfiguration()])
    keycloak_service_configuration = Configuration(pydantic_settings=[KeyCloakServiceConfiguration()])
    keycloak_service = Factory(
        KeycloakService,
        keycloak_service_configuration=keycloak_service_configuration)

    chat_service = Factory(
        ChatService,
        config=bff_configuration,
        keycloak_service=keycloak_service
    )
    workspace_service = Factory(
        WorkspaceService,
        config=bff_configuration,
    )

    chat_suggestion_service = Factory(
        ChatSuggestionsService,
        config=bff_configuration)
