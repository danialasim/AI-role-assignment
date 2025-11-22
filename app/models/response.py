"""Response models for the SEO Content Generator API.

This module defines all the data structures returned by the API,
including article content, SEO metadata, and job status information.
All models use Pydantic for automatic validation and serialization.
"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Job execution status.
    
    Tracks the lifecycle of an article generation job:
    - PENDING: Job created, waiting to start
    - RUNNING: Currently generating article
    - COMPLETED: Successfully finished
    - FAILED: Encountered an error
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SERPResult(BaseModel):
    """A single search engine result from the top 10 rankings.
    
    Contains the key information we extract from each search result
    to understand what content is currently ranking well.
    """
    rank: int  # Position in search results (1-10)
    url: str   # Full URL of the ranking page
    title: str # Page title (usually H1)
    snippet: str  # Meta description or preview text shown in results

class KeywordAnalysis(BaseModel):
    """Analysis of keyword usage throughout the article.
    
    Tracks how well we've optimized for target keywords without
    over-stuffing (which search engines penalize).
    """
    primary_keyword: str  # Main keyword we're targeting (e.g., "productivity tools")
    secondary_keywords: List[str]  # Related keywords to include naturally
    keyword_density: float  # Percentage of content that is the primary keyword (target: 1-2.5%)

class InternalLink(BaseModel):
    """Suggestion for an internal link to another page on the site.
    
    Internal linking helps distribute page authority and keeps users
    engaged by connecting related content.
    """
    anchor_text: str  # The clickable text (should be descriptive, not "click here")
    suggested_target: str  # URL or topic of the target page
    context: str  # Why this link is relevant and where it should be placed

class ExternalReference(BaseModel):
    """Authoritative external source to reference in the article.
    
    Citing reputable sources builds trust and signals to search engines
    that the content is well-researched (E-E-A-T: Expertise, Authority, Trust).
    """
    source_name: str  # Name of the source (e.g., "Harvard Business Review", "Gartner")
    url: str  # Full URL to the source
    context: str  # What this source adds to the article
    placement_suggestion: str  # Where in the article this citation fits best

class SEOMetadata(BaseModel):
    """SEO metadata tags that appear in search results.
    
    These are critical for click-through rates - they're what users
    see in Google before deciding whether to visit your page.
    """
    title_tag: str  # Page title (50-60 chars, appears in browser tab and search results)
    meta_description: str  # Preview text (150-160 chars, shown under title in search)
    focus_keyword: str  # Primary keyword this page is optimized for

class ArticleSection(BaseModel):
    """A single section of the article (H2 or H3).
    
    Articles are broken into sections for better readability and SEO.
    Each section covers a specific subtopic.
    """
    heading: str  # Section title (e.g., "Benefits of Remote Work")
    heading_level: int  # 2 for H2 (main sections), 3 for H3 (subsections)
    content: str  # Full text content of this section
    word_count: int  # Number of words in this section

class ArticleContent(BaseModel):
    """The complete article with all its content.
    
    Combines the title, all sections, and provides both structured
    access to individual sections and the full markdown text.
    """
    h1: str  # Article title (only one H1 per page for SEO)
    sections: List[ArticleSection]  # All H2 and H3 sections
    full_text: str  # Complete article in markdown format
    word_count: int  # Total word count across all sections

class ArticleOutput(BaseModel):
    """The complete output from article generation - everything you need.
    
    This is the final package delivered after a successful generation,
    containing the article itself plus all SEO optimization data.
    """
    article: ArticleContent  # The actual article content
    seo_metadata: SEOMetadata  # Title tags and meta descriptions
    keyword_analysis: KeywordAnalysis  # How well we hit keyword targets
    internal_links: List[InternalLink]  # Suggested links to other pages (3-5)
    external_references: List[ExternalReference]  # Authoritative sources to cite (2-4)
    serp_analysis: List[SERPResult]  # The top 10 results we analyzed

class JobResponse(BaseModel):
    """Response for checking the status of an article generation job.
    
    Since article generation takes 2-5 minutes, we use an async pattern:
    1. POST /generate-article returns a job_id immediately
    2. Client polls GET /job/{id} to check status
    3. When status=completed, the result field contains the article
    """
    job_id: str  # Unique identifier for this generation job
    status: JobStatus  # Current status (pending, running, completed, failed)
    created_at: datetime  # When the job was submitted
    completed_at: Optional[datetime] = None  # When it finished (null if still running)
    result: Optional[ArticleOutput] = None  # The generated article (null until completed)
    error: Optional[str] = None  # Error message if status=failed