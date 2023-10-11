from uuid import UUID

from pydantic import BaseModel, Field


class ChatSuggestion(BaseModel):
    id: UUID = Field(..., description="Chat suggestion id", example='d391c642-563c-11ee-8c99-0242ac120002')
    content: str = Field(..., description="Suggested question", )
    available: bool = Field(..., description="setted for activated suggested question")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class WorkspaceChatSuggestions(BaseModel):
    suggestions: list[ChatSuggestion] = Field([], description="List of suggested questions for the workspace")
