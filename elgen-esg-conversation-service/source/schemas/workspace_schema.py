from uuid import UUID

from pydantic import BaseModel, Field

from source.schemas.source_schema import SourceOutputModel, SourceTypeModel


class WorkspaceInput(BaseModel):
    name: str | None = Field(None, description="workspace name")
    description: str | None = Field(None, description="workspace description")
    type_id: UUID | None = Field(None, description="workspace type")
    active: bool | None = Field(True, description="workspace active or not")
    classification_change_enabled: bool | None = Field(None, description="Enable/disable classification")
    stop_answer_process: bool | None = Field(None, description="Enable/disable classification")
    available_model_codes: list[str] | None = Field(None, description="List of available models for a workspace")
    source_type_id: UUID | None = Field(None, description="Type of source")
    source_id: UUID | None = Field(None, description="Id of source")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class WorkspaceDto(WorkspaceInput):
    id: UUID = Field(..., description="workspace id")


class WorkspaceOutput(BaseModel):
    id: UUID = Field(..., description="workspace id")
    name: str = Field(..., description="workspace name")
    active: bool = Field(..., description="setted for activated workspace")
    description: str = Field(..., description="description of the workspace")


class WorkspaceByUserApiResponseModel(BaseModel):
    workspaces: list[WorkspaceDto] = []


class WorkspaceUsersApiModel(BaseModel):
    users_ids: list[str] = Field(..., description="workspace users")


class WorkspaceTypeInput(BaseModel):
    name: str = Field(..., description="type name", )
    description: str = Field(..., description="description of the Type")
    available: bool = Field(..., description="setted for activated Type")


class WorkspaceTypeModel(WorkspaceTypeInput):
    id: UUID = Field(..., description="workspace type id", example='d391c642-563c-11ee-8c99-0242ac120002')

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class WorkspaceTypeOutputModel(BaseModel):
    data: list[WorkspaceTypeModel]


class GenericWorkspaceInfo(WorkspaceOutput):
    classification_change_enabled: bool | None = Field(None, description="Enable/disable classification")
    stop_answer_process: bool | None = Field(None, description="Enable/disable classification")
    available_model_codes: list[str] = Field(..., description="List of available models for a workspace")
    workspace_type: WorkspaceTypeModel | None = Field(None, description="workspace type data")


class WorkspaceConfigOutputModel(GenericWorkspaceInfo):
    source: SourceOutputModel | None = Field(None, description="source data")
    source_type: SourceTypeModel | None = Field(None, description="source type data")


class GenericWorkspaceInfoOutput(BaseModel):
    """
    Generic information about workspace with workspace type info
    """
    workspaces: list[GenericWorkspaceInfo] = Field(default_factory=list)
