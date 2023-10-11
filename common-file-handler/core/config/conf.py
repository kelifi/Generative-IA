import os

from authorization.utils.api_key import get_user_folder
from core.providers.blobstorage.config import ConnectionString

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 65536))
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "AzureBlobStorageProvider")

key = get_user_folder()


class BlobStorage:
    settings = {"connectionString": ConnectionString,
                "dest": "c/",
                "container": "home"
                }

    credentials = {}


class FileStorage:
    settings = {
        "folder": "/files/",
                "dest": "fileC/"
                }
    credentials = {}


class MongoStorage:
    settings = {"folder": "/files/",
                "dest": "c/"
                }
    credentials = {}


file_storage = FileStorage
blob_storage = BlobStorage
