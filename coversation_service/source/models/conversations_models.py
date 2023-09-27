from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean, Float, Integer

from source.models.common_models import Table, UUIDString
from source.models.workspace_models import Workspace


class Conversation(Table):
    """Conversation Table Model"""
    __tablename__ = "conversation"
    user_id = Column(UUIDString,
                     nullable=False)
    workspace_id = Column(UUIDString, ForeignKey(f"{Workspace.__tablename__}.id", ondelete='CASCADE'), nullable=True)
    title = Column(String, default="New Conversation", nullable=False)
    update_date = Column(DateTime(timezone=True), default=datetime.now, nullable=True)


class Question(Table):
    """Conversation Table Model"""
    __tablename__ = "question"
    conversation_id = Column(UUIDString, ForeignKey(f"{Conversation.__tablename__}.id", ondelete='CASCADE'),
                             nullable=False)
    content = Column(String, nullable=False)
    skip_doc = Column(Boolean, nullable=False, default=False)
    skip_web = Column(Boolean, nullable=False, default=False)


class AnswerTable(Table):
    """Abstract Table Model"""
    __abstract__ = True
    content = Column(String, nullable=False)
    author = Column(String, nullable=True, default=None)
    # edited should be set to nullable=True
    # sqlalchemy.exc.IntegrityError: make sense some existing rows have no defined edited
    edited = Column(Boolean, nullable=True, default=False)
    rating = Column(String, nullable=True)
    update_date = Column(DateTime(timezone=True), default=datetime.now)


class Answer(AnswerTable):
    """Conversation Table Model"""
    __tablename__ = "answer"
    question_id = Column(UUIDString, ForeignKey(f"{Question.__tablename__}.id", ondelete='CASCADE'),
                         nullable=False)


class AnswerAnalytics(Table):
    __tablename__ = 'answer_analytics'

    answer_id = Column(UUIDString, ForeignKey(f"{Answer.__tablename__}.id", ondelete='CASCADE'),
                       nullable=False)
    model_name = Column(String, nullable=True)

    inference_time = Column(Float, nullable=False)
    model_code = Column(String, nullable=True)
    prompt_length = Column(Integer, nullable=True)
    load_in_8bit = Column(Integer, nullable=True)
    load_in_4bit = Column(Integer, nullable=True)
    max_new_tokens = Column(Integer, nullable=True)
    no_repeat_ngram_size = Column(Integer, nullable=True)
    repetition_penalty = Column(Integer, nullable=True)


class VersionedAnswer(AnswerTable):
    """Conversation Table Model"""
    __tablename__ = "versioned_answer"
    answer_id = Column(UUIDString, ForeignKey(f"{Answer.__tablename__}.id", ondelete='CASCADE'),
                       nullable=False)


class SourceDocument(Table):
    """Conversation Table Model"""
    __tablename__ = "source_document"
    question_id = Column(UUIDString, ForeignKey(f"{Question.__tablename__}.id", ondelete='CASCADE'),
                         nullable=False)
    document_path = Column(String, nullable=False)
    content = Column(String, nullable=False)
    document_id = Column(UUIDString)
    document_type = Column(String, nullable=False)


class SourceWeb(Table):
    """Web Sources Table Model"""
    __tablename__ = "source_web"
    question_id = Column(UUIDString, ForeignKey(f"{Question.__tablename__}.id", ondelete='CASCADE'),
                         nullable=False)
    url = Column(String, nullable=False)
    description = Column(String, nullable=False)
    title = Column(String, nullable=False)
    paragraphs = Column(String)
