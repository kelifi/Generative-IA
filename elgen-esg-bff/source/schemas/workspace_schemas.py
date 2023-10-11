from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from source.schemas.source_schemas import SourceTypeSchema, SourceDataInput
from source.utils.utils import CamelModel


class WorkspaceInput(BaseModel):
    name: str | None = Field(None, description="workspace name")
    description: str | None = Field(None, description="workspace description")
    type_id: UUID | None = Field(None, description="workspace type", alias='typeId')
    active: bool | None = Field(True, description="workspace active or not")
    classification_change_enabled: bool | None = Field(None, description="Enable/disable classification",
                                                       alias='classificationChangeEnabled')
    stop_answer_process: bool | None = Field(None, description="Enable/disable classification",
                                             alias='stopAnswerProcess')
    available_model_codes: list[str] | None = Field(None, description="List of available models for a workspace",
                                                    alias="models")
    source_type_id: UUID | None = Field(None, description="Type of source", alias='sourceTypeId')
    source_id: UUID | None = Field(None, description="Id of source", alias="sourceId")

    class Config:
        allow_population_by_field_name = True


class WorkspaceDto(WorkspaceInput):
    id: UUID = Field(..., description="workspace id")


class WorkspaceByUserApiResponseModel(BaseModel):
    workspaces: list[WorkspaceDto] = Field(default_factory=[], description="a list of WorkspaceDto objects")


class WorkspaceOutput(CamelModel):
    id: str = Field(..., description="workspace id", )
    name: str = Field(..., description="workspace name", )
    active: bool = Field(..., description="setted for activated workspace", )
    description: str = Field(..., description="description of the workspace", )


class WorkspaceUsersApiModel(BaseModel):
    users_ids: list[str] = Field(..., description="workspace users")


class WorkspaceTypesEnum(str, Enum):
    database = "database"
    chat = "chat"


class WorkspaceTypeModel(BaseModel):
    id: str = Field(..., description="workspace type id")
    name: WorkspaceTypesEnum = Field(..., description="workspace type name")
    description: str = Field(..., description="description of the workspace type")
    available: bool = Field(..., description="setted for activated workspace")


class WorkspaceTypeOutputModel(BaseModel):
    data: list[WorkspaceTypeModel]


class GenericWorkspaceOutputModel(WorkspaceOutput):
    classification_change_enabled: bool | None = Field(None, description="Enable/disable classification",
                                                       alias='classificationChangeEnabled')
    stop_answer_process: bool | None = Field(None, description="Enable/disable classification",
                                             alias='stopAnswerProcess')
    available_model_codes: list[str] = Field(..., description="List of available models for a workspace",
                                             alias="models")
    workspace_type: WorkspaceTypeModel | None = Field(None, description="workspace type data", alias="type")


class WorkspaceConfigOutputModel(GenericWorkspaceOutputModel):
    source: SourceDataInput | None = Field(None, description="source data")
    source_type: SourceTypeSchema | None = Field(None, description="source type data")


class GenericWorkspacesResponseModel(BaseModel):
    """
    Generic information about workspaces with workspace type info
    """
    workspaces: list[GenericWorkspaceOutputModel] = Field(default_factory=list)
