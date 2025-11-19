"""Celery worker configuration and tasks."""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

from celery import Celery
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.url import URL
from app.models.article import Article
from app.models.scraping_job import ScrapingJob
from app.services.scraper import WebScraper
from app.services.ai_service import AIService
from app.services.cache_service import cache_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'newscatcher',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)


def get_db() -> Session:
    """Get database session for tasks."""
    return SessionLocal()


@celery_app.task(bind=True, name='scrape_url')
def scrape_url_task(self, url_id: int, discover_subdomains: bool = True):
    """
    Background task to scrape a URL.
    
    Args:
        url_id: Database ID of the URL to scrape
        discover_subdomains: Whether to discover and scrape subdomains
    """
    logger.info(f"Starting scrape task for URL ID: {url_id}")
    
    db = get_db()
    job = None
    
    try:
        # Get URL from database
        url_obj = db.query(URL).filter(URL.id == url_id).first()
        if not url_obj:
            logger.error(f"URL with ID {url_id} not found")
            return {"error": "URL not found"}
        
        # Create scraping job
        job = ScrapingJob(
            url_id=url_id,
            status="running",
            celery_task_id=self.request.id,
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        
        # Run scraping
        scraper = WebScraper()
        ai_service = AIService()
        
        # Discover subdomains if requested
        subdomain_urls = []
        if discover_subdomains and not url_obj.is_subdomain:
            logger.info(f"Discovering subdomains for {url_obj.url}")
            subdomain_urls = asyncio.run(scraper.discover_subdomains(url_obj.url))
            
            # Save discovered subdomains
            for subdomain_url in subdomain_urls:
                existing = db.query(URL).filter(URL.url == subdomain_url).first()
                if not existing:
                    subdomain = URL(
                        url=subdomain_url,
                        domain=scraper._extract_domain(subdomain_url),
                        is_subdomain=True,
                        parent_url_id=url_id
                    )
                    db.add(subdomain)
            
            db.commit()
            job.subdomains_found = len(subdomain_urls)
        
        # Scrape main URL with incremental scraping support
        logger.info(f"Scraping {url_obj.url}")
        articles_data, etag, last_modified = asyncio.run(
            scraper.scrape_website(url_obj.url, url_obj.last_etag, url_obj.last_modified)
        )
        job.pages_scraped = len(articles_data)
        
        # Update cache headers
        if etag:
            url_obj.last_etag = etag
        if last_modified:
            url_obj.last_modified = last_modified
        
        # Process with AI
        logger.info(f"Processing {len(articles_data)} articles with AI")
        articles_data = asyncio.run(ai_service.batch_process_articles(articles_data))
        
        # Save articles to database
        new_articles = 0
        duplicates_skipped = 0
        for article_data in articles_data:
            # Generate content hash for deduplication
            content_hash = Article.generate_content_hash(
                article_data.get('title', ''),
                article_data.get('content', '')
            )
            
            # Check if article already exists by URL or content hash
            existing = db.query(Article).filter(
                (Article.url == article_data['url']) | 
                (Article.content_hash == content_hash)
            ).first()
            
            if existing:
                # Skip duplicate - only update if URL matches but content changed
                if existing.url == article_data['url'] and existing.content_hash != content_hash:
                    existing.title = article_data.get('title', existing.title)
                    existing.content = article_data.get('content', existing.content)
                    existing.summary = article_data.get('summary', existing.summary)
                    existing.categories = article_data.get('categories', existing.categories)
                    existing.tags = article_data.get('tags', existing.tags)
                    existing.content_hash = content_hash
                    existing.scraped_at = datetime.utcnow()
                else:
                    duplicates_skipped += 1
            else:
                # Create new article
                article = Article(
                    url=article_data['url'],
                    title=article_data.get('title', ''),
                    content=article_data.get('content', ''),
                    summary=article_data.get('summary', ''),
                    content_hash=content_hash,
                    source_url_id=url_id,
                    scraped_at=datetime.utcnow(),
                    categories=article_data.get('categories', []),
                    tags=article_data.get('tags', []),
                    is_seen=False
                )
                db.add(article)
                new_articles += 1
        
        db.commit()
        job.articles_found = new_articles
        
        # Update URL last scraped time
        url_obj.last_scraped_at = datetime.utcnow()
        
        # Complete job
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Invalidate caches after new articles
        if new_articles > 0:
            cache_service.invalidate_articles_cache()
        
        logger.info(f"Completed scrape task for {url_obj.url}: {new_articles} new articles, {duplicates_skipped} duplicates skipped")
        
        return {
            "url": url_obj.url,
            "pages_scraped": job.pages_scraped,
            "articles_found": job.articles_found,
            "subdomains_found": job.subdomains_found,
            "duplicates_skipped": duplicates_skipped
        }
        
    except Exception as e:
        logger.error(f"Error in scrape task: {e}", exc_info=True)
        
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        return {"error": str(e)}
        
    finally:
        db.close()


@celery_app.task(name='scrape_all_urls')
def scrape_all_urls_task():
    """Background task to scrape all active URLs."""
    logger.info("Starting scrape all URLs task")
    
    db = get_db()
    
    try:
        # Get all active URLs
        urls = db.query(URL).filter(URL.is_active == True).all()
        logger.info(f"Found {len(urls)} active URLs to scrape")
        
        # Trigger scrape tasks for each URL
        results = []
        for url_obj in urls:
            # Only discover subdomains for non-subdomain URLs
            result = scrape_url_task.delay(url_obj.id, discover_subdomains=not url_obj.is_subdomain)
            results.append({
                "url": url_obj.url,
                "task_id": result.id
            })
        
        return {"tasks_started": len(results), "results": results}
        
    except Exception as e:
        logger.error(f"Error in scrape all URLs task: {e}", exc_info=True)
        return {"error": str(e)}
        
    finally:
        db.close()


@celery_app.task(name='calculate_relevance_scores')
def calculate_relevance_scores_task():
    """Background task to calculate relevance scores for all articles against all criteria."""
    logger.info("Starting relevance score calculation task")
    
    db = get_db()
    
    try:
        from app.models.criteria import Criteria
        
        # Get all active criteria
        criteria_list = db.query(Criteria).filter(Criteria.is_active == True).all()
        
        # Get all articles
        articles = db.query(Article).filter(Article.is_active == True).all()
        
        logger.info(f"Calculating relevance for {len(articles)} articles against {len(criteria_list)} criteria")
        
        ai_service = AIService()
        
        for article in articles:
            relevance_scores = {}
            
            for criteria in criteria_list:
                score = asyncio.run(ai_service.match_criteria(
                    article.title,
                    article.summary or article.content[:500],
                    criteria.keywords,
                    criteria.prompt
                ))
                
                relevance_scores[str(criteria.id)] = score
            
            article.relevance_scores = relevance_scores
        
        db.commit()
        
        logger.info("Completed relevance score calculation")
        return {"articles_processed": len(articles), "criteria_count": len(criteria_list)}
        
    except Exception as e:
        logger.error(f"Error calculating relevance scores: {e}", exc_info=True)
        return {"error": str(e)}
        
    finally:
        db.close()

