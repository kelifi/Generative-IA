import datetime
import logging
import mimetypes
import os
from io import BytesIO
from os import listdir
from os.path import isfile, join
import shutil
import tempfile
from typing import List, Union, Set, Optional, Any, Dict
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import HTTPException
from psycopg2._psycopg import IntegrityError
from starlette import status
from starlette.responses import Response, StreamingResponse

from authorization.db.crud import save_file_per_id, get_file_per_path, delete_file_per_id, get_file_per_id
from authorization.utils.api_key import get_user_folder
from core import provider, exceptions
from core.config.conf import CHUNK_SIZE
from core.exceptions import InvalidPathError
from core.path_url import WaterButlerPath
from core.streams.file import FileStreamReader
from core.providers.filestorage.metadata import FileSystemFileMetadata
from core.utils import data_helper, append_id


class FileStorageProvider(provider.BaseProvider):
    """
    class created to make our service support file system storage
    by refactoring the BaseProvider methods
    """

    def __init__(self, credentials, settings, **kwargs):
        super().__init__(credentials, settings, **kwargs)
        self.folder = self.settings['folder']
        self.folder = self.folder + get_user_folder()
        os.makedirs(self.folder, exist_ok=True)

    name = 'filesystem'
    logging.info(name)

    async def validate_path(self, path, **kwargs):
        return WaterButlerPath(path, prepend=self.folder)

    async def download(self, path: str,
                       **kwargs) -> Response:

        path = await self.validate_path(path)
        if not os.path.exists(path.full_path):
            raise exceptions.DownloadError(f' {path} was not found.',
                                           code=status.HTTP_404_NOT_FOUND,
                                           )
        user_id = kwargs.get('user_id')
        if user_id != path.folder_name:
            raise exceptions.DownloadError(f'\'{user_id}\' user is not an allowed user.',
                                           code=status.HTTP_403_FORBIDDEN,
                                           )
        file_pointer = open(path.full_path, 'rb')

        data = await FileStreamReader(file_pointer).read()
        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as file:
            file.write(data)
        media_type = self._metadata_file(path)['Content type']
        file_pointer.close()
        logging.warning(media_type)
        return Response(data, media_type=media_type)

    async def delete(self, src_path: str, **kwargs) -> Set[str]:
        try:
            path = await self.validate_path(src_path, prepend=self.folder)
        except InvalidPathError:
            raise InvalidPathError(f' The system cannot find the file specified')

        if path.is_file:
            try:
                os.remove(path.full_path)
            except FileNotFoundError:
                raise FileNotFoundError(f'The system cannot find the file specified:{path}'
                                        )
            return {"file deleted"}
        try:
            shutil.rmtree(path.full_path)
        except FileNotFoundError:
            raise FileNotFoundError(f'The system cannot find the file specified:{src_path}')
        if path.is_root:
            os.makedirs(self.folder, exist_ok=True)
        return {"directory deleted"}

    async def upload(self, source, paths, *args, **kwargs) -> dict:

        overwrite = kwargs.get('overwrite')
        if not paths:  ### to ckeck
            paths = '/'
        paths = self.change_id_to_path(paths)
        path_name = await self.validate_path(paths, prepend=self.folder)
        file_path = os.path.join(paths, source.filename)

        created = await self.exists(file_path)
        if created and not overwrite:
            file_path = os.path.join(paths, append_id(source.filename))

        path = await self.validate_path(file_path, prepend=self.folder)
        os.makedirs(os.path.split(path.full_path)[0], exist_ok=True)
        if created and overwrite:
            path = await self.validate_path(file_path, prepend=self.folder)
            file_id = get_file_per_path(path.full_path)
            await self.delete(file_path)
            delete_file_per_id(file_id.get('file_id'))
        with open(path.full_path, 'wb') as file_pointer:
            chunk = await source.read(CHUNK_SIZE)
            while chunk:
                file_pointer.write(chunk)
                chunk = await source.read(CHUNK_SIZE)
        file_id_in_db = ""
        try:
            metadata = await self.metadata(file_path)
            data = data_helper(metadata[0], source.filename, kwargs.get('additional_info'))
            try:
                file_id_in_db = save_file_per_id(data)
            except Exception as exception:
                logging.exception(exception)
                logging.exception("file metadata was not saved in file handler")
        except Exception as exception:
            logging.exception(str(exception))

        return {"success": "\'{}\' was saved!".format(path.name),
                "file_id": file_id_in_db,
                "user_id": path_name.name}

    @staticmethod
    def _metadata_file(path, file_name='', **kwargs) -> dict:
        full_path = path.full_path if file_name == '' else os.path.join(path.full_path, file_name)
        modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(full_path)).replace(tzinfo=datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z'),
        mime_type = mimetypes.guess_type(full_path)[0]
        original_file_name = kwargs.get('original_file_name')
        return {
            'path': full_path,
            'size': os.path.getsize(full_path),
            'modified': modified,
            'creation time': modified,
            'Content type': mime_type if mime_type else "No type",
            'file name': os.path.basename(full_path),
            'original_file_name': original_file_name
        }

    async def metadata(self, paths: str, **kwargs) -> List[Union[FileSystemFileMetadata, str]]:
        if not paths:
            paths = '/'
        path = await self.validate_path(paths, prepend=self.folder)
        if path.is_dir:
            if not os.path.exists(path.full_path) or not os.path.isdir(path.full_path):
                raise exceptions.MetadataError(
                    'Could not retrieve folder \'{0}\''.format(path),
                    code=404,
                )
            ret = []
            user_id = kwargs.get('user_id')
            if user_id != path.folder_name:
                raise exceptions.DownloadError(f'\'{user_id}\' user is not an allowed user.',
                                               code=status.HTTP_403_FORBIDDEN,
                                               )
            for item in os.listdir(path.full_path):
                metadata = self._metadata_file(path, item)
                ret.append(FileSystemFileMetadata(metadata, self.folder))
            return ret

        if not os.path.exists(path.full_path) or os.path.isdir(path.full_path):
            raise exceptions.MetadataError(
                'Could not retrieve folder or file \'{0}\''.format(path),
                code=404,
            )
        original_file_name = kwargs.get('original_file_name')

        metadata = self._metadata_file(path, original_file_name=original_file_name)
        return [FileSystemFileMetadata(metadata, self.folder)]

    async def list_files(self, paths: str, **kwargs) -> Dict[str, List[Optional[Any]]]:
        if not paths:
            paths = '/'
        paths = self.change_id_to_path(paths)
        files_and_id = []
        path_src = await self.validate_path(paths, prepend=self.folder)
        try:
            only_files = [f for f in listdir(path_src.full_path) if isfile(join(path_src.full_path, f))]
        except Exception:
            raise exceptions.DownloadError('Could not retrieve file \'{0}\''.format(paths),
                                           code=status.HTTP_404_NOT_FOUND)
        for files in only_files:
            try:
                data = get_file_per_path(os.path.join(path_src.full_path, files))
            except Exception as exception:
                logging.error(str(exception))
                logging.error(type(exception))
                continue
            try:
                files_and_id.append(data.get('file_id'))
            except Exception as exception:
                logging.exception(str(exception))
        return {"files_list": files_and_id}

    @staticmethod
    def change_id_to_path(user_id):
        """
        change the user id to path from uuid to str path
        :param user_id: the id user that uploaded the file to the folder that will be named with his user id
        :return: user id as a path to be user to store files for that user
        """
        if isinstance(user_id, str):
            try:
                user_id = str(user_id)
            except Exception:
                raise exceptions.DownloadError('type not supported \'{0}\''.format(type(user_id)),
                                               code=status.HTTP_406_NOT_ACCEPTABLE)

        if not user_id.endswith('/'):
            user_id += '/'
        if not user_id.startswith('/'):
            user_id = '/' + user_id
        return user_id

    async def download_zip_files(self, files_path_list: List[str], **kwargs) -> StreamingResponse:
        """
        this function allows the user to download multiple files from
        :param files_path_list: list of files ids to be downloaded
        :param kwargs: any special params that would be used in that function
        :return: a zip file that contains a file or list of files
        """
        files_list = []
        for path in files_path_list:
            path = await self.validate_path(path)
            if not os.path.exists(path.full_path):
                raise exceptions.DownloadError(f'\'{path}\' was not found.',
                                               code=status.HTTP_404_NOT_FOUND,
                                               )
            user_id = kwargs.get('user_id')
            if user_id != path.folder_name:
                raise exceptions.DownloadError(f'\'{user_id}\' user is not an allowed user. ',
                                               code=status.HTTP_403_FORBIDDEN,
                                               )
            files_list.append(path.full_path)
        zipped_file = BytesIO()
        with ZipFile(zipped_file, 'a', ZIP_DEFLATED) as zipObj:
            for path in files_list:
                filename = path.split(".")[0]
                extension = path.split(".")[-1]
                path = await self.validate_path(path)
                file_name = path.name
                try:
                    zipObj.write(filename=f'{filename}.{extension}', arcname=f'{file_name}')
                except exceptions as exception:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={str(exception)}
                    )
        zipped_file.seek(0)
        response = StreamingResponse(zipped_file, media_type="application/x-zip-compressed")
        return response

    async def delete_multiple_files(self, files_id_list: dict) -> list:
        """
        this function can used to deleted multiple files by providing a list of file ids
        :param files_id_list: list of file ids that will be provided example
        {"files_list": ['test1_id', 'test_id']
        :return: list of file ids that where deleted or EXCEPTION
        {'files where not deleted'} if list was empty
        """
        files_ids = []
        try:
            for file_id in files_id_list.get('files_list'):
                try:
                    data = get_file_per_id(file_id)
                    src_path = data.get('file_path')
                    try:
                        delete_file_per_id(file_id)
                        try:
                            await self.delete(src_path)
                            files_ids.append(file_id)
                        except FileNotFoundError as file_not_found:
                            logging.error(file_not_found)
                            logging.error("file_not_found")
                            continue
                    except IntegrityError as error:
                        logging.exception("file information not found or can't be deleted")
                        logging.error(str(error))
                        continue
                except (TypeError, AttributeError) as type_error:
                    logging.exception(type_error)
                    logging.exception("file information not found in db")
                    continue
        except Exception as type_err:
            logging.exception(str(type_err))
        return files_ids
