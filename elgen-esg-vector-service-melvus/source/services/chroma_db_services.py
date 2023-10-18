from uuid import uuid4

from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError

from source.exceptions.service_exceptions import InternalError, MaxResultValueException
from source.repositories.collections import VectorCollection
from source.schema.data import ChromaDBSimilarDocumentsResponse
from source.schema.requests import StoreDocumentsRequest
from source.schema.response import SingleSimilarDocumentsResult, SimilarDocumentsResponse, GenericResponse, \
    TotalDocumentsCountResponse
from source.services.abstract import VectorStoreService


class ChromaDBVectorService(VectorStoreService):

    def __init__(self, collection: VectorCollection):
        self.collection = collection

    async def store_documents(self, store_request: StoreDocumentsRequest) -> GenericResponse:

        if not store_request.data:
            raise HTTPException(detail="Empty document list!", status_code=400)

        texts = [doc.document for doc in store_request.data]

        ids = [str(uuid4()) for _ in range(len(store_request.data))]

        metadatas = [doc.metadata for doc in store_request.data]

        logger.info(f"len metadata {len(metadatas)}")

        self.collection.add_documents(ids=ids, documents=texts, metadatas=metadatas)

        return GenericResponse(**{"detail": "ok"})

    async def get_similar_documents(self, query: str, n_result: int):
        total_count = len(self.collection)

        if n_result > total_count:
            error_message = f"Number of requested results {n_result} is greater " \
                            f"than number of elements in index {total_count}"
            logger.error(error_message)
            raise MaxResultValueException(error_message)

        result = self.collection.get_similar_documents_by_text(n_results=n_result, query_texts=[query])

        try:
            # validate that the chroma response schema is correct
            result = ChromaDBSimilarDocumentsResponse(**result)
        except ValidationError as error:
            logger.error("This error may indicate a change in schema from chroma db!")
            logger.error(error)
            raise InternalError("Internal Error!") from error

        if not result.ids[0]:
            raise HTTPException(detail="No similar documents were found", status_code=404)

        data = [
            SingleSimilarDocumentsResult(id=doc_id, text=text, source=metadata.get('source')) for doc_id, text, metadata in
            zip(result.ids[0],
                result.documents[0],
                result.metadatas[0]
                )
        ]

        detail_message = (
            "Retrieved similar documents with success!"
            if data
            else "No documents found!"
        )

        return SimilarDocumentsResponse(data=data,
                                        detail=detail_message,
                                        metadata={"total_count": total_count, "n_results": n_result, "query": query}
                                        )

    async def get_total_documents_count(self) -> TotalDocumentsCountResponse:
        count = len(self.collection)
        return TotalDocumentsCountResponse(
            data={"count": count
                  },
            detail="success!" if count else "db is empty!"
        )
