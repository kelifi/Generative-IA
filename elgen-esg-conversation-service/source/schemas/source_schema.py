from uuid import UUID

from pydantic import BaseModel, Field


class SourceTypeModel(BaseModel):
    id: UUID = Field(..., description="Source id", example='d391c642-563c-11ee-8c99-0242ac120002')
    name: str = Field(..., description="Source name", )
    description: str = Field(..., description="description of the Source")
    available: bool = Field(..., description="setted for activated Source")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class SourceTypeOutputModel(BaseModel):
    data: list[SourceTypeModel]


class NewSourceSchema(BaseModel):
    """Source pydantic schema"""
    url: str = Field(description="The Source URL, e.g. DB connection url")
    description: str | None = Field(description="The source description")
    category: str | None = Field(description="The source category, e.g postgres")
    source_type: str | None = Field(description="The source type, e.g Database source")
    workspace_id: UUID | None = Field(description="The Workspace ID that uses this source")
    user_id: UUID | str | None = Field(description="The user id that added the source")
    source_metadata: dict | None = Field(default_factory=dict, description="Any other metadata related to the source")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class NewSourceOutput(NewSourceSchema):
    id: UUID = Field(description="The Source id")


class SourceOutputModel(BaseModel):
    id: UUID = Field(description="The Source id")
    url: str = Field(description="The Source URL, e.g. DB connection url")
    description: str | None = Field(description="The source description")
    category: str | None = Field(description="The source category, e.g postgres")


class SourceDDLOutputDTO(SourceOutputModel):
    metadata: str = Field(description="The Source DDL, e.g. DB connection url")
