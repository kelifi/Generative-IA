import pytest

from source.exceptions.service_exceptions import WorkspaceFetchDataError, WorkspaceCreationError
from source.repositories.workspace_repository import WorkspaceRepository
from tests.fixtures import test_workspace_service
from tests.service_test.workspace_service_tests.workspace_service_mocks import mock_returned_workspaces_by_user, \
    mock_returned_all_workspaces, mock_error_get_all_workspaces, mock_create_workspace_success, \
    mock_create_workspace_already_exist, mock_create_workspace_db_connection_failure, mock_assign_user_to_workspace, \
    mock_assign_user_to_workspace_not_found
from tests.test_data import user_id, workspaces_data_object, mock_workspace_input, mock_workspace_output, workspace_id


def test_workspaces_per_user(test_workspace_service, monkeypatch):
    """Test if getting user conversations is successful"""
    monkeypatch.setattr(WorkspaceRepository, "get_workspaces_by_user", mock_returned_workspaces_by_user)
    assert test_workspace_service.get_workspaces_by_user(user_id) == workspaces_data_object


def test_get_all_workspaces_success(test_workspace_service, monkeypatch):
    """Test if getting all workspaces is successful"""
    monkeypatch.setattr(WorkspaceRepository, "get_all_workspaces", mock_returned_all_workspaces)
    workspaces = test_workspace_service.get_all_workspaces()

    assert isinstance(workspaces, list)
    assert len(workspaces) == 2
    assert workspaces == workspaces_data_object


def test_get_all_workspaces_failure(test_workspace_service, monkeypatch):
    """Test if getting all workspaces is failed"""
    monkeypatch.setattr(WorkspaceRepository, "get_all_workspaces", mock_error_get_all_workspaces)
    with pytest.raises(WorkspaceFetchDataError):
        test_workspace_service.get_all_workspaces()


def test_create_workspace_success(test_workspace_service, monkeypatch):
    """Test create workspace succeeded"""
    monkeypatch.setattr(WorkspaceRepository, "create_workspace", mock_create_workspace_success)
    result = test_workspace_service.create_workspace(mock_workspace_input)
    assert result.id == mock_workspace_output.id


def test_create_workspace_failure_already_exist(test_workspace_service, monkeypatch):
    """Test  create workspace already exist"""
    monkeypatch.setattr(WorkspaceRepository, "create_workspace", mock_create_workspace_already_exist)
    with pytest.raises(WorkspaceCreationError):
        test_workspace_service.create_workspace(mock_workspace_input)


def test_create_workspace_failure_db_connection(test_workspace_service, monkeypatch):
    """Test  create workspace failed because of db connection"""
    monkeypatch.setattr(WorkspaceRepository, "create_workspace", mock_create_workspace_db_connection_failure)
    with pytest.raises(WorkspaceFetchDataError):
        test_workspace_service.create_workspace(mock_workspace_input)


def test_assign_user_to_workspace_success(test_workspace_service, monkeypatch):
    """Test assign user to a workspace succeeded"""
    monkeypatch.setattr(WorkspaceRepository, "assign_users_to_workspace", mock_assign_user_to_workspace)
    result = test_workspace_service.assign_users_to_workspace(workspace_id=workspace_id, users_ids=[user_id])
    assert result


def test_assign_user_to_workspace_failure_not_found(test_workspace_service, monkeypatch):
    """Test assign user to a workspace failed and not found"""
    monkeypatch.setattr(WorkspaceRepository, "assign_users_to_workspace", mock_assign_user_to_workspace_not_found)
    with pytest.raises(WorkspaceCreationError):
        test_workspace_service.assign_users_to_workspace(workspace_id=workspace_id, users_ids=[user_id])

