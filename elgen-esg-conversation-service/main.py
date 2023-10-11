from fastapi import FastAPI
from fastapi import Request, status
from fastapi.responses import JSONResponse
from uvicorn import Server, Config

from configuration.config import app_config
from configuration.injection_container import DependencyContainer
from configuration.logging_conf import logging_config
from configuration.logging_middleware import RouterLoggingMiddleware
from configuration.logging_setup import logger
from source.apis.chat_api import chat_router
from source.apis.chat_suggestions_api import chat_suggestion_router
from source.apis.conversation_api import conversation_router
from source.apis.health_check_api import health_check_router
from source.apis.model_api import model_router
from source.apis.source_api import sources_router
from source.apis.workspace_api import workspace_router
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.validation_exceptions import QuestionLengthExceededError
from source.middlewares.app_middlewares import middlewares
from source.schemas.common import AppEnv


def get_application() -> FastAPI:
    application = FastAPI(
        title=app_config.PROJECT_NAME, openapi_url="/docs/swagger.json",
        description="Swagger for ELGEN conversation Service API",
        docs_url="/docs",
        redoc_url="/redocs",
        middleware=middlewares
    )

    if app_config.APP_ENV in [AppEnv.DEV, AppEnv.TEST]:
        return application

    application.add_middleware(
        RouterLoggingMiddleware,
        logger=logger
    )

    return application


app = get_application()

app.container = DependencyContainer()

app.include_router(conversation_router, tags=["conversation_api"])
app.include_router(chat_router, tags=["question_answer_api"])
app.include_router(model_router, tags=["model_api"])
app.include_router(chat_suggestion_router, tags=["Chat Suggestions API"])
app.include_router(workspace_router, tags=["Workspaces API"])
app.include_router(sources_router, tags=["Sources Api"])
app.include_router(health_check_router, tags=["healthz_api"])


@app.exception_handler(ElgenAPIException)
async def text_extraction_exception_handler(request: Request, exc: ElgenAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(QuestionLengthExceededError)
async def question_limit_exceeded_error(request: Request, exception: QuestionLengthExceededError):
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"detail": exception.message}
    )


if __name__ == '__main__':
    Server(Config(app=app,
                  host=app_config.APP_HOST,
                  port=app_config.APP_PORT, log_config=logging_config,
                  workers=app_config.NB_OF_WORKERS
                  )).run()
