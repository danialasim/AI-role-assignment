"""SEO Metadata Generator Agent - Creates Title Tags, Descriptions, and Link Strategies.

This agent handles Steps 5-8 in the pipeline, generating all SEO-critical metadata:

Step 5: SEO Metadata
    - Title tag: 50-60 characters with primary keyword
    - Meta description: Exactly 155 characters (SERP preview)
    - Focus keyword: Primary keyword for optimization

Step 6: Internal Links
    - 3-5 internal link suggestions with anchor text
    - Context for where/why to place each link
    - Helps with site structure and PageRank distribution

Step 7: External References
    - 2-4 authoritative external sources to cite
    - E-E-A-T signals (Expertise, Authoritativeness, Trustworthiness)
    - Real domains (harvard.edu, .gov, forbes.com, etc.)

Step 8: Keyword Analysis
    - Count primary keyword occurrences
    - Calculate keyword density (target: 1-2.5%)
    - Track secondary keyword usage

Why This Matters:
    - Title tag = First thing users see in Google results (CTR impact)
    - Meta description = Sales pitch in SERP (155 char limit hard cut-off)
    - Internal links = Site architecture and user navigation
    - External links = E-E-A-T signals and credibility
    - Keyword density = Relevance signal (but avoid stuffing)
"""

from typing import Dict, List
from app.services.llm_service import LLMService
from app.models.response import (
    SEOMetadata, KeywordAnalysis, InternalLink, ExternalReference
)

class SEOMetadataGenerator:
    """Generates all SEO-critical metadata and link strategies for articles.
    
    This is a multi-purpose agent handling 4 different generation tasks
    (metadata, internal links, external refs, keyword analysis).
    """
    
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
        """Calculate keyword density and distribution across the article.
        
        This is a non-LLM method - uses simple string counting and math.
        
        Keyword Density Formula:
            (Keyword Count / Total Words) × 100 = Density %
        
        Target Density:
            - 1-2.5%: Optimal (signals relevance without stuffing)
            - <1%: Under-optimized (might not rank well)
            - >3%: Over-optimized (keyword stuffing penalty risk)
        
        Args:
            article_content: Full article text
            primary_keyword: Main keyword phrase (e.g., "productivity tools")
            secondary_keywords: Related terms (e.g., ["remote work", "collaboration"])
        
        Returns:
            KeywordAnalysis with:
            - primary_keyword: The main keyword
            - secondary_keywords: List of related terms
            - keyword_density: Percentage (e.g., 1.8 for 1.8%)
        
        Example:
            Article: 1500 words, keyword appears 25 times
            Density: (25 / 1500) × 100 = 1.67%
            Result: Good! Within 1-2.5% target range
        """
        
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
