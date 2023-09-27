from datetime import datetime
from uuid import UUID

from source.exceptions.service_exceptions import DataLayerError, ConversationFetchDataError, ConversationNotFoundError, \
    SourceDocumentsFetchDataError, AnswerNotFoundException
from source.models.conversations_models import Answer
from source.schemas.conversation_schema import QuestionSchema, ChatSchema, SourceSchema
from tests.fixtures import MockRequest
from tests.test_data import question, chat, web_source_summarized_paragraph, \
    source_doc, web_source_doc, prompt_with_web_sources_example, answer_object, mocked_streaming_response_generator, \
    mocked_streaming_response_generator_with_error


class MockResponse:
    def __init__(self, json_data: dict | str | None, text: str | None, status_code: int, content: str | None = None):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text
        self.content = content

    def json(self) -> dict | str | None:
        return self.json_data


def mock_returned_question(self, question_id: UUID) -> QuestionSchema:
    return question


def mock_returned_conversation(self, question_id: UUID) -> ChatSchema:
    return chat


def mock_datalayer_exception(self, answer_id: UUID, rating: str):
    raise DataLayerError


def mock_get_source_documents(self, question_id: UUID):
    return [source_doc, source_doc]


def mock_get_web_sources_by_question_id(self, question_id: UUID):
    return [web_source_doc, web_source_doc]


def mock_fetch_data_error(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise ConversationFetchDataError


def mock_not_found_error(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise ConversationNotFoundError


def mock_src_doc_fetch_error(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise SourceDocumentsFetchDataError


def mock_generate_prompt_with_web_sources(self, chat_history: ChatSchema, source_documents: list[SourceSchema],
                                          web_source_summarized_paragraph: str | None, question: str):
    return prompt_with_web_sources_example


def mock_created_answer(self, question_id: UUID, answer: str):
    return answer_object


def mock_created_answer_wrong_object(self, question_id: UUID, answer: str):
    return {"yes": " wrong"}


def mock_update_answer_with_versioning_from_answer_repository(*args, **kwargs):
    """
    return an answer object
    """

    return Answer(
        **{
            "id": str(kwargs['answer_id']),
            "content": kwargs['content'],
            "creation_date": datetime.now()
        }
    )


def mock_update_answer_with_versioning_from_answer_repository_data_layer_error(*args, **kwargs):
    """
    raise a DataLayerError
    """

    raise DataLayerError


def mock_update_answer_with_versioning_from_answer_repository_answer_not_found(*args, **kwargs):
    """
    raise a DataLayerError
    """

    raise AnswerNotFoundException


def mock_prepare_prompt_args(self, question_id: UUID, model_code: str, use_web_sources_flag: bool):
    return question, chat, [source_doc, source_doc], [web_source_doc, web_source_doc], web_source_summarized_paragraph


def mock_model_service_response_by_streaming(*args, **kwargs):
    mock_request = MockRequest()
    mock_request.data = [dict(chunk) for chunk in mocked_streaming_response_generator]
    return mock_request


def mock_model_service_response_by_streaming_error_during_streaming(*args, **kwargs):
    mock_request = MockRequest()
    mock_request.data = [dict(chunk) for chunk in mocked_streaming_response_generator_with_error]
    return mock_request
