from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Boolean, TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UUIDString(TypeDecorator):
    impl = String

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(String())

    def process_bind_param(self, value, dialect):
        if not value:
            return None
        if not isinstance(value, str):
            value = str(value)
        return value

    def process_result_value(self, value, dialect):
        if not value:
            return None
        return value


class Table(AbstractConcreteBase, Base):
    """Abstract Table Model"""
    id = Column(UUIDString, primary_key=True, default=uuid4, unique=True)
    creation_date = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    deleted = Column(Boolean, default=False)
