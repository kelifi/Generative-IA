import json
import logging
import os
from typing import List
from uuid import UUID, uuid4

import pytest
import requests
from fastapi import HTTPException
from pact import Consumer, Provider, Like, SomethingLike
from requests.auth import HTTPBasicAuth

from configuration.config import PactSettings
from source.services.conversation_service import ConversationService
from tests.contract_tests.configuration.configuration import consumer_settings, conversation_answers, \
    conversation_output


pact_settings = PactSettings()


@pytest.fixture
def conversation_client():
    return ConversationService(consumer_settings.dict())


def push_to_broker(version: str):
    """
    push the pact created to the broker
    :param version:
    :return:
    """
    pact_file = f"{pact_settings.PACT_CONSUMER_NAME.lower()}-{pact_settings.PACT_PROVIDER_NAME.lower()}.json"
    with open(os.path.join(pact_settings.PACT_DIR, pact_file), 'rb') as pact_file:
        pact_file_json = json.load(pact_file)

    basic_auth = HTTPBasicAuth(pact_settings.PACT_BROKER_USERNAME, pact_settings.PACT_BROKER_PASSWORD)
    logging.info("Uploading contract_tests file to contract_tests broker...")
    pact_url = "/".join([pact_settings.PACT_URL, "pacts/provider", pact_settings.PACT_PROVIDER_NAME,
                            "consumer", pact_settings.PACT_CONSUMER_NAME, "version"])
    try:
        requests.put(
            "{}/{}".format(pact_url, version),
            auth=basic_auth,
            json=pact_file_json)
    except requests.exceptions.RequestException:
        logging.error("error adding this contract")
        raise HTTPException(status_code=400, detail="error adding/updating the pact to the broker")


@pytest.fixture(scope='session')
def pact(request):
    """
    define Pact consumer from mock server
    :param request:
    :return:
    """
    pact = Consumer(pact_settings.PACT_CONSUMER_NAME).has_pact_with(
        Provider(pact_settings.PACT_PROVIDER_NAME),
        host_name=pact_settings.PACT_MOCK_HOST,
        port=pact_settings.PACT_MOCK_PORT,
        pact_dir=pact_settings.PACT_DIR)
    pact.start_service()
    yield pact
    pact.stop_service()

    if not request.node.testsfailed:
        push_to_broker(pact_settings.PACT_VERSION)


@pytest.mark.asyncio
async def test_get_conversation_not_found(pact, conversation_client: ConversationService):
    """
    test get conversation not found
    :param pact:
    :param conversation_client:
    :return:
    """
    conversation_id = UUID('743f98e3-ea37-483e-9b9c-9909a48063c4')

    (pact
     .given('Conversation does not exist')
     .upon_receiving(f'a request for conversation with id : {conversation_id}')
     .with_request('get', f"/conversations/{conversation_id}")
     .will_respond_with(404, headers={'Content-Type': 'application/json'}))

    with pact:
        result = await conversation_client.get_conversation(str(conversation_id), conversation_id)
    assert result is not None


@pytest.mark.asyncio
async def test_get_conversation_found(pact, conversation_client: ConversationService):
    """
    test get conversation found
    :param pact:
    :param conversation_client:
    :return:
    """
    conversation_answers_str = json.dumps(conversation_answers.dict(), default=str)
    conversation_answers_dict = json.loads(conversation_answers_str)
    (pact
     .given('Conversation exist')
     .upon_receiving(f'a request for conversation with id : {conversation_answers.id}')
     .with_request('get', f"/conversations/{conversation_answers.id}")
     .will_respond_with(200, body=SomethingLike(conversation_answers_dict),
                        headers={'Content-Type': 'application/json'}))

    with pact:
        result = await conversation_client.get_conversation(user_id="user",
                                                            conversation_id=conversation_answers.id)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_all_conversations_user_not_found(pact, conversation_client: ConversationService):
    """
    test get all conversation for a not found user
    :param pact:
    :param conversation_client:
    :return:
    """
    user_id = UUID('743f98e3-ea37-483e-9b9c-9909a48063c4')
    workspace_id = uuid4()
    (pact
     .given('User not Found')
     .upon_receiving(f'a request for getting all conversations')
     .with_request('get', f"/conversations", headers={'user-id': str(user_id), "workspace-id": str(workspace_id)})
     .will_respond_with(200, headers={'Content-Type': 'application/json'}))

    with pact:
        result = await conversation_client.get_available_conversations_per_user(str(user_id), workspace_id=workspace_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_all_conversations_user_found_without_data(pact, conversation_client: ConversationService):
    """
    test get all conversations for a found user without data
    :param pact:
    :param conversation_client:
    :return:
    """
    user_id = UUID('743f98e3-ea37-483e-9b9c-9909a48063c4')
    workspace_id = uuid4()
    (pact
     .given('Conversation list not found')
     .upon_receiving(f'a request for getting all conversations of an existing user')
     .with_request('get', f"/conversations", headers={'user-id': str(user_id), "workspace-id": str(workspace_id)})
     .will_respond_with(200, body=Like([]),
                        headers={'Content-Type': 'application/json'}))

    with pact:
        result = await conversation_client.get_available_conversations_per_user(str(user_id), workspace_id=workspace_id)
    assert isinstance(result, List)


@pytest.mark.asyncio
async def test_get_all_conversations_user_found_with_data(pact, conversation_client: ConversationService):
    """
    test get conversations for an existing user with data
    :param pact:
    :param conversation_client:
    :return:
    """
    user_id = SomethingLike('943f98e3-ea37-483e-9b9c-9909a48063c4')
    workspace_id = uuid4()
    conversation_answers_str = json.dumps(conversation_output.dict(by_alias=True), default=str)
    conversation_answers_dict = json.loads(conversation_answers_str)
    (pact
     .given('Conversation list found')
     .upon_receiving(f'a request for getting all conversations for an existing user')
     .with_request('get', f"/conversations", headers={'user-id': user_id, "workspace-id": str(workspace_id)})
     .will_respond_with(200, body=SomethingLike([conversation_answers_dict]),
                        headers={'Content-Type': 'application/json'}))
    with pact:
        result = await conversation_client.get_available_conversations_per_user(str(user_id), workspace_id=workspace_id)
    assert isinstance(result, List)
