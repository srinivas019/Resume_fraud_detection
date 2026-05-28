"""
AI Resume Tip Generator - Generates intelligent, actionable resume improvement tips
based on NLP analysis, feature extraction, and fraud detection insights.
"""

import re
from typing import Dict, List, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))


class ResumeTipGenerator:
    """Generate AI-powered resume improvement tips based on analysis results."""

    # Tip categories with icons and priorities
    TIP_CATEGORIES = {
        'formatting': {'icon': '📄', 'label': 'Formatting & Structure', 'priority': 1},
        'content': {'icon': '✍️', 'label': 'Content Quality', 'priority': 2},
        'language': {'icon': '🗣️', 'label': 'Language & Tone', 'priority': 3},
        'skills': {'icon': '🛠️', 'label': 'Skills Presentation', 'priority': 4},
        'experience': {'icon': '💼', 'label': 'Experience Details', 'priority': 5},
        'education': {'icon': '🎓', 'label': 'Education & Credentials', 'priority': 6},
        'impact': {'icon': '📊', 'label': 'Impact & Achievements', 'priority': 7},
        'ats': {'icon': '🤖', 'label': 'ATS Optimization', 'priority': 8},
        'professional': {'icon': '🏆', 'label': 'Professional Branding', 'priority': 9},
    }

    # Action verbs for resume improvement
    STRONG_ACTION_VERBS = [
        'achieved', 'implemented', 'developed', 'designed', 'led', 'managed',
        'optimized', 'streamlined', 'delivered', 'increased', 'reduced',
        'automated', 'established', 'launched', 'mentored', 'negotiated',
        'orchestrated', 'spearheaded', 'transformed', 'pioneered'
    ]

    # Common weak phrases to avoid
    WEAK_PHRASES = [
        'responsible for', 'duties included', 'helped with', 'worked on',
        'assisted in', 'participated in', 'was involved in', 'tasked with',
        'in charge of', 'dealt with'
    ]

    def __init__(self):
        pass

    def generate_tips(
        self,
        resume_text: str,
        fraud_results: Dict,
        features: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive AI-powered resume tips.

        Args:
            resume_text: The raw resume text
            fraud_results: Results from fraud analysis
            features: Optional extracted features dictionary

        Returns:
            Dictionary with categorized tips, overall score, and summary
        """
        tips = []

        # 1. Structural & Formatting Tips
        tips.extend(self._analyze_structure(resume_text))

        # 2. Content Quality Tips
        tips.extend(self._analyze_content_quality(resume_text))

        # 3. Language & Tone Tips
        tips.extend(self._analyze_language(resume_text, fraud_results))

        # 4. Skills Section Tips
        tips.extend(self._analyze_skills(resume_text))

        # 5. Experience Tips
        tips.extend(self._analyze_experience(resume_text))

        # 6. Education Tips
        tips.extend(self._analyze_education(resume_text))

        # 7. Impact & Quantification Tips
        tips.extend(self._analyze_impact(resume_text))

        # 8. ATS Optimization Tips
        tips.extend(self._analyze_ats_readiness(resume_text))

        # 9. Professional Branding Tips
        tips.extend(self._analyze_professional_branding(resume_text, fraud_results))

        # Sort tips by priority (category priority, then individual priority)
        tips.sort(key=lambda t: (
            self.TIP_CATEGORIES.get(t['category'], {}).get('priority', 99),
            t.get('priority', 5)
        ))

        # Calculate resume improvement score (0-100)
        improvement_score = self._calculate_improvement_score(resume_text, fraud_results, tips)

        # Generate summary
        summary = self._generate_summary(improvement_score, tips)

        # Group tips by category
        categorized_tips = {}
        for tip in tips:
            cat = tip['category']
            if cat not in categorized_tips:
                cat_info = self.TIP_CATEGORIES.get(cat, {'icon': '💡', 'label': cat.title(), 'priority': 99})
                categorized_tips[cat] = {
                    'icon': cat_info['icon'],
                    'label': cat_info['label'],
                    'tips': []
                }
            categorized_tips[cat]['tips'].append({
                'title': tip['title'],
                'description': tip['description'],
                'priority': tip.get('priority', 'medium'),
                'type': tip.get('type', 'suggestion'),  # suggestion, warning, positive
            })

        return {
            'improvement_score': improvement_score,
            'total_tips': len(tips),
            'summary': summary,
            'categorized_tips': categorized_tips,
            'top_3_tips': [
                {'title': t['title'], 'description': t['description'], 'category': t['category']}
                for t in tips[:3]
            ],
            'strengths': self._identify_strengths(resume_text, fraud_results),
        }

    def _analyze_structure(self, text: str) -> List[Dict]:
        """Analyze resume structure and formatting."""
        tips = []
        lines = text.strip().split('\n')
        word_count = len(text.split())
        non_empty_lines = [l for l in lines if l.strip()]

        # Resume length
        if word_count < 150:
            tips.append({
                'category': 'formatting',
                'title': 'Resume is Too Short',
                'description': f'Your resume contains only {word_count} words. A well-crafted resume typically has 400-800 words. Add more detail about your experience, projects, and achievements.',
                'priority': 1,
                'type': 'warning'
            })
        elif word_count > 1500:
            tips.append({
                'category': 'formatting',
                'title': 'Consider Trimming Your Resume',
                'description': f'At {word_count} words, your resume is quite long. Focus on the most relevant and recent experiences. Aim for 1-2 pages maximum.',
                'priority': 2,
                'type': 'suggestion'
            })

        # Section detection
        essential_sections = {
            'contact': r'(?i)(email|phone|address|contact|linkedin)',
            'experience': r'(?i)(experience|employment|work\s*history|professional)',
            'education': r'(?i)(education|academic|degree|university|college)',
            'skills': r'(?i)(skills|technical\s*skills|competencies|technologies)',
        }

        missing_sections = []
        for section_name, pattern in essential_sections.items():
            if not re.search(pattern, text):
                missing_sections.append(section_name.title())

        if missing_sections:
            tips.append({
                'category': 'formatting',
                'title': 'Missing Essential Sections',
                'description': f'Your resume appears to be missing these key sections: {", ".join(missing_sections)}. Ensure all essential sections are clearly labeled and present.',
                'priority': 1,
                'type': 'warning'
            })

        # Check for summary/objective
        if not re.search(r'(?i)(summary|objective|profile|about\s*me|professional\s*summary)', text):
            tips.append({
                'category': 'formatting',
                'title': 'Add a Professional Summary',
                'description': 'Start your resume with a 2-3 sentence professional summary that highlights your key strengths, years of experience, and career focus. This creates a strong first impression.',
                'priority': 2,
                'type': 'suggestion'
            })

        return tips

    def _analyze_content_quality(self, text: str) -> List[Dict]:
        """Analyze the quality of resume content."""
        tips = []
        text_lower = text.lower()

        # Check for weak phrases
        found_weak = [p for p in self.WEAK_PHRASES if p in text_lower]
        if found_weak:
            examples = ', '.join([f'"{p}"' for p in found_weak[:3]])
            tips.append({
                'category': 'content',
                'title': 'Replace Weak Phrases with Action Verbs',
                'description': f'Your resume uses passive phrases like {examples}. Replace with strong action verbs such as "led," "developed," "achieved," or "implemented" to create more impact.',
                'priority': 1,
                'type': 'suggestion'
            })

        # Check for first-person pronouns
        pronoun_count = len(re.findall(r'\b(I|me|my|mine|myself)\b', text))
        if pronoun_count > 5:
            tips.append({
                'category': 'content',
                'title': 'Remove First-Person Pronouns',
                'description': f'Found {pronoun_count} first-person pronouns. Professional resumes should avoid "I," "me," "my." Instead of "I managed a team," write "Managed cross-functional team of 8."',
                'priority': 2,
                'type': 'suggestion'
            })

        # Check for spelling indicators (repeated chars, common mistakes)
        if re.search(r'teh |recieve|managment|experiance|succesful', text_lower):
            tips.append({
                'category': 'content',
                'title': 'Proofread for Spelling Errors',
                'description': 'Potential spelling errors detected. Run your resume through a spell checker. A single typo can cost you an interview — 77% of hiring managers reject resumes with errors.',
                'priority': 1,
                'type': 'warning'
            })

        return tips

    def _analyze_language(self, text: str, fraud_results: Dict) -> List[Dict]:
        """Analyze language quality based on fraud detection insights."""
        tips = []
        component_scores = fraud_results.get('component_scores', {})
        language_score = component_scores.get('language_score', 0)

        # Exaggeration detection
        if language_score > 40:
            tips.append({
                'category': 'language',
                'title': 'Tone Down Exaggerated Language',
                'description': 'Your resume uses language that may appear exaggerated. Instead of vague superlatives like "best," "greatest," or "expert," use specific achievements with numbers: "Increased sales by 35% in Q3 2024."',
                'priority': 1,
                'type': 'warning'
            })

        # Buzzword overuse
        buzzwords = ['synergy', 'leverage', 'innovative', 'dynamic', 'passionate',
                     'self-starter', 'team player', 'go-getter', 'results-driven',
                     'detail-oriented', 'hard-working']
        found_buzzwords = [b for b in buzzwords if b in text.lower()]
        if len(found_buzzwords) > 2:
            tips.append({
                'category': 'language',
                'title': 'Reduce Overused Buzzwords',
                'description': f'Found cliché buzzwords: {", ".join(found_buzzwords[:4])}. Recruiters see these thousands of times. Replace with concrete examples that demonstrate these qualities instead.',
                'priority': 2,
                'type': 'suggestion'
            })

        # Jargon balance
        technical_terms = len(re.findall(r'\b[A-Z]{2,}\b', text))
        if technical_terms > 20:
            tips.append({
                'category': 'language',
                'title': 'Balance Technical Jargon',
                'description': 'Your resume is heavy on acronyms and technical jargon. While technical depth is important, ensure non-technical recruiters can also understand your impact. Spell out important acronyms on first use.',
                'priority': 3,
                'type': 'suggestion'
            })

        return tips

    def _analyze_skills(self, text: str) -> List[Dict]:
        """Analyze skills section quality."""
        tips = []
        text_lower = text.lower()

        # Check for skills categorization
        skills_section = re.search(r'(?i)skills?(.*?)(?=\n\n|\Z|(?:experience|education|project))',
                                   text, re.DOTALL)

        if skills_section:
            skills_text = skills_section.group(1)

            # Check if skills are categorized
            if not re.search(r'(?i)(programming|technical|soft\s*skills|tools|frameworks|languages)', skills_text):
                tips.append({
                    'category': 'skills',
                    'title': 'Categorize Your Skills',
                    'description': 'Group your skills into categories like "Programming Languages," "Frameworks & Tools," "Cloud & DevOps," and "Soft Skills." This improves readability and ATS parsing.',
                    'priority': 2,
                    'type': 'suggestion'
                })

            # Check for proficiency levels
            skill_count = len(re.findall(r'[,;]', skills_text)) + 1
            if skill_count > 15:
                tips.append({
                    'category': 'skills',
                    'title': 'Prioritize Relevant Skills',
                    'description': f'You list many skills ({skill_count}+). Focus on the 10-15 most relevant to your target role. Tailor this section for each job application.',
                    'priority': 3,
                    'type': 'suggestion'
                })
        else:
            tips.append({
                'category': 'skills',
                'title': 'Add a Dedicated Skills Section',
                'description': 'No clear skills section found. Add a well-organized skills section near the top of your resume to quickly show recruiters your technical capabilities.',
                'priority': 1,
                'type': 'warning'
            })

        return tips

    def _analyze_experience(self, text: str) -> List[Dict]:
        """Analyze work experience quality."""
        tips = []
        component_scores_timeline = 0

        # Check for bullet points
        bullet_count = len(re.findall(r'(?m)^[\s]*[-•●▪►]', text))
        if bullet_count < 3:
            tips.append({
                'category': 'experience',
                'title': 'Use Bullet Points for Experience',
                'description': 'Your resume lacks bullet points. Use 3-5 concise bullet points per role, each starting with a strong action verb. This improves readability and highlights key contributions.',
                'priority': 1,
                'type': 'suggestion'
            })

        # Check for date formats
        dates = re.findall(r'\b(19|20)\d{2}\b', text)
        if len(dates) < 2:
            tips.append({
                'category': 'experience',
                'title': 'Include Clear Date Ranges',
                'description': 'Add clear date ranges (e.g., "Jan 2022 - Present") for each position. This helps recruiters understand your career timeline and tenure.',
                'priority': 2,
                'type': 'suggestion'
            })

        # Check for role descriptions
        if not re.search(r'(?i)(managed|led|developed|created|built|designed|implemented)', text):
            tips.append({
                'category': 'experience',
                'title': 'Start Bullet Points with Action Verbs',
                'description': 'Begin each bullet point with a powerful action verb. For example: "Developed automated testing framework reducing QA time by 40%" instead of "Was responsible for testing."',
                'priority': 1,
                'type': 'suggestion'
            })

        return tips

    def _analyze_education(self, text: str) -> List[Dict]:
        """Analyze education section."""
        tips = []
        text_lower = text.lower()

        # Check for GPA mention (if student/recent grad)
        has_education = bool(re.search(r'(?i)education|university|college|degree', text))
        has_gpa = bool(re.search(r'(?i)(gpa|cgpa|grade\s*point)', text))

        if has_education and not has_gpa:
            # Check if likely recent graduate (lots of education, less experience)
            exp_section = re.search(r'(?i)experience', text)
            if not exp_section or text.lower().index('education') < text.lower().find('experience') if exp_section else True:
                tips.append({
                    'category': 'education',
                    'title': 'Consider Adding Your GPA',
                    'description': 'If your GPA is 3.0/4.0 or above (or equivalent), include it. For recent graduates, a strong GPA helps demonstrate academic excellence.',
                    'priority': 3,
                    'type': 'suggestion'
                })

        # Check for relevant coursework
        if has_education and not re.search(r'(?i)(coursework|courses|relevant\s*course)', text):
            tips.append({
                'category': 'education',
                'title': 'Add Relevant Coursework',
                'description': 'Include 3-5 relevant courses, especially if you\'re a recent graduate. This shows targeted knowledge in your field.',
                'priority': 4,
                'type': 'suggestion'
            })

        return tips

    def _analyze_impact(self, text: str) -> List[Dict]:
        """Analyze quantifiable impact and achievements."""
        tips = []

        # Count numbers/metrics
        numbers = re.findall(r'\b\d+[%$KkMm]?\b', text)
        quantified_achievements = len(re.findall(r'\d+\s*%|\$\s*\d+|\d+[KkMm]\b', text))

        if quantified_achievements < 2:
            tips.append({
                'category': 'impact',
                'title': 'Quantify Your Achievements',
                'description': 'Your resume lacks quantifiable metrics. Add numbers wherever possible: "Managed team of 12," "Reduced costs by 25%," "Increased user engagement by 3x." Numbers make your impact concrete and memorable.',
                'priority': 1,
                'type': 'warning'
            })

        # Check for result-oriented language
        results_pattern = r'(?i)(increased|decreased|improved|reduced|saved|generated|grew|boosted|delivered|achieved)'
        result_mentions = len(re.findall(results_pattern, text))

        if result_mentions < 2:
            tips.append({
                'category': 'impact',
                'title': 'Focus on Results, Not Just Duties',
                'description': 'Your resume describes what you did, but not the outcomes. Use the formula: "Action Verb + Task + Quantifiable Result." Example: "Automated data pipeline, reducing processing time from 4 hours to 15 minutes."',
                'priority': 1,
                'type': 'suggestion'
            })

        return tips

    def _analyze_ats_readiness(self, text: str) -> List[Dict]:
        """Analyze ATS (Applicant Tracking System) optimization."""
        tips = []

        # Check for standard section headers
        standard_headers = ['experience', 'education', 'skills', 'summary']
        creative_headers = re.findall(r'(?i)(my journey|where i\'ve been|what i know|my story)', text)
        if creative_headers:
            tips.append({
                'category': 'ats',
                'title': 'Use Standard Section Headers',
                'description': 'ATS software may not recognize creative headers like "My Journey." Use standard headers: "Professional Experience," "Education," "Technical Skills," "Professional Summary."',
                'priority': 1,
                'type': 'warning'
            })

        # Check for special characters that might break ATS
        special_chars = len(re.findall(r'[★☆►▶◆◇■□●○]', text))
        if special_chars > 5:
            tips.append({
                'category': 'ats',
                'title': 'Minimize Special Characters',
                'description': 'Excessive special characters (★, ►, ◆) can confuse ATS parsers. Use standard bullet points (•) and simple formatting to ensure your resume is parsed correctly.',
                'priority': 2,
                'type': 'suggestion'
            })

        # Check for file format hint
        if not re.search(r'(?i)(linkedin|github|portfolio|website)', text):
            tips.append({
                'category': 'ats',
                'title': 'Add Professional Online Presence',
                'description': 'Include links to your LinkedIn profile, GitHub, or portfolio website. 87% of recruiters check LinkedIn profiles, and online presence strengthens credibility.',
                'priority': 3,
                'type': 'suggestion'
            })

        return tips

    def _analyze_professional_branding(self, text: str, fraud_results: Dict) -> List[Dict]:
        """Analyze professional branding and presentation."""
        tips = []
        fraud_score = fraud_results.get('fraud_score', 0)
        risk_category = fraud_results.get('risk_category', 'Low Risk')

        # Credibility tips based on fraud analysis
        if fraud_score > 40:
            tips.append({
                'category': 'professional',
                'title': 'Improve Resume Credibility',
                'description': 'Our AI analysis flags some credibility concerns. Ensure all claims are verifiable, dates are accurate, and qualifications are genuine. Employers increasingly use AI to verify resumes.',
                'priority': 1,
                'type': 'warning'
            })

        # Check for certifications
        if not re.search(r'(?i)(certification|certified|certificate|license)', text):
            tips.append({
                'category': 'professional',
                'title': 'Add Relevant Certifications',
                'description': 'Consider adding industry certifications relevant to your field (AWS, Google Cloud, PMP, Scrum Master, etc.). Certifications can increase your interview chances by up to 40%.',
                'priority': 3,
                'type': 'suggestion'
            })

        # Check for projects section
        if not re.search(r'(?i)(projects?|portfolio|case\s*stud)', text):
            tips.append({
                'category': 'professional',
                'title': 'Showcase Key Projects',
                'description': 'Add a "Key Projects" section highlighting 2-3 impactful projects with brief descriptions of the problem, your approach, and measurable results. This is especially valuable for technical roles.',
                'priority': 2,
                'type': 'suggestion'
            })

        return tips

    def _identify_strengths(self, text: str, fraud_results: Dict) -> List[str]:
        """Identify positive aspects of the resume."""
        strengths = []
        fraud_score = fraud_results.get('fraud_score', 50)
        component_scores = fraud_results.get('component_scores', {})

        if fraud_score < 30:
            strengths.append('✅ Resume appears highly authentic and genuine')

        if component_scores.get('language_score', 100) < 30:
            strengths.append('✅ Professional and appropriate language tone')

        if component_scores.get('timeline_score', 100) < 30:
            strengths.append('✅ Consistent and logical career timeline')

        if component_scores.get('credential_score', 100) < 30:
            strengths.append('✅ Credentials appear verifiable and legitimate')

        # Check for quantifiable achievements
        if len(re.findall(r'\d+\s*%|\$\s*\d+', text)) >= 3:
            strengths.append('✅ Good use of quantifiable metrics and data')

        # Check for action verbs
        action_count = sum(1 for v in self.STRONG_ACTION_VERBS if v in text.lower())
        if action_count >= 3:
            strengths.append('✅ Strong use of action verbs')

        # Check for contact info
        if re.search(r'[\w.-]+@[\w.-]+\.\w+', text):
            strengths.append('✅ Contact information is clearly provided')

        if re.search(r'(?i)linkedin|github', text):
            strengths.append('✅ Online professional profiles included')

        if not strengths:
            strengths.append('✅ Your resume has been analyzed — follow the tips below to strengthen it!')

        return strengths

    def _calculate_improvement_score(self, text: str, fraud_results: Dict, tips: List[Dict]) -> int:
        """
        Calculate an overall resume quality score (0-100).
        Higher = better resume quality (fewer improvements needed).
        """
        score = 100

        # Deduct for each tip based on priority
        for tip in tips:
            priority = tip.get('priority', 3)
            tip_type = tip.get('type', 'suggestion')

            if tip_type == 'warning':
                score -= (6 - min(priority, 5)) * 3  # Warnings deduct more
            else:
                score -= (6 - min(priority, 5)) * 2  # Suggestions deduct less

        # Bonus for low fraud score (authentic resume)
        fraud_score = fraud_results.get('fraud_score', 50)
        if fraud_score < 30:
            score += 10
        elif fraud_score > 60:
            score -= 10

        # Clamp between 10 and 100
        score = max(10, min(100, score))

        return score

    def _generate_summary(self, improvement_score: int, tips: List[Dict]) -> str:
        """Generate a natural language summary of the resume analysis."""
        warning_count = sum(1 for t in tips if t.get('type') == 'warning')
        suggestion_count = sum(1 for t in tips if t.get('type') == 'suggestion')

        if improvement_score >= 85:
            return f"Excellent resume! Your resume is well-structured with only {len(tips)} minor suggestions for improvement. Focus on the tips below to make it even stronger."
        elif improvement_score >= 65:
            return f"Good foundation! Your resume has {suggestion_count} suggestions and {warning_count} areas needing attention. Addressing these could significantly boost your interview callback rate."
        elif improvement_score >= 45:
            return f"Room for improvement. We found {len(tips)} areas to work on, including {warning_count} important issues. Implementing these tips could dramatically improve your resume's effectiveness."
        else:
            return f"Your resume needs significant improvements. We've identified {len(tips)} actionable tips to help you stand out. Start with the high-priority items for the biggest impact."


# Standalone test
if __name__ == "__main__":
    generator = ResumeTipGenerator()

    sample_text = """
    John Doe
    john.doe@gmail.com

    I am a passionate and dynamic self-starter with extensive experience.
    I was responsible for managing projects and I worked on various tasks.

    EXPERIENCE
    Software Developer - ABC Corp (2020 - Present)
    - Was responsible for writing code
    - Helped with testing
    - Participated in meetings

    EDUCATION
    Bachelor of Computer Science - State University (2016 - 2020)

    SKILLS
    Python, Java, C++, SQL, HTML, CSS, JavaScript, React, Node.js,
    Docker, AWS, Azure, Machine Learning, Deep Learning, NLP
    """

    sample_fraud_results = {
        'fraud_score': 25.0,
        'risk_category': 'Low Risk',
        'ml_confidence': 75.0,
        'component_scores': {
            'timeline_score': 10.0,
            'credential_score': 0.0,
            'language_score': 35.0,
            'anomaly_score': 15.0,
        },
        'red_flags': [],
        'recommendations': []
    }

    tips_result = generator.generate_tips(sample_text, sample_fraud_results)

    print(f"\n{'='*60}")
    print(f"📊 Resume Quality Score: {tips_result['improvement_score']}/100")
    print(f"📝 Total Tips: {tips_result['total_tips']}")
    print(f"\n📋 Summary: {tips_result['summary']}")

    print(f"\n💪 Strengths:")
    for s in tips_result['strengths']:
        print(f"  {s}")

    print(f"\n🎯 Top 3 Priority Tips:")
    for i, tip in enumerate(tips_result['top_3_tips'], 1):
        print(f"  {i}. [{tip['category']}] {tip['title']}")
        print(f"     {tip['description']}")

    print(f"\n📂 All Tips by Category:")
    for cat_key, cat_data in tips_result['categorized_tips'].items():
        print(f"\n  {cat_data['icon']} {cat_data['label']}:")
        for tip in cat_data['tips']:
            marker = '⚠️' if tip['type'] == 'warning' else '💡'
            print(f"    {marker} {tip['title']}")
            print(f"       {tip['description']}")
