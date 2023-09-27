from enum import Enum


class RequestMethod(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"


class LimitType(str, Enum):
    CONVERSATION = "conversation"
    QUESTIONS = "questions"
