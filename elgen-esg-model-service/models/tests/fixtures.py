from typing import Generator

import pytest
from fastapi.testclient import TestClient

from configuration.config import OfflineServiceConfig
from main import app
from source.services.model_service import LLMFactoryHuggingFace
from tests.test_data import offline_model_name, model_directory
from tests.unittests.service_tests.offline_model_service_mocks import MockTokenizer, MockAutoModel


@pytest.fixture(scope="module")
def llm_factory_huggingface_test() -> LLMFactoryHuggingFace:
    config = OfflineServiceConfig()
    config.FOUR_BIT_LLM_QUANTIZATION = False
    return LLMFactoryHuggingFace(model_name=offline_model_name, model_directory=model_directory,
                                 model_class=MockAutoModel,
                                 tokenizer_class=MockTokenizer, config=OfflineServiceConfig())


@pytest.fixture(scope="module")
def llm_factory_huggingface_with_4bit_quantization_test() -> LLMFactoryHuggingFace:
    config = OfflineServiceConfig()
    config.FOUR_BIT_LLM_QUANTIZATION = True
    return LLMFactoryHuggingFace(model_name=offline_model_name, model_directory=model_directory,
                                 model_class=MockAutoModel,
                                 tokenizer_class=MockTokenizer, config=OfflineServiceConfig())


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as client:
        yield client
