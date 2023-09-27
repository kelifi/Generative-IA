from enum import Enum

from pydantic import Field

from source.utils.utils import CamelModel


class AcknowledgeTypes(str, Enum):
    SUCCESS = 'success'
    FAIL = 'fail'


class AcknowledgeResponse(CamelModel):
    acknowledge: AcknowledgeTypes = Field(default=True, description='The Acknowledge response')
