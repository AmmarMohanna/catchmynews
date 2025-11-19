"""Article model for storing scraped content."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

from app.database import Base


class Article(Base):
    """Model for scraped articles/news items."""
    
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Full content
    summary = Column(Text, nullable=True)  # AI-generated summary
    content_hash = Column(String(64), index=True)  # SHA-256 hash for deduplication
    
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
    
    @staticmethod
    def generate_content_hash(title: str, content: str) -> str:
        """Generate SHA-256 hash from title and content for deduplication."""
        # Use title + first 500 chars of content for hash
        text = f"{title}{content[:500]}".lower().strip()
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title[:50]})>"

