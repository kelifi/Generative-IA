from pydantic import BaseModel
from source.models.db_models import SourceDocument

class SourceDocumentOutputSchema(BaseModel):
    text: str
    document_path: str


    class Config:
        orm_mode = True
        orm_model = SourceDocument # this can be set to the class of ORM model
