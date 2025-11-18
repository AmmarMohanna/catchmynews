"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://newscatcher:newscatcher_pass@localhost:5432/newscatcher_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"  # Fast and cost-effective
    
    # Scraping settings
    MAX_SCRAPING_DEPTH: int = 3  # How many levels deep to follow links
    MAX_PAGES_PER_DOMAIN: int = 50  # Max pages to scrape per domain
    REQUEST_TIMEOUT: int = 30  # Seconds
    RATE_LIMIT_DELAY: float = 1.0  # Seconds between requests to same domain
    USER_AGENT: str = "NewsCatcher/1.0 (Educational scraper; respects robots.txt)"
    
    # Cache settings
    CACHE_EXPIRY: int = 3600  # 1 hour in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

