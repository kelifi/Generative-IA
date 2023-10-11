from datetime import datetime
from os.path import basename
from uuid import UUID

from pydantic import Field, validator

from source.utils.utils import CamelModel


class SourceSchema(CamelModel):
    id: UUID | None = Field(description="id of source schema")
    content: str = Field(description="the source paragraph")
    document_path: str | None = Field(alias="link", description="path to the source document")
    document_id: UUID | None = Field(description="The document file handler id", alias="fileId")
    file_name: str | None = Field(description="the file name containing the extension")
    creation_date: datetime | None = Field(description="the creation date of the source")
    document_type: str | None = Field(description="the type of the document")
    download_link: str | None = Field(description="the full download link for the document source")

    class Config:
        allow_population_by_field_name = True

    @validator('download_link', always=True)
    @classmethod
    def download_link_creation(cls, _, values: dict) -> str:
        """create the download link for the file"""
        return f"/sources/v1/download/{values.get('document_id')}"

    @validator('file_name', always=True)
    @classmethod
    def extract_file_name(cls, _, values: dict) -> str:
        """extract the file name from the document path"""
        return basename(values.get('document_path'))


class WebSourceSchema(CamelModel):
    id: UUID | None = Field(description="the id of the web source")
    url: str = Field(description="the url of the web source")
    description: str = Field(description="a brief description on the website")
    title: str = Field(description="the title of the page")


class SourceLimitSchema(CamelModel):
    model_code: str = Field(description="a code identifying a model")
    max_web: int = Field(description="the limit to how many web sources you can include", ge=0)
    max_local: int = Field(description="the limit to how many local sources you can include", ge=0)


class SourceTypeSchema(CamelModel):
    id: str = Field(..., description="source id")
    name: str = Field(..., description="source name")
    description: str = Field(..., description="description of the source")
    available: bool = Field(..., description="setted for activated source")


class SourceTypeOutputSchema(CamelModel):
    data: list[SourceTypeSchema] = Field(..., description="Schema of Source type output")


class SourceVerificationInput(CamelModel):
    url: str = Field(description="The Source URL, e.g. DB connection url")
    category: str | None = Field(description="The source type, e.g postgres")
    source_type: str | None = Field(description="The source type, e.g Database source", alias="type")
    description: str | None = Field(description="description of the source")


class SourceInput(SourceVerificationInput):
    user_id: str | None = Field(description="The user id that added the source")
    source_metadata: dict | None = Field(default_factory=dict, description="Any other metadata related to the source")
    workspace_id: UUID | None = Field(description="The Workspace ID that uses this source")


class SourceOutput(SourceInput):
    id: str | None = Field(description="The source ID")


class ColumnInfo(CamelModel):
    name: str
    description: str


class TableInfo(CamelModel):
    name: str
    columns: list[ColumnInfo]


class DatabaseFieldsMapping(CamelModel):
    tables: list[TableInfo]


class SourceDataInput(SourceVerificationInput):
    id: str | None = Field(description="The source ID")


class SourceDataOutput(SourceDataInput):
    mapping: DatabaseFieldsMapping | None


class SourceVerificationOutput(CamelModel):
    details: str = Field(default='success')


class SourceOutputModel(CamelModel):
    id: UUID = Field(description="The Source id")
    url: str = Field(description="The Source URL, e.g. DB connection url")
    description: str | None = Field(description="The source description")
    category: str | None = Field(description="The source category, e.g postgres")
