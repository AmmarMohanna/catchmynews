"""Web scraping service with subdomain discovery and content extraction."""
import asyncio
import re
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper with subdomain discovery and deep crawling."""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.rate_limit_delays: Dict[str, float] = {}
        
    async def discover_subdomains(self, base_url: str) -> List[str]:
        """
        Discover subdomains by crawling the base URL and finding links.
        
        Args:
            base_url: The base URL to start discovery from
            
        Returns:
            List of discovered subdomain URLs
        """
        logger.info(f"Discovering subdomains for {base_url}")
        subdomains = set()
        base_domain = self._extract_domain(base_url)
        
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                # Fetch the homepage
                response = await self._fetch_url(client, base_url)
                if not response:
                    return []
                
                # Parse and find all links
                soup = BeautifulSoup(response.text, 'lxml')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    absolute_url = urljoin(base_url, href)
                    
                    # Check if it's a subdomain of the base domain
                    link_domain = self._extract_domain(absolute_url)
                    if link_domain and link_domain != base_domain and base_domain in link_domain:
                        subdomains.add(absolute_url)
                        
        except Exception as e:
            logger.error(f"Error discovering subdomains for {base_url}: {e}")
            
        logger.info(f"Found {len(subdomains)} subdomains for {base_url}")
        return list(subdomains)
    
    async def scrape_website(
        self, 
        url: str, 
        max_depth: int = None,
        max_pages: int = None
    ) -> List[Dict]:
        """
        Scrape a website following internal links.
        
        Args:
            url: Starting URL to scrape
            max_depth: Maximum depth to follow links (default from settings)
            max_pages: Maximum pages to scrape (default from settings)
            
        Returns:
            List of scraped articles with metadata
        """
        if max_depth is None:
            max_depth = settings.MAX_SCRAPING_DEPTH
        if max_pages is None:
            max_pages = settings.MAX_PAGES_PER_DOMAIN
            
        logger.info(f"Starting scrape of {url} (depth={max_depth}, max_pages={max_pages})")
        
        self.visited_urls.clear()
        articles = []
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            await self._scrape_recursive(
                client=client,
                url=url,
                base_domain=self._extract_domain(url),
                current_depth=0,
                max_depth=max_depth,
                articles=articles,
                max_pages=max_pages
            )
            
        logger.info(f"Scraped {len(articles)} articles from {url}")
        return articles
    
    async def _scrape_recursive(
        self,
        client: httpx.AsyncClient,
        url: str,
        base_domain: str,
        current_depth: int,
        max_depth: int,
        articles: List[Dict],
        max_pages: int
    ):
        """Recursively scrape pages following internal links."""
        
        # Check limits
        if current_depth > max_depth or len(articles) >= max_pages:
            return
            
        # Check if already visited
        if url in self.visited_urls:
            return
            
        self.visited_urls.add(url)
        
        # Rate limiting
        await self._apply_rate_limit(base_domain)
        
        # Fetch page
        response = await self._fetch_url(client, url)
        if not response:
            return
            
        # Extract article content
        article = self._extract_article(url, response.text)
        if article:
            articles.append(article)
            
        # Find and follow internal links
        if current_depth < max_depth:
            soup = BeautifulSoup(response.text, 'lxml')
            links = soup.find_all('a', href=True)
            
            # Collect internal links
            internal_links = []
            for link in links:
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Only follow links within the same domain
                if self._is_same_domain(absolute_url, base_domain) and absolute_url not in self.visited_urls:
                    internal_links.append(absolute_url)
                    
            # Recursively scrape internal links (limited to avoid explosion)
            for internal_link in internal_links[:10]:  # Limit to 10 links per page
                if len(articles) >= max_pages:
                    break
                await self._scrape_recursive(
                    client, internal_link, base_domain, 
                    current_depth + 1, max_depth, articles, max_pages
                )
    
    async def _fetch_url(self, client: httpx.AsyncClient, url: str) -> Optional[httpx.Response]:
        """Fetch a URL with error handling."""
        try:
            headers = {
                'User-Agent': settings.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return None
                
            return response
            
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None
    
    def _extract_article(self, url: str, html: str) -> Optional[Dict]:
        """Extract article content from HTML."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Try to find title
            title = None
            if soup.find('h1'):
                title = soup.find('h1').get_text(strip=True)
            elif soup.find('title'):
                title = soup.find('title').get_text(strip=True)
            
            # Extract main content
            content_tags = soup.find_all(['article', 'main', 'div'], class_=re.compile(r'content|article|post|entry'))
            
            if not content_tags:
                # Fallback: get all paragraphs
                content_tags = soup.find_all('p')
            
            content_parts = []
            for tag in content_tags:
                text = tag.get_text(strip=True, separator=' ')
                if len(text) > 50:  # Only meaningful content
                    content_parts.append(text)
            
            content = '\n\n'.join(content_parts)
            
            # Only return if we found meaningful content
            if title and len(content) > 100:
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'scraped_at': datetime.utcnow()
                }
            
        except Exception as e:
            logger.warning(f"Error extracting article from {url}: {e}")
            
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to the same domain."""
        try:
            domain = self._extract_domain(url)
            return domain == base_domain
        except:
            return False
    
    async def _apply_rate_limit(self, domain: str):
        """Apply rate limiting per domain."""
        if domain in self.rate_limit_delays:
            await asyncio.sleep(settings.RATE_LIMIT_DELAY)
        self.rate_limit_delays[domain] = datetime.utcnow().timestamp()

