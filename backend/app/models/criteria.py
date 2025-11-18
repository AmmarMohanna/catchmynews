"""Criteria model for storing user-defined search criteria."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from datetime import datetime

from app.database import Base


class Criteria(Base):
    """Model for search criteria/interests."""
    
    __tablename__ = "criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Criteria can be keywords or prompts
    keywords = Column(JSON, default=list)  # List of keywords
    prompt = Column(Text, nullable=True)  # Natural language prompt
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Criteria(id={self.id}, name={self.name})>"

