from source.exceptions.model_exception_handler import ModelError
from tests.test_data import inference_benchmark_response_200, inference_benchmark_response_500, mock_llm_answer


def mock_inference_context_valid(*args, **kwargs):
    return True


def mock_inference_context_invalid(*args, **kwargs):
    return ModelError(detail="Unable to generate answer!")


def mock_model_answer_200(*args, **kwargs):
    return inference_benchmark_response_200


def mock_model_answer_500(*args, **kwargs):
    return inference_benchmark_response_500


def mock_str_model_answer_200(*args, **kwargs):
    return mock_llm_answer
