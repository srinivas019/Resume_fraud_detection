"""
Language Analyzer - Detects exaggeration and suspicious language patterns
"""

from textblob import TextBlob
from typing import Dict, List
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import config


class LanguageAnalyzer:
    """Analyze resume language for fraud indicators"""
    
    def __init__(self):
        self.suspicious_keywords = config.FEATURE_CONFIG['suspicious_keywords']
        self.vague_quantifiers = config.FEATURE_CONFIG['vague_quantifiers']
        
        # Additional fraud indicators
        self.red_flag_phrases = [
            'single-handedly', 'revolutionized', 'transformed the company',
            'best in class', 'world-class', 'industry leader', 'top performer',
            'guru', 'ninja', 'rockstar', 'wizard', 'expert in everything'
        ]
        
        self.exaggeration_modifiers = [
            'extremely', 'highly', 'very', 'exceptionally', 'extraordinarily',
            'uniquely', 'unparalleled', 'unmatched', 'supreme'
        ]
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for language-based fraud indicators
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary with analysis results
        """
        text_lower = text.lower()
        
        results = {
            'exaggeration_score': 0.0,
            'suspicious_keyword_count': 0,
            'vague_quantifier_count': 0,
            'red_flag_phrase_count': 0,
            'exaggeration_modifier_count': 0,
            'sentiment_confidence': 0.0,
            'readability_score': 0.0,
            'details': {
                'suspicious_keywords': [],
                'vague_quantifiers': [],
                'red_flags': [],
                'exaggeration_modifiers': []
            }
        }
        
        # Count suspicious keywords
        for keyword in self.suspicious_keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                results['suspicious_keyword_count'] += count
                results['details']['suspicious_keywords'].append({
                    'word': keyword,
                    'count': count
                })
        
        # Count vague quantifiers
        for quantifier in self.vague_quantifiers:
            count = text_lower.count(quantifier.lower())
            if count > 0:
                results['vague_quantifier_count'] += count
                results['details']['vague_quantifiers'].append({
                    'word': quantifier,
                    'count': count
                })
        
        # Count red flag phrases
        for phrase in self.red_flag_phrases:
            if phrase.lower() in text_lower:
                results['red_flag_phrase_count'] += 1
                results['details']['red_flags'].append(phrase)
        
        # Count exaggeration modifiers
        for modifier in self.exaggeration_modifiers:
            count = text_lower.count(modifier.lower())
            if count > 0:
                results['exaggeration_modifier_count'] += count
                results['details']['exaggeration_modifiers'].append({
                    'word': modifier,
                    'count': count
                })
        
        # Sentiment analysis
        sentiment_results = self.analyze_sentiment(text)
        results['sentiment_confidence'] = sentiment_results['confidence']
        results['sentiment_polarity'] = sentiment_results['polarity']
        
        # Readability
        results['readability_score'] = self.calculate_readability(text)
        
        # Calculate overall exaggeration score (0-100)
        exaggeration_score = min(
            (results['suspicious_keyword_count'] * 5 +
             results['red_flag_phrase_count'] * 10 +
             results['exaggeration_modifier_count'] * 3 +
             results['vague_quantifier_count'] * 2),
            100
        )
        
        results['exaggeration_score'] = exaggeration_score
        
        return results
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of resume text
        Over-confidence can be a fraud indicator
        """
        blob = TextBlob(text)
        
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # High positive polarity + high subjectivity = over-confidence
        confidence_score = (polarity + 1) / 2 * subjectivity * 100
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'confidence': confidence_score
        }
    
    def calculate_readability(self, text: str) -> float:
        """
        Calculate readability score
        Overly complex language can mask fraud
        """
        # Simple readability metric based on sentence and word length
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        words = text.split()
        
        if not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Flesch Reading Ease approximation (simplified)
        # Higher score = easier to read
        readability = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / 5)
        
        return max(0, min(100, readability))
    
    def check_buzzword_density(self, text: str) -> Dict:
        """Check for excessive buzzword usage"""
        buzzwords = [
            'synergy', 'leverage', 'paradigm', 'disruptive', 'innovative',
            'cutting-edge', 'state-of-the-art', 'best-of-breed', 'scalable',
            'robust', 'comprehensive', 'strategic', 'dynamic', 'proactive'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            return {'density': 0.0, 'count': 0}
        
        buzzword_count = sum(1 for word in words if word in buzzwords)
        density = (buzzword_count / len(words)) * 100
        
        return {
            'density': density,
            'count': buzzword_count,
            'excessive': density > 2.0  # > 2% is excessive
        }
    
    def detect_quantification_issues(self, text: str) -> Dict:
        """Detect issues with quantified achievements"""
        issues = {
            'missing_metrics': False,
            'unrealistic_numbers': [],
            'vague_claims': []
        }
        
        # Look for achievement patterns
        achievement_markers = [
            'increased', 'decreased', 'improved', 'reduced', 'grew',
            'achieved', 'delivered', 'saved', 'generated'
        ]
        
        text_lower = text.lower()
        
        # Find achievement claims
        for marker in achievement_markers:
            if marker in text_lower:
                # Check if followed by a number
                pattern = rf'{marker}\s+.*?(\d+)'
                matches = re.findall(pattern, text_lower)
                
                if not matches:
                    issues['vague_claims'].append(marker)
                else:
                    # Check for unrealistic percentages (> 200%)
                    for match in matches:
                        if match.endswith('%') or 'percent' in text_lower:
                            try:
                                value = int(match.replace('%', ''))
                                if value > 200:
                                    issues['unrealistic_numbers'].append({
                                        'value': value,
                                        'context': marker
                                    })
                            except:
                                pass
        
        return issues
    
    def analyze_first_person_usage(self, text: str) -> Dict:
        """
        Analyze first-person pronoun usage
        Excessive "I" usage can indicate self-aggrandizement
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            return {'ratio': 0.0, 'count': 0}
        
        first_person_pronouns = ['i', "i'm", "i've", "my", 'me', 'myself']
        
        count = sum(1 for word in words if word in first_person_pronouns)
        ratio = (count / len(words)) * 100
        
        return {
            'count': count,
            'ratio': ratio,
            'excessive': ratio > 3.0  # > 3% is excessive
        }


def main():
    """Test language analyzer"""
    
    # Sample fraudulent text
    fraudulent_text = """
    I am the best software engineer in the industry and a world-class expert.
    I single-handedly revolutionized the entire company and transformed all processes.
    As a rockstar developer and guru, I've achieved extraordinary results.
    I'm highly skilled in many programming languages and numerous frameworks.
    My exceptional abilities are unmatched and I've delivered groundbreaking solutions.
    """
    
    # Sample genuine text
    genuine_text = """
    Experienced software engineer with 5 years in backend development.
    Worked with teams to deliver scalable applications using Python and Java.
    Contributed to improving system performance by 40% through optimization.
    Collaborated with cross-functional teams on multiple projects.
    """
    
    analyzer = LanguageAnalyzer()
    
    print("FRAUDULENT TEXT ANALYSIS:")
    print("=" * 80)
    fraud_results = analyzer.analyze(fraudulent_text)
    print(f"Exaggeration Score: {fraud_results['exaggeration_score']}/100")
    print(f"Suspicious Keywords: {fraud_results['suspicious_keyword_count']}")
    print(f"Red Flags: {fraud_results['red_flag_phrase_count']}")
    print(f"Sentiment Confidence: {fraud_results['sentiment_confidence']:.2f}")
    
    print("\n\nGENUINE TEXT ANALYSIS:")
    print("=" * 80)
    genuine_results = analyzer.analyze(genuine_text)
    print(f"Exaggeration Score: {genuine_results['exaggeration_score']}/100")
    print(f"Suspicious Keywords: {genuine_results['suspicious_keyword_count']}")
    print(f"Red Flags: {genuine_results['red_flag_phrase_count']}")
    print(f"Sentiment Confidence: {genuine_results['sentiment_confidence']:.2f}")


if __name__ == "__main__":
    main()
