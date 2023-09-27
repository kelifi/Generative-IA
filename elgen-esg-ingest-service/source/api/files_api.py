from fastapi import APIRouter

from configuration.config import doc_config
from source.helpers.file_helpers import get_documents_list

file_router = APIRouter(prefix="/files")


@file_router.post("/")
async def get_doc_list():
    return get_documents_list(doc_config.SOURCE_DIRECTORY)
