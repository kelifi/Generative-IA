import logging

from fastapi import FastAPI
from uvicorn import run

from configuration.config import AppConfig
from configuration.injection import DependencyContainer
from configuration.logging_conf import logging_config
from configuration.logging_middleware import RouterLoggingMiddleware
from source import middlewares
from source.api.ingest_api import ingest_router
from source.middlewares.app_middlewares import middlewares
from source.middlewares.interceptors import GenericExceptionInterceptor
from source.middlewares.observers import ProcessTimeMiddleware

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def get_application() -> FastAPI:
    application = FastAPI(
        title=AppConfig().PROJECT_NAME, openapi_url="/docs/swagger.json",
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

app.container = DependencyContainer()

add_middleware = app.add_middleware

for middleware in [ProcessTimeMiddleware, GenericExceptionInterceptor]:
    add_middleware(middleware)

app.include_router(ingest_router, tags=["ingest"])

if __name__ == '__main__':
    app.container.documents_ingestion_service().create_pipeline()
    app.container.documents_ingestion_service().create_ingest_index()
    run("main:app", host=app.container.app_settings().APP_HOST, port=app.container.app_settings().APP_PORT, log_config=logging_config,
        workers=app.container.app_settings().WORKERS_COUNT)
