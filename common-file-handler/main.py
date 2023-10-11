import os
import uvicorn
from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every

from authorization.config.conf import FileHandlerUserConfig
from authorization.db.crud import delete_all_streaming_temp_files
from authorization.db.postgres import Database
from authorization.init_db.create_table import create_table
from authorization.routes.user_routes import router as file_user_router
from authorization.utils.api_key import get_api_key
from core.exeptions_handler import add_unicorn_exception_handler
from core.streams.media_streaming import streaming_media_object
from routes.file_storage_route import router as file_storage_router
from routes.headers_middleware import HeadersMiddleware
from loguru import logger

app = FastAPI()

""" Routes for file handler services """

app.include_router(file_user_router, tags=["file handler user"])
app.include_router(file_storage_router, tags=["file storage"], dependencies=[Depends(get_api_key)])
add_unicorn_exception_handler(app)

""" Middlewares for file handler services """

app.add_middleware(HeadersMiddleware)


@app.on_event("startup")
@repeat_every(seconds=6 * 60 * 60)  # 6 hours
async def clean_files():
    """
    remove streaming temp file after some time
    """
    try:
        if streaming_media_object.audio_file_path:
            logger.info("Cron Job: Deleting all streaming temp files")
            os.system(f"rm -rf /tmp/tmp*")
            delete_all_streaming_temp_files()
    except FileNotFoundError:
        logger.warning("Error in deleting streaming temp files")


@app.on_event("startup")
async def startup():
    # Initialize database
    Database.initialise(database=FileHandlerUserConfig.DB_NAME, user=FileHandlerUserConfig.DB_USER,
                        password=FileHandlerUserConfig.DB_PASSWORD, host=FileHandlerUserConfig.DB_HOST,
                        port=FileHandlerUserConfig.DB_PORT, sslmode=FileHandlerUserConfig.SSL_MODE)
    create_table()
    delete_all_streaming_temp_files()

if __name__ == '__main__':
    uvicorn.run(app, host=FileHandlerUserConfig.host, port=FileHandlerUserConfig.port)

