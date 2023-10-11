from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AppEnv(str, Enum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class RequestMethod(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"


class ModelTypes(str, Enum):
    CHAT = "chat"
    CLASSIFICATION = "classification"
    DATABASE = "database"


class WorkspaceType(str, Enum):
    CHAT = "chat"
    DATABASE = "database"


class UpdateStatusDataModel(BaseModel):
    id: UUID = Field(..., description="id", example='d391c642-563c-11ee-8c99-0242ac120002')
    updated: bool = Field(..., description="Status of the update")
