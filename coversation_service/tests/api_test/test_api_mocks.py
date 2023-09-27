from datetime import datetime

from sqlalchemy.exc import NoResultFound

from source.exceptions.service_exceptions import AnswerNotFoundError, ChatServiceError, DatabaseConnectionError, \
    DatabaseIntegrityError, ModelRetrievalError, ModelCreationError, ModelUpdateError
from source.exceptions.validation_exceptions import GenericValidationError
from source.models.conversations_models import Answer
from source.schemas.conversation_schema import AnswerSchema
from source.schemas.models_schema import ModelSchema, ModelOutputSchema
from tests.test_data import model_output_1


def mock_answer_object(*args, **kwargs):
    return AnswerSchema.from_orm(Answer(
        **{
            "id": str(kwargs['answer_id']),
            "content": kwargs['content'],
            "creation_date": datetime.now()
        }
    ))


def mock_answer_not_found_error(*args, **kwargs):
    raise AnswerNotFoundError


def mock_chat_service_error(*args, **kwargs):
    raise ChatServiceError


def raise_model_validation_error(*args, **kwargs):
    raise GenericValidationError(model_name=ModelSchema.__name__)


def raise_model_output_validation_error(*args, **kwargs):
    raise GenericValidationError(model_name=ModelOutputSchema.__name__)


def mock_add_model_error(*args, **kwargs):
    raise ModelCreationError


def mock_get_model_error(*args, **kwargs):
    raise ModelRetrievalError


def mock_patch_model_error(*args, **kwargs):
    raise ModelUpdateError


def mock_no_result_found(*args, **kwargs):
    raise NoResultFound


def mock_model_output(*args, **kwargs):
    return model_output_1


def raise_integrity_error(*args, **kwargs):
    raise DatabaseIntegrityError(
        f'An integrity error happened when creating new model with code: wrong_model_code')
