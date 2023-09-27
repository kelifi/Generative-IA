from abc import ABC, abstractmethod
from typing import List


class VectorStoreService(ABC):

    @abstractmethod
    async def get_similar_documents(self, query: str, n_results: int):
        pass

    @abstractmethod
    async def store_documents(self, texts: List[str]):
        pass
