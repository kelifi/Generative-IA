from abc import ABCMeta, abstractmethod
from typing import Optional, List

from psycopg2 import IntegrityError
from pypika import Table, Query, Order, Criterion
from pypika.functions import Count
from pypika.queries import QueryBuilder as PypikaQueryBuilder

from authorization.config.conf import FileHandlerUserConfig
from authorization.models.structures import SortingDirection, FileOutDB


class GenericQueryBuilder(metaclass=ABCMeta):

    @property
    @abstractmethod
    def table_name(self):
        pass

    @property
    @abstractmethod
    def table(self):
        pass

    @property
    @abstractmethod
    def fields(self):
        pass

    @staticmethod
    def validate_schema_fields(existing_fields: List[str],
                               select_fields: List[str],
                               detail: Optional[str] = "A violation of fields schema") -> None:
        if select_fields and not set(select_fields).issubset(existing_fields):
            raise IntegrityError(detail)

    @staticmethod
    def validate_column_exist(existing_fields: List[str],
                              column: str,
                              detail: Optional[str] = "Column does not exist") -> None:
        if column and column not in existing_fields:
            raise ValueError(detail)

    @staticmethod
    def validate_query_pagination(offset: Optional[int] = None, limit: Optional[int] = None) -> bool:
        if limit is None and offset is None:
            return False

        if any((value is None for value in (limit, offset))) or not (limit > 0 and offset >= 0):
            raise ValueError(f'Bad Pagination Parameters: limit={limit}, offset={offset}')

        return True

    @classmethod
    def chain_query_pagination(cls, query: PypikaQueryBuilder, offset: int, limit: int) -> PypikaQueryBuilder:
        add_pagination = cls.validate_query_pagination(offset=offset, limit=limit)
        if add_pagination:
            query = query.limit(str(limit)) \
                .offset(str(offset))
        return query


class UserQuery(GenericQueryBuilder):
    table_name = FileHandlerUserConfig.DB_USER_TABLE
    table = Table(table_name)
    fields = ["id", "user_name", "default_directory", "hashed_password", "api_key", "email"]

    @classmethod
    def select_user_by_api_key_query(cls, api_key: str, fields: Optional[List[str]] = None):
        cls.validate_schema_fields(cls.fields, fields)

        fields = cls.fields if not fields else fields

        return str(Query().from_(cls.table).select(*fields).where(cls.table.api_key == api_key))


class FileQuery(GenericQueryBuilder):
    table_name = FileHandlerUserConfig.DB_FILE_TABLE
    table = Table(table_name)
    fields = list(FileOutDB.__fields__)

    @classmethod
    def select_user_files_by_directory_query(cls, user_directory: str,
                                             select_fields: Optional[List[str]] = None,
                                             limit: Optional[int] = None,
                                             offset: Optional[int] = None,
                                             column: Optional[str] = None,
                                             direction: Optional[SortingDirection] = None,
                                             files_id: Optional[List[str]] = None) -> str:
        cls.validate_schema_fields(cls.fields, select_fields)
        fields = select_fields if select_fields else cls.fields
        column = cls.fields[0] if not column else column
        direction = SortingDirection.ASC if not direction else direction

        query = Query() \
            .from_(cls.table) \
            .select(*fields) \
            .where(cls.table.full_path.like(f'%{user_directory}%'))
        if files_id:
            criterias = [cls.table.id == id for id in files_id]
            query = query.where(Criterion.any(criterias))
        query = query.orderby(column, order=Order(direction.upper()))

        query = cls.chain_query_pagination(query=query, limit=limit, offset=offset)
        return str(query)

    @classmethod
    def get_file_count(cls, user_directory: str):
        return str(Query() \
                   .from_(cls.table) \
                   .select(Count('*')) \
                   .as_('total_rows') \
                   .where(cls.table.full_path.like(f'%{user_directory}%')))
