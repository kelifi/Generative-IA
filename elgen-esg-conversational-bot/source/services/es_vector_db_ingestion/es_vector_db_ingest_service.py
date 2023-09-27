import base64
import glob
import json
from os.path import basename
from typing import List

import requests
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from loguru import logger
from requests import RequestException
from tqdm import tqdm

from configuration.config import ElasticSearchConfig, EmbedderSettings, app_config, CHROMA_SETTINGS, es_config, \
    embedder_settings, AppConfig
from source.utils.common_utils import chunk_text

persist_directory = app_config.PERSIST_DIRECTORY


class IngestionService:

    def __init__(self, elastic_search_config: ElasticSearchConfig, embedder_settings: EmbedderSettings,
                 app_config: AppConfig):
        self.elastic_search_config = elastic_search_config
        self.embedder_settings = embedder_settings
        self.folder_path = app_config.SOURCE_DIRECTORY
        self.app_config = app_config
        self.create_pipeline()

    def elastic_ingest(self, uploaded_file: bytes, filename: str) -> str:
        es_document = {
            "filename": filename,
            self.elastic_search_config.FIELD_NAME: base64.b64encode(uploaded_file).decode('utf-8'),
        }
        re_post = requests.post(
            f"{self.elastic_search_config.ES_URL}/{self.elastic_search_config.INGESTION_INDEX}/_doc",
            params={'pipeline': self.elastic_search_config.PIPELINE_NAME},
            headers={'Content-type': 'application/json'},
            data=json.dumps(es_document))
        es_doc_id = re_post.json().get('_id')
        logger.info(f"File successfully added to ES id: '{es_doc_id}' ")
        return es_doc_id

    def get_text_by_es_id(self, doc_id: str):
        try:
            req = requests.get(
                f'{self.elastic_search_config.ES_URL}/{self.elastic_search_config.INGESTION_INDEX}/_doc/{doc_id}')
        except RequestException as ex:
            pass
            # TODO: DO

        try:
            results = req.json()
            return results['_source']['attachment']['content']
        except (KeyError, IndexError) as ex:
            pass
            # TODO: DOTI

    def ingest_documents_to_es(self, folder_path) -> List[Document]:
        pdf_files = glob.glob(folder_path + '/*.pdf')
        documents_list = []
        for pdf_file in tqdm(iterable=pdf_files, desc="Looping through files"):
            with open(pdf_file, 'rb') as file:
                if not self.check_ingested_in_es(basename(pdf_file)):
                    document_id: str = self.elastic_ingest(uploaded_file=file.read(), filename=basename(pdf_file))
                    indexed_text = self.get_text_by_es_id(doc_id=document_id)
                    if indexed_text:
                        documents_list.append(
                            Document(page_content=indexed_text, metadata={"source": pdf_file, "es_id": document_id}))
        return documents_list

    def process_documents(self, documents_list: List[Document]) -> List[Document]:
        """
        Load documents and split in chunks
        """
        if not documents_list:
            logger.warning("No new documents to load")
            exit(0)

        processed_documents: List[Document] = []
        for document in documents_list:
            chunked_text_list: List[str] = chunk_text(text=document.page_content,
                                                      chunk_size=self.embedder_settings.CHUNK_SIZE,
                                                      overlap=self.embedder_settings.CHUNK_OVERLAP,
                                                      ignore_token_length=self.embedder_settings.IGNORE_TOKEN_LENGTH)
            processed_documents.extend(
                [Document(page_content=text, metadata=document.metadata) for text in chunked_text_list])

        return processed_documents

    def ingest_data(self):
        embeddings = HuggingFaceEmbeddings(model_name=self.app_config.embeddings_model_name)
        processed_documents = self.process_documents(
            documents_list=self.ingest_documents_to_es(folder_path=self.folder_path))
        logger.info("Saving ingested files into VectorStore!")
        db = Chroma.from_documents(documents=processed_documents, embedding=embeddings,
                                   persist_directory=persist_directory,
                                   client_settings=CHROMA_SETTINGS)
        db.persist()
        logger.info("finished ingestion!")

    def check_ingested_in_es(self, filename: str) -> bool:
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
            url=f'{self.elastic_search_config.ES_URL}/{self.elastic_search_config.INGESTION_INDEX}/_search',
            json=query)
        return response.json()["hits"]["hits"] != []

    def create_pipeline(self):
        pipeline_description = {
            "description": "Extract attachment information",
            "processors": [
                {
                    "attachment": {
                        "target_field": "attachment",
                        "field": self.elastic_search_config.FIELD_NAME,
                    },
                    "remove": {
                        "field": self.elastic_search_config.FIELD_NAME
                    }
                }
            ]
        }

        pipeline_req = requests.put(
            f"http://{self.elastic_search_config.HOST}:{self.elastic_search_config.PORT}/_ingest/pipeline/{self.elastic_search_config.PIPELINE_NAME}",
            headers={'Content-type': 'application/json'}, json=pipeline_description)
        index_req = requests.put(
            f"http://{self.elastic_search_config.HOST}:{self.elastic_search_config.PORT}/{self.elastic_search_config.INGESTION_INDEX}")
        if pipeline_req.status_code == 200:
            logger.info("Es pipeline created with success")
        else:
            logger.error(f"Es pipeline creation failed: {pipeline_req.json()}")
            exit(0)

        if index_req.status_code == 200:
            logger.info(f"Index {self.elastic_search_config.INGESTION_INDEX} created with success")
        elif index_req.status_code == 400:
            logger.warning(f"Index already exist!")
        else:
            logger.error(f"Error while creating the Index")
            exit(0)


ingestion_service = IngestionService(elastic_search_config=es_config, embedder_settings=embedder_settings,
                                     app_config=app_config)
