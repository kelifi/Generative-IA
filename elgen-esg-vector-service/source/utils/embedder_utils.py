import numpy as np
from huggingface_hub.utils import RepositoryNotFoundError
from sentence_transformers import SentenceTransformer

from configuration.config import vector_db_config, milvus_collection_config
from source.exceptions.utils_exceptions import EmbeddingError, EmbeddingCompatibilityError, EmbeddingModelNotFoundError


def load_embedding_model(model_name: str) -> tuple[SentenceTransformer, int]:
    try:
        embedding_model = SentenceTransformer(model_name)
    except RepositoryNotFoundError:
        raise EmbeddingModelNotFoundError(model_name)
    return embedding_model, embedding_model.get_sentence_embedding_dimension()


model, embedding_dimension = load_embedding_model(model_name=vector_db_config.EMBEDDING_FUNCTION_NAME)

if milvus_collection_config.TEXT_VECTOR_FIELD_DIMENSION != embedding_dimension:
    raise EmbeddingCompatibilityError(model_name=vector_db_config.EMBEDDING_FUNCTION_NAME,
                                      embedding_dimension=embedding_dimension)


def embed_text(text: str) -> np.ndarray:
    """Embed text into a ndarray"""
    embeddings = model.encode([text])
    try:
        return embeddings[0]
    except IndexError:
        raise EmbeddingError(
            detail=f"Could not get the first element of the returned embeddings using {vector_db_config.EMBEDDING_FUNCTION_NAME}")
