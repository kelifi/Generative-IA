from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound

from configuration.logging_setup import logger
from source.exceptions.service_exceptions import DatabaseConnectionError, WorkspaceFetchDataError, \
    WorkspaceAlreadyExist, WorkspaceCreationError, WorkspaceNotFoundError, DuplicateAssignmentError, \
    WorkspaceTypeFetchDataError, WorkspaceTypeAlreadyExist, WorkspaceTypeCreationError, SourceDataFetchError, \
    SourceTypeFetchDataError
from source.exceptions.validation_exceptions import GenericValidationError
from source.models.workspace_models import Workspace, WorkspaceType
from source.repositories.workspace_repository import WorkspaceRepository
from source.repositories.workspace_type_repository import WorkspaceTypeRepository
from source.schemas.source_schema import SourceOutputModel
from source.schemas.workspace_schema import WorkspaceDto, WorkspaceInput, WorkspaceOutput, WorkspaceTypeModel, \
    WorkspaceTypeInput, WorkspaceTypeOutputModel, WorkspaceConfigOutputModel, GenericWorkspaceInfo
from source.services.source_service import SourceService


class WorkspaceService:
    """
    Service class for handling workspaces for users.
    """

    def __init__(self,
                 workspace_repository: WorkspaceRepository,
                 workspace_type_repository: WorkspaceTypeRepository,
                 source_service: SourceService
                 ):
        """
        Initialize the WorkspaceService.

        Args:
            workspace_repository (WorkspaceRepository): The workspace repository to use.
        """
        self._workspace_repository = workspace_repository
        self._workspace_type_repository = workspace_type_repository
        self.source_service = source_service

    def get_workspaces_by_user(self, user_id: UUID) -> list[GenericWorkspaceInfo]:
        """
        returns a list of workspaces per user
        Args:
            user_id: The user id used to get workspaces.
        """
        try:
            result = []
            for workspace in self._workspace_repository.get_workspaces_by_user(user_id=user_id):
                workspace.available_model_codes = workspace.available_model_codes.split(",")
                type_data = self.get_workspace_type_by_id(workspace.type_id)
                workspace_data = WorkspaceDto.from_orm(workspace)
                result.append(GenericWorkspaceInfo(**workspace_data.dict(), workspace_type=type_data))
            return result
        except DatabaseConnectionError:
            logger.error("error getting workspace")
            raise WorkspaceFetchDataError('Unable to get list of workspaces, database error')

    async def get_all_workspaces(self) -> list[GenericWorkspaceInfo]:
        """
        Retrieve a list of all workspaces.

        Returns:
            list[WorkspaceBasicInfo]: A list of WorkspaceDto objects representing the retrieved workspaces.

        Raises:
            WorkspaceFetchDataError: If there is an error while fetching workspace data from the database.
        """
        try:
            result = []
            for workspace in self._workspace_repository.get_all_workspaces():
                if workspace.available_model_codes:
                    workspace.available_model_codes = workspace.available_model_codes.split(",")
                type_data = self.get_workspace_type_by_id(workspace.type_id)
                workspace_data = WorkspaceDto.from_orm(workspace)
                result.append(GenericWorkspaceInfo(**workspace_data.dict(), workspace_type=type_data))
            return result
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

    async def create_workspace(self, workspace_data: WorkspaceInput) -> WorkspaceOutput:
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
            workspace_data.available_model_codes = ",".join(workspace_data.available_model_codes)
            workspace = Workspace(**workspace_data.dict(exclude={"source_id"}))
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

    async def update_workspace(self, workspace_data: WorkspaceInput, workspace_id: UUID) -> bool:
        """
        Update workspace data by id

        Args:
            workspace_id (UUID): The UUID of the workspace.
            workspace_data (WorkspaceInput): new data

        Returns:
            True if workspace is successfully updated
        """
        try:
            workspace_data = WorkspaceDto(id=workspace_id, **workspace_data.dict(exclude={"source_id"}))
            return await self._workspace_repository.update_workspace(workspace_data, workspace_id)
        except NoResultFound:
            logger.error(f"Workspace with id {workspace_id} is not found ")
            raise WorkspaceNotFoundError('Unable to get workspace, database error')
        except DatabaseConnectionError:
            logger.error("error getting workspace")
            raise WorkspaceFetchDataError('Unable to update workspace, database error')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError(model_name="Workspace")

    async def delete_workspace(self, workspace_id: UUID) -> bool:
        """
        Delete workspace by id : deactivate the workspace
        Args:
            workspace_id (UUID): The UUID of the workspace.


        Returns:
            True if workspace is successfully updated
        """

        try:
            return await self._workspace_repository.delete_workspace(workspace_id)
        except DatabaseConnectionError:
            logger.error("error deleting workspace")
            raise WorkspaceFetchDataError('Unable to delete workspace, database error')
        except NoResultFound:
            logger.error(f"Workspace with id {workspace_id} is not found ")
            raise WorkspaceNotFoundError('Unable to delete workspace, database error')

    async def get_workspace_by_id(self, workspace_id: UUID) -> WorkspaceConfigOutputModel:
        """
        Get workspace data by id

        Args:
            workspace_id (UUID): The UUID of the workspace.

        Returns:
            Workspace fetched data
        """
        try:
            workspace_data = self._workspace_repository.get_workspace_by_id(workspace_id)
            workspace_data.available_model_codes = workspace_data.available_model_codes.split(",")
        except (DatabaseConnectionError, AttributeError):
            logger.error("error getting workspace")
            raise WorkspaceFetchDataError('Unable to get workspace, database error')
        try:
            type_data = self.get_workspace_type_by_id(workspace_data.type_id)
        except (GenericValidationError, WorkspaceTypeFetchDataError):
            type_data = None
        try:
            source_type_data = self.source_service.get_source_type_by_id(workspace_data.source_type_id)
        except (GenericValidationError, SourceTypeFetchDataError):
            source_type_data = None
        try:
            source = await self.source_service.get_source_by_workspace_id(workspace_data.id)
            source_data = SourceOutputModel(**source.dict())
        except (GenericValidationError, SourceDataFetchError, AttributeError):
            source_data = None
        return WorkspaceConfigOutputModel(workspace_type=type_data,
                                          source_type=source_type_data,
                                          source=source_data,
                                          **WorkspaceDto.from_orm(workspace_data).dict()
                                          )

    def assign_users_to_workspace(self, users_ids: list[str], workspace_id: UUID) -> bool:
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

    def get_workspace_types(self) -> WorkspaceTypeOutputModel:
        """
        Get list of available workspaces

        Returns:
            list of workspace types
        """
        try:
            types = self._workspace_type_repository.get_workspace_types()
            return WorkspaceTypeOutputModel(
                data=[WorkspaceTypeModel.from_orm(workspace_type) for workspace_type in types])
        except DatabaseConnectionError:
            logger.error(f'Failed to get list of workspace types due to database issue')
            raise WorkspaceTypeFetchDataError(message='Unable to get list of types for workspace')

    def create_workspace_type(self, workspace_type: WorkspaceTypeInput) -> UUID:
        """
        Create new workspace type
        Args:
            workspace_type (list[WorkspaceTypeInput]): New workspace type data

        Returns:
            Data of workspace type created
        """
        try:
            workspace = WorkspaceType(**dict(workspace_type))
            return self._workspace_type_repository.create_workspace_type(workspace)
        except DatabaseConnectionError:
            logger.error("error creating a workspace")
            raise WorkspaceTypeFetchDataError(message='Unable to create workspace type')
        except WorkspaceTypeAlreadyExist:
            logger.error("error workspace type already exist")
            raise WorkspaceTypeCreationError(message='workspace with same name already exist')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError("Invalid result")

    def get_workspace_type_by_id(self, type_id: UUID) -> WorkspaceTypeModel:
        """
        Get workspace type by id
        Args:
            type_id : type id
        Returns:
            Data of workspace type
        """
        try:
            return WorkspaceTypeModel.from_orm(self._workspace_type_repository.get_workspace_type_per_id(type_id))
        except DatabaseConnectionError:
            logger.error("error when getting a workspace type")
            raise WorkspaceTypeFetchDataError(message='Unable to get workspace type')
        except ValidationError:
            logger.error("error validating result")
            raise GenericValidationError("Invalid result")

    def get_workspace_type(self, workspace_id) -> WorkspaceTypeModel | None:
        """
        Get workspace type by id
        Args:
            workspace_id (UUID): The UUID of the workspace type.

        Returns:
            Data of workspace type created
        """
        try:
            return WorkspaceTypeModel.from_orm(self._workspace_repository.get_workspace_type(workspace_id))
        except DatabaseConnectionError:
            logger.error("error creating a workspace")
            raise WorkspaceTypeFetchDataError(message='Unable to get workspace type')
