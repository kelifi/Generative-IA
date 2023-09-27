from uuid import UUID

import requests
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Path, Query
from fastapi import Body, HTTPException, status
from loguru import logger
from starlette.requests import Request
from starlette.responses import StreamingResponse

from configuration.injection_container import DependencyContainer
from configuration.logging_setup import logger
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import ChatServiceError, ChatAnswerCreationError, \
    ChatIncompleteDataError, AnswerNotFoundError, VersionedAnswerNotFoundException, ChatModelDiscoveryError
from source.schemas.answer_schema import AnswerRatingRequest, AnswerRatingResponse, AnswerUpdatingRequest, \
    VersionedAnswerResponse
from source.schemas.chat_schema import PromptSchema
from source.schemas.conversation_schema import AnswerSchema
from source.services.chat_service import ChatService

chat_router = APIRouter(prefix="/chat")


@chat_router.get(path="/answer/{question_id}/stream")
@inject
async def create_answer_with_streaming(request: Request,
                                       question_id: UUID = Path(...),
                                       user_id: UUID = Header(..., alias='user-id'),
                                       model_code: str = Header(..., alias='model-code'),
                                       use_web_sources_flag: bool = True,
                                       chat_service: ChatService = Depends(
                                           Provide[DependencyContainer.answer_service])):
    """
    The true endpoint for streaming,
    """
    return StreamingResponse(
        chat_service.generate_answer_by_streaming(request=request,
                                                  question_id=question_id,
                                                  model_code=model_code,
                                                  use_web_sources_flag=use_web_sources_flag
                                                  )
    )


@chat_router.post(path="/answer/{question_id}/stream/test", deprecated=True, description="Used for testing")
@inject
def create_answer_with_streaming_testing(request: Request,
                                         text: str | None = Query("Hello World"),
                                         model_code: str = Header(..., alias='model-code'),
                                         question_id: UUID = Path(...),
                                         chat_service: ChatService = Depends(
                                             Provide[DependencyContainer.answer_service])
                                         ):
    async def get_answer(text):

        service_url = chat_service.model_discovery_service.get_model_per_code(model_code)
        response = requests.post(f"{service_url}/inference/stream", json={"prompt": text}, stream=True)

        if response.status_code == 200:
            # Define the chunk size (the number of bytes to read at a time)
            chunk_size = 1024 * 4

            counter = 0
            for chunk in response.iter_content(chunk_size=chunk_size):

                counter += 1
                is_disconnected = await request.is_disconnected()
                logger.info(f"Is disconnected {is_disconnected} : {counter}")
                if is_disconnected:
                    logger.info("Connection disconnected, end streaming!")
                    break
                yield chunk
        else:
            yield str({"detail": f"Request failed with status code {response.status_code}", "status": "ERROR"})

    return StreamingResponse(get_answer(text), media_type="text/event-stream")


@chat_router.get(path="/answer/{question_id}")
@inject
def create_answer(question_id: UUID = Path(...),
                  user_id: UUID = Header(..., alias='user-id'),
                  model_code: str = Header(..., alias='model-code'),
                  use_web_sources_flag: bool = True,
                  chat_service: ChatService = Depends(
                      Provide[DependencyContainer.answer_service])
                  ):
    try:
        return chat_service.generate_answer(question_id=question_id, model_code=model_code,
                                            use_web_sources_flag=use_web_sources_flag)
    except (ChatAnswerCreationError, ChatIncompleteDataError) as error:
        logger.error(error)
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot create answer!")
    except ChatModelDiscoveryError:
        raise ElgenAPIException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail=f"The model service corresponding to code {model_code} is not registered or unavailable")


@chat_router.put(path="/answer/rating")
@inject
async def update_rating_for_answer(
        user_id: UUID = Header(..., alias='user-id'),
        request_body: AnswerRatingRequest = Body(...),
        chat_service: ChatService = Depends(
            Provide[DependencyContainer.answer_service])
) -> AnswerRatingResponse:
    """
    Endpoint for creating rating for an answer
    """
    try:
        return chat_service.set_rating_for_answer(answer_id=request_body.answer_id,
                                                  rating=request_body.rating)
    except ChatServiceError as error:
        raise HTTPException(detail=str(error), status_code=500) from error


@chat_router.get(path="/prompt/{question_id}", response_model=PromptSchema,
                 description="Generate the full prompt that is later passed to the model")
@inject
def create_prompt(question_id: UUID = Path(...),
                  user_id: UUID = Header(..., alias='user-id'),
                  model_code: str = Header(..., alias='model-code'),
                  use_web_sources_flag: bool = Query(default=True),
                  chat_service: ChatService = Depends(
                      Provide[DependencyContainer.answer_service])
                  ):
    try:
        return chat_service.construct_full_prompt(question_id=question_id, model_code=model_code,
                                                  use_web_sources_flag=use_web_sources_flag)
    except ChatIncompleteDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot create prompt!")
    except ChatModelDiscoveryError:
        raise ElgenAPIException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail=f"The model service corresponding to code {model_code} is not registered or unavailable")


@chat_router.put(path="/answer")
@inject
async def update_answer_content(
        user_id: UUID = Header(..., alias='user-id'),
        request_body: AnswerUpdatingRequest = Body(...),
        chat_service: ChatService = Depends(
            Provide[DependencyContainer.answer_service])
) -> AnswerSchema:
    """
    Endpoint for updating an answer with new content and saving the old content too (versioning)
    """
    try:
        return chat_service.update_answer_with_versioning(answer_id=request_body.answer_id,
                                                          content=request_body.content)
    except AnswerNotFoundError as error:
        raise ElgenAPIException(detail="Answer not found!", status_code=status.HTTP_404_NOT_FOUND) from error

    except ChatServiceError as error:
        raise ElgenAPIException(detail="Unexpected Error!",
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from error


@chat_router.get(path="/answer/{answer_id}/history/latest")
@inject
async def get_latest_versioned_answer(
        user_id: UUID = Header(..., alias='user-id'),
        answer_id: UUID = Path(...),
        chat_service: ChatService = Depends(
            Provide[DependencyContainer.answer_service])
) -> VersionedAnswerResponse:
    """
    Endpoint for getting the latest version of an answer before the current one
    """
    try:
        return chat_service.get_last_versioned_answer(answer_id=answer_id)
    except VersionedAnswerNotFoundException as error:
        raise ElgenAPIException(detail="This answer has no older versions",
                                status_code=status.HTTP_404_NOT_FOUND) from error
    except ChatServiceError as error:
        raise ElgenAPIException(detail="Unexpected Error!",
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from error
