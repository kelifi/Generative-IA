import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    HOST = os.environ.get('MONGO_HOST', 'localhost')
    DB = os.environ.get('MONGO_DB_NAME', 'ALDOC')
    MONGO_PORT = os.environ.get('MONGO_DB_PORT', 27017)
    ID_COLLECTION = os.environ.get('MONGO_COLLECTION', 'Id')

    USER = os.environ.get('MONGO_USER', 'haythem')
    PASSWORD = os.environ.get('MONGO_PASSWORD', 'root')
    URI = f'mongodb://{USER}:{PASSWORD}@{HOST}:{MONGO_PORT}/?authSource={DB}'
    print(URI)

settings = Settings()