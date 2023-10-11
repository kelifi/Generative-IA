import json
from datetime import datetime
from uuid import uuid4

import pytest
import requests
from httpx import AsyncClient
from pydantic import ValidationError

from source.exceptions.commons import NotOkServiceResponse
from source.exceptions.custom_exceptions import ModelConfigError
from source.schemas.answer_schemas import AnswerUpdatingRequest, VersionedAnswerResponse
from source.schemas.api_schemas import QuestionLimitOutputSchema
from source.schemas.common import QueryDepth
from source.schemas.conversation_schemas import AnswerSchema, QuestionInputSchema
from source.schemas.source_schemas import SourceLimitSchema
from source.schemas.streaming_answer_schema import ModelStreamingErrorResponse
from source.services import chats_service
from source.services.keycloak_service import KeycloakService
from tests.conftest import test_chat_service, MockRequest
from tests.test_data import sources_limit_dict_list, user_id, mock_add_question_return_object


@pytest.mark.asyncio
async def test_update_answer_with_versioning_success(test_chat_service, mocker):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    request_body = AnswerUpdatingRequest(content="new content!")

    mocked_load_pickled_object = mocker.patch('source.services.chats_service.make_request',
                                              return_value=AnswerSchema(
                                                  **{
                                                      "id": answer_id,
                                                      "content": request_body.content,
                                                      "creation_date": datetime.now()
                                                  }
                                              ))

    result = await test_chat_service.update_answer_with_versioning(user_id=user_id,
                                                                   answer_id=answer_id,
                                                                   update_answer_request=request_body)

    assert mocked_load_pickled_object.call_count == 1
    assert str(result.id) == answer_id


@pytest.mark.asyncio
async def test_update_answer_with_versioning_not_ok_response(test_chat_service, mocker):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    request_body = AnswerUpdatingRequest(content="new content!")

    mocked_load_pickled_object = mocker.patch('source.services.chats_service.make_request',
                                              return_value=NotOkServiceResponse(
                                                  content=json.dumps({"detail": "Answer Not Found!"}),
                                                  status_code=404)
                                              )

    result = await test_chat_service.update_answer_with_versioning(user_id=user_id,
                                                                   answer_id=answer_id,
                                                                   update_answer_request=request_body)

    assert mocked_load_pickled_object.call_count == 1
    assert result.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_versioned_answer_success(test_chat_service, mocker):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    mock_versioned_answer = VersionedAnswerResponse(
        **{
            "id": answer_id,
            "content": "old content",
            "createdAt": datetime.now()
        }
    )

    mocked_load_pickled_object = mocker.patch('source.services.chats_service.make_request',
                                              return_value=mock_versioned_answer)

    result = await test_chat_service.get_latest_versioned_answer(user_id=user_id, answer_id=answer_id)

    assert mocked_load_pickled_object.call_count == 1
    assert str(result.id_) == answer_id


@pytest.mark.asyncio
async def test_get_latest_versioned_answer_not_ok_response(test_chat_service, mocker):
    user_id = str(uuid4())
    answer_id = str(uuid4())
    request_body = AnswerUpdatingRequest(content="new content!")

    mocked_load_pickled_object = mocker.patch('source.services.chats_service.make_request',
                                              return_value=NotOkServiceResponse(
                                                  content=json.dumps({"detail": "Internal Error!"}),
                                                  status_code=500)
                                              )

    result = await test_chat_service.update_answer_with_versioning(user_id=user_id,
                                                                   answer_id=answer_id,
                                                                   update_answer_request=request_body)

    assert mocked_load_pickled_object.call_count == 1
    assert result.status_code == 500


@pytest.mark.asyncio
async def test_extract_config_per_model(test_chat_service, monkeypatch):
    """test extract_config_per_model"""

    async def mock_get_sources_configurations(*args, **kwargs):
        return sources_limit_dict_list

    monkeypatch.setattr(KeycloakService, "get_sources_configurations", mock_get_sources_configurations)
    result = await test_chat_service._extract_config_per_model(model_code="M1")
    assert result == sources_limit_dict_list[1]


@pytest.mark.asyncio
async def test_get_model_config_per_model_code(test_chat_service, monkeypatch):
    """test get_model_config_per_model_code"""

    async def mock_get_model_source_information(*args, **kwargs):
        return {"code": "M1", "max_doc": 1, "max_web": 2}

    monkeypatch.setattr(chats_service, "make_request", mock_get_model_source_information)
    result = await test_chat_service.get_model_config_per_model_code(model_code="M1")
    assert result == SourceLimitSchema(modelCode="M1", maxWeb=2, maxLocal=1)


@pytest.mark.asyncio
async def test_get_model_config_per_model_code_validation_error(test_chat_service, monkeypatch):
    """test if get_model_config_per_model_code handles validation errors"""

    def mock_validation_error(*args, **kwargs):
        raise ValidationError(errors=[], model=SourceLimitSchema)

    async def mock_get_model_source_information(*args, **kwargs):
        return {"code": "M1", "max_doc": 1, "max_local": 2}

    monkeypatch.setattr(chats_service, "make_request", mock_get_model_source_information)
    monkeypatch.setattr(SourceLimitSchema, "__init__", mock_validation_error)
    with pytest.raises(ModelConfigError):
        await test_chat_service.get_model_config_per_model_code(model_code="M1")


@pytest.mark.asyncio
async def test_streaming_response_success(test_chat_service, monkeypatch):
    monkeypatch.setattr(AsyncClient, "stream", MockRequest)

    result = test_chat_service.generate_answer_by_streaming(request=MockRequest(),
                                                            user_id=str(uuid4()),
                                                            question_id=str(uuid4()),
                                                            model_code="M1",
                                                            workspace_type="database",
                                                            workspace_id=str(uuid4()),
                                                            query_depth=QueryDepth.EXPLANATION
                                                            )
    assert result
    async for chunk in result:
        assert chunk


@pytest.mark.asyncio
async def test_streaming_response_error(test_chat_service, monkeypatch):
    def error_from_conversation(*args, **kwargs):
        return MockRequest(status_code=500)

    monkeypatch.setattr(AsyncClient, "stream", error_from_conversation)

    result = test_chat_service.generate_answer_by_streaming(request=MockRequest(),
                                                            user_id=str(uuid4()),
                                                            question_id=str(uuid4()),
                                                            model_code="M1",
                                                            workspace_type="database",
                                                            workspace_id=str(uuid4()),
                                                            query_depth=QueryDepth.EXPLANATION
                                                            )
    async for chunk in result:
        assert json.loads(chunk).get("status") == "ERROR"


@pytest.mark.asyncio
async def test_add_question(test_chat_service, mocker):
    """test add question service"""

    mocked_added_question = mocker.patch('source.services.chats_service.make_request',
                                              return_value=mock_add_question_return_object
                                              )
    result = await test_chat_service.add_question(user_id=user_id,
                                                  conversation_id="221ff523-3774-44ab-9c37-bd0f2d72243f",
                                                  workspace_id=uuid4(),
                                                  question=QuestionInputSchema(question="this is a question"),
                                                  skip_doc=False,
                                                  skip_web=False,
                                                  use_classification=True
                                                  )
    assert mocked_added_question.call_count == 1
    assert result == QuestionLimitOutputSchema(**mock_add_question_return_object)
    assert result.skip_web is False
