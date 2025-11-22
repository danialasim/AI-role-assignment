"""Article Generation Orchestrator - The Brain of the System.

This module coordinates all 5 specialized agents to execute a 10-step pipeline
that transforms a user's topic into a complete SEO-optimized article.

The 10-Step Pipeline:
    1. SERP Fetching - Get top 10 Google results
    2. SERP Analysis - Extract topics, keywords, content gaps
    3. Outline Generation - Create H2/H3 structure (checkpoint saved)
    4. Content Generation - Write full article following outline
    5. SEO Metadata - Generate title, description, slug
    6. Internal Links - Suggest relevant internal link opportunities
    7. External References - Find authoritative sources
    8. Keyword Analysis - Calculate density and distribution
    9. Quality Validation - Check word count, readability, SEO compliance
    10. Final Assembly - Package everything into ArticleOutput

Checkpoint System:
    - After Step 1: Save serp_data (enables debugging SERP analysis)
    - After Step 3: Save outline_data (enables debugging content generation)
    - If generation crashes, we have checkpoints for debugging
    - Currently not implementing resume-from-checkpoint, but data structure supports it

Error Handling:
    - Any step failure triggers catch block
    - Error message saved to database with status=FAILED
    - User sees error when polling GET /job/{job_id}
    - Graceful failure prevents partial/corrupted results

Execution Time:
    - Mock mode: ~15-30 seconds (instant LLM responses)
    - Real mode: ~3-5 minutes (depends on Claude API latency)
"""

from app.agents.serp_analyzer import SERPAnalyzer
from app.agents.outline_generator import OutlineGenerator
from app.agents.content_generator import ContentGenerator
from app.agents.seo_metadata_generator import SEOMetadataGenerator
from app.agents.quality_validator import QualityValidator
from app.services.serp_service import SerpAPIService
from app.models.request import ArticleGenerationRequest
from app.models.response import ArticleOutput
from app.database.models import ArticleJob, JobStatusEnum, SessionLocal
from datetime import datetime
import json

class ArticleGenerationOrchestrator:
    """Orchestrates all agents to execute the 10-step article generation pipeline.
    
    This is the central coordinator that manages the entire workflow from
    topic input to complete article output. Each orchestrator instance is
    tied to a specific job_id for database tracking.
    """
    
    def __init__(self, job_id: str):
        """Initialize orchestrator with all required agents and services.
        
        Args:
            job_id: UUID string identifying this specific generation job
        
        Initializes:
            - SERP Service: Fetches Google search results (Step 1)
            - SERP Analyzer: Extracts insights from search results (Step 2)
            - Outline Generator: Creates article structure (Step 3)
            - Content Generator: Writes article sections (Step 4)
            - SEO Generator: Creates metadata, links, references (Steps 5-7)
            - Quality Validator: Checks SEO compliance (Step 9)
        
        All agents share the same LLM service instance (either real or mock).
        """
        self.job_id = job_id
        
        # Service layer
        self.serp_service = SerpAPIService()
        
        # Agent layer (5 specialized agents)
        self.serp_analyzer = SERPAnalyzer()
        self.outline_generator = OutlineGenerator()
        self.content_generator = ContentGenerator()
        self.seo_generator = SEOMetadataGenerator()
        self.quality_validator = QualityValidator()
    
    async def generate(self, request: ArticleGenerationRequest) -> ArticleOutput:
        """Execute the complete 10-step article generation pipeline.
        
        This is the main entry point called by the background task in main.py.
        It coordinates all agents in sequence, saves checkpoints, and handles
        errors gracefully.
        
        Args:
            request: User's generation request (topic, word count, language)
        
        Returns:
            ArticleOutput with complete article, SEO data, and metadata
        
        Raises:
            Exception: If any step fails (error is saved to database)
        
        Side Effects:
            - Updates job status in database (pending → running → completed/failed)
            - Saves checkpoints at steps 1 and 3
            - Logs progress to console with emojis
            - Saves final result or error to database
        
        Pipeline Steps:
            1. Fetch SERP results from Google (or mock data)
            2. Analyze SERP to extract topics, keywords, content gaps
            3. Generate article outline with H2/H3 structure
            4. Generate full article content following outline
            5. Generate SEO metadata (title, description, slug)
            6. Suggest internal links to other articles
            7. Find external authoritative references
            8. Analyze keyword usage and density
            9. Validate quality against SEO criteria
            10. Package everything into ArticleOutput and save
        
        Quality Checks:
            - Word count within 10% of target
            - Keyword density 1-2.5%
            - Title 50-60 characters
            - Meta description 150-160 characters
            - At least 3 H2 headings
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Article Generation")
        print(f"Job ID: {self.job_id}")
        print(f"Topic: {request.topic}")
        print(f"Target: {request.target_word_count} words")
        print(f"{'='*60}\n")
        
        try:
            # Update database: pending → running
            # This lets API clients see the job is actively processing
            self._update_status(JobStatusEnum.RUNNING)
            
            # ===== STEP 1: Fetch SERP Results =====
            # Get top 10 Google results for the topic
            # In mock mode: Returns pre-defined realistic results
            # In real mode: Calls SerpAPI (costs 1 credit per search)
            print(f"📍 Step 1/10: Fetching SERP results...")
            serp_results = self.serp_service.search(request.topic)
            
            # Save checkpoint: SERP data for debugging
            self._save_checkpoint("serp_data", [
                {"rank": r.rank, "url": r.url, "title": r.title, "snippet": r.snippet}
                for r in serp_results
            ])
            
            # ===== STEP 2: Analyze SERP =====
            # Extract: common topics, subtopics, content gaps, keywords
            # This tells us what's already ranking and what we can add
            print(f"\n📍 Step 2/10: Analyzing SERP data...")
            serp_analysis = await self.serp_analyzer.analyze_serp_results(
                serp_results, request.topic
            )
            
            # ===== STEP 3: Generate Outline =====
            # Create H1, H2s, H3s based on SERP analysis
            # Distributes word count across sections
            print(f"\n📍 Step 3/10: Generating article outline...")
            outline = await self.outline_generator.generate_outline(
                serp_analysis, request.topic, request.target_word_count
            )
            
            # Save checkpoint: Outline for debugging content generation
            self._save_checkpoint("outline_data", outline)
            
            # ===== STEP 4: Generate Article Content =====
            # Write intro, sections, conclusion following outline
            # This is the longest step (~60% of total time)
            print(f"\n📍 Step 4/10: Generating article content...")
            article_content = await self.content_generator.generate_article(
                outline, serp_analysis
            )
            
            # ===== STEP 5: Generate SEO Metadata =====
            # Create title tag (50-60 chars), meta description (150-160), slug
            print(f"\n📍 Step 5/10: Generating SEO metadata...")
            seo_metadata = await self.seo_generator.generate_seo_metadata(
                article_content.full_text,
                article_content.h1,
                serp_analysis.get("primary_keyword", request.topic)
            )
            
            # ===== STEP 6: Generate Internal Links =====
            # Suggest 4-5 internal links with anchor text and context
            print(f"\n📍 Step 6/10: Generating internal link suggestions...")
            internal_links = await self.seo_generator.generate_internal_links(
                article_content.full_text, request.topic
            )
            
            # ===== STEP 7: Generate External References =====
            # Find 3-5 authoritative external sources for E-E-A-T
            print(f"\n📍 Step 7/10: Generating external reference suggestions...")
            external_refs = await self.seo_generator.generate_external_references(
                article_content.full_text, request.topic
            )
            
            # ===== STEP 8: Analyze Keywords =====
            # Calculate keyword density and distribution
            # Target: 1-2.5% density for primary keyword
            print(f"\n📍 Step 8/10: Analyzing keyword usage...")
            keyword_analysis = self.seo_generator.analyze_keywords(
                article_content.full_text,
                serp_analysis.get("primary_keyword", request.topic),
                serp_analysis.get("secondary_keywords", [])
            )
            
            # ===== STEP 9: Validate Quality =====
            # Check: word count, title length, description length, keyword density
            print(f"\n📍 Step 9/10: Validating quality...")
            quality_report = self.quality_validator.validate_seo_quality(
                article_content,
                seo_metadata,
                request.target_word_count
            )
            
            # ===== STEP 10: Package Output =====
            # Combine all components into final ArticleOutput
            print(f"\n📍 Step 10/10: Packaging results...")
            result = ArticleOutput(
                article=article_content,
                seo_metadata=seo_metadata,
                keyword_analysis=keyword_analysis,
                internal_links=internal_links,
                external_references=external_refs,
                serp_analysis=serp_results
            )
            
            # Save to database with status=COMPLETED
            # User can now retrieve the result via GET /job/{job_id}
            self._save_result(result)
            
            # Success message with quality metrics
            print(f"\n{'='*60}")
            print(f"✅ Article Generation Completed Successfully!")
            print(f"   Quality Score: {quality_report['percentage']}%")
            print(f"   Word Count: {article_content.word_count}")
            print(f"   Status: {'PASSED' if quality_report['passed'] else 'NEEDS REVIEW'}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            # Catch any failure from the 10-step pipeline
            # Save error to database so user can see what went wrong
            error_msg = f"Generation failed: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}\n")
            
            # Persist error to database with status=FAILED
            self._save_error(error_msg)
            
            # Re-raise so background task logs it
            raise
    
    def _update_status(self, status: JobStatusEnum):
        """Update job status in database.
        
        Called when status changes: PENDING → RUNNING → COMPLETED/FAILED
        
        Args:
            status: New status to set
        
        Side Effects:
            - Updates job.status in database
            - Commits transaction immediately
            - Logs warning if update fails (non-fatal)
        """
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.status = status
                db.commit()
        except Exception as e:
            print(f"⚠️  Failed to update status: {e}")
        finally:
            db.close()
    
    def _save_checkpoint(self, field: str, data):
        """Save checkpoint data for debugging and potential resumability.
        
        Checkpoints saved:
            - serp_data (after Step 1): List of SERP results
            - outline_data (after Step 3): Article outline structure
        
        These enable:
            - Debugging specific pipeline steps
            - Analyzing what went wrong if generation fails
            - Future feature: Resume from checkpoint if crashed
        
        Args:
            field: Database column name ("serp_data" or "outline_data")
            data: JSON-serializable data to save
        
        Side Effects:
            - Updates specified field in database
            - Logs checkpoint save confirmation
            - Non-fatal if save fails
        """
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                setattr(job, field, data)  # Dynamically set field
                db.commit()
                print(f"   💾 Checkpoint saved: {field}")
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
        finally:
            db.close()
    
    def _save_result(self, result: ArticleOutput):
        """Save final successful result to database.
        
        Args:
            result: Complete ArticleOutput with all components
        
        Side Effects:
            - Converts Pydantic model to JSON and stores in job.result
            - Sets job.status = COMPLETED
            - Sets job.completed_at = current UTC time
            - Commits transaction
        
        After this:
            - User can retrieve result via GET /job/{job_id}
            - API will return status="completed" with full article
        """
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                # Convert Pydantic model to JSON for storage
                job.result = json.loads(result.model_dump_json())
                job.status = JobStatusEnum.COMPLETED
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"⚠️  Failed to save result: {e}")
        finally:
            db.close()
    
    def _save_error(self, error: str):
        """Save error message when generation fails.
        
        Args:
            error: Human-readable error message
        
        Side Effects:
            - Sets job.error = error message
            - Sets job.status = FAILED
            - Sets job.completed_at = current UTC time
            - Commits transaction
        
        After this:
            - User sees error via GET /job/{job_id}
            - API returns status="failed" with error field populated
            - Can analyze what went wrong from error message
        """
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.error = error
                job.status = JobStatusEnum.FAILED
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"⚠️  Failed to save error: {e}")
        finally:
            db.close()
