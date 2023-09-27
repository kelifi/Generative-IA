from pydantic import create_model

from configuration.config import ElasticSearchConfig


def create_ingest_input_schema(es_config: ElasticSearchConfig):
    return create_model("IngestPipelineInput", **{
        "filename": "string",
        "filepath": "string",
        es_config.FIELD_NAME: "string",
        "is_chunked": False,
        "is_vectorized": False
    })
