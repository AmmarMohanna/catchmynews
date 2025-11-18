"""Tests for API endpoints."""
import pytest
from app.models.url import URL
from app.models.criteria import Criteria
from app.models.article import Article


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns OK."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestURLEndpoints:
    """Test URL management endpoints."""
    
    def test_create_url(self, client):
        """Test creating a new URL."""
        response = client.post("/urls", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com"
        assert data["domain"] == "example.com"
        assert data["is_active"] is True
    
    def test_create_duplicate_url(self, client):
        """Test creating duplicate URL fails."""
        client.post("/urls", json={"url": "https://example.com"})
        response = client.post("/urls", json={"url": "https://example.com"})
        assert response.status_code == 400
    
    def test_get_urls(self, client, db_session):
        """Test fetching all URLs."""
        # Create test URLs
        url1 = URL(url="https://example.com", domain="example.com")
        url2 = URL(url="https://test.com", domain="test.com")
        db_session.add_all([url1, url2])
        db_session.commit()
        
        response = client.get("/urls")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_delete_url(self, client, db_session):
        """Test deleting a URL."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        response = client.delete(f"/urls/{url.id}")
        assert response.status_code == 200
        
        # Verify deletion
        assert db_session.query(URL).filter(URL.id == url.id).first() is None
    
    def test_toggle_url(self, client, db_session):
        """Test toggling URL active status."""
        url = URL(url="https://example.com", domain="example.com", is_active=True)
        db_session.add(url)
        db_session.commit()
        
        response = client.patch(f"/urls/{url.id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestCriteriaEndpoints:
    """Test criteria management endpoints."""
    
    def test_create_criteria(self, client):
        """Test creating new criteria."""
        criteria_data = {
            "name": "AI News",
            "description": "Articles about AI",
            "keywords": ["AI", "machine learning"],
            "prompt": "Looking for AI news"
        }
        response = client.post("/criteria", json=criteria_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI News"
        assert len(data["keywords"]) == 2
    
    def test_create_duplicate_criteria(self, client):
        """Test creating duplicate criteria fails."""
        criteria_data = {"name": "AI News", "keywords": ["AI"]}
        client.post("/criteria", json=criteria_data)
        response = client.post("/criteria", json=criteria_data)
        assert response.status_code == 400
    
    def test_get_criteria(self, client, db_session):
        """Test fetching all criteria."""
        crit1 = Criteria(name="AI", keywords=["AI"])
        crit2 = Criteria(name="Tech", keywords=["technology"])
        db_session.add_all([crit1, crit2])
        db_session.commit()
        
        response = client.get("/criteria")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_update_criteria(self, client, db_session):
        """Test updating criteria."""
        crit = Criteria(name="AI", keywords=["AI"])
        db_session.add(crit)
        db_session.commit()
        
        update_data = {"name": "AI & ML", "keywords": ["AI", "ML"]}
        response = client.patch(f"/criteria/{crit.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI & ML"
    
    def test_delete_criteria(self, client, db_session):
        """Test deleting criteria."""
        crit = Criteria(name="AI", keywords=["AI"])
        db_session.add(crit)
        db_session.commit()
        
        response = client.delete(f"/criteria/{crit.id}")
        assert response.status_code == 200
        
        # Verify deletion
        assert db_session.query(Criteria).filter(Criteria.id == crit.id).first() is None


class TestArticleEndpoints:
    """Test article endpoints."""
    
    def test_get_articles(self, client, db_session):
        """Test fetching articles."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article1 = Article(
            url="https://example.com/article1",
            title="Test Article 1",
            content="Content 1",
            source_url_id=url.id
        )
        article2 = Article(
            url="https://example.com/article2",
            title="Test Article 2",
            content="Content 2",
            source_url_id=url.id
        )
        db_session.add_all([article1, article2])
        db_session.commit()
        
        response = client.get("/articles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_article_detail(self, client, db_session):
        """Test fetching single article details."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article = Article(
            url="https://example.com/article1",
            title="Test Article",
            content="Full content here",
            source_url_id=url.id
        )
        db_session.add(article)
        db_session.commit()
        
        response = client.get(f"/articles/{article.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Article"
        assert "content" in data
    
    def test_mark_articles_seen(self, client, db_session):
        """Test marking articles as seen."""
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article = Article(
            url="https://example.com/article1",
            title="Test Article",
            content="Content",
            source_url_id=url.id,
            is_seen=False
        )
        db_session.add(article)
        db_session.commit()
        
        response = client.post("/articles/mark-seen", json={"article_ids": [article.id]})
        assert response.status_code == 200
        
        # Verify article is marked as seen
        db_session.refresh(article)
        assert article.is_seen is True


class TestStatsEndpoint:
    """Test statistics endpoint."""
    
    def test_get_stats(self, client, db_session):
        """Test fetching application statistics."""
        # Create test data
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article = Article(
            url="https://example.com/article1",
            title="Test Article",
            content="Content",
            source_url_id=url.id,
            is_seen=False
        )
        db_session.add(article)
        
        crit = Criteria(name="AI", keywords=["AI"])
        db_session.add(crit)
        db_session.commit()
        
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_urls"] == 1
        assert data["total_articles"] == 1
        assert data["total_criteria"] == 1
        assert data["unseen_articles"] == 1

