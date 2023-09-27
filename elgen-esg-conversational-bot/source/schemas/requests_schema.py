from uuid import UUID

from pydantic import BaseModel


class AnswerQuestionRequestBody(BaseModel):
    conversation_id: UUID
    query: str
