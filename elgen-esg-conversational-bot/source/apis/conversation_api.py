from typing import List
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Path, Depends, status, Body, Header
from sqlalchemy.exc import NoResultFound

from configuration.injection_container import DependencyContainer
from source.exceptions.api_exception_handler import ElgenAPIException
from source.schemas.conversation_schema import ConversationSchema, ConversationIdSchema, ConversationTitleSchema, \
    ConversationOutputSchema
from source.services.conversation_service import ConversationService

conversation_router = APIRouter(prefix="/conversations")


@conversation_router.post(path="", response_model=ConversationIdSchema)
@inject
def create_conversation(conversation_title_body: ConversationTitleSchema = Body(...),
                        user_id: UUID = Header(..., alias="userId"),
                        conversation_service: ConversationService = Depends(
                            Provide[DependencyContainer.conversation_service])):
    return conversation_service.create_conversation(conversation_title=conversation_title_body.title,
                                                    user_id=user_id)


@conversation_router.get(path="/{conversation_id}",
                         description="Get entire conversation history including user queries, model answers and sources")
@inject
def get_conversation(conversation_id: UUID = Path(...),
                     conversation_service: ConversationService = Depends(
                         Provide[DependencyContainer.conversation_service])):
    return conversation_service.get_conversation_by_id(conversation_id=conversation_id)


@conversation_router.delete(path="/{conversation_id}",
                            description="Hard delete a conversation along with its queries, messages and sources",
                            response_model=None)
@inject
def delete_conversation(conversation_id: UUID = Path(...),
                        conversation_service: ConversationService = Depends(
                            Provide[DependencyContainer.conversation_service])) -> None:
    try:
        conversation_service.delete_conversation(conversation_id=conversation_id)
    except NoResultFound:
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find conversation to delete!")


@conversation_router.put(path="/{conversation_id}",
                         description="Update a conversation's title",
                         response_model=ConversationSchema)
@inject
def update_conversation(new_conversation_title_body: ConversationTitleSchema = Body(...),
                        conversation_id: UUID = Path(...),
                        conversation_service: ConversationService = Depends(
                            Provide[DependencyContainer.conversation_service])) -> ConversationSchema:
    try:
        return conversation_service.update_conversation_title(new_conversation_title=new_conversation_title_body.title,
                                                              conversation_id=conversation_id)
    except NoResultFound:
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find conversation to update!")


@conversation_router.get(path="",
                         description="Get all available conversation ids for a certain user",
                         response_model=List[ConversationOutputSchema])
@inject
def get_available_conversations_per_user(user_id: UUID = Header(..., alias="userId"),
                                         conversation_service: ConversationService = Depends(
                                             Provide[DependencyContainer.conversation_service])):
    return conversation_service.get_conversations_per_user(user_id=user_id)
