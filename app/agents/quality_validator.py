from typing import Dict
from app.models.response import ArticleContent, SEOMetadata

class QualityValidator:
    """Agent for validating article quality and SEO compliance"""
    
    def validate_seo_quality(
        self, 
        article: ArticleContent, 
        metadata: SEOMetadata,
        target_word_count: int
    ) -> Dict:
        """
        Validate article meets SEO best practices
        
        Returns:
            Dict with score, max_score, percentage, issues, and passed flag
        """
        
        score = 0
        max_score = 100
        issues = []
        
        # 1. Title tag length (10 points)
        title_len = len(metadata.title_tag)
        if 50 <= title_len <= 60:
            score += 10
        else:
            issues.append(f"Title tag should be 50-60 chars (current: {title_len})")
        
        # 2. Meta description length (10 points)
        desc_len = len(metadata.meta_description)
        if 150 <= desc_len <= 160:
            score += 10
        else:
            issues.append(f"Meta description should be 150-160 chars (current: {desc_len})")
        
        # 3. Primary keyword in H1 (15 points)
        if metadata.focus_keyword.lower() in article.h1.lower():
            score += 15
        else:
            issues.append("Primary keyword not found in H1")
        
        # 4. Keyword in first 100 words (15 points)
        first_100 = ' '.join(article.full_text.split()[:100])
        if metadata.focus_keyword.lower() in first_100.lower():
            score += 15
        else:
            issues.append("Primary keyword not in first 100 words")
        
        # 5. Word count within target range ±10% (10 points)
        word_diff = abs(article.word_count - target_word_count)
        acceptable_range = target_word_count * 0.1
        if word_diff <= acceptable_range:
            score += 10
        else:
            issues.append(f"Word count off target by {word_diff} words (target: {target_word_count}, actual: {article.word_count})")
        
        # 6. Proper heading structure - at least 4 H2 sections (15 points)
        if len(article.sections) >= 4:
            score += 15
        else:
            issues.append(f"Should have at least 4 H2 sections (has {len(article.sections)})")
        
        # 7. Keyword density check - ideal 1-2.5% (10 points)
        content_lower = article.full_text.lower()
        keyword_count = content_lower.count(metadata.focus_keyword.lower())
        density = (keyword_count / article.word_count) * 100 if article.word_count > 0 else 0
        
        if 1.0 <= density <= 2.5:
            score += 10
        else:
            issues.append(f"Keyword density should be 1-2.5% (current: {density:.2f}%)")
        
        # 8. Readability - average sentence length (15 points)
        sentence_count = (
            article.full_text.count('.') + 
            article.full_text.count('!') + 
            article.full_text.count('?')
        )
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
