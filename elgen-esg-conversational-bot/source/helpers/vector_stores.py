from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

from configuration.config import CHROMA_SETTINGS
from configuration.config import app_config

embeddings = HuggingFaceEmbeddings(model_name=app_config.embeddings_model_name)

db = Chroma(
    persist_directory=app_config.PERSIST_DIRECTORY,
    embedding_function=embeddings,
    client_settings=CHROMA_SETTINGS
)

vector_retriever_client = db.as_retriever(search_kwargs={"k": app_config.TOP_K})
