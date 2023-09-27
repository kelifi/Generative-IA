class UnknownModelType(Exception):
    def __init__(self, detail="Unknown Model Type!"):
        self.detail = detail
        super().__init__(detail)


class OopsNoDBError(Exception):
    """Raised when DB is not running"""

    def __init__(self, message="No DB is found"):
        self.message = message
        super().__init__(self.message)


class CreateAllTablesError(Exception):
    """Raised when creating all the tables of the DB is not done correctly"""

    def __init__(self, message="Error while creating all the tables of the DB"):
        self.message = message
        super().__init__(self.message)


class UnvalidQueryError(Exception):

    def __init__(self, message: str = "An error occurred due to invalidity of the query "):
        self.message = message
        super().__init__(self.message)


class InternalDataBaseError(Exception):

    def __init__(self, message: str = "An error occurred while committing the transaction"):
        self.message = message
        super().__init__(self.message)


class PostgresRetrievalError(Exception):

    def __init__(self, message: str = "Unable to retrieve information from postgres"):
        self.message = message
        super().__init__(self.message)


class NoDataFound(Exception):
    def __init__(self, message: str = "Data not found in internal systems"):
        self.message = message
        super().__init__(self.message)


class FileNotFoundInDirectory(Exception):
    def __init__(self, message: str = "Current file not found"):
        self.message = message
        super().__init__(self.message)