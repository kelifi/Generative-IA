from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChromaDBSimilarDocumentsResponse(BaseModel):
    """

    Note: why list of list? because the chroma similar doc feat can be used with multiple queries at the same time!

    example:
    {'ids': [['c42245f4-a593-46d3-94d2-1b86b8df4877', '6b605c7d-9cfb-454e-a1ee-d00d0a15c884',
              '972a5963-55dc-4148-886c-93cdd94aff7d', '4984a2ce-3035-4f33-b725-20bb079d5d1d']], 'embeddings': None,
     'documents': [[
       'The grand symphony hall was filled with anticipation as the conductor raised the baton.',
       'The evening sky was adorned with a tapestry of stars, twinkling brightly against the dark canvas.',
       'As the train pulled into the station, a bustling crowd of commuters hurriedly.',
       'The scent of pine trees filled the forest, as hikers embarked on a journey of exploration and adventure.']],
     'metadatas': None, 'distances': None}
    """
    ids: List[List[UUID]]
    documents: List[List[str]]
    metadatas: Optional[List[List[dict]]] = None
    distances: Optional[List[List[float]]] = None
