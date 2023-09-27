import logging

from fastapi import FastAPI
from uvicorn import Server, Config

from configuration.injection_container import DependencyContainer
from configuration.logging_conf import logging_config
from configuration.logging_middleware import RouterLoggingMiddleware
from source.apis.prediction_api import router
from source.middlewares.app_middlewares import middlewares

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def get_application() -> FastAPI:
    application = FastAPI(
        description="Swagger for ELGEN Online Model Service API",
        middleware=middlewares,
    )
    application.add_middleware(RouterLoggingMiddleware, logger=logger)
    return application


app = get_application()

app.injection_container = DependencyContainer()

app.include_router(router)

if __name__ == "__main__":
    server = Server(
        Config(
            app=app,
            host=app.injection_container.app_config.APP_HOST(),
            port=app.injection_container.app_config.APP_PORT(),
            log_config=logging_config,
        )
    )
    server.run()
