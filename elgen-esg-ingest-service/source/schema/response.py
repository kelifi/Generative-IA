from typing import Optional, Any, List
from uuid import UUID

from pydantic import BaseModel
from starlette.responses import JSONResponse


class GenericResponse(BaseModel):
    data: Optional[Any] = None
    metadata: Optional[Any] = None
    detail: str = "success"


class SingleSimilarDocumentsResult(BaseModel):
    id: UUID
    text: str
