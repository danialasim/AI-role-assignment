"""SERP Analyzer Agent - Extracts Competitive Intelligence from Search Results.

This agent is Step 2 in the pipeline. It analyzes the top 10 Google search results
to understand:
- What topics are currently ranking well (common themes)
- What content structure works (H2 heading patterns)
- What keywords Google associates with the topic
- What gaps exist in current content (differentiation opportunities)

This competitive intelligence drives the entire content strategy:
- Outline Generator uses it to structure the article
- Content Generator uses it to focus on relevant topics
- SEO Generator uses it for keyword targeting

SERP Analysis Outputs:
    - common_topics: 4-6 main themes across top results
    - subtopics: 6-8 specific sub-themes that appear frequently
    - content_gaps: 2-3 topics mentioned rarely (unique angle opportunity)
    - recommended_h2_headings: 5-7 proven section structures
    - primary_keyword: Main target keyword (often = topic)
    - secondary_keywords: 4-6 related terms for natural incorporation

Why SERP Analysis Matters:
    Google has already told us what it considers relevant by ranking these
    pages. By analyzing patterns in top results, we create content that:
    - Covers topics Google expects to see (relevance)
    - Uses proven structures (user intent alignment)
    - Includes gaps for differentiation (competitive advantage)
"""

from typing import List, Dict
from app.models.response import SERPResult
from app.services.llm_service import LLMService

class SERPAnalyzer:
    """Analyzes search engine results to extract competitive intelligence.
    
    Transforms raw SERP data into actionable insights for content strategy.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def analyze_serp_results(self, results: List[SERPResult], topic: str) -> Dict:
        """Extract themes, patterns, and keyword opportunities from SERP results.
        
        This method uses Claude to identify patterns across the top 10 search results,
        answering key questions:
        - What topics do high-ranking articles cover?
        - What content structure (headings) works well?
        - What keywords is Google associating with this topic?
        - Where are the gaps we can fill for differentiation?
        
        Args:
            results: List of 10 SERPResult objects from SERP service containing:
                - rank: Position (1-10)
                - url: Result URL
                - title: Page title (60 chars, keyword-optimized)
                - snippet: Meta description preview (160 chars)
            topic: Original user query (e.g., "best productivity tools for remote work")
        
        Returns:
            Dict with competitive intelligence:
            {
                "common_topics": ["Remote work tools", "Team collaboration", ...],
                "subtopics": ["Video conferencing", "Project management", ...],
                "content_gaps": ["ROI analysis", "Security considerations"],
                "recommended_h2_headings": ["What is X?", "Benefits of X", ...],
                "primary_keyword": "best productivity tools for remote work",
                "secondary_keywords": ["remote collaboration", "team tools", ...]
            }
        
        Raises:
            Exception: If LLM analysis fails (returns fallback analysis)
        
        Analysis Strategy:
            1. Format SERP data for LLM (rank, title, snippet per result)
            2. Ask LLM to identify patterns across all 10 results
            3. Extract both common themes (what's working) and gaps (opportunities)
            4. Return structured insights for downstream agents
        """
        
        # Format SERP results into readable text for LLM analysis
        # Each result shows: rank, title, URL, snippet (meta description)
        # This gives Claude full context about what's ranking
        serp_summary = "\n".join([
            f"{r.rank}. [{r.title}]\n   URL: {r.url}\n   Snippet: {r.snippet}\n"
            for r in results
        ])
        
        # Construct analysis prompt with clear instructions for pattern extraction
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
            # Call LLM to analyze patterns across all SERP results
            # System prompt emphasizes SEO and competitive analysis expertise
            analysis = await self.llm_service.generate_json(
                prompt,
                system_prompt="You are an expert SEO analyst who identifies content patterns and keyword opportunities."
            )
            
            # Log key insights from analysis
            print(f"✅ SERP Analysis complete:")
            print(f"   - Primary keyword: {analysis.get('primary_keyword', 'N/A')}")
            print(f"   - {len(analysis.get('common_topics', []))} common topics identified")
            print(f"   - {len(analysis.get('recommended_h2_headings', []))} H2 suggestions")
            
            return analysis
            
        except Exception as e:
            # If LLM analysis fails, return basic fallback analysis
            # Uses topic to generate minimal but functional insights
            print(f"❌ SERP analysis failed: {e}")
            print("   Using fallback analysis based on topic...")
            
            # Fallback creates generic but valid analysis structure
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
