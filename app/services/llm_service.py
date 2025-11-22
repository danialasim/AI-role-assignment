"""LLM Service - Claude Sonnet 4 Integration with Mock Mode.

This module provides a unified interface for interacting with Anthropic's Claude API,
with intelligent mock mode for development and testing without consuming API credits.

Key Features:
    - Dual mode operation (real API vs mock responses)
    - Structured JSON output with retry logic
    - Exponential backoff for rate limiting
    - Type-safe responses with validation
    - Realistic mock data for testing

Mock Mode Benefits:
    - Zero API costs during development
    - Instant responses (no network latency)
    - Predictable outputs for testing
    - Work offline without API keys
    - Generated 16 real articles with mock mode

Usage:
    llm = LLMService()
    text = await llm.generate("Write an intro about productivity tools")
    data = await llm.generate_json("Return top 3 tools as JSON array")
"""

from anthropic import Anthropic, APIError
from typing import Optional, Dict
from app.config import get_settings
import json
import time
import os

class LLMService:
    """Service for LLM interactions using Claude Sonnet 4.
    
    Supports both real API calls (using ANTHROPIC_API_KEY) and mock mode
    (using hard-coded responses) for development and testing.
    """
    
    def __init__(self):
        """Initialize the LLM service in either mock or real API mode.
        
        Configuration is loaded from .env file via get_settings():
            MOCK_LLM=true  → Use mock responses (free, instant, offline)
            MOCK_LLM=false → Use real Claude API (requires ANTHROPIC_API_KEY)
        
        The service gracefully handles missing API keys by marking itself
        as unavailable, allowing the application to detect the issue at
        runtime with a clear error message.
        """
        settings = get_settings()
        self.mock_mode = settings.mock_llm
        
        if self.mock_mode:
            # Mock mode: No API key needed, instant responses
            print("🎭 Running in MOCK MODE - using simulated LLM responses")
            self.available = True
        else:
            # Real API mode: Requires valid Anthropic API key
            try:
                self.client = Anthropic(api_key=settings.anthropic_api_key)
                # Model: claude-sonnet-4-20250514 (~$3 per million tokens)
                # Chosen for balance of speed, quality, and cost
                self.model = "claude-sonnet-4-20250514"
                self.available = True
            except Exception as e:
                print(f"⚠️  Warning: Anthropic API key not configured. LLM service unavailable.")
                print(f"   Error: {e}")
                self.available = False
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = "You are an expert SEO content writer who creates engaging, human-like content.",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Generate free-form text content using Claude (or mock response).
        
        This is the primary method for content generation - used by all agents
        to create article sections, outlines, and analysis text.
        
        Args:
            prompt: The user's request/instruction to Claude
            system_prompt: Defines Claude's role and behavior (default: SEO writer)
            temperature: Randomness (0.0 = deterministic, 1.0 = creative). 
                        0.7 balances consistency with natural variation
            max_tokens: Maximum response length (4096 = ~3000 words)
        
        Returns:
            Generated text as a string
        
        Raises:
            Exception: If LLM service not available (missing API key)
            APIError: If Claude API returns an error
        
        Cost (Real Mode):
            ~$0.003 per generation at 1000 tokens output
            Full article generation: ~$0.15 (50k tokens total)
        """
        
        # Fail fast if API key missing in real mode
        if not self.available:
            raise Exception("LLM service not available. Please add ANTHROPIC_API_KEY to .env file.")
        
        # Mock mode: Return pre-written content instantly (no API call)
        # This allows full system testing without API costs
        if self.mock_mode:
            return self._generate_mock_response(prompt)
        
        # Real API mode: Call Claude Sonnet 4
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,  # Shapes Claude's personality/expertise
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract text from response (Claude returns structured format)
            return response.content[0].text
            
        except APIError as e:
            print(f"❌ Anthropic API Error: {e}")
            raise
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            raise
    
    async def generate_json(
        self, 
        prompt: str, 
        system_prompt: str = "You are a helpful assistant that outputs valid JSON.",
        max_retries: int = 3
    ) -> Dict:
        """Generate structured JSON output with automatic retry on parse errors.
        
        LLMs sometimes return markdown code blocks or invalid JSON even when
        instructed otherwise. This method handles those cases automatically:
        1. Adds explicit JSON-only instruction to prompt
        2. Strips markdown code blocks (```json ...```)
        3. Retries up to 3 times if parsing fails
        4. Returns parsed dict ready for use
        
        Args:
            prompt: Request for structured data (e.g., "Return outline as JSON")
            system_prompt: Role definition (default: JSON-focused assistant)
            max_retries: Number of retry attempts on JSON parse errors
        
        Returns:
            Parsed dictionary/list from JSON response
        
        Raises:
            json.JSONDecodeError: If all retry attempts fail to produce valid JSON
            Exception: If LLM service unavailable or API error
        
        Used For:
            - SERP analysis results (topics, keywords, headings)
            - Article outlines (sections with h2/h3 structure)
            - SEO metadata (title, description, slug)
            - Internal links and external references
        """
        
        if not self.available:
            raise Exception("LLM service not available. Please add ANTHROPIC_API_KEY to .env file.")
        
        # Mock mode - return simulated JSON
        if self.mock_mode:
            return self._generate_mock_json(prompt)
        
        # Enhance prompt with explicit JSON-only instruction
        # Even with system prompt, LLMs sometimes add markdown formatting
        enhanced_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, just pure JSON."
        
        # Retry loop: Try up to 3 times to get valid JSON
        for attempt in range(max_retries):
            try:
                # Generate text response
                response = await self.generate(
                    enhanced_prompt,
                    system_prompt=system_prompt,
                    temperature=0.7
                )
                
                # Clean response - remove markdown code blocks if present
                # Claude sometimes returns: ```json\n{...}\n```
                # We need to extract just the {...} part
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]  # Remove "```json"
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]   # Remove "```"
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]  # Remove trailing "```"
                cleaned = cleaned.strip()
                
                # Parse JSON - this will raise JSONDecodeError if invalid
                return json.loads(cleaned)
                
            except json.JSONDecodeError as e:
                # JSON parsing failed - retry if we have attempts remaining
                if attempt < max_retries - 1:
                    print(f"⚠️  JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"   Response preview: {response[:200]}...")
                    time.sleep(1)  # Brief pause before retry
                else:
                    # All retries exhausted - fail with detailed error
                    print(f"❌ Failed to parse JSON after {max_retries} attempts")
                    print(f"   Last response: {response[:500]}")
                    raise
            except Exception as e:
                print(f"❌ Error generating JSON: {e}")
                raise
    
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: str = "You are an expert SEO content writer.",
        max_retries: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Generate with exponential backoff retry logic.
        
        Args:
            prompt: User's request/instruction
            system_prompt: Claude's role definition
            max_retries: Number of retry attempts on failure
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum response length (4096 default, 8000 for long articles)
        
        Returns:
            Generated text
        """
        
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, system_prompt, temperature, max_tokens)
            except APIError as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⏳ Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception("Max retries exceeded")
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate realistic mock text responses for development/testing.
        
        This method analyzes the prompt to determine what type of content
        is being requested, then returns pre-written, high-quality content
        that matches that type. This enables full end-to-end testing without
        API costs.
        
        Content Types Detected:
            - Introduction sections ("introduction", "intro")
            - Understanding/What-is sections ("understanding", "what is")
            - Benefits sections ("benefit", "advantage")
            - Best practices sections ("best practice", "how to", "tips")
            - Conclusions ("conclusion", "summary")
            - Generic fallback for other requests
        
        Each mock response is:
            - 200-500 words (realistic length)
            - SEO-optimized with keyword usage
            - Well-structured with clear paragraphs
            - Human-like tone and readability
        
        Args:
            prompt: The generation request (analyzed for keywords)
        
        Returns:
            Pre-written content matching the detected section type
        
        Note:
            These responses are carefully crafted to produce complete,
            publishable articles when combined. The 16 articles in the
            database were generated using these mock responses.
        """
        
        # Detect what type of content is being requested
        prompt_lower = prompt.lower()
        
        if "introduction" in prompt_lower or "intro" in prompt_lower:
            return """In today's digital landscape, understanding the best productivity tools for remote work has become essential for professionals and businesses alike. The shift to remote work has accelerated dramatically over recent years, transforming how organizations operate and how teams collaborate across distributed environments.

Remote work productivity tools represent a fundamental shift in workplace dynamics, enabling seamless communication, efficient task management, and enhanced collaboration regardless of physical location. These technological solutions have evolved from simple communication platforms into comprehensive ecosystems that support every aspect of remote work operations.

This comprehensive guide explores the most effective productivity solutions available in today's market, examining their features, benefits, implementation strategies, and real-world applications. We'll dive deep into various categories of tools—from project management platforms and communication hubs to time tracking applications and collaboration software.

Whether you're a remote worker seeking to optimize your personal workflow, a team leader looking to enhance collaboration among distributed team members, or a business executive evaluating enterprise-wide productivity solutions, this article provides actionable insights into selecting and utilizing the right productivity tools for your specific needs. By understanding the landscape of available tools and implementing them strategically, you can unlock new levels of efficiency and effectiveness in your remote work environment."""
        
        elif "understanding" in prompt_lower or "what is" in prompt_lower:
            return """The best productivity tools for remote work encompass a diverse and sophisticated ecosystem of software solutions specifically designed to facilitate seamless collaboration, efficient task management, and effective communication in distributed work environments. These platforms have revolutionized how teams operate, enabling productivity levels that often exceed traditional office settings.

At the foundation level, we find project management systems like Asana, Trello, Monday.com, and Jira. These platforms provide visual task tracking, deadline management, and workflow automation that keeps teams aligned on priorities and progress. They transform abstract goals into concrete, trackable action items that team members can execute independently.

Communication hubs such as Slack, Microsoft Teams, and Discord represent another critical category. These tools replace fragmented email chains with organized channels, direct messaging, and integrations that centralize team communication. They enable both real-time conversations and asynchronous updates, supporting different working styles and time zones.

Video conferencing solutions including Zoom, Google Meet, and Microsoft Teams have become indispensable for face-to-face interactions. These platforms support everything from quick check-ins to large-scale presentations, incorporating features like screen sharing, breakout rooms, and recording capabilities that enhance virtual meetings.

Cloud storage and collaboration tools like Google Workspace, Microsoft 365, and Dropbox enable teams to create, share, and collaboratively edit documents in real time. Version control and permission management ensure data security while maintaining accessibility.

Time tracking applications such as Toggl, Harvest, and RescueTime help remote workers maintain accountability and analyze productivity patterns. These insights enable better time management and resource allocation across projects.

The evolution of these productivity tools for remote work reflects rapidly changing workplace dynamics. Modern platforms increasingly integrate multiple functionalities, offering unified experiences that reduce context switching and improve workflow efficiency. Features like real-time collaboration, automated workflows, intelligent notifications, and AI-powered insights have transitioned from innovative additions to standard expectations.

Understanding this landscape requires recognizing that different tools serve distinct purposes and excel in specific scenarios. Some platforms optimize synchronous communication for teams working simultaneously, while others enhance asynchronous collaboration for globally distributed teams. The key lies in selecting combinations that complement your team's specific workflow patterns, communication preferences, and operational requirements."""
        
        elif "benefit" in prompt_lower or "advantage" in prompt_lower:
            return """Implementing the best productivity tools for remote work delivers tangible benefits that extend far beyond basic communication improvements. These advantages impact individual productivity, team collaboration, organizational efficiency, and bottom-line business results.

Enhanced collaboration and teamwork stands as the primary advantage. Teams utilizing comprehensive productivity tool suites experience up to 25% increases in project completion rates and 30% improvements in meeting deadlines. These tools break down geographical barriers, enabling seamless interaction regardless of physical location or time zone differences. Real-time document collaboration eliminates version control confusion, while integrated communication channels ensure everyone stays informed and aligned on project objectives.

Time management improvements constitute another significant benefit of productivity tools for remote work. Automated task tracking, intelligent scheduling, and workflow automation reduce administrative overhead by approximately 30%, allowing professionals to redirect their energy toward high-value strategic activities. Calendar integrations prevent scheduling conflicts, while automated reminders ensure nothing falls through the cracks. Real-time visibility into project progress enhances accountability across teams and enables proactive problem-solving before minor issues escalate into major obstacles.

Cost efficiency represents a compelling advantage for organizations of all sizes. Beyond eliminating expenses associated with physical office infrastructure—real estate, utilities, commuting subsidies—remote work tools often provide more affordable alternatives to traditional enterprise software. Subscription-based pricing models offer scalability without large upfront investments, while cloud-based solutions eliminate IT infrastructure costs. Organizations report average savings of 15-20% on operational expenses after transitioning to remote-first workflows supported by productivity tools.

Employee satisfaction and work-life balance improvements contribute to better retention and recruitment outcomes. Remote workers report 40% higher job satisfaction when equipped with effective productivity tools that enable flexible scheduling and autonomous work management. This flexibility reduces burnout, improves mental health, and creates more sustainable work patterns. Higher employee retention translates directly to reduced recruitment and training costs.

Data-driven insights provided by modern productivity platforms enable continuous process optimization and informed strategic decision-making. Analytics dashboards reveal productivity patterns, bottleneck identification, and resource allocation opportunities that might otherwise remain invisible. Organizations can measure what matters, iterate on processes, and drive measurable improvements in efficiency and output quality."""
        
        elif "best practice" in prompt_lower or "how to" in prompt_lower or "tips" in prompt_lower:
            return """Successfully implementing the best productivity tools for remote work requires strategic planning, thoughtful execution, and ongoing optimization. Following proven best practices dramatically increases adoption rates and maximizes return on investment.

Start with comprehensive needs assessment before selecting any tools. Conduct surveys and interviews with team members to identify specific pain points, workflow bottlenecks, and collaboration challenges. Map existing processes to understand where inefficiencies occur and which activities consume disproportionate time. This foundation ensures tool selection aligns with actual operational requirements rather than perceived needs or trendy solutions that may not fit your context.

Develop clear selection criteria that balance functionality, usability, cost, security, and scalability. Create weighted scorecards evaluating potential tools against your specific requirements. Consider factors like learning curve, mobile accessibility, integration capabilities, vendor stability, and data privacy compliance. Involve end users in evaluation processes through pilot programs that test tools with real workflows before organization-wide rollout.

Integration planning and ecosystem design prove critical for long-term success. The best productivity tools for remote work should seamlessly connect with existing systems, minimizing data silos and reducing manual data entry that wastes time and introduces errors. Prioritize platforms offering robust API capabilities, native integrations with your current technology stack, and automation possibilities through tools like Zapier or Make. Map out your ideal workflow showing how different tools connect and where data flows between systems.

Establish clear communication protocols and usage guidelines defining when and how to use each tool. Create a communication matrix specifying which channels to use for different message types—for example, using email for formal documentation and decisions requiring paper trails, Slack for quick questions and updates, project management tools for task-related discussions, and video calls for complex conversations requiring nuance. This clarity prevents communication fragmentation and ensures messages reach intended audiences through appropriate channels.

Training and onboarding represent often-overlooked success factors that make or break adoption. Develop comprehensive training programs addressing varying technical proficiency levels within your team. Create layered documentation including video tutorials for visual learners, written step-by-step guides for reference, and quick-reference sheets for common tasks. Designate tool champions within each team who receive advanced training and serve as first-line support for colleagues. Implement gradual rollouts rather than wholesale changes, allowing teams to build competency progressively and adapt workflows without overwhelming disruption.

Foster a culture of continuous learning and experimentation. Encourage team members to explore advanced features, share productivity tips, and suggest workflow improvements. Create dedicated channels for tool-related questions and best practice sharing. Recognize and celebrate team members who effectively leverage tools to achieve impressive results.

Establish governance structures and best practices for tool usage. Define naming conventions for files and channels, folder structures for document organization, and tagging systems for task categorization. Create templates for common workflows and document types to ensure consistency. Set retention policies for messages and files to manage data volume while maintaining compliance.

Regular evaluation and optimization ensure continued effectiveness and prevent tool sprawl. Schedule quarterly reviews assessing tool utilization metrics, gathering user feedback through surveys and focus groups, and identifying improvement opportunities or redundancies. Monitor key performance indicators like response times, task completion rates, user adoption levels, and productivity metrics. Conduct annual audits identifying underutilized subscriptions that waste budget and consolidation opportunities where multiple tools serve overlapping purposes.

Remain flexible and willing to adjust tool selections as team needs evolve, organizational priorities shift, and new solutions emerge in the rapidly advancing productivity software market. Recognize that optimal configurations change over time—tools that served you well at 20 employees may not scale to 200. Stay informed about emerging features in tools you currently use and new platforms entering the market that might better serve evolving requirements."""
        
        elif "conclusion" in prompt_lower or "summary" in prompt_lower:
            return """The strategic selection and implementation of the best productivity tools for remote work fundamentally shapes organizational success in today's distributed work environment. This comprehensive exploration has revealed how thoughtfully chosen and properly implemented tools drive collaboration, enhance efficiency, reduce costs, and improve employee satisfaction.

Organizations that invest adequate time in understanding their specific operational needs, carefully evaluating available solutions, and supporting effective adoption through training and change management position themselves for sustained competitive advantage. The productivity tool landscape continues evolving at a rapid pace, with artificial intelligence, machine learning, and advanced automation playing increasingly central roles in next-generation platforms.

Remember that tools themselves represent enablers rather than solutions. Success requires combining appropriate technology with clear processes, effective communication practices, and supportive organizational culture. Start with your most pressing pain points, implement solutions incrementally, measure results continuously, and iterate based on feedback and data.

As you move forward with selecting and implementing the best productivity tools for remote work in your organization, maintain focus on core productivity principles—clear goals, effective communication, accountability, and continuous improvement—while leveraging technology to amplify these fundamentals. The future of work is remote, and those who master the tools and practices enabling distributed collaboration will thrive in this new landscape."""
        
        else:
            # Generic content
            return f"""This section provides valuable insights into the topic at hand, offering practical guidance and expert perspectives. Through careful analysis and real-world examples, we explore key considerations that matter most to professionals and organizations. The information presented here draws from industry best practices and proven methodologies, ensuring relevance and applicability to diverse contexts. Understanding these principles enables more informed decision-making and effective strategy implementation."""
    
    def _generate_mock_json(self, prompt: str) -> Dict:
        """Generate mock JSON responses for testing"""
        
        prompt_lower = prompt.lower()
        
        # SERP Analysis
        if "analyze" in prompt_lower and "serp" in prompt_lower:
            return {
                "common_topics": [
                    "Remote work communication tools",
                    "Project management platforms",
                    "Time tracking and productivity monitoring",
                    "Video conferencing solutions",
                    "Document collaboration tools"
                ],
                "common_subtopics": [
                    "Slack vs Microsoft Teams comparison",
                    "Asana and Trello features",
                    "Zoom and Google Meet capabilities",
                    "Cloud storage solutions",
                    "Automation and workflow integration"
                ],
                "content_gaps": [
                    "Detailed ROI analysis of productivity tools",
                    "Integration strategies for mixed tool environments",
                    "Security considerations for remote tools",
                    "Mobile app functionality comparison"
                ],
                "recommended_h2_headings": [
                    "Essential Categories of Remote Work Tools",
                    "Top Communication Platforms Compared",
                    "Project Management Solutions Overview",
                    "Time Tracking and Productivity Apps",
                    "Integration and Automation Strategies",
                    "Security and Compliance Considerations"
                ],
                "primary_keywords": ["productivity tools", "remote work", "collaboration software"],
                "secondary_keywords": ["project management", "team communication", "time tracking", "video conferencing", "workflow automation"]
            }
        
        # Outline Generation
        elif "outline" in prompt_lower or "structure" in prompt_lower:
            return {
                "h1": "The Complete Guide to Best Productivity Tools for Remote Work",
                "sections": [
                    {
                        "h2": "Introduction to Remote Work Productivity Tools",
                        "h3s": ["Why Productivity Tools Matter", "Evolution of Remote Work Software"],
                        "word_count": 200,
                        "key_points": [
                            "Importance of productivity tools in modern remote work",
                            "Overview of tool categories",
                            "Article roadmap"
                        ]
                    },
                    {
                        "h2": "Understanding Remote Work Productivity Tools",
                        "h3s": ["Tool Categories and Use Cases", "Integration Ecosystem"],
                        "word_count": 300,
                        "key_points": [
                            "Different types of productivity tools",
                            "How tools work together",
                            "Key features to look for"
                        ]
                    },
                    {
                        "h2": "Benefits of Using Productivity Tools",
                        "h3s": ["Collaboration Improvements", "Time Management Gains", "Cost Efficiency"],
                        "word_count": 250,
                        "key_points": [
                            "Enhanced team collaboration",
                            "Better time management",
                            "ROI and cost savings"
                        ]
                    },
                    {
                        "h2": "Best Practices for Implementation",
                        "h3s": ["Needs Assessment", "Integration Strategy", "Training and Adoption", "Continuous Optimization"],
                        "word_count": 400,
                        "key_points": [
                            "How to choose the right tools",
                            "Implementation strategies",
                            "Training best practices",
                            "Measuring success"
                        ]
                    },
                    {
                        "h2": "Conclusion and Next Steps",
                        "h3s": ["Key Takeaways", "Getting Started"],
                        "word_count": 150,
                        "key_points": [
                            "Summary of main points",
                            "Action steps for readers"
                        ]
                    }
                ]
            }
        
        # SEO Metadata
        elif "seo" in prompt_lower and ("metadata" in prompt_lower or "title" in prompt_lower or "description" in prompt_lower):
            return {
                "title_tag": "Best Productivity Tools for Remote Work: Complete 2024 Guide",
                "meta_description": "Discover the top productivity tools for remote work. Compare features, benefits, and implementation strategies to boost team collaboration and efficiency.",
                "slug": "best-productivity-tools-remote-work"
            }
        
        # Internal Links
        elif "internal link" in prompt_lower:
            return {
                "links": [
                    {
                        "anchor_text": "remote work communication strategies",
                        "url": "/blog/remote-work-communication-strategies",
                        "relevance": "Complements productivity tools discussion with communication best practices"
                    },
                    {
                        "anchor_text": "project management methodologies",
                        "url": "/blog/project-management-methodologies",
                        "relevance": "Explains frameworks that work well with productivity tools"
                    },
                    {
                        "anchor_text": "building effective remote teams",
                        "url": "/blog/building-remote-teams",
                        "relevance": "Covers team dynamics and culture in remote environments"
                    },
                    {
                        "anchor_text": "remote work security best practices",
                        "url": "/blog/remote-work-security",
                        "relevance": "Addresses security concerns when using productivity tools"
                    }
                ]
            }
        
        # External References
        elif "external" in prompt_lower or "reference" in prompt_lower or "source" in prompt_lower:
            return {
                "references": [
                    {
                        "title": "State of Remote Work Report 2024",
                        "url": "https://buffer.com/state-of-remote-work",
                        "authority": "Buffer",
                        "relevance": "Authoritative research on remote work trends and tool usage"
                    },
                    {
                        "title": "Productivity Tool Comparison Guide",
                        "url": "https://www.gartner.com/en/productivity-tools",
                        "authority": "Gartner",
                        "relevance": "Industry analysis of leading productivity platforms"
                    },
                    {
                        "title": "Remote Collaboration Best Practices",
                        "url": "https://hbr.org/remote-collaboration",
                        "authority": "Harvard Business Review",
                        "relevance": "Expert insights on effective remote collaboration"
                    }
                ]
            }
        
        # Default fallback
        return {
            "status": "success",
            "data": "Mock response generated successfully"
        }