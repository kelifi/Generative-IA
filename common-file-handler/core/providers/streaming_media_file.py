import logging
import os
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from loguru import logger
from starlette import status
from starlette.responses import FileResponse

from authorization.db.crud import get_file_per_id, save_streaming_temp_file, get_streaming_file_per_id, \
    delete_all_streaming_temp_files
from authorization.models.structures import StreamingFileInDB
from core.config.conf import DEFAULT_PROVIDER
from core.config.make_provider import make_prov
from core.streams.media_streaming import streaming_media_object
from datetime import datetime
from fastapi.logger import logger



async def streaming_media_file_service(user_id: str, file_id: str = None, user_file_instance_id: str = ""):
    """
        :param user_id: the path entered as string
        :param file_id: the id of the file
        :param user_file_instance_id: the id of the file opened for streaming
        :return: file path (file or directory)
    """
    data = get_file_per_id(file_id)
    logger.warning("getting file data" + str(data))

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file information not found in db"
        )

    src_path = data.get('file_path')
    provider = make_prov(DEFAULT_PROVIDER)

    streaming_media_object.file_download = user_file_instance_id
    result = get_streaming_file_per_id(user_file_instance_id)
    if result and result['file_id'] == user_file_instance_id:
        file_temp = result['file_temp_path']
        file_temp = FileResponse(file_temp)
    else:
        logger.info("Downloading file from blob storage")
        file_temp = await provider.download(src_path, user_id=user_id)
        try:
            json_compatible_item_data = jsonable_encoder(file_temp)
            streamed_file = json_compatible_item_data['path']
            streaming_file_temp_data = StreamingFileInDB(file_id=user_file_instance_id, file_temp_path=streamed_file,
                                                         file_creation_time=datetime.today().strftime("%d/%m/%Y"))
            file_id = save_streaming_temp_file(streaming_file_temp_data)

        except Exception as exception:
            logging.exception(exception)
            logging.exception("streaming file metadata was not saved in file handler")

    try:
        json_compatible_item_data = jsonable_encoder(file_temp)

        streamed_file = json_compatible_item_data['path']
        logger.info("streamed file path" + str(streamed_file))
        streaming_media_object.audio_file_path = streamed_file

        return streaming_media_object.audio_file_path

    except FileNotFoundError as error:
        raise FileNotFoundError("the media file is not found")
