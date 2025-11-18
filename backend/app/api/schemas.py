"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict
from datetime import datetime


# URL Schemas
class URLCreate(BaseModel):
    url: str = Field(..., description="URL to track")


class URLResponse(BaseModel):
    id: int
    url: str
    domain: str
    is_subdomain: bool
    is_active: bool
    created_at: datetime
    last_scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Criteria Schemas
class CriteriaCreate(BaseModel):
    name: str = Field(..., description="Criteria name")
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    prompt: Optional[str] = None


class CriteriaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    prompt: Optional[str] = None
    is_active: Optional[bool] = None


class CriteriaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    keywords: List[str]
    prompt: Optional[str]
    is_active: bool
    created_at: datetime
    usage_count: int
    
    class Config:
        from_attributes = True


# Article Schemas
class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    summary: Optional[str]
    categories: List[str]
    tags: List[str]
    relevance_scores: Dict[str, float]
    source_url_id: int
    published_at: Optional[datetime]
    scraped_at: datetime
    is_seen: bool
    
    class Config:
        from_attributes = True


class ArticleDetail(ArticleResponse):
    content: Optional[str]


# Scraping Job Schemas
class ScrapingJobResponse(BaseModel):
    id: int
    url_id: int
    status: str
    pages_scraped: int
    articles_found: int
    subdomains_found: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Request/Response Schemas
class ScrapeRequest(BaseModel):
    url_ids: Optional[List[int]] = Field(None, description="Specific URL IDs to scrape. If None, scrapes all.")


class ScrapeResponse(BaseModel):
    task_id: Optional[str] = None
    tasks: Optional[List[Dict]] = None
    message: str


class CriteriaSuggestion(BaseModel):
    name: str
    description: str


class MarkSeenRequest(BaseModel):
    article_ids: List[int]


class StatsResponse(BaseModel):
    total_urls: int
    total_articles: int
    total_criteria: int
    unseen_articles: int
    active_jobs: int

