from typing import Optional, Any, List
from uuid import UUID

from pydantic import BaseModel


class GenericResponse(BaseModel):
    data: Optional[Any] = None
    metadata: Optional[Any] = None
    detail: str = "success"


class SingleSimilarDocumentsResult(BaseModel):
    id: UUID
    text: str
    source: Optional[str] = None


class SimilarDocumentsResponse(GenericResponse):
    data: List[SingleSimilarDocumentsResult]


class DocumentCountResult(BaseModel):
    count: int


class TotalDocumentsCountResponse(GenericResponse):
    data: DocumentCountResult
