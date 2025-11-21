from typing import List, Dict
from app.models.response import SERPResult
from app.services.llm_service import LLMService

class SERPAnalyzer:
    """Agent for analyzing search engine results"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def analyze_serp_results(self, results: List[SERPResult], topic: str) -> Dict:
        """
        Extract themes, patterns, and insights from SERP results
        
        Returns:
            Dict with common_topics, subtopics, content_gaps, recommended_h2_headings,
            primary_keyword, and secondary_keywords
        """
        
        # Format SERP results for analysis
        serp_summary = "\n".join([
            f"{r.rank}. [{r.title}]\n   URL: {r.url}\n   Snippet: {r.snippet}\n"
            for r in results
        ])
        
        prompt = f"""Analyze these top 10 search results for the topic: "{topic}"

SEARCH RESULTS:
{serp_summary}

Based on these results, extract the following information and return as valid JSON:

1. "common_topics": Array of 4-6 main themes/topics covered across multiple articles
2. "subtopics": Array of 6-8 specific subtopics that appear frequently
3. "content_gaps": Array of 2-3 topics mentioned in only 1-2 articles that could differentiate our content
4. "recommended_h2_headings": Array of 5-7 H2 heading suggestions based on what's ranking well
5. "primary_keyword": The main keyword phrase to target (should be close to the original topic)
6. "secondary_keywords": Array of 4-6 related keywords to include naturally

Analysis guidelines:
- Focus on what's actually working in search results
- Identify patterns in successful content
- Look for both common themes and unique angles
- Keywords should be natural phrases, not stuffed

Return ONLY the JSON object, no additional text."""

        try:
            analysis = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an expert SEO analyst who identifies content patterns and keyword opportunities."
            )
            
            print(f"✅ SERP Analysis complete:")
            print(f"   - Primary keyword: {analysis.get('primary_keyword', 'N/A')}")
            print(f"   - {len(analysis.get('common_topics', []))} common topics identified")
            print(f"   - {len(analysis.get('recommended_h2_headings', []))} H2 suggestions")
            
            return analysis
            
        except Exception as e:
            print(f"❌ SERP analysis failed: {e}")
            # Return fallback analysis
            return {
                "common_topics": [f"Introduction to {topic}", f"Benefits of {topic}", f"Best practices for {topic}"],
                "subtopics": [f"{topic} fundamentals", f"Common challenges", f"Expert tips"],
                "content_gaps": [f"Future trends in {topic}"],
                "recommended_h2_headings": [
                    f"What is {topic}?",
                    f"Why {topic} Matters",
                    f"How to Get Started with {topic}",
                    f"Best {topic} Tools and Resources",
                    f"Common Mistakes to Avoid"
                ],
                "primary_keyword": topic,
                "secondary_keywords": [f"{topic} guide", f"{topic} tips", "best practices"]
            }
