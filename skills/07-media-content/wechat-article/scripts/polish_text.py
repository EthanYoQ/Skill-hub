#!/usr/bin/env python3
"""
Polish WeChat article text - check for writing style and readability
"""
import argparse
import re
from pathlib import Path


class ArticlePolisher:
    def __init__(self):
        self.issues = []
        self.suggestions = []
    
    def check_sentence_length(self, text: str) -> None:
        """Check if sentences are too long"""
        sentences = re.split(r'[。！？；]', text)
        for i, sent in enumerate(sentences):
            if len(sent) > 60:  # Too long
                self.issues.append(f"Line {i}: Sentence too long ({len(sent)} chars) - consider breaking it up")
    
    def check_passive_voice(self, text: str) -> None:
        """Check for passive voice patterns"""
        passive_patterns = [
            r'被[^。]*[了着]',
            r'[^。]*来说',
            r'[^。]*而言',
        ]
        
        for pattern in passive_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                self.suggestions.append(f"Consider using active voice instead of: '{match.group()}'")
    
    def check_empty_phrases(self, text: str) -> None:
        """Check for common empty phrases"""
        empty_phrases = [
            '非常重要', '非常关键', '我想说', '当今社会', '在这个时代',
            '不容否认', '值得注意', '根据相关研究',
        ]
        
        for phrase in empty_phrases:
            if phrase in text:
                self.issues.append(f"❌ Empty phrase found: '{phrase}' - be more specific")
    
    def check_paragraph_structure(self, text: str) -> None:
        """Check if paragraphs are well-structured"""
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs):
            if len(para) < 20:  # Too short
                if para.strip():  # Not empty
                    self.suggestions.append(f"Paragraph {i} is very short - consider merging")
            elif len(para) > 500:  # Too long
                self.suggestions.append(f"Paragraph {i} is very long ({len(para)} chars) - consider splitting")
    
    def check_story_elements(self, text: str) -> None:
        """Check if article has storytelling elements"""
        story_keywords = ['故事', '那时', '记得', '曾经', '当时', '比如', '例如']
        has_story = any(keyword in text for keyword in story_keywords)
        
        if not has_story:
            self.suggestions.append("💡 Consider adding more stories or examples to make it relatable")
    
    def check_data_support(self, text: str) -> None:
        """Check if article has data support"""
        data_patterns = [r'\d+%', r'\d+亿', r'\d+万', r'\$\d+']
        has_data = any(re.search(pattern, text) for pattern in data_patterns)
        
        if not has_data:
            self.suggestions.append("💡 Consider adding data/numbers to support your points")
    
    def check_opinions(self, text: str) -> None:
        """Check if article has clear opinions"""
        opinion_keywords = ['我认为', '我觉得', '老实说', '我的看法', '在我看来']
        has_opinion = any(keyword in text for keyword in opinion_keywords)
        
        if not has_opinion:
            self.suggestions.append("⚠️ Consider expressing clearer personal opinions or viewpoints")
    
    def polish(self, text: str) -> dict:
        """Run all checks"""
        self.issues = []
        self.suggestions = []
        
        self.check_sentence_length(text)
        self.check_passive_voice(text)
        self.check_empty_phrases(text)
        self.check_paragraph_structure(text)
        self.check_story_elements(text)
        self.check_data_support(text)
        self.check_opinions(text)
        
        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "word_count": len(text),
            "paragraph_count": len(text.split('\n\n')),
            "avg_paragraph_length": len(text) // max(1, len(text.split('\n\n')))
        }


def main():
    parser = argparse.ArgumentParser(description="Polish WeChat article")
    parser.add_argument("file", help="Article file path (.md or .txt)")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix simple issues")
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    text = file_path.read_text(encoding='utf-8')
    polisher = ArticlePolisher()
    result = polisher.polish(text)
    
    print("=" * 60)
    print("📊 ARTICLE ANALYSIS")
    print("=" * 60)
    print(f"📝 Word count: {result['word_count']}")
    print(f"📄 Paragraph count: {result['paragraph_count']}")
    print(f"📏 Avg paragraph length: {result['avg_paragraph_length']} chars")
    print()
    
    if result['issues']:
        print("❌ ISSUES TO FIX:")
        print("-" * 60)
        for issue in result['issues']:
            print(f"  • {issue}")
        print()
    else:
        print("✅ No critical issues found!")
        print()
    
    if result['suggestions']:
        print("💡 SUGGESTIONS:")
        print("-" * 60)
        for suggestion in result['suggestions']:
            print(f"  • {suggestion}")
        print()
    else:
        print("🎉 Article looks great!")
        print()
    
    # Overall score
    total_checks = 7
    issues_count = len(result['issues'])
    suggestions_count = len(result['suggestions'])
    
    score = max(0, 100 - (issues_count * 10) - (suggestions_count * 5))
    
    print("=" * 60)
    print(f"📈 OVERALL SCORE: {score}/100")
    print("=" * 60)
    
    if score >= 80:
        print("🎉 Great article! Ready to publish.")
    elif score >= 60:
        print("👍 Good article. Address suggestions to improve.")
    else:
        print("⚠️ Needs work. Fix issues before publishing.")


if __name__ == "__main__":
    main()
