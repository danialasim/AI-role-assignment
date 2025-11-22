"""Outline Generator Agent - Transforms SERP Insights into Article Structure.

This agent is Step 3 in the pipeline. It takes the SERP analysis results and
creates a detailed article outline that:
- Covers topics that are already ranking well (competitive intelligence)
- Addresses content gaps identified in SERP analysis (differentiation)
- Distributes word count across sections for balanced coverage
- Creates SEO-friendly H1/H2/H3 hierarchy

The outline serves as a blueprint for the Content Generator (Step 4), ensuring
the final article is both comprehensive and strategically positioned to rank.

Outline Structure:
    - H1: Main title (55-65 chars with primary keyword)
    - Sections: 5-7 H2 sections (Introduction, 3-5 main sections, Conclusion)
    - H3s: 0-3 subsections under each H2 (not every section needs H3s)
    - Word counts: Distributed to hit target (e.g., 1500 words total)
    - Key points: 2-4 bullets per section guiding content generation

SERP-Driven Planning:
    The outline incorporates insights from SERP analysis:
    - Common topics from top 10 results (what's working)
    - Recommended H2 headings (proven structures)
    - Primary/secondary keywords (for natural incorporation)
    - Content gaps (unique angles for differentiation)
"""

from typing import Dict
from app.services.llm_service import LLMService

class OutlineGenerator:
    """Generates SEO-optimized article outlines based on SERP analysis.
    
    This agent bridges SERP research and content creation, transforming
    competitive intelligence into actionable content structure.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_outline(
        self, 
        serp_analysis: Dict, 
        topic: str, 
        target_word_count: int
    ) -> Dict:
        """Generate structured article outline based on competitive SERP analysis.
        
        This method constructs a detailed blueprint that balances:
        1. Competitive alignment (covering topics that rank)
        2. Differentiation (addressing gaps in existing content)
        3. SEO optimization (keyword placement, heading structure)
        4. Reader value (logical flow, comprehensive coverage)
        
        Args:
            serp_analysis: Results from SERP analyzer containing:
                - common_topics: What's covered in top 10 results
                - recommended_h2_headings: Proven section structures
                - primary_keyword: Main keyword to target
                - secondary_keywords: Related terms to incorporate
            topic: User's original search query/topic
            target_word_count: Desired article length (e.g., 1500)
        
        Returns:
            Dict with complete outline structure:
            {
                "h1": "Engaging title with keyword (55-65 chars)",
                "sections": [
                    {
                        "h2": "Section heading",
                        "h3s": ["Subsection 1", "Subsection 2"],
                        "word_count": 250,
                        "key_points": ["Point 1", "Point 2", "Point 3"]
                    },
                    ...
                ]
            }
        
        Raises:
            Exception: If LLM generation fails (fallback outline returned)
        
        Outline Requirements:
            - 5-7 total sections (intro, 3-5 main, conclusion)
            - H1: 55-65 characters with primary keyword
            - Word counts distributed to match target (±50 words)
            - Mix of sections with/without H3 subsections
            - Specific, actionable key points (not generic)
        """
        
        # Construct a detailed prompt that provides competitive context
        # and specific structural requirements for the outline
        prompt = f"""Create a detailed article outline for: "{topic}"

TARGET WORD COUNT: {target_word_count} words

COMPETITIVE INTELLIGENCE:
(What's working in top 10 Google results - use this to inform structure)
- Common topics in ranking articles: {', '.join(serp_analysis.get('common_topics', []))}
- Frequently covered subtopics: {', '.join(serp_analysis.get('subtopics', []))}
- Recommended H2 headings from top results: {', '.join(serp_analysis.get('recommended_h2_headings', []))}
- Primary keyword: {serp_analysis.get('primary_keyword', topic)}
- Secondary keywords: {', '.join(serp_analysis.get('secondary_keywords', []))}

Create an outline with the following structure (return as JSON):

{{
  "h1": "Compelling article title (55-65 characters, include primary keyword)",
  "sections": [
    {{
      "h2": "Section heading",
      "h3s": ["Subheading 1", "Subheading 2"],  // 0-3 H3s per section, can be empty array
      "word_count": 200,  // Approximate words for this section
      "key_points": ["Point 1", "Point 2", "Point 3"]  // 2-4 key points to cover
    }}
  ]
}}

REQUIREMENTS:
1. H1 should be engaging, include primary keyword, and be 55-65 characters
2. Start with an "Introduction" section (~200 words)
3. Include 4-6 main content sections (H2s)
4. End with a "Conclusion" section (~150 words)
5. Some sections should have 2-3 H3 subheadings, others can have none
6. Total word count across all sections should equal {target_word_count} (±50 words)
7. Key points should be specific and actionable
8. Cover topics from SERP analysis but with unique angle

Return ONLY the JSON object."""

        try:
            # Call LLM to generate structured outline as JSON
            # System prompt emphasizes SEO expertise and content strategy
            outline = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an expert content strategist who creates SEO-optimized article structures."
            )
            
            # Validate the outline structure and calculate totals
            section_count = len(outline.get('sections', []))
            total_wc = sum(s.get('word_count', 0) for s in outline.get('sections', []))
            
            # Log success with key metrics
            print(f"✅ Outline generated:")
            print(f"   - H1: {outline.get('h1', 'N/A')[:60]}...")
            print(f"   - {section_count} sections, ~{total_wc} total words")
            
            return outline
            
        except Exception as e:
            # If LLM generation fails, return a generic but valid outline
            # This ensures the pipeline never completely fails
            print(f"❌ Outline generation failed: {e}")
            print("   Using fallback outline template...")
            
            # Fallback outline uses topic to create basic structure
            # This is functional but less optimized than LLM-generated outline
            return {
                "h1": f"The Complete Guide to {topic.title()}",
                "sections": [
                    {
                        "h2": "Introduction",
                        "h3s": [],
                        "word_count": 200,
                        "key_points": [f"Define {topic}", "Explain importance", "Overview of article"]
                    },
                    {
                        "h2": f"Understanding {topic.title()}",
                        "h3s": ["Key Concepts", "Common Terminology"],
                        "word_count": 300,
                        "key_points": ["Explain fundamentals", "Provide context", "Share examples"]
                    },
                    {
                        "h2": f"Benefits of {topic.title()}",
                        "h3s": [],
                        "word_count": 250,
                        "key_points": ["List main benefits", "Provide evidence", "Share statistics"]
                    },
                    {
                        "h2": f"Best Practices for {topic.title()}",
                        "h3s": ["Getting Started", "Advanced Tips"],
                        "word_count": 400,
                        "key_points": ["Step-by-step guidance", "Expert recommendations", "Common pitfalls"]
                    },
                    {
                        "h2": "Conclusion",
                        "h3s": [],
                        "word_count": 150,
                        "key_points": ["Summarize key takeaways", "Encourage action", "Future outlook"]
                    }
                ]
            }
