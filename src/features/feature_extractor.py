"""
Feature Extractor - Converts resume data into ML-ready features
"""

import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.extraction.resume_parser import ResumeParser
from src.nlp.ner_extractor import NERExtractor
from src.nlp.timeline_analyzer import TimelineAnalyzer
from src.nlp.language_analyzer import LanguageAnalyzer


class FeatureExtractor:
    """Extract machine learning features from resumes"""
    
    def __init__(self):
        self.parser = ResumeParser()
        self.ner = NERExtractor()
        self.timeline_analyzer = TimelineAnalyzer()
        self.language_analyzer = LanguageAnalyzer()
        
        # Feature names for reference
        self.feature_names = []
        self._initialize_feature_names()
    
    def _initialize_feature_names(self):
        """Initialize feature names for tracking"""
        # Structural features (10)
        self.feature_names.extend([
            'resume_length', 'num_sections', 'num_paragraphs',
            'num_sentences', 'num_words', 'avg_sentence_length',
            'avg_word_length', 'has_summary', 'has_skills', 'has_certifications'
        ])
        
        # Contact features (5)
        self.feature_names.extend([
            'has_email', 'has_phone', 'num_emails', 'num_phones', 'email_domain_common'
        ])
        
        # Education features (15)
        self.feature_names.extend([
            'num_degrees', 'has_bachelors', 'has_masters', 'has_phd',
            'avg_education_duration', 'max_gpa', 'has_unknown_university',
            'num_universities', 'education_timeline_consistent',
            'education_recent', 'education_order_correct',
            'has_prestigious_university', 'education_level_score',
            'num_education_overlaps', 'education_gap_years'
        ])
        
        # Experience features (20)
        self.feature_names.extend([
            'num_jobs', 'total_experience_years', 'avg_job_duration',
            'min_job_duration', 'max_job_duration', 'num_companies',
            'num_job_changes', 'career_progression_score', 'has_executive_title',
            'has_inflated_title', 'title_consistency', 'num_employment_overlaps',
            'employment_gap_months', 'has_prestigious_company',
            'responsibility_count', 'avg_responsibilities_per_job',
            'has_quantified_achievements', 'job_title_diversity',
            'company_diversity', 'experience_education_gap'
        ])
        
        # Skills features (15)
        self.feature_names.extend([
            'num_skills', 'num_programming_languages', 'num_frameworks',
            'num_databases', 'num_cloud_platforms', 'num_ml_skills',
            'skill_diversity_score', 'skills_experience_ratio',
            'has_unrealistic_skills', 'skill_category_balance',
            'rare_skill_combination', 'skill_proficiency_claims',
            'technical_depth_score', 'skill_recency_score', 'skill_overlap_score'
        ])
        
        # Timeline features (20)
        self.feature_names.extend([
            'timeline_anomaly_score', 'num_overlapping_periods',
            'education_work_overlap', 'total_timeline_gaps',
            'suspicious_gaps', 'career_jump_severity',
            'years_to_senior', 'years_to_executive',
            'promotion_frequency', 'job_hopping_score',
            'timeline_consistency', 'date_format_consistency',
            'missing_dates_count', 'future_dates_count',
            'timeline_logical_order', 'experience_continuity',
            'education_timing_realistic', 'early_career_appropriate',
            'mid_career_appropriate', 'late_career_appropriate'
        ])
        
        # Language features (25)
        self.feature_names.extend([
            'exaggeration_score', 'suspicious_keyword_count',
            'vague_quantifier_count', 'red_flag_phrase_count',
            'exaggeration_modifier_count', 'sentiment_polarity',
            'sentiment_subjectivity', 'sentiment_confidence',
            'readability_score', 'buzzword_density',
            'buzzword_count', 'first_person_ratio',
            'first_person_count', 'quantification_issues',
            'missing_metrics', 'unrealistic_numbers_count',
            'vague_claims_count', 'superlative_density',
            'passive_voice_ratio', 'jargon_density',
            'grammar_score', 'spelling_errors', 'formatting_consistency',
            'professional_tone_score', 'language_complexity'
        ])
        
        # Certification features (8)
        self.feature_names.extend([
            'num_certifications', 'has_genuine_certs', 'has_fake_certs',
            'cert_relevance_score', 'cert_recency', 'cert_issuer_credibility',
            'cert_skill_alignment', 'excessive_certifications'
        ])
        
        # Anomaly features (12)
        self.feature_names.extend([
            'overall_anomaly_score', 'structural_anomalies',
            'content_anomalies', 'temporal_anomalies',
            'credential_anomalies', 'statistical_outlier_score',
            'pattern_mismatch_score', 'information_density',
            'detail_level_consistency', 'verification_difficulty',
            'red_flag_density', 'trust_score'
        ])
    
    def extract_features(self, resume_path: str = None, resume_text: str = None) -> Dict:
        """
        Extract all features from resume
        
        Args:
            resume_path: Path to resume file
            resume_text: Resume text (if already parsed)
            
        Returns:
            Dictionary of features
        """
        # Parse resume if needed
        if resume_text is None:
            if resume_path is None:
                raise ValueError("Either resume_path or resume_text must be provided")
            resume_text = self.parser.parse(Path(resume_path))
        
        if not resume_text:
            raise ValueError("Failed to extract text from resume")
        
        # Extract entities
        entities = self.ner.extract_all(resume_text)
        
        # Analyze timeline
        timeline_results = self.timeline_analyzer.analyze_timeline(
            entities.get('education', []),
            entities.get('experience', [])  # Note: We'll need work_experience from NER
        )
        
        # Analyze language
        language_results = self.language_analyzer.analyze(resume_text)
        
        # Build feature vector
        features = {}
        
        # Structural features
        features.update(self._extract_structural_features(resume_text))
        
        # Contact features
        features.update(self._extract_contact_features(entities))
        
        # Education features
        features.update(self._extract_education_features(entities.get('education', [])))
        
        # Experience features (placeholder - needs work experience extraction)
        features.update(self._extract_experience_features([]))
        
        # Skills features
        features.update(self._extract_skills_features(entities.get('skills', [])))
        
        # Timeline features
        features.update(self._extract_timeline_features(timeline_results))
        
        # Language features
        features.update(self._extract_language_features(language_results))
        
        # Certification features
        features.update(self._extract_certification_features(entities.get('certifications', [])))
        
        # Anomaly features
        features.update(self._extract_anomaly_features(features, timeline_results, language_results))
        
        return features
    
    def extract_features_batch(self, resume_paths: List[str]) -> List[Dict]:
        """Extract features from multiple resumes"""
        features_list = []
        
        for path in resume_paths:
            try:
                features = self.extract_features(resume_path=path)
                features_list.append(features)
            except Exception as e:
                print(f"Error extracting features from {path}: {e}")
                features_list.append(None)
        
        return features_list
    
    def features_to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dictionary to numpy vector"""
        vector = []
        
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0)
            vector.append(value)
        
        return np.array(vector)
    
    def _extract_structural_features(self, text: str) -> Dict:
        """Extract structural features"""
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        sentences = [s for s in text.split('.') if s.strip()]
        words = text.split()
        
        return {
            'resume_length': len(text),
            'num_sections': len(paragraphs),
            'num_paragraphs': len(paragraphs),
            'num_sentences': len(sentences),
            'num_words': len(words),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'avg_word_length': sum(len(w) for w in words) / max(len(words), 1),
            'has_summary': 1 if 'summary' in text.lower() else 0,
            'has_skills': 1 if 'skills' in text.lower() else 0,
            'has_certifications': 1 if 'certification' in text.lower() else 0,
        }
    
    def _extract_contact_features(self, entities: Dict) -> Dict:
        """Extract contact-related features"""
        emails = entities.get('emails', [])
        phones = entities.get('phones', [])
        
        common_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
        email_domain_common = any(
            any(domain in email for domain in common_domains)
            for email in emails
        ) if emails else 0
        
        return {
            'has_email': 1 if emails else 0,
            'has_phone': 1 if phones else 0,
            'num_emails': len(emails),
            'num_phones': len(phones),
            'email_domain_common': email_domain_common,
        }
    
    def _extract_education_features(self, education: List[Dict]) -> Dict:
        """Extract education-related features"""
        if not education:
            return {f: 0 for f in self.feature_names if 'education' in f or 'degree' in f or 'university' in f}
        
        degree_types = [edu.get('degree', '').lower() for edu in education]
        
        return {
            'num_degrees': len(education),
            'has_bachelors': 1 if any('bachelor' in d for d in degree_types) else 0,
            'has_masters': 1 if any('master' in d for d in degree_types) else 0,
            'has_phd': 1 if any('phd' in d or 'doctor' in d for d in degree_types) else 0,
            'avg_education_duration': 4.0,  # Placeholder
            'max_gpa': 0.0,  # Placeholder
            'has_unknown_university': 0,
            'num_universities': len(set(edu.get('university', '') for edu in education)),
            'education_timeline_consistent': 1,
            'education_recent': 0,
            'education_order_correct': 1,
            'has_prestigious_university': 0,
            'education_level_score': len(education) * 10,
            'num_education_overlaps': 0,
            'education_gap_years': 0,
        }
    
    def _extract_experience_features(self, experience: List[Dict]) -> Dict:
        """Extract work experience features"""
        # Placeholder implementation
        return {f: 0 for f in self.feature_names if 'job' in f or 'experience' in f or 'career' in f or 'employment' in f}
    
    def _extract_skills_features(self, skills: List[str]) -> Dict:
        """Extract skills-related features"""
        programming = ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go']
        ml_skills = ['machine learning', 'deep learning', 'tensorflow', 'pytorch']
        
        return {
            'num_skills': len(skills),
            'num_programming_languages': sum(1 for s in skills if s.lower() in programming),
            'num_frameworks': 0,
            'num_databases': 0,
            'num_cloud_platforms': 0,
            'num_ml_skills': sum(1 for s in skills if any(ml in s.lower() for ml in ml_skills)),
            'skill_diversity_score': len(set(skills)),
            'skills_experience_ratio': 0,
            'has_unrealistic_skills': 1 if len(skills) > 50 else 0,
            'skill_category_balance': 0,
            'rare_skill_combination': 0,
            'skill_proficiency_claims': 0,
            'technical_depth_score': min(len(skills) * 2, 100),
            'skill_recency_score': 50,
            'skill_overlap_score': 0,
        }
    
    def _extract_timeline_features(self, timeline_results: Dict) -> Dict:
        """Extract timeline-related features"""
        return {
            'timeline_anomaly_score': timeline_results.get('anomaly_score', 0),
            'num_overlapping_periods': len(timeline_results.get('overlapping_employment', [])),
            'education_work_overlap': len(timeline_results.get('education_work_overlap', [])),
            'total_timeline_gaps': timeline_results.get('timeline_gaps', {}).get('total_gaps', 0),
            'suspicious_gaps': timeline_results.get('timeline_gaps', {}).get('suspicious_gaps', 0),
            'career_jump_severity': len(timeline_results.get('unrealistic_progression', [])) * 20,
            'years_to_senior': 0,
            'years_to_executive': 0,
            'promotion_frequency': 0,
            'job_hopping_score': 0,
            'timeline_consistency': 100 - timeline_results.get('anomaly_score', 0),
            'date_format_consistency': 80,
            'missing_dates_count': 0,
            'future_dates_count': 0,
            'timeline_logical_order': 1,
            'experience_continuity': 80,
            'education_timing_realistic': 1,
            'early_career_appropriate': 1,
            'mid_career_appropriate': 1,
            'late_career_appropriate': 1,
        }
    
    def _extract_language_features(self, language_results: Dict) -> Dict:
        """Extract language analysis features"""
        buzzword_check = language_results.get('buzzword_density', {})
        
        return {
            'exaggeration_score': language_results.get('exaggeration_score', 0),
            'suspicious_keyword_count': language_results.get('suspicious_keyword_count', 0),
            'vague_quantifier_count': language_results.get('vague_quantifier_count', 0),
            'red_flag_phrase_count': language_results.get('red_flag_phrase_count', 0),
            'exaggeration_modifier_count': language_results.get('exaggeration_modifier_count', 0),
            'sentiment_polarity': language_results.get('sentiment_polarity', 0),
            'sentiment_subjectivity': language_results.get('sentiment_confidence', 0) / 100,
            'sentiment_confidence': language_results.get('sentiment_confidence', 0),
            'readability_score': language_results.get('readability_score', 0),
            'buzzword_density': buzzword_check.get('density', 0) if isinstance(buzzword_check, dict) else 0,
            'buzzword_count': buzzword_check.get('count', 0) if isinstance(buzzword_check, dict) else 0,
            'first_person_ratio': 0,
            'first_person_count': 0,
            'quantification_issues': 0,
            'missing_metrics': 0,
            'unrealistic_numbers_count': 0,
            'vague_claims_count': 0,
            'superlative_density': language_results.get('suspicious_keyword_count', 0),
            'passive_voice_ratio': 0,
            'jargon_density': 0,
            'grammar_score': 80,
            'spelling_errors': 0,
            'formatting_consistency': 85,
            'professional_tone_score': 70,
            'language_complexity': 60,
        }
    
    def _extract_certification_features(self, certifications: List[str]) -> Dict:
        """Extract certification features"""
        genuine_certs = ['aws', 'microsoft', 'google', 'pmp', 'cissp']
        has_genuine = any(any(gc in cert.lower() for gc in genuine_certs) for cert in certifications)
        
        return {
            'num_certifications': len(certifications),
            'has_genuine_certs': 1 if has_genuine else 0,
            'has_fake_certs': 0,
            'cert_relevance_score': 50,
            'cert_recency': 50,
            'cert_issuer_credibility': 70 if has_genuine else 30,
            'cert_skill_alignment': 60,
            'excessive_certifications': 1 if len(certifications) > 10 else 0,
        }
    
    def _extract_anomaly_features(
        self, features: Dict, timeline_results: Dict, language_results: Dict
    ) -> Dict:
        """Calculate overall anomaly scores"""
        
        # Aggregate anomaly scores
        timeline_anomaly = timeline_results.get('anomaly_score', 0)
        language_anomaly = language_results.get('exaggeration_score', 0)
        
        overall_anomaly = (timeline_anomaly + language_anomaly) / 2
        
        return {
            'overall_anomaly_score': overall_anomaly,
            'structural_anomalies': 0,
            'content_anomalies': language_anomaly,
            'temporal_anomalies': timeline_anomaly,
            'credential_anomalies': 0,
            'statistical_outlier_score': 0,
            'pattern_mismatch_score': 0,
            'information_density': 50,
            'detail_level_consistency': 70,
            'verification_difficulty': 50,
            'red_flag_density': language_results.get('red_flag_phrase_count', 0) * 10,
            'trust_score': max(0, 100 - overall_anomaly),
        }


def main():
    """Test feature extraction"""
    extractor = FeatureExtractor()
    
    # Sample resume text
    sample_text = """
    John Doe
    john.doe@email.com | +1-555-1234
    
    SUMMARY
    Senior Software Engineer with 8 years of experience.
    
    EXPERIENCE
    Senior Software Engineer - Google (2018 - Present)
    Software Engineer - Microsoft (2015 - 2018)
    
    EDUCATION
    Master of Science in Computer Science - Stanford (2013 - 2015)
    Bachelor of Engineering - MIT (2009 - 2013)
    
    SKILLS
    Python, Java, React, AWS, Machine Learning
    
    CERTIFICATIONS
    AWS Certified Solutions Architect
    """
    
    features = extractor.extract_features(resume_text=sample_text)
    
    print(f"Total features extracted: {len(features)}")
    print(f"\nKey features:")
    for key, value in list(features.items())[:20]:
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
