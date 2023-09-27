class ModelError(Exception):
    """Base exception related to model predictions."""

    def __init__(self, detail: str) -> None:
        """
        Initializes PredictionError
        Args:
            detail: Message of the error
        """
        self.detail = detail
        super().__init__(f"error : {detail}")


class ModelCallPredictionError(ModelError):
    """Exception raised when a model inference fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ModelCallPredictionError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)


class ResultParsingPredictionError(ModelError):
    """Exception raised when model result parsing fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ResultParsingPredictionError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)


class ModelLoadError(ModelError):
    """Exception raised when model loading fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes ModelLoadError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)


class PromptError(ModelError):
    """Exception raised when a prompt is not compatible with the model"""

    def __init__(self, detail: str = "Prompt is invalid!") -> None:
        """
        Initializes PromptError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)

class MetadataParsingError(ModelError):
    """Exception raised when model metadata parsing fails"""

    def __init__(self, detail: str) -> None:
        """
        Initializes MetadataParsingError
        Args:
            detail: Message of the error
        """
        super().__init__(detail)