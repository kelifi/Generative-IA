from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ModelNamesChoice(BaseModel):
    label: str = Field(..., description='The name of the model')
    loaded: bool | None = Field(True, description='Is the model enabled or not')


class OpenAIRoles(str, Enum):
    SYSTEM = 'system'
    USER = 'user'


class OpenAIRoleSchema(BaseModel):
    role: OpenAIRoles = Field(..., description='The message role')
    content: str = Field(..., description='The instruction prompt')


class OpenAIDataSchema(BaseModel):
    model: str = Field(..., description='The model name to be called')
    messages: List[OpenAIRoleSchema] = Field(..., description='The content for each role fo the chat')
