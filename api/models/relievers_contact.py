from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

Base = declarative_base()

class RelieversContact(Base):
    """SQLAlchemy model for reliever contact information"""
    __tablename__ = "reliever_request_reliever_line"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    contact = Column(String, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RelieversContactSchema(BaseModel):
    """Pydantic schema for reliever contact information"""
    id: int
    full_name: str
    contact: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True