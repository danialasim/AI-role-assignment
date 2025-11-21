from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SERPResult(BaseModel):
    """Single search engine result"""
    rank: int
    url: str
    title: str
    snippet: str

class KeywordAnalysis(BaseModel):
    """Keyword usage analysis"""
    primary_keyword: str
    secondary_keywords: List[str]
    keyword_density: float

class InternalLink(BaseModel):
    """Internal link suggestion"""
    anchor_text: str
    suggested_target: str
    context: str

class ExternalReference(BaseModel):
    """External source to cite"""
    source_name: str
    url: str
    context: str
    placement_suggestion: str

class SEOMetadata(BaseModel):
    """SEO metadata for the article"""
    title_tag: str
    meta_description: str
    focus_keyword: str

class ArticleSection(BaseModel):
    """Individual article section"""
    heading: str
    heading_level: int  # 2 for H2, 3 for H3
    content: str
    word_count: int

class ArticleContent(BaseModel):
    """Complete article content"""
    h1: str
    sections: List[ArticleSection]
    full_text: str
    word_count: int

class ArticleOutput(BaseModel):
    """Complete article generation output"""
    article: ArticleContent
    seo_metadata: SEOMetadata
    keyword_analysis: KeywordAnalysis
    internal_links: List[InternalLink]
    external_references: List[ExternalReference]
    serp_analysis: List[SERPResult]

class JobResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[ArticleOutput] = None
    error: Optional[str] = None