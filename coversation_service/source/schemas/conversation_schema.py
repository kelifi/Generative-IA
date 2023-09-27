from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator

from configuration.config import question_config
from source.exceptions.validation_exceptions import QuestionLengthExceededError
from source.schemas.answer_schema import AnswerRatingEnum


class ConversationIdSchema(BaseModel):
    id: UUID


class ConversationTitleSchema(BaseModel):
    title: str


class QuestionInputSchema(BaseModel):
    question: str = Field(..., description='The question to be asked in the chat', example='How are you?')

    @validator('question')
    def validate_question_length(cls, question: str) -> str:
        """validate the length of the input question, if it fails raise a QuestionLengthExceededError error!"""
        if len(question) > question_config.QUESTION_LENGTH_LIMIT:
            raise QuestionLengthExceededError(length=question_config.QUESTION_LENGTH_LIMIT)
        return question


class ConversationOutputSchema(ConversationIdSchema, ConversationTitleSchema):
    creation_date: datetime = Field(alias="creationTime")
    update_date: datetime | None = Field(alias="updateTime")
    workspace_id: UUID | str | None = Field(None, alias="workspaceId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ConversationSchema(ConversationOutputSchema):
    user_id: UUID = Field(alias="userId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class SourceSchema(BaseModel):
    id: Optional[UUID]
    content: str
    document_path: Optional[str] = Field(alias="link")
    file_name: Optional[str] = Field(alias="fileName")
    creation_date: Optional[datetime] = Field(alias="creationTime")
    document_type: Optional[str] = Field(alias="documentType")
    document_id: Optional[UUID]= Field(alias="fileId")
    download_link: Optional[str] = Field(alias="downloadLink")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class WebSourceSchema(BaseModel):
    id: Optional[UUID]
    url: str
    description: str
    title: str
    paragraphs: Optional[str]

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class AnswerSchema(BaseModel):
    id: UUID
    content: str
    creation_date: datetime = Field(alias="creationTime")
    update_date: datetime | None = Field(None, alias="updatedAt")
    rating: AnswerRatingEnum | None = None
    edited: bool | None = Field(None, description="is the versioned answer edited or not, if false, "
                                                  "it means that it was the first ever answer!")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class QuestionSchema(BaseModel):
    id: UUID
    content: str
    creation_date: datetime
    answer: Optional[AnswerSchema]
    skip_doc: Optional[bool] = False
    skip_web: Optional[bool] = False
    local_sources: Optional[list[SourceSchema]] = Field(alias="localSources", default=[])
    web_sources: Optional[list[WebSourceSchema]] = Field(alias="webSources", default=[])

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class SourceDocumentsInput(BaseModel):
    similar_docs: List[SourceSchema]


class SourceWebInput(BaseModel):
    web_sources: List[WebSourceSchema]


class ChatSchema(BaseModel):
    id: UUID
    questions: List[QuestionSchema]


class AnswerOutputSchema(BaseModel):
    question_id: UUID = Field(..., description='The question id for the answer output', alias='id')
    answer: AnswerSchema = Field(..., description='The answer')
