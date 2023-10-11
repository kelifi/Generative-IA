import uuid
from datetime import datetime

from configuration.config import BFFSettings
from source.schemas.api_schemas import QuestionSchema, ConversationHistoryOutputSchema, ConversationOutputSchema

consumer_settings = BFFSettings(HOST="0.0.0.0",
                                PORT=8004,
                                CONVERSATION_SERVICE_URL="http://localhost:1234",
                                SOURCES_SERVICE_URL="http://localhost:1234",
                                PROJECT_NAME="EL-GEN-bff-service",
                                ROOT_PATH="")
question_instance = QuestionSchema(
    id=uuid.uuid4(),
    content="Sample question content",
    creation_date=datetime.now(),
    answer=None,
    skip_doc=False,
    skip_web=True
)
conversation_answers = ConversationHistoryOutputSchema(
    id=uuid.uuid4(),
    questions=[]
)
conversation_output = ConversationOutputSchema(
            id=uuid.uuid4(),
            title="Sample conversation",
            creation_date=datetime.now(),
            update_date=datetime.now()
        )
