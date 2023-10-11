import os

from pydantic import BaseSettings


class SettingsBlobStorage(BaseSettings):
    ACCOUNT_NAME = os.environ.get('AccountName', 'devstoreaccount1')
    ACCOUNT_KEY = os.environ.get('AccountKey',
                                 'Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw" \ "==')
    DEFAULT_ENDPOINT_PROTOCOL = os.environ.get('DefaultEndpointsProtocol', 'http')
    DEV_STORAGE_PROXY = os.environ.get('DevelopmentStorageProxyUri', 'http://azurite')
    USE_DEV_STORAGE = os.environ.get('UseDevelopmentStorage', 'true')
    BLOB_ENDPOINT = os.environ.get('BlobEndpoint', 'http://127.0.0.1:10000/devstoreaccount1')


blob_storage_settings = SettingsBlobStorage()

ConnectionStringVars = "AccountName=" + blob_storage_settings.ACCOUNT_NAME + \
                       ";AccountKey=" + blob_storage_settings.ACCOUNT_KEY + \
                       ";DefaultEndpointsProtocol=" + blob_storage_settings.DEFAULT_ENDPOINT_PROTOCOL + \
                       ";UseDevelopmentStorage=" + blob_storage_settings.USE_DEV_STORAGE + \
                       ";DevelopmentStorageProxyUri=" + blob_storage_settings.DEV_STORAGE_PROXY + \
                       ";BlobEndpoint=" + blob_storage_settings.BLOB_ENDPOINT + ";"

ConnectionString = os.getenv('BS_CONNECTION_STRING', ConnectionStringVars)

