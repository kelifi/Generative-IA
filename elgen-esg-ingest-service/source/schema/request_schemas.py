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
                                                               "source": "Nature Magazine"
                                                           }
                                                       },
                                                       {
                                                           "document": "The bustling city streets were filled with the sound of honking cars and people rushing by.",
                                                           "metadata": {
                                                               "source": "Urban Living Blog"
                                                           }
                                                       },
                                                       {
                                                           "document": "In the quiet forest, the leaves rustled gently with the whisper of the wind.",
                                                           "metadata": {
                                                               "source": "Nature Sounds Podcast"
                                                           }
                                                       },
                                                       {
                                                           "document": "The aroma of freshly brewed coffee filled the cozy café, inviting customers to savor its rich flavor.",
                                                           "metadata": {
                                                               "source": "Coffee Connoisseur Magazine"
                                                           }
                                                       },
                                                       {
                                                           "document": "As the waves crashed against the shore, a sense of tranquility washed over the beachgoers.",
                                                           "metadata": {
                                                               "source": "Coastal Travel Blog"
                                                           }
                                                       }
                                                   ]
                                                   )
