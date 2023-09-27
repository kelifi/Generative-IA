import os
from re import search as re_search
from typing import List

import nltk

nltk.download('punkt')

from loguru import logger


def extract_file_and_error(log_entry):
    pattern = r"Error at : `([^`]*)` : `([^`]*)`"
    if match := re_search(pattern, log_entry):
        file_path = match.group(1)
        error_message = match.group(2)
        return file_path, error_message
    else:
        return None, None


def generate_logs_report(log_file_path='logs.log', output_path='log_report.csv'):
    with open(log_file_path, 'r') as f_output, open(output_path, 'a+') as f:
        for line in f:
            f_output.write(line)


def delete_file(file_path: str):
    if os.path.isfile(file_path):
        logger.info(f"delete temporary file {file_path}")
        os.remove(file_path)
    else:
        raise FileNotFoundError


def chunk_text(text: str, chunk_size: int = 250, overlap: int = 50, ignore_token_length: int = 30) -> List[str]:
    """Chunk text in to a list following this strategy:
    - split using double \n as it usually signifies a new paragraph
    - if the paragraph is less than the specified ignore_token_length parameter then we won't consider it
    - if the paragraph is more than the specified chunk_size then truncate it into sub-paragraphs with overlap"""
    chunks = []
    for paragraph in text.split("\n\n"):
        paragraph_tokens = nltk.word_tokenize(paragraph)
        if len(paragraph_tokens) < ignore_token_length:
            pass
        elif len(paragraph_tokens) > chunk_size:
            for i in range(0, len(paragraph_tokens), chunk_size - overlap):
                chunk = " ".join(paragraph_tokens[i:i + chunk_size])  # Join the tokens into a single string
                chunks.append(chunk)
        else:
            chunks.append(paragraph)

    return chunks
