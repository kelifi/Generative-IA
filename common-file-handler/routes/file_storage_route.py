import json
import logging
from urllib import parse
from typing import List, Dict

from fastapi import Request
from fastapi.logger import logger

from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Header, Depends
from psycopg2._psycopg import IntegrityError
from starlette import status
from starlette.responses import StreamingResponse, Response, FileResponse

from authorization.config.conf import DEFAULT_TEST_USER
from authorization.db.crud import get_file_per_id, delete_file_per_id, get_additional_info_by_id, \
    get_last_file, get_user_files_metadata
from authorization.models.structures import FileListRequest, FilesListResponse
from core.config.conf import DEFAULT_PROVIDER
from core.config.make_provider import make_prov
from os import listdir
from os.path import isfile, join

from core.media_files_metadata import MediaFilesMetadataService
from core.providers.streaming_media_file import streaming_media_file_service
from core.streams.media_streaming import streaming_media, streaming_media_object, streaming_media_condition
from exceptions.service_exceptions import UserDataNotFoundException, DataLayerException

router = APIRouter()


@router.post("/save_file")
async def save_file(additional_info: str = None, user_id: str = None, overwrite: bool = None,
                    file: UploadFile = File(...)
                    ) -> dict:
    """
    :param overwrite:
    :param user_id: the user id
    :param additional_info: optional additional info
    :param file: the file to save
    :param api_key: the api key provided to use the service
    :return:
    """
    provider = make_prov(DEFAULT_PROVIDER)
    file.filename = parse.unquote(file.filename)
    additional_info_json = json.loads(additional_info) if additional_info else None
    upload_result = await provider.upload(file, user_id, overwrite=overwrite, additional_info=additional_info_json)
    if not upload_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='file was not uploaded'
        )
    return upload_result


@router.post("/v1/save_file")
async def save_file_v1(file_name: str, user_id: str = None, overwrite: bool = None, file: UploadFile = File(...)
                       ) -> dict:
    """
    :param overwrite:
    :param user_id: the user id
    :param file: the file to save
    :param file_name: the original file name
    :return:
    """
    provider = make_prov(DEFAULT_PROVIDER)
    file.filename = file_name
    upload_result = await provider.upload(file, user_id, overwrite=overwrite)
    if not upload_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='file was not uploaded'
        )
    return upload_result


@router.get("/get_file")
async def get_file(user_id: str, file_id: str = None) -> Response:
    r"""Download a file from this provider.

    :param file_id: the id of the file that will be used to fetch the file path to downloaded it
    :param user_id:  resprents the Path to the file to be downloaded
    :param \*\*kwargs: ( :class:`dict` ) Arguments to be parsed by child classes
    :rtype: :class:`.Response`
    :raises: :class:`.HTTPException`
    """
    data = get_file_per_id(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )

    src_path = data.get('file_path')
    provider = make_prov(DEFAULT_PROVIDER)
    download_result = await provider.download(src_path, user_id=user_id)

    if not download_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='no api key found for this user'
        )
    return download_result


@router.get("/streaming_media_file")
async def streaming_media_file(file_id: str, user_id: str, range: str = Header(None)):
    id_file_user_instance = str(file_id) + user_id
    await streaming_media_file_service(user_id, file_id, id_file_user_instance)
    logger.warning("audio file path" + str(streaming_media_object.audio_file_path))

    try:
        return await streaming_media(streaming_media_object.audio_file_path, range)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail='Error in streaming that file',
        )


@router.get("/streaming_media_file_condition")
async def streaming_media_file_condition(file_id: str, user_id: str, range: str = Header(None)):
    id_file_user_instance = str(file_id) + user_id
    await streaming_media_file_service(user_id, file_id, id_file_user_instance)

    try:
        return await streaming_media_condition(streaming_media_object.audio_file_path, range)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail='Error in streaming that file',
        )


@router.get("/get_file_for_testing")
async def get_file_for_testing(file_name: str) -> Response:
    r"""Download a file from this provider.

    :param file_name: the name of the file that will be used to fetch the file path to downloaded it
    :rtype: :class:`.Response`
    :raises: :class:`.HTTPException`
    """
    provider = make_prov(DEFAULT_PROVIDER)
    file_path = "/" + DEFAULT_TEST_USER + "/" + file_name
    download_result = await provider.download(file_path, user_id=DEFAULT_TEST_USER)

    if not download_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='no api key found for this user'
        )
    return download_result


@router.get("/media_folder_testing_files")
async def media_folder_testing_path() -> list:
    r"""Download a file from this provider.
    :rtype: :class:`.Response`
    :raises: :class:`.HTTPException`
    """
    default_folder = "/" + DEFAULT_TEST_USER + "/"

    media_files = [default_folder + file for file in listdir(default_folder)
                   if isfile(join(default_folder, file))]

    if not media_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='not finding files in folder'
        )

    return media_files


@router.delete("/delete_file")
async def delete_file_with_id(file_id: str = None, recursive: str = None,
                              ):
    """
    this endpoint is used to delete a given file by providing it's id
    :rtype: (`dict`)
    :raises: :class:`.HTTPException`
    :return: {"file deleted"}
    """
    data = get_file_per_id(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )
    src_path = data.get('file_path')
    try:
        delete_file_per_id(file_id)
    except IntegrityError as error:
        logging.exception("file information not found or can't be deleted")
        logging.error(str(error))
    provider = make_prov(DEFAULT_PROVIDER)
    delete_file_response = await provider.delete(src_path, recursive=recursive)
    if not delete_file_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='file was not deleted'
        )
    return delete_file_response


@router.get("/list_files")
async def list_files(src_path: str = None):
    """
    this endpoint is used to list all the file ids that a given user uploaded
    :param src_path: or we can say user id in our case
    :rtype: (`List[str]` or HTTPException)
    :raises: :class:`.HTTPException`
    :return: list of file ids
    """
    provider = make_prov(DEFAULT_PROVIDER)
    list_files_result = await provider.list_files(src_path)
    if not list_files_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found or user dont have files"
        )
    return list_files_result


@router.get("/metadata_id")
async def metadata_with_id(user_id: str, file_id: str = None) \
        -> dict or HTTPException:
    """
    this endpoint is used to get the file metadata by providing the file id in the data base
    :param user_id: the id user that uploaded the file to the folder that will be named with his user id
    :param file_id: the id of file that will be used to get the file path from the database
    :raises: :class:`.HTTPException`
    :return:
    """
    original_name = ""
    data = get_file_per_id(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )
    src_path = data.get('file_path')
    try:
        original_name = data.get('original_file_name')
    except (TypeError, AttributeError) as type_error:
        logging.exception(type_error)
        logging.exception("file information not found in db")
    provider = make_prov(DEFAULT_PROVIDER)
    metadata_result = await provider.metadata(src_path, user_id=user_id,
                                              original_file_name=original_name)
    if not metadata_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file metadata can't be provided"
        )
    return metadata_result


@router.post("/metadata_ids")
async def metadata_with_ids(user_id: str = Body(...), file_ids: List[str] = Body(...)) \
        -> dict or HTTPException:
    """
    this endpoint is used to get the file metadata by providing the file id in the data base
    :param file_ids:
    :param user_id: the id user that uploaded the file to the folder that will be named with his user id
    :raises: :class:`.HTTPException`
    :return:
    """
    result = []
    for file_id in file_ids:
        original_name = ""
        data = get_file_per_id(file_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="file information not found in db"
            )
        src_path = data.get('file_path')
        try:
            original_name = data.get('original_file_name')
        except (TypeError, AttributeError) as type_error:
            logging.exception(type_error)
            logging.exception("file information not found in db")
        provider = make_prov(DEFAULT_PROVIDER)
        metadata_result = await provider.metadatas(src_path, user_id=user_id,
                                                   original_file_name=original_name)
        metadata_result = metadata_result.__dict__
        metadata_result["file_id"] = file_id
        result.append(metadata_result)
    return result


@router.get("/additional-info")
async def get_additional_info(file_id: str = None) \
        -> dict or HTTPException:
    """
    this endpoint is used to get the file additional info by providing the file id in the data base

    :param file_id: the id of file that will be used to get the file path from the database
    :raises: :class:`.HTTPException`
    :return:
    """

    data = get_additional_info_by_id(file_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )

    return data.get("additional_info")


@router.post("/get_zip_files")
async def get_zip_files(user_id: str, files_id_list: dict = None) \
        -> StreamingResponse or HTTPException:
    """
     this endpoint allows the user to download multiple files from
     :param user_id: the id user that uploaded the file to the folder that will be named with his user id
     :param files_id_list: list of files ids to be downloaded
     :rtype: (`StreamingResponse` or HTTPException)
     :return: a zip file that contains a file or list of files
     """
    src_path_list = []
    try:
        for file_id in files_id_list.get('files_list'):
            try:
                data = get_file_per_id(file_id)
                src_path = data.get('file_path')
                src_path_list.append(src_path)
            except (TypeError, HTTPException, AttributeError) as type_error:
                logging.exception(type_error)
                logging.exception("file information not found in db")
    except Exception as type_err:
        logging.exception(str(type_err))
    provider = make_prov(DEFAULT_PROVIDER)
    result_download_zip_file = await provider.download_zip_files(src_path_list, user_id=user_id)
    if not result_download_zip_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='files where not downloaded'
        )
    return result_download_zip_file


@router.delete("/multiple_files")
async def delete_multiple_files(files_id_list: dict = None) \
        -> Dict[str, List]:
    """
    this endpoint is used to deleted a file or  multiple files at once by providing a list of file ids
    :param files_id_list: list of file ids that will be provided example
    {"files_list": ['test1_id', 'test_id']

    :rtype: (`List[str]` or HTTPException)
    :return: list of file ids that where deleted or EXCEPTION
    {'files where not deleted'} if list was empty
    """
    provider = make_prov(DEFAULT_PROVIDER)
    deleted_files_list = await provider.delete_multiple_files(files_id_list)
    logging.warning(deleted_files_list)
    if not deleted_files_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='files where not deleted'
        )
    return {'files_deleted': deleted_files_list}


@router.get("/files/last")
async def get_last(user_id: str) \
        -> dict or HTTPException:
    data = get_last_file(user_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )
    return data


@router.post("/files/metadata")
async def get_files_metadata(
        request: Request,
        query_params: FileListRequest = Depends(FileListRequest)
) -> FilesListResponse or HTTPException:
    """
    this endpoint is used to fetch a paginated list of files instead of getting all the files from endpoint "/file_list"

    """
    logger.info(request)

    try:
        result = get_user_files_metadata(
            limit=query_params.limit,
            offset=query_params.offset,
            column=query_params.column,
            direction=query_params.direction,
            src_path=query_params.src_path,
            files_id=query_params.files_ids)

    except ValueError as error:
        logger.error(error)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )
    except UserDataNotFoundException as error:
        logger.error(error)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this api key"
        )
    except DataLayerException as error:
        logger.error(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

    return FilesListResponse.parse_obj(result)


@router.post("/restricted_upload")
async def upload_media_file_restricted(total_duration_left: float,
                                       user_id: str = None,
                                       file: UploadFile = File(...),
                                       media_files_service: MediaFilesMetadataService =
                                       Depends(MediaFilesMetadataService)) \
        -> dict or HTTPException:
    """
    save a media file with restriction on the file duration
    :param total_duration_left: duration left for the user
    :param file: the file to save
    :param user_id
    :param media_files_service
    :return:
    """
    logger.info(f"total duration left for the user is : {total_duration_left}")
    restriction_result = await media_files_service.create_duration_process(file, total_duration_left)
    if not restriction_result or type(restriction_result) is bool:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sorry, you reached the limit of uploading !"
        )

    provider = make_prov(DEFAULT_PROVIDER)
    file.filename = parse.unquote(file.filename)
    upload_result = await provider.upload(file, user_id, overwrite=True)
    if not upload_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='file was not uploaded'
        )
    upload_result.update({"total_duration_left": restriction_result})
    return upload_result
