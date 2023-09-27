from fastapi import HTTPException


class AnswerGenerationApiError(HTTPException):
    """
    Raise at the api layer  when an unexpected error occurred during model prediction
    """
    def __init__(self, status_code: int, detail: str) -> None:
        """
        :param status_code:
        :param detail:
        """
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return (
            f"<Exception occurred with status_code={self.status_code} - message={self.detail}>"
        )
