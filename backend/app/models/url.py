"""URL model for storing tracked URLs and their subdomains."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class URL(Base):
    """Model for tracked URLs."""
    
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    is_subdomain = Column(Boolean, default=False)
    parent_url_id = Column(Integer, nullable=True)  # Reference to parent domain if this is a subdomain
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)
    
    # Incremental scraping support
    last_etag = Column(String, nullable=True)  # ETag for cache validation
    last_modified = Column(String, nullable=True)  # Last-Modified header
    
    # Relationships
    articles = relationship("Article", back_populates="source_url", cascade="all, delete-orphan")
    scraping_jobs = relationship("ScrapingJob", back_populates="url", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<URL(id={self.id}, url={self.url})>"

