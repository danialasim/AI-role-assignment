import requests
from typing import List
from app.models.response import SERPResult
from app.config import get_settings

class SerpAPIService:
    """Service for fetching search engine results"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.serpapi_key
        self.base_url = "https://serpapi.com/search"
    
    def search(self, query: str, num_results: int = 10) -> List[SERPResult]:
        """Fetch top search results for a query"""
        
        # Use mock data if no API key or in development
        if not self.api_key or self.settings.environment == "development":
            print(f"📝 Using mock SERP data for query: '{query}'")
            return self.get_mock_data(query)
        
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for i, item in enumerate(data.get("organic_results", [])[:num_results]):
                results.append(SERPResult(
                    rank=i + 1,
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", "")
                ))
            
            print(f"✅ Fetched {len(results)} real SERP results")
            return results
            
        except Exception as e:
            print(f"⚠️  SERP API Error: {e}. Falling back to mock data.")
            return self.get_mock_data(query)
    
    def get_mock_data(self, query: str) -> List[SERPResult]:
        """Return realistic mock SERP data for testing"""
        
        base_results = [
            SERPResult(
                rank=1,
                url="https://example.com/comprehensive-guide",
                title=f"The Complete Guide to {query.title()} in 2025",
                snippet=f"Discover everything you need to know about {query}. Our comprehensive guide covers best practices, expert tips, and proven strategies that work."
            ),
            SERPResult(
                rank=2,
                url="https://techblog.com/best-practices",
                title=f"15 Best {query.title()} Strategies for Success",
                snippet=f"Learn the top strategies for {query}. Industry experts share their insights, case studies, and actionable recommendations."
            ),
            SERPResult(
                rank=3,
                url="https://industry-leader.com/ultimate-guide",
                title=f"Ultimate {query.title()} Guide for Beginners",
                snippet=f"Start your journey with {query}. Step-by-step tutorials, tools, and resources to help you get started quickly and effectively."
            ),
            SERPResult(
                rank=4,
                url="https://expert-reviews.com/comparison",
                title=f"Top 10 {query.title()} Tools Compared",
                snippet=f"We tested and compared the leading {query} solutions. See detailed reviews, pricing, features, and our expert recommendations."
            ),
            SERPResult(
                rank=5,
                url="https://business-insider.com/trends",
                title=f"{query.title()} Trends to Watch in 2025",
                snippet=f"Stay ahead with the latest {query} trends. Market analysis, expert predictions, and emerging technologies shaping the industry."
            ),
            SERPResult(
                rank=6,
                url="https://professional-blog.com/how-to",
                title=f"How to Implement {query.title()} Successfully",
                snippet=f"A practical guide to implementing {query}. Real-world examples, common pitfalls to avoid, and proven implementation strategies."
            ),
            SERPResult(
                rank=7,
                url="https://authority-site.com/advanced",
                title=f"Advanced {query.title()} Techniques",
                snippet=f"Take your {query} skills to the next level. Advanced techniques, optimization strategies, and expert-level insights."
            ),
            SERPResult(
                rank=8,
                url="https://case-studies.com/success-stories",
                title=f"{query.title()} Success Stories and Case Studies",
                snippet=f"Learn from real success stories. Companies share how they used {query} to achieve remarkable results and ROI."
            ),
            SERPResult(
                rank=9,
                url="https://research-institute.com/report",
                title=f"2025 {query.title()} Research Report",
                snippet=f"Comprehensive research on {query}. Data-driven insights, statistics, and analysis from leading industry researchers."
            ),
            SERPResult(
                rank=10,
                url="https://community-forum.com/discussion",
                title=f"{query.title()} Community Discussion and Tips",
                snippet=f"Join the discussion about {query}. Community members share tips, answer questions, and provide peer support."
            ),
        ]
        
        return base_results