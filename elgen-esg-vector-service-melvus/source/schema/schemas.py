from pydantic import BaseModel


class SourceData(BaseModel):
    text: str
    source_file: str
