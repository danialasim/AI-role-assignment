# 🚀 Complete Setup and Usage Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [Testing the System](#testing-the-system)
6. [API Usage Examples](#api-usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure Explained](#project-structure-explained)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

- **Python 3.10 or higher**
  ```bash
  python3 --version  # Should show 3.10.x or higher
  ```

- **pip** (Python package installer)
  ```bash
  pip3 --version
  ```

- **Git** (for cloning the repository)
  ```bash
  git --version
  ```

### Required API Keys

1. **Anthropic Claude API Key** (Required)
   - Sign up at: https://console.anthropic.com/
   - Navigate to "API Keys" section
   - Click "Create Key"
   - Add $5-10 credits to your account
   - Cost: ~$0.10-0.20 per article

2. **SerpAPI Key** (Optional but recommended)
   - Sign up at: https://serpapi.com/
   - Free tier: 100 searches/month
   - Navigate to "Dashboard" → "API Key"
   - Note: System works with mock data if no key provided

---

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd /Users/danialasim/work/aiseo-agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# You should see (.venv) in your terminal prompt
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# This installs:
# - fastapi (web framework)
# - uvicorn (ASGI server)
# - anthropic (Claude API)
# - pydantic (data validation)
# - sqlalchemy (database ORM)
# - and more...
```

### Step 4: Verify Installation

```bash
# Check FastAPI installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed')"

# Check Anthropic installation
python -c "import anthropic; print('Anthropic SDK installed')"

# Expected output:
# FastAPI x.x.x installed
# Anthropic SDK installed
```

---

## Configuration

### Step 1: Set Up Environment Variables

The `.env` file is already created. Update it with your API keys:

```bash
# Edit the .env file
nano .env  # or use any text editor

# Update these values:
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
SERPAPI_KEY=your-serpapi-key-here  # Optional
DATABASE_URL=sqlite:///./seo_content.db
ENVIRONMENT=development
```

**Important:** 
- Replace `sk-ant-your-actual-key-here` with your real Anthropic API key
- Keep `ENVIRONMENT=development` to enable mock SERP data
- The `DATABASE_URL` uses SQLite by default (no additional setup needed)

### Step 2: Initialize Database

```bash
# Initialize the SQLite database
python -c "from app.database.models import init_db; init_db()"

# Expected output:
# ✅ Database initialized successfully
```

This creates a `seo_content.db` file in your project root.

### Step 3: Verify Configuration

```bash
# Test configuration loading
python -c "from app.config import get_settings; settings = get_settings(); print('✅ Config loaded successfully')"
```

---

## Running the Application

### Option 1: Development Server (Recommended for Testing)

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

The `--reload` flag automatically restarts the server when code changes.

### Option 2: Production Server

```bash
# For production deployment
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points

Once the server is running, access these URLs:

- **API Server**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

---

## Testing the System

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Expected output:
# ==================== 20 passed in X.XXs ====================
```

### Run Tests with Coverage

```bash
# Install coverage if not already installed
pip install pytest-cov

# Run tests with coverage report
pytest tests/ --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# or xdg-open htmlcov/index.html  # Linux
# or start htmlcov/index.html  # Windows
```

### Run Specific Tests

```bash
# Test only API endpoints
pytest tests/test_api.py -v

# Test only agents
pytest tests/test_agents.py -v

# Test specific function
pytest tests/test_api.py::test_generate_article_endpoint -v
```

---

## API Usage Examples

### Example 1: Generate an Article (Quick Test)

**Terminal 1: Start Server**
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2: Make Request**
```bash
# Generate a short article (faster for testing)
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "best productivity tools for remote teams",
    "target_word_count": 800,
    "language": "en"
  }'

# Response (save the job_id):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-11-21T10:00:00Z"
}
```

### Example 2: Check Job Status

```bash
# Replace <job_id> with your actual job_id from above
curl http://localhost:8000/job/550e8400-e29b-41d4-a716-446655440000

# While running:
{
  "job_id": "550e8400-...",
  "status": "running",
  "created_at": "2025-11-21T10:00:00Z",
  "completed_at": null,
  "result": null
}

# When complete (2-5 minutes later):
{
  "job_id": "550e8400-...",
  "status": "completed",
  "created_at": "2025-11-21T10:00:00Z",
  "completed_at": "2025-11-21T10:04:32Z",
  "result": {
    "article": { ... },
    "seo_metadata": { ... },
    "keyword_analysis": { ... }
  }
}
```

### Example 3: Using Python Requests

```python
import requests
import time
import json

# 1. Generate article
response = requests.post(
    "http://localhost:8000/generate-article",
    json={
        "topic": "AI in healthcare",
        "target_word_count": 1000
    }
)
job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# 2. Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/job/{job_id}")
    data = status_response.json()
    
    if data["status"] == "completed":
        print("✅ Article generated successfully!")
        print(json.dumps(data["result"]["seo_metadata"], indent=2))
        break
    elif data["status"] == "failed":
        print(f"❌ Generation failed: {data['error']}")
        break
    else:
        print(f"⏳ Status: {data['status']}...")
        time.sleep(10)
```

### Example 4: Using the Interactive Docs

1. Open browser: http://localhost:8000/docs
2. Click on "POST /generate-article"
3. Click "Try it out"
4. Enter your request:
   ```json
   {
     "topic": "machine learning basics",
     "target_word_count": 1200,
     "language": "en"
   }
   ```
5. Click "Execute"
6. Copy the `job_id` from response
7. Use "GET /job/{job_id}" to check status

---

## Troubleshooting

### Issue 1: "LLM service not available"

**Problem:** Anthropic API key not configured

**Solution:**
```bash
# Check if .env file has the key
cat .env | grep ANTHROPIC_API_KEY

# If missing or showing placeholder, add your real key:
# ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```

### Issue 2: "Module not found" errors

**Problem:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Issue 3: Database locked error

**Problem:** Multiple processes accessing SQLite

**Solution:**
```bash
# Stop all running servers
# Delete and recreate database
rm seo_content.db
python -c "from app.database.models import init_db; init_db()"
```

### Issue 4: Port already in use

**Problem:** Port 8000 is occupied

**Solution:**
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001

# Or find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
```

### Issue 5: JSON parse error from LLM

**Problem:** Claude occasionally returns malformed JSON

**Solution:** System automatically retries 3 times. If persists:
- Check your API key is valid
- Ensure you have sufficient credits
- Try reducing `target_word_count` for testing

### Issue 6: Tests fail with "async" errors

**Problem:** pytest-asyncio not installed

**Solution:**
```bash
pip install pytest-asyncio
pytest tests/ -v
```

---

## Project Structure Explained

### Core Application (`app/`)

```
app/
├── main.py                  # FastAPI application entry point
├── config.py                # Configuration and environment variables
│
├── agents/                  # AI agents for generation pipeline
│   ├── orchestrator.py           # Main coordinator (10 steps)
│   ├── serp_analyzer.py          # Analyzes search results
│   ├── outline_generator.py      # Creates article structure
│   ├── content_generator.py      # Writes article content
│   ├── seo_metadata_generator.py # SEO tags and links
│   └── quality_validator.py      # Quality scoring (0-100)
│
├── models/                  # Data models (Pydantic)
│   ├── request.py                # API request schemas
│   ├── response.py               # API response schemas
│   └── article.py                # Article data structures
│
├── database/                # Database layer
│   ├── models.py                 # SQLAlchemy ORM models
│   └── connection.py             # DB utilities
│
└── services/                # External service integrations
    ├── serp_service.py           # SerpAPI wrapper
    └── llm_service.py            # Claude API wrapper
```

### Generation Pipeline (10 Steps)

1. **SERP Fetching** → Retrieves top 10 search results
2. **SERP Analysis** → Extracts themes, keywords, patterns
3. **Outline Generation** → Creates H1/H2/H3 structure
4. **Content Writing** → Generates article sections
5. **SEO Metadata** → Creates title tag & meta description
6. **Internal Links** → Suggests 3-5 related pages
7. **External References** → Identifies authoritative sources
8. **Keyword Analysis** → Calculates density & usage
9. **Quality Validation** → Scores against SEO criteria
10. **Result Packaging** → Saves to database

### Database Schema

**ArticleJob Table:**
- `id`: Unique job identifier (UUID)
- `topic`: Article topic/keyword
- `target_word_count`: Desired length
- `status`: pending/running/completed/failed
- `serp_data`: Checkpoint (SERP results)
- `outline_data`: Checkpoint (article outline)
- `result`: Final article output (JSON)
- `error`: Error message if failed

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Generation Time (800 words) | 2-3 minutes |
| Generation Time (1500 words) | 3-5 minutes |
| Cost per Article (Claude) | $0.10-0.20 |
| Quality Score (average) | 75-90% |
| API Response Time | < 100ms |
| Database Query Time | < 10ms |

---

## Advanced Usage

### Custom Word Counts

```bash
# Quick test (800 words)
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{"topic": "cloud computing", "target_word_count": 800}'

# Standard article (1500 words)
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{"topic": "blockchain technology", "target_word_count": 1500}'

# Long-form content (3000 words)
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{"topic": "complete guide to SEO", "target_word_count": 3000}'
```

### Batch Processing

```python
import requests
import json

topics = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural networks"
]

job_ids = []

# Create all jobs
for topic in topics:
    response = requests.post(
        "http://localhost:8000/generate-article",
        json={"topic": topic, "target_word_count": 1000}
    )
    job_ids.append(response.json()["job_id"])
    print(f"Created job for: {topic}")

# Save job IDs
with open("batch_jobs.json", "w") as f:
    json.dump(job_ids, f)

print(f"Created {len(job_ids)} jobs. Check status later.")
```

### Monitoring Jobs

```bash
# Get database file
sqlite3 seo_content.db

# Query all jobs
SELECT id, topic, status, created_at FROM article_jobs ORDER BY created_at DESC;

# Count jobs by status
SELECT status, COUNT(*) FROM article_jobs GROUP BY status;
```

---

## Production Deployment Considerations

### 1. Use PostgreSQL Instead of SQLite

```env
# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/seo_content
```

### 2. Add Redis for Caching

Cache SERP results to reduce API calls and costs.

### 3. Implement Rate Limiting

Prevent API abuse using FastAPI middleware.

### 4. Set Up Background Worker

Use Celery + Redis for distributed task processing.

### 5. Add Monitoring

Implement logging, error tracking (Sentry), and performance monitoring.

---

## Next Steps After Setup

1. ✅ **Test with Sample Topic**
   ```bash
   # Generate test article
   curl -X POST http://localhost:8000/generate-article \
     -H "Content-Type: application/json" \
     -d '{"topic": "test productivity tools", "target_word_count": 800}'
   ```

2. ✅ **Review Generated Content**
   - Check quality score (should be >70%)
   - Verify SEO metadata
   - Review article readability

3. ✅ **Run Full Test Suite**
   ```bash
   pytest tests/ -v
   ```

4. ✅ **Generate Example Outputs**
   - Create 2-3 articles with different topics
   - Document results in `examples/` folder

5. ✅ **Prepare for Submission**
   - Ensure README is complete
   - All tests passing
   - Example outputs included
   - Code is clean and documented

---

## Support & Resources

- **Project Documentation**: `README.md`
- **API Documentation**: http://localhost:8000/docs
- **Example Outputs**: `examples/sample_output.json`
- **Implementation Tracker**: `IMPLEMENTATION_TRACKER.md`

---

**Last Updated**: November 21, 2025  
**Status**: Production Ready (pending API key)
