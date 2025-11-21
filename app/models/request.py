from pydantic import BaseModel, Field
from typing import Optional

class ArticleGenerationRequest(BaseModel):
    """Request model for article generation"""
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic or keyword")
    target_word_count: int = Field(default=1500, ge=500, le=5000, description="Target article length")
    language: str = Field(default="en", pattern="^[a-z]{2}$", description="Language code (ISO 639-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "best productivity tools for remote teams",
                "target_word_count": 1500,
                "language": "en"
            }
        }

class JobStatusRequest(BaseModel):
    """Request model for checking job status"""
    job_id: str = Field(..., description="Unique job identifier")