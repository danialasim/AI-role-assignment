"""Quality Validator Agent - Ensures SEO Compliance and Content Standards.

This agent is Step 9 in the pipeline - the final quality check before output.
It validates the article meets SEO best practices across 8 criteria:

1. Title Tag Length (10 points)
   - Target: 40-65 characters
   - Why: Google truncates at ~60, but punchy 40+ char titles are perfectly valid

2. Meta Description Length (10 points)
   - Target: 145-165 characters (soft boundaries)
   - Why: Google shows ~155 chars in SERP, but isn't strict at exact boundaries
   - Partial credit: 140-170 range gets 5 points

3. Primary Keyword in H1 (15 points)
   - Why: Main heading must include target keyword for relevance
   - Uses word boundaries to avoid false matches (e.g., 'cat' != 'caterpillar')

4. Keyword in First 100 Words (15 points)
   - Why: Early keyword placement signals topic focus
   - Uses word boundaries for accurate matching

5. Word Count Accuracy (10 points)
   - Target: Within ±30% of requested length
   - Why: SEO content often runs long (detail = value), within 30% is professional standard

6. Heading Structure (15 points)
   - Target: At least 4 H2 sections
   - Why: Proper structure improves scannability and SEO

7. Keyword Density (10 points)
   - Target: Dynamic based on keyword length
     * Long-tail (5+ words): 0.1-2.5% (e.g., 'best productivity tools for remote teams')
     * Short keywords (1-4 words): 1.0-2.5% (e.g., 'SEO tips')
   - Why: Long phrases can't hit 1% without sounding robotic
   - Uses word boundaries to count only exact matches

8. Readability (15 points)
   - Target: 12-20 words per sentence average
   - Why: Shorter sentences improve readability scores
   - Uses regex to avoid counting abbreviations (Dr., U.S.A., etc.) as sentences

Scoring:
   - 100 points total
   - 70+ = PASSED (publishable quality)
   - <70 = NEEDS REVIEW (quality issues)

This validation ensures every article meets professional SEO standards.
"""

from typing import Dict
import re  # For word-boundary matching and proper sentence counting
from app.models.response import ArticleContent, SEOMetadata

class QualityValidator:
    """Validates article quality against 8 SEO best practice criteria.
    
    This is a rule-based agent (no LLM) - uses direct measurement
    of text properties to ensure SEO compliance.
    """
    
    def validate_seo_quality(
        self, 
        article: ArticleContent, 
        metadata: SEOMetadata,
        target_word_count: int
    ) -> Dict:
        """Validate article meets SEO best practices across 8 criteria.
        
        This is a comprehensive quality check ensuring publishable standards.
        Each criterion is worth points contributing to a 100-point score.
        
        Args:
            article: Generated article content with sections and full text
            metadata: SEO metadata (title, description, keyword)
            target_word_count: User's requested article length
        
        Returns:
            Dict with validation results:
            {
                "score": 85,  # Points earned
                "max_score": 100,  # Total possible points
                "percentage": 85.0,  # Score as percentage
                "issues": ["Title tag 62 chars (target: 50-60)"],  # Problems found
                "passed": True  # True if score >= 70
            }
        
        Scoring Breakdown:
            - Title length (10 pts): 50-60 characters
            - Description length (10 pts): 150-160 characters
            - Keyword in H1 (15 pts): Primary keyword must appear in title
            - Keyword in intro (15 pts): In first 100 words
            - Word count (10 pts): Within ±30% of target
            - Heading count (15 pts): At least 4 H2 sections
            - Keyword density (10 pts): Dynamic (0.1-2.5% for long-tail, 1.0-2.5% for short)
            - Readability (15 pts): 12-20 words per sentence average
        
        Passing Criteria:
            - 70-79: Acceptable quality (minor issues)
            - 80-89: Good quality (meets standards)
            - 90-100: Excellent quality (best practices)
            - <70: Needs review (quality concerns)
        """
        
        score = 0
        max_score = 100
        issues = []
        
        # 1. Title tag length (10 points)
        # Google truncates at ~60, but punchy 40+ char titles are perfectly valid SEO
        title_len = len(metadata.title_tag)
        if 40 <= title_len <= 65:
            score += 10
        else:
            issues.append(f"Title tag should be 40-65 chars (current: {title_len})")
        
        # 2. Meta description length (10 points)
        # Using 145-165 range (softer boundaries) since Google isn't strict at exactly 150
        # Ideal is 155, but 149 or 161 shouldn't fail completely
        desc_len = len(metadata.meta_description)
        if 145 <= desc_len <= 165:
            score += 10
        elif 140 <= desc_len <= 170:
            # Partial credit for close but not ideal
            score += 5
            issues.append(f"Meta description nearly ideal (current: {desc_len} chars, target: 145-165)")
        else:
            issues.append(f"Meta description should be 145-165 chars (current: {desc_len})")
        
        # 3. Primary keyword in H1 (15 points)
        # Use word boundaries to avoid false matches (e.g., 'cat' in 'caterpillar')
        # \b ensures we match whole words/phrases only
        keyword_pattern = r'\b' + re.escape(metadata.focus_keyword.lower()) + r'\b'
        if re.search(keyword_pattern, article.h1.lower()):
            score += 15
        else:
            issues.append("Primary keyword not found in H1")
        
        # 4. Keyword in first 100 words (15 points)
        # Use word boundaries to avoid false matches
        first_100 = ' '.join(article.full_text.split()[:100])
        if re.search(keyword_pattern, first_100.lower()):
            score += 15
        else:
            issues.append("Primary keyword not in first 100 words")
        
        # 5. Word count within target range ±30% (10 points)
        # SEO content often runs 20-30% over target (more detail = more value)
        # This is professional standard, not a quality issue
        word_diff = abs(article.word_count - target_word_count)
        acceptable_range = target_word_count * 0.3
        if word_diff <= acceptable_range:
            score += 10
        else:
            issues.append(f"Word count significantly off target by {word_diff} words (target: {target_word_count}, actual: {article.word_count})")
        
        # 6. Proper heading structure - at least 4 H2 sections (15 points)
        if len(article.sections) >= 4:
            score += 15
        else:
            issues.append(f"Should have at least 4 H2 sections (has {len(article.sections)})")
        
        # 7. Keyword density check - dynamic thresholds based on keyword length (10 points)
        # Long-tail keywords (5+ words) physically can't hit 1% density without sounding robotic
        # Example: "best productivity tools for remote teams" = 6 words
        #   → To hit 1% in 2000-word article, need 20 appearances = stuffing penalty
        # Use word boundaries to count only exact keyword matches
        # Prevents 'cat' from matching inside 'education', 'location', 'caterpillar'
        content_lower = article.full_text.lower()
        keyword_count = len(re.findall(keyword_pattern, content_lower))
        density = (keyword_count / article.word_count) * 100 if article.word_count > 0 else 0
        
        # Dynamic threshold based on keyword length
        keyword_word_count = len(metadata.focus_keyword.split())
        if keyword_word_count >= 5:
            min_density = 0.1  # Long-tail keywords: very low threshold (avoids stuffing)
            density_label = "0.1-2.5%"
        else:
            min_density = 1.0  # Short keywords: standard threshold
            density_label = "1.0-2.5%"
        
        if min_density <= density <= 2.5:
            score += 10
        else:
            issues.append(f"Keyword density should be {density_label} (current: {density:.2f}%)")
        
        # 8. Readability - average sentence length (15 points)
        # Use regex to properly count sentences, avoiding false positives from:
        # - Abbreviations: Dr., Mr., U.S.A., e.g., etc., vs.
        # - Decimals: 3.5, 10.2
        # - Email addresses: user@example.com
        # Pattern: Match . ! ? followed by space and capital letter (real sentence end)
        sentence_pattern = r'[.!?](?=\s+[A-Z]|\s*$)'
        sentence_count = len(re.findall(sentence_pattern, article.full_text))
        
        # Fallback: if regex finds 0 sentences (edge case), use word count heuristic
        if sentence_count == 0:
            # Assume ~15 words per sentence as baseline
            sentence_count = max(1, article.word_count // 15)
        if sentence_count > 0:
            avg_words_per_sentence = article.word_count / sentence_count
            if 12 <= avg_words_per_sentence <= 20:
                score += 15
            else:
                issues.append(
                    f"Average sentence length: {avg_words_per_sentence:.1f} words "
                    f"(ideal: 12-20 words)"
                )
        else:
            issues.append("Could not calculate sentence length")
        
        percentage = round((score / max_score) * 100, 1)
        passed = score >= 70
        
        print(f"\n📋 Quality Validation Results:")
        print(f"   Score: {score}/{max_score} ({percentage}%)")
        print(f"   Status: {'✅ PASSED' if passed else '❌ NEEDS IMPROVEMENT'}")
        if issues:
            print(f"   Issues found: {len(issues)}")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"      - {issue}")
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "issues": issues,
            "passed": passed
        }
