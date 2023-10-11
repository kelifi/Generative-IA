import gridfs
from pymongo import MongoClient

from core.providers.mongodb.config import settings


class MongoBaseSettings:
    client = MongoClient(settings.URI)
    print(settings.URI)
    db = client.get_database(settings.DB)
    documents_collection = db.get_collection(settings.ID_COLLECTION)
    file_collection = db.get_collection(settings.ID_COLLECTION)
    fs = gridfs.GridFS(db)


mongo_base_settings = MongoBaseSettings
