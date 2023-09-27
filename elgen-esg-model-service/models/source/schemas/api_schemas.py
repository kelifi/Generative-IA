from pydantic import BaseModel, Field


class PromptInputSchema(BaseModel):
    prompt: str = Field(..., description="Prompt to be fed to the model.")

