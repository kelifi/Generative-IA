import json
from unittest import mock

from fastapi import status

from main import app
from source.exceptions.service_exceptions import WorkspaceFetchDataError, WorkspaceCreationError
from source.services.workspace_service import WorkspaceService
from tests.fixtures import client
from tests.test_data import user_id, workspaces_data_object, mock_workspace_input, \
    workspace_users_ids, workspace_output_instance

service_mock = mock.Mock(spec=WorkspaceService)


def test_get_workspaces_by_user_api(client):
    service_mock.get_workspaces_by_user.return_value = workspaces_data_object
    with app.container.workspace_service.override(service_mock):
        response = client.get("/workspaces/users",
                              headers={'user-id': user_id})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data.get("workspaces"), list)
        assert len(data) > 0


def test_empty_list_of_workspaces_by_user_from_service(client):
    service_mock.get_workspaces_by_user.return_value = []
    with app.container.workspace_service.override(service_mock):
        response = client.get("/workspaces/users", headers={'user-id': user_id})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data.get("workspaces"), list)
        assert len(data.get("workspaces")) == 0


def test_get_all_workspaces(client):
    service_mock.get_all_workspaces.return_value = workspaces_data_object
    with app.container.workspace_service.override(service_mock):
        response = client.get("/workspaces")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data.get("workspaces"), list)
        assert len(data) > 0


def test_get_all_workspaces_error_fetching_data(client):
    service_mock.get_all_workspaces.side_effect = WorkspaceFetchDataError()
    with app.container.workspace_service.override(service_mock):
        response = client.get("/workspaces")
        assert response.is_error
        assert response.status_code == 500


def test_create_workspace_success(client):
    service_mock.create_workspace.return_value = workspace_output_instance
    with app.container.workspace_service.override(service_mock):
        response = client.post("/workspaces", data=json.dumps(mock_workspace_input.dict()))
        assert response.status_code == 200
        assert response.json() == workspace_output_instance.dict()


def test_create_workspace_failure_creation(client):
    service_mock.create_workspace.side_effect = WorkspaceCreationError()
    with app.container.workspace_service.override(service_mock):
        response = client.post("/workspaces", data=json.dumps(mock_workspace_input.dict()))
        assert response.is_error
        assert response.status_code == 500


def test_create_workspace_failure_fetch_data(client):
    service_mock.create_workspace.side_effect = WorkspaceFetchDataError()
    with app.container.workspace_service.override(service_mock):
        response = client.post("/workspaces", data=json.dumps(mock_workspace_input.dict()))
        assert response.is_error
        assert response.status_code == 500


def test_assign_user_to_workspace_success(client):
    service_mock.assign_users_to_workspace.return_value = True
    with app.container.workspace_service.override(service_mock):
        response = client.post("/workspaces/4d8b5dbf-188a-4fb0-9eab-18ad833c7a3a/users",
                               data=json.dumps(workspace_users_ids.dict()))
        assert response.status_code == 200
        assert response.json() == True


def test_assign_user_to_workspace_not_found(client):
    service_mock.assign_users_to_workspace.side_effect = WorkspaceCreationError()
    with app.container.workspace_service.override(service_mock):
        response = client.post("/workspaces/4d8b5dbf-188a-4fb0-9eab-18ad833c7a3a/users",
                               data=json.dumps(workspace_users_ids.dict()))
        assert response.status_code == 404
        assert response.json() == {'detail': 'workspace already exist'}
