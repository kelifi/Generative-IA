class BlobStorageError(Exception):
    """
    Generic Azure Blob Storage error class.
    """

    def __init__(self, message: str = "Blob storage error."):
        self.message = message
        super().__init__(self.message)


class BlobStorageRetrievalError(BlobStorageError):
    """
    Error raised when a blob cannot be downloaded.
    """

    def __init__(self, message: str = "Unable to retrieve blob from Blob Storage."):
        self.message = message
        super().__init__(self.message)
