from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from source.schemas.models_schema import ModelServiceAnswer


class QueryDepth(str, Enum):
    """
    Used to determine the step at which to stop the Full SQL chain
    """
    COMMAND = "sqlCommand"
    RESULT = "sqlResult"
    EXPLANATION = "sqlExplanation"


class SqlSourceResponseDTO(BaseModel):
    id: UUID
    question_id: UUID
    query: str = Field(..., description="save the generated sql query")
    result: str = Field(None, description="save the result of sql query execution")
    model_answer: ModelServiceAnswer | None = Field(None,
                                                    description="response of sql llm model")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class SqlExecuteRequest(BaseModel):
    url: str | None = Field(description="the source url")
    query: str | None = Field(description="the query to execute")


class SqlExecuteResponse(BaseModel):
    result: str | None = Field(description="the result of the query")
