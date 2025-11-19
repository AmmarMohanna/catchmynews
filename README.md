# NewsCatcher

A powerful, AI-powered news aggregation and analysis platform that scrapes multiple websites, discovers subdomains, and intelligently categorizes content based on your interests.

## Features

- **Dynamic URL Management**: Add/remove URLs through an intuitive UI
- **Subdomain Discovery**: Automatically finds and scrapes subdomains via web crawling
- **AI-Powered Analysis**: 
  - Automatic article summarization
  - Content categorization and tagging
  - Keyword-based relevance matching
  - AI-suggested criteria based on scraped content
- **Custom Criteria**: Define search interests using keywords or natural language prompts
- **Background Scraping**: Fast, async scraping with Celery workers
- **Smart Caching**: Redis-backed caching for optimal performance
- **Seen/Unseen Tracking**: Keep track of new articles
- **Fully Dockerized**: Easy deployment with docker-compose

## Architecture

```
┌─────────────────┐
│   Streamlit     │  Frontend (Port 8501)
│   Frontend      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    FastAPI      │  Backend API (Port 8000)
│    Backend      │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐
│Postgres│ │ Redis │ │ Celery │ │ OpenAI │
│   DB   │ │ Cache │ │ Worker │ │   API  │
└────────┘ └───────┘ └────────┘ └────────┘
```

### Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **AI**: OpenAI API (GPT-4o-mini)
- **Scraping**: BeautifulSoup4 + httpx
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
```

3. **Start the application**

```bash
docker-compose up -d
```

This will start all services:
- Frontend (Streamlit): http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

4. **Access the application**

Open your browser and go to: **http://localhost:8501**

### First Time Setup

1. Add some URLs to track (e.g., news websites, blogs)
2. Define your criteria/interests
3. Click the **UPDATE** button to start scraping
4. Watch as articles are discovered, scraped, and analyzed!

## Usage Guide

### Managing URLs

1. Navigate to the **"Manage URLs"** tab
2. Click **"Add New URL"** and enter a website URL
3. Click **UPDATE** in the sidebar to scrape the URL
4. The system will automatically discover subdomains

### Creating Criteria

1. Navigate to the **"Manage Criteria"** tab
2. Click **"Add New Criteria"**
3. Fill in:
   - **Name**: e.g., "AI & Machine Learning"
   - **Keywords (optional)**: e.g., "AI, machine learning, neural networks, GPT"
   - **Sentence (optional)**: e.g., "Articles about artificial intelligence and deep learning"
   - Both keywords and sentence words are used for matching (common words filtered)
4. Save the criteria

Note: You can provide keywords, a sentence, or both. Keywords are used directly for matching, while sentences are processed to extract meaningful words (excluding common words like "the", "a", "is").

### Getting AI Recommendations

1. After scraping some articles, go to **"Manage Criteria"**
2. Click **"Get AI Recommendations"**
3. The LLM analyzes your articles and suggests criteria based on common themes
4. Use these recommendations as inspiration for your own criteria

### Filtering Articles

1. In the **"News Feed"** tab:
2. Select a criteria from the dropdown
3. Adjust the minimum relevance score slider
4. Toggle **"Unseen Only"** to show only new articles
5. Click on article cards to read more

## Running Tests

### Backend Tests

```bash
# Enter the backend container
docker-compose exec backend bash

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html
```

Or use the test script:

```bash
docker-compose exec backend bash run_tests.sh
```

### Test Categories

- **API Tests**: Test all REST endpoints
- **Model Tests**: Test database models and relationships
- **Scraper Tests**: Test web scraping functionality

## Configuration

### Environment Variables

Edit `.env` to customize:

```env
# Database
POSTGRES_USER=newscatcher
POSTGRES_PASSWORD=newscatcher_pass
POSTGRES_DB=newscatcher_db

# OpenAI
OPENAI_API_KEY=your_key_here
```

### Scraping Settings

Edit `backend/app/config.py`:

```python
MAX_SCRAPING_DEPTH = 3        # How deep to follow links
MAX_PAGES_PER_DOMAIN = 50     # Max pages per domain
REQUEST_TIMEOUT = 30          # Request timeout in seconds
RATE_LIMIT_DELAY = 1.0        # Delay between requests
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### URLs
- `GET /urls` - List all tracked URLs
- `POST /urls` - Add a new URL
- `DELETE /urls/{url_id}` - Remove a URL
- `PATCH /urls/{url_id}/toggle` - Toggle URL active status

#### Criteria
- `GET /criteria` - List all criteria
- `POST /criteria` - Create new criteria
- `PATCH /criteria/{criteria_id}` - Update criteria
- `DELETE /criteria/{criteria_id}` - Delete criteria
- `GET /criteria/suggestions` - Get AI-suggested criteria

#### Articles
- `GET /articles` - List articles with filters
- `GET /articles/{article_id}` - Get article details
- `POST /articles/mark-seen` - Mark articles as seen

#### Scraping
- `POST /scrape` - Trigger scraping
- `GET /scraping-jobs` - Get scraping job history

#### Statistics
- `GET /stats` - Get application statistics

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose down
docker-compose up -d
```

### Database issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Scraping not working

1. Check Celery worker logs: `docker-compose logs celery_worker`
2. Ensure Redis is running: `docker-compose ps redis`
3. Check backend logs: `docker-compose logs backend`

### OpenAI API errors

- Verify your API key is correct in `.env`
- Check your OpenAI account has credits
- Restart services after changing `.env`: `docker-compose restart`

## Project Structure

```
NewsCatcher/
├── backend/
│   ├── app/
│   │   ├── api/          # API schemas and endpoints
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic (scraper, AI)
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   ├── main.py       # FastAPI app
│   │   └── celery_worker.py  # Celery tasks
│   ├── tests/            # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py           # Streamlit app
│   ├── Dockerfile
│   └── requirements.txt
├── postgres/
│   └── init.sql         # Database initialization
├── docker-compose.yml
├── .env.example
└── README.md
```

## Security Notes

### For Production Deployment

1. **Change default passwords** in `.env`
2. **Restrict CORS origins** in `backend/app/main.py`
3. **Use HTTPS** with a reverse proxy (nginx/traefik)
4. **Set up authentication** for the frontend
5. **Use secrets management** for API keys
6. **Enable rate limiting** on the API
7. **Regular backups** of the PostgreSQL database

### robots.txt Compliance

The scraper respects website policies. However:
- Always check if a website allows scraping
- Add appropriate delays between requests
- Consider reaching out to site owners for permission
- Use responsibly and ethically

## Development

### Adding New Features

1. **Backend changes**: Edit files in `backend/app/`
2. **Frontend changes**: Edit `frontend/app.py`
3. **Models**: Add/modify files in `backend/app/models/`
4. **API endpoints**: Edit `backend/app/main.py`
5. **Tests**: Add tests in `backend/tests/`

### Hot Reload

Both backend and frontend support hot reload during development:
- Backend: Code changes trigger auto-reload (uvicorn --reload)
- Frontend: Streamlit auto-detects changes

### Running Without Docker

<details>
<summary>Click to expand</summary>

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis separately
# Then:
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export OPENAI_API_KEY=...

uvicorn app.main:app --reload
celery -A app.celery_worker worker --loglevel=info
```

#### Frontend

```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export BACKEND_URL=http://localhost:8000
streamlit run app.py
```

</details>

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

This project is provided as-is for educational purposes.

## Acknowledgments

- OpenAI for the GPT API
- FastAPI for the excellent web framework
- Streamlit for the amazing UI framework
- The open-source community

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review logs: `docker-compose logs`
3. Check API docs: http://localhost:8000/docs

---
