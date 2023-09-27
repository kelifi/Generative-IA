from langchain import OpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores.base import VectorStoreRetriever

from configuration.config import app_config
from configuration.logging import logger
from source.helpers.model_loaders import LLMFactory, llm_factory
from source.helpers.vector_stores import vector_retriever_client
from source.schemas.common_schema import LLMResponse, Source
from source.schemas.llm_schema import SupportedLLModels


class LLMInferenceService:
    def __init__(self, model_type: str, model_factory: LLMFactory, vector_retriever: VectorStoreRetriever):
        self.model_type = model_type
        self.model_factory = model_factory
        self.vector_retriever = vector_retriever
        self.model = self.model_factory(self.model_type)
        self.qa = RetrievalQA.from_chain_type(llm=self.model, chain_type="stuff", retriever=self.vector_retriever,
                                              return_source_documents=True)
        self.openai = RetrievalQA.from_chain_type(
            llm=OpenAI(model_name=app_config.OPENAI_MODEL_NAME, openai_api_key=app_config.OPENAI_API_KEY), chain_type="stuff",
            retriever=self.vector_retriever,
            return_source_documents=True)

    async def get_response_from_query(self, query: str, model_name: str) -> LLMResponse:
        logger.info('Generating Response')

        if model_name == SupportedLLModels.open_ai:
            try:
                model_response = await self.openai.acall(inputs={"query": query})
            except Exception as e:
                logger.error(f"Error {e} happened when trying to do the inference using OpenAI")
                model_response = await self.qa.acall(
                    inputs={"query": query}
                )
        else:
            model_response = await self.qa.acall(
                inputs={"query": query}
            )

        answer, docs = model_response['result'], model_response['source_documents']

        return LLMResponse(response=answer,
                           source_documents=[Source(page_content=doc.page_content, source_path=doc.metadata['source'])
                                             for doc in docs])


llm_service = LLMInferenceService(
    model_type=app_config.model_type,
    model_factory=llm_factory,
    vector_retriever=vector_retriever_client
)
