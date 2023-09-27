from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceInput(BaseModel):
    name: str = Field(..., description="workspace name")
    description: str | None = Field(None, description="workspace description")
    active: bool | None = Field(None, description="workspace active or not")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class WorkspaceDto(WorkspaceInput):
    id: UUID = Field(..., description="workspace id")


class WorkspaceOutput(BaseModel):
    id: str = Field(..., description="workspace id", )
    name: str = Field(..., description="workspace name", )
    active: bool = Field(..., description="setted for activated workspace", )
    description: str = Field(..., description="description of the workspace", )


class WorkspaceByUserApiResponseModel(BaseModel):
    workspaces: list[WorkspaceDto] = []


class WorkspaceUsersApiModel(BaseModel):
    users_ids: list[str] = Field(..., description="workspace users")
