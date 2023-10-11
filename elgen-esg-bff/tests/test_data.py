from datetime import date, timedelta, datetime
from uuid import uuid4

import jwt
from fastapi.security import HTTPAuthorizationCredentials

from configuration.config import KeyCloakServiceConfiguration
from source.exceptions.custom_exceptions import SchemaError
from source.schemas.api_schemas import AnswerOutputSchema, ModelInfoSchema, SourceResponse, QuestionLimitOutputSchema
from source.schemas.chat_suggestions_schemas import ChatSuggestion, WorkspaceChatSuggestions
from source.schemas.common import AcknowledgeResponse, AcknowledgeTypes, UpdateStatusDataModel
from source.schemas.conversation_schemas import AnswerSchema, QuestionInputSchema
from source.schemas.ingestion_schemas import IngestedFileOutput, IngestedFilesCountOutput
from source.schemas.keycloak_schemas import (ConversationInfo, KeycloakAttribute, KeycloakPartialImportResponse,
                                             KeycloakPartialImportResult, UserCreationBulkResponse, UserInfo,
                                             KeycloakTokenInfo, LoginData, ClientRole,
                                             UserLimits, UserInfoRegistration, LoginModel, UserInfoWorkspace)
from source.schemas.source_schemas import SourceLimitSchema, SourceTypeOutputSchema
from source.schemas.source_schemas import SourceVerificationOutput, SourceVerificationInput, SourceDataOutput, \
    DatabaseFieldsMapping, TableInfo, ColumnInfo, SourceOutput, SourceInput
from source.schemas.workspace_schemas import (WorkspaceDto, WorkspaceByUserApiResponseModel, WorkspaceUsersApiModel,
                                              WorkspaceOutput, WorkspaceInput, WorkspaceTypeOutputModel,
                                              WorkspaceTypeModel, WorkspaceConfigOutputModel,
                                              GenericWorkspacesResponseModel, GenericWorkspaceOutputModel,
                                              WorkspaceTypesEnum)

valid_date_and_limit_attributes = ConversationInfo(
    conversationsDate=[str(date.today())],
    conversationsInit=[999],
    conversationsLimit=[998],
    questionsDate=[str(date.today())],
    questionsInit=[999],
    questionsLimit=[998]
).dict(by_alias=True)
valid_date_non_valid_limit_attributes = ConversationInfo(
    conversationsDate=[str(date.today())],
    conversationsInit=[999],
    conversationsLimit=[0],
    questionsDate=[str(date.today())],
    questionsInit=[999],
    questionsLimit=[998]
).dict(by_alias=True)

non_valid_user_limit_attributes = ConversationInfo(
    conversationsDate=[],
    conversationsInit=[],
    conversationsLimit=[],
    questionsDate=[],
    questionsInit=[],
    questionsLimit=[]
).dict(by_alias=True)

non_valid_limit_non_valid_date_attributes = ConversationInfo(
    conversationsDate=[str(date.today() - timedelta(days=1))],
    conversationsInit=[999],
    conversationsLimit=[0],
    questionsDate=[str(date.today())],
    questionsInit=[999],
    questionsLimit=[998]
)

login_data_success = {'id': 'user123',
                      'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIj'
                               'oxNjkzMDAyMTU3LCJpYXQiOjE2OTI5OTg1NTd9.gssPZM_D1L_8B4JfpBhZ8Dg5GQxS2UA6Mc5HvbE9EPI',
                      'refreshToken': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNjkzMDA'
                                      'yMTU3LCJpYXQiOjE2OTI5OTg1NTd9.gssPZM_D1L_8B4JfpBhZ8Dg5GQxS2UA6Mc5HvbE9EPI',
                      'tokenType': 'Bearer', 'expiresIn': '3600', 'refreshExpiresIn': '7200'}
wrong_date_attributes = ConversationInfo(
    conversationsDate=[],
    conversationsInit=[],
    conversationsLimit=[998],
    questionsDate=[str(date.today())],
    questionsInit=[999],
    questionsLimit=[998]
).dict(by_alias=True)

user_attributes = {
    f'{KeycloakAttribute.CONVERSATIONS}Limit': [5],
    f'{KeycloakAttribute.CONVERSATIONS}Init': [10],
    f'{KeycloakAttribute.CONVERSATIONS}Date': [str(datetime.now().strftime('%Y-%m-%d'))]
}

user_email = 'tester@test.com'
first_name = 'tester'
last_name = 'tester'
user_id = '221ff523-3774-44ab-9c37-bd0f2d72243f'

user_info = UserInfo(
    email=user_email,
    first_name=first_name,
    last_name=last_name,
    user_actual_limits=valid_date_and_limit_attributes
)

user_info_workspace = UserInfoWorkspace(
    id=uuid4(),
    email=user_email,
    first_name=first_name,
    last_name=last_name,
    user_actual_limits=valid_date_and_limit_attributes
).dict(by_alias=True)

user_info_error = UserInfo(
    email=user_email,
    first_name=first_name,
    last_name=last_name,
    user_actual_limits=wrong_date_attributes
)

mock_service_response = [
    {
        "email": "hello@example.com",
        "firstName": "string",
        "lastName": "string",
        "emailVerified": True,
        "clientRoles": None,
        "role": None,
        "attributes": {
            "conversationsInit": [
                100
            ],
            "questionsInit": [
                100
            ],
            "conversationsDate": [
                "2023-10-05"
            ],
            "conversationsLimit": [
                100
            ],
            "questionsDate": [
                "2023-10-05"
            ],
            "questionsLimit": [
                100
            ]
        },
        "id": "82e57ca1-a659-44dd-b176-02e3f7a5ac58"
    },
    {
        "email": "nihed@example.com",
        "firstName": "nihed",
        "lastName": "mosbehi",
        "emailVerified": True,
        "clientRoles": None,
        "role": None,
        "attributes": {
            "conversationsInit": [
                9999
            ],
            "questionsInit": [
                9999
            ],
            "conversationsDate": [
                "2023-10-05"
            ],
            "conversationsLimit": [
                9999
            ],
            "questionsDate": [
                "2023-10-05"
            ],
            "questionsLimit": [
                9999
            ]
        },
        "id": "ca0e9513-ec61-42d2-8273-6af8e6604fb1"
    }]
wrong_users_list_format = [
    {
        "email_2": "hello@example.com",
        "firstName": "string",
        "lastName": "string",
        "emailVerified": True,
        "clientRoles": None,
        "role": None,
        "attributes": {
            "conversationsInit": [
                100
            ],
            "questionsInit": [
                100
            ],
            "conversationsDate": [
                "2023-10-05"
            ],
            "conversationsLimit": [
                100
            ],
            "questionsDate": [
                "2023-10-05"
            ],
            "questionsLimit": [
                100
            ]
        },
        "id": "82e57ca1-a659-44dd-b176-02e3f7a5ac58"
    },
    {
        "email": "nihed@example.com",
        "firstName": "nihed",
        "lastName": "mosbehi",
        "emailVerified": True,
        "clientRoles": None,
        "role": None,
        "attributes": {
            "conversationsInit": [
                9999
            ],
            "questionsInit": [
                9999
            ],
            "conversationsDate": [
                "2023-10-05"
            ],
            "conversationsLimit": [
                9999
            ],
            "questionsDate": [
                "2023-10-05"
            ],
            "questionsLimit": [
                9999
            ]
        },
        "id": "ca0e9513-ec61-42d2-8273-6af8e6604fb1"
    },
]


dummy_token = {
    "exp": 1691446465,
    "iat": 1691410465,
    "jti": "bbceaa95-44cf-49da-b608-b4d58a6db72e",
    "iss": "http://localhost:8089/realms/elgen",
    "aud": "account",
    "sub": "5ed73121-7be0-4bcf-9945-9245636e059d",
    "typ": "Bearer",
    "azp": "elgen",
    "session_state": "427a4195-b8a2-4326-8803-4365f7ef69c5",
    "acr": "1",
    "allowed-origins": [
        "*"
    ],
    "realm_access": {
        "roles": [
            "default-roles-elgen",
            "offline_access",
            "uma_authorization",
            "super_admins"
        ]
    },
    "resource_access": {
        "elgen": {
            "roles": [
                "user"
            ]
        },
        "account": {
            "roles": [
                "manage-account",
                "manage-account-links",
                "view-profile"
            ]
        }
    },
    "scope": "profile email",
    "sid": "427a4195-b8a2-4326-8803-4365f7ef69c5",
    "email_verified": True,
    "name": "string string",
    "preferred_username": "user@example.com",
    "given_name": "string",
    "family_name": "string",
    "email": "user@example.com",
    "username": "my_username",
    "active": True
}

testing_token = {
  "exp": 1696877510,
  "iat": 1696841510,
  "jti": "d9b14be2-c4bc-43e5-ba9c-e04435dcbae9",
  "iss": "http://localhost:8089/realms/elgen",
  "sub": "1435282e-72a0-4114-955d-83b597abf8b5",
  "typ": "Bearer",
  "azp": "elgen",
  "session_state": "6101f4e8-efed-4b29-85d0-c404fd27591c",
  "acr": "1",
  "allowed-origins": [
    "*"
  ],
  "resource_access": {
    "elgen": {
      "roles": [
        "super_admin",
        "user"
      ]
    }
  },
  "scope": "roles profile email",
  "sid": "6101f4e8-efed-4b2=-85d0-c404fd27591c",
  "email_verified": True,
  "name": "string string",
  "preferred_username": "user@example.com",
  "given_name": "string",
  "family_name": "string",
  "email": "user@example.com"
}


dummy_user_info = {
    "email": "user@example.com",
    "firstName": "string",
    "lastName": "string",
    "emailVerified": True,
    "createdTimestamp": 0,
    "attributes": {
        "conversationsDate": [
            "2023-08-08"
        ],
        "conversationsInit": [
            "100"
        ],
        "conversationsLimit": [
            "100"
        ],
        "questionsDate": [
            "2023-08-08"
        ],
        "questionsInit": [
            "100"
        ],
        "questionsLimit": [
            "100"
        ]
    },
    "clientRoles": {
        "elgen": [
            "user"
        ]
    },
    "role": "user",
    "password": "string",
    "id": user_id
}
decoded_data_success = {'attributes': {'conversationsInit': ['100'], 'questionsInit': ['100']},
                        'clientRoles': {'elgen': ['user']},
                        'email': 'user@example.com', 'emailVerified': True, 'firstName': 'string', 'lastName': 'string',
                        'password': 'string', 'role': 'user'}

decoded_user_created_success = UserInfoRegistration(
    **{'client_roles': {'elgen': ['user']}, 'email': 'user@example.com', 'email_verified': True, 'first_name': 'string',
       'last_name': 'string', 'password': 'string', 'role': 'user',
       'user_default_limits': {'conversations_init': [100], 'questions_init': [100]}})

dummy_user_data_success = {
    "userData": "C62tB8CcM1KZSOM7EacyAQigvOtE4b/CvsuoMWb+26KUOlzWhcMkmlODPxbkZDDtclQoCYTiTHOFUoTsQhxJg2iSfAWY7TOw6jG"
                "gSS4E4XiUEkVeIfPPDzl0W5jPEmnQkMsSFrdQkdiBQ5PKvyzIMKoSlqIuLs3N2MjRFXHZrSTRBejgf7Wy6g51s94Qpp8/UGgLRe6"
                "01lVIZyTc0W8E7xgTVxnNCyJ4hqnasaZTqeFivTQFYRcJQmtCaDIbVeJ3L1GRFucaP+D6K3S3LFfS+af4osxzosCVFDW0134j99uQ"
                "fQO4Tto02dhBhp/hkLkp"}

dummy_login_data_success = {
    'userData': "C62tB8CcM1KZSOM7EacyAQigvOtE4b/CvsuoMWbo06OUOX3FjIQ8ggKEOQ3jbXWy9azTFkhcEahSoQ1rEOaghA=="}
dummy_user_data_fail = {"userData": "qLR3WZDyIugr"}

dummy_source_data = {"data": [{
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "content": "string",
    "link": "string",
    "fileId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "fileName": "string",
    "creationDate": None,
    "documentType": "string",
    "downloadLink": "/sources/v1/download/3fa85f64-5717-4562-b3fc-2c963f66afa6"
}], "detail": "test"}

dummy_source_data_fail = {"detail": "test"}


async def mock_token(*args, **kwargs):
    return dummy_token


async def token_for_testing (*args, **kwargs):
    return testing_token


async def mock_token_not_dict(*args, **kwargs):
    return KeycloakTokenInfo(**dummy_token)


async def mock_get_source_docs(*args, **kwargs):
    return SourceResponse(**dummy_source_data)


async def mock_get_source_docs_fail(*args, **kwargs):
    raise SchemaError


keycloak_create_user_partial_import_response = KeycloakPartialImportResponse(
    overwritten=0,
    added=1,
    skipped=0,
    results=[KeycloakPartialImportResult(
        action="ADD",
        resource_type="USER",
        resource_name="USER",
        id=user_id
    )]
)


def mock_check_role_user_success(*args, **kwargs0):
    return None


def mock_check_role_admin(*args, **kwargs0):
    return [ClientRole.SUPER_ADMIN]


async def mock_create_user_success(*args, **kwargs):
    return UserCreationBulkResponse(user_id=user_id)


token_info = KeycloakTokenInfo(
    exp=int(datetime.now().timestamp()),
    iat=int(datetime.now().timestamp()),
    jti=uuid4(),
    iss='issuer',
    aud='audience',
    sub=uuid4(),
    typ='Bearer',
    azp='authorized_party',
    preferred_username='user123',
    email_verified=True,
    acr='acr_value',
    realm_access={'role': 'realm_role'},
    resource_access={'client_id': {'role': 'client_role'}},
    scope='scope_value',
    client_id='client123',
    clientHost='client_host',
    clientAddress='client_address',
    username='user123',
    active=True
)


async def mock_token_infos(*args, **kwargs):
    return token_info


mock_roles = [ClientRole.USER]


async def mock_roles_func(*args, **kwargs):
    return mock_roles


async def mock_user_data(*args, **kwargs):
    return dummy_user_info


login_data_dict = {"email": "test@gmail.com", "password": "test"}
login_data_dict_error = {"email": "test@gmail.com", }
login_data = LoginData(email="test@gmail.com", password="test")
keycloak_endpoints_data = {"token_endpoint": "token_endpoint"}

token_payload = {
    "sub": "user123",
    "exp": datetime.utcnow() + timedelta(hours=1),
    "iat": datetime.utcnow(),
}

token = jwt.encode(token_payload, "secret_key", algorithm="HS256")

login_instance = {"id": "user123",
                  "token_type": "Bearer",
                  "expires_in": "3600",
                  "refresh_expires_in": "7200",
                  "access_token": token,
                  "refresh_token": token,
                  "token": token
                  }
login_model_success = LoginModel(**login_instance)
credentials = HTTPAuthorizationCredentials(scheme="bearer", credentials="token")

sources_limit_list = [
    SourceLimitSchema(
        model_code="M2",
        max_web=10,
        max_local=10
    ),
    SourceLimitSchema(
        model_code="M1",
        max_web=2,
        max_local=2
    )]

sources_limit_dict_list = [source_limit_schema.dict() for source_limit_schema in sources_limit_list]

success_ack = AcknowledgeResponse(acknowledge=AcknowledgeTypes.SUCCESS)

dummy_question = {"question": "this is a question"}


async def mock_check_user_limit_false(self, user_id, attribute_to_check):
    return False


async def mock_check_user_limit_true(self, user_id, attribute_to_check):
    return True


question_id = "dba202cd-9268-43ca-86db-7d4525f22625"

answer_data = {
    "id": "6f99e4b5-4c35-4b92-8f0f-9f593b802b8f",
    "content": "This is the answer to your question.",
    "creationTime": "2023-08-21T12:00:00",
    "updated_at": "2023-08-21T14:30:00",
    "rating": "like",
    "edited": True,
}
answer_schema = AnswerSchema(**answer_data)
answer_output = AnswerOutputSchema(question_id=question_id, answer=answer_schema)
answer_output_dict = {'id': 'dba202cd-9268-43ca-86db-7d4525f22625',
                      'answer': {'id': '6f99e4b5-4c35-4b92-8f0f-9f593b802b8f',
                                 'content': 'This is the answer to your question.',
                                 'creationTime': '2023-08-21T12:00:00', 'updatedAt': '2023-08-21T14:30:00',
                                 'rating': 'like', 'edited': True}}


async def mock_get_answer(*args, **kwargs):
    return answer_output


model_data_1 = {'available': True,
                'code': 'LP1',
                'default': True,
                'maxWeb': 1,
                'maxLocal': 1,
                'name': 'Falcon'}

model_data_1_updated = model_data_1
model_data_1_updated["maxWeb"] = 2
model_data_1_updated["maxLocal"] = 2

model_data_2 = {'available': True,
                'code': 'LP2',
                'default': False,
                'maxWeb': 2,
                'maxLocal': 2,
                'name': 'OPEN AI'}

model_info = ModelInfoSchema(**model_data_1)
updated_model = ModelInfoSchema(**model_data_1_updated)
available_models = [model_info, ModelInfoSchema(**model_data_2)]
user_workspaces = [WorkspaceDto(id=uuid4(), name="my  workspace",
                                active=True,
                                description="My workspace description",
                                available_model_codes=["M1"]),
                   WorkspaceDto(id=uuid4(), name="my second workspace",
                                active=True,
                                description="My second workspace description",
                                available_model_codes=["M1"])]
user_workspaces_response_api_response = WorkspaceByUserApiResponseModel(workspaces=user_workspaces)
workspace_users_response_api_response = WorkspaceUsersApiModel(users_ids=[str(uuid4()), str(uuid4())])

workspace_input = WorkspaceInput(name="my workspace",
                                 active=True,
                                 description="My workspace description",
                                 available_model_codes=["M1"])
workspace_output = WorkspaceOutput(id=str(uuid4()),
                                   name="my workspace",
                                   active=True,
                                   description="My workspace description")

user_info_registration = UserInfoRegistration(
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    email_verified=True,
    client_roles={
        KeyCloakServiceConfiguration().KEYCLOAK_CLIENT_ID: [ClientRole.USER]
    },
    user_default_limits=UserLimits(
        conversations_init=[100],
        questions_init=[100]
    ),
    password="mysecretpassword"
)


async def mock_get_models(*args, **kwargs):
    return available_models


async def mock_get_models_by_workspace_id(*args, **kwargs):
    return {"models": available_models}


async def mock_user_info_registration(*args, **kwargs):
    return user_info_registration


async def mock_model(*args, **kwargs):
    return model_info


model_post_dict = {'available': True,
                   'route': '/route',
                   'type': 'chat',
                   'code': 'LP2',
                   'default': False,
                   'maxLocal': 2,
                   'maxWeb': 2,
                   'name': 'OPEN AI'}

model_update_dict = {'code': 'M1',
                     'maxLocal': 2,
                     'maxWeb': 2}

workspace_id = suggestion_id = "dba202cd-9268-43ca-86db-7d4525f22625"
dummy_ingested_files = IngestedFileOutput(file_id="dba202cd-9268-43ca-86db-7d4525f22625")
dummy_nb_files = IngestedFilesCountOutput(count=10)
dummy_question_input = {"id": "6f99e4b5-4c35-4b92-8f0f-9f593b802b8f", "content": "this is a question"}
dummy_workspace_types = WorkspaceTypeOutputModel(data=[WorkspaceTypeModel(**{
    "name": WorkspaceTypesEnum.chat,
    "description": "string",
    "available": "true",
    "id": "41685673-26d1-450d-8489-5de85ddc813a"
})])

dummy_available_sources = SourceTypeOutputSchema(data=[{
    "id": "c3e4bd86-b6ef-46e1-9adf-efb23b39b21c",
    "name": "test",
    "description": "testtt",
    "available": "true"
}])
dummy_workspace_models = {'models': [
    {'available': True, 'code': 'M1', 'default': True, 'maxLocal': 2, 'maxWeb': 2, 'name': 'Online Model',
     'route': 'dummy_route', 'type': 'chat'}]}

dummy_verification_value = SourceVerificationOutput()
dummy_source_data_output = SourceDataOutput(url="example")

dummy_workspace_data = WorkspaceConfigOutputModel(**{
    "id": "4c480ff9-454b-41e1-80cb-a13ba1b66f79",
    "name": "test",
    "active": False,
    "description": "",
    "classification_change_enabled": True,
    "stop_answer_process": True,
    "models": [
        "M1",
        " M6",
        " M2",
        " M3"
    ],
    "workspace_type": {
        "id": "39852f75-83b5-4c4e-a060-357385a2f825",
        "name": "database",
        "description": "string",
        "available": True
    }
})

dummy_workspaces_data = GenericWorkspacesResponseModel(workspaces=([GenericWorkspaceOutputModel(**{
    "id": "4c480ff9-454b-41e1-80cb-a13ba1b66f79",
    "name": "test",
    "active": False,
    "description": "",
    "available_model_codes": ["M1"],
    "workspace_type": {
        "id": "39852f75-83b5-4c4e-a060-357385a2f825",
        "name": "database",
        "description": "string",
        "available": True
    }
})]))

mock_workspace_deleted = mock_workspace_updated = mock_suggestion_deleted = mock_suggestion_updated = UpdateStatusDataModel(
    **{
        "id": "e85cb91e-4f7a-4e6f-b4df-f9c98e393fda",
        "updated": True
    })


async def mock_verification_value(*args, **kwargs):
    return dummy_verification_value


async def mock_source_data_output(*args, **kwargs):
    return dummy_source_data_output.dict()


async def mock_source_output(*args, **kwargs):
    return SourceOutput(url="example").dict()


def mock_check_user_role_valid(*args, **kwargs):
    return None


async def mock_get_workspaces_by_user_id(*args, **kwargs):
    return dummy_workspaces_data


async def mock_get_all_workspaces(*args, **kwargs):
    return dummy_workspaces_data


async def mock_get_users_by_workspace_id(*args, **kwargs):
    return workspace_users_response_api_response.dict()


async def mock_assign_users_to_workspace(*args, **kwargs):
    return True


async def mock_get_workspace_users(*args, **kwargs):
    return [user_info_workspace]


async def mock_create_workspace(*args, **kwargs):
    return workspace_output


async def mock_update_workspace(*args, **kwargs):
    return mock_workspace_updated


async def mock_delete_workspace(*args, **kwargs):
    return mock_workspace_updated


async def mock_store_documents(*args, **kwargs):
    return dummy_ingested_files


async def mock_count_files(*args, **kwargs):
    return dummy_nb_files


async def mock_get_workspace_types(*args, **kwargs):
    return dummy_workspace_types


async def mock_get_available_sources_per_type(*args, **kwargs):
    return dummy_available_sources


async def mock_get_workspace_models(*args, **kwargs):
    return dummy_workspace_models


async def mock_get_workspace_by_id(*args, **kwargs):
    return dummy_workspace_data.dict()


fake_db_url = "www.fake_url.com/?user=one&pwd=two"

mock_source_verification_input = SourceVerificationInput(url=fake_db_url, category="postgres",
                                                         source_type="database")

mock_add_source_input = SourceInput(url=fake_db_url, category="postgres", source_type="database")

add_source_mock_response = update_field_mapping_input_mock = SourceDataOutput(
    id=str(uuid4()),
    url="www.fake-url.com",
    category="postgres",
    source_type="database",
    mapping=DatabaseFieldsMapping(
        tables=[
            TableInfo(
                name="table name",
                columns=[ColumnInfo(name="column name", description="description 1"),
                         ColumnInfo(name="column name 2", description="description 2")]
            ), TableInfo(
                name="table name 2",
                columns=[ColumnInfo(name="column name", description="description 1"),
                         ColumnInfo(name="column name 2", description="description 2")]
            )]))


async def mock_verify_source_ok(*args, **kwargs):
    return SourceVerificationOutput()


async def mock_extract_source_information(*args, **kwargs):
    return add_source_mock_response


async def mock_add_source_to_db(*args, **kwargs):
    return SourceOutput(
        id=str(uuid4()),
        url=fake_db_url,
        description="fake_db_description",
        category="mysql",
        source_type="database",
        workspace_id=workspace_id,
        user_id=user_id,
        source_metadata={"hello": "test"}
    ).dict()


async def mock_update_source_field_mapping(*args, **kwargs):
    return update_field_mapping_input_mock


add_question_return_mock = QuestionLimitOutputSchema(id=question_id,
                                                     content='test_content',
                                                     answer=answer_schema,
                                                     creation_date=datetime.now(),
                                                     skip_doc=False,
                                                     skip_web=False,
                                                     local_sources=None,
                                                     web_sources=None,
                                                     is_specific=True
                                                     )


async def mock_add_question(*args, **kwargs):
    return add_question_return_mock


async def mock_update_rate_limit(*args, **kwargs):
    return user_info


mock_add_question_return_object = {
    "id": "dba202cd-9268-43ca-86db-7d4525f22625",
    "content": 'test_content',
    "answer": {
        "id": "6f99e4b5-4c35-4b92-8f0f-9f593b802b8f",
        "content": "This is the answer to your question.",
        "creationTime": "2023-08-21T12:00:00",
        "updated_at": "2023-08-21T14:30:00",
        "rating": "like",
        "edited": True,
    },
    "creation_date": datetime.now(),
    "skip_doc": False,
    "skip_web": False,
    "local_sources": None,
    "web_sources": None,
    "is_specific": True
}
mock_chat_suggestion_input_data = QuestionInputSchema(question="What is the purpose of life?")

chat_suggestion = ChatSuggestion(**{
    "id": "d831cd24-7d8d-42ca-bfaa-ac75c67bc350",
    "content": "What is the purpose of life?",
    "available": True
})
chat_suggestions_list = WorkspaceChatSuggestions(suggestions=[chat_suggestion])


async def mock_create_chat_suggestion(*args, **kwargs):
    return chat_suggestion


async def mock_get_chat_suggestions(*args, **kwargs):
    return chat_suggestions_list


async def mock_delete_suggestion_by_id(*args, **kwargs):
    return mock_suggestion_deleted


async def mock_update_suggestion_by_id(*args, **kwargs):
    return mock_suggestion_updated
