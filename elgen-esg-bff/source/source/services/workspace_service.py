from source.models.enums import RequestMethod
from source.schemas.workspace_schemas import WorkspaceByUserApiResponseModel
from source.utils.utils import make_request


class WorkspaceService:
    def __init__(self, config: dict) -> None:
        self.config = config

    async def get_workspaces_by_user_id(self, user_id: str) -> WorkspaceByUserApiResponseModel:
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
            uri="/workspaces",
            method=RequestMethod.GET,
            headers=headers
        )
