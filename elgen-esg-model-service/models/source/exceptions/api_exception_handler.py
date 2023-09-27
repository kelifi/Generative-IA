from fastapi import HTTPException, status


class ElgenAPIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return (
            f"<Exception occurred with status_code={self.status_code} - message={self.detail}>"
        )


class ModelLoadAPIException(ElgenAPIException):
    """
    Exception raised when model loading fails.
    """

    def __init__(self,
                 status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
                 detail: str = "Failed to load model."):
        super().__init__(status_code, detail)

    def __str__(self):
        return (
            f"<ModelLoadAPIException occurred for model"
            f"with status_code={self.status_code} - message={self.detail}>"
        )
