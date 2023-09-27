import pytest

from source.exceptions.model_exception_handler import ModelLoadError, PromptError
from tests.fixtures import llm_factory_huggingface_test, llm_factory_huggingface_with_4bit_quantization_test
from tests.test_data import short_prompt, mock_llm_answer, mock_generate_answer_response_llm
from tests.unittests.service_tests.offline_model_service_mocks import mock_pipeline_call, \
    MockAutoModel, \
    MockTokenizer


def test_predict(llm_factory_huggingface_test, monkeypatch):
    """
    test predicting answer
    """
    monkeypatch.setattr(llm_factory_huggingface_test,
                        'inference_pipeline', mock_pipeline_call)
    assert llm_factory_huggingface_test.predict(
        prompt=short_prompt) == mock_llm_answer


def test_predict_no_model(llm_factory_huggingface_test):
    """
    test if ModelLoadError is handled
    """
    with pytest.raises(ModelLoadError):
        llm_factory_huggingface_test.predict(prompt=short_prompt)


def test_generate_answer(llm_factory_huggingface_test, monkeypatch):
    """
    test generating answer
    """
    monkeypatch.setattr(llm_factory_huggingface_test,
                        'inference_pipeline', mock_pipeline_call)
    llm_answer = llm_factory_huggingface_test.generate_answer(
        prompt=short_prompt)
    assert llm_answer.response == mock_generate_answer_response_llm.response
    assert llm_answer.prompt_length == mock_generate_answer_response_llm.prompt_length
    assert llm_answer.inference_time > 0
    assert llm_answer.model_name == mock_generate_answer_response_llm.model_name


def test_generate_answer_prompt_too_long_error(llm_factory_huggingface_test, monkeypatch):
    """
    test having too long prompt
    """
    def mock_encode_very_long_sequence(*args, **kwargs):
        return [210] * 10000

    monkeypatch.setattr(MockTokenizer, "encode", mock_encode_very_long_sequence)

    with pytest.raises(PromptError):
        llm_factory_huggingface_test.generate_answer(prompt=short_prompt * 10000)


def test_generate_answer_no_model(llm_factory_huggingface_test):
    """
    test if ModelLoadError is handled
    """
    with pytest.raises(ModelLoadError):
        llm_factory_huggingface_test.generate_answer(prompt=short_prompt)


def test_get_metadata(llm_factory_huggingface_test):
    """
    test returning correctly the metadata
    """
    metadata = llm_factory_huggingface_test.get_metadata()
    assert metadata["load_in_8bit"] != None
    assert metadata["load_in_4bit"] != None
    assert metadata["max_new_tokens"] > 0
    assert metadata["no_repeat_ngram_size"] >= 0
    assert metadata["repetition_penalty"] >= 1.0


def test_load_without_4bit_quantization(llm_factory_huggingface_test, monkeypatch):
    """
    test loading the model without enabling the 4bit quantization
    """
    monkeypatch.setattr(llm_factory_huggingface_test.model_class, 'from_pretrained',
                        MockAutoModel.from_pretrained)
    model = llm_factory_huggingface_test.load()

    assert model is not None


def test_load_with_4bit_quantization(llm_factory_huggingface_with_4bit_quantization_test, monkeypatch):
    """
    test loading the model with enabling the 4bit quantization
    """
    monkeypatch.setattr(llm_factory_huggingface_with_4bit_quantization_test.model_class, 'from_pretrained',
                        MockAutoModel.from_pretrained)
    model = llm_factory_huggingface_with_4bit_quantization_test.load()

    assert model is not None
