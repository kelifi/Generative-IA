from enum import Enum
from json import dumps
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from source.schemas.conversation_schema import AnswerOutputSchema
from source.schemas.models_schema import ModelServiceAnswer


class StreamingResponseStatus(str, Enum):
    """
    Used when developing streaming features
    """
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"
    DONE = "DONE"


class ModelStreamingResponse(BaseModel):
    """
    Standard response to be sent for any streaming feature
    """
    status: StreamingResponseStatus = Field(..., description="status of this response chunk")
    detail: str | None = Field(None, description="a message telling more information about this chunk")

    def __str__(self) -> str:
        """
        Use this to convert your pydantic model to a dict and then to a string
        pydantic -> dict -> str
        :return:
        """
        return dumps(jsonable_encoder(self.dict()))


class ModelStreamingInProgressResponse(ModelStreamingResponse):
    status: StreamingResponseStatus = Field(StreamingResponseStatus.IN_PROGRESS,
                                            description="by default IN_PROGRESS")
    data: str = Field(..., description="contains the streamed token")


class ModelStreamingDoneResponse(ModelStreamingResponse):
    status: StreamingResponseStatus = Field(StreamingResponseStatus.DONE,
                                            description="by default DONE")
    data: ModelServiceAnswer = Field(...,
                                     description="contains the entire response + metadata")


class ModelStreamingErrorResponse(ModelStreamingResponse):
    status: StreamingResponseStatus = Field(StreamingResponseStatus.ERROR,
                                            description="by default ERROR")


class ConversationStreamingDoneResponse(ModelStreamingResponse):
    status: StreamingResponseStatus = Field(StreamingResponseStatus.DONE,
                                            description="by default DONE")
    data: AnswerOutputSchema = Field(...,
                                     description="contains the entire response + metadata")