"""Request models for the SEO Content Generator API.

This module defines the input structures that clients send to the API.
Pydantic handles automatic validation, ensuring all inputs meet our requirements.
"""

from pydantic import BaseModel, Field
from typing import Optional

class ArticleGenerationRequest(BaseModel):
    """Request to generate a new SEO-optimized article.
    
    This is the main input to the system - just give us a topic and we'll
    handle the rest (SERP research, outline, writing, optimization).
    """
    # The topic or primary keyword to write about
    # Example: "best productivity tools for remote teams"
    topic: str = Field(
        ..., 
        min_length=3,  # Must be at least 3 characters
        max_length=200,  # Prevent extremely long inputs
        description="Main topic or keyword to write about"
    )
    
    # How long the article should be
    # Sweet spot for SEO is usually 1500-2500 words
    target_word_count: int = Field(
        default=1500,  # Default to a standard blog post length
        ge=500,  # Minimum 500 words (anything less isn't worth ranking)
        le=5000,  # Maximum 5000 words (diminishing returns)
        description="Target article length in words"
    )
    
    # Language for the article
    # Currently supports any ISO 639-1 two-letter code
    language: str = Field(
        default="en",  # English by default
        pattern="^[a-z]{2}$",  # Must be exactly 2 lowercase letters
        description="Language code (ISO 639-1 format, e.g., 'en', 'es', 'fr')"
    )
    
    class Config:
        # Example request shown in API docs (/docs)
        json_schema_extra = {
            "example": {
                "topic": "best productivity tools for remote teams",
                "target_word_count": 1500,
                "language": "en"
            }
        }

class JobStatusRequest(BaseModel):
    """Request to check the status of a generation job.
    
    Used internally for validation - the actual endpoint uses
    a path parameter instead: GET /job/{job_id}
    """
    job_id: str = Field(
        ..., 
        description="Unique job identifier returned from /generate-article"
    )