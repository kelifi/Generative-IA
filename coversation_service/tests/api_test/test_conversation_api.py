import datetime
import json
from unittest import mock

from fastapi.encoders import jsonable_encoder

from main import app
from source.exceptions.service_exceptions import ConversationFetchDataError, ConversationValidationError, \
    ConversationNotFoundError, SourceDocumentsFetchDataError, SourceDocumentsValidationError, \
    ModelServiceConnectionError, ClassificationModelRetrievalError
from source.schemas.conversation_schema import ConversationIdSchema, ConversationTitleSchema, ConversationSchema, \
    SourceDocumentsInput, SourceWebInput, QuestionInputSchema, QuestionSchema
from source.services.conversation_service import ConversationService
from tests.fixtures import client
from tests.test_data import (conversation_uuid, input_conversation, user_id, conv_schema, chat, source_schema1,
    source_schema2, web_source_schema1, web_source_schema2, current_time, workspace_id)

service_mock = mock.Mock(spec=ConversationService)


def test_create_conversation(client):
    service_mock.create_conversation.return_value = ConversationIdSchema(id=conversation_uuid)
    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations", data=json.dumps(input_conversation.dict()),
                               headers={'user-id': user_id, 'workspace-id': str(workspace_id)})
        assert response.status_code == 200
        assert response.json() == {'id': str(conversation_uuid)}


def test_wrong_schema_on_create_conversation(client):
    service_mock.create_conversation.return_value = ConversationIdSchema(id=conversation_uuid)
    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations", data={'query': 'title'},
                               headers={'user-id': user_id, 'workspace-id': str(workspace_id)})
        assert response.status_code == 422


def test_missing_user_on_create_conversation(client):
    service_mock.create_conversation.return_value = ConversationIdSchema(id=conversation_uuid)
    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations", data=json.dumps(input_conversation.dict()))
        assert response.status_code == 422


def test_successful_get_conversations(client):
    service_mock.get_conversations_per_user.return_value = [conv_schema]
    with app.container.conversation_service.override(service_mock):
        response = client.get("/conversations", headers={'user-id': user_id, 'workspace-id': str(workspace_id)})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0].get('id') == str(conv_schema.id)
        assert data[0].get('title') == str(conv_schema.title)


def test_missing_user_id_on_get_conversations(client):
    service_mock.get_conversations_per_user.return_value = [conv_schema]
    with app.container.conversation_service.override(service_mock):
        response = client.get("/conversations")
        assert response.status_code == 422


def test_get_available_conversations_unexpected_exception(client):
    service_mock.get_conversations_per_user.side_effect = ConversationFetchDataError()

    with app.container.conversation_service.override(service_mock):
        response = client.get("/conversations", headers={'user-id': user_id, 'workspace-id': str(workspace_id)})
        assert response.status_code == 500
        assert response.json() == {"detail": f"Cannot fetch conversation for user {user_id}!"}


def test_get_available_conversations_unvalid_schema_exception(client):
    service_mock.get_conversations_per_user.side_effect = ConversationValidationError()

    with app.container.conversation_service.override(service_mock):
        response = client.get("/conversations", headers={'user-id': user_id, 'workspace-id': str(workspace_id)})
        assert response.status_code == 422
        assert response.json() == {"detail": f"Cannot validate Schema!"}


def test_get_existing_conversation(client):
    # Assuming an existing conversation ID

    # Assuming the service returns a response with the conversation details
    service_mock.get_conversation_by_id.return_value = chat

    with app.container.conversation_service.override(service_mock):
        response = client.get(f"/conversations/{conversation_uuid}", headers={'user-id': user_id})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data.get('questions')) > 0
        questions_data = data.get('questions')
        assert questions_data[0].get('id') == str(chat.questions[0].id)
        assert questions_data[0].get('content') == str(chat.questions[0].content)

        answer_object = questions_data[0].get('answer')
        assert answer_object.get('updatedAt') == jsonable_encoder(current_time)
        assert answer_object.get('edited') == False


def test_get_non_existing_conversation(client):
    non_existing_conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e7'

    service_mock.get_conversation_by_id.side_effect = ConversationNotFoundError()

    with app.container.conversation_service.override(service_mock):
        response = client.get(f"/conversations/{non_existing_conversation_id}", headers={'user-id': user_id})
        assert response.status_code == 404


def test_wrong_schema_get_conversation(client):
    service_mock.get_conversation_by_id.side_effect = ConversationValidationError()

    with app.container.conversation_service.override(service_mock):
        response = client.get(f"/conversations/{conversation_uuid}", headers={'user-id': user_id})
        assert response.status_code == 422


def test_db_error_get_conversation(client):
    service_mock.get_conversation_by_id.side_effect = ConversationFetchDataError()

    with app.container.conversation_service.override(service_mock):
        response = client.get(f"/conversations/{conversation_uuid}", headers={'user-id': user_id})
        assert response.status_code == 500


def test_delete_conversation_success(client):
    # Assuming an existing conversation ID
    service_mock.delete_conversation.return_value = None
    with app.container.conversation_service.override(service_mock):
        response = client.delete(f"/conversations/{conversation_uuid}")
        assert response.status_code == 200


def test_delete_non_existing_conversation(client):
    # Assuming a non-existing conversation ID
    non_existing_conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e7'

    # Assuming the service raises a NoResultFound exception
    service_mock.delete_conversation.side_effect = ConversationNotFoundError()

    with app.container.conversation_service.override(service_mock):
        response = client.delete(f"/conversations/{non_existing_conversation_id}")
        assert response.status_code == 404


def test_delete_conversation_fetch_data_error(client):
    conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_conversation_service = mock.Mock(spec=ConversationService)
    mock_conversation_service.delete_conversation.side_effect = ConversationFetchDataError()

    with app.container.conversation_service.override(mock_conversation_service):
        response = client.delete(f"/conversations/{conversation_id}")
        assert response.status_code == 500
        assert response.json() == {"detail": "Database error when trying to delete conversation!"}


def test_update_conversation_success(client):
    # Assuming an existing conversation ID

    # Assuming the new conversation title to be updated
    new_conversation_title = ConversationTitleSchema(title='Updated Conversation')

    # Assuming the service returns the updated conversation data
    updated_conversation_data = {
        "id": conversation_uuid,
        "title": "Updated Conversation",
        "creationTime": "2023-07-26T14:19:39.199142",
        "updateTime": "2023-07-26T14:19:51.623821",
        "userId": user_id
        # Add additional fields as needed
    }
    service_mock.update_conversation_title.return_value = ConversationSchema(**updated_conversation_data)

    with app.container.conversation_service.override(service_mock):
        response = client.put(f"/conversations/{conversation_uuid}",
                              data=json.dumps(new_conversation_title.dict()))
        assert response.status_code == 200
        data = response.json()
        assert data.get('creationTime') == updated_conversation_data.get('creationTime')
        assert data.get('title') == updated_conversation_data.get('title')
        assert data.get('id') == str(updated_conversation_data.get('id'))
        assert data.get('userId') == updated_conversation_data.get('userId')


def test_update_non_existing_conversation(client):
    # Assuming a non-existing conversation ID
    non_existing_conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e7'

    # Assuming the new conversation title to be updated
    new_conversation_title = ConversationTitleSchema(title='Updated Conversation')

    # Assuming the service raises a NoResultFound exception
    service_mock.update_conversation_title.side_effect = ConversationNotFoundError

    with app.container.conversation_service.override(service_mock):
        response = client.put(f"/conversations/{non_existing_conversation_id}",
                              data=json.dumps(new_conversation_title.dict()))
        assert response.status_code == 404


def test_database_error_update_conversation(client):
    # Assuming a non-existing conversation ID

    # Assuming the new conversation title to be updated
    new_conversation_title = ConversationTitleSchema(title='Updated Conversation')

    # Assuming the service raises a NoResultFound exception
    service_mock.update_conversation_title.side_effect = ConversationFetchDataError

    with app.container.conversation_service.override(service_mock):
        response = client.put(f"/conversations/{conversation_uuid}",
                              data=json.dumps(new_conversation_title.dict()))
        assert response.status_code == 500


def test_create_sources_success(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    source_documents_data = SourceDocumentsInput(similar_docs=[source_schema1, source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_source_documents.return_value = [source_schema1, source_schema2]

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/sources?question_id={existing_question_id}",
                               data=json.dumps(source_documents_data.dict()))
        assert response.status_code == 200


def test_create_sources_missing_question_id(client):
    # Assuming valid source document data
    source_documents_data = SourceDocumentsInput(similar_docs=[source_schema1, source_schema2])
    service_mock.create_source_documents.return_value = [source_schema1, source_schema2]
    with app.container.conversation_service.override(service_mock):
        response = client.post("/conversations/sources", data=json.dumps(source_documents_data.dict()))
    assert response.status_code == 422


def test_database_error_on_create_sources(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    source_documents_data = SourceDocumentsInput(similar_docs=[source_schema1, source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_source_documents.side_effect = SourceDocumentsFetchDataError

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/sources?question_id={existing_question_id}",
                               data=json.dumps(source_documents_data.dict()))
        assert response.status_code == 500


def test_schema_validation_on_create_sources(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    source_documents_data = SourceDocumentsInput(similar_docs=[source_schema1, source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_source_documents.side_effect = SourceDocumentsValidationError

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/sources?question_id={existing_question_id}",
                               data=json.dumps(source_documents_data.dict()))
        assert response.status_code == 422


def test_create_web_sources_success(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    web_source_documents_data = SourceWebInput(web_sources=[web_source_schema1, web_source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_web_sources.return_value = [web_source_schema1, web_source_schema2]

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/web-sources?question_id={existing_question_id}",
                               data=json.dumps(web_source_documents_data.dict()))
        assert response.status_code == 200


def test_create_web_sources_missing_question_id(client):
    # Assuming valid source document data
    web_source_documents_data = SourceWebInput(web_sources=[web_source_schema1, web_source_schema2])
    service_mock.create_web_sources.return_value = [web_source_schema1, web_source_schema2]
    with app.container.conversation_service.override(service_mock):
        response = client.post("/conversations/web-sources", data=json.dumps(web_source_documents_data.dict()))
    assert response.status_code == 422


def test_database_error_on_create_web_sources(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    web_source_documents_data = SourceWebInput(web_sources=[web_source_schema1, web_source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_web_sources.side_effect = SourceDocumentsFetchDataError

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/web-sources?question_id={existing_question_id}",
                               data=json.dumps(web_source_documents_data.dict()))
        assert response.status_code == 500


def test_schema_validation_on_create_web_sources(client):
    # Assuming an existing question ID
    existing_question_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    # Assuming valid source document data to be created
    source_documents_data = SourceWebInput(web_sources=[web_source_schema1, web_source_schema2])

    # Assuming the service returns a successful response (e.g., 201 Created)
    service_mock.create_web_sources.side_effect = SourceDocumentsValidationError

    with app.container.conversation_service.override(service_mock):
        response = client.post(f"/conversations/web-sources?question_id={existing_question_id}",
                               data=json.dumps(source_documents_data.dict()))
        assert response.status_code == 422


def test_create_question_success(client):
    question_input = QuestionInputSchema(question="What is the purpose of life?")
    conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_conversation_service = mock.Mock(spec=ConversationService)
    mock_conversation_service.create_question.return_value = QuestionSchema(id="6c439586-82a7-4f85-8c63-e38d6a8c6007",
                                                                            content="What is the purpose of life?",
                                                                            creation_date=datetime.datetime.now())

    with app.container.conversation_service.override(mock_conversation_service):
        response = client.post(
            f"/conversations/question?conversation-id={conversation_id}&skip_doc=false&skip_web=false",
            data=json.dumps(question_input.dict()))
        assert response.status_code == 200
        assert response.json().get("id") == "6c439586-82a7-4f85-8c63-e38d6a8c6007"
        assert response.json().get("content") == "What is the purpose of life?"


def test_create_question_missing_conversation(client):
    question_input = QuestionInputSchema(question="What is the purpose of life?")
    conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_conversation_service = mock.Mock(spec=ConversationService)
    mock_conversation_service.create_question.side_effect = ModelServiceConnectionError(
        "Oops! can't classify question.")
    mock_conversation_service.create_question.side_effect = ConversationFetchDataError()

    with app.container.conversation_service.override(mock_conversation_service):
        response = client.post(
            f"/conversations/question?conversation-id={conversation_id}&skip_doc=false&skip_web=false",
            data=json.dumps(question_input.dict()))
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal error when creating a new question!"}


def test_create_question_validation_error(client):
    question_input = QuestionInputSchema(question="What is the purpose of life?")
    conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_conversation_service = mock.Mock(spec=ConversationService)
    mock_conversation_service.create_question.side_effect = ConversationValidationError()

    with app.container.conversation_service.override(mock_conversation_service):
        response = client.post(
            f"/conversations/question?conversation-id={conversation_id}&skip_doc=false&skip_web=false",
            data=json.dumps(question_input.dict()))
        assert response.status_code == 422
        assert response.json() == {"detail": "Failed to parse question schema!"}


def test_create_question_classification_model_error(client):
    question_input = QuestionInputSchema(question="What is the purpose of life?")
    conversation_id = '6c439586-82a7-4f85-8c63-e38d6a8c62e8'

    mock_conversation_service = mock.Mock(spec=ConversationService)
    mock_conversation_service.create_question.side_effect = ClassificationModelRetrievalError()

    with app.container.conversation_service.override(mock_conversation_service):
        response = client.post(
            f"/conversations/question?conversation-id={conversation_id}&skip_doc=false&skip_web=false",
            data=json.dumps(question_input.dict()))
        assert response.status_code == 503
        assert response.json() == {'detail': 'Could not get classification model'}
