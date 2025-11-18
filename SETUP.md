# 🚀 Setup Guide for NewsCatcher

This guide will walk you through setting up NewsCatcher from scratch.

## Prerequisites

### Required Software

1. **Docker Desktop** (includes Docker Compose)
   - macOS: [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Windows: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - Linux: Install Docker and Docker Compose separately
     ```bash
     # Docker
     curl -fsSL https://get.docker.com -o get-docker.sh
     sh get-docker.sh
     
     # Docker Compose
     sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
     sudo chmod +x /usr/local/bin/docker-compose
     ```

2. **OpenAI API Key**
   - Sign up at [OpenAI](https://platform.openai.com)
   - Navigate to [API Keys](https://platform.openai.com/api-keys)
   - Create a new API key
   - Save it securely (you'll need it in step 3)

### System Requirements

- **Minimum**: 4GB RAM, 10GB disk space
- **Recommended**: 8GB RAM, 20GB disk space
- **CPU**: 2+ cores

## Step-by-Step Setup

### 1. Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version
```

You should see version information for both commands.

### 2. Navigate to Project Directory

```bash
cd /Users/ammarmohanna/Desktop/NewsCatcher
```

### 3. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit the `.env` file with your favorite editor:

```bash
# macOS
nano .env

# or use VS Code
code .env
```

**Required**: Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Optional**: Customize other settings:

```env
# Database credentials (change for production)
POSTGRES_USER=newscatcher
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=newscatcher_db
```

Save and close the file.

### 4. Build and Start Services

```bash
# Build images (first time only, or after code changes)
docker-compose build

# Start all services
docker-compose up -d
```

The `-d` flag runs containers in detached mode (background).

### 5. Verify Services Are Running

```bash
docker-compose ps
```

You should see 5 services running:
- `newscatcher_postgres` (PostgreSQL)
- `newscatcher_redis` (Redis)
- `newscatcher_backend` (FastAPI)
- `newscatcher_celery` (Celery Worker)
- `newscatcher_frontend` (Streamlit)

### 6. Check Logs (Optional)

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker

# Press Ctrl+C to stop viewing logs
```

### 7. Access the Application

Open your web browser and navigate to:

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Initial Usage

### Add Your First URL

1. Open http://localhost:8501
2. Click on the **"Manage URLs"** tab
3. Expand **"➕ Add New URL"**
4. Enter a website URL (e.g., `https://news.ycombinator.com`)
5. Click **"Add URL"**

### Create Search Criteria

1. Go to the **"Manage Criteria"** tab
2. Expand **"➕ Add New Criteria"**
3. Fill in:
   - **Name**: "Technology News"
   - **Keywords**: "AI, technology, software, programming"
   - **Description**: "Latest technology and software news"
4. Click **"Add Criteria"**

### Start Scraping

1. Click the large **"🔄 UPDATE"** button in the sidebar
2. Wait a few moments (check the "Statistics" section for progress)
3. Go to the **"News Feed"** tab to see discovered articles

### View Results

1. In the **"News Feed"** tab:
   - Select a criteria to filter articles
   - Adjust relevance threshold
   - Click on articles to read them
2. Click **"🔗 Open"** to visit the original article
3. Mark articles as seen to track what you've read

## Common Setup Issues

### Issue: Port Already in Use

**Error**: "Port 8501/8000/5432 is already allocated"

**Solution**:
```bash
# Find and stop the conflicting service
# For macOS/Linux:
lsof -ti:8501 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Or change ports in docker-compose.yml
```

### Issue: Docker Daemon Not Running

**Error**: "Cannot connect to the Docker daemon"

**Solution**:
- Start Docker Desktop application
- Wait for Docker to fully start (whale icon in menu bar/system tray)

### Issue: Out of Memory

**Error**: Container keeps restarting

**Solution**:
1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory to at least 4GB
4. Click "Apply & Restart"

### Issue: API Key Invalid

**Error**: "OpenAI API authentication failed"

**Solution**:
1. Check your API key in `.env`
2. Verify key is valid at https://platform.openai.com/api-keys
3. Ensure there are no extra spaces or quotes around the key
4. Restart services: `docker-compose restart`

### Issue: Database Connection Failed

**Error**: "Could not connect to database"

**Solution**:
```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Stopping the Application

### Temporary Stop

```bash
# Stop services (data is preserved)
docker-compose stop

# Start again later
docker-compose start
```

### Complete Shutdown

```bash
# Stop and remove containers
docker-compose down

# To also remove volumes (deletes all data)
docker-compose down -v
```

## Updating the Application

If you make code changes:

```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Advanced Configuration

### Increase Scraping Limits

Edit `backend/app/config.py`:

```python
MAX_SCRAPING_DEPTH = 5        # Default: 3
MAX_PAGES_PER_DOMAIN = 100    # Default: 50
```

Then rebuild:

```bash
docker-compose build backend
docker-compose restart backend celery_worker
```

### Change OpenAI Model

Edit `backend/app/config.py`:

```python
OPENAI_MODEL = "gpt-4"  # Default: gpt-4o-mini
```

**Note**: GPT-4 is more capable but more expensive.

### Enable Debug Logging

Add to `.env`:

```env
LOG_LEVEL=DEBUG
```

Restart:
```bash
docker-compose restart
```

## Database Management

### Backup Database

```bash
docker-compose exec postgres pg_dump -U newscatcher newscatcher_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U newscatcher newscatcher_db < backup.sql
```

### Access Database Directly

```bash
docker-compose exec postgres psql -U newscatcher newscatcher_db
```

## Monitoring

### View Resource Usage

```bash
docker stats
```

### Check Service Health

```bash
# Backend health check
curl http://localhost:8000/

# Expected output: {"status":"ok","service":"NewsCatcher API"}
```

### View Celery Tasks

```bash
docker-compose logs celery_worker | tail -50
```

## Production Deployment

For production deployment, see the **Security Notes** section in README.md.

Key points:
1. Change all default passwords
2. Use environment-specific `.env` files
3. Enable HTTPS
4. Set up monitoring and alerting
5. Configure backups
6. Restrict CORS origins
7. Use a reverse proxy (nginx/traefik)

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Review README.md troubleshooting section
3. Test API directly: http://localhost:8000/docs
4. Verify environment variables: `cat .env`

---

🎉 **You're all set!** Enjoy using NewsCatcher!

