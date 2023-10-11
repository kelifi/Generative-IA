import json
import logging
from typing import Type, Dict, Any, Set, List, Optional

from fastapi import HTTPException
from psycopg2 import IntegrityError, DataError, DatabaseError, ProgrammingError, OperationalError
from starlette import status
from starlette.responses import Response

from authorization.config.conf import FileHandlerUserConfig
from authorization.db.postgres import CursorFromConnectionPool, RealDictCursorFromConnectionPool
from authorization.db.queries import FileQuery, UserQuery
from authorization.models.structures import UserInDB, FileInDB, StreamingFileInDB, FileOutDB
from authorization.utils.auth import get_password_hash, generate_key, verify_password
from exceptions.service_exceptions import DataLayerException, UserDataNotFoundException


class User:
    def __init__(self, user: UserInDB):
        self.user = user

    def create(self) -> dict:
        """
        create user in database
        :return: success/error message
        """
        # This is creating a new connection pool
        hashed_password = get_password_hash(self.user.password)
        api_key = generate_key()

        try:
            with CursorFromConnectionPool() as cursor:
                cursor.execute((f"INSERT INTO {FileHandlerUserConfig.DB_USER_TABLE} "
                                "(user_name,default_directory , hashed_password, api_key, email) "
                                "VALUES (%s, %s, %s, %s, %s)"),
                               (self.user.user_name, self.user.default_directory, hashed_password, api_key,
                                self.user.email))
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.args[0],
            )
        return {'success': f'user {self.user.user_name} created successfully', 'api_key': api_key}


def get_user_by_key(key: str) -> dict:
    with CursorFromConnectionPool() as cursor:
        cursor.execute(
            f'SELECT user_name,api_key FROM {FileHandlerUserConfig.DB_USER_TABLE} WHERE api_key= \'{key}\'')
        try:
            user_name, token = cursor.fetchone()
            response = {
                "user_name": user_name,
                "key": token
            }
        except TypeError:
            logging.warning(f'api key {key} was not found.')

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'api key {key} was not found.',
            )

        return response


def get_key_per_user(user_name: str, password: str) -> Dict[str, Any]:
    """

    :param user_name: the user id exp : aldoc
    :param password: the user password
    :return: the user's api key
    """
    with CursorFromConnectionPool() as cursor:
        cursor.execute(
            f'SELECT user_name,api_key,hashed_password FROM {FileHandlerUserConfig.DB_USER_TABLE} WHERE user_name= \'{user_name}\'')
        try:
            user_name, key, hashed_password = cursor.fetchone()
            response = {
                "user_name": user_name,
                "hashed_password": hashed_password,
                "key": key
            }
        except TypeError:
            logging.warning(f'user {user_name} was not found.')

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'user {user_name} was not found.',
            )
        if not verify_password(password, response.get('hashed_password')):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'password was wrong.',
            )

        return {'api_key': response.get('key')}


def save_file_per_id(data: Type[FileInDB]) -> any:
    """
    create user in database
    :return: success/error message
    """
    # This is creating a new connection pool

    try:
        with CursorFromConnectionPool() as cursor:
            cursor.execute((f"INSERT INTO {FileHandlerUserConfig.DB_FILE_TABLE} "
                            "(file_path , file_size, file_creation_time, file_content,file_name, full_path,"
                            "original_name, additional_info) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) returning id"),
                           (data.file_path, data.file_size, data.file_creation_time, data.file_content,
                            data.file_name, data.full_path, data.original_name, json.dumps(data.additional_info)))
            db_resonse = cursor.fetchone()
    except IntegrityError as integrity_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=integrity_exception.args[0],
        )

    return db_resonse[0]


def get_file_per_id(file_id: str) -> dict:
    with CursorFromConnectionPool() as cursor:
        try:
            cursor.execute(
                f"SELECT id,file_path,original_name FROM {FileHandlerUserConfig.DB_FILE_TABLE} WHERE id= '{file_id}'")

            file_id, file_path, original_file_name = cursor.fetchone()
            response = {
                "file_id": file_id,
                "file_path": file_path,
                "original_file_name": original_file_name
            }
            return response
        except (TypeError, Exception):
            logging.warning(f'file id {file_id} was not found or file format was wrong.')
            # raise HTTPException(404, "file not found")
            return {}


def get_last_file(user_id: str) -> dict:
    print(type(user_id))
    with CursorFromConnectionPool() as cursor:
        cursor.execute(
            f"SELECT id,original_name FROM {FileHandlerUserConfig.DB_FILE_TABLE} WHERE file_path "
            f"like '%{user_id}%' ORDER BY file_name DESC LIMIT 1")

        file_id, original_file_name = cursor.fetchone()
        response = {
            "file_id": file_id,
            "original_file_name": original_file_name
        }
        return response


def delete_file_per_id(file_id: str) -> Set[str]:
    """
    create user in database
    :return: success/error message
    """
    # This is creating a new connection pool
    try:
        with CursorFromConnectionPool() as cursor:
            cursor.execute(
                f'DELETE FROM {FileHandlerUserConfig.DB_FILE_TABLE} WHERE id= \'{file_id}\'')

    except IntegrityError as e:
        raise IntegrityError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.args[0],
        )
    return {'deleted'}


def get_file_per_path(full_path: str) -> dict:
    """

    :param full_path: the path of the file used to get the file id
    :return: dict{"file_id": file_id, "full_path": full_path}
    """
    with CursorFromConnectionPool() as cursor:
        cursor.execute(
            f"SELECT id,full_path FROM {FileHandlerUserConfig.DB_FILE_TABLE} WHERE full_path= '{full_path}'")
        try:
            file_id, full_path = cursor.fetchone()
            response = {
                "file_id": file_id,
                "full_path": full_path
            }
            return response
        except TypeError:
            logging.warning(f'file path {full_path} was not found.')
            raise HTTPException(404, "File not found in DB")


def get_additional_info_by_id(file_id: str) -> dict:
    with CursorFromConnectionPool() as cursor:
        try:
            cursor.execute(
                f"SELECT additional_info, id FROM {FileHandlerUserConfig.DB_FILE_TABLE} WHERE id= '{file_id}'")

            additional_info, id = cursor.fetchone()
            response = {
                "additional_info": additional_info,
                "id": id
            }
            return response
        except (TypeError, Exception):
            logging.exception(f'file with id {file_id} was not found.')
            return {}


def save_streaming_temp_file(data: StreamingFileInDB) -> any:
    """
    create streaming temp file in database
    :return: success/error message
    """
    # This is creating a new connection pool

    try:
        with CursorFromConnectionPool() as cursor:
            cursor.execute((f"INSERT INTO {FileHandlerUserConfig.DB_STREAMING_FILES_TABLE} "
                            "(file_temp_path, file_id, file_creation_time) "
                            "VALUES (%s, %s, %s) returning id"),
                           (data.file_temp_path, data.file_id, data.file_creation_time))
            db_resonse = cursor.fetchone()
            return db_resonse[0]
    except IntegrityError as integrity_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=integrity_exception.args[0],
        )


def get_streaming_file_per_id(file_id: str) -> dict:
    """
    get streaming temp file info
    :param file_id: the path of the file used to get the streaming file id
    :return: dict{"file_id": file_id, "full_path": full_path}
    """
    with CursorFromConnectionPool() as cursor:
        cursor.execute(
            f"SELECT file_id,file_temp_path FROM {FileHandlerUserConfig.DB_STREAMING_FILES_TABLE} "
            f"WHERE file_id= '{file_id}'")
        try:
            file_id, file_temp_path = cursor.fetchone()
            response = {
                "file_id": file_id,
                "file_temp_path": file_temp_path
            }
            return response
        except TypeError:
            logging.warning(f'file path {file_id} was not found.')
            return {}


def delete_all_streaming_temp_files():
    """
    delete all streaming temp files
    :return: success/error message
    """
    # This is creating a new connection pool
    try:
        with CursorFromConnectionPool() as cursor:
            cursor.execute(
                f'DELETE FROM {FileHandlerUserConfig.DB_STREAMING_FILES_TABLE}')

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except IntegrityError as e:
        raise IntegrityError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.args[0],
        )


def get_single_user_data_by_api_key(key: str, fields: Optional[List[str]] = None) -> dict:
    try:
        with CursorFromConnectionPool() as cursor:
            cursor.execute(UserQuery.select_user_by_api_key_query(key, fields))
            user_data = cursor.fetchone()
    except (IntegrityError, DataError, DatabaseError, ProgrammingError, OperationalError) as error:
        raise DataLayerException(str(error))

    if not user_data:
        raise UserDataNotFoundException
    return dict(zip(fields, user_data))


def get_user_files_metadata(
                            src_path: str,
                            limit: Optional[int] = None,
                            offset: Optional[int] = None,
                            column: Optional[str] = None,
                            direction: Optional[str] = None,
                            files_id:Optional[List[str]]=None
                            ):
    """
    get a paginated list of files
    :param api_key: client api key
    :param offset: 1 - .. page request by client
    :param limit: how many rows in one page
    :param column: column for order by
    :param direction: asc or desc order by
    :return: list of files and its length
    """
    select_fields = list(FileOutDB.__fields__)
    FileQuery.validate_column_exist(existing_fields=FileQuery.fields, column=column,
                                    detail=f"Query Param Column does not exist")
    FileQuery.validate_query_pagination(offset=offset, limit=limit)
    try:
        with RealDictCursorFromConnectionPool() as cursor:

            cursor.execute(
                FileQuery.select_user_files_by_directory_query(user_directory=src_path,
                                                               select_fields=select_fields,
                                                               limit=limit,
                                                               offset=offset,
                                                               column=column,
                                                               direction=direction,
                                                               files_id=files_id)
            )
            response = cursor.fetchall()
            cursor.execute(
                FileQuery.get_file_count(user_directory=src_path)

            )
            files_count = cursor.fetchone().get('count')
    except (IntegrityError, DataError, DatabaseError, ProgrammingError, OperationalError) as error:
        raise DataLayerException(str(error))

    return {
        "data": response,
        "total_rows": files_count
    }
