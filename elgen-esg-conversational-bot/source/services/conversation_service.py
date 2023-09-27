from typing import List
from uuid import UUID

from source.repositories.conversation_repository import ConversationRepository
from source.schemas.conversation_schema import ConversationSchema, AnswerSchema, QuestionSchema, ChatSchema, \
    ConversationIdSchema


class ConversationService:

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    def create_conversation(self, conversation_title: str, user_id: UUID) -> ConversationIdSchema:
        return ConversationIdSchema(
            id=self.conversation_repository.create_conversation(conversation_title=conversation_title, user_id=user_id))

    def update_conversation_title(self, new_conversation_title: str, conversation_id: UUID) -> ConversationSchema:
        return self.conversation_repository.update_conversation_title(conversation_id=conversation_id,
                                                                      new_conversation_title=new_conversation_title)

    def delete_conversation(self, conversation_id: UUID) -> None:
        self.conversation_repository.delete_conversation(conversation_id=conversation_id)

    def get_conversation_by_id(self, conversation_id: UUID):
        questions_list = []
        conversations = self.conversation_repository.get_conversation_by_id(conversation_id=conversation_id)

        for conversation in conversations:
            answer = AnswerSchema(id=conversation.answer_id, content=conversation.answer_content,
                                  creation_date=conversation.answer_date,
                                  sources=self.conversation_repository.get_sources_by_answer_id(
                                      answer_id=conversation.answer_id)) if conversation.answer_id else None

            questions_list.append(QuestionSchema(id=conversation.quest_id, content=conversation.quest_content,
                                                 creation_date=conversation.quest_date, answer=answer))

        return ChatSchema(id=conversation_id, questions=questions_list)

    def get_conversations_per_user(self, user_id: UUID) -> List[ConversationSchema]:
        conversations = self.conversation_repository.get_conversations_by_user(user_id=user_id)
        return [ConversationSchema.from_orm(conversation) for conversation in conversations]
