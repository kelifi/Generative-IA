import logging

from fastapi import FastAPI
from uvicorn import Server, Config

from configuration.config import app_config
from configuration.injection_container import DependencyContainer
from configuration.logging_conf import logging_config
from configuration.logging_middleware import RouterLoggingMiddleware
from source.apis.health_check_api import health_check_router
from source.apis.model_inference_api import router
from source.helpers.blob_storage_helper import BlobStorageModelDownloader
from source.middlewares.app_middlewares import middlewares
from huggingface_hub import login as hf_login

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def get_application() -> FastAPI:
    application = FastAPI(
        root_path=app_config.ROOT_PATH,
        title=app_config.PROJECT_NAME,
        description="Swagger for ELGEN Model Service API",
        middleware=middlewares,
    )
    application.add_middleware(RouterLoggingMiddleware, logger=logger)
    return application


app = get_application()

app.injection_container = DependencyContainer()

app.include_router(router)
app.include_router(health_check_router)

if __name__ == "__main__":
    hf_login(app.injection_container.app_config()["HUGGINGFACE_TOKEN"])

    if app.injection_container.blob_storage_configuration()["DOWNLOAD_FROM_BLOB_STORAGE"]:
        downloader = BlobStorageModelDownloader()
        downloader.download_model()
    model = app.injection_container.model()
    model.model = model.load()
    model.inference_pipeline = model.create_pipeline()

    server = Server(
        Config(
            app=app,
            host=app.injection_container.app_config.APP_HOST(),
            port=app.injection_container.app_config.APP_PORT(),
            log_config=logging_config,
        )
    )
    server.run()
