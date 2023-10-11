from uuid import UUID

from fastapi.encoders import jsonable_encoder

from source.models.enums import RequestMethod
from source.schemas.api_schemas import WorkspaceModelsSchema
from source.schemas.common import UpdateStatusDataModel
from source.schemas.workspace_schemas import WorkspaceInput, WorkspaceOutput, \
    WorkspaceUsersApiModel, WorkspaceTypeOutputModel, GenericWorkspacesResponseModel
from source.utils.utils import make_request


class WorkspaceService:
    def __init__(self, config: dict) -> None:
        self.config = config

    async def get_workspaces_by_user_id(self, user_id: str) -> GenericWorkspacesResponseModel:
        """
        Returns a WorkspaceByUserApiResponseModel containing a list of available workspaces for the connected user
        :param user_id:
        :return: WorkspaceByUserApiResponseModel
        """
        headers = {
            "user-id": user_id
        }
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/workspaces/users",
            method=RequestMethod.GET,
            headers=headers
        )

    async def get_all_workspaces(self) -> GenericWorkspacesResponseModel:
        """
        Returns a WorkspaceByUserApiResponseModel containing a list of available workspaces for the connected user
        :return: WorkspaceByUserApiResponseModel
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/workspaces",
            method=RequestMethod.GET,
        )

    async def get_users_in_workspace(self, workspace_id: UUID) -> dict:
        """
        Retrieve a dictionary containing information about users in a specific workspace.

        Args:
            workspace_id (UUID): The unique identifier of the workspace.

        Returns:
            dict: A dictionary containing user information from the workspace.

        Raises:
            Exception: Any exceptions raised during the request to the conversation service.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/{workspace_id}/users",
            method=RequestMethod.GET,
        )

    async def create_workspace(self, workspace: WorkspaceInput) -> WorkspaceOutput:
        """
        Create a new workspace with the provided data.

        Args:
            workspace (WorkspaceInput): The data related to the workspace to be created.

        Returns:
            WorkspaceOutput: An instance of WorkspaceOutput representing the created workspace.

        Raises:
            Exception: Any exceptions raised during the request to the conversation service.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri="/workspaces",
            method=RequestMethod.POST,
            body=jsonable_encoder(workspace.dict())
        )

    async def update_workspace(self, workspace_id: UUID, workspace_data: WorkspaceInput) -> UpdateStatusDataModel:
        """
        Update workspace with the provided data.

        Args:
            workspace_data (WorkspaceInput): The data related to the workspace to be updated.
            workspace_id (UUID): id of workspace

        Returns:
            UpdateStatusDataModel: An instance of UpdateStatusDataModel representing the status of the update

        Raises:
            Exception: Any exceptions raised during the request to the conversation service.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/{workspace_id}",
            method=RequestMethod.PATCH,
            body=jsonable_encoder(workspace_data.dict())
        )

    async def delete_workspace(self, workspace_id: UUID) -> UpdateStatusDataModel:
        """
        Delete a  workspace by id

        Args:
            workspace_id (UUID): id of workspace

        Returns:
            UpdateStatusDataModel: An instance of UpdateStatusDataModel representing the status of the deleted workspace

        Raises:
            Exception: Any exceptions raised during the request to the conversation service.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/{workspace_id}",
            method=RequestMethod.DELETE)

    async def get_workspace_by_id(self, workspace_id: UUID) -> dict:
        """
        Get workspace data by id

        Args:
            workspace_id (UUID): id of workspace

        Returns:
            WorkspaceOutput: An instance of WorkspaceOutput representing the created workspace.

        Raises:
            Exception: Any exceptions raised during the request to the conversation service.
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/{workspace_id}",
            method=RequestMethod.GET
        )

    async def assign_users_to_workspace(self, workspace_users: WorkspaceUsersApiModel, workspace_id: UUID) -> bool:
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/{workspace_id}/users",
            method=RequestMethod.POST,
            body=workspace_users.dict(),
        )

    async def get_workspace_types(self) -> WorkspaceTypeOutputModel:
        """
        Get list of available workspace types
        """
        return await make_request(
            service_url=self.config["CONVERSATION_SERVICE_URL"],
            uri=f"/workspaces/types",
            method=RequestMethod.GET,
        )

    async def get_workspace_models(self, workspace_type: str) -> WorkspaceModelsSchema:
        """Get models corresponding to the workspace type"""
        models_endpoint = self.config.get("MODELS_ENDPOINT")
        return WorkspaceModelsSchema(
            models=await make_request(
                service_url=self.config.get("CONVERSATION_SERVICE_URL"),
                uri=f"{models_endpoint}/types?workspace_type={workspace_type}",
                method=RequestMethod.GET,
            ))
