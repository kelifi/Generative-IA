from pydantic import BaseModel, Field


class SingleWebSourceSchema(BaseModel):
    url: str
    description: str
    title: str
    paragraphs: str


class PromptSchema(BaseModel):
    prompt: str = Field(
        description="A full prompt containing the source documents, optionally the summarized web sources and the question")


class QuestionPurposeResponse(BaseModel):
    is_specific: bool = Field(description="the field to confirm if a question is specific or not", )
