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
    description="AI-powered SEO article generation service using Claude Sonnet 3.5",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
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
    """Initialize database on application startup"""
    init_db()
    print("\n🚀 SEO Content Generator API Started")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Alternative Docs: http://localhost:8000/redoc\n")

@app.get("/")
async def root():
    """API root endpoint - provides basic information"""
    return {
        "message": "SEO Content Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "generate_article": "POST /generate-article",
            "check_status": "GET /job/{job_id}",
            "api_docs": "GET /docs"
        }
    }

@app.post("/generate-article", response_model=JobResponse, status_code=202)
async def generate_article(
    request: ArticleGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate an SEO-optimized article
    
    This endpoint creates a new article generation job and runs it in the background.
    
    **Parameters:**
    - **topic** (required): Main topic or keyword for the article
    - **target_word_count** (optional): Desired article length (500-5000 words, default: 1500)
    - **language** (optional): Language code (default: 'en')
    
    **Returns:**
    - job_id: Unique identifier to check job status
    - status: Current job status (will be 'pending' initially)
    - created_at: Timestamp when job was created
    
    **Example:**
    ```json
    {
        "topic": "best productivity tools for remote teams",
        "target_word_count": 1500,
        "language": "en"
    }
    ```
    """
    
    # Create unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
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
    
    print(f"\n📝 New article generation request:")
    print(f"   Job ID: {job_id}")
    print(f"   Topic: {request.topic}")
    print(f"   Target: {request.target_word_count} words")
    
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
    Check the status of an article generation job
    
    **Parameters:**
    - **job_id**: Unique job identifier returned from /generate-article
    
    **Returns:**
    - job_id: The job identifier
    - status: Current status (pending, running, completed, failed)
    - created_at: When the job was created
    - completed_at: When the job finished (if completed)
    - result: Complete article output (if completed)
    - error: Error message (if failed)
    
    **Status Values:**
    - **pending**: Job created, waiting to start
    - **running**: Currently generating article
    - **completed**: Generation finished successfully
    - **failed**: Generation encountered an error
    """
    
    job = db.query(ArticleJob).filter(ArticleJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return JobResponse(
        job_id=job.id,
        status=JobStatus(job.status.value),
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

async def run_generation(job_id: str, request: ArticleGenerationRequest):
    """
    Background task to run article generation
    
    This runs asynchronously so the API can return immediately
    """
    try:
        orchestrator = ArticleGenerationOrchestrator(job_id)
        await orchestrator.generate(request)
    except Exception as e:
        print(f"\n❌ Background generation error for job {job_id}: {e}\n")
        # Error is already saved by orchestrator

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
