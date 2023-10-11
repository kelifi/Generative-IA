class ServiceException(Exception):
    """A generic service exception"""

    def __init__(self, detail="A service exception occurred"):
        self.detail = detail
        super().__init__(self.detail)

    def __str__(self):
        return self.detail


class ModelNotLoaded(ServiceException):
    """Error raised when the model is not loaded"""

    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class ModelNotSupported(ServiceException):
    """Error raised when the model is not supported"""

    def __init__(self, detail="This model is not currently supported!"):
        super().__init__(detail)


class DataLayerError(ServiceException):
    """Error raised when the embedding model fails to load"""

    def __init__(self, detail="Unable to load embedding model!"):
        super().__init__(detail)


class VectorApiError(ServiceException):
    """Error raised when the vector service fails"""

    def __init__(self, detail="Error with Vector Store Api!"):
        super().__init__(detail)


class CheckError(ServiceException):
    """Error raised when checking the existence of a file in ES fails"""

    def __init__(self, detail="Error with Checking a file's existence in ES"):
        super().__init__(detail)


class FileAlreadyIngestedError(ServiceException):
    """Error raised when file is already ingested in ES"""

    def __init__(self, detail="Error with Checking a file's existence in ES"):
        super().__init__(detail)


class IngestPipelineCreationError(ServiceException):
    """Error raised when the creation of the ingestion pipeline fails"""

    def __init__(self, detail="Error with elastic search pipeline creation!"):
        super().__init__(detail)


class IngestIndexCreationError(ServiceException):
    """Error raised when the creation of the ingestion index creation fails"""

    def __init__(self, detail="Error with elastic search index creation!"):
        super().__init__(detail)


class IngestionDeletionError(ServiceException):
    """Error raised when the creation of the ingestion index fails"""

    def __init__(self, detail="Error in deletion of the index"):
        super().__init__(detail)


class ElasticIndexCheckError(ServiceException):
    """Error raised when the checking of the existence of the elastic search index fails"""

    def __init__(self, detail="The check for the ingestion index in elastic search has failed"):
        super().__init__(detail)


class FileIngestionError(ServiceException):
    """Error raised when the ingestion of a file in elastic search fails"""

    def __init__(self, detail="The file was not ingested"):
        super().__init__(detail)


class TextRetrievalError(ServiceException):
    """Error raised when the text retrival from elastic search fails"""

    def __init__(self, detail="The file was not ingested"):
        super().__init__(detail)


class SchemaValidationError(ServiceException):
    """Error raised when a schema error arises"""

    def __init__(self, detail="Schema was not validated correctly"):
        super().__init__(detail)


class SendDataToVectorError(ServiceException):
    """Error raised when sending data to the vector store fails"""

    def __init__(self, detail="An error arises when communicating with the vector service to send the data"):
        super().__init__(detail)


class PDFExtractionError(ServiceException):
    """Error raised when a pdf error arises from pdfminer"""

    def __init__(self, detail="An error arises when handling the provided file"):
        super().__init__(detail)
