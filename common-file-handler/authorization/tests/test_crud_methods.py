import pytest
from loguru import logger
import authorization.db.crud as crudFunctions
from authorization.config.conf import FileHandlerUserConfig
from authorization.config.test_config import UnitTestFiles
from authorization.db.postgres import Database

streaming_temp_file_data = UnitTestFiles.STREAMING_FILE_DATA
Database.initialise(database=FileHandlerUserConfig.DB_NAME, user=FileHandlerUserConfig.DB_USER,
                    password=FileHandlerUserConfig.DB_PASSWORD, host=FileHandlerUserConfig.DB_HOST,
                    port=FileHandlerUserConfig.DB_PORT)


def test_save_streaming_temp_file():
    """Check main postgresql fixture."""
    logger.info("Testing : adding streaming temp file to database")
    response = crudFunctions.save_streaming_temp_file(streaming_temp_file_data)
    assert response is not None
    assert isinstance(response, str)


def test_get_streaming_file_per_id():
    """ Test getting a streaming temp file data by file id """
    logger.info("Testing : getting temp file from db ")
    response = crudFunctions.get_streaming_file_per_id(streaming_temp_file_data.file_id)
    assert len(response) > 0
    assert response['file_id'] == streaming_temp_file_data.file_id
    assert response['file_temp_path'] == streaming_temp_file_data.file_temp_path


def test_delete_all_streaming_temp_files():
    """ Test getting deleting temp file from db"""
    logger.info("Testing: deleting temp file from db ")
    response = crudFunctions.delete_all_streaming_temp_files()
    assert response == {'deleted'}
