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
                                                               "es_id": "es_001"
                                                           }
                                                       },
                                                       {
                                                           "document": "The bustling city streets were filled with the sound of honking cars and people rushing by.",
                                                           "metadata": {
                                                               "file_name": "urban_blog.pdf",
                                                               "file_id": "1002",
                                                               "es_id": "es_002"
                                                           }
                                                       },
                                                       {
                                                           "document": "In the quiet forest, the leaves rustled gently with the whisper of the wind.",
                                                           "metadata": {
                                                               "file_name": "nature_podcast.pdf",
                                                               "file_id": "1003",
                                                               "es_id": "es_003"
                                                           }
                                                       },
                                                       {
                                                           "document": "The aroma of freshly brewed coffee filled the cozy café, inviting customers to savor its rich flavor.",
                                                           "metadata": {
                                                               "file_name": "coffee_magazine.pdf",
                                                               "file_id": "1004",
                                                               "es_id": "es_004"
                                                           }
                                                       },
                                                       {
                                                           "document": "As the waves crashed against the shore, a sense of tranquility washed over the beachgoers.",
                                                           "metadata": {
                                                               "file_name": "coastal_blog.pdf",
                                                               "file_id": "1005",
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


class SimilarDocumentsOutput(BaseModel):
    data: List[dict]
    detail: str | None
