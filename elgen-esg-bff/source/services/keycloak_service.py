import base64
import json
import logging
import os
from datetime import datetime, date
from typing import Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, Response
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from pydantic import ValidationError

from configuration.config import app_config
from source.exceptions.api_exceptions import UserNotFoundApiException, KeycloakInternalApiException
from source.exceptions.custom_exceptions import WrongCredentials, UserNotFound, UserAlreadyExistException, \
    KeycloakError, SessionNotFound, UserInformationFormatError, UserRolesNotDefined, AttributesError, \
    MissingUserInformation, DataEncryptionError
from source.helpers.keycloack_helper import format_login_keycloak_response, format_user_info
from source.models.enums import RequestMethod, LimitType
from source.schemas.common import AcknowledgeResponse, AcknowledgeTypes
from source.schemas.keycloak_schemas import LoginData, LoginModel, RequestHeader, LoginRequest, UserInfo, \
    AdminTokenModel, \
    RegisterModel, KeycloakAttribute, ConversationInfo, KeycloakTokenInfo, TokenValidationModel, UserInfoRegistration, \
    RefreshTokenRequest, ClientRole, UserCreationBulkRequest, KeycloakPartialImportResponse, UserCreationBulkResponse, \
    UserInfoWorkspace
from source.schemas.source_schemas import SourceLimitSchema
from source.utils.utils import NotOkServiceResponse, make_request


class KeycloakService:
    def __init__(self, keycloak_service_configuration: dict) -> None:
        self.keycloak_service_configuration = keycloak_service_configuration
        self.request_base_path = (f"{self.keycloak_service_configuration['SERVER_URL']}/admin/realms/"
                                  f"{self.keycloak_service_configuration['REALM']}")

    async def _get_keycloak_endpoints_configuration(self) -> dict:
        """
        Returns Keycloak Open ID Connect configuration
        :returns: dict: Open ID Configuration
        """
        return await make_request(
            service_url=self.keycloak_service_configuration['SERVER_URL'],
            uri=f"/realms/{self.keycloak_service_configuration['REALM']}/.well-known/openid-configuration",
            headers={'Content-Type': RequestHeader.json}, method=RequestMethod.GET)

    async def login(self, user_login: LoginData) -> LoginModel:
        """
        If the username and password of this user are correct, user is logged in and returns all the information
        related to its token.
        Else
        """
        configurations = await self._get_keycloak_endpoints_configuration()
        response = await make_request(
            service_url=configurations.get("token_endpoint"),
            uri="",
            keycloak_request_option=True,
            headers={'Content-Type': RequestHeader.urlencoded},
            method=RequestMethod.POST,
            body=jsonable_encoder(LoginRequest.from_configuration(user_login, self.keycloak_service_configuration)))
        if isinstance(response, NotOkServiceResponse):
            logging.error(f"Login failed {json.loads(response.body)}")
            raise WrongCredentials(status.HTTP_400_BAD_REQUEST, json.loads(response.body))
        try:
            return format_login_keycloak_response(response)
        except (ValidationError, KeyError, AttributesError):
            logging.error("error getting all user infos from keycloak")
            raise KeycloakError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="error getting user infos")

    async def get_token_infos(self, token: str) -> KeycloakTokenInfo:
        """
        get token information's
        :param token: access token
        :return: KeycloakTokenInfo
        """
        response = await make_request(
            service_url=self.keycloak_service_configuration['SERVER_URL'],
            uri=f"/realms/{self.keycloak_service_configuration['REALM']}/protocol/openid-connect/token/introspect",
            headers={'Content-Type': RequestHeader.urlencoded},
            keycloak_request_option=True,
            method=RequestMethod.POST,
            body=jsonable_encoder(
                TokenValidationModel.from_configuration_dict(self.keycloak_service_configuration, token))
        )
        if isinstance(response, NotOkServiceResponse):
            logging.error("error getting user infos")
            raise KeycloakError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="error getting user infos")

        try:
            return KeycloakTokenInfo(**response)
        except ValidationError:
            logging.error("Error validating user info response")
            raise KeycloakError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="error getting user infos")

    @staticmethod
    def check_token_auth(token_infos: KeycloakTokenInfo) -> bool:
        """
        return True if authorized else return False
        :param token_infos: token information's
        :return: bool
        """
        return token_infos.is_active

    async def check_auth(self, credentials: HTTPAuthorizationCredentials) -> KeycloakTokenInfo:
        """
        check if user is authorized or not
        :param credentials: The HTTP authorization credentials.
        :return: The payload containing the token information.
        """
        token = credentials.credentials
        try:
            payload = await self.get_token_infos(token)
        except KeycloakError as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token information") from error
        if not self.check_token_auth(payload):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user is not active")
        return payload

    async def check_logout_auth(self, credentials: HTTPAuthorizationCredentials) -> KeycloakTokenInfo:
        """
        check if user is authorized or not
        :param credentials: The HTTP authorization credentials.
        :return: The payload containing the token information.
        """
        return await self.get_token_infos(credentials.credentials)

    async def _get_admin_token(self) -> dict:
        """
        Exchanges client credentials (admin-cli) for an access token.
        :returns: dict: Inplace method that updated the class attribute `_admin_token`
        PS:Is executed on startup and may be executed again if the token validation fails
        """
        return await make_request(
            service_url=(await self._get_keycloak_endpoints_configuration()).get("token_endpoint"),
            uri="",
            headers={'Content-Type': RequestHeader.urlencoded},
            keycloak_request_option=True,
            body=jsonable_encoder(AdminTokenModel.from_configuration_dict(self.keycloak_service_configuration)),
            method=RequestMethod.POST)

    async def create_user(self, user_info: UserInfoRegistration) -> UserCreationBulkResponse:
        """
        Create a new user endpoint
        """
        admin_token = await self._get_admin_token()

        try:
            user_info.user_default_limits = ConversationInfo(
                conversations_init=user_info.user_default_limits.conversations_init,
                conversations_limit=user_info.user_default_limits.conversations_init,
                conversations_date=[str(datetime.today().strftime("%Y-%m-%d"))],
                questions_limit=user_info.user_default_limits.questions_init,
                questions_init=user_info.user_default_limits.questions_init,
                questions_date=[str(datetime.today().strftime("%Y-%m-%d"))])
            data = (UserCreationBulkRequest(users=[RegisterModel.from_user_info(user_info).dict(by_alias=True)])
                    .dict(by_alias=True))
            # keycloak does not accept this field even if it has None
            del data['users'][0]["role"]
            data["users"][0]["createdTimestamp"] = 0
        except (IndexError, ValidationError) as error:
            logger.error(f"There is a change in schema possibly! {error}")
            raise KeycloakError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected Error!",
            ) from error

        response = await make_request(
            service_url=f"{self.request_base_path}",
            uri="partialImport",
            headers={"Content-Type": RequestHeader.json,
                     "Authorization": f"Bearer {admin_token.get('access_token')}"},
            method=RequestMethod.POST,
            keycloak_request_option=True,
            body=json.dumps(data))

        if isinstance(response, NotOkServiceResponse):
            logger.error(f"Error while creating user {json.loads(response.body)}")
            raise KeycloakError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected Error!")
        try:
            response = KeycloakPartialImportResponse(**response)
            user_id = response.results[0].id
        except (ValidationError, IndexError) as error:
            logger.error(f"There is a change in schema possibly! {error}")
            raise KeycloakError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected Error!",
            ) from error

        if response.skipped:
            logger.error("skipping the creation of this user, they exist already")
            raise UserAlreadyExistException(status_code=status.HTTP_409_CONFLICT, detail="User Already exists!")

        return UserCreationBulkResponse(detail="User Created Successfully!", user_id=user_id)

    async def get_user(self, user_id: str = None,
                       user_roles: list[ClientRole] = None,
                       update_attributes_option: bool = True) -> Union[UserInfo, dict]:
        """
        Queries the keycloak API for a specific user either based on its ID or any **native** attribute
        :param user_id: The user ID of interest
        :param user_roles: roles of the user
        :param: query: Query string. e.g. `email=testuser@codespecialist.com` or `username=codespecialist`
        :param update_attributes_option: return the keycloak object response if True else UserInfo
        :returns: KeycloakUser: If the user was found
        """
        admin_token = await self._get_admin_token()
        if isinstance(admin_token, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(admin_token.status_code, json.loads(admin_token.body))

        response = await make_request(
            service_url=self.request_base_path,
            uri=f"/users/{user_id}",
            keycloak_request_option=True,
            headers={
                "Content-Type": RequestHeader.json,
                "Authorization": f"Bearer {admin_token.get('access_token')}",
            },
            method=RequestMethod.GET)

        if isinstance(response, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(response.status_code, json.loads(response.body))
        return format_user_info(response, user_roles=user_roles) if update_attributes_option else response

    async def get_all_users(self):
        admin_token = await self._get_admin_token()
        if isinstance(admin_token, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(admin_token.status_code, json.loads(admin_token.body))

        response = await make_request(
            service_url=self.request_base_path,
            uri="users",
            keycloak_request_option=True,
            headers={
                "Content-Type": RequestHeader.json,
                "Authorization": f"Bearer {admin_token.get('access_token')}",
            },
            method=RequestMethod.GET)

        if isinstance(response, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(response.status_code, json.loads(response.body))
        return [format_user_info(keycloak_response=user,
                                 workspace=True,
                                 user_roles=[ClientRole.USER])
                if user.get('attributes')
                else None for user
                in response]

    async def get_workspace_users(self, users_ids: list) -> list[UserInfoWorkspace]:
        users = await self.get_all_users()
        return [user for user in users if user is not None and getattr(user, 'id', None) in users_ids]

    async def get_workspace_non_included_users(self, users_ids: list) -> list[UserInfoWorkspace]:
        users = await self.get_all_users()
        return [user for user in users if user is not None and getattr(user, 'id', None) not in users_ids]

    async def check_user_limit(self, user_id: str, attribute_to_check: KeycloakAttribute) -> bool:
        """
        check if the user still have the access to create a conversation
        :param user_id:
        :param attribute_to_check: the user attribute to check which is either conversations/questions
        :return:
        """
        user_profile = await self.get_user(user_id)
        try:
            conversation_info = ConversationInfo(**user_profile.user_actual_limits.dict()).dict(by_alias=True)
        except ValidationError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unexpected error occurred !")

        last_date_attr = f'{attribute_to_check}Date'
        limit_attr = f'{attribute_to_check}Limit'
        try:
            last_date = conversation_info[last_date_attr][0]
            limit = int(conversation_info[limit_attr][0])
            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
        except (ValueError, IndexError):
            logging.error("error getting user limits data")
            raise KeycloakInternalApiException
        return (limit > 0 and last_date == date.today()) or (date.today() > last_date)

    async def check_date_limit(self, user_id: str,
                               user_roles: list[ClientRole] = None) -> dict:
        """
        check if the user still have the access to create a conversation
        :param user_roles:
        :param user_id:
        :return:
        """
        admin_token = await self._get_admin_token()
        if isinstance(admin_token, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(admin_token.status_code, json.loads(admin_token.body))
        try:
            user_profile = await self.get_user(user_id=user_id, user_roles=user_roles)
            conversation_info = ConversationInfo(**user_profile.user_actual_limits.dict()).dict(by_alias=True)
            last_date_conversations = conversation_info.get(f'{KeycloakAttribute.CONVERSATIONS}Date')[0]
            last_date_questions = conversation_info.get(f'{KeycloakAttribute.QUESTIONS}Date')[0]
        except (MissingUserInformation, IndexError, ValidationError):
            logging.error("error getting user data from keycloak")
            raise UserInformationFormatError
        last_date_conversations = datetime.strptime(last_date_conversations, "%Y-%m-%d").date()
        last_date_questions = datetime.strptime(last_date_questions, "%Y-%m-%d").date()
        if date.today() > last_date_conversations and date.today() > last_date_questions:
            return await self.reset_user_limits(user_profile, user_id)
        if last_date_questions < date.today() == last_date_conversations:
            return await self.reset_user_limits(user_profile, user_id, LimitType.QUESTIONS)
        if last_date_conversations < date.today() == last_date_questions:
            return await self.reset_user_limits(user_profile, user_id, LimitType.CONVERSATION)

        return user_profile.dict(by_alias=True)

    async def reset_user_limits(self, user_profile: UserInfo, user_id: str,
                                attribute_type: LimitType = None) -> UserInfo:
        """
        reset the user limits in conversations and questions
        :param attribute_type:
        :param user_profile:
        :param user_id:
        :return:
        """
        admin_token = await self._get_admin_token()
        if isinstance(admin_token, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(admin_token.status_code, json.loads(admin_token.body))
        try:
            if attribute_type == LimitType.CONVERSATION:
                user_profile.user_actual_limits.conversations_limit = user_profile.user_actual_limits.conversations_init

            elif attribute_type == LimitType.QUESTIONS:
                user_profile.user_actual_limits.questions_limit = user_profile.user_actual_limits.questions_init
            else:
                user_profile.user_actual_limits.questions_limit = user_profile.user_actual_limits.questions_init
                user_profile.user_actual_limits.conversations_limit = user_profile.user_actual_limits.conversations_init

            user_profile.user_actual_limits.questions_date = [str(date.today())]
            user_profile.user_actual_limits.conversations_date = [str(date.today())]

            response = await make_request(
                service_url=self.request_base_path,
                uri=f"/users/{user_id}",
                body={"email": user_profile.email, "attributes": user_profile.user_actual_limits.dict(by_alias=True)},
                headers={
                    "Content-Type": RequestHeader.json,
                    "Authorization": f"Bearer {admin_token.get('access_token')}",
                },
                method=RequestMethod.PUT
            )
        except (KeyError, TypeError):
            raise UserInformationFormatError

        if isinstance(response, NotOkServiceResponse):
            logger.error("Error updating user limit, user not found")
            raise UserNotFoundApiException(detail="error in updating rate limit")
        return user_profile

    async def update_rate_limit(self, user_id: str, attribute_to_update: KeycloakAttribute,
                                incrementation_condition: bool = False) -> UserInfo:
        """
        update the rate limit defined for user in keycloak
        :param user_id:
        :param attribute_to_update:
        :param incrementation_condition:
        :return:
        """
        admin_token = await self._get_admin_token()

        if isinstance(admin_token, NotOkServiceResponse):
            logger.error("User not found")
            raise UserNotFound(admin_token.status_code, json.loads(admin_token.body))

        user_profile = await self.get_user(user_id=user_id)
        user_attributes = user_profile.user_actual_limits

        try:
            last_date = self._get_last_date(user_attributes, attribute_to_update)
            today_date = date.today()
            if attribute_to_update == KeycloakAttribute.QUESTIONS:
                attribute_value = int(user_attributes.questions_limit[0])
                attribute_limit = int(user_attributes.questions_init[0])
            else:
                attribute_value = int(user_attributes.conversations_limit[0])
                attribute_limit = int(user_attributes.conversations_init[0])
            if attribute_value >= attribute_limit and incrementation_condition:
                raise UserInformationFormatError
            attribute_value = self._update_attribute_limit(attribute_value, incrementation_condition)
            user_attributes = self._update_user_attributes(user_attributes.dict(by_alias=True), attribute_to_update,
                                                           last_date, today_date, attribute_value)
            user_profile.user_actual_limits = ConversationInfo.parse_obj(user_attributes)

            response = await self._make_update_request(admin_token, user_id, user_profile)

            if isinstance(response, NotOkServiceResponse):
                logger.error("Error updating user limit, user not found")
                raise UserNotFoundApiException(detail="error in updating rate limit")

            return user_profile
        except (MissingUserInformation, ValidationError, ValueError, KeyError, IndexError):
            raise UserInformationFormatError

    @staticmethod
    def _get_last_date(user_attributes: ConversationInfo, attribute_to_update: KeycloakAttribute) \
            -> date:
        """
        get the user_default_limits date set in keycloak
        :param user_attributes:
        :param attribute_to_update:
        :return: date set in keycloak
        """
        try:
            last_date_str = user_attributes.dict(by_alias=True).get(f'{attribute_to_update}Date', [str(date.min)])[0]
        except (IndexError, ValueError):
            raise UserInformationFormatError
        return datetime.strptime(last_date_str, '%Y-%m-%d').date()

    @staticmethod
    def _update_attribute_limit(attribute_value: int, incrementation_condition: bool) -> int:
        """
        update limit attribute in keycloak
        :param attribute_value:
        :param incrementation_condition:
        :return: updated value
        """
        return attribute_value + 1 if incrementation_condition else attribute_value - 1

    @staticmethod
    def _update_user_attributes(user_attributes: dict, attribute_to_update: KeycloakAttribute,
                                last_date: date, today_date: date, attribute_value: int) -> dict:
        """
        update all user_default_limits
        :param user_attributes:
        :param attribute_to_update:
        :param last_date:
        :param today_date:
        :param attribute_value:
        :return:
        """
        updated_attributes = user_attributes.copy()
        try:
            if today_date > last_date:
                updated_attributes.update({
                    f'{attribute_to_update}Limit': [int(user_attributes[f'{attribute_to_update}Init'][0]) - 1],
                    f'{attribute_to_update}Date': [str(today_date)]
                })
            else:
                updated_attributes.update({
                    f'{attribute_to_update}Limit': [attribute_value]
                })
            return updated_attributes
        except (KeyError, ValueError, ValidationError):
            raise UserInformationFormatError

    async def _make_update_request(self, admin_token: dict, user_id: str, user_profile: UserInfo) \
            -> dict:
        """
        make the update  of user_default_limits on keycloak
        :param admin_token:
        :param user_id:
        :param user_profile:
        :return:
        """
        try:
            return await make_request(
                service_url=self.request_base_path,
                uri=f"/users/{user_id}",
                body={"email": user_profile.email, "attributes": user_profile.user_actual_limits.dict(by_alias=True)},
                headers={
                    "Content-Type": RequestHeader.json,
                    "Authorization": f"Bearer {admin_token.get('access_token')}",
                },
                method=RequestMethod.PUT
            )
        except KeyError:
            raise MissingUserInformation

    async def get_user_sessions(self, user_id: str) -> dict:
        """
        get the actual user session infos
        :param user_id:
        :return:
        """
        admin_token = await self._get_admin_token()
        return await make_request(
            service_url=self.request_base_path,
            uri=f"/users/{user_id}/sessions",
            headers={
                "Content-Type": RequestHeader.json,
                "Authorization": f"Bearer {admin_token.get('access_token')}",
            },
            method=RequestMethod.GET
        )

    async def logout(self, user_id: str) -> Response:
        """
        delete the user session
        :param user_id:
        :return:
        """
        user_session_ids = await self.get_user_sessions(user_id)
        if not user_session_ids:
            raise SessionNotFound
        try:
            session_id = user_session_ids[0]['id']
        except IndexError:
            raise SessionNotFound
        admin_token = await self._get_admin_token()
        logger.info("kill the active session in keycloak")
        return await make_request(
            service_url=self.request_base_path,
            uri=f"/sessions/{session_id}",
            headers={
                "Content-Type": RequestHeader.json,
                "Authorization": f"Bearer {admin_token.get('access_token')}",
            },
            method=RequestMethod.DELETE
        )

    async def refresh_token(self, credentials: HTTPAuthorizationCredentials) -> LoginModel:
        """
        create new token for the user
        :param credentials:
        :return:
        """
        refresh_token = credentials.credentials
        response = await make_request(
            service_url=(await self._get_keycloak_endpoints_configuration()).get("token_endpoint"),
            uri="",
            keycloak_request_option=True,
            headers={'Content-Type': RequestHeader.urlencoded},
            method=RequestMethod.POST,
            body=jsonable_encoder(RefreshTokenRequest.from_configuration(refresh_token,
                                                                         self.keycloak_service_configuration)))
        if isinstance(response, NotOkServiceResponse):
            logger.error(f"error getting the token: {json.loads(response.body)}")
            raise WrongCredentials(response.status_code, json.loads(response.body))
        try:
            return format_login_keycloak_response(response)
        except ValidationError:
            logging.error("error getting all user infos from keycloak")
            raise KeycloakError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="error getting user infos")

    def get_roles_from_token(self, payload: KeycloakTokenInfo) -> list[ClientRole]:
        return payload.resource_access.get(
            self.keycloak_service_configuration['KEYCLOAK_CLIENT_ID'], {}).get('roles')

    def check_user_role(self, payload: KeycloakTokenInfo, roles_to_check: list[ClientRole]) -> list[ClientRole]:
        """
        Use this method to validate a user given a list of roles to check
        :payload KeycloakTokenInfo:
        :roles_to_check list[ClientRole]:
        """
        try:
            user_current_roles = self.get_roles_from_token(payload)
            if not user_current_roles:
                raise UserRolesNotDefined(detail="User does not have roles set for them")
            if not bool(set(user_current_roles) & set(roles_to_check)):
                raise HTTPException(detail="You are not allowed to do this action",
                                    status_code=status.HTTP_403_FORBIDDEN)
            return user_current_roles
        except (KeyError, ValueError) as error:
            logger.error(f"unable to parse user roles: {error}")
            raise KeycloakError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="unable to parse user roles") from error

    async def get_sources_configurations(self) -> list[SourceLimitSchema] | NotOkServiceResponse:
        """Get the current sources config from the provided client identified by client_id"""
        admin_token = await self._get_admin_token()
        client_id = self.keycloak_service_configuration.get("CLIENT_ID")
        headers = {
            "Authorization": f"Bearer {admin_token.get('access_token')}"
        }

        response = await make_request(service_url=self.request_base_path,
                                      uri=f"/clients/{client_id}",
                                      headers=headers,
                                      method=RequestMethod.GET)
        if isinstance(response, NotOkServiceResponse):
            return response

        source_config_result = response.get("attributes").get("sourceConfig")

        if not source_config_result:
            logger.error("Cannot extract the fields attributes and sourceConfig from keycloak")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Could not extract or find the configurations sources")

        return json.loads(source_config_result)

    async def extract_source_configurations(self) -> list[SourceLimitSchema]:
        """return the appropriate schema of source limits"""
        sources_config = await self.get_sources_configurations()
        try:
            return [SourceLimitSchema(**data) for data in sources_config]
        except ValidationError as error:
            logger.error(error)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="An error occurred while creating the SourceLimitSchema schema")

    async def update_sources_config(self, sources_config: SourceLimitSchema) -> (
            list[SourceLimitSchema] | NotOkServiceResponse):
        """Update the sources config in the provided client identified by client_id"""
        admin_token = await self._get_admin_token()
        client_id = self.keycloak_service_configuration.get("CLIENT_ID")
        headers = {
            "Authorization": f"Bearer {admin_token.get('access_token')}"
        }
        existing_source_configs = await self.get_sources_configurations()

        # Loop through the available configurations until we find the one corresponding to the provided model name
        for index, existing_source_config in enumerate(existing_source_configs):
            if existing_source_config.get("model_code") == sources_config.model_code:
                # Patch the existing sources config
                existing_source_configs[index].update(sources_config.dict())
                update_request = await make_request(service_url=self.request_base_path,
                                                    uri=f"/clients/{client_id}",
                                                    headers=headers,
                                                    body={"attributes": {
                                                        "sourceConfig": json.dumps(existing_source_configs)}},
                                                    method=RequestMethod.PUT)
                if isinstance(update_request, NotOkServiceResponse):
                    return update_request
                break

        return await self.get_sources_configurations()

    async def add_complete_sources_configuration(self, complete_sources_config: list[SourceLimitSchema]) -> (
            AcknowledgeResponse | NotOkServiceResponse):
        """Add the complete list of sources to keycloak"""

        admin_token = await self._get_admin_token()
        client_id = self.keycloak_service_configuration.get("CLIENT_ID")
        headers = {
            "Authorization": f"Bearer {admin_token.get('access_token')}"
        }
        parsed_sources_input = [elem.dict() for elem in complete_sources_config]
        response = await make_request(service_url=self.request_base_path,
                                      uri=f"/clients/{client_id}",
                                      headers=headers,
                                      body={"attributes": {
                                          "sourceConfig": json.dumps(parsed_sources_input)}},
                                      method=RequestMethod.PUT)
        if isinstance(response, NotOkServiceResponse):
            return response
        logger.warning("Sources configurations in keycloak have been set or overwritten")
        return AcknowledgeResponse(acknowledge=AcknowledgeTypes.SUCCESS)

    @staticmethod
    def decrypt_data(user_data_encrypted: str) -> dict:
        """
        decrypt user data
        :param user_data_encrypted: User encrypted credentials
        :return: decrypted credentials
        """
        secret_key = base64.b64decode(app_config.ENCRYPTION_KEY)
        gcm_encryption = AESGCM(secret_key)

        try:
            decrypted_data = gcm_encryption.decrypt(base64.b64decode(app_config.NONCE_ENCRYPTION_PARAM),
                                                    base64.b64decode(user_data_encrypted), b'')
            return json.loads(decrypted_data.decode('utf8'))
        except (ValueError, InvalidTag):
            logging.error("error decoding the received the data credentials")
            raise DataEncryptionError

    async def login_encrypted(self, user_data: str) -> LoginModel:
        """
        If the username and password of this user are correct, user is logged in and returns all the information
        related to its token.
        :param user_data
        :return token and refresh token of user
        """
        try:
            user_data_dict = self.decrypt_data(user_data)
            configurations = await self._get_keycloak_endpoints_configuration()
            response = await make_request(
                service_url=configurations.get("token_endpoint"),
                uri="",
                keycloak_request_option=True,
                headers={'Content-Type': RequestHeader.urlencoded},
                method=RequestMethod.POST,
                body=jsonable_encoder(
                    LoginRequest.from_configuration(LoginData(**user_data_dict), self.keycloak_service_configuration)))
            if isinstance(response, NotOkServiceResponse):
                logging.error(f"LoginData failed {json.loads(response.body)}")
                raise WrongCredentials(status.HTTP_400_BAD_REQUEST, json.loads(response.body))
            return format_login_keycloak_response(response)
        except DataEncryptionError as encryption_error:
            logging.error("error decoding the received the data credentials")
            raise KeycloakError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="error decrypting user data",
            ) from encryption_error
        except (ValidationError, KeyError, AttributesError):
            logging.error("error getting all user infos from keycloak")
            raise KeycloakError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="error getting user infos")

    def decrypt_user_creation_data(self, user_data: str) -> UserInfoRegistration:
        """
        decrypt the data received to create user
        :param user_data: str
        :return:
        """
        try:
            return UserInfoRegistration(**self.decrypt_data(user_data))
        except ValidationError as error:
            error_details = ', '.join(f"{field}: {error}" for field, error in error.errors())
            logging.error(f"Error validating received encrypted data of user: {error_details}")
            raise DataEncryptionError
