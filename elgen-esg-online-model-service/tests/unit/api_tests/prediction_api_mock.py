from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper

from source.exceptions.model_exception_handler import PredictionError
from source.schemas.model_answer_schema import ModelAnswer
from tests.test_data import inference_benchmark_response_200, mock_llm_answer


def mock_inference_context_valid(*args, **kwargs):
    return True


def mock_inference_context_invalid(*args, **kwargs):
    return PredictionError


def mock_model_answer_200(*args, **kwargs):
    return inference_benchmark_response_200


def mock_prediction_error(*args, **kwargs):
    raise PredictionError(detail="Internal_error!")


def mock_validation_error(*args, **kwargs):
    raise ValidationError(
        [
            ErrorWrapper(ValueError('Wrong car error 1.'), '/cars'),
            ErrorWrapper(ValueError('Wrong car error 2.'), '/cars')
        ],
        ModelAnswer
    )


def mock_str_model_answer_200(*args, **kwargs):
    return mock_llm_answer
