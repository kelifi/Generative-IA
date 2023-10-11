from tests.test_data import index_deletion_response, vector_store_error, check_in_es_error, ingestion_error, \
    text_retrival_error, schema_error, ingest_index_deletion_error, file_already_ingested


async def mock_ingest_data(*args, **kwargs):
    return None


async def vector_store_fail(*args, **kwargs):
    raise vector_store_error


def mock_check_if_ingested_by_filename_error(*args, **kwargs):
    raise check_in_es_error


def mock_ingestion_error(*args, **kwargs):
    raise ingestion_error


def mock_text_retrival_from_es_error(*args, **kwargs):
    raise text_retrival_error


def mock_schema_error(*args, **kwargs):
    raise schema_error


async def mock_delete_ingest_index(self):
    return index_deletion_response


def mock_ingest_index_deletion_error(*args, **kwargs):
    raise ingest_index_deletion_error


def mock_file_already_exist_error(*args, **kwargs):
    raise file_already_ingested
