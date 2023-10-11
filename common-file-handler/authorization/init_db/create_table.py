import logging

from authorization.config.conf import FileHandlerUserConfig
from authorization.db.postgres import Database, CursorFromConnectionPool

# Database.initialise(database=FileHandlerUserConfig.DB_NAME, user=FileHandlerUserConfig.DB_USER,
#                     password=FileHandlerUserConfig.DB_PASSWORD, host=FileHandlerUserConfig.DB_HOST,
#                     port=FileHandlerUserConfig.DB_PORT)


def create_table():
    """
    Create users table
    """
    with open(FileHandlerUserConfig.init_path, 'r') as file:
        data = file.read().replace('\n', '')
    with CursorFromConnectionPool() as cursor:
        cursor.execute(data)
    print("done")
    return True

