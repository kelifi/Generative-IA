import logging
import sys
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

import requests
from dependency_injector import providers
from fastapi import FastAPI
from pydantic import ValidationError

from configuration.config import pact_config
from configuration.injection_container import DependencyContainer
from source.apis.chat_api import chat_router
from source.apis.conversation_api import conversation_router
from source.apis.health_check_api import health_check_router
from source.exceptions.service_exceptions import PactVerificationError
from source.helpers.db_helpers import DBHelper
from tests.contract_test.configuration.configuration import BrokerStateData


class PactStates:
    def __init__(self, container):
        self.container = container
        self.container.wire(modules=[sys.modules[__name__]])
        self.conversation_repository = container.conversation_repository()
        self.states = dict()

    def get_pact_states_data(self):
        """
        get the data used in the states defined in pact broker
        """
        pact_url = self._get_pact_url()
        pact_file = self._get_pact_file(pact_url)
        interactions = pact_file.get("interactions", [])

        for interaction in interactions:
            self._process_interaction(interaction)

    @staticmethod
    def _get_pact_url() -> str:
        """
        get the full url path of the contract in pact broker
        """
        return (f"{pact_config.PACT_BROKER_URL}/pacts/provider/{pact_config.PROVIDER_NAME}"
                f"/consumer/{pact_config.CONSUMER_NAME}/latest")

    @staticmethod
    def _get_pact_file(pact_url: str) -> dict:
        """
        get the informations of pact defined
        """
        headers = {
            "Authorization": f"Basic {pact_config.BROKER_KEY}",
            "Content-Type": "application/json",
        }
        return requests.get(pact_url, headers=headers).json()

    def _process_interaction(self, interaction: dict):
        """
        saves the interaction related data in a list
        """
        try:
            request = interaction["request"]
            method = request['method']
            parsed_url = urlparse(request["path"])
            headers = request.get('headers', {})
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)

            if not isinstance(path, str) or path is None:
                raise ValueError("Invalid input: path must be a non-empty string")

            path_params = [param for param in path.split("/")[2:] if param]
            broker_state = BrokerStateData(
                request_method=method,
                query_params=query_params,
                request_body=request.get("body", None),
                path_params=path_params,
                headers=headers
            )
            self.states[interaction["providerState"]] = broker_state
        except (IndexError, ValidationError):
            logging.info("error getting data for that state")
            pass

    def setup_user_exist_and_conversation_data_exist(self):
        """
        state provided when the user conversations exists in DB
        """
        logging.info("mocking 'get_conversations_per_user' in ConversationService")
        try:
            self.conversation_repository.create_conversation(conversation_title="test",
                                                             user_id=str(self.states["Conversation list found"]
                                                                         .headers['user-id']),
                                                             workspace_id=str(self.states["Conversation list found"]
                                                                              .headers['workspace-id'])
                                                             )
        except (KeyError, IndexError):
            raise PactVerificationError

    def setup_conversation_exist(self):
        """
        state provided when the conversation exists in DB
        """
        logging.info("mocking 'get_conversation_by_id' in ConversationService")

        try:
            self.conversation_repository.create_conversation_mock(conversation_title="test",
                                                                  user_id=str(uuid4()),
                                                                  conversation_id=str(self.states["Conversation exist"]
                                                                                      .path_params[0]),
                                                                  workspace_id=str(uuid4())
                                                                  )
        except (KeyError, IndexError):
            raise PactVerificationError


server_start_time = 1
app = FastAPI()

db_helpers = providers.Singleton(DBHelper, db_url="sqlite://")
container = DependencyContainer()
# Assign the overridden db_helpers to the container
container.db_helpers.override(db_helpers)
app.container = container

app.include_router(conversation_router, tags=["conversation_api"])
app.include_router(chat_router, tags=["question_answer_api"])
app.include_router(health_check_router, tags=["healthz_api"])
pact_states = PactStates(container)
