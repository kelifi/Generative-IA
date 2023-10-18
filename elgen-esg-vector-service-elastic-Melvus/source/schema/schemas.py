from pydantic import BaseModel
from pydantic.fields import Field


class SourceData(BaseModel):
    text: str
    source_file: str


class ESDocumentCountSchema(BaseModel):
    """
    Schema for counting documents inside an Elasticsearch index.
    """
    count: int = Field(description="count of documents inside Elastic search")


class QueryMatchAll(BaseModel):
    """
     Schema of query that matches all documents in Elasticsearch
    """
    match_all: dict


class QueryTerm(BaseModel):
    """
    Query condition that filters documents based on a specific term in Elasticsearch.
    """
    term: dict


class QueryBool(BaseModel):
    """
    Boolean query in Elasticsearch, combining multiple query conditions with logical operators.
    """
    must: list[dict]


class Query(BaseModel):
    """
    This class represents a query in Elasticsearch, specifically a Boolean query.
    """
    bool: QueryBool


class ScriptParams(BaseModel):
    """
    This class represents parameters for a script used in Elasticsearch.
    """
    queryVector: list[float]


class Script(BaseModel):
    """
    This class represents a script to be used in Elasticsearch, typically for custom scoring or data transformation.
    """
    source: str
    params: ScriptParams


class QueryScriptScore(BaseModel):
    """
    This class represents a script_score query in Elasticsearch, which combines a query condition with a custom scoring script.
    """
    query: Query
    script: Script
