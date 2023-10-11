import json

import pytest
from fastapi import status, HTTPException

from source.exceptions.custom_exceptions import UserRolesNotDefined, KeycloakError, UserAlreadyExistException
from source.schemas.keycloak_schemas import UserInfoWorkspaceAPIResponse
from source.schemas.workspace_schemas import WorkspaceOutput
from source.services.keycloak_service import KeycloakService
from source.services.workspace_service import WorkspaceService
from tests.conftest import test_client
from tests.test_data import (mock_token_not_dict, mock_get_workspaces_by_user_id,
                             mock_check_role_user_success, mock_get_users_by_workspace_id, mock_get_workspace_users,
                             workspace_id, user_info_workspace, mock_create_workspace, workspace_input,
                             workspace_output, mock_assign_users_to_workspace, workspace_users_response_api_response,
                             mock_get_workspace_types, dummy_workspace_types, mock_get_workspace_models,
                             dummy_workspace_models, mock_get_workspace_by_id, mock_check_role_admin,
                             mock_get_all_workspaces, mock_workspace_updated, mock_update_workspace,
                             mock_delete_workspace, mock_workspace_deleted)


@pytest.mark.asyncio
async def test_get_available_workspaces_for_super_admin(test_client, monkeypatch):
    """test getting the available workspaces for super admin"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)

    monkeypatch.setattr(WorkspaceService, "get_all_workspaces", mock_get_all_workspaces)

    result = test_client.get(url="/workspaces",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_available_workspaces(test_client, monkeypatch):
    """test getting the available workspaces for non super admin"""

    def mock_check_role_super_admin_failure(*args, **kwargs):
        raise HTTPException(detail="You are not allowed to do this action",
                            status_code=status.HTTP_403_FORBIDDEN)

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_super_admin_failure)
    monkeypatch.setattr(WorkspaceService, "get_workspaces_by_user_id", mock_get_workspaces_by_user_id)

    result = test_client.get(url="/workspaces",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_users_in_workspace(test_client, monkeypatch):
    """test getting the users in a workspace"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_users_in_workspace", mock_get_users_by_workspace_id)
    monkeypatch.setattr(KeycloakService, "get_workspace_users", mock_get_workspace_users)

    result = test_client.get(url=f"/workspaces/{workspace_id}/users",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.status_code == status.HTTP_200_OK
    assert UserInfoWorkspaceAPIResponse(**result.json()) == UserInfoWorkspaceAPIResponse(users=[user_info_workspace])


@pytest.mark.asyncio
async def test_get_users_in_workspace_fail_user_role_not_defined(test_client, monkeypatch):
    """test getting the users in a workspace"""

    def mock_create_workspace_failure(*args, **kwargs):
        raise UserRolesNotDefined()

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_create_workspace_failure)
    monkeypatch.setattr(WorkspaceService, "get_users_in_workspace", mock_get_users_by_workspace_id)
    monkeypatch.setattr(KeycloakService, "get_workspace_users", mock_get_workspace_users)

    result = test_client.get(url=f"/workspaces/{workspace_id}/users",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_users_in_workspace_fail_keycloak_error(test_client, monkeypatch):
    """test getting the users in a workspace"""

    def mock_create_workspace_failure(*args, **kwargs):
        raise KeycloakError(401, "keycloak error")

    monkeypatch.setattr(KeycloakService, "check_auth", mock_create_workspace_failure)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_users_in_workspace", mock_get_users_by_workspace_id)
    monkeypatch.setattr(KeycloakService, "get_workspace_users", mock_get_workspace_users)

    result = test_client.get(url=f"/workspaces/{workspace_id}/users",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_users_in_workspace_fail_user_already_exists(test_client, monkeypatch):
    """test getting the users in a workspace"""

    def mock_create_workspace_failure(*args, **kwargs):
        raise UserAlreadyExistException(401)

    monkeypatch.setattr(KeycloakService, "check_auth", mock_create_workspace_failure)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_users_in_workspace", mock_get_users_by_workspace_id)
    monkeypatch.setattr(KeycloakService, "get_workspace_users", mock_get_workspace_users)

    result = test_client.get(url=f"/workspaces/{workspace_id}/users",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_unavailable_users_in_workspace(test_client, monkeypatch):
    """test getting the users that are not in a workspace"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_users_in_workspace", mock_get_users_by_workspace_id)
    monkeypatch.setattr(KeycloakService, "get_workspace_non_included_users", mock_get_workspace_users)

    result = test_client.get(url=f"/workspaces/{workspace_id}/users/unavailable",
                             headers={"Authorization": "Bearer dummy_token"},
                             )

    assert result.status_code == status.HTTP_200_OK
    assert UserInfoWorkspaceAPIResponse(**result.json()) == UserInfoWorkspaceAPIResponse(users=[user_info_workspace])


@pytest.mark.asyncio
async def test_assign_users_to_workspace(test_client, monkeypatch):
    """test assign users to workspace"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "assign_users_to_workspace", mock_assign_users_to_workspace)

    result = test_client.post(url=f"/workspaces/{workspace_id}/users",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=workspace_users_response_api_response.dict()
                              )

    assert result.status_code == status.HTTP_200_OK
    assert result.json() == {"success": True}


@pytest.mark.asyncio
async def test_create_workspace(test_client, monkeypatch):
    """ test create workspace """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "create_workspace", mock_create_workspace)

    result = test_client.post(url="/workspaces",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=workspace_input.dict()
                              )
    assert result.status_code == status.HTTP_200_OK
    assert WorkspaceOutput(**result.json()) == workspace_output


@pytest.mark.asyncio
async def test_update_workspace(test_client, monkeypatch):
    """ test update workspace """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "update_workspace", mock_update_workspace)

    result = test_client.patch(url=f"/workspaces/{workspace_id}",
                               headers={"Authorization": "Bearer dummy_token"},
                               json=workspace_input.dict()
                               )
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == json.loads(mock_workspace_updated.json())


@pytest.mark.asyncio
async def test_delete_workspace(test_client, monkeypatch):
    """ test delete workspace """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "delete_workspace", mock_delete_workspace)

    result = test_client.delete(url=f"/workspaces/{workspace_id}",
                                headers={"Authorization": "Bearer dummy_token"},
                                )
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == json.loads(mock_workspace_deleted.json())


@pytest.mark.asyncio
async def test_create_workspace_fail_user_role_not_defined(test_client, monkeypatch):
    """ test create workspace """

    def mock_create_workspace_failure(*args, **kwargs):
        raise UserRolesNotDefined()

    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_create_workspace_failure)
    monkeypatch.setattr(WorkspaceService, "create_workspace", mock_create_workspace)

    result = test_client.post(url="/workspaces",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=workspace_input.dict()
                              )
    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_workspace_fail_keycloak_error(test_client, monkeypatch):
    """ test create workspace """

    def mock_create_workspace_failure(*args, **kwargs):
        raise KeycloakError(401, "keycloak error")

    monkeypatch.setattr(KeycloakService, "check_auth", mock_create_workspace_failure)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "create_workspace", mock_create_workspace)

    result = test_client.post(url="/workspaces",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=workspace_input.dict()
                              )
    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_workspace_fail_user_already_exists(test_client, monkeypatch):
    """ test create workspace """

    async def mock_create_workspace_failure(*args, **kwargs):
        raise UserAlreadyExistException(401)

    monkeypatch.setattr(KeycloakService, "check_auth", mock_create_workspace_failure)

    result = test_client.post(url="/workspaces",
                              headers={"Authorization": "Bearer dummy_token"},
                              json=workspace_input.dict()
                              )
    assert result.is_error
    assert result.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_available_workspace_type(test_client, monkeypatch):
    """ test Get workspace types"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_workspace_types", mock_get_workspace_types)

    result = test_client.get(url="/workspaces/types",
                             headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_workspace_types


@pytest.mark.asyncio
async def test_get_available_workspace_models(test_client, monkeypatch):
    """ test Get workspace types"""
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_user_success)
    monkeypatch.setattr(WorkspaceService, "get_workspace_models", mock_get_workspace_models)

    result = test_client.get(url="/workspaces/models",
                             headers={"Authorization": "Bearer dummy_token"},
                             params={"workspaceType": "chat"}
                             )
    assert result.status_code == status.HTTP_200_OK
    assert result.json() == dummy_workspace_models


@pytest.mark.asyncio
async def test_get_workspace_by_id(test_client, monkeypatch):
    """ test Get workspace by id """
    monkeypatch.setattr(KeycloakService, "check_auth", mock_token_not_dict)
    monkeypatch.setattr(KeycloakService, "check_user_role", mock_check_role_admin)
    monkeypatch.setattr(WorkspaceService, "get_workspace_by_id", mock_get_workspace_by_id)

    result = test_client.get(url=f"/workspaces/{workspace_id}",
                             headers={"Authorization": "Bearer dummy_token"})
    assert result.status_code == status.HTTP_200_OK
