from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field, BaseModel

from source.schemas.conversation_schemas import AnswerSchema
from source.schemas.source_schemas import WebSourceSchema, SourceSchema
from source.utils.utils import CamelModel


class SourceResponse(CamelModel):
    data: list[SourceSchema | WebSourceSchema] = Field(
        description="Source data that can be either local sources of web sources")
    detail: str = Field(
        description="A field containing details on the data usually success if we have data or failed for an empty data list")


class AnswerOutputSchema(CamelModel):
    question_id: UUID = Field(..., description='The question id for the answer output', alias='id')
    answer: AnswerSchema = Field(..., description='The answer for the question identified by the question_id')


class ModelSourcesUpdateSchema(CamelModel):
    code: str = Field(description="The code of the model")
    max_web: int = Field(description="How many web sources to return", ge=0)
    max_doc: int = Field(description="How many document sources to return", ge=0, alias="maxLocal")


class ModelInfoSchema(ModelSourcesUpdateSchema):
    name: str = Field(description="The name of the model")
    available: bool = Field(description="A flag indicating whether the model is available or not")
    default: bool = Field(description="A flag indicating whether this model should be used by default or not")


class ModelPostInfoSchema(ModelInfoSchema):
    route: str = Field(description="The route of the model, that will be used to call the appropriate model service")
    type: str = Field(description="The type of the model")


class ChatModelsOutputSchema(BaseModel):
    models: list[ModelInfoSchema]


class WorkspaceModelsSchema(CamelModel):
    models: list[ModelPostInfoSchema]


class PromptOutputSchema(CamelModel):
    prompt: str = Field(
        description="A full prompt containing the source documents, optionally the summarized web sources and the question")


class ConversationOutputSchema(CamelModel):
    id: UUID = Field(description="id of the conversation")
    title: str = Field(description="title of the conversation")
    creation_date: datetime = Field(alias="creationTime", description="creation time of the conversation")
    update_date: datetime | None = Field(alias="updateTime",
                                         description="when was the last time the conversation was updated")


class ConversationTitleInputSchema(CamelModel):
    title: str = Field(description="title of the conversation")


class ConversationIOutputSchema(CamelModel):
    id: UUID = Field(description="id of the conversation")


class ConversationIdLimitOutputSchema(ConversationIOutputSchema):
    conversations_remaining: int = Field(description="remaining conversations count")


class QuestionInput(CamelModel):
    id: UUID = Field(description="id of the question")
    content: str = Field(description="the question")


class QuestionSchema(QuestionInput):
    creation_date: datetime = Field(description="creation time of the question")
    answer: AnswerSchema | None = Field(description="the complete answer/sources to the question")
    skip_doc: bool = Field(description="a flag to skip the document sources")
    skip_web: bool = Field(description="a flag to skip the web sources")
    local_sources: list[SourceSchema] | None = Field(description="the local document sources", default=None)
    web_sources: list[WebSourceSchema] | None = Field(description="the external web sources", default=None)
    is_specific: bool | None = Field(description="question classification specific or not", default=True)

    class Config:
        allow_population_by_field_name = True


class QuestionLimitOutputSchema(QuestionSchema):
    questions_remaining: int | None = Field(description="number of remaining questions")


class ConversationHistoryOutputSchema(BaseModel):
    id: UUID = Field(description="id of the conversation")
    questions: List[QuestionSchema] = Field(
        description="complete list of questions/answers/sources of the conversation representing the complete history")


class FileNameInputSchema(CamelModel):
    file_name: str = Field(description="file name input")


class SourceContentInputSchema(FileNameInputSchema):
    content: str = Field(description="source input")


class FileInputSchema(CamelModel):
    content: str = Field(..., description="content to highlight in file")
