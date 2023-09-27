class PredictionError(Exception):
    """Base exception related to model predictions."""

    def __init__(self, detail: str) -> None:
        """
        Initializes PredictionError
        Args:
            detail: Message of the error
        """
        super().__init__(f"error : {detail}")


class OpenAIRequestError(PredictionError):
    """Exception raised when a model inference fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ModelCallPredictionError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)


class ResultParsingPredictionError(PredictionError):
    """Exception raised when model result parsing fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ResultParsingPredictionError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)


class ModelLoadError(PredictionError):
    """Exception raised when model loading fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ModelLoadError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)
