"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_url():
    """Sample URL data."""
    return {
        "url": "https://example.com",
        "domain": "example.com",
        "is_subdomain": False
    }


@pytest.fixture
def sample_criteria():
    """Sample criteria data."""
    return {
        "name": "AI & Technology",
        "description": "Articles about artificial intelligence and technology",
        "keywords": ["AI", "machine learning", "technology"],
        "prompt": "Looking for news about AI developments"
    }


@pytest.fixture
def sample_article():
    """Sample article data."""
    return {
        "url": "https://example.com/article1",
        "title": "Sample Article Title",
        "content": "This is a sample article content about AI and machine learning.",
        "summary": "Sample article about AI.",
        "categories": ["Technology", "AI"],
        "tags": ["AI", "machine learning"],
        "relevance_scores": {}
    }

