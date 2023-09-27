from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint

from source.models.common_models import Table, UUIDString


class Workspace(Table):
    """WorkspaceDto Table Model"""
    __tablename__ = "workspace"
    name = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=False)
    description = Column(String, nullable=True)
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
