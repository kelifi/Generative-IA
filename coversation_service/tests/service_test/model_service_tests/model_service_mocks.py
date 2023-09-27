from fastapi import status
from pydantic import ValidationError
from requests import RequestException
from sqlalchemy.exc import NoResultFound

from source.exceptions.service_exceptions import DatabaseConnectionError
from source.schemas.models_schema import ModelSchema
from tests.test_data import model_service_answer, model_1_orm, model_2_orm, model_1, model_2


class MockResponse:
    def __init__(self, json_data: dict | str | None, text: str | None, status_code: int, content: str | None = None):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text
        self.content = content

    def json(self) -> dict | str | None:
        return self.json_data


def mock_model_service_request_not_200_response(*args,
                                                **kwargs):  # signature of requests.post method from requests library
    return MockResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, json_data=None, text=None,
                        content=("{\"message\":\"error\""))


def mock_model_service_request_parsing_error(*args, **kwargs):
    return MockResponse(status_code=status.HTTP_200_OK, json_data={"data": "data"}, text=None)


def mock_model_service_request_exception(*args, **kwargs):  # signature of requests.post method from requests library
    raise RequestException


def mock_request_model_service_per_code(*args, **kwargs):
    return model_service_answer


def mock_request_model_service_per_code_dict(*args, **kwargs):
    return model_service_answer.dict()


def mock_get_models(*args, **kwargs):
    return [model_1, model_2]


def mock_get_models_orm(*args, **kwargs):
    return [model_1_orm, model_2_orm]


def mock_model_validation_error(*args, **kwargs):
    """raises a validation error for ModelSchema"""
    raise ValidationError(errors=[], model=ModelSchema)


def mock_no_result_found_error(*args, **kwargs):
    """raises a no result found error"""
    raise NoResultFound


def mock_model_route(*args, **kwargs):
    return "/route"


def mock_model(*args, **kwargs):
    return model_1_orm


def mock_model_output(*args, **kwargs):
    return model_1


def mock_database_conn_error(*args, **kwargs):  # real signature unknown as it can be used in multiple places
    raise DatabaseConnectionError
