import os
from re import search as re_search

from configuration.logging import logger


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
