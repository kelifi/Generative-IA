from typing import Optional, List

from pydantic import BaseModel, Field


class SingleStoreDocumentRequest(BaseModel):
    document: str
    vector: Optional[List[float]] = None
    metadata: Optional[dict] = None


class StoreDocumentsRequest(BaseModel):
    data: List[SingleStoreDocumentRequest] = Field(...,
                                                   description="list of documents to store",
                                                   example=[
                                                       {
                                                           "document": "The sky was painted with vibrant hues of orange and pink as the sun began to set.",
                                                           "metadata": {
                                                               "file_name": "nature_article.pdf",
                                                               "file_id": "1001",
                                                               "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                                               "es_id": "es_001"
                                                           }
                                                       },
                                                       {
                                                           "document": "The bustling city streets were filled with the sound of honking cars and people rushing by.",
                                                           "metadata": {
                                                               "file_name": "urban_blog.pdf",
                                                               "file_id": "1002",
                                                               "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                                                               "es_id": "es_002"
                                                           }
                                                       },
                                                       {
                                                           "document": "In the quiet forest, the leaves rustled gently with the whisper of the wind.",
                                                           "metadata": {
                                                               "file_name": "nature_podcast.pdf",
                                                               "file_id": "1003",
                                                               "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
                                                               "es_id": "es_003"
                                                           }
                                                       },
                                                       {
                                                           "document": "The aroma of freshly brewed coffee filled the cozy café, inviting customers to savor its rich flavor.",
                                                           "metadata": {
                                                               "file_name": "coffee_magazine.pdf",
                                                               "file_id": "1004",
                                                               "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa9",
                                                               "es_id": "es_004"
                                                           }
                                                       },
                                                       {
                                                           "document": "As the waves crashed against the shore, a sense of tranquility washed over the beachgoers.",
                                                           "metadata": {
                                                               "file_name": "coastal_blog.pdf",
                                                               "file_id": "1005",
                                                               "workspace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa5",
                                                               "es_id": "es_005"
                                                           }
                                                       }
                                                   ]
                                                   )


class GetSimilarDocumentsRequest(BaseModel):
    query: str = Field(...,
                       description="the query string with which we will match similar docs",
                       example="Hello World!"
                       )
    n_results: int = Field(..., description="max number of similar documents results", example=4)

    workspace_id: str | None = Field(default=None, description="workspace of the user",
                                     example='3fa85f64-5717-4562-b3fc-2c963f66afa6')


class SimilarDocumentsOutput(BaseModel):
    data: List[dict]
    detail: str | None
