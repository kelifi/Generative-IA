from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerRatingEnum(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

    def __str__(self):
        return str(self.value)


class AnswerRatingRequest(BaseModel):
    answer_id: UUID = Field(..., description="The id of an answer object", alias='answerId')
    rating: AnswerRatingEnum = Field(..., description="The rating value for a given answer")


class AnswerUpdatingRequest(BaseModel):
    answer_id: UUID = Field(..., description="The id of an answer object", alias='id')
    content: str = Field(..., description="The new content of the answer")


class AnswerRatingResponse(BaseModel):
    detail: str = Field("Rating updated succesfully!", description="A message to be returned for the client")


class VersionedAnswerResponse(BaseModel):
    id_: UUID = Field(..., description="The id of a versioned answer object", alias='id')
    content: str = Field(..., description="The content of the versioned answer")
    rating: str = Field(None, description="The rating of the versioned answer")
    author: str = Field(None, description="The author of of the versioned answer")
    edited: bool | None = Field(None, description="is the versioned answer edited or not, if false, "
                                                  "it means that it was the first ever answer!")
    creation_date: datetime = Field(..., description="creation date information", alias="createdAt")
    update_date: datetime = Field(None, description="update date information", alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
