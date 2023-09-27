from fastapi import HTTPException


class ElgenAPIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return (
            f"<Exception occurred with status_code={self.status_code} - message={self.detail}>"
        )
