import os.path
from os.path import isfile
from pathlib import Path

import pytest

from configuration.config import ElasticSearchConfig
from source.exceptions.service_exceptions import VectorApiError, CheckError, FileIngestionError, TextRetrievalError, \
    SchemaValidationError, IngestionDeletionError, FileAlreadyIngestedError
from source.schema.elastic_search_schemas import IngestionDelSchema, Document
from source.schema.request_schemas import SingleStoreDocumentRequest, StoreDocumentsRequest
from source.schema.response_schemas import GenericResponse, IngestedVectorBatchesCount

current_path = str(Path(__file__).resolve().parent)
ingestion_response_mock = GenericResponse(detail="File was ingested, chunked and sent to vector service")
file_id = "82d2a87b-f279-4193-9a72-ef672526e5be"
document_id = "82d2a87b-f279-4193-9a72-ef672526e5ca"
workspace_id = 'd875d722-be7e-48bb-89f1-d78960224eea'

test_pdf_file_path = os.path.join(current_path, "test.pdf")
if not isfile(test_pdf_file_path):
    raise pytest.fail("pdf test file was not found")

_files = {"file": (
    "test.pdf", open(test_pdf_file_path, "rb"),
    "application/pdf")}

index_deletion_response = IngestionDelSchema(
    detail=f"Ingest Index named {ElasticSearchConfig().INGESTION_INDEX} deleted successfully!")

ingested_data_count = IngestedVectorBatchesCount(count=69)
dto_vector_service = StoreDocumentsRequest(data=[
    SingleStoreDocumentRequest(document="doc1", vector=[0.1, 0.2, 0.3], metadata={"source": "web", "language": "en"}),
    SingleStoreDocumentRequest(document="doc2", vector=[0.21, 0.12, 0.33],
                               metadata={"source": "doc", "language": "fr"})])

text_from_es = "This is a large corpus of text that was ingested in ES"
clean_text = "This text was the large corpus taken from es and cleaned"
empty_text = ""
cleaned_document_from_es = Document(page_content=clean_text,
                                    metadata={"file_name": "file_name.pdf", "file_id": file_id, "es_id": document_id,
                                              'workspace_id': 'd875d722-be7e-48bb-89f1-d78960224eea'})
chunked_test_list = ["chunk 1", "chunk 2"]
documents_list = [cleaned_document_from_es, cleaned_document_from_es]
processed_documents_list = [Document(page_content=chunked_test_list[0],
                                     metadata={"file_name": "file_name.pdf", "file_id": file_id, "es_id": document_id,
                                               'workspace_id': 'd875d722-be7e-48bb-89f1-d78960224eea'}),
                            Document(page_content=chunked_test_list[1],
                                     metadata={"file_name": "file_name.pdf", "file_id": file_id, "es_id": document_id,
                                               'workspace_id': 'd875d722-be7e-48bb-89f1-d78960224eea'}),
                            Document(page_content=chunked_test_list[0],
                                     metadata={"file_name": "file_name.pdf", "file_id": file_id, "es_id": document_id,
                                               'workspace_id': 'd875d722-be7e-48bb-89f1-d78960224eea'}),
                            Document(page_content=chunked_test_list[1],
                                     metadata={"file_name": "file_name.pdf", "file_id": file_id, "es_id": document_id,
                                               'workspace_id': 'd875d722-be7e-48bb-89f1-d78960224eea'})
                            ]

# Errors
vector_store_error = VectorApiError(detail="storing in vector store failed!")
check_in_es_error = CheckError()  # can be raised with multiple messages
ingestion_error = FileIngestionError()  # can be raised with multiple messages
text_retrival_error = TextRetrievalError()  # can be raised with multiple messages
schema_error = SchemaValidationError(detail="an error has occurred when creating the ingest input schema")
ingest_index_deletion_error = IngestionDeletionError()  # can be raised with multiple messages
file_already_ingested = FileAlreadyIngestedError()

with open(os.path.join(current_path, "onepage.pdf"), 'rb') as pdf_file:
    pdf_content = pdf_file.read()

expected_pdf_content = Document(
    page_content=" Strong financial and  operational performance In 2018, we continued to nurture and invest in our marketplace.  As a result, we connected more buyers and sellers than ever before, and delivered a strong performance across important financial and operating metrics.  Our vibrant community includes people buying and selling in nearly every country in the world.  Active sellers grew 9. 1 million* Active buyers grew 18. 4 million* *As of December 31, 2018.  Gross Merchandise Sales (GMS) Revenue GMS growth accelerated to  20. 8% in 2018 compared to 2017.  % Domestic GMS % International GMS Revenue growth accelerated to 36. 8% in 2018 compared to 2017",
    metadata={'file_name': 'file_name.pdf', 'file_id': 'd875d722-be7e-48bb-89f1-d78960ba4eea',
              'es_id': '2132a473-b63d-4bf9-bbc2-812382ca3ce8'})

expected_text = "Revenue growth accelerated to 36.8% in 2018 compared to 2017. 2015 2016 2017 2018 Revenue $273M $365M $441M $604M % Domestic GMS % International GMS Gross Merchandise Sales (GMS) GMS growth accelerated to 20.8% in 2018 compared to 2017. 2015 2016 2017 2018 70% 30% $2.39B $2.84B $3.25B $3.93B 70% 30% 67% 33% 65% 35% *As of December 31, 2018. Strong financial and operational performance In 2018, we continued to nurture and invest in our marketplace. As a result, we connected more buyers and sellers than ever before, and delivered a strong performance across important financial and operating metrics. Active buyers grew 18.2% to 39.4 million* Active sellers grew 9.4% to 2.1 million* Our vibrant community includes people buying and selling in nearly every country in the world. 6"
