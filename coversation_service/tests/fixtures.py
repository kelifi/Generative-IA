import json
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from configuration.config import SummarizationConfig, ModelsConfig, StreamingResponseConfig
from main import app
from source.models.common_models import Base
from source.models.model_table import Model_base
from source.repositories.answer_repository import AnswerRepository
from source.repositories.conversation_repository import ConversationRepository
from source.repositories.model_repository import ModelRepository
from source.repositories.workspace_repository import WorkspaceRepository
from source.services.chat_service import ChatService
from source.services.conversation_service import ConversationService
from source.services.model_service import ModelService
from source.services.workspace_service import WorkspaceService
from tests.integration_tests.data_model_mock import create_fresh_database_data


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


@pytest.fixture(scope="module")
def test_chat_service() -> ChatService:
    yield ChatService(
        conversation_service=ConversationService(conversation_repository=None,
                                                 model_discovery_service=ModelService(model_repository=None,
                                                                                      models_config=ModelsConfig()),
                                                 ),
        answer_repository=AnswerRepository(database_helper=None, data_model=None,
                                           versioning_data_model=None),
        model_discovery_service=ModelService(model_repository=None, models_config=ModelsConfig()),
        summarization_config=SummarizationConfig(),
        streaming_response_config=StreamingResponseConfig()
    )


@pytest.fixture(scope="module")
def test_conversation_service():
    yield ConversationService(conversation_repository=ConversationRepository(database_helper=None),
                              model_discovery_service=ModelService(model_repository=None, models_config=ModelsConfig()))


@pytest.fixture(scope="module")
def test_model_service():
    yield ModelService(model_repository=ModelRepository(database_helper=None), models_config=ModelsConfig())


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture(scope="function")
def scope_session():
    # Generate a unique temp db_file to separate sessions, otherwise some tests may try to use other sessions not closed correctly
    db_file = tempfile.mktemp()
    engine = create_engine(f'sqlite:///{db_file}')
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
    Model_base.metadata.create_all(engine, Model_base.metadata.tables.values(), checkfirst=True)
    session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))
    session.add_all(instances=create_fresh_database_data())
    session.commit()
    yield session
    engine.dispose()  # Safely dispose of the engine after each test


@pytest.fixture(scope="module")
def test_workspace_service():
    yield WorkspaceService(workspace_repository=WorkspaceRepository(database_helper=None))
