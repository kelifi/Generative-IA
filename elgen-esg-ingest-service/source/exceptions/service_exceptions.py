class ServiceException(Exception):
    def __init__(self, detail="A service exception occurred"):
        self.detail = detail
        super().__init__(self.detail)

    def __str__(self):
        return self.detail


class ModelNotLoaded(ServiceException):
    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class ModelNotSupported(ServiceException):
    def __init__(self, detail="This model is not currently supported!"):
        super().__init__(detail)


class DataLayerError(ServiceException):
    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class SourceDirectoryNotFound(ServiceException):
    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class ElasticSearchError(ServiceException):
    def __init__(self, detail="Error with Elasticsearch!"):
        super().__init__(detail)


class VectorApiError(ServiceException):
    def __init__(self, detail="Error with Vector Store Api!"):
        super().__init__(detail)
