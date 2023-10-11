from core import exceptions
from core.config.conf import BlobStorage, FileStorage, MongoStorage
from core.providers.blobstorage.provider import AzureBlobStorageProvider
from core.providers.mongodb.provider import MongoDbProvider
from core.providers.filestorage.provider import FileStorageProvider

setting_dict = {
    "AzureBlobStorageProvider": BlobStorage,
    "FileStorageProvider": FileStorage,
    "MongoDbProvider": MongoStorage
}

credentials_dict = {}


def make_prov(default_provider):
    """

    :param default_provider: name of the provider
    :return: the provider relative to that name
    """


    try:
        provider = eval(default_provider)(setting_dict.get(default_provider).credentials,
                                          setting_dict.get(default_provider).settings)
        if not setting_dict.get(default_provider).settings:
            raise exceptions.UnhandledProviderError(
                'provider settings \'{0}\' are not defined'.format(default_provider),
                )

    except exceptions.ProviderNotFound:
        raise exceptions.ProviderNotFound('provider  \'{0}\' is not defined'.format(default_provider),
                                          )
    return provider


# def validate_connection_string():



