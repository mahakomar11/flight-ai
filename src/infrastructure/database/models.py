import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    phone = Column(Text, nullable=False)
    answers = Column(JSON, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendation"

    id = Column(DB_UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    message = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, index=True, nullable=False)
    delivered = Column(Boolean, nullable=False)
