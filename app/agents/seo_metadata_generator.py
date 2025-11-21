from typing import Dict, List
from app.services.llm_service import LLMService
from app.models.response import (
    SEOMetadata, KeywordAnalysis, InternalLink, ExternalReference
)

class SEOMetadataGenerator:
    """Agent for generating SEO metadata and link suggestions"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_seo_metadata(
        self, 
        article_content: str, 
        h1: str,
        primary_keyword: str
    ) -> SEOMetadata:
        """Generate SEO title tag and meta description"""
        
        prompt = f"""Generate SEO metadata for this article:

Article Title (H1): {h1}
Primary Keyword: {primary_keyword}
Article Preview (first 250 chars): {article_content[:250]}

Create the following (return as JSON):
{{
  "title_tag": "SEO title (50-60 characters, include primary keyword near the start)",
  "meta_description": "Compelling meta description (EXACTLY 155 characters, include keyword, call-to-action)",
  "focus_keyword": "Primary keyword phrase"
}}

REQUIREMENTS:
- Title tag: 50-60 characters, engaging, includes primary keyword
- Meta description: EXACTLY 155 characters (count carefully!), compelling, includes keyword and benefit
- Focus keyword: Should match or be very close to the primary keyword

Return ONLY the JSON object."""

        try:
            metadata_dict = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an SEO expert who creates compelling meta tags that improve click-through rates."
            )
            
            return SEOMetadata(
                title_tag=metadata_dict.get("title_tag", h1[:60]),
                meta_description=metadata_dict.get("meta_description", ""),
                focus_keyword=metadata_dict.get("focus_keyword", primary_keyword)
            )
            
        except Exception as e:
            print(f"⚠️  SEO metadata generation failed: {e}, using fallback")
            return SEOMetadata(
                title_tag=h1[:60] if len(h1) <= 60 else h1[:57] + "...",
                meta_description=f"Learn everything about {primary_keyword}. Complete guide with tips, strategies, and best practices.",
                focus_keyword=primary_keyword
            )
    
    async def generate_internal_links(
        self, 
        article_content: str, 
        topic: str
    ) -> List[InternalLink]:
        """Generate internal link suggestions"""
        
        prompt = f"""Suggest 3-5 internal links for this article about "{topic}".

Article excerpt (first 500 characters):
{article_content[:500]}...

For each internal link, provide (return as JSON):
{{
  "links": [
    {{
      "anchor_text": "3-6 word anchor text",
      "suggested_target": "Descriptive page/topic to link to",
      "context": "Where and why this link makes sense in the article"
    }}
  ]
}}

REQUIREMENTS:
- Suggest links to related, relevant content
- Anchor text should be natural and descriptive
- Links should add value for the reader
- Suggest 3-5 links total

Return ONLY the JSON object."""

        try:
            links_data = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an SEO expert who creates natural, valuable internal linking strategies."
            )
            
            return [
                InternalLink(
                    anchor_text=link.get("anchor_text", ""),
                    suggested_target=link.get("suggested_target", ""),
                    context=link.get("context", "")
                )
                for link in links_data.get("links", [])[:5]
            ]
            
        except Exception as e:
            print(f"⚠️  Internal link generation failed: {e}, using fallback")
            return [
                InternalLink(
                    anchor_text=f"{topic} best practices",
                    suggested_target=f"/blog/{topic.replace(' ', '-')}-best-practices",
                    context="Link when discussing implementation strategies"
                )
            ]
    
    async def generate_external_references(
        self, 
        article_content: str, 
        topic: str
    ) -> List[ExternalReference]:
        """Generate external reference suggestions"""
        
        prompt = f"""Suggest 2-4 authoritative external sources to cite for an article about "{topic}".

Focus on credible sources like:
- Industry research reports
- Academic studies
- Government/official statistics  
- Established publications (Forbes, HBR, TechCrunch, etc.)
- Official documentation

For each source, provide (return as JSON):
{{
  "references": [
    {{
      "source_name": "Publication or organization name",
      "url": "Realistic URL (use actual domains like harvard.edu, .gov sites, forbes.com)",
      "context": "What information/data this source provides",
      "placement_suggestion": "Where in the article to cite this (intro, specific section, etc.)"
    }}
  ]
}}

REQUIREMENTS:
- Suggest 2-4 authoritative sources
- URLs should be realistic (use real domain names of authoritative sites)
- Each source should add credibility or data
- Placement suggestions should be specific

Return ONLY the JSON object."""

        try:
            refs_data = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are a research expert who identifies authoritative sources for content credibility."
            )
            
            return [
                ExternalReference(
                    source_name=ref.get("source_name", ""),
                    url=ref.get("url", ""),
                    context=ref.get("context", ""),
                    placement_suggestion=ref.get("placement_suggestion", "")
                )
                for ref in refs_data.get("references", [])[:4]
            ]
            
        except Exception as e:
            print(f"⚠️  External reference generation failed: {e}, using fallback")
            return [
                ExternalReference(
                    source_name="Industry Research Report",
                    url=f"https://research.example.com/{topic.replace(' ', '-')}-report",
                    context=f"Statistics and trends in {topic}",
                    placement_suggestion="Cite in introduction to establish credibility"
                )
            ]
    
    def analyze_keywords(
        self, 
        article_content: str, 
        primary_keyword: str, 
        secondary_keywords: List[str]
    ) -> KeywordAnalysis:
        """Analyze keyword usage in the article"""
        
        content_lower = article_content.lower()
        primary_count = content_lower.count(primary_keyword.lower())
        total_words = len(article_content.split())
        
        # Calculate density as percentage
        density = (primary_count / total_words) * 100 if total_words > 0 else 0
        
        print(f"📊 Keyword Analysis:")
        print(f"   - Primary keyword '{primary_keyword}' appears {primary_count} times")
        print(f"   - Keyword density: {density:.2f}%")
        
        return KeywordAnalysis(
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            keyword_density=round(density, 2)
        )
