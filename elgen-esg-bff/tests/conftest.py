import json

import pytest
from fastapi import Header
from fastapi.testclient import TestClient

from app import app
from configuration.config import KeyCloakServiceConfiguration, BFFSettings
from source.apis.chats_router import get_workspace_type
from source.schemas.workspace_schemas import WorkspaceTypesEnum
from source.services.chats_service import ChatService
from source.services.keycloak_service import KeycloakService
from source.services.sources_service import SourceService


class MockRequest:
    """
    Use it to mock starlette request object used by Fastapi under the hood
    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        self.status_code = kwargs.get("status_code") or 200
        self.data = [
            {"data": "word1"},
            {"data": "word2"},
            {"data": "word3"}
        ]

    async def is_disconnected(self, *args, **kwargs):
        return False

    def iter_content(self, *args, **kwargs):
        for chunk in self.data:
            yield json.dumps(chunk)

    async def aiter_bytes(self, *args, **kwargs):
        for chunk in self.data:
            yield json.dumps(chunk)

    async def __aenter__(self, *args, **kwargs):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass


@pytest.fixture(scope="module")
def test_keycloak_service():
    yield KeycloakService(keycloak_service_configuration=KeyCloakServiceConfiguration().dict())


@pytest.fixture(scope="session")
def test_chat_service():
    yield ChatService(config={}, keycloak_service=KeycloakService(
        keycloak_service_configuration=KeyCloakServiceConfiguration().dict()))


@pytest.fixture(scope="session")
def test_client():
    def mock_get_workspace_type(workspace_id=Header(..., alias="workspace-id")):
        return WorkspaceTypesEnum.chat

    app.dependency_overrides[get_workspace_type] = mock_get_workspace_type
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_source_service():
    yield SourceService(config=BFFSettings().dict())
