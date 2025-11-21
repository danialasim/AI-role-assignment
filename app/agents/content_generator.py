from typing import Dict, List
from app.services.llm_service import LLMService
from app.models.response import ArticleContent, ArticleSection

class ContentGenerator:
    """Agent for generating article content"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_article(
        self, 
        outline: Dict, 
        serp_analysis: Dict
    ) -> ArticleContent:
        """
        Generate complete article content from outline
        
        Returns:
            ArticleContent with h1, sections, full_text, and word_count
        """
        
        h1 = outline.get("h1", "")
        sections_data = outline.get("sections", [])
        primary_keyword = serp_analysis.get("primary_keyword", "")
        secondary_keywords = serp_analysis.get("secondary_keywords", [])
        
        generated_sections = []
        full_text = f"# {h1}\n\n"
        total_words = 0
        
        print(f"🖊️  Generating article: '{h1}'")
        
        for idx, section in enumerate(sections_data, 1):
            h2 = section.get("h2", "")
            h3s = section.get("h3s", [])
            word_count_target = section.get("word_count", 300)
            key_points = section.get("key_points", [])
            
            print(f"   - Section {idx}/{len(sections_data)}: {h2} (~{word_count_target} words)")
            
            # Generate content for this section
            section_content = await self._generate_section_content(
                h1=h1,
                h2=h2,
                h3s=h3s,
                word_count=word_count_target,
                key_points=key_points,
                keywords=[primary_keyword] + secondary_keywords[:2]
            )
            
            # Create section object
            article_section = ArticleSection(
                heading=h2,
                heading_level=2,
                content=section_content,
                word_count=len(section_content.split())
            )
            
            generated_sections.append(article_section)
            full_text += f"## {h2}\n\n{section_content}\n\n"
            total_words += article_section.word_count
        
        print(f"✅ Article generated: {total_words} words total")
        
        return ArticleContent(
            h1=h1,
            sections=generated_sections,
            full_text=full_text,
            word_count=total_words
        )
    
    async def _generate_section_content(
        self, 
        h1: str, 
        h2: str, 
        h3s: List[str],
        word_count: int,
        key_points: List[str],
        keywords: List[str]
    ) -> str:
        """Generate content for a specific section"""
        
        h3_context = ""
        if h3s:
            h3_context = f"\n\nStructure the content with these H3 subheadings:\n" + "\n".join([f"- {h3}" for h3 in h3s])
        
        points_context = ""
        if key_points:
            points_context = f"\n\nKey points to cover:\n" + "\n".join([f"- {point}" for point in key_points])
        
        keywords_str = ", ".join(keywords[:3])
        
        prompt = f"""Write a {word_count}-word section for an SEO-optimized article.

ARTICLE CONTEXT:
Article Title: {h1}
Section Heading: {h2}{h3_context}{points_context}

KEYWORDS TO INCLUDE NATURALLY: {keywords_str}

WRITING REQUIREMENTS:
1. Write in a professional but conversational tone
2. Use short paragraphs (2-4 sentences each)
3. Include specific examples, data, or actionable tips when relevant
4. If H3 subheadings are provided, use them to structure the content (write "### H3 Title" before that subsection)
5. Make it sound human-written, not AI-generated:
   - Avoid phrases like "In conclusion", "It's important to note", "In today's digital age"
   - Use contractions naturally (you'll, we're, it's)
   - Vary sentence length and structure
   - Be specific rather than generic
6. Include transitional phrases between ideas
7. Target exactly {word_count} words (±20 words acceptable)

Write the section content now (do not repeat the H2 heading, start with the content):"""

        try:
            content = await self.llm_service.generate(
                prompt,
                system_prompt="You are an expert content writer who creates engaging, SEO-optimized articles that read naturally and provide real value to readers.",
                temperature=0.8  # Higher temperature for more creative, varied writing
            )
            
            return content.strip()
            
        except Exception as e:
            print(f"⚠️  Warning: Content generation failed for '{h2}': {e}")
            # Return placeholder content
            return f"""This section would cover {h2.lower()}. In a production environment, this content would be generated using the LLM service.

Key topics to explore include {', '.join(key_points[:2]) if key_points else 'relevant information'}.

The content would naturally incorporate keywords like {keywords[0] if keywords else 'relevant terms'} while maintaining readability and providing actionable insights for readers."""
