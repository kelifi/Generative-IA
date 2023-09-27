from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body, Path, Header

from configuration.injection_container import DependencyContainer
from source.schemas.conversation_schema import QuestionInputSchema, QuestionSchema, AnswerResponse
from source.schemas.llm_schema import ExposedModels
from source.services.chat_service import ChatService

chat_router = APIRouter(prefix="/chat")


@chat_router.post(path="/question", response_model=QuestionSchema)
@inject
def create_question(question: QuestionInputSchema = Body(...), conversation_id=Header(alias="conversationId"),
                    chat_service: ChatService = Depends(
                        Provide[DependencyContainer.chat_service])):
    return chat_service.create_question(question=question.question, conversation_id=conversation_id)


@chat_router.get(path="/answer/{question_id}", response_model=AnswerResponse)
@inject
async def get_answer(question_id: UUID = Path(...), user_id: UUID = Header(...),
                     model_name: ExposedModels = Header(..., alias="model-name"),
                     chat_service: ChatService = Depends(
                         Provide[DependencyContainer.chat_service])):
    return await chat_service.answer_question_by_id(user_id=user_id, question_id=question_id, model_name=model_name)
