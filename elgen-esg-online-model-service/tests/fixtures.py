import pytest

from configuration.config import OpenAIConfig
from source.services.model_service import OpenAIService
from fastapi.testclient import TestClient
from typing import Generator
from main import app

@pytest.fixture(scope="module")
def mock_open_ai_service() -> OpenAIService:
    return OpenAIService(OpenAIConfig())


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as client:
        yield client
