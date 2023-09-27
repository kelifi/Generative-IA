from enum import Enum


class AppEnv(str, Enum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class RequestMethod(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"


class ModelTypes(str, Enum):
    CHAT = "chat"
    CLASSIFICATION = "classification"
