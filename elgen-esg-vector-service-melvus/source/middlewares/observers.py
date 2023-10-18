import time

from fastapi import Request, FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """
    Observability utility to know execution time of each request handling
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request at {request.url.path}")
        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time), ndigits=4)
        logger.debug(f"request {request.url.path} execution time {process_time}")
        response.headers["X-Process-Time"] = str(process_time)
        return response
