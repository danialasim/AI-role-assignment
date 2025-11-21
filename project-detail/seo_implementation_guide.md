# SEO Content Generator - Complete Implementation Guide

## Project Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  POST /generate-article   GET /job/{id}   GET /job-status   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│         (Coordinates the entire generation pipeline)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                     ↓                      ↓
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│ SERP Analyzer │    │ Outline Agent  │    │Content Agent │
│   (Research)  │ →  │   (Planning)   │ →  │  (Writing)   │
└───────────────┘    └────────────────┘    └──────────────┘
                              ↓
                    ┌──────────────────┐
                    │ Quality Validator│
                    │  (SEO Scoring)   │
                    └──────────────────┘
                              ↓
                    ┌──────────────────┐
                    │ Database Layer   │
                    │   (PostgreSQL)   │
                    └──────────────────┘
```

## Phase 1: Project Setup (30 minutes)

### 1.1 Technology Stack

**Backend Framework:**
- FastAPI (Python 3.10+) - Modern, fast API framework
- Pydantic v2 - Data validation and structured output

**LLM Integration:**
- OpenAI API (GPT-4) or Anthropic Claude API
- LangChain or direct API calls for agent orchestration

**SERP Data:**
- SerpAPI (easiest to start, free tier available)
- Alternative: ValueSERP or DataForSEO

**Database:**
- PostgreSQL with SQLAlchemy ORM
- Alternative: SQLite for simpler setup

**Task Queue (Bonus):**
- Celery + Redis for async job processing

**Environment Setup:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary
pip install openai anthropic langchain
pip install serpapi python-dotenv requests
pip install pytest httpx  # for testing
```

### 1.2 Project Structure

```
seo-content-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration management
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py          # API request models
│   │   ├── response.py         # API response models
│   │   └── article.py          # Article data structures
│   │
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   └── connection.py       # DB connection
│   │
│   ├── agents/                 # Agent implementations
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Main agent coordinator
│   │   ├── serp_analyzer.py    # SERP analysis agent
│   │   ├── outline_generator.py # Outline creation
│   │   ├── content_generator.py # Content writing
│   │   └── quality_validator.py # SEO validation
│   │
│   ├── services/               # External services
│   │   ├── __init__.py
│   │   ├── serp_service.py     # SERP API integration
│   │   └── llm_service.py      # LLM API wrapper
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── seo_helpers.py      # SEO utility functions
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_api.py
│
├── examples/
│   └── sample_output.json
│
├── .env                        # Environment variables
├── requirements.txt
├── README.md
└── docker-compose.yml         # Optional: for PostgreSQL
```

## Phase 2: Data Models (1 hour)

### 2.1 Request/Response Models (Pydantic)

**File: `app/models/request.py`**
```python
from pydantic import BaseModel, Field
from typing import Optional

class ArticleGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    target_word_count: int = Field(default=1500, ge=500, le=5000)
    language: str = Field(default="en", pattern="^[a-z]{2}$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "best productivity tools for remote teams",
                "target_word_count": 1500,
                "language": "en"
            }
        }
```

**File: `app/models/response.py`**
```python
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SERPResult(BaseModel):
    rank: int
    url: HttpUrl
    title: str
    snippet: str

class KeywordAnalysis(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str]
    keyword_density: float

class InternalLink(BaseModel):
    anchor_text: str
    suggested_target: str
    context: str

class ExternalReference(BaseModel):
    source_name: str
    url: HttpUrl
    context: str
    placement_suggestion: str

class SEOMetadata(BaseModel):
    title_tag: str
    meta_description: str
    focus_keyword: str

class ArticleContent(BaseModel):
    h1: str
    sections: List[dict]  # {h2: str, h3s: [...], content: str}
    full_text: str
    word_count: int

class ArticleOutput(BaseModel):
    article: ArticleContent
    seo_metadata: SEOMetadata
    keyword_analysis: KeywordAnalysis
    internal_links: List[InternalLink]
    external_references: List[ExternalReference]
    serp_analysis: List[SERPResult]

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[ArticleOutput]
    error: Optional[str]
```

### 2.2 Database Models (SQLAlchemy)

**File: `app/database/models.py`**
```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class JobStatusEnum(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ArticleJob(Base):
    __tablename__ = "article_jobs"
    
    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False)
    target_word_count = Column(Integer, default=1500)
    language = Column(String, default="en")
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Store intermediate results for resumability
    serp_data = Column(JSON, nullable=True)
    outline_data = Column(JSON, nullable=True)
    content_data = Column(Text, nullable=True)
    
    # Final output
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
```

## Phase 3: Core Agent Implementation (3-4 hours)

### 3.1 SERP Analyzer Agent

**Purpose:** Fetch and analyze top 10 search results

**File: `app/agents/serp_analyzer.py`**

Key functions:
- `fetch_serp_results(topic: str)` - Call SERP API
- `extract_themes(results: List[SERPResult])` - Use LLM to identify common topics
- `analyze_heading_structure(results)` - Extract H2/H3 patterns

**LLM Prompt Example:**
```python
prompt = f"""
Analyze these top 10 search results for "{topic}":

{serp_results}

Extract:
1. Common topics/themes covered across multiple results
2. Subtopics that appear frequently
3. Content gaps (topics only 1-2 articles cover)
4. Recommended heading structure

Return as JSON.
"""
```

### 3.2 Outline Generator Agent

**Purpose:** Create article structure based on SERP analysis

**File: `app/agents/outline_generator.py`**

Key functions:
- `generate_outline(theme_analysis, target_word_count)` - Create H1/H2/H3 structure
- `allocate_word_counts(outline)` - Distribute words across sections
- `identify_keyword_placement()` - Plan keyword usage

**Outline Structure:**
```python
{
    "h1": "15 Best Productivity Tools for Remote Teams in 2025",
    "sections": [
        {
            "h2": "Introduction to Remote Team Productivity",
            "word_count": 200,
            "keywords": ["remote teams", "productivity tools"]
        },
        {
            "h2": "Top Communication Tools",
            "h3s": [
                "Slack for Team Messaging",
                "Zoom for Video Conferencing"
            ],
            "word_count": 400
        }
    ]
}
```

### 3.3 Content Generator Agent

**Purpose:** Write actual article content

**File: `app/agents/content_generator.py`**

Key functions:
- `generate_section(heading, keywords, word_count)` - Write individual sections
- `generate_introduction(h1, outline)` - Compelling intro with primary keyword
- `generate_conclusion(h1, main_points)` - Summarize key takeaways

**LLM Prompt Strategy:**
```python
# Use structured output with GPT-4 or Claude
prompt = f"""
Write a {word_count}-word section for an SEO article.

Heading: {heading}
Keywords to include naturally: {keywords}
Context: This is part of an article about {main_topic}

Requirements:
- Write in a conversational, human tone
- Include the primary keyword in the first 100 words
- Use short paragraphs (2-3 sentences)
- Include specific examples or data points
- Don't sound like generic AI content

Write the section now:
"""
```

### 3.4 Quality Validator Agent

**Purpose:** Score content quality and SEO compliance

**File: `app/agents/quality_validator.py`**

**Validation Checks:**
```python
def validate_seo_quality(article: ArticleContent, metadata: SEOMetadata):
    score = 0
    issues = []
    
    # 1. Title tag length (50-60 chars)
    if 50 <= len(metadata.title_tag) <= 60:
        score += 10
    else:
        issues.append("Title tag should be 50-60 characters")
    
    # 2. Primary keyword in H1
    if metadata.focus_keyword.lower() in article.h1.lower():
        score += 15
    else:
        issues.append("Primary keyword missing from H1")
    
    # 3. Keyword in first 100 words
    first_100 = article.full_text[:100]
    if metadata.focus_keyword.lower() in first_100.lower():
        score += 15
    
    # 4. Proper heading hierarchy
    # Check H2s exist, H3s are under H2s, etc.
    score += validate_heading_structure(article.sections)
    
    # 5. Content length within target range (±10%)
    # 6. Keyword density (1-2%)
    # 7. Readability (sentence length, paragraph length)
    # 8. Internal link count (3-5)
    # 9. External reference count (2-4)
    
    return {"score": score, "issues": issues}
```

### 3.5 Agent Orchestrator

**Purpose:** Coordinate all agents in sequence

**File: `app/agents/orchestrator.py`**

```python
class ArticleGenerationOrchestrator:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.serp_analyzer = SERPAnalyzer()
        self.outline_generator = OutlineGenerator()
        self.content_generator = ContentGenerator()
        self.quality_validator = QualityValidator()
    
    async def generate(self, request: ArticleGenerationRequest):
        # Step 1: Update job status
        await self.update_job_status("running")
        
        try:
            # Step 2: SERP Analysis (resumable checkpoint)
            serp_data = await self.get_or_fetch_serp(request.topic)
            await self.save_checkpoint("serp_data", serp_data)
            
            # Step 3: Generate Outline
            outline = await self.outline_generator.generate(
                serp_data, request.target_word_count
            )
            await self.save_checkpoint("outline_data", outline)
            
            # Step 4: Generate Content
            article = await self.content_generator.generate(outline)
            
            # Step 5: Generate SEO Metadata
            metadata = await self.generate_seo_metadata(article)
            
            # Step 6: Generate Links
            internal_links = await self.generate_internal_links(article)
            external_refs = await self.generate_external_references(article)
            
            # Step 7: Validate Quality
            quality_score = self.quality_validator.validate(article, metadata)
            
            # Step 8: Package Output
            result = ArticleOutput(
                article=article,
                seo_metadata=metadata,
                keyword_analysis=self.analyze_keywords(article),
                internal_links=internal_links,
                external_references=external_refs,
                serp_analysis=serp_data
            )
            
            await self.complete_job(result)
            return result
            
        except Exception as e:
            await self.fail_job(str(e))
            raise
```

## Phase 4: API Implementation (1 hour)

### 4.1 FastAPI Endpoints

**File: `app/main.py`**

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.models.request import ArticleGenerationRequest
from app.models.response import JobResponse
from app.agents.orchestrator import ArticleGenerationOrchestrator
import uuid

app = FastAPI(title="SEO Content Generator API")

@app.post("/generate-article", response_model=JobResponse)
async def generate_article(
    request: ArticleGenerationRequest,
    background_tasks: BackgroundTasks
):
    # Create job
    job_id = str(uuid.uuid4())
    
    # Store in database
    job = create_job(job_id, request)
    
    # Run generation in background
    background_tasks.add_task(
        run_generation,
        job_id,
        request
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        created_at=job.created_at
    )

@app.get("/job/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    job = get_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        job_id=job_id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error
    )

async def run_generation(job_id: str, request: ArticleGenerationRequest):
    orchestrator = ArticleGenerationOrchestrator(job_id)
    await orchestrator.generate(request)
```

## Phase 5: External Service Integration (1 hour)

### 5.1 SERP API Service

**File: `app/services/serp_service.py`**

```python
import os
import requests
from typing import List
from app.models.response import SERPResult

class SerpAPIService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"
    
    def search(self, query: str, num_results: int = 10) -> List[SERPResult]:
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for i, item in enumerate(data.get("organic_results", [])[:10]):
                results.append(SERPResult(
                    rank=i + 1,
                    url=item.get("link"),
                    title=item.get("title"),
                    snippet=item.get("snippet", "")
                ))
            
            return results
            
        except requests.exceptions.RequestException as e:
            # Fallback to mock data if API fails
            return self.get_mock_data(query)
    
    def get_mock_data(self, query: str) -> List[SERPResult]:
        # Return realistic mock data for testing
        return [...]
```

### 5.2 LLM Service Wrapper

**File: `app/services/llm_service.py`**

```python
import os
from openai import OpenAI

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4-turbo-preview"
    
    async def generate(self, prompt: str, json_mode: bool = False):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert SEO content writer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} if json_mode else None,
            temperature=0.7
        )
        
        return response.choices[0].message.content
```

## Phase 6: Testing & Documentation (1 hour)

### 6.1 Unit Tests

**File: `tests/test_agents.py`**

```python
import pytest
from app.agents.serp_analyzer import SERPAnalyzer
from app.models.response import SERPResult

@pytest.mark.asyncio
async def test_serp_theme_extraction():
    analyzer = SERPAnalyzer()
    
    mock_results = [
        SERPResult(rank=1, url="https://example.com", 
                   title="Best Tools", snippet="..."),
        # ... more results
    ]
    
    themes = await analyzer.extract_themes(mock_results)
    
    assert len(themes) > 0
    assert "common_topics" in themes
```

### 6.2 API Tests

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_article():
    response = client.post("/generate-article", json={
        "topic": "best productivity tools",
        "target_word_count": 1500,
        "language": "en"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
```

### 6.3 README Documentation

**Key Sections:**
1. Project Overview
2. Installation Instructions
3. Environment Variables Setup
4. API Endpoints Documentation
5. Example Usage
6. Architecture Decisions
7. Running Tests

## Phase 7: Bonus Features (Optional)

### 7.1 Resumability Implementation

Store checkpoints in database:
```python
async def save_checkpoint(self, stage: str, data: dict):
    # Update job record with intermediate data
    await update_job(self.job_id, {
        f"{stage}_data": data,
        "last_checkpoint": stage
    })

async def resume_from_checkpoint(self, job_id: str):
    job = await get_job(job_id)
    last_stage = job.last_checkpoint
    
    # Skip completed stages
    if last_stage == "serp_data":
        # Resume from outline generation
        return await self.generate_outline(job.serp_data)
```

### 7.2 Content Quality Scorer

Implement automated revision:
```python
async def score_and_revise(self, article: ArticleContent):
    score = self.quality_validator.score(article)
    
    if score < 70:  # Threshold
        # Identify weak sections
        issues = self.identify_issues(article, score)
        
        # Regenerate specific sections
        for issue in issues:
            improved_section = await self.regenerate_section(
                issue.section, issue.feedback
            )
            article.update_section(issue.section, improved_section)
    
    return article
```

## Environment Variables (.env file)

```env
# API Keys
OPENAI_API_KEY=sk-...
SERPAPI_KEY=...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/seo_content

# Optional
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379
```

## Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database
python -m app.database.init_db

# 3. Run development server
uvicorn app.main:app --reload

# 4. Run tests
pytest tests/ -v

# 5. Generate example article
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{"topic": "best productivity tools for remote teams"}'

# 6. Check job status
curl http://localhost:8000/job/{job_id}
```

## Time Allocation

| Phase | Task | Time |
|-------|------|------|
| 1 | Project setup & dependencies | 30 min |
| 2 | Data models (Pydantic + SQLAlchemy) | 1 hour |
| 3 | Core agents implementation | 3-4 hours |
| 4 | API endpoints | 1 hour |
| 5 | External services integration | 1 hour |
| 6 | Testing & documentation | 1 hour |
| 7 | Bonus features (optional) | 1-2 hours |

**Total: 7.5-10 hours** (focus on core features first)

## Priority Order for Implementation

**Day 1 (Core System - 6 hours):**
1. Project structure & setup
2. Data models
3. Basic SERP analyzer (with mock data initially)
4. Outline generator
5. Simple content generator
6. API endpoints

**Day 2 (Polish & Testing - 4 hours):**
1. Integrate real SERP API
2. Improve content quality
3. Add SEO validation
4. Write tests
5. Documentation
6. Example output

This ensures you have a working system early, then enhance it.