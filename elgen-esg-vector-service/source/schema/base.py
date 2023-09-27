from enum import Enum


class AppEnv(str, Enum):
    dev = "dev"
    prod = "prod"


