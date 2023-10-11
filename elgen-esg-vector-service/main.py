import logging

from fastapi import FastAPI
from uvicorn import run

from configuration.config import app_config
from configuration.injection import DependencyContainer
from configuration.logging_middleware import RouterLoggingMiddleware
from source.api.elasticsearch_store_api import es_store_router
from source.middlewares.app_middlewares import middlewares
from source.middlewares.interceptors import GenericExceptionInterceptor
from source.middlewares.observers import ProcessTimeMiddleware

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def get_application() -> FastAPI:
    application = FastAPI(
        title=app_config.PROJECT_NAME, openapi_url="/docs/swagger.json",
        description="ELGEN Vector Service Swagger API Playground",
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

app.include_router(es_store_router, tags=["es"])

if __name__ == '__main__':
    # Connect to the running milvus instance at the start of the application
    run("main:app", host=app.container.app_settings().APP_HOST, port=app.container.app_settings().APP_PORT,
        workers=app.container.app_settings().WORKERS_COUNT)
