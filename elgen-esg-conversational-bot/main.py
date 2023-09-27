from fastapi import FastAPI, Request
from loguru import logger
from starlette.responses import HTMLResponse
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from uvicorn import Server, Config

from configuration.config import app_config
from configuration.injection_container import DependencyContainer
from source.apis.chat_api import chat_router
from source.apis.conversation_api import conversation_router
from source.apis.inference_api import inference_router
from source.apis.reports_api import report_router
from source.apis.source_documents_router import source_document
from source.exceptions.api_exception_handler import ElgenAPIException
from source.helpers.websocket_helpers import connection_manager
from source.middlewares.commons import middlewares
from source.schemas.common_schema import AppEnv

app = FastAPI(title="ESG Conversational Bot - API",
              description="Swagger for ESG Conversational Bot API",
              version="0.0.0",
              docs_url="/docs",
              redoc_url="/redocs",
              openapi_url="/docs/swagger.json",
              root_path="/",
              middleware=middlewares,
              )

app.container = DependencyContainer()

app.container.db_helpers().init_database()

app.include_router(inference_router, tags=["inference_api"])
app.include_router(conversation_router, tags=["conversation_api"])
app.include_router(source_document, tags=["source_documents"])
app.include_router(chat_router, tags=["chat_api"])
app.include_router(report_router, tags=["reports"])


@app.exception_handler(ElgenAPIException)
async def text_extraction_exception_handler(request: Request, exc: ElgenAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(user_id: str, websocket: WebSocket):
    await connection_manager.connect(user_id=user_id, websocket=websocket)

    try:
        while True:
            data = await connection_manager.recv_text(websocket)
            await connection_manager.send_message(f"You wrote: {data}", user_id)

    except WebSocketDisconnect as error:
        await connection_manager.disconnect(user_id=user_id, websocket=websocket)
        logger.error(f"Disconnected because : {error}")


if app_config.APP_ENV == AppEnv.dev:
    @app.get("/")
    async def get():
        return HTMLResponse(open("static/live-decoding.html").read())

if __name__ == '__main__':
    Server(Config(app=app,
                  host=app.container.app_config.APP_HOST(),
                  port=app.container.app_config.APP_PORT(), workers=app.container.app_config.WORKERS_COUNT())).run()
