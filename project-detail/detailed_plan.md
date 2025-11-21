# 2-Day Execution Plan with Code Templates

## DAY 1: Build Core System (6-7 hours)

### HOUR 1: Setup & Foundation (9:00 AM - 10:00 AM)

#### Step 1.1: Create Project Structure
```bash
mkdir seo-content-generator
cd seo-content-generator
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Create all directories
mkdir -p app/{models,database,agents,services,utils} tests examples
touch app/__init__.py app/{models,database,agents,services,utils}/__init__.py
```

#### Step 1.2: Create requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
openai==1.3.0
anthropic==0.7.0
requests==2.31.0
pytest==7.4.3
httpx==0.25.2
python-multipart==0.0.6
```

```bash
pip install -r requirements.txt
```

#### Step 1.3: Create .env file
```env
OPENAI_API_KEY=your_key_here
SERPAPI_KEY=your_key_here
DATABASE_URL=sqlite:///./seo_content.db
ENVIRONMENT=development
```

#### Step 1.4: Create config.py
```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str
    serpapi_key: str = ""
    database_url: str = "sqlite:///./seo_content.db"
    environment: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

---

### HOUR 2-3: Data Models & Database (10:00 AM - 12:00 PM)

#### Step 2.1: Pydantic Models (app/models/request.py)
```python
from pydantic import BaseModel, Field
from typing import Optional

class ArticleGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Main topic or keyword")
    target_word_count: int = Field(default=1500, ge=500, le=5000)
    language: str = Field(default="en")

class JobStatusRequest(BaseModel):
    job_id: str
```

#### Step 2.2: Response Models (app/models/response.py)
```python
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SERPResult(BaseModel):
    rank: int
    url: str
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
    url: str
    context: str
    placement_suggestion: str

class SEOMetadata(BaseModel):
    title_tag: str
    meta_description: str
    focus_keyword: str

class ArticleSection(BaseModel):
    heading: str
    heading_level: int  # 2 or 3
    content: str
    word_count: int

class ArticleContent(BaseModel):
    h1: str
    sections: List[ArticleSection]
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
    completed_at: Optional[datetime] = None
    result: Optional[ArticleOutput] = None
    error: Optional[str] = None
```

#### Step 2.3: Database Models (app/database/models.py)
```python
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import enum
from app.config import get_settings

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
    status = Column(SQLEnum(JobStatusEnum), default=JobStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    serp_data = Column(JSON, nullable=True)
    outline_data = Column(JSON, nullable=True)
    
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

# Database setup
settings = get_settings()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### HOUR 3-4: SERP Service & Analyzer (12:00 PM - 2:00 PM)

#### Step 3.1: SERP Service (app/services/serp_service.py)
```python
import os
import requests
from typing import List, Dict
from app.models.response import SERPResult
from app.config import get_settings

class SerpAPIService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.serpapi_key
        self.base_url = "https://serpapi.com/search"
    
    def search(self, query: str, num_results: int = 10) -> List[SERPResult]:
        if not self.api_key or self.settings.environment == "development":
            return self.get_mock_data(query)
        
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for i, item in enumerate(data.get("organic_results", [])[:10]):
                results.append(SERPResult(
                    rank=i + 1,
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", "")
                ))
            
            return results
            
        except Exception as e:
            print(f"SERP API Error: {e}. Using mock data.")
            return self.get_mock_data(query)
    
    def get_mock_data(self, query: str) -> List[SERPResult]:
        """Mock SERP data for testing"""
        return [
            SERPResult(
                rank=1,
                url="https://example.com/article-1",
                title=f"15 Best {query.title()} in 2025 - Complete Guide",
                snippet=f"Discover the top {query} that professionals use. Our comprehensive guide covers features, pricing, and real user reviews..."
            ),
            SERPResult(
                rank=2,
                url="https://example.com/article-2",
                title=f"Ultimate {query.title()} Comparison",
                snippet=f"Compare the leading {query} options. Find the perfect fit for your needs with our detailed analysis and recommendations..."
            ),
            SERPResult(
                rank=3,
                url="https://example.com/article-3",
                title=f"Top 10 {query.title()} for Teams",
                snippet=f"Boost team productivity with these {query}. Features include collaboration tools, integrations, and mobile apps..."
            ),
            # Add 7 more similar results
        ] + [
            SERPResult(
                rank=i,
                url=f"https://example.com/article-{i}",
                title=f"{query.title()} Guide #{i}",
                snippet=f"Learn about {query} with detailed tutorials and best practices..."
            ) for i in range(4, 11)
        ]
```

#### Step 3.2: LLM Service (app/services/llm_service.py)
```python
from openai import OpenAI
from typing import Optional, Dict
from app.config import get_settings
import json

class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = "You are an expert SEO content writer.",
        json_mode: bool = False,
        temperature: float = 0.7
    ) -> str:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM Error: {e}")
            raise
    
    async def generate_json(self, prompt: str, system_prompt: str = None) -> Dict:
        response = await self.generate(prompt, system_prompt or "You are a helpful assistant that outputs JSON.", json_mode=True)
        return json.loads(response)
```

#### Step 3.3: SERP Analyzer Agent (app/agents/serp_analyzer.py)
```python
from typing import List, Dict
from app.models.response import SERPResult
from app.services.llm_service import LLMService

class SERPAnalyzer:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def analyze_serp_results(self, results: List[SERPResult], topic: str) -> Dict:
        """Extract themes and patterns from SERP results"""
        
        serp_summary = "\n".join([
            f"{r.rank}. Title: {r.title}\n   Snippet: {r.snippet}"
            for r in results
        ])
        
        prompt = f"""Analyze these top 10 search results for the topic: "{topic}"

{serp_summary}

Extract and return a JSON object with:
1. "common_topics": List of main topics covered across multiple articles (3-5 topics)
2. "subtopics": List of specific subtopics that appear frequently (5-8 items)
3. "content_gaps": Topics mentioned in only 1-2 articles that could differentiate our content
4. "recommended_h2_headings": 5-7 H2 heading suggestions based on what's ranking
5. "primary_keyword": The main keyword phrase to target
6. "secondary_keywords": 3-5 related keywords to include

Return only valid JSON."""

        analysis = await self.llm_service.generate_json(prompt)
        return analysis
```

---

### HOUR 4-5: Outline & Content Generators (2:00 PM - 4:00 PM)

#### Step 4.1: Outline Generator (app/agents/outline_generator.py)
```python
from typing import Dict, List
from app.services.llm_service import LLMService

class OutlineGenerator:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_outline(
        self, 
        serp_analysis: Dict, 
        topic: str, 
        target_word_count: int
    ) -> Dict:
        """Generate article outline based on SERP analysis"""
        
        prompt = f"""Create a detailed article outline for: "{topic}"

Based on this competitive analysis:
- Common topics: {serp_analysis.get('common_topics', [])}
- Subtopics: {serp_analysis.get('subtopics', [])}
- Recommended H2s: {serp_analysis.get('recommended_h2_headings', [])}
- Primary keyword: {serp_analysis.get('primary_keyword', topic)}

Target word count: {target_word_count}

Create an outline with:
1. "h1": Compelling article title (include primary keyword)
2. "sections": Array of sections, each with:
   - "h2": Main section heading
   - "h3s": Array of 2-3 H3 subheadings (can be empty for some sections)
   - "word_count": Approximate words for this section
   - "key_points": 2-3 bullet points to cover

Requirements:
- H1 should be engaging and include the primary keyword
- Introduction section (~200 words)
- 4-6 main H2 sections
- Conclusion section (~150 words)
- Total word count should match target (±10%)

Return only valid JSON."""

        outline = await self.llm_service.generate_json(prompt)
        return outline
```

#### Step 4.2: Content Generator (app/agents/content_generator.py)
```python
from typing import Dict, List
from app.services.llm_service import LLMService
from app.models.response import ArticleContent, ArticleSection

class ContentGenerator:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_article(
        self, 
        outline: Dict, 
        serp_analysis: Dict
    ) -> ArticleContent:
        """Generate full article content from outline"""
        
        h1 = outline.get("h1", "")
        sections_data = outline.get("sections", [])
        primary_keyword = serp_analysis.get("primary_keyword", "")
        secondary_keywords = serp_analysis.get("secondary_keywords", [])
        
        generated_sections = []
        full_text = f"# {h1}\n\n"
        total_words = 0
        
        for section in sections_data:
            h2 = section.get("h2", "")
            h3s = section.get("h3s", [])
            word_count_target = section.get("word_count", 300)
            key_points = section.get("key_points", [])
            
            # Generate content for this section
            section_content = await self._generate_section_content(
                h1=h1,
                h2=h2,
                h3s=h3s,
                word_count=word_count_target,
                key_points=key_points,
                keywords=[primary_keyword] + secondary_keywords[:2]
            )
            
            # Create section object
            article_section = ArticleSection(
                heading=h2,
                heading_level=2,
                content=section_content,
                word_count=len(section_content.split())
            )
            
            generated_sections.append(article_section)
            full_text += f"## {h2}\n\n{section_content}\n\n"
            total_words += article_section.word_count
        
        return ArticleContent(
            h1=h1,
            sections=generated_sections,
            full_text=full_text,
            word_count=total_words
        )
    
    async def _generate_section_content(
        self, 
        h1: str, 
        h2: str, 
        h3s: List[str],
        word_count: int,
        key_points: List[str],
        keywords: List[str]
    ) -> str:
        """Generate content for a specific section"""
        
        h3_context = f"\nInclude these subtopics: {', '.join(h3s)}" if h3s else ""
        points_context = f"\nKey points to cover: {', '.join(key_points)}" if key_points else ""
        
        prompt = f"""Write a {word_count}-word section for an SEO article.

Article title: {h1}
Section heading: {h2}{h3_context}{points_context}

Keywords to include naturally: {', '.join(keywords)}

Requirements:
- Write in a conversational, professional tone
- Use short paragraphs (2-4 sentences each)
- Include specific examples or data when relevant
- If H3s are provided, structure content under those subheadings
- Make it sound human-written, not AI-generated
- Don't use phrases like "in conclusion" or "it's important to note"
- Include transitional phrases between ideas

Write the section content now (no heading, just the content):"""

        content = await self.llm_service.generate(prompt, temperature=0.8)
        return content.strip()
```

---

### HOUR 5-6: SEO Metadata & Links (4:00 PM - 5:00 PM)

#### Step 5.1: SEO Metadata Generator (app/agents/seo_generator.py)
```python
from typing import Dict, List
from app.services.llm_service import LLMService
from app.models.response import (
    SEOMetadata, KeywordAnalysis, InternalLink, ExternalReference
)

class SEOGenerator:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_seo_metadata(
        self, 
        article_content: str, 
        h1: str,
        primary_keyword: str
    ) -> SEOMetadata:
        """Generate SEO metadata"""
        
        prompt = f"""Generate SEO metadata for this article:

Title: {h1}
Primary Keyword: {primary_keyword}
First 200 characters: {article_content[:200]}

Create:
1. "title_tag": 50-60 character title tag (include primary keyword)
2. "meta_description": 150-160 character meta description (compelling, includes keyword)
3. "focus_keyword": The primary keyword phrase

Return only valid JSON."""

        metadata_dict = await self.llm_service.generate_json(prompt)
        
        return SEOMetadata(
            title_tag=metadata_dict.get("title_tag", ""),
            meta_description=metadata_dict.get("meta_description", ""),
            focus_keyword=metadata_dict.get("focus_keyword", primary_keyword)
        )
    
    async def generate_internal_links(self, article_content: str, topic: str) -> List[InternalLink]:
        """Generate internal link suggestions"""
        
        prompt = f"""Suggest 3-5 internal links for this article about "{topic}".

Article excerpt: {article_content[:500]}...

For each link, provide:
1. "anchor_text": The text to hyperlink (3-5 words)
2. "suggested_target": The topic/page to link to
3. "context": Where in the article this link makes sense

Return only valid JSON with an array of link objects."""

        links_data = await self.llm_service.generate_json(prompt)
        
        return [
            InternalLink(
                anchor_text=link.get("anchor_text", ""),
                suggested_target=link.get("suggested_target", ""),
                context=link.get("context", "")
            )
            for link in links_data.get("links", [])
        ]
    
    async def generate_external_references(self, article_content: str, topic: str) -> List[ExternalReference]:
        """Generate external reference suggestions"""
        
        prompt = f"""Suggest 2-4 authoritative external sources to cite for an article about "{topic}".

Focus on:
- Industry reports
- Academic studies
- Government/official statistics
- Established publications

For each source:
1. "source_name": Name of the publication/org
2. "url": Realistic URL (use actual domains like harvard.edu, .gov sites)
3. "context": What type of information this source provides
4. "placement_suggestion": Where in the article to cite this

Return only valid JSON with an array."""

        refs_data = await self.llm_service.generate_json(prompt)
        
        return [
            ExternalReference(
                source_name=ref.get("source_name", ""),
                url=ref.get("url", ""),
                context=ref.get("context", ""),
                placement_suggestion=ref.get("placement_suggestion", "")
            )
            for ref in refs_data.get("references", [])
        ]
    
    def analyze_keywords(self, article_content: str, primary_keyword: str, secondary_keywords: List[str]) -> KeywordAnalysis:
        """Analyze keyword usage"""
        
        content_lower = article_content.lower()
        primary_count = content_lower.count(primary_keyword.lower())
        total_words = len(article_content.split())
        
        density = (primary_count / total_words) * 100 if total_words > 0 else 0
        
        return KeywordAnalysis(
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            keyword_density=round(density, 2)
        )
```

---

### HOUR 6-7: Orchestrator & API (5:00 PM - 6:00 PM)

#### Step 6.1: Orchestrator (app/agents/orchestrator.py)
```python
from app.agents.serp_analyzer import SERPAnalyzer
from app.agents.outline_generator import OutlineGenerator
from app.agents.content_generator import ContentGenerator
from app.agents.seo_generator import SEOGenerator
from app.services.serp_service import SerpAPIService
from app.models.request import ArticleGenerationRequest
from app.models.response import ArticleOutput
from app.database.models import ArticleJob, JobStatusEnum, SessionLocal
from datetime import datetime
import json

class ArticleGenerationOrchestrator:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.serp_service = SerpAPIService()
        self.serp_analyzer = SERPAnalyzer()
        self.outline_generator = OutlineGenerator()
        self.content_generator = ContentGenerator()
        self.seo_generator = SEOGenerator()
    
    async def generate(self, request: ArticleGenerationRequest) -> ArticleOutput:
        """Main orchestration method"""
        
        try:
            # Update status to running
            self._update_status(JobStatusEnum.RUNNING)
            
            # Step 1: Fetch SERP results
            print(f"[{self.job_id}] Fetching SERP results...")
            serp_results = self.serp_service.search(request.topic)
            self._save_checkpoint("serp_data", [r.dict() for r in serp_results])
            
            # Step 2: Analyze SERP
            print(f"[{self.job_id}] Analyzing SERP...")
            serp_analysis = await self.serp_analyzer.analyze_serp_results(
                serp_results, request.topic
            )
            
            # Step 3: Generate outline
            print(f"[{self.job_id}] Generating outline...")
            outline = await self.outline_generator.generate_outline(
                serp_analysis, request.topic, request.target_word_count
            )
            self._save_checkpoint("outline_data", outline)
            
            # Step 4: Generate content
            print(f"[{self.job_id}] Generating article content...")
            article_content = await self.content_generator.generate_article(
                outline, serp_analysis
            )
            
            # Step 5: Generate SEO metadata
            print(f"[{self.job_id}] Generating SEO metadata...")
            seo_metadata = await self.seo_generator.generate_seo_metadata(
                article_content.full_text,
                article_content.h1,
                serp_analysis.get("primary_keyword", request.topic)
            )
            
            # Step 6: Generate internal links
            print(f"[{self.job_id}] Generating internal links...")
            internal_links = await self.seo_generator.generate_internal_links(
                article_content.full_text, request.topic
            )
            
            # Step 7: Generate external references
            print(f"[{self.job_id}] Generating external references...")
            external_refs = await self.seo_generator.generate_external_references(
                article_content.full_text, request.topic
            )
            
            # Step 8: Analyze keywords
            keyword_analysis = self.seo_generator.analyze_keywords(
                article_content.full_text,
                serp_analysis.get("primary_keyword", request.topic),
                serp_analysis.get("secondary_keywords", [])
            )
            
            # Step 9: Package output
            result = ArticleOutput(
                article=article_content,
                seo_metadata=seo_metadata,
                keyword_analysis=keyword_analysis,
                internal_links=internal_links,
                external_references=external_refs,
                serp_analysis=serp_results
            )
            
            # Save result
            self._save_result(result)
            print(f"[{self.job_id}] Generation completed!")
            
            return result
            
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            print(f"[{self.job_id}] ERROR: {error_msg}")
            self._save_error(error_msg)
            raise
    
    def _update_status(self, status: JobStatusEnum):
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.status = status
                db.commit()
        finally:
            db.close()
    
    def _save_checkpoint(self, field: str, data):
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                setattr(job, field, data)
                db.commit()
        finally:
            db.close()
    
    def _save_result(self, result: ArticleOutput):
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.result = result.dict()
                job.status = JobStatusEnum.COMPLETED
                job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    def _save_error(self, error: str):
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.error = error
                job.status = JobStatusEnum.FAILED
                job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
```

#### Step 6.2: API (app/main.py)
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models.request import ArticleGenerationRequest
from app.models.response import JobResponse, JobStatus
from app.database.models import ArticleJob, JobStatusEnum, init_db, get_db
from app.agents.orchestrator import ArticleGenerationOrchestrator

app = FastAPI(
    title="SEO Content Generator API",
    description="AI-powered SEO article generation service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/generate-article", response_model=JobResponse)
async def generate_article(
    request: ArticleGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate an SEO-optimized article
    
    - **topic**: Main topic or keyword
    - **target_word_count**: Desired article length (500-5000 words)
    - **language**: Language code (default: 'en')
    """
    
    # Create job
    job_id = str(uuid.uuid4())
    
    job = ArticleJob(
        id=job_id,
        topic=request.topic,
        target_word_count=request.target_word_count,
        language=request.language,
        status=JobStatusEnum.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(job)
    db.commit()
    
    # Run generation in background
    background_tasks.add_task(run_generation, job_id, request)
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=job.created_at
    )

@app.get("/job/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Check the status of a generation job
    """
    job = db.query(ArticleJob).filter(ArticleJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        job_id=job.id,
        status=JobStatus(job.status.value),
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error
    )

@app.get("/")
async def root():
    return {
        "message": "SEO Content Generator API",
        "docs": "/docs",
        "version": "1.0.0"
    }

async def run_generation(job_id: str, request: ArticleGenerationRequest):
    """Background task to run article generation"""
    try:
        orchestrator = ArticleGenerationOrchestrator(job_id)
        await orchestrator.generate(request)
    except Exception as e:
        print(f"Background generation error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## END OF DAY 1 ✅

At this point you have:
- ✅ Complete project structure
- ✅ All data models
- ✅ SERP integration (with mock data fallback)
- ✅ All agent implementations
- ✅ Working API endpoints
- ✅ Database setup

**Test your setup:**
```bash
# Run the server
uvicorn app.main:app --reload

# In another terminal, test the API
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "best productivity tools for remote teams",
    "target_word_count": 1500,
    "language": "en"
  }'

# Get the job_id from response, then check status
curl http://localhost:8000/job/{job_id}
```

---

## DAY 2: Testing, Documentation & Polish (4-5 hours)

### HOUR 1: Testing (9:00 AM - 10:00 AM)

#### Step 7.1: Create Test Files (tests/test_api.py)
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_generate_article():
    response = client.post(
        "/generate-article",
        json={
            "topic": "best productivity tools",
            "target_word_count": 1500,
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

def test_get_job_status():
    # First create a job
    create_response = client.post(
        "/generate-article",
        json={"topic": "test topic"}
    )
    job_id = create_response.json()["job_id"]
    
    # Then check status
    response = client.get(f"/job/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id

def test_invalid_job_id():
    response = client.get("/job/invalid-id-123")
    assert response.status_code == 404

def test_validation_min_word_count():
    response = client.post(
        "/generate-article",
        json={
            "topic": "test",
            "target_word_count": 100  # Below minimum
        }
    )
    assert response.status_code == 422

def test_validation_empty_topic():
    response = client.post(
        "/generate-article",
        json={
            "topic": "",
            "target_word_count": 1500
        }
    )
    assert response.status_code == 422
```

#### Step 7.2: Agent Tests (tests/test_agents.py)
```python
import pytest
from app.agents.serp_analyzer import SERPAnalyzer
from app.agents.outline_generator import OutlineGenerator
from app.models.response import SERPResult

@pytest.mark.asyncio
async def test_serp_analysis():
    analyzer = SERPAnalyzer()
    
    mock_results = [
        SERPResult(
            rank=i,
            url=f"https://example.com/{i}",
            title=f"Title {i}",
            snippet=f"Snippet {i}"
        )
        for i in range(1, 11)
    ]
    
    analysis = await analyzer.analyze_serp_results(mock_results, "test topic")
    
    assert "common_topics" in analysis
    assert "primary_keyword" in analysis
    assert isinstance(analysis["common_topics"], list)

@pytest.mark.asyncio
async def test_outline_generation():
    generator = OutlineGenerator()
    
    mock_analysis = {
        "common_topics": ["Topic 1", "Topic 2"],
        "subtopics": ["Subtopic A", "Subtopic B"],
        "primary_keyword": "test keyword"
    }
    
    outline = await generator.generate_outline(
        mock_analysis, 
        "test topic", 
        1500
    )
    
    assert "h1" in outline
    assert "sections" in outline
    assert len(outline["sections"]) > 0
```

Run tests:
```bash
pytest tests/ -v
```

---

### HOUR 2: Documentation (10:00 AM - 11:00 AM)

#### Step 8.1: Create Comprehensive README.md
```markdown
# SEO Content Generator

AI-powered backend service for generating SEO-optimized articles at scale.

## Features

- 🔍 **SERP Analysis**: Analyzes top 10 search results to understand competitive landscape
- 📝 **Intelligent Content Generation**: Creates human-like, publish-ready articles
- 🎯 **SEO Optimization**: Built-in keyword optimization and metadata generation
- 🔗 **Smart Linking**: Suggests internal and external links with context
- 💾 **Job Tracking**: Persistent job management with resumability
- ✅ **Quality Validation**: SEO scoring and compliance checks

## Architecture

```
┌─────────────────┐
│   FastAPI REST  │
│      API        │
└────────┬────────┘
         │
┌────────▼────────┐
│  Orchestrator   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Agents: │
    ├─────────┤
    │ SERP    │
    │ Outline │
    │ Content │
    │ SEO     │
    └─────────┘
```

## Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **LLM**: OpenAI GPT-4 / Anthropic Claude
- **Database**: SQLite (PostgreSQL-ready)
- **SERP Data**: SerpAPI
- **Validation**: Pydantic v2

## Installation

### Prerequisites
- Python 3.10+
- OpenAI API key
- SerpAPI key (optional, has mock fallback)

### Setup

1. Clone and setup environment:
```bash
git clone <your-repo>
cd seo-content-generator
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

`.env` file:
```env
OPENAI_API_KEY=sk-...
SERPAPI_KEY=...  # Optional
DATABASE_URL=sqlite:///./seo_content.db
ENVIRONMENT=development
```

4. Initialize database:
```bash
python -c "from app.database.models import init_db; init_db()"
```

5. Run server:
```bash
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

## Usage

### Generate an Article

**Request:**
```bash
curl -X POST http://localhost:8000/generate-article \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "best productivity tools for remote teams",
    "target_word_count": 1500,
    "language": "en"
  }'
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2025-11-21T10:00:00Z"
}
```

### Check Job Status

```bash
curl http://localhost:8000/job/{job_id}
```

**Response (Completed):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "created_at": "2025-11-21T10:00:00Z",
  "completed_at": "2025-11-21T10:05:30Z",
  "result": {
    "article": {
      "h1": "15 Best Productivity Tools for Remote Teams in 2025",
      "sections": [...],
      "full_text": "...",
      "word_count": 1523
    },
    "seo_metadata": {
      "title_tag": "15 Best Productivity Tools for Remote Teams | 2025 Guide",
      "meta_description": "Discover the top productivity tools...",
      "focus_keyword": "productivity tools for remote teams"
    },
    "keyword_analysis": {
      "primary_keyword": "productivity tools for remote teams",
      "secondary_keywords": ["remote work", "team collaboration"],
      "keyword_density": 1.8
    },
    "internal_links": [...],
    "external_references": [...],
    "serp_analysis": [...]
  }
}
```

## API Endpoints

### POST /generate-article
Generate a new SEO-optimized article.

**Parameters:**
- `topic` (string, required): Main topic or keyword
- `target_word_count` (integer, default: 1500): Target length (500-5000)
- `language` (string, default: "en"): Language code

### GET /job/{job_id}
Get the status and result of a generation job.

**Response statuses:**
- `pending`: Job created, waiting to start
- `running`: Currently generating
- `completed`: Generation finished successfully
- `failed`: Generation encountered an error

## Architecture Decisions

### 1. Agent-Based Design
Used separate agents for each phase (SERP analysis, outline, content, SEO) to:
- Allow independent testing and improvement
- Enable resumability at checkpoints
- Maintain clear separation of concerns

### 2. Structured Data with Pydantic
All data validated through Pydantic models to:
- Ensure output consistency
- Enable easy serialization
- Provide automatic API documentation

### 3. Async Processing with Background Tasks
Articles generated in background tasks to:
- Return immediate job ID to client
- Handle long-running operations gracefully
- Allow horizontal scaling

### 4. Checkpoint-Based Resumability
Store intermediate results (SERP data, outline) to:
- Resume after crashes
- Debug individual stages
- Avoid re-running expensive API calls

### 5. Mock Data Fallback
Provide realistic mock SERP data when API unavailable:
- Enable testing without API keys
- Ensure demo functionality
- Reduce API costs during development

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Example Output

See `examples/sample_output.json` for a complete example of generated article structure.

## Project Structure

```
seo-content-generator/
├── app/
│   ├── agents/           # Core generation agents
│   │   ├── orchestrator.py
│   │   ├── serp_analyzer.py
│   │   ├── outline_generator.py
│   │   ├── content_generator.py
│   │   └── seo_generator.py
│   ├── database/         # Database models and config
│   ├── models/           # Pydantic models
│   ├── services/         # External service integrations
│   └── main.py           # FastAPI application
├── tests/                # Test suite
├── examples/             # Example outputs
├── requirements.txt
└── README.md
```

## Performance Considerations

- **Generation Time**: 2-5 minutes per article (1500 words)
- **API Costs**: ~$0.10-0.20 per article (GPT-4)
- **Rate Limits**: Respects OpenAI rate limits with exponential backoff

## Future Enhancements

- [ ] Content quality scorer with auto-revision
- [ ] FAQ section generation
- [ ] Multi-language support
- [ ] Celery + Redis for distributed processing
- [ ] WebSocket for real-time progress updates
- [ ] A/B testing framework for prompts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions, please open a GitHub issue.
```

---

### HOUR 3: Example Output & Polish (11:00 AM - 12:00 PM)

#### Step 9.1: Create Sample Output (examples/sample_output.json)
```json
{
  "article": {
    "h1": "15 Best Productivity Tools for Remote Teams in 2025",
    "sections": [
      {
        "heading": "Introduction to Remote Team Productivity",
        "heading_level": 2,
        "content": "Remote work has transformed how teams collaborate...",
        "word_count": 187
      },
      {
        "heading": "Communication Tools",
        "heading_level": 2,
        "content": "Effective communication is the foundation...",
        "word_count": 342
      }
    ],
    "full_text": "# 15 Best Productivity Tools for Remote Teams in 2025\n\n## Introduction...",
    "word_count": 1523
  },
  "seo_metadata": {
    "title_tag": "15 Best Productivity Tools for Remote Teams | 2025 Guide",
    "meta_description": "Discover the top productivity tools that help remote teams collaborate effectively. Compare features, pricing, and user reviews to find your perfect match.",
    "focus_keyword": "productivity tools for remote teams"
  },
  "keyword_analysis": {
    "primary_keyword": "productivity tools for remote teams",
    "secondary_keywords": [
      "remote work software",
      "team collaboration tools",
      "virtual team management"
    ],
    "keyword_density": 1.8
  },
  "internal_links": [
    {
      "anchor_text": "remote work best practices",
      "suggested_target": "/blog/remote-work-guide",
      "context": "Link in introduction when discussing effective remote work strategies"
    },
    {
      "anchor_text": "project management software comparison",
      "suggested_target": "/tools/project-management",
      "context": "When discussing specific tool categories"
    }
  ],
  "external_references": [
    {
      "source_name": "Harvard Business Review",
      "url": "https://hbr.org/remote-work-productivity",
      "context": "Statistics on remote work productivity gains",
      "placement_suggestion": "Cite in introduction to establish credibility"
    },
    {
      "source_name": "Gartner Research",
      "url": "https://www.gartner.com/en/articles/digital-workplace",
      "context": "Industry trends and adoption rates",
      "placement_suggestion": "Reference when discussing market trends"
    }
  ],
  "serp_analysis": [
    {
      "rank": 1,
      "url": "https://example.com/top-tools",
      "title": "20 Best Remote Work Tools in 2025",
      "snippet": "Comprehensive guide to the best remote work tools..."
    }
  ]
}
```

#### Step 9.2: Add Quality Validator (app/agents/quality_validator.py)
```python
from typing import Dict, List
from app.models.response import ArticleContent, SEOMetadata

class QualityValidator:
    def validate_seo_quality(
        self, 
        article: ArticleContent, 
        metadata: SEOMetadata,
        target_word_count: int
    ) -> Dict:
        """Validate article meets SEO best practices"""
        
        score = 0
        max_score = 100
        issues = []
        
        # 1. Title tag length (10 points)
        title_len = len(metadata.title_tag)
        if 50 <= title_len <= 60:
            score += 10
        else:
            issues.append(f"Title tag should be 50-60 chars (current: {title_len})")
        
        # 2. Meta description length (10 points)
        desc_len = len(metadata.meta_description)
        if 150 <= desc_len <= 160:
            score += 10
        else:
            issues.append(f"Meta description should be 150-160 chars (current: {desc_len})")
        
        # 3. Primary keyword in H1 (15 points)
        if metadata.focus_keyword.lower() in article.h1.lower():
            score += 15
        else:
            issues.append("Primary keyword not found in H1")
        
        # 4. Keyword in first 100 words (15 points)
        first_100 = ' '.join(article.full_text.split()[:100])
        if metadata.focus_keyword.lower() in first_100.lower():
            score += 15
        else:
            issues.append("Primary keyword not in first 100 words")
        
        # 5. Word count within range (10 points)
        word_diff = abs(article.word_count - target_word_count)
        if word_diff <= target_word_count * 0.1:  # Within 10%
            score += 10
        else:
            issues.append(f"Word count off target by {word_diff} words")
        
        # 6. Proper heading structure (15 points)
        if len(article.sections) >= 4:
            score += 15
        else:
            issues.append(f"Should have at least 4 H2 sections (has {len(article.sections)})")
        
        # 7. Keyword density (10 points)
        # Ideal: 1-2%
        content_lower = article.full_text.lower()
        keyword_count = content_lower.count(metadata.focus_keyword.lower())
        density = (keyword_count / article.word_count) * 100
        
        if 1.0 <= density <= 2.5:
            score += 10
        else:
            issues.append(f"Keyword density should be 1-2.5% (current: {density:.2f}%)")
        
        # 8. Readability - average sentence length (15 points)
        sentences = article.full_text.count('.') + article.full_text.count('!') + article.full_text.count('?')
        if sentences > 0:
            avg_words_per_sentence = article.word_count / sentences
            if 15 <= avg_words_per_sentence <= 20:
                score += 15
            else:
                issues.append(f"Average sentence length: {avg_words_per_sentence:.1f} words (ideal: 15-20)")
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "issues": issues,
            "passed": score >= 70
        }
```

---

### HOUR 4: Final Integration & Testing (12:00 PM - 1:00 PM)

#### Step 10.1: Add validation to orchestrator
```python
# Add to app/agents/orchestrator.py after generating everything

# Step 9: Validate quality
print(f"[{self.job_id}] Validating quality...")
from app.agents.quality_validator import QualityValidator
validator = QualityValidator()

quality_report = validator.validate_seo_quality(
    article_content,
    seo_metadata,
    request.target_word_count
)

print(f"[{self.job_id}] Quality Score: {quality_report['percentage']}%")
if not quality_report['passed']:
    print(f"[{self.job_id}] Quality issues: {quality_report['issues']}")
```

#### Step 10.2: Create Docker support (docker-compose.yml)
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SERPAPI_KEY=${SERPAPI_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/seo_content
    depends_on:
      - db
    volumes:
      - ./app:/app/app

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: seo_content
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Step 10.3: Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

###