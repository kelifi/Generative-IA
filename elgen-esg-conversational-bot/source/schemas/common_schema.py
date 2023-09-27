import time
from datetime import datetime
from enum import Enum
from typing import List
from typing import Optional

from pydantic import BaseModel, Field


class AppEnv(str, Enum):
    dev = "dev"
    prod = "prod"


class LLMQueryRequestModel(BaseModel):
    query: str


class Source(BaseModel):
    page_content: str
    source_path: str


class LLMResponse(BaseModel):
    response: str
    source_documents: List[Source]


class ReportDataModel(BaseModel):
    data: Optional[dict] = Field(
        None, description="the model related data the original data extracted from the model", example="{}"
    )


class ReportModel(ReportDataModel):
    user_id: Optional[str] = Field(
        None, description="the user id ", example="test"
    )
    report_id: Optional[str] = Field(
        None, description="the report id", example="test"
    )
    saving_date: Optional[datetime] = Field(datetime.fromtimestamp(time.time(), None))
