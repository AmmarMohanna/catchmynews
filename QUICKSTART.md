# 🚀 NewsCatcher - Quickstart Guide

Get up and running with NewsCatcher in 5 minutes!

## Prerequisites

✅ Docker Desktop installed and running  
✅ OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation (3 Steps)

### Step 1: Configure API Key

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 2: Start the Application

**Option A: Using the start script (Recommended)**

```bash
./start.sh
```

**Option B: Using Docker Compose**

```bash
docker-compose up -d
```

**Option C: Using Make**

```bash
make up
```

### Step 3: Access the UI

Open your browser: **http://localhost:8501**

## First Usage (2 Minutes)

### 1. Add a URL

- Go to **"Manage URLs"** tab
- Click **"➕ Add New URL"**
- Enter: `https://news.ycombinator.com`
- Click **"Add URL"**

### 2. Create Criteria

- Go to **"Manage Criteria"** tab
- Click **"➕ Add New Criteria"**
- Fill in:
  - **Name**: "Tech News"
  - **Keywords**: "AI, technology, programming"
- Click **"Add Criteria"**

### 3. Start Scraping

- Click the big **"🔄 UPDATE"** button in the sidebar
- Wait 30-60 seconds
- Go to **"News Feed"** tab to see results!

## That's It! 🎉

You now have:
- ✅ A working news aggregator
- ✅ AI-powered summarization
- ✅ Automatic categorization
- ✅ Relevance filtering

## What's Next?

### Add More Sources

Popular news sources to try:
- `https://techcrunch.com`
- `https://arstechnica.com`
- `https://www.theverge.com`
- `https://github.com/trending`
- `https://dev.to`

### Explore Features

1. **Filter by Criteria**: Select different criteria to see relevant articles
2. **Adjust Relevance**: Use the slider to filter by relevance score
3. **Unseen Articles**: Toggle to see only new articles
4. **Change Theme**: Try different color schemes in the sidebar
5. **AI Suggestions**: Let AI suggest criteria based on your content

### Advanced Usage

- **View API**: http://localhost:8000/docs
- **Run Tests**: `make test`
- **View Logs**: `make logs`
- **Stop Services**: `make down`

## Common Commands

```bash
# Start services
./start.sh
# or
make up

# Stop services
docker-compose down
# or
make down

# View logs
docker-compose logs -f
# or
make logs

# Restart services
docker-compose restart
# or
make restart

# Run tests
make test

# Check status
docker-compose ps
# or
make status
```

## Troubleshooting

### Application won't start?

```bash
# Check if Docker is running
docker ps

# Check logs
docker-compose logs -f
```

### No articles appearing?

1. Wait 1-2 minutes after clicking UPDATE
2. Check **Statistics** in sidebar for "Active Jobs"
3. Check logs: `docker-compose logs celery_worker`

### OpenAI errors?

- Verify API key in `.env` is correct
- Check you have credits: https://platform.openai.com/account/billing
- Restart: `docker-compose restart`

## Getting Help

📖 **Full Documentation**: See `README.md`  
🏗️ **Architecture Details**: See `ARCHITECTURE.md`  
⚙️ **Setup Guide**: See `SETUP.md`  
🤝 **Contributing**: See `CONTRIBUTING.md`

## Key Features to Try

### 1. Subdomain Discovery
Add a main domain and watch it discover subdomains automatically!

### 2. Relevance Scoring
Each article gets a relevance score (0-100%) for each criteria.

### 3. AI Summarization
Every article is automatically summarized for quick reading.

### 4. Smart Categorization
AI automatically categorizes and tags each article.

### 5. Seen/Unseen Tracking
Keep track of what you've read with the "NEW" badge.

### 6. Multiple Color Themes
Choose from 5 different color schemes!

## Performance Tips

### For Faster Scraping

Edit `backend/app/config.py`:

```python
MAX_SCRAPING_DEPTH = 2  # Reduce from 3
MAX_PAGES_PER_DOMAIN = 25  # Reduce from 50
```

### For Better Results

Use specific criteria:

```
✅ Good: "AI, machine learning, neural networks, GPT"
❌ Too broad: "technology"
```

## Production Deployment

For production use:

1. Change database password in `.env`
2. Set up HTTPS with nginx
3. Add authentication
4. Enable rate limiting
5. Set up monitoring

See **README.md** for full production checklist.

## Example Use Cases

### Tech Enthusiast
- **URLs**: TechCrunch, Hacker News, Ars Technica
- **Criteria**: "AI/ML", "Web Development", "Startups"

### Researcher
- **URLs**: ArXiv, Nature, IEEE
- **Criteria**: "Machine Learning Research", "Computer Vision", "NLP"

### Developer
- **URLs**: GitHub Trending, Dev.to, Stack Overflow Blog
- **Criteria**: "Python", "JavaScript", "DevOps"

### Business Analyst
- **URLs**: Bloomberg, TechCrunch, WSJ
- **Criteria**: "Fintech", "Market Trends", "IPO"

## FAQ

**Q: How often should I click UPDATE?**  
A: Once or twice a day is usually sufficient.

**Q: Can I scrape private/authenticated sites?**  
A: No, only public websites are supported.

**Q: How much does OpenAI cost?**  
A: GPT-4o-mini is very cheap (~$0.01 per 100 articles).

**Q: Can I run this without Docker?**  
A: Yes, but Docker is recommended. See README.md for manual setup.

**Q: How do I backup my data?**  
A: `docker-compose exec postgres pg_dump -U newscatcher newscatcher_db > backup.sql`

**Q: Is my API key secure?**  
A: Yes, it stays in your `.env` file and is never exposed.

## Support

Having issues? Check:

1. ✅ Docker is running
2. ✅ API key is correct in `.env`
3. ✅ Services are healthy: `docker-compose ps`
4. ✅ Logs for errors: `docker-compose logs -f`

---

**Happy News Catching! 📰**

Made with ❤️ using Python, FastAPI, and Streamlit

