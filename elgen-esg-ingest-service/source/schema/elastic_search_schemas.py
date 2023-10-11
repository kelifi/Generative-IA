from pydantic import create_model, BaseModel, Field

from configuration.config import ElasticSearchConfig


def create_ingest_input_schema(es_config: ElasticSearchConfig):
    return create_model("IngestPipelineInput", **{
        "filename": "string",
        "filepath": "string",
        es_config.FIELD_NAME: "string",
        "is_chunked": False,
        "is_vectorized": False
    })


class IngestionDelSchema(BaseModel):
    detail: str = Field(description="detail on the deletion of Elastic Search index")


class Document(BaseModel):
    """Class for storing a piece of text and associated metadata."""

    page_content: str = Field(description="A page's content")
    metadata: dict = Field(default_factory=dict, description="metadata of the document")

