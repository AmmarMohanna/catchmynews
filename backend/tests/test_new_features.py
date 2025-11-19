"""Tests for new features: deduplication, fuzzy matching, search, caching, incremental scraping."""
import pytest
import asyncio
from app.models.article import Article
from app.models.url import URL
from app.services.ai_service import AIService
from app.services.cache_service import CacheService


class TestArticleDeduplication:
    """Test article deduplication feature."""
    
    def test_content_hash_generation(self):
        """Test that content hash is generated consistently."""
        hash1 = Article.generate_content_hash("Test Title", "Test content here")
        hash2 = Article.generate_content_hash("Test Title", "Test content here")
        hash3 = Article.generate_content_hash("Different", "Different content")
        
        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
        # Hash should be 64 chars (SHA-256 hex)
        assert len(hash1) == 64
    
    def test_content_hash_case_insensitive(self):
        """Test that hash is case-insensitive."""
        hash1 = Article.generate_content_hash("Test Title", "Test Content")
        hash2 = Article.generate_content_hash("test title", "test content")
        
        assert hash1 == hash2


class TestImprovedKeywordMatching:
    """Test improved keyword matching with fuzzy search."""
    
    @pytest.mark.asyncio
    async def test_exact_keyword_match(self):
        """Test exact keyword matching."""
        ai = AIService()
        score = await ai.match_criteria(
            "Article about AI",
            "This is about artificial intelligence",
            criteria_keywords=["AI", "technology"],
            criteria_prompt=None
        )
        # Should match "AI" exactly
        assert score > 0.0
    
    @pytest.mark.asyncio
    async def test_fuzzy_keyword_match(self):
        """Test fuzzy keyword matching."""
        ai = AIService()
        score = await ai.match_criteria(
            "Machine Learning Tutorial",
            "This tutorial covers machine learning algorithms",
            criteria_keywords=["machine-learning", "AI"],
            criteria_prompt=None
        )
        # Should match "machine-learning" to "machine learning" via normalization
        assert score >= 0.5
    
    @pytest.mark.asyncio
    async def test_prompt_keyword_extraction(self):
        """Test keyword extraction from prompt."""
        ai = AIService()
        score = await ai.match_criteria(
            "Python Programming Guide",
            "Learn Python programming with examples",
            criteria_keywords=None,
            criteria_prompt="Looking for Python programming tutorials"
        )
        # Should extract "python" and "programming" from prompt
        assert score > 0.0


class TestCacheService:
    """Test Redis caching functionality."""
    
    def test_cache_set_and_get(self):
        """Test setting and getting values from cache."""
        cache = CacheService()
        
        if cache.redis_client:
            # Test set and get
            cache.set("test_key", {"foo": "bar"}, ttl=60)
            result = cache.get("test_key")
            
            assert result is not None
            assert result["foo"] == "bar"
            
            # Clean up
            cache.delete("test_key")
    
    def test_cache_expiry(self):
        """Test cache TTL."""
        cache = CacheService()
        
        if cache.redis_client:
            cache.set("test_ttl", "value", ttl=1)
            assert cache.get("test_ttl") == "value"
            
            # Wait for expiry
            import time
            time.sleep(2)
            assert cache.get("test_ttl") is None
    
    def test_cache_pattern_delete(self):
        """Test deleting cache by pattern."""
        cache = CacheService()
        
        if cache.redis_client:
            cache.set("test:1", "value1")
            cache.set("test:2", "value2")
            cache.set("other:1", "value3")
            
            deleted = cache.delete_pattern("test:*")
            assert deleted >= 2
            
            assert cache.get("test:1") is None
            assert cache.get("test:2") is None
            assert cache.get("other:1") == "value3"
            
            # Clean up
            cache.delete("other:1")


class TestArticleSearch:
    """Test article search functionality."""
    
    def test_search_endpoint_exists(self, client):
        """Test that search endpoint is accessible."""
        response = client.get("/articles/search?q=test")
        # Should return 200 even with no results
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_search_with_results(self, client, db_session):
        """Test search returns matching articles."""
        # Create test URL and articles
        url = URL(url="https://example.com", domain="example.com")
        db_session.add(url)
        db_session.commit()
        
        article1 = Article(
            url="https://example.com/ai-article",
            title="Introduction to AI",
            content="This article discusses artificial intelligence",
            summary="AI basics",
            content_hash=Article.generate_content_hash("Introduction to AI", "This article discusses artificial intelligence"),
            source_url_id=url.id
        )
        article2 = Article(
            url="https://example.com/python",
            title="Python Programming",
            content="Learn Python programming",
            summary="Python tutorial",
            content_hash=Article.generate_content_hash("Python Programming", "Learn Python programming"),
            source_url_id=url.id
        )
        db_session.add_all([article1, article2])
        db_session.commit()
        
        # Search for "AI"
        response = client.get("/articles/search?q=AI")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
        assert any("AI" in r["title"] for r in results)


class TestIncrementalScraping:
    """Test incremental scraping with ETags and Last-Modified."""
    
    def test_url_model_has_cache_fields(self, db_session):
        """Test that URL model has caching fields."""
        url = URL(
            url="https://example.com",
            domain="example.com",
            last_etag="test-etag",
            last_modified="Mon, 01 Jan 2024 00:00:00 GMT"
        )
        db_session.add(url)
        db_session.commit()
        
        assert url.last_etag == "test-etag"
        assert url.last_modified == "Mon, 01 Jan 2024 00:00:00 GMT"
    
    @pytest.mark.asyncio
    async def test_scraper_returns_cache_headers(self):
        """Test that scraper returns ETags and Last-Modified."""
        from app.services.scraper import WebScraper
        scraper = WebScraper()
        
        # This would need a real test with mocked responses
        # For now, just verify the signature returns a tuple
        articles, etag, last_modified = await scraper.scrape_website(
            "https://httpbin.org",
            max_depth=1,
            max_pages=2
        )
        
        assert isinstance(articles, list)
        # etag and last_modified can be None if not provided by server
        assert etag is None or isinstance(etag, str)
        assert last_modified is None or isinstance(last_modified, str)

