class EmbeddingError(Exception):
    def __init__(self, detail="An error occurred when generating the Embedding"):
        super().__init__(detail)


class EmbeddingCompatibilityError(Exception):
    def __init__(self, model_name: str, embedding_dimension: int):
        detail = f"the model {model_name} and {embedding_dimension} do not match!"
        super().__init__(detail)


class EmbeddingModelNotFoundError(Exception):
    def __init__(self, model_name: str):
        detail = f"the model {model_name} was not found in the HuggingFace repository!"
        super().__init__(detail)
