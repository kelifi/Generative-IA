import asyncio
import logging
from os import path
from pathlib import Path
from loguru import logger
from fastapi import Response, HTTPException
from authorization.config.conf import CHUNK_SIZE
from core.streams.streamer_object import Streaming_media_object

streaming_media_object = Streaming_media_object.Instance()


async def streaming_media(audio_file_path: str, range: str) -> Response:
    """
    Stream the audio file called from the file handler chunk per chunk.
        :param audio_file_path: the audio file path
        :param range : range received for starting and ending points
        :return: response header
    """

    try:
        start, end = range.replace("bytes=", "").split("-")

        start = int(start) if start else 0

        logger.info("audio_file_path " + str(audio_file_path))
        streaming_media_object.video_path = Path(audio_file_path)
        logger.info("video_path  " + str(streaming_media_object.video_path))

        end = int(end) if end else start + CHUNK_SIZE
        logger.info("start" + str(start) + " and end " + str(end))

    except TypeError as error:
        logger.error("No bytes parameters are specified{}".format(error))
        raise TypeError("No bytes parameters are specified")

    try:
        logger.info("returning streaming" + str(start) + "and file size is " + str(
            streaming_media_object.video_path.stat().st_size))
        size_video = path.getsize(audio_file_path)

        if start < size_video - 1:
            end = size_video - 1 if end > streaming_media_object.video_path.stat().st_size else end

            logger.info("end chunk  " + str(end))

            with open(streaming_media_object.video_path, "rb") as video:
                video.seek(start)
                data = video.read(end - start)
                streaming_media_object.file_size = str(streaming_media_object.video_path.stat().st_size)

                headers = {
                    'Content-Range': f'bytes {str(start)}-{str(end)}/{str(size_video)}',
                    'Accept-Ranges': 'bytes'
                }

            return Response(data, status_code=206, headers=headers, media_type="video/mp4")
    except Exception as error:
        raise HTTPException(
            status_code=404,
            detail="media file path not founded"
        )


async def streaming_media_condition(audio_file_path: str, range: str):
    """
    Stream the audio file called from the file handler chunk per chunk.
    The logic of this streamer is different because of the difference in the browser's pre implemented audio component
        :param audio_file_path: the audio file path
        :param range : range received for starting and ending points
        :return: response header
    """

    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(start + CHUNK_SIZE)

    with open(audio_file_path, "rb") as myfile:
        myfile.seek(start)
        data = myfile.read(end - start)
        size_video = str(path.getsize(audio_file_path))

        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{size_video}',
            'Accept-Ranges': 'bytes'
        }
        return Response(content=data, status_code=206, headers=headers, media_type="video/mp4")
