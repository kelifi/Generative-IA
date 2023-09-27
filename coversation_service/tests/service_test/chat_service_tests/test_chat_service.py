import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from source.exceptions.service_exceptions import ChatServiceError, ChatIncompleteDataError, \
    ChatAnswerCreationError, AnswerNotFoundError, ConversationFetchDataError
from source.repositories.answer_repository import AnswerRepository
from source.schemas.answer_schema import AnswerRatingResponse
from source.schemas.conversation_schema import AnswerSchema
from source.schemas.streaming_answer_schema import StreamingResponseStatus
from source.services.chat_service import ChatService
from source.services.conversation_service import ConversationService
from source.services.model_service import ModelService
from tests.fixtures import test_chat_service, MockRequest
from tests.service_test.chat_service_tests.chat_service_mocks import mock_datalayer_exception, mock_returned_question, \
    mock_returned_conversation, \
    mock_get_source_documents, mock_get_web_sources_by_question_id, \
    mock_fetch_data_error, mock_not_found_error, mock_src_doc_fetch_error, \
    mock_generate_prompt_with_web_sources, mock_created_answer, \
    mock_update_answer_with_versioning_from_answer_repository, \
    mock_update_answer_with_versioning_from_answer_repository_data_layer_error, \
    mock_update_answer_with_versioning_from_answer_repository_answer_not_found, \
    mock_created_answer_wrong_object, mock_prepare_prompt_args, mock_model_service_response_by_streaming, \
    mock_model_service_response_by_streaming_error_during_streaming
from tests.service_test.model_service_tests.model_service_mocks import mock_request_model_service_per_code
from tests.test_data import chat, web_source_summarized_paragraph, source_doc, prompt_with_web_sources_example, \
    prompt_with_no_web_sources_example, answer_id, \
    question_id, question, web_source_doc, prompt_object, output_answer_example, model_code


def test_generate_prompt_with_web_sources(test_chat_service):
    """Test that the prompt contains source documents, summarized web paragraphs and the question.
    The tests  any indentation!

    Chat history is not used"""
    generated_prompt = test_chat_service._generate_prompt(chat_history=chat,
                                                          source_documents=[source_doc, source_doc],
                                                          web_source_summarized_paragraph=web_source_summarized_paragraph,
                                                          question=question.content)
    assert generated_prompt.replace('\t', '').replace(' ', '') == \
           prompt_with_web_sources_example.replace('\t', '').replace(' ', '')


def test_generate_prompt_with_no_web_sources(test_chat_service):
    """Test that the prompt contains source documents, summarized web paragraphs and the question.
    The tests disregards any indentation and the web sources

    Chat history is not used"""
    generated_prompt = test_chat_service._generate_prompt(chat_history=chat,
                                                          source_documents=[source_doc, source_doc],
                                                          web_source_summarized_paragraph=None,
                                                          question=question.content)
    assert generated_prompt.replace('\t', '').replace(' ', '') == \
           prompt_with_no_web_sources_example.replace('\t', '').replace(' ', '')


def test_set_rating_for_answer(test_chat_service, monkeypatch):
    """Test updating the answer rating in db successfully that is the db call returns 1"""
    monkeypatch.setattr(AnswerRepository, "update_rating_for_answer", lambda self, answer_id, rating: 1)
    assert test_chat_service.set_rating_for_answer(answer_id=answer_id,
                                                   rating="some rating") == AnswerRatingResponse()


def test_set_rating_for_answer_result_zero(test_chat_service, monkeypatch):
    """Test updating the answer rating was not successful when the db call returns 0"""
    monkeypatch.setattr(AnswerRepository, "update_rating_for_answer", lambda self, answer_id, rating: 0)
    with pytest.raises(HTTPException):
        test_chat_service.set_rating_for_answer(answer_id=answer_id, rating="some rating")


def test_set_rating_for_answer_datalayer_exception(test_chat_service, monkeypatch):
    """Test updating the answer rating was not successful due to some DB layer"""
    monkeypatch.setattr(AnswerRepository, "update_rating_for_answer", mock_datalayer_exception)
    with pytest.raises(ChatServiceError):
        test_chat_service.set_rating_for_answer(answer_id=answer_id, rating="some rating")


def test_prepare_prompt_arguments_with_web_sources(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments is successful with web sources included """

    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_returned_question)
    monkeypatch.setattr(ConversationService, "get_conversation_by_question_id", mock_returned_conversation)
    monkeypatch.setattr(ConversationService, "get_source_documents", mock_get_source_documents)
    monkeypatch.setattr(ConversationService, "get_web_sources_by_question_id", mock_get_web_sources_by_question_id)
    monkeypatch.setattr(ModelService, "request_model_service_per_code", mock_request_model_service_per_code)

    question_result, chat_history_result, source_documents_result, web_sources_result, summarized_paragraphs_result = test_chat_service.prepare_prompt_arguments(
        question_id=question_id, model_code=model_code, use_web_sources_flag=True)

    assert question_result == question.content
    assert chat_history_result == chat
    assert source_documents_result == [source_doc, source_doc]
    assert web_sources_result == [web_source_doc, web_source_doc]
    assert summarized_paragraphs_result == web_source_summarized_paragraph + '\n' + web_source_summarized_paragraph


def test_prepare_prompt_arguments_without_web_sources(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_question_by_id fails"""

    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_fetch_data_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_conv_by_quest_id_fetch_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_conversation_by_question_id fails"""
    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_returned_question)
    monkeypatch.setattr(ConversationService, "get_conversation_by_question_id", mock_fetch_data_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_question_by_id_fetch_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_question_by_id fails"""

    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_fetch_data_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_question_by_id_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_conversation_by_question_id fails"""
    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_not_found_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_conv_by_quest_id_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_conversation_by_question_id fails"""
    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_returned_question)
    monkeypatch.setattr(ConversationService, "get_conversation_by_question_id", mock_not_found_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_source_documents_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_source_documents fails"""

    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_returned_question)
    monkeypatch.setattr(ConversationService, "get_conversation_by_question_id", mock_returned_conversation)
    monkeypatch.setattr(ConversationService, "get_source_documents", mock_src_doc_fetch_error)

    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_prepare_prompt_arguments_with_get_web_sources_by_question_id_exception(test_chat_service, monkeypatch):
    """Test if the preparation of the prompt arguments raises a ChatIncompleteDataError when get_web_sources_by_question_id fails"""

    monkeypatch.setattr(ConversationService, "get_question_by_id", mock_returned_question)
    monkeypatch.setattr(ConversationService, "get_conversation_by_question_id", mock_returned_conversation)
    monkeypatch.setattr(ConversationService, "get_source_documents", mock_get_source_documents)
    monkeypatch.setattr(ConversationService, "get_web_sources_by_question_id", mock_src_doc_fetch_error)
    with pytest.raises(ChatIncompleteDataError):
        test_chat_service.prepare_prompt_arguments(question_id=question_id, model_code=model_code,
                                                   use_web_sources_flag=True)


def test_construct_full_prompt(test_chat_service, monkeypatch):
    """Test if the prompt generation returns the right PromptSchema object"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)

    generated_prompt = test_chat_service.construct_full_prompt(question_id=question_id, model_code=model_code,
                                                               use_web_sources_flag=True)

    assert generated_prompt == prompt_object


def test_generate_answer(test_chat_service, monkeypatch):
    """Test if an answer is generated successfully"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code", mock_request_model_service_per_code)
    monkeypatch.setattr(ConversationService, "create_answer", mock_created_answer)

    generated_answer = test_chat_service.generate_answer(question_id=question_id, model_code=model_code,
                                                         use_web_sources_flag=True)

    assert generated_answer == output_answer_example


def test_generate_answer_validation_error_to_creation_error(test_chat_service, monkeypatch):
    """Test if an answer is generated successfully"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code", mock_request_model_service_per_code)
    monkeypatch.setattr(ConversationService, "create_answer", mock_created_answer_wrong_object)

    with pytest.raises(ChatAnswerCreationError):
        test_chat_service.generate_answer(question_id=question_id, model_code=model_code,
                                          use_web_sources_flag=True)


def test_generate_answer_fetch_exception(test_chat_service, monkeypatch):
    """Test if answer saving the answer in the database is handled"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code", mock_request_model_service_per_code)
    monkeypatch.setattr(ConversationService, "create_answer", mock_fetch_data_error)

    with pytest.raises(ChatAnswerCreationError):
        test_chat_service.generate_answer(question_id=question_id, model_code=model_code,
                                          use_web_sources_flag=True)


def test_update_answer_with_versioning_success(test_chat_service, monkeypatch):
    monkeypatch.setattr(AnswerRepository, "update_answer_with_versioning",
                        mock_update_answer_with_versioning_from_answer_repository)
    monkeypatch.setattr(ConversationService, "get_source_documents", mock_get_source_documents)
    monkeypatch.setattr(ConversationService, "get_web_sources_by_question_id",
                        mock_get_web_sources_by_question_id)

    mock_answer_id = uuid4()
    new_content = "updated content!"

    result = test_chat_service.update_answer_with_versioning(answer_id=mock_answer_id, content=new_content)

    assert isinstance(result, AnswerSchema)
    assert result.id == mock_answer_id
    assert result.content == new_content


def test_update_answer_with_versioning_chat_service_error_from_data_layer_error(test_chat_service, monkeypatch):
    monkeypatch.setattr(AnswerRepository, "update_answer_with_versioning",
                        mock_update_answer_with_versioning_from_answer_repository_data_layer_error)

    mock_answer_id = uuid4()
    new_content = "updated content!"

    with pytest.raises(ChatServiceError):
        test_chat_service.update_answer_with_versioning(answer_id=mock_answer_id, content=new_content)


def test_update_answer_with_versioning_chat_service_error_from_fetch_doc_error(test_chat_service, monkeypatch):
    monkeypatch.setattr(AnswerRepository, "update_answer_with_versioning",
                        mock_update_answer_with_versioning_from_answer_repository_data_layer_error)
    monkeypatch.setattr(ConversationService, "get_source_documents", mock_src_doc_fetch_error)

    mock_answer_id = uuid4()
    new_content = "updated content!"

    with pytest.raises(ChatServiceError):
        test_chat_service.update_answer_with_versioning(answer_id=mock_answer_id, content=new_content)


def test_update_answer_with_versioning_chat_service_error_from_answer_not_found(test_chat_service, monkeypatch):
    monkeypatch.setattr(AnswerRepository, "update_answer_with_versioning",
                        mock_update_answer_with_versioning_from_answer_repository_answer_not_found)

    mock_answer_id = uuid4()
    new_content = "updated content!"

    with pytest.raises(AnswerNotFoundError):
        test_chat_service.update_answer_with_versioning(answer_id=mock_answer_id, content=new_content)


@pytest.mark.asyncio
async def test_generate_answer_by_streaming(test_chat_service, monkeypatch):
    """Test if an answer is generated by streaming successfully"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code_by_streaming",
                        mock_model_service_response_by_streaming)
    monkeypatch.setattr(ConversationService, "create_answer", mock_created_answer)

    streaming_generator = test_chat_service.generate_answer_by_streaming(request=MockRequest(), question_id=question_id,
                                                                         model_code=model_code,
                                                                         use_web_sources_flag=True)

    async for chunk in streaming_generator:
        assert chunk


@pytest.mark.asyncio
async def test_generate_answer_by_streaming(test_chat_service, monkeypatch):
    """Test if an answer is generated by streaming successfully"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code_by_streaming",
                        mock_model_service_response_by_streaming)
    monkeypatch.setattr(ConversationService, "create_answer", mock_created_answer)

    streaming_generator = test_chat_service.generate_answer_by_streaming(request=MockRequest(), question_id=question_id,
                                                                         model_code=model_code,
                                                                         use_web_sources_flag=True)

    async for chunk in streaming_generator:
        assert chunk
        assert json.loads(chunk).get("status") in [StreamingResponseStatus.DONE, StreamingResponseStatus.IN_PROGRESS]


@pytest.mark.asyncio
async def test_generate_answer_by_streaming_error_preprocessing(test_chat_service, monkeypatch):
    """Test if an answer is generated by streaming successfully"""

    def bad_error(*args, **kwargs):
        raise ConversationFetchDataError

    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", bad_error)

    streaming_generator = test_chat_service.generate_answer_by_streaming(request=MockRequest(), question_id=question_id,
                                                                         model_code=model_code,
                                                                         use_web_sources_flag=True)

    async for chunk in streaming_generator:
        assert chunk
        assert json.loads(chunk).get("status") == StreamingResponseStatus.ERROR


@pytest.mark.asyncio
async def test_generate_answer_by_streaming_error_during_streaming(test_chat_service, monkeypatch):
    """Test if an answer is generated by streaming successfully"""
    monkeypatch.setattr(ChatService, "prepare_prompt_arguments", mock_prepare_prompt_args)
    monkeypatch.setattr(ChatService, "_generate_prompt", mock_generate_prompt_with_web_sources)
    monkeypatch.setattr(ModelService, "request_model_service_per_code_by_streaming",
                        mock_model_service_response_by_streaming_error_during_streaming)

    streaming_generator = test_chat_service.generate_answer_by_streaming(request=MockRequest(), question_id=question_id,
                                                                         model_code=model_code,
                                                                         use_web_sources_flag=True)

    async for chunk in streaming_generator:
        assert chunk
        assert json.loads(chunk).get("status") in [StreamingResponseStatus.IN_PROGRESS, StreamingResponseStatus.ERROR]
