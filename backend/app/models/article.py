"""Article model for storing scraped content."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Article(Base):
    """Model for scraped articles/news items."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Full content
    summary = Column(Text, nullable=True)  # AI-generated summary
    
    # Metadata
    source_url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # AI-generated fields
    categories = Column(JSON, default=list)  # List of categories
    tags = Column(JSON, default=list)  # List of tags
    relevance_scores = Column(JSON, default=dict)  # {criteria_id: score}
    
    # Tracking
    is_seen = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    source_url = relationship("URL", back_populates="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title[:50]})>"

