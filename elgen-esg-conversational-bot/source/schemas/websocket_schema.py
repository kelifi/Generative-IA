from enum import Enum
from typing import Optional

from pydantic import BaseModel


class WebsocketMessageStatus(str, Enum):
    START = 'START'
    END = 'END'
    SENDING = 'SENDING'
    ERROR = 'ERROR'


class WebsocketMessage(BaseModel):
    user_id: str  # for now, it should be string, to not cause issues with langchain streaming
    data: Optional[str] = None
    status: WebsocketMessageStatus
