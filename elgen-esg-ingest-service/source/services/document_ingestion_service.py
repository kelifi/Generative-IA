import base64
import io
import json
from os.path import basename
from typing import List
from uuid import uuid4

import requests
from bidi.algorithm import get_display
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTPage, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError
from pydantic import ValidationError
from requests import RequestException
from tqdm import tqdm

from configuration.config import ElasticSearchConfig, AppConfig, DocumentsConfig, \
    TextProcessingConfig, VectorStoreApiConfig
from configuration.logging_setup import logger
from source.enums.extraction_methods import ExtractionMethods
from source.exceptions.service_exceptions import VectorApiError, CheckError, \
    IngestionDeletionError, IngestPipelineCreationError, IngestIndexCreationError, \
    ElasticIndexCheckError, FileIngestionError, TextRetrievalError, SchemaValidationError, PDFExtractionError, \
    FileAlreadyIngestedError
from source.schema.elastic_search_schemas import create_ingest_input_schema, IngestionDelSchema, Document
from source.schema.request_schemas import StoreDocumentsRequest
from source.schema.response_schemas import IngestedVectorBatchesCount
from source.utils.common import divide_into_batches, clean_non_sense_text
from source.utils.text_preprocessing_utils import chunk_text_nltk


class DocumentsIngestionService:

    def __init__(self, elastic_search_config: ElasticSearchConfig, doc_config: DocumentsConfig,
                 text_proc_config: TextProcessingConfig, vec_api_config: VectorStoreApiConfig,
                 app_config: AppConfig, file_to_text_methods: dict) -> None:

        self.request_headers = {'Content-type': 'application/json'}

        self.es_config = elastic_search_config
        self.text_proc_config = text_proc_config
        self.folder_path = doc_config.SOURCE_DIRECTORY
        self.app_config = app_config
        self.vec_api_config = vec_api_config

        self.ingest_input_schema = create_ingest_input_schema(es_config=self.es_config)
        self.__file_to_text_methods = file_to_text_methods

    def create_ingest_index(self) -> None:
        """Create the ingest index in elastic search"""
        if self.check_ingest_index_exists():
            return None
        try:
            req = requests.put(
                f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
                headers=self.request_headers)
            if req.status_code != requests.codes.OK:
                logger.error(f"Ingest Index creation failed: {req.json()}")
                raise IngestIndexCreationError(
                    detail=f"An error occurred when executing the PUT request to es")

            logger.info(f"Ingest Index {self.es_config.INGESTION_INDEX} created with success!")

        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            logger.warning("Unable to create ingested documents index!")
            raise IngestIndexCreationError(detail="An error occurred when sending the PUT request to es")

    def send_data_to_vector_service(self, data: StoreDocumentsRequest) -> IngestedVectorBatchesCount:
        """send data to vector store"""
        logger.info(f"Data length to send to vector service: {len(data.data)}")
        try:
            response = requests.post(self.vec_api_config.VEC_STORE_URL, json=data.dict())

            if response.status_code >= requests.codes.BAD_REQUEST:
                raise VectorApiError(detail="storing in vector store failed!")
            logger.info("Data was successfully sent to vector service")

        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            raise VectorApiError(detail="failed to send request to vector service")

        try:
            return IngestedVectorBatchesCount(**response.json())
        except ValidationError as error:
            logger.error(error)
            raise SchemaValidationError(detail="an error has occurred when creating vector batch count schema")

    def ingest_single_document(self, uploaded_file: bytes, filename: str, file_id: str = None,
                               workspace_id: str = None) -> str | None:
        """Ingest a single document in elastic search and get its id"""
        if self.check_if_ingested_by_filename(file_name=f'{workspace_id}/{filename}'):
            raise FileAlreadyIngestedError(detail=f"file {filename} is already ingested!")

        try:
            es_document = self.ingest_input_schema(**{
                "filepath": filename,
                "filename": f'{workspace_id}/{basename(filename)}',
                "fileid": file_id or "",
                self.es_config.FIELD_NAME: base64.b64encode(uploaded_file).decode('utf-8'),
            }).dict()

        except ValidationError as error:
            logger.error(error)
            raise SchemaValidationError(detail="an error has occurred when creating the ingest input schema")

        logger.info(f"Ingesting the following document: '{filename}' ...")

        try:
            re_post = requests.post(
                f"{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_doc",
                params={'pipeline': self.es_config.PIPELINE_NAME},
                headers=self.request_headers,
                data=json.dumps(es_document))

            if re_post.status_code >= requests.codes.BAD_REQUEST:
                logger.error(f"the json of the response is: {re_post.json()}")
                raise FileIngestionError(
                    detail=f"Could not ingest {filename} with filehandler id {file_id} in elastic search,")


        except RequestException as error:
            logger.error(error)
            raise FileIngestionError(detail="Could not send Post request to elastic search")

        es_doc_id = re_post.json().get('_id')

        if es_doc_id is None:
            raise FileIngestionError(detail="Could not extract _id field from elastic search response")

        logger.info(f"File successfully added to ES with the following id: '{es_doc_id}' ")
        return es_doc_id

    def get_text_by_es_id(self, doc_id: str) -> str:
        """Get the text by its document id"""
        try:
            req = requests.get(
                f'{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_doc/{doc_id}')
        except RequestException as error:
            logger.error(error)
            raise TextRetrievalError("Error with sending the get request to elastic search to get the text by id")

        try:
            return req.json()['_source']['attachment']['content']
        except KeyError as error:
            logger.error(f"Key error for key: {error}")
            raise TextRetrievalError(detail="Could not retrieve text from document")

    def check_if_ingested_by_filename(self, file_name: str) -> bool:
        """check if a file was already ingested or not"""
        check_existence_query = {
            "query": {
                "term": {
                    "filename.keyword": file_name
                }
            }
        }
        try:
            response = requests.get(f'{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_search',
                                    json=check_existence_query)
            if response.status_code >= requests.codes.BAD_REQUEST:
                logger.error(f"here is the json of the response: {response.json()}")
                raise CheckError(
                    detail=f"An error occurred when sending the get request to check {file_name} existence in ES")
        except RequestException as error:
            logger.error(error)
            raise CheckError(
                detail=f"An error occurred when sending the get request to check {file_name} existence in ES")
        try:
            return response.json()['hits']['total']['value'] > 0
        except KeyError as error:
            logger.error(error)
            raise CheckError(
                detail=f"Cannot parse the response from ES to check {file_name} existence")

    def get_full_document_from_es(self, file_content: bytes, file_id: str, file_name: str,
                                  workspace_id: str) -> Document:
        """Get the text, clean it and construct a proper Document object that can be sent to the vector service"""
        document_id = self.ingest_single_document(uploaded_file=file_content, filename=file_name, file_id=file_id,
                                                  workspace_id=workspace_id)

        indexed_text = self.get_text_by_es_id(doc_id=document_id)

        if not indexed_text:
            logger.warning(f"The text retrieved from elastic search with {document_id} is empty!")
            raise TextRetrievalError(
                detail=f"the file was ingested but no text was extracted or found")

        clean_ingested_text = clean_non_sense_text(indexed_text)

        if not clean_ingested_text:
            logger.warning(f"The text retrieved from elastic search with {document_id} was cleaned but it is empty!")
            raise TextRetrievalError(detail="Cleaning text returned an empty string")

        try:
            return Document(page_content=clean_ingested_text,
                            metadata={"file_name": file_name, "file_id": file_id, "workspace_id": workspace_id,
                                      "es_id": document_id})
        except ValidationError as error:
            logger.error(error)
            raise SchemaValidationError(
                "An error occurred when filling the Document model after cleaning the text!")

    def process_documents(self, documents_list: List[Document]) -> List[Document]:
        """
        Load documents and split in chunks of smaller Documents
        """
        processed_documents = []

        logger.info("start loading documents and split in chunks")
        for document in tqdm(iterable=documents_list, desc="chunking a document"):
            chunked_text_list: List[str] = chunk_text_nltk(text=document.page_content,
                                                           chunk_size=self.text_proc_config.CHUNK_SIZE,
                                                           overlap=self.text_proc_config.CHUNK_OVERLAP)
            try:
                processed_documents.extend(
                    [Document(page_content=text, metadata=document.metadata) for text in chunked_text_list])
            except ValidationError as error:
                logger.error(error)
                raise SchemaValidationError(
                    "An error occurred when filling the Document model after chunking its content")
        return processed_documents

    # TODO remove this if pdfplumber is to be used
    @staticmethod
    def get_text_from_one_page(layouts: LTPage) -> str:
        """
        Extract the text from one page only with many layouts
        :param layouts: the detected layouts
        :return: text from page
        """
        detected_text = ''
        for layout_object in layouts:
            if isinstance(layout_object, LTTextBoxHorizontal):
                text = get_display(layout_object.get_text())
                if any(char.isalpha() for char in text) and any(char.islower() for char in text):
                    detected_text += '\n' + text.replace('\n', ' ')
        return clean_non_sense_text(detected_text)

    # TODO remove this if pdfplumber is to be used
    def extract_text_from_pdf(self, file_content: bytes, file_name: str, file_id: str, workspace_id: str) -> Document:
        """
        Extract the text from the entire pdf document
        :param file_content: byte content of the file
        :param file_name: the file's name
        :param file_id: the file's id
        :param workspace_id: workspace id
        :return: the list of extracted texts
        """
        resource_manager = PDFResourceManager()
        device = PDFPageAggregator(resource_manager, laparams=LAParams())
        interpreter = PDFPageInterpreter(resource_manager, device)
        pages = PDFPage.get_pages(fp=io.BytesIO(file_content))
        text_list = []
        logger.info("start extraction of text from pdf")
        try:
            i = 0
            for page in pages:
                interpreter.process_page(page)
                extracted_layouts = device.get_result()
                text_list.append(self.get_text_from_one_page(layouts=extracted_layouts))
                logger.info(f"Text Extracted from page {i}")
                i += 1

        except PDFSyntaxError as error:
            logger.error(error)
            raise PDFExtractionError(detail="An syntax error arised when reading the provided file")
        logger.info("End of text extraction from pdf")
        # the es_id here is a random uuid, until we decide to remove elastic search from the ingest service completely
        return Document(page_content='\n'.join(text_list),
                        metadata={"file_name": file_name, "file_id": file_id, "workspace_id": workspace_id,
                                  "es_id": str(uuid4())})

    async def ingest_into_es_and_vector(self, file_content: bytes, file_name: str, file_id: str,
                                        workspace_id: str) -> None:
        """Ingest a document elastic search, chunk it and send it to vector store"""
        file_extension = file_name.split('.')[-1]

        if file_extension == ExtractionMethods.PDF:
            extracted_text = self.__file_to_text_methods.get(ExtractionMethods.PDF).extract_text_from_pdf(
                files_bytes=file_content)

            document = Document(page_content=extracted_text,
                                metadata={"file_name": file_name, "file_id": file_id, "workspace_id": workspace_id,
                                          "es_id": str(uuid4())})
        else:
            document = self.get_full_document_from_es(file_content=file_content, file_id=file_id,
                                                      file_name=file_name, workspace_id=workspace_id)

        documents_batches = divide_into_batches([document], batch_size=self.vec_api_config.BATCH_SIZE)

        vec_store_request_data_batches = [StoreDocumentsRequest(data=[
            {"document": doc.page_content, "metadata": doc.metadata} for doc in self.process_documents(
                documents_list=document_batch
            )]
        ) for document_batch in documents_batches]

        logger.info(f"Will send {len(vec_store_request_data_batches)} batches to vector service")

        for batch in vec_store_request_data_batches:
            self.send_data_to_vector_service(batch)

    def check_ingest_index_exists(self) -> bool:
        """Check if the ingest index already exist or not"""
        req = requests.get(
            f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
            headers={'Content-type': 'application/json'})
        if req.status_code == 200:
            logger.info("Ingest Index exists already!")
            return True
        elif req.status_code == requests.codes.not_found:
            logger.warning("Ingest Index does not exist")
            return False
        raise ElasticIndexCheckError(detail="Unable to check if Ingest Index exists!")

    async def delete_ingest_index(self) -> IngestionDelSchema:
        """Delete Elastic-Search's ingestion index"""
        try:
            req = requests.delete(
                f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
                headers=self.request_headers)

            if req.status_code >= requests.codes.BAD_REQUEST:
                raise IngestionDeletionError(
                    detail="the delete request sent to es failed with an error")

            return IngestionDelSchema(
                detail=f"Ingest Index named {self.es_config.INGESTION_INDEX} deleted successfully!")

        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            raise IngestionDeletionError(
                detail="Could not connect to elastic search to execute the delete request")

    def create_pipeline(self) -> None:
        """create the extraction pipeline"""
        pipeline_description = {
            "description": "Extract attachment information",
            "processors": [
                {
                    "attachment": {
                        "target_field": "attachment",
                        "field": self.es_config.FIELD_NAME,
                    },
                    "remove": {
                        "field": self.es_config.FIELD_NAME
                    }
                }
            ]
        }

        try:
            req = requests.put(
                f"http://{self.es_config.HOST}:{self.es_config.PORT}/_ingest/pipeline/{self.es_config.PIPELINE_NAME}",
                headers=self.request_headers, json=pipeline_description)

            if req.status_code >= requests.codes.BAD_REQUEST:
                logger.error(f"Es pipeline creation failed: {req.json()}")
                raise IngestPipelineCreationError(
                    detail="Error in creating the Elastic search pipline")

            logger.info(f"Es pipeline {self.es_config.PIPELINE_NAME} created or updated with success")

        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            logger.warning("Application will not work as intended without ES!")
            raise IngestPipelineCreationError(
                detail="Error in sending the put request to Elastic search pipline")
