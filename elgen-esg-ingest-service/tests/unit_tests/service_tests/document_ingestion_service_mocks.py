import requests
from pydantic import ValidationError

from source.schema.elastic_search_schemas import Document
from source.schema.response_schemas import IngestedVectorBatchesCount
from tests.test_data import document_id, text_from_es, clean_text, empty_text, chunked_test_list


class MockResponse:
    """A class used to mock the requests library"""

    def __init__(self, status_code: int, json_data: dict | str | None = None,
                 content: bytes = b'response content') -> None:
        self.json_data = json_data
        self.status_code = status_code
        self.content = content
        self.text = str(content)

    def json(self) -> dict | str | None:
        return self.json_data


def mock_success_request(*args, **kwargs):
    return MockResponse(status_code=requests.codes.OK)


def mock_fail_request(*args, **kwargs):
    return MockResponse(status_code=requests.codes.BAD_REQUEST)


def mock_connection_error(*args, **kwargs):
    raise requests.exceptions.ConnectionError


def mock_send_data_to_vector_response(*args, **kwargs):
    return MockResponse(status_code=requests.codes.OK, json_data={"count": 69})


def mock_checking_file_response_true(*args, **kwargs):
    return MockResponse(status_code=requests.codes.OK, json_data={"hits": {"total": {"value": 5}}})


def mock_checking_file_response_true_wrong_format(*args, **kwargs):
    return MockResponse(status_code=requests.codes.OK, json_data={"value": 5})


def mock_checking_file_response_false(*args, **kwargs):
    return MockResponse(status_code=requests.codes.OK, json_data={"hits": {"total": {"value": 0}}})


def mock_key_error(*args, **kwargs):
    raise KeyError


def mock_ingest_single_document(*args, **kwargs):
    return document_id


def mock_get_text_by_es_id(*args, **kwargs):
    return text_from_es


def mock_non_empty_clean_text(*args, **kwargs):
    return clean_text


def mock_empty_text(*args, **kwargs):
    return empty_text


def mock_chunk_text(*args, **kwargs):
    return chunked_test_list


def mock_batch_count_validation_error(*args, **kwargs):
    raise ValidationError(errors=[], model=IngestedVectorBatchesCount)


def mock_document_validation_error(*args, **kwargs):
    raise ValidationError(errors=[], model=Document)
