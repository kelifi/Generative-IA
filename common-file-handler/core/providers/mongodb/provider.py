import mimetypes
import os
import tempfile
from typing import Tuple, Set, Union, List, Dict
from fastapi.responses import FileResponse
from starlette import status
from authorization.db.crud import save_file_per_id
from authorization.utils.api_key import get_user_folder
from core import provider, streams, exceptions

from core.exceptions import UploadFailedError
from core.path_url import WaterButlerPath
from core.providers.filestorage.metadata import FileSystemFileMetadata
from core.providers.mongodb.db import mongo_base_settings
from core.utils import data_helper


class MongoDbProvider(provider.BaseProvider):
    """
    class created to make our service support mongo db
    by refactoring the BaseProvider methods
    """

    def __init__(self, credentials, settings, **kwargs):
        super().__init__(credentials, settings)
        self.folder = self.settings['folder']
        self.folder = self.folder + get_user_folder()

    Name = "MongoDbProvider"

    async def delete(self, src_path: str, **kwargs) -> Set[str]:

        check_file = await self.list_files(src_path)
        if not check_file:
            raise FileNotFoundError(f' The system cannot find the  specified:{src_path}'
                                    )
        data, _type = await self.get_file_or_dir(src_path)
        for file in data:
            _id = file["_id"]
            mongo_base_settings.fs.delete(file["_id"])
        if _type == "file":
            return {"file deleted"}
        return {"directory deleted"}

    async def validate_path(self, path: str) -> WaterButlerPath:
        return WaterButlerPath(path, prepend=self.folder)

    async def upload(self, file, path: str, *args, **kwargs) -> Dict[str, str]:
        if not path.endswith('/'):
            path += '/'
        paths = await self.validate_path(path)
        file_path = os.path.join(paths.path, file.filename)
        print(file_path)
        test = await self.list_files(path + file.filename)
        if test:
            raise UploadFailedError('\'{}\' exists in folder \'{}\' !'.format(file.filename, paths.name,
                                                                              code=status.HTTP_302_FOUND
                                                                              )
                                    )
        mime_type = mimetypes.guess_type(file_path)[0]

        file_stream = streams.FileStreamReader(file.file)
        stream = await file_stream.read()
        mongo_base_settings.fs.put(stream, filename=file.filename,
                                   content_type=mime_type if mime_type else "No type",
                                   path=os.path.dirname(paths.full_path),
                                   user=get_user_folder()
                                   )
        metadata = await self.metadata(path)
        data = data_helper(metadata[0], path + file.filename, kwargs.get('additional_info'))
        file_id = save_file_per_id(data)
        return {"success": "\'{}\' was saved in folder \'{}\' !".format(file.filename, paths.name), "file id": file_id}

    def _metadata_file(self, resp) -> dict:
        return {
            'path': resp.path,
            'size': resp.length,
            'creation time': resp.uploadDate.strftime('%a, %d %b %Y %H:%M:%S %z'),
            'Content type': resp.contentType,
            'file name': resp.filename,
        }

    async def metadata(self, path: str, **kwargs) -> List[Union[FileSystemFileMetadata, str]]:
        response = await self.list_files(path, recursive=True)
        if not response:
            raise exceptions.MetadataError(
                'Could not retrieve  \'{0}\''.format(path),
                code=404,
            )
        return response

    async def download(self, path: str, **kwargs):
        if kwargs.get('file_id'):
            data = await self.get_file_by_id(kwargs.get('file_id'))
            return await self.download_file(data)

        data, _ = await self.get_file_or_dir(path)
        rep = await self.download_file(data)
        if rep:
            return rep
        raise exceptions.DownloadError(f'\'{path}\' was not found.',
                                       code=status.HTTP_404_NOT_FOUND,
                                       )

    async def download_file(self, data) -> FileResponse:
        """

        :param data: mongo db cursor used to fine the file
        :return: the file as FileResponse
        """
        for file in data:
            db_response = mongo_base_settings.fs.get(file["_id"])
            with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as file:
                file.write(db_response.read())
                media_type = self._metadata_file(db_response)['Content type']
                if media_type:
                    return FileResponse(file.name, media_type=media_type)

    async def list_files(self, path: str, **kwargs) -> List[Union[FileSystemFileMetadata, str]]:
        metadata = []
        if not path:
            data = mongo_base_settings.db.fs.files.find({"user": get_user_folder()})
        else:
            data, _ = await self.get_file_or_dir(path)
        for file in data:
            db_response = mongo_base_settings.fs.get(file["_id"])
            if kwargs.get('recursive'):
                metadata.append(FileSystemFileMetadata(self._metadata_file(db_response), self.folder))
            else:
                metadata.append(FileSystemFileMetadata(self._metadata_file(db_response), self.folder).name)
        return metadata

    async def get_file_or_dir(self, paths: str) -> Tuple[dict, str]:
        """

        :param paths: the path entered as string
        :return: files information and the path entre type (file or directory)
        """
        path = await self.validate_path(paths)
        path_basename = os.path.basename(path.full_path)
        _type = "file"
        if path.is_file:
            data: dict = mongo_base_settings.db.fs.files.find(
                {"filename": path_basename, "path": os.path.dirname(path.full_path)})
        else:
            full_path = path.full_path
            if not full_path.endswith('/'):
                full_path += '/'

            data = mongo_base_settings.db.fs.files.find({"path": os.path.dirname(full_path)})
            _type = "dir"
        return data, _type

    async def get_file_by_id(self, file_id: str):
        """

        :param file_id: the id of the file to get from the db
        :return: file information
        """
        data: dict = mongo_base_settings.db.fs.files.find(
            {"unique_filename": file_id})
        return data
