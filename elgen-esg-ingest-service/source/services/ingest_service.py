import base64
import concurrent
import json
from concurrent.futures import ThreadPoolExecutor
from os.path import basename
from typing import List, Optional

import requests
from fastapi import HTTPException
from langchain.docstore.document import Document
from pydantic import ValidationError
from requests import RequestException
from starlette.background import BackgroundTasks
from starlette.responses import JSONResponse
from tqdm import tqdm

from configuration.config import ElasticSearchConfig, es_config, AppConfig, DocumentsConfig, \
    TextProcessingConfig, app_config, doc_config, text_proc_config, VectorStoreApiConfig, vec_api_config
from configuration.logging import logger
from source.exceptions.service_exceptions import ElasticSearchError, VectorApiError
from source.helpers.file_helpers import get_documents_list
from source.helpers.text_processing_helpers import chunk_text_nltk
from source.schema.es import create_ingest_input_schema
from source.schema.requests import StoreDocumentsRequest
from source.utils.common import divide_into_batches, clean_non_sense_text


class IngestionService:

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

    def check_ingested_in_es(self, filename: str) -> Optional[str]:
        """Check if a file was already ingested based on its filename.
        Returns True if it was ingested else False"""
        query = {
            'query': {
                'term': {
                    'filename.keyword': filename
                }
            }
        }
        response = requests.get(
            url=f'{self.es_config.ES_URL}/{self.es_config.INGESTION_INDEX}/_search',
            json=query)
        if response.status_code not in [200, 201]:
            logger.error(response.json())
            raise ElasticSearchError(detail="Unable to check if file exists!")

        data = response.json()

        try:
            hits = data["hits"]["hits"]
            if not hits:
                return None

            if document_id := hits[0]['_id']:
                logger.info(f"Document {filename} already exists in Elasticsearch with id {document_id}!")
                return document_id
            else:
                return None

        except KeyError as error:
            logger.error(f"{error} with response {data}")
            raise ElasticSearchError(
                detail="Response Schema Error! Check logs!"
            ) from error

    def ingest_single_document(self, uploaded_file: bytes, filename: str) -> str:
        try:
            es_document = self.ingest_input_schema(**{
                "filepath": filename,
                "filename": basename(filename),
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
        logger.info(f"Document {filename} supposedly created with id {es_doc_id}")
        logger.info(f"Tika Pipeline Json Response {re_post.json()}")
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

    def ingest_documents_to_es(self, pdf_files: List[str]) -> List[Document]:
        """
        :param pdf_files:
        :param folder_path:
        :param filter_documents: use it from the vector store to filter out source documents and to prevent
        unncessary calls to elasticsearch ;)
        :return:
        """

        documents_list = []
        for pdf_file in tqdm(iterable=pdf_files, desc="Looping through files"):
            with open(pdf_file, 'rb') as file:
                document_id = self.check_ingested_in_es(pdf_file)
                try:
                    if not document_id:
                        document_id = self.ingest_single_document(uploaded_file=file.read(), filename=pdf_file)

                    indexed_text = self.get_text_by_es_id(doc_id=document_id)
                    clean_ingested_text = clean_non_sense_text(indexed_text)
                    documents_list.append(
                        Document(page_content=clean_ingested_text,
                                 metadata={"source": basename(pdf_file), "es_id": document_id}))
                except (ElasticSearchError, RequestException) as error:
                    logger.error(error)
                    logger.warning(f"skipping document {document_id}")
        return documents_list

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

    async def ingest_data(self, bg_tasks: BackgroundTasks):

        self.create_ingest_index()  # this will not create an index if it does exist already

        file_list = get_documents_list(doc_config.SOURCE_DIRECTORY)

        if not file_list:
            raise HTTPException(detail="No file was found in the source directory", status_code=404)

        documents = self.ingest_documents_to_es(file_list)

        documents_batches = divide_into_batches(documents, batch_size=10)

        vec_store_request_data_batches = [StoreDocumentsRequest(data=[
            {"document": doc.page_content, "metadata": doc.metadata} for doc in self.process_documents(
                documents_list=document_batch
            )]
        ) for document_batch in documents_batches]

        logger.info(f"how many batches {len(vec_store_request_data_batches)}")

        def send_doc_batch(data: StoreDocumentsRequest):
            logger.info(f"Batch length {len(data.data)}")
            response = requests.post(self.vec_api_config.VEC_STORE_URL, json=data.dict())

            logger.info(response.json())
            if not response.ok:
                raise VectorApiError(detail="storing in vector store failed!")

            return response.json()

        def send_to_vector_database(batches):
            with ThreadPoolExecutor() as executor:
                # Submit each batch to the executor
                future_tasks = [executor.submit(send_doc_batch, batch) for batch in batches]

                # Retrieve the results as they complete
                for future in tqdm(iterable=concurrent.futures.as_completed(future_tasks), desc="sending a batch"):
                    try:
                        result = future.result()
                        logger.info(result)
                    except (RequestException, VectorApiError) as error:
                        logger.error(error)

        bg_tasks.add_task(send_to_vector_database, batches=vec_store_request_data_batches)

        return JSONResponse(content={
            "detail": "ingestion in elastic search done! Sending batches to vector store in background tasks!check "
                      "service logs!"
        }, background=bg_tasks)

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


ingestion_service = IngestionService(elastic_search_config=es_config, doc_config=doc_config,
                                     text_proc_config=text_proc_config, vec_api_config=vec_api_config,
                                     app_config=app_config)
