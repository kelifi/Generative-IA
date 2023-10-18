import logging

import numpy as np
import openai
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


def openai_embedder(input: str, model: str = 'text-embedding-ada-002'):
    """
    set the openai api key
    """
    openai.api_key = vector_db_config.OPENAI_KEY
    return openai.Embedding.create(input=input, model=model)['data'][0]['embedding']

# TODO update exception
def embed_text(text: str, openai: int) -> np.ndarray:
    """Embed text into a ndarray"""
    if openai == 1:
        try:
            raw_embeddings = openai_embedder(text)
            embeddings = np.array(raw_embeddings).reshape(1, len(raw_embeddings))

        except Exception as error:
            logging.error(str(error))
            raise EmbeddingError(detail=f"Could not get the first element of the returned embeddings using {vector_db_config.EMBEDDING_FUNCTION_NAME}") from error

    else:
        embeddings = model.encode([text])
    try:
        return embeddings[0]
    except IndexError:
        raise EmbeddingError(
            detail=f"Could not get the first element of the returned embeddings using {vector_db_config.EMBEDDING_FUNCTION_NAME}")
