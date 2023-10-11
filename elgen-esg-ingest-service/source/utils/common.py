import logging

from nostril import nonsense

from source.schema.elastic_search_schemas import Document


def divide_into_batches(documents_list: list[Document], batch_size: int) -> list[list[Document]]:
    """Divide documents into batches of documents"""
    logging.info("Divide documents into batches")
    return [documents_list[i:i + batch_size] for i in range(0, len(documents_list), batch_size)]


def clean_non_sense_text(text: str) -> str:
    """Clean text that is deemed worthy"""
    clean_text_list = []
    for sub_text in text.split('.'):
        try:
            if not nonsense(sub_text):
                clean_text_list.append(sub_text)
        except ValueError:
            pass

    return '. '.join(clean_text_list).replace('\n', ' ').replace('  ', ' ')
