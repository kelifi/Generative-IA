from pydantic import Field

from source.utils.utils import CamelModel


class IngestedFileOutput(CamelModel):
    file_id: str = Field(description="file id from Common file handler")


class IngestedFilesCountOutput(CamelModel):
    count: int = Field(description="file count in elastic search")
