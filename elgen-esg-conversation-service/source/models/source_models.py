from datetime import datetime

from sqlalchemy import Column, String, JSON, Boolean, DateTime

from source.models.common_models import Table, UUIDString


class Source(Table):
    """Sources Table Model"""
    __tablename__ = "sources"
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    workspace_id = Column(UUIDString, nullable=True)
    user_id = Column(UUIDString, nullable=True)
    source_metadata = Column(JSON, nullable=True)


class SourceType(Table):
    """SourceType Table Model"""
    __tablename__ = "source_type"
    name = Column(String, nullable=False)
    type_name = Column(String, nullable=True)
    available = Column(Boolean, nullable=False, default=False)
    description = Column(String, nullable=True)
    update_date = Column(DateTime(timezone=True), default=datetime.now, nullable=True)
