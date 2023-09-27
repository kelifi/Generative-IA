import base64
import concurrent
import json
from concurrent.futures import ThreadPoolExecutor
from os.path import basename
from typing import List

import requests
from fastapi import HTTPException
from langchain.schema import Document
from pydantic import ValidationError
from requests import RequestException
from starlette.background import BackgroundTasks
from starlette.responses import JSONResponse
from tqdm import tqdm

from configuration.config import ElasticSearchConfig, AppConfig, DocumentsConfig, \
    TextProcessingConfig, VectorStoreApiConfig
from configuration.logging import logger
from source.exceptions.service_exceptions import ElasticSearchError, VectorApiError
from source.helpers.text_processing_helpers import chunk_text_nltk
from source.schema.es import create_ingest_input_schema
from source.schema.requests import StoreDocumentsRequest
from source.utils.common import divide_into_batches, clean_non_sense_text


class DocumentsIngestionService:

    def __init__(self, elastic_search_config: ElasticSearchConfig, doc_config: DocumentsConfig,
                 text_proc_config: TextProcessingConfig, vec_api_config: VectorStoreApiConfig,
                 app_config: AppConfig):

        self.request_headers = {'Content-type': 'application/json'}

        self.es_config = elastic_search_config
        self.text_proc_config = text_proc_config
        self.folder_path = doc_config.SOURCE_DIRECTORY
        self.app_config = app_config
        self.vec_api_config = vec_api_config
        self.create_pipeline()
        self.create_ingest_index()

        self.ingest_input_schema = create_ingest_input_schema(self.es_config)
        self.create_ingest_index()

    def create_ingest_index(self):
        try:
            if not self.check_ingest_index_exists():
                req = requests.put(
                    f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
                    headers=self.request_headers)
                if req.status_code == 200:
                    logger.info("Ingest Index created with success!")
                else:
                    logger.error(f"Ingest Index creation failed: {req.json()}")
        except (requests.exceptions.ConnectionError, ElasticSearchError) as error:
            logger.error(error)
            logger.warning("Unable to create ingested documents index!")

    def send_doc_batch(self, data: StoreDocumentsRequest):
        logger.info(f"Batch length {len(data.data)}")
        response = requests.post(self.vec_api_config.VEC_STORE_URL, json=data.dict())

        logger.info(response.json())
        if not response.ok:
            raise VectorApiError(detail="storing in vector store failed!")

        return response.json()

    def send_to_vector_database(self, batches):
        with ThreadPoolExecutor() as executor:
            # Submit each batch to the executor
            future_tasks = [executor.submit(self.send_doc_batch, batch) for batch in batches]

            # Retrieve the results as they complete
            for future in tqdm(iterable=concurrent.futures.as_completed(future_tasks), desc="sending a batch"):
                try:
                    result = future.result()
                    logger.info(result)
                except VectorApiError as error:
                    logger.error(error)

    def ingest_documents_to_es(self, file, file_id) -> List[Document]:
        """
        :param pdf_files:
        :param folder_path:
        :param filter_documents: use it from the vector store to filter out source documents and to prevent
        unncessary calls to elasticsearch ;)
        :return:
        """
        try:
            document_id = self.ingest_single_document(uploaded_file=file, file_name=file.name, file_id=file.name)
            indexed_text = self.get_text_by_es_id(doc_id=document_id)
            clean_ingested_text = clean_non_sense_text(indexed_text)
            return Document(page_content=clean_ingested_text,
                            metadata={"source": file_id, "es_id": document_id})
        except (ElasticSearchError, RequestException) as error:
            logger.error(error)
            logger.warning(f"skipping document {document_id}")

    def ingest_single_document(self, uploaded_file: bytes, filename: str, file_id: str = None) -> str:
        try:
            es_document = self.ingest_input_schema(**{
                "filepath": filename,
                "filename": basename(filename),
                "fileid": file_id or "",
                self.es_config.FIELD_NAME: base64.b64encode(uploaded_file).decode('utf-8'),
            }).dict()
        except ValidationError as error:
            logger.error(error)
            logger.error("Possibly because of a change in ingest pipeline schema/input schema!")
            raise ElasticSearchError() from error

        logger.info(f"Ingesting Document ='{filename}' ...")

        re_post = requests.post(
            f"{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_doc",
            params={'pipeline': self.es_config.PIPELINE_NAME},
            headers=self.request_headers,
            data=json.dumps(es_document))
        es_doc_id = re_post.json().get('_id')
        logger.info(f"File successfully added to ES id: '{es_doc_id}' ")
        return es_doc_id

    def get_text_by_es_id(self, doc_id: str):
        try:
            req = requests.get(
                f'{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_doc/{doc_id}')
        except RequestException as ex:
            logger.error(ex)
            raise ElasticSearchError(f"Error with doc_id {doc_id} : {ex}") from ex

        try:
            results = req.json()
            return results['_source']['attachment']['content']
        except (KeyError, IndexError) as ex:
            raise ElasticSearchError(f"Error with doc_id {doc_id} : {ex}") from ex

    def filter_existing_documents(self, file_list: List[str]):
        return [f for f in file_list if not self.check_ingested_in_es(f)]

    def ingest_file_to_es(self, file: bytes, file_id: str, file_name: str):
        try:
            document_id = self.ingest_single_document(uploaded_file=file, filename= file_name,  file_id=file_id)

            indexed_text = self.get_text_by_es_id(doc_id=document_id)
            clean_ingested_text = clean_non_sense_text(indexed_text)
            return Document(page_content=clean_ingested_text,
                            metadata={"file_name": file_name, "file_id": file_id, "es_id": document_id})

        except (ElasticSearchError, RequestException) as error:
            logger.error(error)
            logger.warning(f"skipping document {document_id}")

    def ingest_documents_to_es(self, file: bytes, filename: str, file_id: str) -> Document:
        """
        :param pdf_files:
        :param folder_path:
        :param filter_documents: use it from the vector store to filter out source documents and to prevent
        unncessary calls to elasticsearch ;)
        :return:
        """
        try:
            document_id = self.ingest_single_document(file, filename, file_id)

            indexed_text = self.get_text_by_es_id(doc_id=document_id)
            clean_ingested_text = clean_non_sense_text(indexed_text)
            return Document(page_content=clean_ingested_text,
                            metadata={"source": file_id, "es_id": document_id})
        except (ElasticSearchError, RequestException) as error:
            logger.error(error)
            logger.warning(f"skipping document {document_id}")


    def process_documents(self, documents_list: List[Document]) -> List[Document]:
        """
        Load documents and split in chunks
        """

        processed_documents = []

        for document in tqdm(iterable=documents_list, desc="chunking a document"):
            chunked_text_list: List[str] = chunk_text_nltk(text=document.page_content,
                                                           chunk_size=self.text_proc_config.CHUNK_SIZE,
                                                           overlap=self.text_proc_config.CHUNK_OVERLAP)
            processed_documents.extend(
                [Document(page_content=text, metadata=document.metadata) for text in chunked_text_list])

        return processed_documents


    async def ingest_file_data(self, bg_tasks: BackgroundTasks, my_file, file_id):
        self.create_ingest_index()  # this will not create an index if it does exist already
        file = await  my_file.read()
        document = self.ingest_file_to_es(file, file_id, my_file.filename)
        documents_batches = divide_into_batches([document], batch_size=10)
        vec_store_request_data_batches = [StoreDocumentsRequest(data=[
            {"document": doc.page_content, "metadata": doc.metadata} for doc in self.process_documents(
                documents_list=document_batch
            )]
        ) for document_batch in documents_batches]

        logger.info(f"how many batches {len(vec_store_request_data_batches)}")
        bg_tasks.add_task(self.send_to_vector_database, batches=vec_store_request_data_batches)
        return JSONResponse(content={
            "detail": "ingestion in elastic search done! Sending batches to vector store in background tasks!check "
                      "service logs!"
        }, background=bg_tasks)


    def create_ingest_index(self):
        try:
            if not self.check_ingest_index_exists():
                req = requests.put(
                    f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
                    headers=self.request_headers)
                if req.status_code == 200:
                    logger.info("Ingest Index created with success!")
                else:
                    logger.error(f"Ingest Index creation failed: {req.json()}")
        except (requests.exceptions.ConnectionError, ElasticSearchError) as error:
            logger.error(error)
            logger.warning("Unable to create ingested documents index!")

    def check_ingest_index_exists(self) -> bool:
        req = requests.get(
            f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
            headers={'Content-type': 'application/json'})
        if req.status_code == 200:
            logger.info("Ingest Index exists already!")
            return True
        elif req.status_code == 404:
            logger.warning(f"Ingest Index does not exist: {req.json()}")
            return False
        else:
            raise ElasticSearchError(detail="Unable to check if Ingest Index exists!")


    async def delete_ingest_index(self):
        try:
            req = requests.delete(
                f"http://{self.es_config.HOST}:{self.es_config.PORT}/{self.es_config.INGESTION_INDEX}",
                headers=self.request_headers)
            if req.status_code == 200:
                return {"detail": "Ingest Index deleted successfully!"}

            if req.status_code == 404:
                raise HTTPException(detail="Ingest Index does not exist already!", status_code=404)

            raise HTTPException(detail=f"{req.json()}", status_code=500)
        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            return {"detail": "Not able to perform request to elasticsearch!"}


    def create_pipeline(self):
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
            if req.status_code == 200:
                logger.info("Es pipeline created with success")
            else:
                logger.error(f"Es pipeline creation failed: {req.json()}")
        except requests.exceptions.ConnectionError as error:
            logger.error(error)
            logger.warning("Application will not work as intended without ES!")
