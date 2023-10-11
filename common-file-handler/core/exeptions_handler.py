from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from core import exceptions
from core.exceptions import UploadFailedError


def add_unicorn_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(exceptions.MetadataError)
    async def meta_exception_handler(request: Request, exc: exceptions.MetadataError, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=str(exc)
        )

    @app.exception_handler(exceptions.DownloadError)
    async def http_exception_handler(request: Request, exc: exceptions.MetadataError, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        return JSONResponse(
            status_code=404,
            content=str(exc),
        )

    @app.exception_handler(FileNotFoundError)
    async def http_exception_handler(request: Request, exc: FileNotFoundError, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        return JSONResponse(
            status_code=404,
            content=str(exc),
        )

    @app.exception_handler(UploadFailedError)
    async def http_exception_handler(request: Request, exc: UploadFailedError, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        return JSONResponse(
            status_code=status.HTTP_302_FOUND,
            content=str(exc),
        )

    @app.exception_handler(exceptions.ProviderNotFound)
    async def http_exception_handler(request: Request, exc: exceptions.ProviderNotFound, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        return JSONResponse(
            status_code=404,
            content=str(exc),
        )

    @app.exception_handler(Exception)
    async def http_exception_handler(request: Request, exc: Exception, **kwargs) -> JSONResponse:
        """
        Default exception handler.
        This returns a JSON format message.
        :param request:
        :param exc:
        :return:
        """
        print(exc.args)
        return JSONResponse(
            status_code=404,
            content=str(exc),
        )
