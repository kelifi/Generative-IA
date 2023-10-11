from pydantic import BaseModel, Field


class GenericResponse(BaseModel):
    detail: str = Field(description="a brief detail of the response")


class IngestedVectorBatchesCount(BaseModel):
    count: str = Field(description="Count of batches ingested into the vector service")
