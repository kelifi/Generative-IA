import enum
from functools import partial
from typing import List
from uuid import UUID
from enum import Enum
from typing import Optional

from fastapi import HTTPException, Query
from inflection import camelize
from pydantic import BaseModel, EmailStr, Field
from pydantic.class_validators import validator
from pypika import Order
from starlette import status


class CamelModel(BaseModel):
    """
    class configured to return select_fields in camelCase for all the child classes
    """

    def get_by_alias(self, alias):
        for field, details in self.__fields__.items():
            if details.alias == alias:
                return self.__getattribute__(field)
        raise AttributeError(f"'{self.__class__}' object has no attribute with alias '{alias}'")

    class Config:
        """
        Config to return select_fields as camelCase but keep using snake_case in dev
        """

        alias_generator = partial(camelize, uppercase_first_letter=False)
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        use_enum_values = True


class UserInDB(BaseModel):
    id: Optional[str]
    email: EmailStr
    default_directory: Optional[str]
    user_name: str
    password: str

    @validator('user_name')
    def allowed_service_types_names(cls, col):
        """ check if the user name can be used as a directory """
        list = [':', '*', '/', ' ', '?', '>', '|', '<', '"']
        for c in list:
            if c in col:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="user name not valid do not use [':', '*', '/', ' ', '?', '>', '|', '<']"
                )
        return col


class FileInDB(BaseModel):
    id: Optional[str]
    file_path: str
    file_size: str
    file_creation_time: str
    file_content: str
    file_name: str
    full_path: str
    original_name: str
    additional_info: dict


class StreamingFileInDB(BaseModel):
    id: Optional[str] = Field(
        description="the id of the streaming temp file",
        example=[])
    file_temp_path: str = Field(
        description="the path of the file",
        example="/tmp/tmp_134")
    file_id: str = Field(
        description="id of the original file",
        example="123e4567-e89b-12d3-a456-426614174000")
    file_creation_time: str = Field(
        description="file creation time",
        example="05-05-2022")


class File(BaseModel):
    id: Optional[str] = Field(
        description="the id of the streaming temp file",
        example=[])
    file_temp_path: str = Field(
        description="the path of the file",
        example="/tmp/tmp_134")


class SortingDirection(str, Enum):
    ASC = str(Order.asc.value).lower()
    DESC = str(Order.desc.value).lower()

    def upper(self):
        return str(self.value).upper()


class FileListRequest(CamelModel):
    limit: Optional[int]
    offset: Optional[int]
    column: Optional[str]
    direction: Optional[SortingDirection]
    files_ids: Optional[List[str]]
    src_path: str



class FileOutDB(CamelModel):
    id: UUID
    file_name: str
    file_size: str
    file_creation_time: str
    file_path: str
    file_content: str
    full_path: str
    original_name: str
    additional_info: Optional[dict]


class FilesListResponse(CamelModel):
    data: List[FileOutDB]
    total_rows: int


class FileType(enum.Enum):
    """
    file type enumerations
    """
    audio = "audio"
    video = 'video'
    invalid = 'invalid'
