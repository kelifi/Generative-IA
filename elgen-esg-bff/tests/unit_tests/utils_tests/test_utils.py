import mimetypes

import pytest

from source.exceptions.custom_exceptions import FileTypeExtractionError
from source.utils.utils import guess_and_extract_content_type


def test_guess_and_extract_content_type():
    """test if the mimetype is correct then we can extract it correctly"""
    assert guess_and_extract_content_type(file_name="test.docx") == (
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'vnd.openxmlformats-officedocument.wordprocessingml.document')


def test_guess_and_extract_content_type_could_not_guess_error():
    """test if the mimetype was not guessed correctly and it returns none type it is handled"""
    with pytest.raises(FileTypeExtractionError):
        guess_and_extract_content_type(file_name="file_name_with_no extension")


def test_guess_and_extract_content_type_could_wrong_guess_error(monkeypatch):
    """test if the mimetype was not guessed correctly, and it returns something not in the format of
     "application/* then it is handled"""
    monkeypatch.setattr(mimetypes, 'guess_type', lambda x: ("pdf" , None))
    with pytest.raises(FileTypeExtractionError):
        guess_and_extract_content_type(file_name="file_name_with_no extension")
