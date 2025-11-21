from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
from app.config import get_settings

Base = declarative_base()

class JobStatusEnum(enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ArticleJob(Base):
    """Article generation job model"""
    __tablename__ = "article_jobs"
    
    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False)
    target_word_count = Column(Integer, default=1500)
    language = Column(String, default="en")
    status = Column(SQLEnum(JobStatusEnum), default=JobStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Checkpoint data for resumability
    serp_data = Column(JSON, nullable=True)
    outline_data = Column(JSON, nullable=True)
    
    # Final results
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

# Database setup
settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()