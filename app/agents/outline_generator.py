from typing import Dict
from app.services.llm_service import LLMService

class OutlineGenerator:
    """Agent for generating article outlines"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_outline(
        self, 
        serp_analysis: Dict, 
        topic: str, 
        target_word_count: int
    ) -> Dict:
        """
        Generate structured article outline based on SERP analysis
        
        Returns:
            Dict with h1, and sections array containing h2, h3s, word_count, key_points
        """
        
        prompt = f"""Create a detailed article outline for: "{topic}"

TARGET WORD COUNT: {target_word_count} words

COMPETITIVE INTELLIGENCE:
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
            outline = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an expert content strategist who creates SEO-optimized article structures."
            )
            
            # Validate and log
            section_count = len(outline.get('sections', []))
            total_wc = sum(s.get('word_count', 0) for s in outline.get('sections', []))
            
            print(f"✅ Outline generated:")
            print(f"   - H1: {outline.get('h1', 'N/A')[:60]}...")
            print(f"   - {section_count} sections, ~{total_wc} total words")
            
            return outline
            
        except Exception as e:
            print(f"❌ Outline generation failed: {e}")
            # Return fallback outline
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
