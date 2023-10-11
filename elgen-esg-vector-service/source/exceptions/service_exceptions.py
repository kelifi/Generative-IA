class InternalError(Exception):
    def __init__(self, detail="A service exception occurred"):
        self.detail = detail
        super().__init__(self.detail)

    def __str__(self):
        return self.detail


class ModelNotLoaded(InternalError):
    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class ModelNotSupported(InternalError):
    def __init__(self, detail="This model is not currently supported!"):
        super().__init__(detail)


class DataLayerError(InternalError):
    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class ServiceException(Exception):
    def __init__(self, detail="A service exception occurred"):
        self.detail = detail
        super().__init__(self.detail)

    def __str__(self):
        return self.detail


class MaxResultValueException(ServiceException):
    def __init__(self, detail="bad value for n_results!"):
        super().__init__(detail)


class DBRuntimeError(DataLayerError):
    def __init__(self, detail="Unexpected error while running a query!"):
        super().__init__(detail)


class EmptyMilvusCollection(ServiceException):
    def __init__(self, detail="No records in Milvus collection!"):
        super().__init__(detail)


class MilvusNotFoundError(ServiceException):
    def __init__(self, detail="resource was not found!"):
        super().__init__(detail)


class ExistenceCheckError(ServiceException):
    """Exception raised when an existence check fails"""

    def __init__(self, expression: str, milvus_error: str):
        detail = f'the following expression {expression}, could not be executed, the following is the error! {milvus_error}'
        super().__init__(detail)


class DataAlreadyInMilvusError(ServiceException):
    """Exception raised when the data exists in milvus"""

    def __init__(self, detail="The data you are trying to save is already in Milvus"):
        super().__init__(detail)


class ElasticsearchStoreDataError(ServiceException):
    """Exception if we fail to save data in elasticsearch"""

    def __init__(self, detail="Failed to store data into elasticsearch"):
        super().__init__(detail)


class ElasticsearchFetchDataError(ServiceException):
    """Exception if we fail to fetch data from elasticsearch"""

    def __init__(self, detail="Failed to store data into elasticsearch"):
        super().__init__(detail)


class ServiceOutputValidationError(ServiceException):
    """Exception raised when the data doesn't fit in the expected schemas"""

    def __init__(self, detail="Failed to validate the schema of output data"):
        super().__init__(detail)


class ElasticSearchCountError(ServiceException):
    """Exception raised when an error arises during the count"""

    def __init__(self, detail="an error occurred during the count of the files in elastic search"):
        super().__init__(detail)
