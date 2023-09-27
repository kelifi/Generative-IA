from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, UUID, ForeignKey, String, DateTime
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import declarative_base

from source.utils.constants import default_user_id

Base = declarative_base()


class Table(AbstractConcreteBase, Base):
    """Abstract Table Model"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)


class User(Table):
    """User Table Model"""
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=default_user_id, unique=True)


class Conversation(Table):
    """Conversation Table Model"""
    __tablename__ = "conversation"
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{User.__tablename__}.id", ondelete='CASCADE'),
                     nullable=False)
    title = Column(String, default="New Conversation", nullable=False)
    update_date = Column(DateTime, nullable=True)


class Question(Table):
    """Conversation Table Model"""
    __tablename__ = "question"
    conversation_id = Column(UUID(as_uuid=True), ForeignKey(f"{Conversation.__tablename__}.id", ondelete='CASCADE'),
                             nullable=False)
    content = Column(String, nullable=False)


class Answer(Table):
    """Conversation Table Model"""
    __tablename__ = "answer"
    question_id = Column(UUID(as_uuid=True), ForeignKey(f"{Question.__tablename__}.id", ondelete='CASCADE'),
                         nullable=False)
    content = Column(String, nullable=False)


class SourceDocument(Table):
    """Conversation Table Model"""
    __tablename__ = "source_document"
    answer_id = Column(UUID(as_uuid=True), ForeignKey(f"{Answer.__tablename__}.id", ondelete='CASCADE'),
                       nullable=False)
    document_path = Column(String, nullable=False)
    content = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
