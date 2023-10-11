import re

from tests.fixtures import test_pdf_extractor
from tests.test_data import pdf_content, expected_text


def test_extract_text_from_pdf(test_pdf_extractor):
    """Test extraction of test from pdf via pdfplumber"""
    extracted_text = test_pdf_extractor.extract_text_from_pdf(
        files_bytes=pdf_content)
    assert ' '.join(extracted_text.split()) == ' '.join(expected_text.split())