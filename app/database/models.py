"""Database Models - SQLAlchemy ORM for Article Generation Jobs.

This module defines the database schema and provides session management
for persisting article generation jobs and their results.

Database: SQLite (seo_content.db)
    - Single-file database in project root
    - Perfect for development and demos
    - Production could swap to PostgreSQL by changing DATABASE_URL

Key Features:
    - Job lifecycle tracking (pending → running → completed/failed)
    - Checkpoint system (saves SERP and outline data mid-process)
    - Resumable generation (can restart from checkpoint if crashed)
    - JSON storage for complex nested data structures
    - Dependency injection pattern for FastAPI integration

Schema Design:
    ArticleJob table stores everything about a generation request:
    - Request parameters (topic, word count, language)
    - Status and timestamps (created_at, completed_at)
    - Checkpoint data (serp_data, outline_data for step 1 & 3)
    - Final results (complete ArticleOutput as JSON)
    - Error messages (if generation failed)
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
from app.config import get_settings

# Base class for all ORM models
Base = declarative_base()

class JobStatusEnum(enum.Enum):
    """Job status enumeration tracking generation lifecycle.
    
    Status Flow:
        PENDING → RUNNING → COMPLETED (success path)
        PENDING → RUNNING → FAILED (error occurred)
    
    Never:
        - PENDING to COMPLETED (must go through RUNNING)
        - FAILED to RUNNING (failed jobs stay failed)
        - COMPLETED to RUNNING (completed jobs don't re-run)
    """
    PENDING = "pending"      # Job created, queued for processing
    RUNNING = "running"      # Currently executing 10-step pipeline
    COMPLETED = "completed"  # Successfully finished, result available
    FAILED = "failed"        # Error occurred, check error field

class ArticleJob(Base):
    """SQLAlchemy model for article generation jobs.
    
    This table stores complete state for each article generation request,
    enabling async processing, checkpointing, and result retrieval.
    
    Checkpoint System:
        serp_data saved after Step 1 (SERP analysis complete)
        outline_data saved after Step 3 (outline generation complete)
        
        If generation crashes, we could resume from last checkpoint
        instead of starting over. Currently not implemented but the
        data structure supports it.
    
    JSON Storage:
        SQLite stores JSON as TEXT internally, SQLAlchemy handles conversion.
        Fields like serp_data, outline_data, and result can store complex
        nested dictionaries/arrays without needing separate tables.
    """
    __tablename__ = "article_jobs"
    
    # Primary Key - UUID4 string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    id = Column(String, primary_key=True)
    
    # Request Parameters - copied from ArticleGenerationRequest
    topic = Column(String, nullable=False)  # User's search query/topic
    target_word_count = Column(Integer, default=1500)  # Desired article length
    language = Column(String, default="en")  # ISO 639-1 language code
    
    # Job Status Tracking
    status = Column(SQLEnum(JobStatusEnum), default=JobStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)  # When job was created
    completed_at = Column(DateTime, nullable=True)  # When job finished (success or failure)
    
    # Checkpoint Data - saved mid-process for debugging and potential resume
    # Stored as JSON to handle complex nested structures
    serp_data = Column(JSON, nullable=True)     # Step 1: SERP analysis results
    outline_data = Column(JSON, nullable=True)  # Step 3: Article outline structure
    
    # Final Results - only populated when status=COMPLETED or FAILED
    result = Column(JSON, nullable=True)  # Complete ArticleOutput with all sections
    error = Column(Text, nullable=True)   # Error message if status=FAILED

# Database Setup - creates engine and session factory
# Configuration loaded from .env via get_settings()
settings = get_settings()

# Create SQLAlchemy engine
# - SQLite: check_same_thread=False allows multi-threaded access
# - echo=False: Disable SQL query logging (set True for debugging)
engine = create_engine(
    settings.database_url,  # e.g., "sqlite:///./seo_content.db"
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False  # Set to True to see all SQL queries
)

# Session factory - creates new database sessions
# autocommit=False: Require explicit .commit() calls
# autoflush=False: Manual control over when changes are flushed
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database by creating all tables.
    
    Creates the article_jobs table if it doesn't exist.
    Safe to call multiple times - won't drop existing data.
    
    Called from:
        - app/main.py startup event
        - First API request (via lazy initialization)
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def get_db():
    """Database session dependency for FastAPI endpoints.
    
    This is a generator function that:
    1. Creates a new SQLAlchemy session
    2. Yields it to the endpoint (via Depends(get_db))
    3. Closes the session when endpoint completes
    
    Usage in endpoints:
        @app.get("/job/{job_id}")
        async def get_job(job_id: str, db: Session = Depends(get_db)):
            job = db.query(ArticleJob).filter(ArticleJob.id == job_id).first()
            return job
    
    Benefits:
        - Automatic session lifecycle management
        - Ensures connections are properly closed
        - Prevents connection leaks in long-running apps
        - One session per request (thread-safe)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Always close, even if endpoint raises exception