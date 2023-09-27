from enum import Enum
from json import dumps

from pydantic import BaseModel, Field


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
        return dumps(self.dict())


class ModelStreamingErrorResponse(ModelStreamingResponse):
    status: StreamingResponseStatus = Field(StreamingResponseStatus.ERROR,
                                            description="by default ERROR")