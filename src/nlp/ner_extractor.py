"""
Named Entity Recognition (NER) Extractor
Extracts entities from resume text using SpaCy and custom patterns
"""

import spacy
from spacy.matcher import Matcher
from typing import Dict, List
import re
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NERExtractor:
    """Extract named entities from resume text"""
    
    def __init__(self, model_name='en_core_web_lg'):
        """Initialize NER extractor with SpaCy model"""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', model_name])
            self.nlp = spacy.load(model_name)
        
        self.matcher = Matcher(self.nlp.vocab)
        self._add_custom_patterns()
    
    def _add_custom_patterns(self):
        """Add custom patterns for better entity recognition"""
        
        # Phone number pattern
        phone_pattern = [
            {'TEXT': {'REGEX': r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'}}
        ]
        self.matcher.add('PHONE', [phone_pattern])
        
        # Email pattern
        email_pattern = [
            {'TEXT': {'REGEX': r'[\w\.-]+@[\w\.-]+\.\w+'}}
        ]
        self.matcher.add('EMAIL', [email_pattern])
        
        # GPA pattern
        gpa_pattern = [
            {'LOWER': 'gpa'},
            {'IS_PUNCT': True, 'OP': '?'},
            {'LIKE_NUM': True}
        ]
        self.matcher.add('GPA', [gpa_pattern])
    
    def extract_all(self, text: str) -> Dict:
        """
        Extract all entities from resume text
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary containing all extracted entities
        """
        doc = self.nlp(text)
        
        return {
            'person_name': self.extract_person_name(doc),
            'emails': self.extract_emails(text),
            'phones': self.extract_phones(text),
            'organizations': self.extract_organizations(doc),
            'education': self.extract_education(doc, text),
            'skills': self.extract_skills(doc, text),
            'dates': self.extract_dates(doc),
            'certifications': self.extract_certifications(text),
        }
    
    def extract_person_name(self, doc) -> str:
        """Extract person's name (usually first PERSON entity)"""
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text
        return ""
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers"""
        phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        phones = re.findall(phone_pattern, text)
        # Filter out dates and other numbers
        phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 10]
        return list(set(phones))
    
    def extract_organizations(self, doc) -> List[str]:
        """Extract organization names"""
        organizations = []
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                organizations.append(ent.text)
        return list(set(organizations))
    
    def extract_education(self, doc, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(?:Bachelor|B\.?S\.?|B\.?A\.?|B\.?Tech|B\.?E\.?)\s+(?:of\s+)?(?:Science|Arts|Technology|Engineering)?(?:\s+in\s+[\w\s]+)?',
            r'(?:Master|M\.?S\.?|M\.?A\.?|M\.?Tech|M\.?B\.?A\.?|M\.?E\.?)\s+(?:of\s+)?(?:Science|Arts|Technology|Business Administration|Engineering)?(?:\s+in\s+[\w\s]+)?',
            r'(?:Ph\.?D\.?|Doctor of Philosophy|Doctorate)\s+(?:in\s+[\w\s]+)?',
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                degree_text = match.group(0)
                
                # Try to find associated university
                context_start = max(0, match.start() - 200)
                context_end = min(len(text), match.end() + 200)
                context = text[context_start:context_end]
                
                # Look for ORG entities in context
                context_doc = self.nlp(context)
                universities = [ent.text for ent in context_doc.ents if ent.label_ == 'ORG']
                
                education.append({
                    'degree': degree_text,
                    'university': universities[0] if universities else 'Unknown',
                })
        
        return education
    
    def extract_skills(self, doc, text: str) -> List[str]:
        """Extract skills from resume"""
        skills = []
        
        # Common technical skills
        skill_keywords = [
            # Programming languages
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift',
            'Kotlin', 'Go', 'Rust', 'TypeScript', 'Scala', 'R', 'MATLAB',
            
            # Web technologies
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
            'ASP.NET', 'Express', 'jQuery', 'HTML', 'CSS', 'Bootstrap',
            
            # Databases
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra',
            'Oracle', 'SQLite', 'DynamoDB', 'Elasticsearch',
            
            # Cloud & DevOps
            'AWS', 'Azure', 'Google Cloud', 'GCP', 'Docker', 'Kubernetes',
            'Jenkins', 'CI/CD', 'Terraform', 'Ansible',
            
            # ML/AI
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'Scikit-learn', 'Keras', 'NLP', 'Computer Vision', 'AI',
            
            # Tools & Methodologies
            'Git', 'Agile', 'Scrum', 'JIRA', 'REST API', 'GraphQL',
            'Microservices', 'Linux', 'Unix',
        ]
        
        text_lower = text.lower()
        
        for skill in skill_keywords:
            # Case-insensitive search
            if skill.lower() in text_lower:
                skills.append(skill)
        
        return list(set(skills))
    
    def extract_dates(self, doc) -> List[str]:
        """Extract dates from resume"""
        dates = []
        
        for ent in doc.ents:
            if ent.label_ == 'DATE':
                dates.append(ent.text)
        
        # Also extract year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, doc.text)
        dates.extend(years)
        
        return list(set(dates))
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'AWS Certified[\w\s]+',
            r'Microsoft Certified[\w\s]+',
            r'Google (?:Cloud )?Certified[\w\s]+',
            r'Certified[\w\s]+(?:Professional|Specialist|Administrator|Developer)',
            r'(?:PMP|CISSP|CISA|CISM|CEH|CompTIA|Cisco)',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)
        
        return list(set(certifications))
    
    def extract_work_experience(self, text: str) -> List[Dict]:
        """Extract work experience entries"""
        experiences = []
        
        # Job title patterns
        title_patterns = [
            r'(?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Software|Data|ML|AI)?\s*(?:Engineer|Developer|Scientist|Analyst)',
            r'(?:Engineering|Product|Project|Program)\s+Manager',
            r'(?:CTO|VP|Director|Head)\s+(?:of\s+)?(?:Engineering|Technology|Product)?',
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                title = match.group(0)
                
                # Get context around the title
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 300)
                context = text[context_start:context_end]
                
                # Extract company name (ORG entities)
                context_doc = self.nlp(context)
                companies = [ent.text for ent in context_doc.ents if ent.label_ == 'ORG']
                
                # Extract dates
                dates = [ent.text for ent in context_doc.ents if ent.label_ == 'DATE']
                
                experiences.append({
                    'title': title,
                    'company': companies[0] if companies else 'Unknown',
                    'dates': dates[:2] if len(dates) >= 2 else dates,
                })
        
        return experiences


def main():
    """Test NER extraction"""
    sample_text = """
    John Smith
    john.smith@email.com | +1-555-123-4567
    
    PROFESSIONAL SUMMARY
    Experienced Software Engineer with 5+ years of expertise.
    
    WORK EXPERIENCE
    Senior Software Engineer - Google
    Jan 2020 - Present
    • Developed scalable applications using Python and React
    
    Software Engineer - Microsoft
    Jun 2018 - Dec 2019
    
    EDUCATION
    Master of Science in Computer Science
    Stanford University (2016 - 2018)
    GPA: 3.8
    
    Bachelor of Engineering
    MIT (2012 - 2016)
    
    SKILLS
    Python, Java, JavaScript, React, AWS, Docker, Machine Learning
    
    CERTIFICATIONS
    AWS Certified Solutions Architect
    """
    
    extractor = NERExtractor()
    entities = extractor.extract_all(sample_text)
    
    print("Extracted Entities:")
    print("=" * 80)
    for key, value in entities.items():
        print(f"\n{key.upper()}:")
        print(value)


if __name__ == "__main__":
    main()
