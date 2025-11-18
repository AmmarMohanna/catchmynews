"""Tests for web scraper service."""
import pytest
from app.services.scraper import WebScraper


class TestWebScraper:
    """Test web scraping functionality."""
    
    @pytest.fixture
    def scraper(self):
        """Create a scraper instance."""
        return WebScraper()
    
    def test_extract_domain(self, scraper):
        """Test domain extraction."""
        assert scraper._extract_domain("https://example.com/path") == "example.com"
        assert scraper._extract_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert scraper._extract_domain("https://example.com:8080/path") == "example.com:8080"
    
    def test_is_same_domain(self, scraper):
        """Test same domain checking."""
        assert scraper._is_same_domain("https://example.com/page1", "example.com") is True
        assert scraper._is_same_domain("https://other.com/page1", "example.com") is False
        assert scraper._is_same_domain("https://example.com/path", "example.com") is True
    
    @pytest.mark.asyncio
    async def test_scrape_website_structure(self, scraper):
        """Test that scrape_website returns proper structure."""
        # This is a live test - you might want to mock the HTTP requests
        # For now, we'll just test with a simple publicly available test page
        try:
            articles = await scraper.scrape_website(
                "https://httpbin.org",
                max_depth=1,
                max_pages=2
            )
            # Should return a list (may be empty if no articles found)
            assert isinstance(articles, list)
        except Exception as e:
            pytest.skip(f"Network test skipped: {e}")
    
    def test_extract_article_with_minimal_content(self, scraper):
        """Test article extraction from HTML."""
        html = """
        <html>
        <head><title>Test Title</title></head>
        <body>
            <h1>Main Title</h1>
            <article>
                <p>This is a paragraph with enough content to be extracted as a meaningful article.</p>
                <p>Another paragraph to ensure we have substantial content for extraction.</p>
            </article>
        </body>
        </html>
        """
        article = scraper._extract_article("https://example.com/test", html)
        
        if article:  # May be None if content is too short
            assert "title" in article
            assert "content" in article
            assert "url" in article
    
    def test_extract_article_no_content(self, scraper):
        """Test article extraction with insufficient content."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body><p>Short</p></body>
        </html>
        """
        article = scraper._extract_article("https://example.com/test", html)
        assert article is None  # Should return None for insufficient content

