from datetime import datetime
from os.path import basename
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ConversationIdSchema(BaseModel):
    id: UUID


class ConversationTitleSchema(BaseModel):
    title: str


class ConversationOutputSchema(ConversationIdSchema, ConversationTitleSchema):
    creation_date: datetime = Field(alias="creationTime")
    update_date: Optional[datetime] = Field(alias="updateTime")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ConversationSchema(ConversationOutputSchema):
    user_id: UUID = Field(alias="userId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class SourceSchema(BaseModel):
    id: UUID
    content: str
    document_path: str = Field(alias="link")
    file_name: Optional[str] = Field(alias="fileName")
    creation_date: datetime = Field(alias="creationTime")
    document_type: str = Field(alias="documentType")
    download_link: Optional[str] = Field(alias="downloadLink")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

    @validator('download_link', always=True)
    def download_link_creation(cls, _, values):
        return f"/source-documents/download-document/{basename(values['document_path'])}"

    @validator('file_name', always=True)
    def extract_file_name(cls, _, values):
        return basename(values['document_path'])


class AnswerSchema(BaseModel):
    id: UUID
    content: str
    creation_date: datetime = Field(alias="creationTime")
    sources: Optional[List[SourceSchema]] = []

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class QuestionSchema(BaseModel):
    id: UUID
    content: str
    creation_date: datetime = Field(alias="creationTime")
    answer: Optional[AnswerSchema]

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class ChatSchema(BaseModel):
    id: UUID
    questions: List[QuestionSchema]


class QuestionInputSchema(BaseModel):
    question: str


class AnswerInputSchema(BaseModel):
    answer: str
    question_id: UUID


class AnswerResponse(BaseModel):
    id: UUID
    answer: AnswerSchema
