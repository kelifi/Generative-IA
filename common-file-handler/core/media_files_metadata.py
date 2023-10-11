import os
import subprocess
from typing import Union
import uuid

import ffmpeg
from fastapi import UploadFile
from loguru import logger

from authorization.config.conf import FileHandlerUserConfig
from authorization.models.structures import FileType
from core.exceptions import ProcessFailError
import filetype


class MediaFilesMetadataService:
    async def create_duration_process(self, file: UploadFile, total_duration_left: float) -> Union[float, None]:
        """
        get the duration of a media file
        :param file: input file as bytes string
        :param total_duration_left: duration limit left for the user
        :return: the ts file duration
        """
        try:
            if not os.path.exists(FileHandlerUserConfig.TEMP_METADATA_FILES):
                os.mkdir(FileHandlerUserConfig.TEMP_METADATA_FILES)
            temp_file = f"{FileHandlerUserConfig.TEMP_METADATA_FILES}/{str(uuid.uuid4())}"
            with open(temp_file, "wb") as temp:
                temp.write(file.file.read())
            await file.seek(0)
            file_duration = self.get_duration_of_file(temp_file)
            self.clean_temp_file(temp_file)
            return self.verify_upload_access(file_duration, total_duration_left) if file_duration else None
        except subprocess.CalledProcessError:
            raise ProcessFailError

    @staticmethod
    def get_duration_of_file(filename: str) -> Union[float, None]:
        """
        get the duration of a temp file
        :param filename:
        :return: the ts file duration
        """
        try:
            file_kind = filetype.guess(filename)
            media_file_type = file_kind.mime.split('/')[0]
            if media_file_type != FileType.invalid:
                probe = ffmpeg.probe(filename)
                logger.info(f" duration of file uploaded: {float(probe['format']['duration'])}")
                return float(probe['format']["duration"])
        except (subprocess.CalledProcessError, ValueError):
            logger.info("Error in finding the file duration")
        return None

    @staticmethod
    def verify_upload_access(duration_info: float, total_duration_left: float) -> Union[float, None]:
        """
        verify if the user is able to upload the file
        :param duration_info: info of current file duration saved in a temp file
        :param total_duration_left: duration left for user
        :return bool
        """
        try:
            duration = total_duration_left - duration_info
            logger.info(f"duration left {duration}")
            return duration if duration > 0 else None
        except IOError:
            logger.error("error in reading duration file")
            raise FileNotFoundError("duration file is not founded")

    @staticmethod
    def clean_temp_file(path: str) -> bool:
        """
        remove a duration temp file after verifying the restriction
        :param path: path to file
        """
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            logger.error(f"File {path} does not exist")
            return False


