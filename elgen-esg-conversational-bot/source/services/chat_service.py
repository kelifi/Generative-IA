from uuid import UUID

from source.helpers.context_helpers import user_id_var
from source.repositories.answer_repository import AnswerRepository
from source.repositories.question_repository import QuestionRepository
from source.schemas.common_schema import LLMResponse
from source.schemas.conversation_schema import QuestionSchema, AnswerSchema, SourceSchema, AnswerResponse
from source.services.inference_services import llm_service, LLMInferenceService


class ChatService:
    def __init__(self, question_repository: QuestionRepository, answer_repository: AnswerRepository):
        self.question_repository = question_repository
        self.answer_repository = answer_repository
        self.llm_service: LLMInferenceService = llm_service

    def create_question(self, question: str, conversation_id: UUID) -> QuestionSchema:
        return QuestionSchema.from_orm(
            self.question_repository.create_question(question=question, conversation_id=conversation_id))

    def get_question(self, question_id: UUID) -> QuestionSchema:
        return QuestionSchema.from_orm(self.question_repository.get_question_by_id(question_id=question_id))

    def create_answer(self, data: LLMResponse, question_id) -> AnswerResponse:
        answer_orm = self.answer_repository.create_answer(answer=data.response, question_id=question_id)
        sources = []
        for source_document in data.source_documents:
            source_document_schema = self.source_schema(answer_orm, source_document)
            if source_document_schema not in sources:
                sources.append(source_document_schema)

        answer = AnswerSchema.from_orm(answer_orm)
        answer.sources = sources
        return AnswerResponse(id=question_id, answer=answer)

    async def answer_question_by_id(self, question_id: UUID, user_id: UUID, model_name: str):
        question = self.get_question(question_id=question_id).content

        user_id_var.set(str(user_id))

        model_response = await self.llm_service.get_response_from_query(query=question, model_name=model_name)

        return self.create_answer(data=model_response, question_id=question_id)

    def source_schema(self, answer_orm, source_document):
        return SourceSchema.from_orm(
            self.answer_repository.create_source_document(answer_id=answer_orm.id,
                                                          document_path=source_document.source_path,
                                                          content=source_document.page_content,
                                                          document_type='pdf'))
