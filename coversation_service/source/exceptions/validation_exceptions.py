class QuestionLengthExceededError(Exception):
    def __init__(self, length: int):
        self.message = f"Question length exceeded the limit which is set to {length} chars"
        super().__init__(self.message)


class GenericValidationError(Exception):
    def __init__(self, model_name: str):
        self.message = f"An error occurred with {model_name} schema"
        super().__init__(self.message)
