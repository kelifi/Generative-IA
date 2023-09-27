from uuid import UUID

from pydantic import ValidationError

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceFetchDataError, \
    WorkspaceAlreadyExist, WorkspaceCreationError, WorkspaceNotFoundError, DuplicateAssignmentError
from source.exceptions.validation_exceptions import GenericValidationError
from source.repositories.workspace_repository import WorkspaceRepository
from source.schemas.workspace_schema import WorkspaceDto, WorkspaceInput, WorkspaceOutput
from source.models.workspace_models import Workspace


class WorkspaceService:
    """
    Service class for handling workspaces for users.
    """

    def __init__(self,
                 workspace_repository: WorkspaceRepository,
                 ):
        """
        Initialize the WorkspaceService.

        Args:
            workspace_repository (WorkspaceRepository): The workspace repository to use.
        """
        self._workspace_repository = workspace_repository

    def get_workspaces_by_user(self, user_id: UUID) -> list[WorkspaceDto]:
        """
        returns a list of workspaces per user
        Args:
            user_id: The user id used to get workspaces.
        """
        try:

            return [WorkspaceDto.from_orm(workspace) for workspace in
                    self._workspace_repository.get_workspaces_by_user(user_id=user_id)]
        except DatabaseConnectionError:
            logger.error("error getting workspace")
            raise WorkspaceFetchDataError('Unable to get list of workspaces, database error')

    def get_all_workspaces(self) -> list[WorkspaceDto]:
        """
        Retrieve a list of all workspaces.

        Returns:
            list[WorkspaceDto]: A list of WorkspaceDto objects representing the retrieved workspaces.

        Raises:
            WorkspaceFetchDataError: If there is an error while fetching workspace data from the database.
        """
        try:
            return [WorkspaceDto.from_orm(workspace) for workspace in
                    self._workspace_repository.get_all_workspaces()]
        except DatabaseConnectionError:
            logger.error("error getting all workspaces")
            raise WorkspaceFetchDataError('Unable to get list of workspaces, database error')

    def get_workspace_users(self, workspace_id: UUID) -> list[str]:
        """
        Retrieve a list of user IDs for a specific workspace.

        Args:
            workspace_id (UUID): The UUID of the workspace.

        Returns:
            list[UUID]: A list of UUIDs representing the users associated with the workspace.

        Raises:
            WorkspaceFetchDataError: If there is an error while fetching user data for the workspace from the database.
        """
        try:
            users_ids = self._workspace_repository.get_workspace_users(workspace_id=workspace_id)
            return [str(user_workspace.user_id) for user_workspace in users_ids]
        except DatabaseConnectionError:
            logger.error("error getting all workspaces")
            raise WorkspaceFetchDataError('Unable to get list of workspaces, database error')

    def create_workspace(self, workspace_data: WorkspaceInput) -> WorkspaceOutput:
        """
        Create a new workspace with the provided workspace data.

        Args:
            workspace_data (WorkspaceDto): The workspace data to be created.

        Returns:
            Workspace: the newly created workspace.

        Raises:
            WorkspaceFetchDataError: If there is an issue creating the workspace, including cases where
                a workspace with the same name already exists or a database error occurs.
        """
        try:
            workspace = Workspace(**dict(workspace_data))
            return self._workspace_repository.create_workspace(workspace)
        except DatabaseConnectionError:
            logger.error("error creating a workspace")
            raise WorkspaceFetchDataError(message='Unable to create workspace, database error')
        except WorkspaceAlreadyExist:
            logger.error("error workspace already exist")
            raise WorkspaceCreationError(message='workspace with same name already exist')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError

    def assign_users_to_workspace(self, users_ids: list[UUID], workspace_id: UUID) -> bool:
        """
        Assign a user to a workspace.

        Args:
            users_ids (list[UUID]): The UUID of the user to be assigned.
            workspace_id (UUID): The UUID of the workspace to which the user should be assigned.

        Returns:
            bool: True if the user was successfully assigned to the workspace, False otherwise.

        Raises:
            WorkspaceFetchDataError: If there is a database error while performing the assignment.
            WorkspaceCreationError: If the specified workspace does not exist.

        """
        try:
            return self._workspace_repository.assign_users_to_workspace(workspace_id=workspace_id, users_ids=users_ids)
        except DatabaseConnectionError:
            logger.error("error validating result")
            raise WorkspaceFetchDataError(message='Unable to assign user to workspace')
        except WorkspaceNotFoundError:
            logger.error("error validating result")
            raise WorkspaceCreationError(message='workspace does not exist')
        except DuplicateAssignmentError:
            logger.error("error workspace already exist")
            raise WorkspaceCreationError(message='workspace already assigned for that user')

