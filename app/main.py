"""SEO Content Generator - FastAPI Application.

This is the main entry point for the API. It handles:
- HTTP requests from clients
- Background task orchestration
- Database session management
- API documentation generation

The application uses an async pattern where article generation runs in the
background and clients poll for results, preventing timeouts during the
2-5 minute generation process.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models.request import ArticleGenerationRequest
from app.models.response import JobResponse, JobStatus
from app.database.models import ArticleJob, JobStatusEnum, init_db, get_db
from app.agents.orchestrator import ArticleGenerationOrchestrator

# Initialize FastAPI application with metadata for auto-generated docs
app = FastAPI(
    title="SEO Content Generator API",
    description="AI-powered SEO article generation service using Claude Sonnet 4",
    version="1.0.0",
    docs_url="/docs",  # Interactive Swagger UI
    redoc_url="/redoc"  # Alternative ReDoc UI
)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows frontend applications on different domains/ports to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production!)
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Lifecycle event: runs once when server starts
@app.on_event("startup")
def startup_event():
    """Initialize the database when the application starts.
    
    Creates all necessary tables if they don't exist.
    This is idempotent - safe to run multiple times.
    """
    init_db()
    print("\n🚀 SEO Content Generator API Started")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Alternative Docs: http://localhost:8000/redoc\n")

@app.get("/")
async def root():
    """Root endpoint - provides API information and available endpoints.
    
    Returns:
        Basic API info and a map of available endpoints
    """
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
    """Generate a new SEO-optimized article (async).
    
    This endpoint immediately returns a job_id and runs the generation in
    the background. Clients should poll GET /job/{job_id} to check status.
    
    The generation process takes 2-5 minutes and includes:
    1. Fetching top 10 search results
    2. Analyzing competitive landscape
    3. Generating outline
    4. Writing article content
    5. Creating SEO metadata
    6. Suggesting internal/external links
    7. Validating quality
    
    Args:
        request: Article generation parameters (topic, word count, language)
        background_tasks: FastAPI's background task queue
        db: Database session (auto-injected)
    
    Returns:
        JobResponse with job_id, status=pending, and created_at timestamp
        
    Status Code:
        202 Accepted - Request acknowledged, processing in background
    
    Example Request:
        ```json
        {
            "topic": "best productivity tools for remote teams",
            "target_word_count": 1500,
            "language": "en"
        }
        ```
    
    Example Response:
        ```json
        {
            "job_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "pending",
            "created_at": "2025-11-22T10:00:00Z",
            "completed_at": null,
            "result": null,
            "error": null
        }
        ```
    """
    
    # Step 1: Generate a unique job ID using UUID4 (random)
    # This ID will be used to track and query the job status
    job_id = str(uuid.uuid4())
    
    # Step 2: Create a database record for this job
    # Status starts as PENDING (not yet started)
    job = ArticleJob(
        id=job_id,
        topic=request.topic,
        target_word_count=request.target_word_count,
        language=request.language,
        status=JobStatusEnum.PENDING,
        created_at=datetime.utcnow()
    )
    
    # Step 3: Save to database immediately
    # This ensures the job exists before we start background processing
    db.add(job)
    db.commit()
    
    # Log the request for monitoring/debugging
    print(f"\n📝 New article generation request:")
    print(f"   Job ID: {job_id}")
    print(f"   Topic: {request.topic}")
    print(f"   Target: {request.target_word_count} words")
    
    # Step 4: Queue the actual generation work in the background
    # This runs in a separate thread/process so we can return immediately
    background_tasks.add_task(run_generation, job_id, request)
    
    # Step 5: Return the job info to the client
    # They'll use the job_id to poll for results
    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=job.created_at
    )

@app.get("/job/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Check the status and result of an article generation job.
    
    Clients should poll this endpoint every 5-10 seconds to check
    if their article is ready. When status changes to 'completed',
    the result field will contain the full article.
    
    Args:
        job_id: The UUID returned from POST /generate-article
        db: Database session (auto-injected)
    
    Returns:
        JobResponse with current status and result (if completed)
        
    Raises:
        404: If job_id doesn't exist in database
    
    Status Transitions:
        pending → running → completed (success)
        pending → running → failed (error occurred)
    
    Example Response (completed):
        ```json
        {
            "job_id": "123e4567-...",
            "status": "completed",
            "created_at": "2025-11-22T10:00:00Z",
            "completed_at": "2025-11-22T10:03:42Z",
            "result": {
                "article": {...},
                "seo_metadata": {...},
                "keyword_analysis": {...},
                "internal_links": [...],
                "external_references": [...]
            },
            "error": null
        }
        ```
    """
    
    # Query the database for this job
    job = db.query(ArticleJob).filter(ArticleJob.id == job_id).first()
    
    # Return 404 if job doesn't exist
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    # Return the job status and result
    # Note: job.result is already parsed from JSON by SQLAlchemy
    return JobResponse(
        job_id=job.id,
        status=JobStatus(job.status.value),  # Convert DB enum to API enum
        created_at=job.created_at,
        completed_at=job.completed_at,
        result=job.result,  # Full ArticleOutput when completed
        error=job.error  # Error message if failed
    )

@app.get("/health")
async def health_check():
    """Simple health check endpoint for monitoring and load balancers.
    
    Returns a 200 OK with basic service status. Use this endpoint
    to verify the API is running and accepting requests.
    
    Returns:
        Dict with status and current timestamp
        
    Example Response:
        ```json
        {
            "status": "healthy",
            "timestamp": "2025-11-22T10:15:30.123456"
        }
        ```
    
    Use Cases:
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Uptime monitoring (UptimeRobot, Pingdom, etc.)
        - Quick API availability tests before making real requests
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

async def run_generation(job_id: str, request: ArticleGenerationRequest):
    """Background task that executes the full article generation pipeline.
    
    This function runs asynchronously in the background (via BackgroundTasks),
    allowing the API to return a 202 Accepted response immediately while
    the actual generation happens separately.
    
    The Pipeline (10 Steps):
        1. SERP Analysis - Fetch top 10 Google results for the topic
        2. Outline Generation - Create H2/H3 structure based on SERP analysis
        3. Content Writing - Generate full article following the outline
        4. SEO Metadata - Create optimized title, description, slug
        5. Keyword Analysis - Identify primary/secondary keywords with density
        6. Internal Linking - Suggest relevant internal link opportunities
        7. External References - Find authoritative sources for E-E-A-T
        8. Quality Validation - Check word count, readability, SEO compliance
        9. Final Assembly - Combine all components into ArticleOutput
        10. Database Save - Persist complete result with status=completed
    
    Args:
        job_id: The unique job identifier created in generate_article()
        request: The original user request with topic, word count, language
    
    Side Effects:
        - Updates database job status: pending → running → completed/failed
        - Saves checkpoints at steps 1 (SERP) and 3 (outline)
        - Logs progress to console with emojis for visibility
        - Persists final result or error message to database
    
    Error Handling:
        If ANY step fails, the orchestrator catches the exception,
        saves it to the database with status=failed, and this function
        logs it to console. The API client will see the error when
        they poll GET /job/{job_id}.
    
    Execution Time:
        - Mock mode: ~15-30 seconds (no real API calls)
        - Real mode: ~3-5 minutes (depends on Claude API response time)
    """
    try:
        # Create the orchestrator for this specific job
        orchestrator = ArticleGenerationOrchestrator(job_id)
        
        # Run the full 10-step pipeline
        # This will update the job status in the database automatically
        await orchestrator.generate(request)
        
    except Exception as e:
        # This catch-all is a safety net - the orchestrator should handle
        # most errors internally. If we get here, something unexpected happened.
        print(f"\n❌ Critical background error for job {job_id}: {e}\n")
        # The orchestrator already saved the error to DB, so just log it

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
