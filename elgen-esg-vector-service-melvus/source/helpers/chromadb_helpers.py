import chromadb
from chromadb.config import Settings


def create_chromadb_client(persist_directory: str) -> chromadb.Client:
    """
    A little utility to create the db connection with the dependency container
    Args:
        persist_directory:

    Returns:

    """
    chroma_client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=persist_directory,
        anonymized_telemetry=False
    ))

    chroma_client.heartbeat()

    return chroma_client
