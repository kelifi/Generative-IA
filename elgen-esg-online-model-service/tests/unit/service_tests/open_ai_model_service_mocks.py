import datetime

from tests.test_data import mock_openapi_response
from requests import RequestException


class MockResponse:
    def __init__(self, json_data: dict | str | None,
                 text: str | None,
                 status_code: int,
                 elapsed: datetime.timedelta):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text
        self.elapsed = elapsed

    def json(self) -> dict | str | None:
        return self.json_data


def mock_openai_api_request(*args, **kwargs):
    return MockResponse(status_code=200, json_data=mock_openapi_response, text=None,
                        elapsed=datetime.timedelta(seconds=0.7))


def mock_openai_api_request_not_200_response(*args, **kwargs):
    return MockResponse(status_code=500, json_data=None, text=None, elapsed=datetime.timedelta(seconds=0.7))


def mock_openai_api_request_exception(*args, **kwargs):
    raise RequestException
