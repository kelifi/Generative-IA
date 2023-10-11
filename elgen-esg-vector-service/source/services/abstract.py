from abc import ABC, abstractmethod
from typing import List

from source.schema.requests import SimilarDocumentsOutput


class VectorStoreService(ABC):

    @abstractmethod
    async def get_similar_documents(self, query: str, n_results: int, workspace_id: str) -> SimilarDocumentsOutput:
        """return paragraphs/documents that are similar to the query"""
        raise NotImplemented("Method should be implemented in the child class")

    @abstractmethod
    async def store_documents(self, texts: List[str]) -> int:
        """Store the documents in the vector DB"""
        raise NotImplemented("Method should be implemented in the child class")
