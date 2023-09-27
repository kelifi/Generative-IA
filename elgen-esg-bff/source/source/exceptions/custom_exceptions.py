class KeycloakError(Exception):
    """
    Thrown if any response of keycloak does not match our expectation:
        If fetching an admin access token fails,
        or the response does not contain an access_token at all
    Attributes:
        status_code (int): The status code of the response received
        detail (str): The detail why the requests did fail
    """

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class WrongCredentials(Exception):
    def __init__(self, status_code: int, detail: str = "Wrong credentials"):
        self.detail = detail
        self.status_code = status_code


class MissingUserInformation(Exception):
    def __init__(self, key: str):
        self.detail = f"Missing Key {key} from keycloak response"


class SessionNotFound(Exception):
    def __init__(self):
        self.detail = f"error getting user session"


class UserInformationFormatError(Exception):
    def __init__(self):
        self.detail = "Error in user data format, user account is not configured"


class UserNotFound(Exception):
    """Thrown when a user lookup fails.

    Attributes:
        status_code (int): The status code of the response received
        detail (str): The detail why the requests did fail
    """

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class UserAlreadyExistException(Exception):
    """
    Exception raised when KeysType cannot recognize a key string
    """

    def __init__(self, status_code: int, detail: str = "This user (with same username) already exists"):
        self.status_code = status_code
        self.detail = detail


class SchemaError(Exception):
    """
    Exception raised when a pydantic validation error pops up
    """

    def __init__(self, detail: str = "Schema was not successfully validated"):
        self.detail = detail


class MetadataObjParseError(Exception):
    """
      Exception raised when parsing the metadata object fails
      """

    def __init__(self, detail: str = "Could not parse the metadata object"):
        self.detail = detail


class UserRolesNotDefined(Exception):
    """
    Exception raised when a user does not have roles defined for them
    """

    def __init__(self, detail: str = "no roles defined for the user"):
        self.detail = detail


class AttributesError(Exception):
    """
    Exception raised when a user does not have roles defined for them
    """

    def __init__(self, detail: str = "error in the users user_default_limits defined"):
        self.detail = detail


class DataEncryptionError(Exception):
    """
    Exception raised when a user does not have roles defined for them
    """

    def __init__(self, detail: str = "error in decrypting the user data received"):
        self.detail = detail
