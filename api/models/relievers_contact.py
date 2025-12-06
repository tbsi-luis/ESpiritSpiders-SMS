from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

Base = declarative_base()

class RelieversContact(Base):
    """SQLAlchemy model for reliever contact information"""
    __tablename__ = "reliever_request_reliever_line"

    # Primary Keys & Foreign Keys
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, nullable=True)
    employee_id = Column(Integer, nullable=True)

    # Basic Info
    full_name = Column(String, nullable=False)
    contact = Column(String, nullable=False)

    # Status Tracking - THIS IS WHAT WE UPDATE
    status = Column(String, nullable=True)  # 'open', 'notified', 'Confirmed', etc.

    # Timestamps - matching actual database column names
    create_date = Column(DateTime, nullable=True)
    write_date = Column(DateTime, nullable=True)
    
    # User tracking
    create_uid = Column(Integer, nullable=True)
    write_uid = Column(Integer, nullable=True)

    # Additional fields
    notify = Column(Boolean, nullable=True)
    rank = Column(Integer, nullable=True)
    match_score = Column(Integer, nullable=True)
    matched_to = Column(String, nullable=True)
    matched_skills = Column(Text, nullable=True)


class RelieversContactSchema(BaseModel):
    """Pydantic schema for reliever contact information"""
    id: int
    request_id: Optional[int] = None
    employee_id: Optional[int] = None
    full_name: str
    contact: str
    status: Optional[str] = None
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

    class Config:
        from_attributes = True