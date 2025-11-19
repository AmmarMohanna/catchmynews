# NewsCatcher Architecture

This document provides a detailed overview of NewsCatcher's architecture, components, and data flow.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                      (Streamlit Frontend)                       │
│                         Port: 8501                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│                        (FastAPI)                                │
│                         Port: 8000                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   URLs   │  │ Criteria │  │ Articles │  │ Scraping │      │
│  │ Endpoints│  │Endpoints │  │Endpoints │  │Endpoints │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└───────────────┬─────────────────────┬───────────────────────────┘
                │                     │
     ┌──────────┴──────────┐          │
     ▼                     ▼          ▼
┌─────────┐          ┌──────────────────┐
│PostgreSQL│         │  Background Jobs │
│Database │          │  (Celery Worker) │
│Port:5432│          └────────┬─────────┘
└─────────┘                   │
     ▲                        ▼
     │              ┌───────────────────┐
     │              │  Redis (Broker)   │
     │              │   Port: 6379      │
     │              └───────────────────┘
     │                        │
     │                        ▼
     │              ┌───────────────────┐
     │              │  Scraping Service │
     │              │  ┌─────────────┐  │
     │              │  │Web Crawler  │  │
     │              │  │Subdomain    │  │
     │              │  │Discovery    │  │
     │              │  └─────────────┘  │
     │              └───────────────────┘
     │                        │
     └────────────────────────┤
                              ▼
                    ┌──────────────────┐
                    │   OpenAI API     │
                    │ ┌──────────────┐ │
                    │ │Summarization │ │
                    │ │Categorization│ │
                    │ │Relevance     │ │
                    │ │Scoring       │ │
                    │ └──────────────┘ │
                    └──────────────────┘
```

## Components

### 1. Frontend (Streamlit)

**Technology**: Python Streamlit
**Port**: 8501
**Container**: `newscatcher_frontend`

**Responsibilities**:
- User interface for all interactions
- Real-time updates and statistics
- Article visualization and filtering
- URL and criteria management

**Key Features**:
- News Feed with filtering
- URL Management
- Criteria Management
- Real-time statistics

**Files**:
- `frontend/app.py` - Main Streamlit application

### 2. Backend API (FastAPI)

**Technology**: Python FastAPI
**Port**: 8000
**Container**: `newscatcher_backend`

**Responsibilities**:
- RESTful API endpoints
- Request validation (Pydantic)
- Database operations (SQLAlchemy)
- Task queue management
- Business logic orchestration

**API Endpoints**:

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Health | `/` | GET | Health check |
| URLs | `/urls` | GET | List all URLs |
| | `/urls` | POST | Add new URL |
| | `/urls/{id}` | DELETE | Delete URL |
| | `/urls/{id}/toggle` | PATCH | Toggle active status |
| Criteria | `/criteria` | GET | List criteria |
| | `/criteria` | POST | Create criteria |
| | `/criteria/{id}` | PATCH | Update criteria |
| | `/criteria/{id}` | DELETE | Delete criteria |
| | `/criteria/suggestions` | GET | AI suggestions |
| Articles | `/articles` | GET | List articles (filtered) |
| | `/articles/{id}` | GET | Get article details |
| | `/articles/mark-seen` | POST | Mark as seen |
| Scraping | `/scrape` | POST | Trigger scraping |
| | `/scraping-jobs` | GET | Job history |
| Stats | `/stats` | GET | Statistics |

**Files**:
- `backend/app/main.py` - FastAPI application
- `backend/app/api/` - API schemas and routes
- `backend/app/database.py` - Database configuration

### 3. Database (PostgreSQL)

**Technology**: PostgreSQL 15
**Port**: 5432
**Container**: `newscatcher_postgres`

**Schema**:

```sql
┌─────────────────┐
│      urls       │
├─────────────────┤
│ id (PK)         │
│ url             │
│ domain          │
│ is_subdomain    │
│ parent_url_id   │
│ is_active       │
│ created_at      │
│ last_scraped_at │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────┐
│    articles     │
├─────────────────┤
│ id (PK)         │
│ url             │
│ title           │
│ content         │
│ summary         │
│ source_url_id(FK)│
│ categories      │
│ tags            │
│ relevance_scores│
│ published_at    │
│ scraped_at      │
│ is_seen         │
│ is_active       │
└─────────────────┘

┌─────────────────┐
│    criteria     │
├─────────────────┤
│ id (PK)         │
│ name            │
│ description     │
│ keywords        │
│ prompt          │
│ is_active       │
│ created_at      │
│ usage_count     │
└─────────────────┘

┌─────────────────┐
│ scraping_jobs   │
├─────────────────┤
│ id (PK)         │
│ url_id (FK)     │
│ status          │
│ celery_task_id  │
│ pages_scraped   │
│ articles_found  │
│ subdomains_found│
│ error_message   │
│ started_at      │
│ completed_at    │
└─────────────────┘
```

**Files**:
- `backend/app/models/` - SQLAlchemy models

### 4. Cache & Message Broker (Redis)

**Technology**: Redis 7
**Port**: 6379
**Container**: `newscatcher_redis`

**Usage**:
- **Database 0**: General caching
- **Database 1**: Celery message broker
- **Database 2**: Celery result backend

**Cached Data**:
- Scraped content (temporary)
- API responses
- Session data

**Files**: N/A (configured in `docker-compose.yml`)

### 5. Background Worker (Celery)

**Technology**: Celery with Redis broker
**Container**: `newscatcher_celery`

**Tasks**:

| Task | Description | Trigger |
|------|-------------|---------|
| `scrape_url_task` | Scrape single URL | API call or scheduled |
| `scrape_all_urls_task` | Scrape all URLs | UPDATE button |
| `calculate_relevance_scores_task` | Update relevance scores | After criteria change |

**Task Flow**:

```
User clicks UPDATE
        ▼
API POST /scrape
        ▼
Queue scrape_all_urls_task
        ▼
For each URL:
  Queue scrape_url_task
        ▼
Celery Worker executes:
  1. Discover subdomains
  2. Scrape pages
  3. Extract articles
  4. Call AI service
  5. Save to database
        ▼
Update scraping_job status
```

**Configuration**:
- Concurrency: 4 workers
- Time limit: 1 hour per task
- Retry policy: No automatic retries (manual re-scrape)

**Files**:
- `backend/app/celery_worker.py` - Task definitions

### 6. Services

#### 6.1 Scraping Service

**File**: `backend/app/services/scraper.py`

**Class**: `WebScraper`

**Methods**:
- `discover_subdomains(url)` - Find subdomains via link crawling
- `scrape_website(url, max_depth, max_pages)` - Deep scraping
- `_scrape_recursive()` - Recursive link following
- `_fetch_url()` - HTTP request with retry
- `_extract_article()` - Content extraction from HTML
- `_apply_rate_limit()` - Rate limiting per domain

**Features**:
- Async/await for performance
- Respects rate limits (1 second default)
- Extracts meaningful content only
- Handles redirects and errors gracefully
- User-Agent spoofing

#### 6.2 AI Service

**File**: `backend/app/services/ai_service.py`

**Class**: `AIService`

**Methods**:
- `summarize_article(title, content)` - Generate summary using LLM
- `categorize_article(title, content)` - Extract categories & tags using LLM
- `match_criteria(article, criteria)` - Calculate relevance (0-1) using keyword matching
- `suggest_criteria(articles)` - Generate criteria suggestions using LLM
- `batch_process_articles(articles)` - Bulk processing

**OpenAI API Usage**:
- Model: `gpt-4o-mini` (fast & cost-effective)
- Temperature: 0.1-0.7 (depending on task)
- Max tokens: Limited per task
- Used for: Summarization, categorization, and criteria suggestions only
- NOT used for: Article matching (uses keyword matching instead)

**Cost Optimization**:
- Content truncation (max 3000 chars for summarization)
- Keyword-based matching (no API calls)
- Batch processing where possible
- Caching of results

## Data Flow

### Scraping Flow

```
1. User adds URL
   └─▶ Save to database (urls table)

2. User clicks UPDATE
   └─▶ API: POST /scrape
       └─▶ Queue: scrape_all_urls_task
           └─▶ For each URL:
               └─▶ Queue: scrape_url_task

3. Celery Worker processes task
   ├─▶ Discover subdomains (if main domain)
   │   └─▶ Save subdomains to database
   ├─▶ Scrape website (max depth & pages)
   │   ├─▶ Fetch HTML
   │   ├─▶ Extract articles
   │   └─▶ Follow internal links
   ├─▶ AI Processing
   │   ├─▶ Summarize each article
   │   ├─▶ Categorize & tag
   │   └─▶ Calculate relevance scores
   └─▶ Save articles to database

4. Frontend polls for updates
   └─▶ Display new articles in News Feed
```

### Filtering Flow

```
1. User selects criteria
   └─▶ Frontend: Update filter state

2. Fetch articles with filter
   └─▶ API: GET /articles?criteria_id=X&min_relevance=0.5

3. Backend filters articles
   └─▶ Query database
   └─▶ Filter by relevance_scores JSON field
   └─▶ Return filtered results

4. Frontend displays articles
   └─▶ Render article cards
   └─▶ Show relevance score
   └─▶ Highlight unseen articles
```

## Scalability Considerations

### Current Limitations

- Single Celery worker (4 concurrent tasks)
- In-memory rate limiting (lost on restart)
- Simple relevance filtering (not indexed)

### Scaling Options

1. **Horizontal Scaling**:
   - Add more Celery workers: `docker-compose scale celery_worker=5`
   - Use load balancer for API (nginx/HAProxy)
   - Add read replicas for PostgreSQL

2. **Performance Optimization**:
   - Add database indexes on frequently queried fields
   - Implement Elasticsearch for full-text search
   - Use Redis caching more aggressively
   - Implement pagination for large result sets

3. **Advanced Features**:
   - Scheduled scraping (Celery Beat)
   - Incremental scraping (only new content)
   - Vector embeddings for semantic search
   - Real-time notifications (WebSockets)

## Security Architecture

### Current Security

- ✅ Database credentials via environment variables
- ✅ API key management via .env
- ✅ CORS middleware (configurable)
- ✅ SQL injection protection (SQLAlchemy)
- ✅ Input validation (Pydantic)
- ⚠️ No authentication (local use)

### Production Security Checklist

- [ ] Add JWT authentication
- [ ] Enable HTTPS with SSL certificates
- [ ] Implement rate limiting (per user/IP)
- [ ] Use secrets manager (AWS Secrets Manager, Vault)
- [ ] Enable database encryption at rest
- [ ] Set up VPC/network isolation
- [ ] Implement audit logging
- [ ] Add API key rotation
- [ ] Enable CSP headers
- [ ] Set up monitoring & alerting

## Configuration Management

### Environment Variables

All configuration via `.env` file:

```env
# Database
DATABASE_URL=postgresql://...
POSTGRES_USER=...
POSTGRES_PASSWORD=...

# Redis
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...

# OpenAI
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

### Application Config

**File**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Scraping
    MAX_SCRAPING_DEPTH: int = 3
    MAX_PAGES_PER_DOMAIN: int = 50
    RATE_LIMIT_DELAY: float = 1.0
    
    # AI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
```

## Development Workflow

```
1. Edit code
   └─▶ Auto-reload (FastAPI/Streamlit)

2. Run tests
   └─▶ pytest backend/tests/

3. Commit changes
   └─▶ Git commit

4. Rebuild if needed
   └─▶ docker-compose build

5. Deploy
   └─▶ docker-compose up -d
```

## Monitoring & Observability

### Current Logging

- FastAPI: uvicorn logs
- Celery: task execution logs
- Database: PostgreSQL logs
- Redis: connection logs

### Recommended Additions

- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger or DataDog
- **Alerting**: PagerDuty or Slack integration
- **Log Aggregation**: ELK Stack or Loki

---

This architecture is designed for:
- Easy local development
- Simple deployment (Docker Compose)
- Horizontal scalability
- Maintainability
- Extensibility

