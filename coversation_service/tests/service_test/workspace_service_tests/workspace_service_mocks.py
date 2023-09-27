from uuid import UUID

from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceAlreadyExist, WorkspaceNotFoundError
from source.models.workspace_models import Workspace
from tests.test_data import workspaces_orm_object, mock_workspace_output


class MockResponse:
    def __init__(self, json_data: dict | str | None, text: str | None, status_code: int):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text

    def json(self) -> dict | str | None:
        return self.json_data


def mock_returned_workspaces_by_user(self, user_id: UUID) -> list[Workspace]:
    return workspaces_orm_object


def mock_returned_all_workspaces(self) -> list[Workspace]:
    return workspaces_orm_object


def mock_error_get_all_workspaces(self):
    raise DatabaseConnectionError("Database connection error")


def mock_create_workspace_success(self, workspace_data: Workspace):
    return mock_workspace_output


def mock_create_workspace_already_exist(self, workspace_data: Workspace):
    raise WorkspaceAlreadyExist


def mock_create_workspace_db_connection_failure(self, workspace_data: Workspace):
    raise DatabaseConnectionError


def mock_assign_user_to_workspace(self, workspace_id: str, users_ids: str) -> bool:
    return True


def mock_assign_user_to_workspace_not_found(self, workspace_id: str, users_ids: str) -> WorkspaceNotFoundError:
    raise WorkspaceNotFoundError
