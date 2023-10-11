import logging

from pydantic import BaseSettings, Field

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()


class BFFSettings(BaseSettings):
    HOST: str = Field(env="APP_HOST", default="0.0.0.0")
    PORT: int = Field(env="APP_PORT", default=8000)
    NB_OF_WORKERS: int = Field(env="NB_OF_WORKERS", default=3)
    CONVERSATION_SERVICE_URL: str = Field(env="CONVERSATION_SERVICE_URL", default="http://localhost:8001")
    SOURCES_SERVICE_URL: str = Field(env="SOURCES_SERVICE_URL", default="http://localhost:7002")
    FILE_HANDLER_URL: str = Field(env="COMMON_FILE_HANDLER_URL", default="http://localhost:8003")
    FILE_HANDLER_API_KEY: str = Field(env="FILE_HANDLER_API_KEY", default="X5v6PkyBu4QVFVHD-i19lQ")
    FILE_HANDLER_USER: str = Field(env="FILE_HANDLER_USER", default="ELGEN")
    PROJECT_NAME: str = Field(env="PROJECT_NAME", default="EL-GEN-bff-service")
    ROOT_PATH: str = Field(env="ROOT_PATH", default="")
    INGEST_SERVICE_HOST: str = Field(env="INGEST_SERVICE_HOST", default="localhost")
    INGEST_SERVICE_PORT: int = Field(env="INGEST_SERVICE_PORT", default=8015)
    MODELS_ENDPOINT: str = Field(env="MODELS_ENDPOINT", default="/models",
                                 description="Endpoint to interact with the models")
    ENCRYPTION_KEY: str = Field(env="ENCRYPTION_KEY", default="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=")
    NONCE_ENCRYPTION_PARAM: str = Field(env="NONCE_ENCRYPTION_PARAM", default="MDEyMzQ1Njc4OTAx")
    RESPONSE_CHUNK_SIZE: int = Field(env="RESPONSE_CHUNK_SIZE", default=1024)

class PactSettings(BaseSettings):
    PACT_URL: str = Field(env="PACT_URL", default="http://127.0.0.1")
    PACT_CONSUMER_NAME: str = Field(env="PACT_CONSUMER_NAME", default="BFF")
    PACT_PROVIDER_NAME: str = Field(env="PACT_PROVIDER_NAME", default="ConversationService")
    PACT_BROKER_USERNAME: str = Field(env="PACT_BROKER_USERNAME", default="pactbroker")
    PACT_BROKER_PASSWORD: str = Field(env="PACT_BROKER_PASSWORD", default="pactbroker")
    PACT_DIR: str = Field(env="PACT_DIR", default="./contracts")
    PACT_MOCK_HOST: str = Field(env="PACT_MOCK_HOST", default="localhost")
    PACT_MOCK_PORT: int = Field(env="PACT_MOCK_PORT", default=1234)
    PACT_VERSION: str = Field(env="PACT_VERSION", default="0.0.1")


class KeyCloakServiceConfiguration(BaseSettings):
    SERVER_URL: str = Field(env="SERVER_URL", default="http://localhost:8089")
    TOKEN_URL: str = Field(env="TOKEN_URL",
                           default="http://localhost:8080/realms/elgen/protocol/openid-connect/token")
    KEYCLOAK_CLIENT_ID: str = Field(env="KEYCLOAK_CLIENT_ID", default="elgen")
    CLIENT_ID: str = Field(env="CLIENT_ID", default="e96eed43-5ba4-4dc7-a45d-4e757febc8fe",
                           description="the client uuid of KEYCLOAK_CLIENT_ID")
    KEYCLOAK_CLIENT_SECRET: str = Field(env="KEYCLOAK_CLIENT_SECRET", default="yq3x73d6sETB091zYmnOeK1ZUuOSBPlf")
    ADMIN_CLIENT_ID: str = Field(env="ADMIN_CLIENT_ID", default="admin-cli")
    ADMIN_CLIENT_SECRET: str = Field(env="ADMIN_CLIENT_SECRET", default="m5IQE8MdBO7lVkFNRORciPVI4KYd58Ue")
    REALM: str = Field(env="REALM", default="elgen")
    REDIRECT_PATH: str = Field(env="REDIRECT_PATH", default="https://0.0.0.0:4200/callback")
    ADMIN_GROUP_ID: str = Field(env="ADMIN_GROUP_ID", default="088f18c2-7f2a-46b4-9b50-e7534a7fa0d9")
    USER_GROUP_ID: str = Field(env="USER_GROUP_ID", default="071f1f4b-1f46-47f8-8b4b-e734858b93da")
    GRANT_TYPE: str = Field(env="GRANT_TYPE", default="password")
    DEFAULT_RATE_LIMIT: str = Field(env="DEFAULT_RATE_LIMIT", default="100")
    REFRESH_GRANT_TYPE: str = Field(env="REFRESH_GRANT_TYPE", default="refresh_token")
    JWT_ALGORITHM: str = Field(env="JWT_ALGORITHM", default="HS256")

    DEFAULT_CLIENT_DURATION: int = Field(env="DEFAULT_USE_DURATION",
                                         description="maximum use duration by days for clients",
                                         default=30)


class KeyCloakHelperConfiguration(BaseSettings):
    ADMIN_GROUP_NAME: str = Field(env="ADMIN_GROUP_NAME", default="admins_group")
    USERS_GROUP_NAME: str = Field(env="USERS_GROUP_NAME", default="users_group")
    ADMIN_ROLE_NAME: str = Field(env="ADMIN_ROLE_NAME", default="admin")
    USER_ROLE_NAME: str = Field(env="USER_ROLE_NAME", default="user")


app_config = BFFSettings()
