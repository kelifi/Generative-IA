from datetime import datetime

import jwt
from loguru import logger
from pydantic import ValidationError

from source.exceptions.custom_exceptions import MissingUserInformation, UserInformationFormatError, KeycloakError
from source.schemas.keycloak_schemas import LoginModel, UserInfo, ClientRole


def format_login_keycloak_response(keycloak_response: dict) -> LoginModel:
    """
    Formats the login keycloak method default response and extracts the user id after decoding the access token
    """
    return LoginModel(id=jwt.decode(keycloak_response.get('access_token'), verify=False).get("sub"),
                      token_type=keycloak_response.get('token_type'),
                      expires_in=keycloak_response.get('expires_in'),
                      token=keycloak_response.get('access_token'),
                      refresh_expires_in=keycloak_response.get('refresh_expires_in'),
                      refresh_token=keycloak_response.get('refresh_token'))


def get_date_from_keycloak(timestamp: int):
    return datetime.fromtimestamp(timestamp / 1000.0)


def format_user_info(keycloak_response: dict, user_roles: list[ClientRole] = None):
    """
    Formats the get user keycloak method default response.
    Input can be a list of dicts or a dict
    """
    try:
        if isinstance(keycloak_response, dict):
            user_info = UserInfo(email=keycloak_response['email'], first_name=keycloak_response['firstName'],
                                 last_name=keycloak_response['lastName'],
                                 user_actual_limits=keycloak_response['attributes'],
                                 registration_date=get_date_from_keycloak(keycloak_response['createdTimestamp']),
                                 id=keycloak_response['id'],
                                 )
            if user_roles:
                try:
                    user_info.role = user_roles[0]
                except IndexError as error:
                    logger.error(f"unexpected error! {error}")
                    raise KeycloakError(status_code=500, detail="Unexpected Error!") from error
            return user_info
        raise UserInformationFormatError
    except KeyError as missing_key:
        logger.error(f"Missing user information from keycloak response {missing_key}")
        raise MissingUserInformation(str(missing_key))
    except ValidationError as missing_key:
        logger.error(f"Missing user information from keycloak response {missing_key}")
        raise MissingUserInformation(str(missing_key))
