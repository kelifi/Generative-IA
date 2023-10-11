from datetime import datetime
from uuid import UUID

from pydantic import Field

from source.schemas.answer_schemas import AnswerRatingEnum
from source.utils.utils import CamelModel


class AnswerSchema(CamelModel):
    id: UUID = Field(description="id of the answer")
    content: str = Field(description="the answer")
    creation_date: datetime = Field(alias="creationTime", description="creation date of the answer")
    updated_at: datetime = Field(None, description="creation date of the answer")
    rating: AnswerRatingEnum | None = Field(description="rating of the answer")
    edited: bool | None = Field(None, description="is the versioned answer edited or not, if false, "
                                                  "it means that it was the first ever answer!")

    class Config:
        allow_population_by_field_name = True


class QuestionInputSchema(CamelModel):
    question: str = Field(..., description='The question to be asked in the chat', example='How are you?')
