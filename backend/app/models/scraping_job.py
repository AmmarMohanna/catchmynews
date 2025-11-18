"""Scraping job model for tracking scraping tasks."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ScrapingJob(Base):
    """Model for tracking scraping jobs."""
    
    __tablename__ = "scraping_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    
    # Job status
    status = Column(String, default="pending")  # pending, running, completed, failed
    celery_task_id = Column(String, nullable=True, unique=True, index=True)
    
    # Results
    pages_scraped = Column(Integer, default=0)
    articles_found = Column(Integer, default=0)
    subdomains_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    job_metadata = Column(JSON, default=dict)  # Additional metadata
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    url = relationship("URL", back_populates="scraping_jobs")
    
    def __repr__(self):
        return f"<ScrapingJob(id={self.id}, status={self.status})>"

