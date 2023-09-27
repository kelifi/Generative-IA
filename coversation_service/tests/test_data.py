import datetime
import json
from uuid import uuid4, UUID

from source.models.conversations_models import Conversation, Question
from source.models.model_table import Model
from source.models.workspace_models import Workspace
from source.schemas.chat_schema import PromptSchema
from source.schemas.conversation_schema import (SourceSchema, WebSourceSchema, AnswerSchema, QuestionSchema, ChatSchema,
                                                ConversationTitleSchema, ConversationSchema, AnswerOutputSchema,
                                                ConversationIdSchema)
from source.schemas.models_schema import (ModelServiceAnswer, ModelOutputSchema, ModelInputSchema, ModelSchema,
                                          ModelSourcesUpdateSchema)
from source.schemas.streaming_answer_schema import (ModelStreamingInProgressResponse, StreamingResponseStatus,
                                                    ModelStreamingErrorResponse)
from source.schemas.workspace_schema import WorkspaceOutput, WorkspaceDto, WorkspaceUsersApiModel, WorkspaceInput

current_time = datetime.datetime.now()
conversation_uuid = 'e85cb91e-4f7a-4e6f-b4df-f9c98e393fd9'
user_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e393fda'
workspace_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e393fda'
question_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e393aaa'
answer_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e39dada'
source_doc_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e393fdb'
web_source_doc_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e222fdb'
model_id = 'e85cb91e-4f7a-4e6f-b4df-f9c98e222aaa'
source_doc = SourceSchema(id='e85cb91e-4f7a-4e6f-b4df-f9c98e393fdb', content='blablabla', file_name='doc.pdf',
                          document_type='pdf')
workspace_users_ids = WorkspaceUsersApiModel(users_ids=[str(user_id)])

source_schema1 = source_doc
source_schema1.id = str(source_schema1.id).replace('a', '1')
source_schema1.content = f'{source_schema1.content} 1'

source_schema2 = source_doc
source_schema2.id = str(source_schema1.id).replace('a', '2')
source_schema2.content = f'{source_schema1.content} 2'

web_source_doc = WebSourceSchema(id='e85cb91e-4f7a-4e6f-b4df-f9c98e393eee', url='blablabla.com',
                                 description='This source is good', title='websource tested', paragraphs='')

web_source_schema1 = web_source_doc
web_source_schema1.id = str(web_source_schema1.id).replace('a', '1')
web_source_schema1.description = f'{web_source_schema1.description} 1'

web_source_schema2 = web_source_doc
web_source_schema2.id = str(web_source_schema1.id).replace('a', '2')
web_source_schema2.description = f'{web_source_schema1.description} 2'
answer_object = AnswerSchema(id=answer_id, content='test_answer',
                             creation_date=current_time,
                             update_date=current_time,
                             edited=False)

question = QuestionSchema(id=question_id,
                          content='test_content',
                          creation_date=current_time,
                          answer=answer_object,
                          skip_doc=False,
                          skip_web=False,
                          local_sources=None,
                          web_sources=None, )
chat = ChatSchema(id=conversation_uuid, questions=[question])
input_conversation = ConversationTitleSchema(title='test')
conv_schema = ConversationSchema(user_id=user_id, title='test', id=conversation_uuid, workspace_id=workspace_id,
                                 creationTime=current_time, updateTime=None)
updated_conv_schema = ConversationSchema(user_id=user_id, title='updated title', id=conversation_uuid,
                                         workspace_id=workspace_id,
                                         creationTime=current_time, updateTime=None)

source_documents_string = "\n".join([source_doc.content, source_doc.content])
text_to_summarize = "summarize me please!"
web_source_summarized_paragraph = "The answer to the question or summarization"

prompt_with_web_sources_example = f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {source_documents_string}

    {web_source_summarized_paragraph}

        Question: {question.content}
        """

prompt_with_no_web_sources_example = f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {source_documents_string}

    {''}

        Question: {question.content}
        """

mock_model_answer = "The model has answered"

prompt_object = PromptSchema(prompt=prompt_with_web_sources_example)

answer_with_sources = AnswerSchema(id=answer_id, content='test_answer',
                                   creation_date=current_time, update_date=current_time, edited=False
                                   )
output_answer_example = AnswerOutputSchema(id=question_id, answer=answer_with_sources)

conversations_orm_object = [
    Conversation(
        id=uuid4(), user_id=user_id,
        title="Conv 1", creation_date=current_time, workspace_id=workspace_id),
    Conversation(
        id=uuid4(), user_id=user_id,
        title="Conv 2", creation_date=current_time, workspace_id=workspace_id)]

conversations_data_object = [ConversationSchema.from_orm(conversation) for conversation in conversations_orm_object]
conversation_id_object = ConversationIdSchema(id=UUID(conversation_uuid))

question_orm_object = Question(id=question_id, conversation_id=conversation_uuid, content='test_content',
                               skip_doc=False, skip_web=False, creation_date=current_time, deleted=False)
question_data_object = QuestionSchema.from_orm(question_orm_object)

model_code = 'M1'

model_service_answer = ModelServiceAnswer(
    response="The answer to the question or summarization",
    prompt_length=20,
    inference_time=0.043,
    model_code=model_code,
    model_name="ModelName")

model_service_streaming_done_answer = dict(
    data=dict(response="The answer to the question or summarization",
              prompt_length=20,
              inference_time=0.043,
              model_name="ModelName"),
    status=StreamingResponseStatus.DONE
)

model_1_orm = Model(
    id=model_id,
    name="Elyadata model",
    code=model_code,
    route="/model/question-answering",
    available=True,
    default=True,
    type="chat",
    creation_date=datetime.datetime.now(),
    max_web=1,
    max_doc=2

)

updated_model_1_orm = Model(
    id=model_id,
    name="Elyadata model",
    code=model_code,
    route="/model/question-answering",
    available=True,
    default=True,
    type="chat",
    creation_date=datetime.datetime.now(),
    max_web=10,
    max_doc=20

)

model_1_input = ModelInputSchema(name="Elyadata model",
                                 code=model_code,
                                 route="/model/question-answering",
                                 available=True,
                                 default=True,
                                 type="chat",
                                 max_web=1,
                                 max_doc=2
                                 )
model_2_orm = Model(
    id=model_id,
    name="Elyadata model 2",
    code="M2",
    route="/model/question-answering",
    available=True,
    default=False,
    type="chat",
    creation_date=datetime.datetime.now(),
    max_web=3,
    max_doc=3

)

model_1 = ModelSchema.from_orm(model_1_orm)
model_2 = ModelSchema.from_orm(model_2_orm)

model_output_1 = ModelOutputSchema(name="Elyadata model",
                                   code=model_code,
                                   available=True,
                                   default=True,
                                   max_web=1,
                                   max_doc=2
                                   )
model_output_2 = ModelOutputSchema(name="Elyadata model 2",
                                   code="M2",
                                   available=True,
                                   default=False,
                                   max_web=3,
                                   max_doc=3)

model_1_update_object = ModelSourcesUpdateSchema(code=model_code,
                                                 max_web=10,
                                                 max_doc=10)

source_to_add_1 = SourceSchema(
    id="c6e8b8a5-8fb6-4d48-9763-ff6c22c0e6e0",
    content="This is the content of the document 1",
    document_path="/documents/doc12345",
    file_name="document1.pdf",
    creation_date=datetime.datetime(2023, 9, 4, 10, 0, 0),
    document_type="pdf",
    document_id="d6e8b8a5-8fb6-4d48-9763-ff6c22c0e6e1",
    download_link="https://example.com/documents/doc12345/download"
)

source_to_add_2 = SourceSchema(
    id="4f279153-17f7-4ea7-8990-8bf11cafa79a",
    content="This is the content of the document 2",
    document_path="/documents/doc12346",
    file_name="document2.pdf",
    creation_date=datetime.datetime(2023, 9, 4, 10, 0, 0),
    document_type="pdf",
    document_id="bd05bbae-5832-470d-8f75-4e291215ee07",
    download_link="https://example.com/documents/doc12345/download"
)

sources_to_add = {
    'similar_docs': [
        {
            'content': 'This is the content of the document 1',
            'link': '/documents/doc12345',
            'fileName': 'document1.pdf',
            'documentType': 'pdf',
            'fileId': 'd6e8b8a5-8fb6-4d48-9763-ff6c22c0e6e1',
        },
        {
            'content': 'This is the content of the document 2',
            'link': '/documents/doc12346',
            'fileName': 'document2.pdf',
            'documentType': 'pdf',
            'fileId': 'bd05bbae-5832-470d-8f75-4e291215ee07',
        }
    ]
}

web_sources_to_add = {
    "web_sources": [
        {
            "url": "url1",
            "description": "description1",
            "title": "title1",
            "paragraphs": "long paragraphs for first web sources"
        },
        {
            "url": "url2",
            "description": "description2",
            "title": "title2",
            "paragraphs": "long paragraphs for second web sources"
        }
    ]
}

example_answer = ModelServiceAnswer(
    response="This is an example answer generated by the model.",
    inference_time=0.123,
    model_code="MODEL123",
    model_name="ModelName2"
)

workspaces_orm_object = [
    WorkspaceDto(id=uuid4(), name="my workspace",
                 active=True,
                 description="My workspace description"),
    WorkspaceDto(id=uuid4(), name="my second workspace",
                 active=True,
                 description="My second workspace description")]
workspaces_data_object = [WorkspaceDto.from_orm(workspace) for workspace in workspaces_orm_object]

mock_workspace_input = WorkspaceInput(
    name="MockWorkspace",
    description="Mock Description",
    active=True
)

workspace_output_instance = WorkspaceOutput(
    id="f42c01ac-3285-410d-a070-a4c4419e9c1c",
    name="MockWorkspace",
    description="Mock Description",
    active=True
)

mock_workspace_output = Workspace(
    name="MockWorkspace",
    active=True,
    description="Mock Description",
    id='f42c01ac-3285-410d-a070-a4c4419e9c1c'
)

mocked_generated_tokens = ["hi", "how", "are", "you", "?"]

evil_seperation_token = """___"""

mocked_streaming_response_generator = [ModelStreamingInProgressResponse(
    status=StreamingResponseStatus.IN_PROGRESS,
    detail="streaming!",
    data=token
) for token in mocked_generated_tokens] + [
                                          model_service_streaming_done_answer
                                      ]

mocked_streaming_response_generator_with_error = [
    ModelStreamingInProgressResponse(
        status=StreamingResponseStatus.IN_PROGRESS,
        detail="streaming!",
        data=mocked_generated_tokens[0]),
    ModelStreamingErrorResponse(
        status=StreamingResponseStatus.ERROR,
        detail="error!",
        data=None)
]


def mock_streaming_response_behavior(content: bytes):
    """
        response = '{"status": "OK", "detail": "streaming!", "data": "hi"}{"status": "DONE", "detail": "Success", "data": {"response": "hihowareyou?", "prompt_length": 5, "inference_time": 0.1, "model_name": "gpt2", "metadata": {"load_in_8bit": 0, "load_in_4bit": 0, "max_new_tokens": 256, "no_repeat_ngram_size": 3, "repetition_penalty": 0.5}}}'

    :param content:
    :return:
    """

    # Split the response into individual JSON objects
    json_objects = content.decode().split(evil_seperation_token)

    for json_object in json_objects:
        if json_object:  # an empty string is returned at the end, skip it
            yield json.loads(json_object)
