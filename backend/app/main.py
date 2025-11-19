"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models.url import URL
from app.models.article import Article
from app.models.criteria import Criteria
from app.models.scraping_job import ScrapingJob
from app.api.schemas import (
    URLCreate, URLResponse,
    CriteriaCreate, CriteriaUpdate, CriteriaResponse,
    ArticleResponse, ArticleDetail,
    ScrapingJobResponse,
    ScrapeRequest, ScrapeResponse,
    CriteriaSuggestion,
    MarkSeenRequest,
    StatsResponse
)
from app.services.scraper import WebScraper
from app.services.ai_service import AIService
from app.services.cache_service import cache_service
from app.celery_worker import scrape_url_task, scrape_all_urls_task, calculate_relevance_scores_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app."""
    # Startup
    logger.info("Starting NewsCatcher API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down NewsCatcher API...")


# Create FastAPI app
app = FastAPI(
    title="NewsCatcher API",
    description="API for scraping and analyzing news from multiple sources",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# URL Management Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "NewsCatcher API"}


@app.get("/urls", response_model=List[URLResponse], tags=["URLs"])
async def get_urls(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all tracked URLs."""
    query = db.query(URL)
    if active_only:
        query = query.filter(URL.is_active == True)
    urls = query.all()
    return urls


@app.post("/urls", response_model=URLResponse, tags=["URLs"])
async def create_url(
    url_data: URLCreate,
    db: Session = Depends(get_db)
):
    """Add a new URL to track."""
    # Check if URL already exists
    existing = db.query(URL).filter(URL.url == url_data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="URL already exists")
    
    # Extract domain
    scraper = WebScraper()
    domain = scraper._extract_domain(url_data.url)
    
    # Create new URL
    new_url = URL(
        url=url_data.url,
        domain=domain,
        is_subdomain=False
    )
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    
    logger.info(f"Added new URL: {url_data.url}")
    return new_url


@app.delete("/urls/{url_id}", tags=["URLs"])
async def delete_url(
    url_id: int,
    db: Session = Depends(get_db)
):
    """Delete a tracked URL."""
    url_obj = db.query(URL).filter(URL.id == url_id).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")
    
    db.delete(url_obj)
    db.commit()
    
    logger.info(f"Deleted URL: {url_obj.url}")
    return {"message": "URL deleted successfully"}


@app.patch("/urls/{url_id}/toggle", response_model=URLResponse, tags=["URLs"])
async def toggle_url(
    url_id: int,
    db: Session = Depends(get_db)
):
    """Toggle URL active status."""
    url_obj = db.query(URL).filter(URL.id == url_id).first()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")
    
    url_obj.is_active = not url_obj.is_active
    db.commit()
    db.refresh(url_obj)
    
    return url_obj


# ============================================================================
# Criteria Management Endpoints
# ============================================================================

@app.get("/criteria", response_model=List[CriteriaResponse], tags=["Criteria"])
async def get_criteria(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all criteria."""
    query = db.query(Criteria)
    if active_only:
        query = query.filter(Criteria.is_active == True)
    criteria = query.all()
    return criteria


@app.post("/criteria", response_model=CriteriaResponse, tags=["Criteria"])
async def create_criteria(
    criteria_data: CriteriaCreate,
    db: Session = Depends(get_db)
):
    """Create new search criteria."""
    # Check if name already exists
    existing = db.query(Criteria).filter(Criteria.name == criteria_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Criteria with this name already exists")
    
    new_criteria = Criteria(
        name=criteria_data.name,
        description=criteria_data.description,
        keywords=criteria_data.keywords,
        prompt=criteria_data.prompt
    )
    db.add(new_criteria)
    db.commit()
    db.refresh(new_criteria)
    
    # Trigger relevance score calculation
    calculate_relevance_scores_task.delay()
    
    logger.info(f"Created new criteria: {criteria_data.name}")
    return new_criteria


@app.patch("/criteria/{criteria_id}", response_model=CriteriaResponse, tags=["Criteria"])
async def update_criteria(
    criteria_id: int,
    criteria_data: CriteriaUpdate,
    db: Session = Depends(get_db)
):
    """Update existing criteria."""
    criteria_obj = db.query(Criteria).filter(Criteria.id == criteria_id).first()
    if not criteria_obj:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Update fields
    if criteria_data.name is not None:
        criteria_obj.name = criteria_data.name
    if criteria_data.description is not None:
        criteria_obj.description = criteria_data.description
    if criteria_data.keywords is not None:
        criteria_obj.keywords = criteria_data.keywords
    if criteria_data.prompt is not None:
        criteria_obj.prompt = criteria_data.prompt
    if criteria_data.is_active is not None:
        criteria_obj.is_active = criteria_data.is_active
    
    db.commit()
    db.refresh(criteria_obj)
    
    # Trigger relevance score recalculation
    calculate_relevance_scores_task.delay()
    
    return criteria_obj


@app.delete("/criteria/{criteria_id}", tags=["Criteria"])
async def delete_criteria(
    criteria_id: int,
    db: Session = Depends(get_db)
):
    """Delete criteria."""
    criteria_obj = db.query(Criteria).filter(Criteria.id == criteria_id).first()
    if not criteria_obj:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    db.delete(criteria_obj)
    db.commit()
    
    return {"message": "Criteria deleted successfully"}


@app.get("/criteria/suggestions", response_model=List[CriteriaSuggestion], tags=["Criteria"])
async def get_criteria_suggestions(
    db: Session = Depends(get_db)
):
    """Get AI-suggested criteria based on scraped articles."""
    # Get recent articles
    articles = db.query(Article).filter(Article.is_active == True).limit(20).all()
    
    if not articles:
        return []
    
    # Prepare article data
    articles_data = [
        {"title": a.title, "summary": a.summary}
        for a in articles
    ]
    
    ai_service = AIService()
    suggestions = await ai_service.suggest_criteria(articles_data)
    
    return suggestions


# ============================================================================
# Article Endpoints
# ============================================================================

@app.get("/articles", response_model=List[ArticleResponse], tags=["Articles"])
async def get_articles(
    criteria_id: Optional[int] = None,
    min_relevance: float = 0.0,
    unseen_only: bool = False,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get articles with optional filtering."""
    query = db.query(Article).filter(Article.is_active == True)
    
    if unseen_only:
        query = query.filter(Article.is_seen == False)
    
    # Filter by criteria relevance
    if criteria_id:
        # This is a simplified filter - in production you'd want a more efficient approach
        all_articles = query.all()
        filtered = [
            a for a in all_articles
            if a.relevance_scores.get(str(criteria_id), 0) >= min_relevance
        ]
        # Apply pagination
        return filtered[offset:offset + limit]
    
    articles = query.order_by(Article.scraped_at.desc()).offset(offset).limit(limit).all()
    return articles


@app.get("/articles/search", response_model=List[ArticleResponse], tags=["Articles"])
async def search_articles(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Search articles by title, summary, or content with caching."""
    # Check cache first (cache for 5 minutes)
    cache_key = f"search:{q}:{limit}:{offset}"
    cached = cache_service.get(cache_key)
    if cached:
        logger.debug(f"Returning cached search results for '{q}'")
        return [ArticleResponse(**a) for a in cached]
    
    search_term = f"%{q}%"
    
    articles = db.query(Article).filter(
        Article.is_active == True
    ).filter(
        (Article.title.ilike(search_term)) |
        (Article.summary.ilike(search_term)) |
        (Article.content.ilike(search_term))
    ).order_by(
        Article.scraped_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Cache results for 5 minutes
    article_dicts = [
        {
            "id": a.id,
            "url": a.url,
            "title": a.title,
            "summary": a.summary,
            "categories": a.categories,
            "tags": a.tags,
            "relevance_scores": a.relevance_scores,
            "source_url_id": a.source_url_id,
            "published_at": a.published_at,
            "scraped_at": a.scraped_at,
            "is_seen": a.is_seen
        }
        for a in articles
    ]
    cache_service.set(cache_key, article_dicts, ttl=300)
    
    logger.info(f"Search for '{q}' returned {len(articles)} results")
    return articles


@app.get("/articles/{article_id}", response_model=ArticleDetail, tags=["Articles"])
async def get_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed article information."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@app.post("/articles/mark-seen", tags=["Articles"])
async def mark_articles_seen(
    request: MarkSeenRequest,
    db: Session = Depends(get_db)
):
    """Mark articles as seen."""
    articles = db.query(Article).filter(Article.id.in_(request.article_ids)).all()
    
    for article in articles:
        article.is_seen = True
    
    db.commit()
    
    return {"message": f"Marked {len(articles)} articles as seen"}


# ============================================================================
# Scraping Endpoints
# ============================================================================

@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def trigger_scrape(
    request: ScrapeRequest = None,
    db: Session = Depends(get_db)
):
    """Trigger scraping for URLs."""
    if request and request.url_ids:
        # Scrape specific URLs
        tasks = []
        for url_id in request.url_ids:
            url_obj = db.query(URL).filter(URL.id == url_id).first()
            if url_obj:
                result = scrape_url_task.delay(url_id, discover_subdomains=not url_obj.is_subdomain)
                tasks.append({
                    "url": url_obj.url,
                    "task_id": result.id
                })
        
        return ScrapeResponse(
            tasks=tasks,
            message=f"Started scraping {len(tasks)} URLs"
        )
    else:
        # Scrape all URLs
        result = scrape_all_urls_task.delay()
        return ScrapeResponse(
            task_id=result.id,
            message="Started scraping all URLs"
        )


@app.get("/scraping-jobs", response_model=List[ScrapingJobResponse], tags=["Scraping"])
async def get_scraping_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get scraping job history."""
    query = db.query(ScrapingJob)
    
    if status:
        query = query.filter(ScrapingJob.status == status)
    
    jobs = query.order_by(ScrapingJob.created_at.desc()).limit(limit).all()
    return jobs


# ============================================================================
# Statistics Endpoints
# ============================================================================

@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(db: Session = Depends(get_db)):
    """Get application statistics with caching."""
    # Try to get from cache first
    cached = cache_service.get("stats")
    if cached:
        logger.debug("Returning cached stats")
        return StatsResponse(**cached)
    
    # Calculate stats
    total_urls = db.query(URL).filter(URL.is_active == True).count()
    total_articles = db.query(Article).filter(Article.is_active == True).count()
    total_criteria = db.query(Criteria).filter(Criteria.is_active == True).count()
    unseen_articles = db.query(Article).filter(
        Article.is_active == True,
        Article.is_seen == False
    ).count()
    active_jobs = db.query(ScrapingJob).filter(
        ScrapingJob.status.in_(["pending", "running"])
    ).count()
    
    stats = {
        "total_urls": total_urls,
        "total_articles": total_articles,
        "total_criteria": total_criteria,
        "unseen_articles": unseen_articles,
        "active_jobs": active_jobs
    }
    
    # Cache for 30 seconds
    cache_service.set("stats", stats, ttl=30)
    
    return StatsResponse(**stats)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

