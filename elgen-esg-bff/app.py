import logging

from fastapi import FastAPI
from uvicorn import Config, Server

from configuration.config import app_config
from configuration.injection import InjectionContainer
from configuration.logging_conf import logging_config
from configuration.logging_middleware import RouterLoggingMiddleware
from source import middlewares
from source.apis.chat_suggestions_api import chat_suggestion_router
from source.apis.chats_router import chats_router
from source.apis.conversation_router import conversations_router
from source.apis.ingestion_router import ingest_router
from source.apis.keycloak_router import keycloak_router
from source.apis.sources_router import sources_router
from source.apis.workspace_router import workspace_router
from source.middlewares.app_middlewares import middlewares

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def get_application() -> FastAPI:
    application = FastAPI(
        title=app_config.PROJECT_NAME, openapi_url="/docs/swagger.json",
        description="ELGEN ingest Service Swagger API Playground",
        docs_url="/docs",
        redoc_url="/redocs",
        middleware=middlewares,
    )
    application.add_middleware(
        RouterLoggingMiddleware,
        logger=logger
    )
    return application


app = get_application()

app.injection_container = InjectionContainer()
app.include_router(chat_suggestion_router, tags=["Chat Suggestions API"])
app.include_router(workspace_router, tags=["Workspaces"])
app.include_router(chats_router, tags=["Chats"])
app.include_router(sources_router, tags=["Sources"])
app.include_router(conversations_router, tags=["Conversations"])
app.include_router(keycloak_router, tags=["Users"])
app.include_router(ingest_router, tags=['Ingestion'])

if __name__ == '__main__':
    server = Server(
        Config(app=app, host=app.injection_container.bff_configuration.HOST(),
               port=app.injection_container.bff_configuration.PORT(), log_config=logging_config,
               workers=app.injection_container.bff_configuration.NB_OF_WORKERS()))
    server.run()
