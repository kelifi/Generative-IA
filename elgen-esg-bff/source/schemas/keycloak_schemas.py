import datetime
from enum import Enum
from typing import List, Dict
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from configuration.config import KeyCloakServiceConfiguration
from source.utils.utils import CamelModel


class UserLimits(CamelModel):
    conversations_init: List[int] = Field([KeyCloakServiceConfiguration().DEFAULT_RATE_LIMIT],
                                          description="List of initial conversation values")
    questions_init: List[int] = Field([KeyCloakServiceConfiguration().DEFAULT_RATE_LIMIT],
                                      description="List of initial question values")


class ConversationInfo(UserLimits):
    conversations_date: List[str] | None = Field([str(datetime.datetime.now().strftime("%Y-%m-%d"))],
                                                 alias="conversationsDate",
                                                 description="List of conversation dates")
    conversations_limit: List[int] | None = Field([KeyCloakServiceConfiguration().DEFAULT_RATE_LIMIT],
                                                  alias="conversationsLimit",
                                                  description="List of conversation limits")
    questions_date: List[str] | None = Field([str(datetime.datetime.now().strftime("%Y-%m-%d"))],
                                             alias="questionsDate",
                                             description="List of question dates")
    questions_limit: List[int] | None = Field([KeyCloakServiceConfiguration().DEFAULT_RATE_LIMIT],
                                              alias="questionsLimit",
                                              description="List of question limits")


class LoginModel(CamelModel):
    id: str = Field(..., description="User ID")
    token: str = Field(..., description="Access Token")
    refresh_token: str = Field(..., description="Refresh Token")
    token_type: str = Field(..., description="Token Type")
    expires_in: str = Field(..., description="Access Token Expiration Time")
    refresh_expires_in: str = Field(..., description="Refresh Token Expiration Time")


class LoginData(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """
    Keycloak login request Model
    """
    client_id: str = Field(..., description="Client ID of the Keycloak client")
    client_secret: str = Field(..., description="Client secret of the Keycloak client")
    username: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    grant_type: str = Field(..., description="Type of grant for authentication")

    @classmethod
    def from_configuration(cls, user_login: LoginData, configuration_dict: dict):
        return cls(
            client_id=configuration_dict['KEYCLOAK_CLIENT_ID'],
            client_secret=configuration_dict['KEYCLOAK_CLIENT_SECRET'],
            username=user_login.email,
            password=user_login.password,
            grant_type=configuration_dict['GRANT_TYPE']
        )


class RefreshTokenRequest(BaseModel):
    """
    Keycloak login request Model
    """
    client_id: str = Field(..., description="Client ID of the Keycloak client")
    client_secret: str = Field(..., description="Client secret of the Keycloak client")
    refresh_token: str = Field(..., description="Client refresh token")
    grant_type: str = Field(..., description="Type of grant for authentication")

    @classmethod
    def from_configuration(cls, refresh_token: str, configuration_dict: dict):
        """
        create refresh token object
        :param refresh_token:
        :param configuration_dict:
        :return:
        """
        return cls(
            client_id=configuration_dict.get('KEYCLOAK_CLIENT_ID'),
            client_secret=configuration_dict.get('KEYCLOAK_CLIENT_SECRET'),
            refresh_token=refresh_token,
            grant_type=configuration_dict.get('REFRESH_GRANT_TYPE')
        )


class Role(str, Enum):
    """
    Keycloak roles
    """
    admin = "admin"
    user = "user"


class ClientRole(str, Enum):
    """
    Client roles
    """
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

    def __str__(self):
        return self.value


class BaseUserModel(CamelModel):
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email_verified: bool | None = Field(True, description="Flag indicating if user's email is verified")
    client_roles: dict | None = Field(None, example={
        KeyCloakServiceConfiguration().KEYCLOAK_CLIENT_ID: [ClientRole.USER]
    })
    role: ClientRole | None = None


class UserInfo(BaseUserModel):
    user_actual_limits: ConversationInfo | None = Field(None, alias="attributes",
                                                        description="Additional user_default_limits for the user")


class UserInfoWorkspace(UserInfo):
    id: UUID | str | None = Field(None, description="User ID")


class PlatformUsers(BaseModel):
    users: list[UserInfoWorkspace] = Field(default_factory=lambda: [], description="list of all platform users")


class UserInfoWorkspaceAPIResponse(BaseModel):
    users: list[UserInfoWorkspace] = Field([], description="list of users in a workspace")


class UserRegistrationData(BaseUserModel):
    user_default_limits: UserLimits | None = Field(None, alias="attributes",
                                                   description="Additional user_default_limits for the user")


class UserInfoRegistration(UserRegistrationData):
    """
    Keycloak user information model
    """
    password: str | None

    @classmethod
    def from_dict(cls, user_info: dict):
        return cls(**user_info)


class KeycloakTokenInfo(BaseModel):
    exp: int | None = Field(..., description="The expiration time of the token (Unix timestamp)")
    iat: int | None = Field(..., description="The time when the token was issued (Unix timestamp)")
    jti: UUID | None = Field(..., description="The unique identifier for the token")
    iss: str | None = Field(..., description="The issuer of the token")
    aud: str | None = Field(None, description="The intended audience for the token")
    sub: UUID | None = Field(...,
                             description="The subject identifier, typically representing the user associated with the token")
    typ: str | None = Field(..., description="The token type (e.g., 'Bearer')")
    azp: str | None = Field(...,
                            description="The authorized party, representing the client application that requested the token.")
    preferred_username: str | None = Field(..., description="The preferred username of the user.")
    email_verified: bool | None = Field(..., description="Indicates if the user's email has been verified.")
    acr: str | None = Field(..., description="The authentication context class reference.")
    realm_access: Dict | None = Field(None,
                                      description="Roles assigned to the realm (server-level) in which the user resides.")
    resource_access: Dict | None = Field(...,
                                         description="Roles assigned to specific resources (e.g., client applications) for the user.")
    scope: str | None = Field(..., description="The scopes associated with the token.")
    client_id: str | None = Field(default=None, description="The ID of the client application.")
    clientHost: str | None = Field(default=None, description="The host of the client application.")
    clientAddress: str | None = Field(default=None, description="The IP address of the client application.")
    username: str = Field(..., description="The username of the user.")
    active: bool = Field(..., description="Indicates if the token is active or valid.")

    @property
    def is_active(self):
        return self.active


class RegisterModel(UserInfo):
    """
    Keycloak Registration model
    """
    username: EmailStr = Field(..., description="User's email address used as username")
    enabled: bool = Field(True, description="Flag indicating if the user is enabled")
    credentials: list = Field(..., description="List of user credentials")
    required_actions: list = Field([], description="List of required actions for the user")
    user_actual_limits: ConversationInfo | None = Field(None, alias="attributes",
                                                        description="Additional user_default_limits for the user")

    @classmethod
    def from_user_info(cls, user_info: UserInfoRegistration):
        return cls(
            email=user_info.email, first_name=user_info.first_name, email_verified=user_info.email_verified,
            enabled=True, last_name=user_info.last_name, username=user_info.email,
            user_actual_limits=user_info.user_default_limits,
            client_roles=user_info.client_roles,
            credentials=[
                {"temporary": False, "type": "password",
                 "value": user_info.password}]
        )


class UserCreationBulkRequest(CamelModel):
    if_resource_exists: str = Field("SKIP", description="a flag for keycloak to skip existing users")
    realm: str = Field(KeyCloakServiceConfiguration().REALM, description="keycloak realm")
    users: list[RegisterModel] = Field(None, description="list of returned created users")


class KeycloakPartialImportResult(CamelModel):
    action: str = Field(..., description="action related to keycloak internally, for example, ADD")
    resource_type: str = Field(..., description="resource type for keycloak")
    resource_name: str = Field(..., description="resource name for keycloak")
    id: UUID = Field(..., description="id of the result (can be user, etc...)")


class KeycloakPartialImportResponse(CamelModel):
    overwritten: int
    added: int
    skipped: int
    results: list[KeycloakPartialImportResult]


class UserCreationBulkResponse(CamelModel):
    detail: str = Field("User created succesfully!", description="details clarifying the result")
    user_id: UUID = Field(..., description="created user id")


class TokenValidationModel(BaseModel):
    client_id: str = Field(..., description="Client ID of the Keycloak client")
    client_secret: str = Field(..., description="Client secret of the Keycloak client")
    token: str = Field(..., description="The token to be validated")

    @classmethod
    def from_configuration_dict(cls, config_dict: dict, token: str):
        return cls(client_id=config_dict['ADMIN_CLIENT_ID'],
                   client_secret=config_dict['ADMIN_CLIENT_SECRET'], token=token)


class UserGroupRequest(CamelModel):
    realm: str
    user_id: str
    group_id: str


class RequestHeader:
    urlencoded = "application/x-www-form-urlencoded"
    json = "application/json"


class KeycloakAttribute(str, Enum):
    CONVERSATIONS = 'conversations'
    QUESTIONS = 'questions'


class AdminTokenModel(BaseModel):
    """
    Admin token request model
    """
    client_id: str = Field(..., description="Client ID of the Keycloak client")
    client_secret: str = Field(..., description="Client secret of the Keycloak client")
    grant_type: str = Field("client_credentials", description="Type of grant for authentication")

    @classmethod
    def from_configuration_dict(cls, config_dict: dict):
        return cls(client_id=config_dict['ADMIN_CLIENT_ID'],
                   client_secret=config_dict['ADMIN_CLIENT_SECRET'])


class UserEncrypted(CamelModel):
    user_data: str = Field(..., description="the user data defined for login/signup")
