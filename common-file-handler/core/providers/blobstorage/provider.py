import contextlib
import logging
import mimetypes
import os
import tempfile
import ntpath

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from typing import List
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from fastapi.responses import FileResponse, StreamingResponse
from starlette import status
from psycopg2._psycopg import IntegrityError
from fastapi import HTTPException

from authorization.db.crud import (save_file_per_id, get_file_per_path, delete_file_per_id, get_file_per_id)
from authorization.utils.api_key import get_user_folder
from core import provider, exceptions
from core.path_url import WaterButlerPath
from core.providers.filestorage.metadata import FileSystemFileMetadata
from core.utils import data_helper, append_id


class AzureBlobStorageProvider(provider.BaseProvider):
    """
    class created to make our service support azure blob storage
    by refactoring the BaseProvider methods
    """

    def __init__(self, credentials, settings, **kwargs):
        super().__init__(credentials, settings, **kwargs)
        self.connection_string = self.settings.get("connectionString")
        self.folder = get_user_folder()
        self.container_name = self.settings.get("container")
        self.service_client = BlobServiceClient.from_connection_string(self.connection_string,
                                                                       container_name=self.container_name)

        self.client = self.service_client.get_container_client(self.container_name)
        self.create_container()

    name = "Azure blob storage"

    def create_container(self):
        try:
            self.client.create_container()
        except Exception as e:
            logging.info(e)

    def delete_container(self):
        try:
            self.client.delete_container()
        except Exception as exception:
            logging.info(exception)

    @staticmethod
    async def validate_path(path: str, prepend: str) -> WaterButlerPath or None:
        try:
            return WaterButlerPath(path, prepend=prepend)
        except Exception as exception:
            logging.info(exception)

    async def upload(self, source, dest, **kwargs) -> dict:
        """
        Upload a single file to a path inside the container
        """
        file_id = ""
        overwrite = kwargs.get('overwrite')
        if not dest:
            dest = '/'
        dest = self.change_id_to_path(dest)
        logging.info(f'Uploading {source} to {dest}')
        if not dest.endswith('/'):
            dest += '/'
        paths = await self.validate_path(dest, prepend=self.folder)
        file_path = os.path.join(paths.path, source.filename)
        mime_type = mimetypes.guess_type(file_path)[0]
        data = await source.read()
        created = await self.exists(file_path)
        if not created:
            self.client.upload_blob(name=file_path, data=data,
                                    metadata={"content_type": mime_type if mime_type else "No type"
                                              }
                                    )
        else:
            if not overwrite:
                file_path = os.path.join(paths.path, append_id(source.filename))
                self.client.upload_blob(name=file_path, data=data,
                                        metadata={"content_type": mime_type if mime_type else "No type"
                                                  }
                                        )
            else:
                path = await self.validate_path('/' + file_path, prepend=self.folder)
                file_id = get_file_per_path(path.path)
                await self.delete(file_path)
                delete_file_per_id(file_id.get('file_id'))
                self.client.upload_blob(name=file_path, data=data,
                                        metadata={"content_type": mime_type if mime_type else "No type"
                                                  }
                                        )
        metadata = await self.metadata(file_path)
        data = data_helper(metadata[0], source.filename, kwargs.get('additional_info'))
        try:
            file_id = save_file_per_id(data)
        except Exception as exception:
            logging.exception(exception)
            logging.exception("file metadata was not saved in file handler")
        return {"success": "\'{}\' was saved!".format(ntpath.basename(file_path)),
                "file_id": file_id,
                "user_id": paths.name}

    async def delete(self, src_path, **kwargs):
        """
        Delete a file from azure blob storage
        """
        if not src_path == '' and not src_path.startswith('/'):
            src_path = '/' + src_path
        recursive = kwargs.get("recursive")
        path = await self.validate_path(src_path, prepend=self.folder)
        if recursive:
            return await self.rmdir(src_path)

        try:
            self.client.delete_blob(path.path)
        except Exception:
            raise FileNotFoundError(f' The system cannot find the file specified:{src_path}'
                                    )
        return {"file deleted"}

    async def rmdir(self, path):
        """
        Remove a directory and its contents recursively
        """
        blobs = await self.list_files(path, recursive=True)
        path = await self.validate_path(path, prepend=self.folder)
        path = path.path
        if not blobs:
            raise FileNotFoundError(f' The system cannot find the folder specified:{path}'
                                    )
        if not path == '' and not path.endswith('/'):
            path += '/'
        blobs = [path + blob for blob in blobs]
        for blob in blobs:
            self.client.delete_blob(blob)
        return {"directory deleted"}

    async def download(self, path, **kwargs) -> FileResponse:
        """
        Download a file on the local filesystem
        """
        if not path == '' and not path.startswith('/'):
            path = '/' + path
        source = await self.validate_path(path, prepend=self.folder)
        source = source.path

        dest = self.settings.get("dest")
        if not dest:
            raise Exception('A destination must be provided')

        blobs = await self.list_files(path)
        blobs = blobs.get('files_list')
        if blobs:
            # if source is a directory, dest must also be a directory
            if not source == '' and not source.endswith('/'):
                source += '/'
            if not dest.endswith('/'):
                dest += '/'
            # append the directory name from source to the destination
            dest += os.path.basename(os.path.normpath(source)) + '/'

            blobs = [source + blob for blob in blobs]
            for blob in blobs:
                blob_dest = dest + os.path.relpath(blob, source)
                await self.download_file(blob, blob_dest)
        else:
            return await self.download_file(source, dest)

    async def download_file(self, source, dest):
        """
        Download a single file to a path on the local filesystem
        """
        if dest.endswith('.'):
            dest += '/'
        try:
            blob_client = self.client.get_blob_client(blob=source)
            data = blob_client.download_blob()
            media_type = data.properties.metadata.get('content_type')
            with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as file:
                file.write(data.readall())
        except ResourceNotFoundError:
            raise exceptions.DownloadError(f'/{source} was not found.',
                                           code=status.HTTP_404_NOT_FOUND
                                           )
        return FileResponse(file.name, media_type=media_type)

    async def list_files(self, paths: str, **kwargs) -> dict:

        """
        List files under a path, optionally recursively
        """
        if not paths:
            paths = '/'
        paths = self.change_id_to_path(paths)

        path_src = await self.validate_path(paths, prepend=self.folder)
        path = path_src.path

        if not path == '' and not path.endswith('/'):
            path += '/'

        blob_iter = self.client.list_blobs(name_starts_with=path)
        files = []
        for blob in blob_iter:
            data = get_file_per_path(blob.name)
            try:
                files.append(data.get('file_id'))
            except Exception as exception:
                logging.exception(str(exception))
        return {"files_list": files}

    def metadata_file(self, resp, **kwargs) -> dict:
        logging.warning(resp)
        content_type = resp.metadata.get('content_type', "other")
        file_path = resp.name
        file_name = os.path.basename(file_path)
        creation_time = resp.creation_time.strftime('%a, %d %b %Y %H:%M:%S %z')
        original_file_name = kwargs.get('original_file_name')

        return {
            'path': file_path if file_path else None,
            'size': resp.size,
            'creation time': creation_time if creation_time else None,
            'Content type': content_type if content_type else None,
            'file name': file_name if file_name else None,
            'original_file_name': original_file_name
        }

    async def metadata(self, path_src: str, **kwargs) -> List[FileSystemFileMetadata]:
        """
        List files with meta data under a path, optionally recursively
        """
        blob_iter, path_basename, path_src = await self.check_path_src(path_src)

        files = []
        for blob in blob_iter:
            original_file_name = kwargs.get('original_file_name')
            with contextlib.suppress(TypeError):
                original_file_name = os.path.basename(original_file_name)

            meta_data = self.metadata_file(blob, original_file_name=original_file_name)
            if "." not in path_basename:
                meta_data['file name'] = path_basename
                files.append(FileSystemFileMetadata(meta_data, self.folder))

            else:
                if meta_data['path'] == path_src:
                    meta_data['file name'] = path_basename
                    files.append(FileSystemFileMetadata(meta_data, self.folder))
        if not files:
            raise exceptions.MetadataError(
                f"Could not retrieve folder or file '/{path_src}'",
                code=status.HTTP_404_NOT_FOUND
            )

        return files

    async def metadatas(self, path_src: str, **kwargs) -> dict:
        """
        List files with meta data under a path, optionally recursively
        """
        blob_iter, path_basename, path_src = await self.check_path_src(path_src)

        files = {}
        for blob in blob_iter:
            original_file_name = kwargs.get('original_file_name')
            with contextlib.suppress(TypeError):
                original_file_name = os.path.basename(original_file_name)

            meta_data = self.metadata_file(blob, original_file_name=original_file_name)
            if "." not in path_basename:
                meta_data['file name'] = path_basename
                files = FileSystemFileMetadata(meta_data, self.folder)

            else:
                if meta_data['path'] == path_src:
                    meta_data['file name'] = path_basename
                    files = FileSystemFileMetadata(meta_data, self.folder)
        if not files:
            raise exceptions.MetadataError(
                f"Could not retrieve folder or file '/{path_src}'",
                code=status.HTTP_404_NOT_FOUND
            )

        return files

    async def check_path_src(self, path_src):
        if not path_src:
            path_src = '/'
        if not path_src == '' and not path_src.startswith('/'):
            path_src = '/' + path_src
        path = await self.validate_path(path_src, prepend=self.folder)
        path_src = path.path
        path = os.path.dirname(path_src)
        path_basename = os.path.basename(path_src)
        if not path == '' and not path.endswith('/'):
            path += '/'
        blob_iter = self.client.list_blobs(name_starts_with=path_src)
        return blob_iter, path_basename, path_src

    @staticmethod
    def change_id_to_path(user_id):
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

    async def delete_multiple_files(self, files_id_list: dict) -> list:
        """
        this function allows the user to delete multiple files from
        :param files_id_list: list of files ids to be downloaded
        :return: a id list for the deleted files
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

    async def download_zip_files(self, files_path_list: List[str], **kwargs) -> StreamingResponse:

        """
        this function allows the user to download multiple files from
        :param files_path_list: list of files ids to be downloaded
        :param kwargs: any special params that would be used in that function
        :return: a zip file that contains a file or list of files
        """
        files_list = []
        for path in files_path_list:
            path = await self.validate_path(path, prepend=self.folder)
            user_id = kwargs.get('user_id')
            if user_id != path.folder_name:
                raise exceptions.DownloadError(f'\'{user_id}\' user is not an allowed user. ',
                                               code=status.HTTP_403_FORBIDDEN,
                                               )
            files_list.append(path.full_path)

        zipped_file = BytesIO()
        with ZipFile(zipped_file, 'a', ZIP_DEFLATED) as zip_obj:
            for source in files_list:
                file_name = ntpath.basename(source)
                blob_client = self.client.get_blob_client(blob=source)
                data = blob_client.download_blob()
                try:
                    zip_obj.writestr(file_name, data.content_as_bytes())
                except exceptions as exception:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={str(exception)}
                    )

        zipped_file.seek(0)
        return StreamingResponse(zipped_file, media_type="application/x-zip-compressed",
                                 headers={"Content-Disposition": f"attachment; filename=images.zip"})
