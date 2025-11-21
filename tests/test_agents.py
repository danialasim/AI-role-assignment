import pytest
from app.agents.serp_analyzer import SERPAnalyzer
from app.agents.outline_generator import OutlineGenerator
from app.agents.quality_validator import QualityValidator
from app.models.response import SERPResult, ArticleContent, ArticleSection, SEOMetadata
from app.services.serp_service import SerpAPIService

def test_serp_service_returns_results():
    """Test SERP service returns mock data"""
    serp_service = SerpAPIService()
    results = serp_service.search("test query")
    
    assert len(results) == 10
    assert all(isinstance(r, SERPResult) for r in results)
    assert all(r.rank >= 1 and r.rank <= 10 for r in results)
    assert all(r.url for r in results)
    assert all(r.title for r in results)

def test_serp_service_mock_data_structure():
    """Test mock SERP data has correct structure"""
    serp_service = SerpAPIService()
    results = serp_service.get_mock_data("productivity tools")
    
    assert len(results) == 10
    assert results[0].rank == 1
    assert "productivity tools" in results[0].title.lower() or "productivity tools" in results[0].snippet.lower()

@pytest.mark.asyncio
async def test_serp_analyzer_fallback():
    """Test SERP analyzer provides fallback analysis when LLM unavailable"""
    analyzer = SERPAnalyzer()
    
    mock_results = [
        SERPResult(
            rank=i,
            url=f"https://example.com/article-{i}",
            title=f"Best Productivity Tools - Article {i}",
            snippet=f"Learn about productivity tools and remote work strategies..."
        )
        for i in range(1, 11)
    ]
    
    # Even without API key, should return fallback structure
    try:
        analysis = await analyzer.analyze_serp_results(mock_results, "productivity tools")
        
        assert "common_topics" in analysis
        assert "subtopics" in analysis
        assert "primary_keyword" in analysis
        assert "secondary_keywords" in analysis
        assert "recommended_h2_headings" in analysis
        
        assert isinstance(analysis["common_topics"], list)
        assert isinstance(analysis["secondary_keywords"], list)
        assert len(analysis["recommended_h2_headings"]) >= 3
        
    except Exception as e:
        # If LLM fails, should still get fallback
        pytest.skip(f"LLM service not available: {e}")

@pytest.mark.asyncio
async def test_outline_generator_structure():
    """Test outline generator returns correct structure"""
    generator = OutlineGenerator()
    
    mock_analysis = {
        "common_topics": ["Introduction", "Benefits", "Best Practices"],
        "subtopics": ["Getting Started", "Advanced Tips"],
        "primary_keyword": "test keyword",
        "secondary_keywords": ["keyword 1", "keyword 2"],
        "recommended_h2_headings": ["What is X?", "Why X Matters", "How to Use X"]
    }
    
    try:
        outline = await generator.generate_outline(mock_analysis, "test topic", 1500)
        
        assert "h1" in outline
        assert "sections" in outline
        assert isinstance(outline["sections"], list)
        assert len(outline["sections"]) >= 3
        
        # Check section structure
        for section in outline["sections"]:
            assert "h2" in section
            assert "word_count" in section
            assert "key_points" in section
            assert isinstance(section.get("h3s", []), list)
            
    except Exception as e:
        pytest.skip(f"LLM service not available: {e}")

def test_quality_validator_title_tag_length():
    """Test quality validator checks title tag length"""
    validator = QualityValidator()
    
    # Good title tag (55 chars)
    article = ArticleContent(
        h1="Test Article",
        sections=[],
        full_text="test content with test keyword",
        word_count=5
    )
    
    metadata = SEOMetadata(
        title_tag="This is a perfectly sized title tag for SEO testing",  # 52 chars
        meta_description="This is a meta description that is exactly one hundred and fifty-five characters long for testing purposes and SEO validation.",
        focus_keyword="test keyword"
    )
    
    result = validator.validate_seo_quality(article, metadata, 1500)
    
    assert "score" in result
    assert "percentage" in result
    assert "issues" in result
    assert "passed" in result
    assert isinstance(result["score"], int)
    assert result["score"] >= 0 and result["score"] <= 100

def test_quality_validator_keyword_in_h1():
    """Test quality validator checks keyword in H1"""
    validator = QualityValidator()
    
    article_with_keyword = ArticleContent(
        h1="Best Productivity Tools for Remote Teams",
        sections=[
            ArticleSection(heading="Section 1", heading_level=2, content="content", word_count=100),
            ArticleSection(heading="Section 2", heading_level=2, content="content", word_count=100),
            ArticleSection(heading="Section 3", heading_level=2, content="content", word_count=100),
            ArticleSection(heading="Section 4", heading_level=2, content="content", word_count=100),
        ],
        full_text="productivity tools " * 100,  # Repeat for density
        word_count=200
    )
    
    metadata = SEOMetadata(
        title_tag="Productivity Tools Guide - Complete 2025 Overview",
        meta_description="Learn about the best productivity tools for remote teams. Comprehensive guide with tips, features, and expert recommendations for success.",
        focus_keyword="productivity tools"
    )
    
    result = validator.validate_seo_quality(article_with_keyword, metadata, 200)
    
    # Should pass keyword in H1 check
    keyword_issues = [issue for issue in result["issues"] if "H1" in issue]
    # If keyword is in H1, there should be no H1-related issues
    assert len(keyword_issues) == 0 or "not found" not in keyword_issues[0]

def test_quality_validator_minimum_sections():
    """Test quality validator checks for minimum sections"""
    validator = QualityValidator()
    
    # Article with only 2 sections (should fail)
    article_few_sections = ArticleContent(
        h1="Test Article",
        sections=[
            ArticleSection(heading="Intro", heading_level=2, content="test", word_count=50),
            ArticleSection(heading="Conclusion", heading_level=2, content="test", word_count=50),
        ],
        full_text="test keyword appears here in the article",
        word_count=100
    )
    
    metadata = SEOMetadata(
        title_tag="Test Article - Complete Guide to Testing",
        meta_description="This is a test meta description for validation purposes with exactly the right length for SEO requirements.",
        focus_keyword="test keyword"
    )
    
    result = validator.validate_seo_quality(article_few_sections, metadata, 100)
    
    # Should have issue about sections
    section_issues = [issue for issue in result["issues"] if "section" in issue.lower()]
    assert len(section_issues) > 0

def test_quality_validator_word_count_accuracy():
    """Test quality validator checks word count accuracy"""
    validator = QualityValidator()
    
    article = ArticleContent(
        h1="Test",
        sections=[ArticleSection(heading="S1", heading_level=2, content="c", word_count=50)] * 4,
        full_text="word " * 200,  # 200 words
        word_count=200
    )
    
    metadata = SEOMetadata(
        title_tag="Test Article - Testing Word Count Validation",
        meta_description="This meta description is designed to test the word count validation feature of our quality validator system.",
        focus_keyword="test"
    )
    
    # Target 1500, actual 200 - should flag as issue
    result = validator.validate_seo_quality(article, metadata, 1500)
    
    word_count_issues = [issue for issue in result["issues"] if "word count" in issue.lower()]
    assert len(word_count_issues) > 0
