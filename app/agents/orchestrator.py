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
    """Main orchestrator coordinating all agents for article generation"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.serp_service = SerpAPIService()
        self.serp_analyzer = SERPAnalyzer()
        self.outline_generator = OutlineGenerator()
        self.content_generator = ContentGenerator()
        self.seo_generator = SEOMetadataGenerator()
        self.quality_validator = QualityValidator()
    
    async def generate(self, request: ArticleGenerationRequest) -> ArticleOutput:
        """
        Main orchestration method - coordinates all agents
        
        Flow:
        1. Fetch SERP results (checkpoint)
        2. Analyze SERP data
        3. Generate outline (checkpoint)
        4. Generate article content
        5. Generate SEO metadata
        6. Generate internal links
        7. Generate external references
        8. Analyze keywords
        9. Validate quality
        10. Package and save result
        """
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Article Generation")
        print(f"Job ID: {self.job_id}")
        print(f"Topic: {request.topic}")
        print(f"Target: {request.target_word_count} words")
        print(f"{'='*60}\n")
        
        try:
            # Update status to running
            self._update_status(JobStatusEnum.RUNNING)
            
            # Step 1: Fetch SERP results
            print(f"📍 Step 1/10: Fetching SERP results...")
            serp_results = self.serp_service.search(request.topic)
            self._save_checkpoint("serp_data", [
                {"rank": r.rank, "url": r.url, "title": r.title, "snippet": r.snippet}
                for r in serp_results
            ])
            
            # Step 2: Analyze SERP
            print(f"\n📍 Step 2/10: Analyzing SERP data...")
            serp_analysis = await self.serp_analyzer.analyze_serp_results(
                serp_results, request.topic
            )
            
            # Step 3: Generate outline
            print(f"\n📍 Step 3/10: Generating article outline...")
            outline = await self.outline_generator.generate_outline(
                serp_analysis, request.topic, request.target_word_count
            )
            self._save_checkpoint("outline_data", outline)
            
            # Step 4: Generate content
            print(f"\n📍 Step 4/10: Generating article content...")
            article_content = await self.content_generator.generate_article(
                outline, serp_analysis
            )
            
            # Step 5: Generate SEO metadata
            print(f"\n📍 Step 5/10: Generating SEO metadata...")
            seo_metadata = await self.seo_generator.generate_seo_metadata(
                article_content.full_text,
                article_content.h1,
                serp_analysis.get("primary_keyword", request.topic)
            )
            
            # Step 6: Generate internal links
            print(f"\n📍 Step 6/10: Generating internal link suggestions...")
            internal_links = await self.seo_generator.generate_internal_links(
                article_content.full_text, request.topic
            )
            
            # Step 7: Generate external references
            print(f"\n📍 Step 7/10: Generating external reference suggestions...")
            external_refs = await self.seo_generator.generate_external_references(
                article_content.full_text, request.topic
            )
            
            # Step 8: Analyze keywords
            print(f"\n📍 Step 8/10: Analyzing keyword usage...")
            keyword_analysis = self.seo_generator.analyze_keywords(
                article_content.full_text,
                serp_analysis.get("primary_keyword", request.topic),
                serp_analysis.get("secondary_keywords", [])
            )
            
            # Step 9: Validate quality
            print(f"\n📍 Step 9/10: Validating quality...")
            quality_report = self.quality_validator.validate_seo_quality(
                article_content,
                seo_metadata,
                request.target_word_count
            )
            
            # Step 10: Package output
            print(f"\n📍 Step 10/10: Packaging results...")
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
            
            print(f"\n{'='*60}")
            print(f"✅ Article Generation Completed Successfully!")
            print(f"   Quality Score: {quality_report['percentage']}%")
            print(f"   Word Count: {article_content.word_count}")
            print(f"   Status: {'PASSED' if quality_report['passed'] else 'NEEDS REVIEW'}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            print(f"\n❌ ERROR: {error_msg}\n")
            self._save_error(error_msg)
            raise
    
    def _update_status(self, status: JobStatusEnum):
        """Update job status in database"""
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
        """Save checkpoint data for resumability"""
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                setattr(job, field, data)
                db.commit()
                print(f"   💾 Checkpoint saved: {field}")
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
        finally:
            db.close()
    
    def _save_result(self, result: ArticleOutput):
        """Save final result to database"""
        db = SessionLocal()
        try:
            job = db.query(ArticleJob).filter(ArticleJob.id == self.job_id).first()
            if job:
                job.result = json.loads(result.model_dump_json())
                job.status = JobStatusEnum.COMPLETED
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"⚠️  Failed to save result: {e}")
        finally:
            db.close()
    
    def _save_error(self, error: str):
        """Save error to database"""
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
