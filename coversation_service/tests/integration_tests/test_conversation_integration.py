from uuid import UUID

import pytest
from fastapi import status

from source.helpers.db_helpers import DBHelper
from source.schemas.chat_schema import QuestionPurposeResponse
from source.services.model_service import ModelService
from tests.fixtures import client, scope_session
from tests.integration_tests.data_model_mock import random_user_id
from tests.test_data import input_conversation, user_id, sources_to_add, web_sources_to_add
from tests.utils import assert_custom_equality_between_objects


@pytest.mark.comment(
    "This test will not check the returned value but instead check if it is a valid UUID as it is generated automatically")
def test_int_create_conversation(client, scope_session, monkeypatch):
    """Assert a conversation was created successfully"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.post(f"/conversations", json=input_conversation.dict(),
                           headers={'user-id': user_id})

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(UUID(response.json().get('id')), UUID)


def test_int_get_conversation_empty(client, scope_session, monkeypatch):
    """Test getting an empty conversation for a user not in the database"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.get("/conversations", headers={'user-id': user_id})

    assert response.status_code == status.HTTP_200_OK
    assert not response.json()


def test_int_get_conversation_non_empty(client, scope_session, monkeypatch):
    """test getting the available conversation for a certain user"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.get("/conversations", headers={'user-id': random_user_id})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {'title': 'Conversation 3', 'id': '4bf1e1df-498c-4f51-b289-fbfccf4bd6a5', 'creationTime': '2023-08-03T15:19:36',
         'updateTime': '2023-08-01T15:19:36'},
        {'title': 'Conversation 2', 'id': 'a970dfb8-8be8-4e0e-927a-54247aece9c2', 'creationTime': '2023-08-02T15:19:36',
         'updateTime': '2023-08-01T15:19:36'},
        {'title': 'Conversation 1', 'id': '0e16b7a6-d396-45fc-be6f-16f43882d09b', 'creationTime': '2023-08-01T15:19:36',
         'updateTime': '2023-08-01T15:19:36'}]


def test_int_create_specific_question(client, scope_session, monkeypatch):
    """Test creating a question that is specific"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)

    monkeypatch.setattr(ModelService, "request_question_classification_model",
                        lambda self, question: QuestionPurposeResponse(is_specific=True))
    response = client.post(
        f"/conversations/question?conversation-id=0e16b7a6-d396-45fc-be6f-16f43882d09b&skip_doc=false&skip_web=false",
        json={"question": "what is an esg report?"})

    expected = {'answer': None, 'content': 'what is an esg report?', 'creation_date': '2023-08-29T16:52:41.595872',
                'id': 'ba73833e-9f3d-4057-9914-abdaeb68643f', 'localSources': [], 'skip_doc': False, 'skip_web': False,
                'webSources': []}

    assert response.status_code == status.HTTP_200_OK
    assert_custom_equality_between_objects(object1=response.json(), object2=expected,
                                           fields_to_exclude=['id', 'creation_date'])


def test_int_create_generic_question(client, scope_session, monkeypatch):
    """Test creation a question that is generic (not specific)"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)

    # Mock the call to the classification model
    monkeypatch.setattr(ModelService, "request_question_classification_model",
                        lambda self, question: QuestionPurposeResponse(is_specific=False))
    response = client.post(
        f"/conversations/question?conversation-id=0e16b7a6-d396-45fc-be6f-16f43882d09b&skip_doc=false&skip_web=false",
        json={"question": "Hello"})
    expected = {'answer': None, 'content': 'Hello', 'creation_date': '2023-08-29T16:52:41.595872',
                'id': 'ba73833e-9f3d-4057-9914-abdaeb68643f', 'localSources': [], 'skip_doc': True, 'skip_web': True,
                'webSources': []}

    assert response.status_code == status.HTTP_200_OK
    assert_custom_equality_between_objects(object1=response.json(), object2=expected,
                                           fields_to_exclude=['id', 'creation_date'])


def test_int_create_sources(client, scope_session, monkeypatch):
    """test creating sources in db, we will ignore id and date"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.post(
        f"/conversations/sources?question_id=0e16b7a6-d396-45fc-be6f-16f43882d09b",
        json=sources_to_add)
    expected = [{'id': '97552ea4-8ca1-4ed5-a454-4980f9e88cf7', 'content': 'This is the content of the document 1',
                 'link': 'document1.pdf', 'fileName': None, 'creationTime': '2023-09-04T10:34:47.041288',
                 'documentType': 'pdf', 'fileId': 'd6e8b8a5-8fb6-4d48-9763-ff6c22c0e6e1', 'downloadLink': None},
                {'id': 'd24aa74b-0012-4b21-97f2-7b65b3793e12', 'content': 'This is the content of the document 2',
                 'link': 'document2.pdf', 'fileName': None, 'creationTime': '2023-09-04T10:34:47.045976',
                 'documentType': 'pdf', 'fileId': 'bd05bbae-5832-470d-8f75-4e291215ee07', 'downloadLink': None}]
    assert response.status_code == status.HTTP_200_OK
    assert_custom_equality_between_objects(object1=response.json(), object2=expected,
                                           fields_to_exclude=['id', 'creationTime'])


def test_int_create_web_sources(client, scope_session, monkeypatch):
    """test creating web sources in db, we will ignore id and date"""
    monkeypatch.setattr(DBHelper, "create_db_local_session", scope_session)
    response = client.post(
        f"/conversations/web-sources?question_id=0e16b7a6-d396-45fc-be6f-16f43882d09b",
        json=web_sources_to_add)
    expected = [
        {'id': 'ff3111a3-a8e3-4155-86d8-b9a9e3d527a3', 'url': 'url1', 'description': 'description1', 'title': 'title1',
         'paragraphs': 'long paragraphs for first web sources'},
        {'id': 'ee844e6d-0d8b-4fc3-85cd-2a815ce93118', 'url': 'url2', 'description': 'description2', 'title': 'title2',
         'paragraphs': 'long paragraphs for second web sources'}]
    assert response.status_code == status.HTTP_200_OK
    assert_custom_equality_between_objects(object1=response.json(), object2=expected, fields_to_exclude=['id'])
