import logging

from pydantic.error_wrappers import ValidationError

from source.exceptions.utils_exceptions import ParseError


def log_validation_error(validation_error: ValidationError) -> str:
    """Prettify validation error from pydantic"""
    try:
        return "\n".join([f"Field '{error['loc'][0]}': {error['msg']}" for error in validation_error.errors()])
    except (IndexError, KeyError) as error:
        logging.error(error)
        raise ParseError(detail="unable to parse the error validation error")
