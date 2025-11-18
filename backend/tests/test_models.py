"""Tests for database models."""
import pytest
from datetime import datetime
from app.models.url import URL
from app.models.article import Article
from app.models.criteria import Criteria
from app.models.scraping_job import ScrapingJob


class TestURLModel:
    """Test URL model."""
    
    def test_create_url(self, db_session):
        """Test creating a URL."""
        url = URL(
            url="https://example.com",
            domain="example.com",
            is_subdomain=False
        )
        db_session.add(url)
        db_session.commit()
        
        assert url.id is not None
        assert url.is_active is True
        assert url.created_at is not None
    
    def test_url_relationships(self, db_session):
        """Test URL relationships with articles."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article = Article(
            url="https://example.com/article1",
            title="Test Article",
            content="Content",
            source_url_id=url.id
        )
        db_session.add(article)
        db_session.commit()
        
        assert len(url.articles) == 1
        assert url.articles[0].title == "Test Article"


class TestArticleModel:
    """Test Article model."""
    
    def test_create_article(self, db_session):
        """Test creating an article."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article = Article(
            url="https://example.com/article1",
            title="Test Article",
            content="Article content here",
            summary="Summary",
            source_url_id=url.id,
            categories=["Technology", "AI"],
            tags=["AI", "ML"],
            relevance_scores={"1": 0.85}
        )
        db_session.add(article)
        db_session.commit()
        
        assert article.id is not None
        assert article.is_seen is False
        assert article.is_active is True
        assert len(article.categories) == 2
        assert len(article.tags) == 2
        assert article.relevance_scores["1"] == 0.85


class TestCriteriaModel:
    """Test Criteria model."""
    
    def test_create_criteria(self, db_session):
        """Test creating criteria."""
        criteria = Criteria(
            name="AI & Technology",
            description="Articles about AI",
            keywords=["AI", "machine learning"],
            prompt="Looking for AI news"
        )
        db_session.add(criteria)
        db_session.commit()
        
        assert criteria.id is not None
        assert criteria.is_active is True
        assert criteria.usage_count == 0
        assert len(criteria.keywords) == 2


class TestScrapingJobModel:
    """Test ScrapingJob model."""
    
    def test_create_scraping_job(self, db_session):
        """Test creating a scraping job."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        job = ScrapingJob(
            url_id=url.id,
            status="pending",
            celery_task_id="test-task-123"
        )
        db_session.add(job)
        db_session.commit()
        
        assert job.id is not None
        assert job.status == "pending"
        assert job.pages_scraped == 0
        assert job.articles_found == 0
    
    def test_scraping_job_relationship(self, db_session):
        """Test scraping job relationship with URL."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        job = ScrapingJob(url_id=url.id, status="completed")
        db_session.add(job)
        db_session.commit()
        
        assert job.url.url == "https://example.com"
        assert len(url.scraping_jobs) == 1

