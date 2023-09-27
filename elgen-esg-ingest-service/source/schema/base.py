from enum import Enum


class AppEnv(str, Enum):
    Dev = "dev"
    PROD = "prod"
