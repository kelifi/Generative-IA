import os
import pathlib


class FileHandlerUserConfig:
    # Database information
    DB_HOST = os.getenv("DB_HOST", "0.0.0.0")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "database")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "very_hard_pwd")
    DB_USER_TABLE = os.getenv("DB_USER_TABLE", "users")
    DB_FILE_TABLE = os.getenv("DB_FILE_TABLE", "files")
    DB_STREAMING_FILES_TABLE = os.getenv("DB_STREAMING_FILES_TABLE", "streaming_files")

    # define path
    current_dir = pathlib.Path(__file__).parent.parent
    sql_init = os.path.join(current_dir, 'init_db/init.sql')
    init_path = os.getenv('init_db.sql', sql_init)
    SSL_MODE = os.getenv("SSL_MODE", "allow")
    TEMP_METADATA_FILES = os.getenv("TEMP_METADATA_FILES", "./temp_metadata_files")

    # App information
    port: int = int(os.getenv("PORT", 8003))
    host: int = os.getenv("HOST", "0.0.0.0")
    SECRET_KEY = os.urandom(24).hex()
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_DEFAULT_EXPIRE_MINUTES = 3600


CHUNK_SIZE = 1024 * 1024  # 1MB chunk size
URL = "http://{}:{}".format(FileHandlerUserConfig.host, FileHandlerUserConfig.port)
download = URL + '/get_file'
download_testing = URL + '/get_file_for_testing'
FILE_NAME = "temp_file"
DEFAULT_TEST_USER = "0"
