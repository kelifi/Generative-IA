class DataLayerException(Exception):
    """Exception raised in the crud level when there are database related error
    like integrity, data, database, Connection etc
        message -- explanation of the error
    """

    def __init__(self, detail: str = "Unable To Fetch Data"):
        self.detail = detail


class UserDataNotFoundException(Exception):
    """Exception raised in the crud level when User is not found
    """

    def __init__(self, detail: str = "User Not Found"):
        self.detail = detail
