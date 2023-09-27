import logging

from fastapi import HTTPException, status


class UnauthenticatedKeycloakAPIError(HTTPException):
    def __init__(self, detail, status_code=status.HTTP_403_FORBIDDEN):
        super().__init__(detail=detail, status_code=status_code)


class WrongCredentialsApiException(HTTPException):
    def __init__(self, detail, status_code):
        super().__init__(detail=detail, status_code=status_code)


class LogoutSessionError(HTTPException):
    def __init__(self, detail, status_code):
        super().__init__(detail=detail, status_code=status_code)


class UserAlreadyExistApiException(HTTPException):
    def __init__(self, detail, status_code):
        super().__init__(detail=detail, status_code=status_code)


class UserFormatApiException(HTTPException):
    def __init__(self, detail):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class NotFoundException(HTTPException):
    """*404* `Not found`
    Raise if the browser sends something to the application
    or the server which they cannot find.
    """

    def __init__(self, detail):
        logging.error(detail)
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UserNotFoundApiException(NotFoundException):
    def __init__(self, detail):
        super().__init__(detail=detail)


class KeycloakInternalApiException(HTTPException):
    def __init__(self, detail="error getting user data from keycloak"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationsLimitApiException(HTTPException):
    def __init__(self, detail="conversations limit surpassed, you can check later!"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class QuestionsLimitApiException(HTTPException):
    def __init__(self, detail="questions limit surpassed, you can check later!"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class UserRolesNotDefinedApiError(HTTPException):
    """
       Exception raised at the api level when a user does not have roles defined for them
    """
    def __init__(self, detail, status_code):
        super().__init__(detail=detail, status_code=status_code)