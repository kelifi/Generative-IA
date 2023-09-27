from datetime import datetime
from uuid import uuid4

from source.models.conversations_models import Conversation, Question, Answer, AnswerAnalytics, \
    VersionedAnswer, SourceDocument, SourceWeb, Table
from source.models.model_table import Model
from source.schemas.models_schema import ModelInputSchema

random_user_id = str(uuid4())
question_db_id = "62abcde0-2b5e-4944-b30e-95c727931adb"
answer_db_id = "40b9be8f-6f95-4f4a-9caa-591c0b55faf9"
versioned_answer_db_id = "d875d722-be7e-48bb-89f1-d78960ba4eea"


def create_fresh_database_data() -> list[Table]:
    """Create data to insert in to the in-memory database, the reason for this function is to generate new ORM objects
    that are not bound to any session when executing multiple integration tests"""
    conversation1 = Conversation(id='0e16b7a6-d396-45fc-be6f-16f43882d09b', user_id=random_user_id,
                                 title="Conversation 1",
                                 creation_date=datetime(2023, 8, 1, 15, 19, 36),
                                 update_date=datetime(2023, 8, 1, 15, 19, 36))
    conversation2 = Conversation(id='a970dfb8-8be8-4e0e-927a-54247aece9c2', user_id=random_user_id,
                                 title="Conversation 2",
                                 creation_date=datetime(2023, 8, 2, 15, 19, 36),
                                 update_date=datetime(2023, 8, 1, 15, 19, 36))
    conversation3 = Conversation(id='4bf1e1df-498c-4f51-b289-fbfccf4bd6a5', user_id=random_user_id,
                                 title="Conversation 3",
                                 creation_date=datetime(2023, 8, 3, 15, 19, 36),
                                 update_date=datetime(2023, 8, 1, 15, 19, 36))
    conversations = [conversation1, conversation2, conversation3]

    question1 = Question(id=question_db_id, conversation_id=conversation1.id, content="Question content 1",
                         skip_doc=False,
                         skip_web=False)
    question2 = Question(id=str(uuid4()), conversation_id=conversation2.id, content="Question content 2", skip_doc=True,
                         skip_web=False)
    question3 = Question(id=str(uuid4()), conversation_id=conversation3.id, content="Question content 3",
                         skip_doc=False,
                         skip_web=True)
    questions = [question1, question2, question3]

    answer1 = Answer(id=answer_db_id, question_id=question1.id, content="Answer content 1",
                     creation_date=datetime(2023, 8, 3, 15, 19, 36))
    answer2 = Answer(id=str(uuid4()), question_id=question2.id, content="Answer content 2")
    answer3 = Answer(id=str(uuid4()), question_id=question3.id, content="Answer content 3")
    answers = [answer1, answer2, answer3]

    analytics1 = AnswerAnalytics(id=str(uuid4()), answer_id=answer1.id, inference_time=0.5, model_code="Model A")
    analytics2 = AnswerAnalytics(id=str(uuid4()), answer_id=answer2.id, inference_time=1.2, model_code="Model B")
    analytics3 = AnswerAnalytics(id=str(uuid4()), answer_id=answer3.id, inference_time=0.8, model_code="Model C")
    analytics = [analytics1, analytics2, analytics3]

    versioned_answer1 = VersionedAnswer(id=str(uuid4()), answer_id=answer1.id, content="version1", author="author1",
                                        creation_date=datetime(2023, 8, 3, 15, 19, 36))
    versioned_answer2 = VersionedAnswer(id=versioned_answer_db_id, answer_id=answer2.id, content="version2")
    versioned_answer3 = VersionedAnswer(id=str(uuid4()), answer_id=answer3.id, content="version3")
    answer_versions = [versioned_answer1, versioned_answer2, versioned_answer3]

    source_document1 = SourceDocument(id=str(uuid4()), question_id=question1.id, document_path="/path1",
                                      content="Document content 1",
                                      document_type="PDF")

    source_document2 = SourceDocument(id=str(uuid4()), question_id=question2.id, document_path="/path2",
                                      content="Document content 2",
                                      document_type="PDF")

    source_document3 = SourceDocument(id=str(uuid4()), question_id=question3.id, document_path="/path3",
                                      content="Document content 3",
                                      document_type="PDF")

    source_docs = [source_document1, source_document2, source_document3]

    source_web1 = SourceWeb(id=str(uuid4()), question_id=question1.id, url="https://web1.com",
                            description="Web source 1",
                            title="Web 1")
    source_web2 = SourceWeb(id=str(uuid4()), question_id=question2.id, url="https://web2.com",
                            description="Web source 2",
                            title="Web 2")
    source_web3 = SourceWeb(id=str(uuid4()), question_id=question3.id, url="https://web3.com",
                            description="Web source 3",
                            title="Web 3")
    source_webs = [source_web1, source_web2, source_web3]

    model_1 = Model(
        id=str(uuid4()),
        name="Example Model",
        code="model123",
        route="/models/model123",
        available=True,
        default=True,
        type="classification",
        max_web="2",
        max_doc="5"
    )

    model_2 = Model(
        id=str(uuid4()),
        name="Example Model",
        code="model122",
        route="/models/model123",
        available=False,
        default=False,
        type="chat",
        max_web="5",
        max_doc="5"
    )

    model_3 = Model(
        id=str(uuid4()),
        name="Example Model 2",
        code="model124",
        route="/models/model124",
        available=True,
        default=False,
        type="chat",
        max_web="2",
        max_doc="2"
    )
    models = [model_1, model_2, model_3]
    return [*conversations, *questions, *answers, *analytics, *answer_versions, *source_docs, *source_webs,
            *models]


model_input = ModelInputSchema(name="Example Model 2",
                               code="model124",
                               route="/models/model124",
                               available=True,
                               default=False,
                               type="chat",
                               max_web="2",
                               max_doc="2"
                               )
