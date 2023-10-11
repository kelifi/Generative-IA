import abc
from enum import Enum
import typing
from core import path_url, exceptions
from core import streams


class BaseProvider(metaclass=abc.ABCMeta):

    def __init__(self, 
                 credentials: dict,
                 settings: dict,
                 ) -> None:
        self.credentials = credentials
        self.settings = settings

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    def __eq__(self, other) -> typing.Union[bool, typing.Any]:
        try:
            return (
                    type(self) == type(other) and
                    self.credentials == other.credentials
            )
        except AttributeError:
            return False

    def serialized(self) -> dict:
        return {
            'name': self.name,
            'settings': self.settings,
            'credentials': self.credentials,
        }

    @abc.abstractmethod
    async def download(self, path: str, **kwargs) \
            -> streams:
        r"""Download a file from this provider.

        :param path: ( :class:`.WaterButlerPath` ) Path to the file to be downloaded
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: :class:`.ResponseStreamReader`
        :raises: :class:`.DownloadError`
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def upload(self, file, path: str, *args,
                     **kwargs):
        r"""Uploads the given stream to the provider.  Returns the metadata for the newly created
        file and a boolean indicating whether the file is completely new (``True``) or overwrote
        a previously-existing file (``False``)

        :param path: ( :class:`.WaterButlerPath` ) Where to upload the file to
        :param  file: ( :class:`.BaseStream` ) The content to be uploaded
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: (:class:`.BaseFileMetadata`, :class:`bool`)
        :raises: :class:`.uploadError`
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, src_path: str, **kwargs) -> None:
        r"""
        :param src_path: ( :class:`.WaterButlerPath` ) Path to be deleted
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: :class:`None`
        :raises: :class:`.DeleteError`
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def metadata(self, path: str, **kwargs) \
            :
        r"""Get metadata about the specified resource from this provider. Will be a :class:`list`
        if the resource is a directory otherwise an instance of
        :class:`.BaseFileMetadata`

        .. note::
            Mypy doesn't seem to do very well with functions that can return more than one type of
            thing. See: https://github.com/python/mypy/issues/1693

        :param path: ( :class:`.WaterButlerPath` ) The path to a file or folder
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: :class:`.BaseMetadata`
        :rtype: :class:`list` of :class:`.BaseMetadata`
        :raises: :class:`.MetadataError`
        """
        raise NotImplementedError

    async def exists(self, path: path_url.WaterButlerPath, **kwargs) \
            :
        """Check for existence of WaterButlerPath

        Attempt to retrieve provider metadata to determine existence of a WaterButlerPath.  If
        successful, will return the result of `self.metadata()` which may be `[]` for empty
        folders.

        :param  path: ( :class:`.WaterButlerPath` ) path to check for
        :rtype: (`self.metadata()` or False)
        """
        try:
            return await self.metadata(path, **kwargs)
        except exceptions.NotFoundError:
            return False
        except exceptions.MetadataError as e:
            if e.code != 404:
                raise
        return False

    @abc.abstractmethod
    async def list_files(self, path: str, **kwargs):
        """List all files in directory

        :param path: directory path to check for
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: (`List` or None)
        :return: list of files in that path
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def download_zip_files(self, files_path_list: typing.List[str], **kwargs):
        """download all files as a zip file

        :param files_path_list: file paths to check for
        :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
        :rtype: (`StreamingResponse` or None)
        :return: zip file that contains all the files
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def delete_multiple_files(self, files_id_list: dict) -> list:
        """
        delete multiple files
        :param files_id_list : a dict in this format {'files_list': List of files id you want to delete}
        :rtype: (List)
        :return: id List of deleted files

        """
        raise NotImplementedError


class Providers(Enum):
    blob_storage = "AzureBlobStorageProvider"
    mongodb = "MongoDbProvider"
    file_storage = "FileStorageProvider"
