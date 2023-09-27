import json
import logging
from uuid import UUID

import requests
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Header, Body, Depends, Path, Query, Security, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError

from configuration.config import BFFSettings
from configuration.injection import InjectionContainer
from source.exceptions.api_exceptions import QuestionsLimitApiException, \
    KeycloakInternalApiException
from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import SchemaError, UserInformationFormatError
from source.schemas.answer_schemas import AnswerRatingRequest, AnswerRatingResponse, AnswerUpdatingRequest, \
    VersionedAnswerResponse
from source.schemas.api_schemas import AnswerOutputSchema, ModelInfoSchema, SourceResponse, PromptOutputSchema, \
    QuestionLimitOutputSchema, QuestionInput, ModelPostInfoSchema, ModelSourcesUpdateSchema
from source.schemas.conversation_schemas import QuestionInputSchema, AnswerSchema
from source.schemas.keycloak_schemas import KeycloakAttribute, ClientRole
from source.services.chats_service import ChatService
from source.services.keycloak_service import KeycloakService

chats_router = APIRouter(prefix="/chat")
security = HTTPBearer()


@chats_router.post("/question", response_model=QuestionLimitOutputSchema)
@inject
async def add_question(
        conversation_id: str = Header(..., alias="conversation-id"),
        skip_doc: bool = Query(..., alias="skipDoc"),
        skip_web: bool = Query(..., alias="skipWeb"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        question: QuestionInputSchema = Body(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])):
    """
    create question
    :param conversation_id:
    :param skip_doc:
    :param skip_web:
    :param credentials:
    :param keycloak_service:
    :param question:
    :param chat_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    if not await keycloak_service.check_user_limit(user_id=user_id,
                                                   attribute_to_check=KeycloakAttribute.QUESTIONS):
        raise QuestionsLimitApiException
    try:
        created_question = await chat_service.add_question(user_id=user_id,
                                                           conversation_id=conversation_id,
                                                           question=question,
                                                           skip_doc=skip_doc,
                                                           skip_web=skip_web)
        if isinstance(created_question, NotOkServiceResponse):
            return created_question
        updated_rate_limit = await keycloak_service.update_rate_limit(user_id, KeycloakAttribute.QUESTIONS)
        return QuestionLimitOutputSchema(**created_question.dict(),
                                         questions_remaining=int(
                                             updated_rate_limit.user_actual_limits.questions_limit[0]))
    except (UserInformationFormatError, IndexError, ValidationError):
        logging.error("error getting questions limit")
        raise KeycloakInternalApiException


@chats_router.get("/answer/{question_id}/stream")
@inject
async def get_answer_by_streaming(
        request: Request,
        text: str = Query(...),
        model_code: str = Header(..., alias="model-code"),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        question_id: str = Path(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
) -> StreamingResponse:
    """
    Stream the answer to a user's question asynchronously.
       Args:
           request (Request): The FastAPI request object.
           text (str): The text of the user's question.
           model_code (str): The code of the model to use.
           credentials (HTTPAuthorizationCredentials): The user's authorization credentials.
           keycloak_service (KeycloakService): Keycloak service for authentication.
           question_id (str): The identifier of the user's question.
           chat_service (ChatService): Chat service for generating the answer.
       Returns:
           StreamingResponse: A streaming response with the answer in text/event-stream format.
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return StreamingResponse(
        chat_service.generate_answer_by_streaming(text, request=request, user_id=user_id, model_code=model_code,
                                                  question_id=question_id),
        media_type="text/event-stream")


@chats_router.get("/answer/{question_id}", response_model=AnswerOutputSchema)
@inject
async def get_answer(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        model_code: str = Header(..., alias="model-code"),
        question_id: str = Path(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    """
    get the user's
    :param credentials:
    :param keycloak_service:
    :param model_code: the model code to use later on
    :param question_id:
    :param chat_service:
    :return:
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    try:
        return await chat_service.get_answer(user_id=user_id, model_code=model_code, question_id=question_id)
    except HTTPException as http_exception:
        logging.error("error getting the answer for that question !")
        if http_exception.status_code == status.HTTP_504_GATEWAY_TIMEOUT:
            updated_user_data = await keycloak_service.update_rate_limit(user_id=user_id,
                                                                         attribute_to_update=KeycloakAttribute.QUESTIONS,
                                                                         incrementation_condition=True)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    'error': 'This request has timed out and has been cancelled, please retry.',
                    'actualQuestionsNumber': updated_user_data.user_actual_limits.questions_limit[0]
                }
            )
        raise http_exception


@chats_router.get("/models", response_model=list[ModelInfoSchema])
@inject
async def get_available_models(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    _ = await keycloak_service.check_auth(credentials)
    return await chat_service.get_chat_models()


@chats_router.post("/source-doc", response_model=SourceResponse)
@inject
async def get_source_documents(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        question: QuestionInput = Body(...),
        model_code: str = Header(description="The model code to use later on with the web sources",
                                 alias="model-code"),
        local_sources_count: int | None = Query(
            description="the count of local sources to fetch, if this param is not set then it will be set to the value "
                        "specified in keycloak for the provided model name", ge=0, default=None,
            alias="localSourcesCount"),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    try:
        return await chat_service.get_source_docs(user_id=user_id, question=question, model_code=model_code,
                                                  local_sources_count=local_sources_count)
    except SchemaError:
        logging.error("unexpected error occurred when getting documents source")
        raise HTTPException(status_code=500, detail="Unexpected error")


@chats_router.post("/source-web", response_model=SourceResponse)
@inject
async def get_source_from_web(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        question: QuestionInput = Body(...),
        model_code: str = Header(description="The model code to use later on with the web sources",
                                 alias="model-code"),
        web_sources_count: int | None = Query(
            description="the count of web sources to fetch, if this param is not set then it will be set to the value "
                        "specified in keycloak for the provided model name",
            ge=0, default=None,
            alias="webSourcesCount"),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    try:
        return await chat_service.get_web_source(user_id=user_id, question=question, model_code=model_code,
                                                 web_sources_count=web_sources_count)
    except SchemaError:
        logging.error("unexpected error occurred when getting web source")
        raise HTTPException(status_code=status.s, detail="Unexpected error")


@chats_router.get("/prompt/{question_id}", response_model=PromptOutputSchema)
@inject
async def create_prompt(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        model_code: str = Header(..., alias="model_code"),
        question_id: UUID = Path(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await chat_service.create_prompt(user_id=user_id, model_code=model_code, question_id=question_id)


@chats_router.put(path="/answer/rating", response_model=AnswerRatingResponse)
@inject
async def create_rating_for_answer(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        request_body: AnswerRatingRequest = Body(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])):
    """
    Creates a rating for an answer provided by the chat service.

    Args:
        credentials (HTTPAuthorizationCredentials): The HTTP Authorization credentials.
        keycloak_service (KeycloakService): The instance of KeycloakService for authentication.
        request_body (AnswerRatingRequest): The request body containing the rating information.
        chat_service (ChatService): The instance of the ChatService used to create the rating.

    Returns:
        AnswerRatingResponse: The response from the chat service indicating the success of the rating creation.
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = str(payload.dict().get("sub"))
    return await chat_service.create_rating_for_answer(user_id, request_body)


@chats_router.put(path="/answer/{answer_id}")
@inject
async def update_answer_with_versioning(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        request_body: AnswerUpdatingRequest = Body(...),
        answer_id: UUID = Path(..., description="The id of an answer object"),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])) -> AnswerSchema:
    """
    Endpoint for updating an answer with new content and versioning the older version
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = payload.dict().get("sub")

    return await chat_service.update_answer_with_versioning(update_answer_request=request_body,
                                                            answer_id=answer_id,
                                                            user_id=user_id,
                                                            )


@chats_router.get(path="/answer/{answer_id}/history/latest")
@inject
async def get_latest_versioned_answer(
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        answer_id: UUID = Path(...),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])) \
        -> VersionedAnswerResponse:
    """
    Endpoint for retrieving the latest oldest version of a given answer
    """
    payload = await keycloak_service.check_auth(credentials)
    user_id = payload.dict().get("sub")

    return await chat_service.get_latest_versioned_answer(answer_id=answer_id, user_id=user_id)


@chats_router.post("/models", response_model=ModelInfoSchema, description="Add a Model to the database")
@inject
async def add_new_model(
        model_info_input: ModelPostInfoSchema = Body(),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await chat_service.add_model(model_info_input=model_info_input)


@chats_router.patch("/models", response_model=ModelInfoSchema)
@inject
async def patch_existing_model(
        model_info_input: ModelSourcesUpdateSchema = Body(),
        credentials: HTTPAuthorizationCredentials = Security(security),
        keycloak_service: KeycloakService = Depends(Provide[InjectionContainer.keycloak_service]),
        chat_service: ChatService = Depends(Provide[InjectionContainer.chat_service])
):
    payload = await keycloak_service.check_auth(credentials)
    keycloak_service.check_user_role(payload, [ClientRole.SUPER_ADMIN])
    return await chat_service.patch_model(model_info_input=model_info_input)
