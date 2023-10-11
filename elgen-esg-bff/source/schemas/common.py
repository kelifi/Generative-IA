from enum import Enum
from uuid import UUID

from pydantic import Field

from source.utils.utils import CamelModel


class AcknowledgeTypes(str, Enum):
    SUCCESS = 'success'
    FAIL = 'fail'


class AcknowledgeResponse(CamelModel):
    acknowledge: AcknowledgeTypes = Field(default=True, description='The Acknowledge response')


class QueryDepth(str, Enum):
    """
    Used to determine the step at which to stop the Full SQL chain
    """
    COMMAND = "sqlCommand"
    RESULT = "sqlResult"
    EXPLANATION = "sqlExplanation"


class UpdateStatusDataModel(CamelModel):
    id: UUID = Field(..., description="id", example='d391c642-563c-11ee-8c99-0242ac120002')
    updated: bool = Field(..., description="Status of the update")
