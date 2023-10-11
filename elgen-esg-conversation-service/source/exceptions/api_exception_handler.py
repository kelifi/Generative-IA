from fastapi import HTTPException
from fastapi.responses import JSONResponse


class ElgenAPIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class NotOkServiceResponse(JSONResponse):
    pass
