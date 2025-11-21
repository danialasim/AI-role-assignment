# Complete Implementation Checklist & Troubleshooting

## Pre-Implementation Checklist

### API Keys & Accounts
- [ ] OpenAI API account with GPT-4 access
  - Sign up: https://platform.openai.com/
  - Add payment method (required for GPT-4)
  - Generate API key
  
- [ ] SerpAPI account (optional but recommended)
  - Sign up: https://serpapi.com/
  - Free tier: 100 searches/month
  - Get API key

### Development Environment
- [ ] Python 3.10 or higher installed
- [ ] Git installed
- [ ] Code editor (VS Code, PyCharm, etc.)
- [ ] Terminal/Command line access

---

## Day 1 Implementation Checklist

### Hour 1: Project Setup ✅
- [ ] Create project directory
- [ ] Initialize virtual environment
- [ ] Install all dependencies from requirements.txt
- [ ] Create .env file with API keys
- [ ] Test imports work: `python -c "import fastapi"`

**Quick Test:**
```bash
python -c "from app.config import get_settings; print(get_settings())"
```

### Hour 2: Data Models ✅
- [ ] Create all Pydantic models in app/models/
- [ ] Create SQLAlchemy models in app/database/
- [ ] Initialize database: `python -c "from app.database.models import init_db; init_db()"`
- [ ] Verify database file created: `ls seo_content.db`

**Quick Test:**
```python
# test_models.py
from app.models.request import ArticleGenerationRequest
from app.models.response import SERPResult

# Should not raise errors
req = ArticleGenerationRequest(topic="test")
serp = SERPResult(rank=1, url="https://example.com", title="Test", snippet="Test snippet")
print("Models OK!")
```

### Hour 3: Services ✅
- [ ] Implement SerpAPIService in app/services/serp_service.py
- [ ] Implement LLMService in app/services/llm_service.py
- [ ] Test mock SERP data works
- [ ] Test OpenAI connection

**Quick Test:**
```python
# test_services.py
from app.services.serp_service import SerpAPIService
from app.services.llm_service import LLMService
import asyncio

async def test():
    # Test SERP (will use mock)
    serp = SerpAPIService()
    results = serp.search("test query")
    print(f"SERP: Got {len(results)} results")
    
    # Test LLM
    llm = LLMService()
    response = await llm.generate("Say 'hello'")
    print(f"LLM: {response[:50]}")

asyncio.run(test())
```

### Hour 4: Agents ✅
- [ ] Implement SERPAnalyzer
- [ ] Implement OutlineGenerator
- [ ] Implement ContentGenerator
- [ ] Implement SEOGenerator
- [ ] Test each agent independently

**Quick Test:**
```python
# test_agents.py
from app.agents.serp_analyzer import SERPAnalyzer
from app.models.response import SERPResult
import asyncio

async def test():
    analyzer = SERPAnalyzer()
    mock_results = [
        SERPResult(rank=i, url=f"https://example.com/{i}", 
                   title=f"Title {i}", snippet=f"Snippet {i}")
        for i in range(1, 11)
    ]
    analysis = await analyzer.analyze_serp_results(mock_results, "test topic")
    print(f"Analysis keys: {analysis.keys()}")

asyncio.run(test())
```

### Hour 5: Orchestrator ✅
- [ ] Implement ArticleGenerationOrchestrator
- [ ] Add checkpoint saving
- [ ] Add error handling
- [ ] Test full pipeline

**Quick Test:**
```python
# test_orchestrator.py
from app.agents.orchestrator import ArticleGenerationOrchestrator
from app.models.request import ArticleGenerationRequest
from app.database.models import ArticleJob, SessionLocal, JobStatusEnum
import asyncio
import uuid

async def test():
    # Create job in DB
    job_id = str(uuid.uuid4())
    db = SessionLocal()
    job = ArticleJob(id=job_id, topic="test", status=JobStatusEnum.PENDING)
    db.add(job)
    db.commit()
    db.close()
    
    # Run orchestrator
    orchestrator = ArticleGenerationOrchestrator(job_id)
    request = ArticleGenerationRequest(topic="best productivity tools", target_word_count=800)
    result = await orchestrator.generate(request)
    
    print(f"Generated article with {result.article.word_count} words")
    print(f"H1: {result.article.h1}")

asyncio.run(test())
```

### Hour 6: API ✅
- [ ] Implement FastAPI endpoints in app/main.py
- [ ] Add CORS middleware
- [ ] Test server starts: `uvicorn app.main:app --reload`
- [ ] Visit http://localhost:8000/docs
- [ ] Test POST /generate-article
- [ ] Test GET /job/{id}

**Quick Test:**
```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Test API
curl http://localhost:8000/
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{"topic": "test topic", "target_word_count": 800}'
```

---

## Day 2 Implementation Checklist

### Hour 1: Testing ✅
- [ ] Create tests/test_api.py
- [ ] Create tests/test_agents.py
- [ ] Run tests: `pytest tests/ -v`
- [ ] Achieve >70% test coverage

**Quick Test:**
```bash
pytest tests/ -v --cov=app
```

### Hour 2: Documentation ✅
- [ ] Write comprehensive README.md
- [ ] Add architecture diagrams
- [ ] Document API endpoints
- [ ] Add usage examples
- [ ] Create examples/sample_output.json

### Hour 3: Quality Validation ✅
- [ ] Implement QualityValidator
- [ ] Add SEO scoring
- [ ] Integrate into orchestrator
- [ ] Test validation works

### Hour 4: Final Polish ✅
- [ ] Test end-to-end generation (3-5 test runs)
- [ ] Verify all outputs are valid
- [ ] Check SEO quality scores
- [ ] Fix any remaining issues
- [ ] Create Docker setup (optional)

---

## Submission Checklist

### Code Quality ✅
- [ ] All code properly formatted
- [ ] No syntax errors
- [ ] No unused imports
- [ ] Consistent naming conventions
- [ ] Comments for complex logic

### Documentation ✅
- [ ] README.md complete
- [ ] Installation instructions clear
- [ ] API endpoints documented
- [ ] Architecture decisions explained
- [ ] Example output provided

### Testing ✅
- [ ] API tests passing
- [ ] Agent tests passing
- [ ] At least one full generation tested
- [ ] Edge cases handled

### Repository ✅
- [ ] .gitignore file (exclude venv/, __pycache__/, .env, *.db)
- [ ] requirements.txt complete
- [ ] All files committed
- [ ] Repository pushed to GitHub
- [ ] README visible on GitHub

### Final Verification ✅
- [ ] Clone repo fresh and follow README instructions
- [ ] Generates article successfully
- [ ] API docs accessible
- [ ] No sensitive data in repo (API keys)

---

## Common Issues & Solutions

### Issue 1: OpenAI API Rate Limit
**Error:** `RateLimitError: Rate limit exceeded`

**Solution:**
```python
# Add retry logic to LLMService
import time
from openai import RateLimitError

async def generate_with_retry(self, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.generate(prompt)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

### Issue 2: Database Locked
**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
```python
# In database/models.py
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

### Issue 3: JSON Parse Error from LLM
**Error:** `JSONDecodeError: Expecting value`

**Solution:**
```python
async def generate_json(self, prompt: str) -> Dict:
    response = await self.generate(prompt, json_mode=True)
    
    # Clean response
    response = response.strip()
    # Remove markdown code blocks if present
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {response[:200]}")
        raise
```

### Issue 4: Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in the project root and running:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or on Windows:
set PYTHONPATH=%PYTHONPATH%;%CD%

# Better: Always run from project root with:
python -m uvicorn app.main:app --reload
```

### Issue 5: Async Function Not Awaited
**Error:** `RuntimeWarning: coroutine was never awaited`

**Solution:**
```python
# Wrong:
result = self.llm_service.generate(prompt)

# Correct:
result = await self.llm_service.generate(prompt)

# Or in non-async context:
import asyncio
result = asyncio.run(self.llm_service.generate(prompt))
```

### Issue 6: Background Task Not Completing
**Problem:** Job stays "running" forever

**Solution:**
```python
# Add timeout to orchestrator
import asyncio

async def generate_with_timeout(self, request, timeout=600):  # 10 min
    try:
        return await asyncio.wait_for(
            self.generate(request),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        self._save_error("Generation timeout exceeded")
        raise
```

### Issue 7: SERP API Quota Exceeded
**Error:** `SerpAPI: Monthly quota exceeded`

**Solution:**
Already handled! The code falls back to mock data:
```python
# In serp_service.py - already implemented
def search(self, query: str):
    if not self.api_key or self.settings.environment == "development":
        return self.get_mock_data(query)
    # ... actual API call
```

---

## Performance Optimization Tips

### 1. Reduce Word Count for Testing
```python
# Use shorter articles during development
request = ArticleGenerationRequest(
    topic="test",
    target_word_count=800  # Instead of 1500
)
```

### 2. Cache SERP Results
```python
# Add simple cache to avoid repeated searches
from functools import lru_cache

class SerpAPIService:
    @lru_cache(maxsize=100)
    def search(self, query: str):
        # ... implementation
```

### 3. Parallel Section Generation
```python
# In content_generator.py
import asyncio

async def generate_article(self, outline, serp_analysis):
    # Generate all sections in parallel
    tasks = [
        self._generate_section_content(...)
        for section in outline["sections"]
    ]
    section_contents = await asyncio.gather(*tasks)
    # ... rest of implementation
```

### 4. Use Cheaper Models for Development
```python
# In llm_service.py
class LLMService:
    def __init__(self):
        # Use gpt-3.5-turbo for testing (10x cheaper)
        self.model = "gpt-3.5-turbo" if get_settings().environment == "development" else "gpt-4-turbo-preview"
```

---

## Quality Checklist Before Submission

### Content Quality ✅
- [ ] Generated articles are coherent and on-topic
- [ ] No obvious AI patterns ("in conclusion", "it's worth noting")
- [ ] Proper heading hierarchy (H1 > H2 > H3)
- [ ] Keyword usage feels natural
- [ ] Word count within ±10% of target

### SEO Quality ✅
- [ ] Primary keyword in H1
- [ ] Primary keyword in first 100 words
- [ ] Title tag 50-60 characters
- [ ] Meta description 150-160 characters
- [ ] 3-5 internal link suggestions
- [ ] 2-4 external reference suggestions
- [ ] Keyword density 1-2.5%

### Code Quality ✅
- [ ] No hardcoded values (use config)
- [ ] Error handling on all API calls
- [ ] Proper type hints
- [ ] Descriptive variable names
- [ ] Functions under 50 lines
- [ ] Classes have single responsibility

### System Quality ✅
- [ ] Jobs persist in database
- [ ] Background tasks complete
- [ ] API returns proper status codes
- [ ] Checkpoints enable resumability
- [ ] Tests cover main flows

---

## Time-Saving Tips

### 1. Use the Mock Data First
Don't waste time debugging API issues. Get everything working with mock data, then add real APIs.

### 2. Test Components Independently
Don't wait until everything is built. Test each agent as you build it.

### 3. Use Smaller Word Counts
Generate 800-word articles instead of 1500 during development. Saves time and API costs.

### 4. Copy-Paste Wisely
The code templates are complete. Just copy, adjust file paths, and test.

### 5. Use AI Autocomplete
If using VS Code, install GitHub Copilot or similar. It'll speed up repetitive code.

### 6. Focus on Core First
Skip bonus features until core system works end-to-end.

---

## Final Git Commands

```bash
# Initialize repo
git init
git add .
git commit -m "Initial commit: SEO content generator"

# Create .gitignore
cat > .gitignore << EOF
venv/
__pycache__/
*.pyc
.env
*.db
.pytest_cache/
htmlcov/
.coverage
*.log
EOF

# Create GitHub repo (via GitHub CLI or web)
gh repo create seo-content-generator --public --source=. --push

# Or manually:
# 1. Create repo on GitHub
# 2. git remote add origin <your-repo-url>
# 3. git push -u origin main
```

---

## Submission Email Template

```
Subject: SEO Content Generator - Take-Home Assessment Submission

Hi [Hiring Manager],

I've completed the SEO Content Generator assessment. Here are the details:

GitHub Repository: [your-repo-url]
Live Demo: [if deployed]
Completion Time: ~[X] hours

Key Features Implemented:
✅ Agent-based architecture with 4 specialized agents
✅ SERP analysis using SerpAPI (with mock fallback)
✅ LLM-powered content generation (GPT-4)
✅ SEO metadata and linking suggestions
✅ Job persistence with resumability
✅ Comprehensive test suite
✅ Quality validation scoring

Technical Stack:
- FastAPI for REST API
- Pydantic v2 for data validation
- SQLAlchemy with SQLite/PostgreSQL
- OpenAI GPT-4 for generation
- Pytest for testing

To run locally:
1. Clone repo
2. Install: pip install -r requirements.txt
3. Configure .env with API keys
4. Run: uvicorn app.main:app --reload
5. Visit: http://localhost:8000/docs

Example generation:
POST /generate-article
{"topic": "best productivity tools for remote teams", "target_word_count": 1500}

Architecture Highlights:
- Checkpoint-based resumability for crash recovery
- Background task processing for async operations
- Structured output using Pydantic models
- Mock data fallback for reliable testing

See README.md for complete documentation.

Looking forward to discussing the implementation!

Best regards,
[Your Name]
```

---

## Emergency Shortcuts (If Running Out of Time)

### If you only have 4 hours total:
1. Skip tests (2 hours saved) - Add TODO comments
2. Use mock SERP only (30 min saved)
3. Simplify content generator - single-pass generation (1 hour saved)
4. Skip quality validator (30 min saved)

### Minimum Viable Implementation:
- ✅ FastAPI with 2 endpoints
- ✅ One agent that calls GPT-4 with a good prompt
- ✅ Basic database storage
- ✅ Working end-to-end flow
- ✅ README with clear instructions

Even simplified version shows:
- API design skills
- LLM integration
- Structured thinking
- Clear documentation

---

## Success Criteria Checklist

According to the assignment, they're evaluating:

### Code Organization ✅
- [ ] Clear separation of concerns
- [ ] Logical file structure
- [ ] Consistent naming
- [ ] Proper imports

### Agent Logic ✅
- [ ] SERP data properly analyzed
- [ ] Outline reflects competitive landscape
- [ ] Content generation quality
- [ ] Linking strategy makes sense

### Content Quality ✅
- [ ] Articles follow SEO principles
- [ ] Reads like human-written content
- [ ] Proper heading structure
- [ ] Natural keyword usage

### Error Handling ✅
- [ ] API failures handled gracefully
- [ ] Database errors caught
- [ ] User-friendly error messages
- [ ] No silent failures

### Documentation ✅
- [ ] Clear README
- [ ] Setup instructions work
- [ ] Example provided
- [ ] Design decisions explained

---

**You're Ready! 🚀**

Follow the day-by-day plan, use the code templates, and you'll have a solid submission. Good luck with your interview!