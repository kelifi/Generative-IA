class HelperException(Exception):
    def __init__(self, detail="A helper exception occurred"):
        self.detail = detail
        super().__init__(self.detail)

    def __str__(self):
        return self.detail


class CountError(HelperException):
    """Exception raised when counting how many distinct files are stores in es fails"""
    def __init__(self, detail="Failed to validate the schema of output data"):
        super().__init__(detail)
