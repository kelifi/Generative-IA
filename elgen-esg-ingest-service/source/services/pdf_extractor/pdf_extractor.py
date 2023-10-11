from io import BytesIO

import fitz

from source.services.pdf_extractor.common_pdf_extractor import CommonPDFExtractor


class PDFExtractor(CommonPDFExtractor):

    @staticmethod
    def extract_text_from_pdf(files_bytes: bytes) -> str:
        with fitz.open(stream=files_bytes) as pdf:
            full_text = ""
            for page_number in range(pdf.page_count):
                full_text += pdf[page_number].get_textpage().extractText()
            return full_text
