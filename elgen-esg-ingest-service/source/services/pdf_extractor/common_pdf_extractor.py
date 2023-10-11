from abc import ABC, abstractmethod

from source.exceptions.common_exceptions import NotImplementedFunction


class CommonPDFExtractor(ABC):

    @staticmethod
    @abstractmethod
    async def extract_text_from_pdf(files_bytes: bytes) -> str:
        raise NotImplementedFunction
