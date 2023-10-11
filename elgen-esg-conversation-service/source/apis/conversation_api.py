from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Path, Depends, status, Body, Header, Query

from configuration.injection_container import DependencyContainer
from source.exceptions.api_exception_handler import ElgenAPIException
from source.exceptions.service_exceptions import ConversationValidationError, ConversationFetchDataError, \
    ConversationNotFoundError, SourceDocumentsFetchDataError, SourceDocumentsValidationError, \
    ModelServiceConnectionError, ChatModelDiscoveryError, ClassificationModelRetrievalError, ResourceOwnershipException
from source.exceptions.validation_exceptions import GenericValidationError
from source.schemas.conversation_schema import ConversationSchema, ConversationIdSchema, ConversationTitleSchema, \
    ConversationOutputSchema, QuestionInputSchema, SourceDocumentsInput, SourceWebInput
from source.services.conversation_service import ConversationService

conversation_router = APIRouter(prefix="/conversations")


@conversation_router.post(path="", response_model=ConversationIdSchema)
@inject
def create_conversation(conversation_title_body: ConversationTitleSchema = Body(...),
                        workspace_id: UUID = Header(..., alias='workspace-id'),
                        user_id: UUID = Header(..., alias='user-id'),
                        conversation_service: ConversationService = Depends(
                            Provide[DependencyContainer.conversation_service])):
    return conversation_service.create_conversation(conversation_title=conversation_title_body.title,
                                                    workspace_id=workspace_id,
                                                    user_id=user_id)


@conversation_router.get(path="/{conversation_id}",
                         description="Get entire conversation history including user queries, model answers and sources")
@inject
def get_conversation(conversation_id: UUID = Path(...),
                     conversation_service: ConversationService = Depends(
                         Provide[DependencyContainer.conversation_service])):
    try:
        return conversation_service.get_conversation_by_id(conversation_id=conversation_id)
    except ConversationFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Cannot connect to database to fetch conversation to details!")
    except ConversationNotFoundError:
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find data for conversation {conversation_id} in internal resources!")
    except ConversationValidationError:
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot validate Schema!")


@conversation_router.delete(path="/{conversation_id}",
                            description="Hard delete a conversation along with its queries, messages and sources",
                            response_model=None)
@inject
def delete_conversation(conversation_id: UUID = Path(...),
                        conversation_service: ConversationService = Depends(
                            Provide[DependencyContainer.conversation_service])) -> None:
    try:
        conversation_service.delete_conversation(conversation_id=conversation_id)
    except ConversationNotFoundError:
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find conversation {conversation_id} to delete!")
    except ConversationFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Database error when trying to delete conversation!")


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
    except ConversationNotFoundError:
        raise ElgenAPIException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find conversation {conversation_id} to update!")
    except ConversationFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Database error when trying to update conversation!")


@conversation_router.get(path="",
                         description="Get all available conversation ids for a certain user and workspace",
                         response_model=list[ConversationOutputSchema])
@inject
def get_available_conversations_per_user(user_id: UUID = Header(..., alias="user-id"),
                                         workspace_id: UUID = Header(..., alias="workspace-id"),
                                         conversation_service: ConversationService = Depends(
                                             Provide[DependencyContainer.conversation_service])):
    try:
        return conversation_service.get_conversations_per_user(user_id=user_id, workspace_id=workspace_id)
    except ConversationFetchDataError as ex:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Cannot fetch conversation for user {user_id}!")
    except ConversationValidationError as ex:
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot validate Schema!")


@conversation_router.post(path="/question")
@inject
async def create_question(question_input: QuestionInputSchema,
                          workspace_id: UUID = Header(...),
                          user_id: UUID = Header(...),
                          conversation_id: UUID = Query(..., alias='conversation-id'),
                          skip_doc: bool = Query(...),
                          skip_web: bool = Query(...),
                          use_classification: bool = Query(True, description="use question-classifer or not"),
                          conversation_service: ConversationService = Depends(
                              Provide[DependencyContainer.conversation_service])):
    """

    :param question_input: The question To be created
    :param use_classification: whether to classify the question or not
    :param conversation_id: The conversation id to which the question is connected
    :param skip_doc: flag if we should skip the source docs
    :param skip_web: flag if we should skip the web sources
    :param workspace_id:
    :param user_id:
    :param conversation_service:
    :return:
    """
    try:
        return await conversation_service.create_question(question=question_input.question,
                                                          conversation_id=conversation_id,
                                                          skip_doc=skip_doc,
                                                          skip_web=skip_web,
                                                          use_classification=use_classification,
                                                          workspace_id=workspace_id,
                                                          user_id=user_id)
    except ResourceOwnershipException as error:
        raise ElgenAPIException(status_code=status.HTTP_403_FORBIDDEN, detail=error.message) from error
    except ModelServiceConnectionError as exc:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message)
    except ConversationFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal error when creating a new question!")
    except ConversationValidationError:
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Failed to parse question schema!")
    except (ChatModelDiscoveryError, ClassificationModelRetrievalError) as error:
        raise ElgenAPIException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail=error.message)

    except GenericValidationError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Could not create the schema for the question")


@conversation_router.post(path="/sources")
@inject
def create_sources(data: SourceDocumentsInput, question_id: UUID,
                   conversation_service: ConversationService = Depends(
                       Provide[DependencyContainer.conversation_service])):
    source_documents = data.similar_docs
    try:
        return conversation_service.create_source_documents(question_id, source_documents)
    except SourceDocumentsFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal error when creating source docs!")
    except SourceDocumentsValidationError:
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Failed to parse Source documents schema!")


@conversation_router.post(path="/web-sources")
@inject
def create_web_sources(question_id: UUID, source_web_input: SourceWebInput = Body(),
                       conversation_service: ConversationService = Depends(
                           Provide[DependencyContainer.conversation_service])):
    web_sources = source_web_input.web_sources
    try:
        return conversation_service.create_web_sources(question_id, web_sources)
    except SourceDocumentsFetchDataError:
        raise ElgenAPIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Internal error when creating source docs!")
    except SourceDocumentsValidationError:
        raise ElgenAPIException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Failed to parse Source documents schema!")
