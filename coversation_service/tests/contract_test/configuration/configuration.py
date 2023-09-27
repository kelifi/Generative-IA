from typing import List

from pydantic import BaseModel, Field

from configuration.config import pact_config


class ProviderState(BaseModel):
    state: str = Field(..., description='the state provided for PACT', alias='state')


class PactBrokerConfig(BaseModel):
    broker_username: str = Field(..., description="the broker username")
    broker_password: str = Field(..., description="the broker password")
    broker_url: str = Field(..., description="the broker url")
    publish_version: str = Field(..., description="the publish version in broker")
    publish_verification_results: bool = Field(default=True, description="decision to either publish results or no")


class BrokerStateData(BaseModel):
    request_method: str = Field(..., description="the defined request method in the broker state")
    query_params: dict | None = Field(..., description="the defined query params in the broker state")
    path_params: List | None = Field(..., description="the defined path params in the broker state")
    request_body: str | None = Field(..., description="the defined request body in the broker state")
    headers: dict | None = Field(..., description="the defined request headers in the broker state")


broker_opts = PactBrokerConfig(
    broker_username=pact_config.PACT_BROKER_USERNAME,
    broker_password=pact_config.PACT_BROKER_PASSWORD,
    broker_url=pact_config.PACT_BROKER_URL,
    publish_version=pact_config.PUBLISH_VERSION,
    publish_verification_results=True
)
