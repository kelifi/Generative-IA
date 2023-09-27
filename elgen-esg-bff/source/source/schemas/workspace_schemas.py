from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceOutput(BaseModel):
    id: UUID = Field(..., description="workspace id")
    workspace_name: str = Field(..., description="workspace name")
    description: str | None = Field(None, description="workspace description")
    active: bool | None = Field(None, description="workspace active or not")


class WorkspaceByUserApiResponseModel(BaseModel):
    workspaces: list[WorkspaceOutput] = Field(default_factory=[], description="a list of WorkspaceOutput objects")
