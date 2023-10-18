from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from huggingface_hub.utils import RepositoryNotFoundError
from loguru import logger

from source.exceptions.service_exceptions import ModelNotLoaded


def get_embedding_function(embedding_function_name: str) -> SentenceTransformerEmbeddingFunction:
    """
    A callable factory that creates embedding functions,
    for now support SentenceTransformerEmbeddingFunction from chromadb
    Args:
        embedding_function_name: str

    Returns: SentenceTransformerEmbeddingFunction
    """
    try:
        return SentenceTransformerEmbeddingFunction(model_name=embedding_function_name)
    except RepositoryNotFoundError as error:
        logger.error(error)
        raise ModelNotLoaded(detail="Unable to load embedding model!") from error
