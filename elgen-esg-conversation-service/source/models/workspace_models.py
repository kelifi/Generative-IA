from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from source.models.common_models import Table, UUIDString
from source.models.source_models import SourceType


class WorkspaceType(Table):
    """WorkspaceType Table Model"""
    __tablename__ = "workspace_type"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    available = Column(Boolean, nullable=False, default=False)
    update_date = Column(DateTime(timezone=True), default=datetime.now, nullable=True)

    workspaces = relationship("Workspace", back_populates="type")


class Workspace(Table):
    """WorkspaceDto Table Model"""
    __tablename__ = "workspace"
    name = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)
    update_date = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
    type_id = Column(UUIDString, ForeignKey(f"{WorkspaceType.__tablename__}.id"), nullable=False)
    source_type_id = Column(UUIDString, ForeignKey(f"{SourceType.__tablename__}.id"), nullable=True)
    classification_change_enabled = Column(Boolean, nullable=True, default=True)
    available_model_codes = Column(String, nullable=True)
    stop_answer_process = Column(Boolean, nullable=True, default=False)

    type = relationship("WorkspaceType", back_populates="workspaces")


class ChatSuggestions(Table):
    """SuggestedQuestions Table Model"""
    __tablename__ = "workspace_chat_suggestions"
    content = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint('content', 'workspace_id', name='uq_content_workspace_combination'),
    )
    available = Column(Boolean, nullable=False, default=True)
    workspace_id = Column(
        UUIDString,
        ForeignKey(f"{Workspace.__tablename__}.id"),
        nullable=False
    )
    update_date = Column(DateTime(timezone=True), default=datetime.now, nullable=True)


class UsersWorkspaces(Table):
    """UsersWorkspaces Table Model"""
    __tablename__ = "users_workspaces"
    __table_args__ = (
        UniqueConstraint('user_id', 'workspace_id', name='uq_user_workspace_combination'),
    )
    user_id = Column(UUIDString, nullable=False)
    workspace_id = Column(
        UUIDString,
        ForeignKey(f"{Workspace.__tablename__}.id"),
        nullable=False
    )
