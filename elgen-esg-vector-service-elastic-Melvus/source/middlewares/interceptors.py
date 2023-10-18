from fastapi import Request, status, FastAPI
from fastapi.encoders import jsonable_encoder
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from source.exceptions.service_exceptions import ModelNotLoaded, DataLayerError, InternalError


class GenericExceptionInterceptor(BaseHTTPMiddleware):
    """
    Used to catch the following generic exceptions:
        exception ModelNotLoaded
            There is an issue when loading the embeding model
        exception DataLayerError, ServiceException
            Generally use these exceptions when there is a possibility of something breaking internally:
                like change in schema between db and code
    Generic exceptions are exceptions that are not specific to a certain logic or feature
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except (ModelNotLoaded, DataLayerError) as error:
            logger.error('Unable to perform the requested query!')
            logger.error(f'Error: {error.detail}', backtrace=True)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=jsonable_encoder({"detail": "Service Unavailable!"})
            )
        except InternalError as error:
            logger.error('Something went wrong!')
            logger.error(f'Error: {error.detail}', backtrace=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder({"detail": "Internal Error!"})
            )
