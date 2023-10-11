from uuid import uuid4

from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.orm import declarative_base

from source.models.common_models import UUIDString

Model_base = declarative_base()


class Model(Model_base):
    """Available Models Table Model"""
    __tablename__ = "model"
    id = Column(UUIDString, primary_key=True, default=uuid4, unique=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    route = Column(String, nullable=False)
    available = Column(Boolean, nullable=False)
    default = Column(Boolean, nullable=False)
    type = Column(String, nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_date = Column(DateTime(timezone=True), server_default=func.now())
    max_web = Column(String, nullable=False)
    max_doc = Column(String, nullable=False)
