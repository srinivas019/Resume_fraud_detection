"""
Timeline Analyzer - Detects timeline anomalies and inconsistencies
"""

from datetime import datetime
from dateutil import parser
from typing import List, Dict, Tuple
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimelineAnalyzer:
    """Analyze resume timelines for fraud indicators"""
    
    def __init__(self):
        self.date_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y',
            '%B %Y', '%b %Y', '%Y'
        ]
    
    def analyze_timeline(self, education: List[Dict], experience: List[Dict]) -> Dict:
        """
        Analyze complete timeline for anomalies
        
        Args:
            education: List of education entries
            experience: List of work experience entries
            
        Returns:
            Dictionary with timeline analysis results
        """
        results = {
            'overlapping_employment': [],
            'education_work_overlap': [],
            'timeline_gaps': [],
            'unrealistic_progression': [],
            'date_inconsistencies': [],
            'total_anomalies': 0,
            'anomaly_score': 0.0,
        }
        
        # Parse all dates
        education_timeline = self._parse_education_timeline(education)
        experience_timeline = self._parse_experience_timeline(experience)
        
        # Check for overlapping employment
        employment_overlaps = self._check_employment_overlaps(experience_timeline)
        results['overlapping_employment'] = employment_overlaps
        
        # Check for education-work overlaps
        edu_work_overlaps = self._check_education_work_overlap(
            education_timeline, experience_timeline
        )
        results['education_work_overlap'] = edu_work_overlaps
        
        # Check for unrealistic career progression
        progression_issues = self._check_career_progression(experience_timeline)
        results['unrealistic_progression'] = progression_issues
        
        # Check for timeline gaps
        gaps = self._check_timeline_gaps(experience_timeline)
        results['timeline_gaps'] = gaps
        
        # Calculate total anomalies and score
        total_anomalies = (
            len(employment_overlaps) +
            len(edu_work_overlaps) +
            len(progression_issues) +
            (1 if gaps['suspicious_gaps'] > 0 else 0)
        )
        
        results['total_anomalies'] = total_anomalies
        results['anomaly_score'] = min(total_anomalies * 15, 100)  # Max 100
        
        return results
    
    def _parse_date(self, date_string: str) -> datetime:
        """
        Parse date string to datetime object
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_string or date_string.lower() in ['present', 'current', 'now']:
            return datetime.now()
        
        # Clean the date string
        date_string = date_string.strip()
        
        # Try dateutil parser (flexible)
        try:
            return parser.parse(date_string, fuzzy=True)
        except:
            pass
        
        # Try predefined formats
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except:
                continue
        
        # Try to extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
        if year_match:
            year = int(year_match.group(0))
            return datetime(year, 1, 1)
        
        return None
    
    def _parse_education_timeline(self, education: List[Dict]) -> List[Dict]:
        """Parse education timeline"""
        timeline = []
        
        for edu in education:
            start_date = self._parse_date(edu.get('start_date', ''))
            end_date = self._parse_date(edu.get('end_date', ''))
            
            if start_date and end_date:
                timeline.append({
                    'type': 'education',
                    'degree': edu.get('degree', 'Unknown'),
                    'institution': edu.get('university', 'Unknown'),
                    'start': start_date,
                    'end': end_date,
                })
        
        return sorted(timeline, key=lambda x: x['start'])
    
    def _parse_experience_timeline(self, experience: List[Dict]) -> List[Dict]:
        """Parse work experience timeline"""
        timeline = []
        
        for exp in experience:
            start_date = self._parse_date(exp.get('start_date', ''))
            end_date = self._parse_date(exp.get('end_date', ''))
            
            if start_date and end_date:
                timeline.append({
                    'type': 'experience',
                    'title': exp.get('title', 'Unknown'),
                    'company': exp.get('company', 'Unknown'),
                    'start': start_date,
                    'end': end_date,
                })
        
        return sorted(timeline, key=lambda x: x['start'])
    
    def _check_employment_overlaps(self, experience_timeline: List[Dict]) -> List[Dict]:
        """Check for overlapping employment periods"""
        overlaps = []
        
        for i in range(len(experience_timeline)):
            for j in range(i + 1, len(experience_timeline)):
                job1 = experience_timeline[i]
                job2 = experience_timeline[j]
                
                # Check if periods overlap
                if self._periods_overlap(
                    job1['start'], job1['end'],
                    job2['start'], job2['end']
                ):
                    overlap_days = self._calculate_overlap(
                        job1['start'], job1['end'],
                        job2['start'], job2['end']
                    )
                    
                    # Only flag if overlap is significant (> 30 days)
                    if overlap_days > 30:
                        overlaps.append({
                            'job1': f"{job1['title']} at {job1['company']}",
                            'job2': f"{job2['title']} at {job2['company']}",
                            'overlap_days': overlap_days,
                            'severity': 'high' if overlap_days > 180 else 'medium'
                        })
        
        return overlaps
    
    def _check_education_work_overlap(
        self, education_timeline: List[Dict], experience_timeline: List[Dict]
    ) -> List[Dict]:
        """Check for education-work overlaps (potential fraud indicator)"""
        overlaps = []
        
        for edu in education_timeline:
            for exp in experience_timeline:
                if self._periods_overlap(
                    edu['start'], edu['end'],
                    exp['start'], exp['end']
                ):
                    overlap_days = self._calculate_overlap(
                        edu['start'], edu['end'],
                        exp['start'], exp['end']
                    )
                    
                    # Full-time work during full-time education is suspicious
                    # (unless it's clearly an internship)
                    if overlap_days > 180:  # > 6 months
                        overlaps.append({
                            'education': f"{edu['degree']} at {edu['institution']}",
                            'work': f"{exp['title']} at {exp['company']}",
                            'overlap_days': overlap_days,
                            'suspicious': True
                        })
        
        return overlaps
    
    def _check_career_progression(self, experience_timeline: List[Dict]) -> List[Dict]:
        """Check for unrealistic career progression"""
        issues = []
        
        # Define career levels
        level_keywords = {
            'entry': ['junior', 'associate', 'trainee', 'intern', 'analyst'],
            'mid': ['engineer', 'developer', 'consultant', 'specialist'],
            'senior': ['senior', 'lead', 'principal', 'staff'],
            'executive': ['director', 'vp', 'cto', 'head', 'chief', 'executive']
        }
        
        def get_level(title: str) -> int:
            """Determine seniority level (0-3)"""
            title_lower = title.lower()
            if any(kw in title_lower for kw in level_keywords['executive']):
                return 3
            if any(kw in title_lower for kw in level_keywords['senior']):
                return 2
            if any(kw in title_lower for kw in level_keywords['mid']):
                return 1
            return 0
        
        for i in range(1, len(experience_timeline)):
            prev_job = experience_timeline[i - 1]
            curr_job = experience_timeline[i]
            
            prev_level = get_level(prev_job['title'])
            curr_level = get_level(curr_job['title'])
            
            # Check for unrealistic jumps (e.g., junior to VP)
            level_jump = curr_level - prev_level
            
            # Calculate years between jobs
            years_between = (curr_job['start'] - prev_job['start']).days / 365.25
            
            # Unrealistic: jumping 2+ levels in < 2 years
            if level_jump >= 2 and years_between < 2:
                issues.append({
                    'from': prev_job['title'],
                    'to': curr_job['title'],
                    'years': round(years_between, 1),
                    'reason': 'Unrealistic career jump in short time',
                    'severity': 'high'
                })
            
            # Unrealistic: reaching executive level in < 5 years total experience
            if curr_level == 3:  # Executive
                total_years = (curr_job['end'] - experience_timeline[0]['start']).days / 365.25
                if total_years < 5:
                    issues.append({
                        'title': curr_job['title'],
                        'total_experience': round(total_years, 1),
                        'reason': 'Executive role with minimal experience',
                        'severity': 'high'
                    })
        
        return issues
    
    def _check_timeline_gaps(self, experience_timeline: List[Dict]) -> Dict:
        """Check for suspicious gaps in employment"""
        gaps = {
            'total_gaps': 0,
            'suspicious_gaps': 0,
            'gap_details': []
        }
        
        if len(experience_timeline) < 2:
            return gaps
        
        for i in range(1, len(experience_timeline)):
            prev_job = experience_timeline[i - 1]
            curr_job = experience_timeline[i]
            
            gap_days = (curr_job['start'] - prev_job['end']).days
            
            if gap_days > 30:  # More than 1 month gap
                gaps['total_gaps'] += 1
                
                gap_months = gap_days / 30
                
                # Gaps > 6 months are suspicious
                if gap_months > 6:
                    gaps['suspicious_gaps'] += 1
                
                gaps['gap_details'].append({
                    'after': f"{prev_job['title']} at {prev_job['company']}",
                    'before': f"{curr_job['title']} at {curr_job['company']}",
                    'gap_months': round(gap_months, 1),
                    'suspicious': gap_months > 6
                })
        
        return gaps
    
    def _periods_overlap(
        self, start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> bool:
        """Check if two time periods overlap"""
        return start1 < end2 and start2 < end1
    
    def _calculate_overlap(
        self, start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> int:
        """Calculate overlap duration in days"""
        latest_start = max(start1, start2)
        earliest_end = min(end1, end2)
        
        if latest_start < earliest_end:
            return (earliest_end - latest_start).days
        return 0


def main():
    """Test timeline analyzer"""
    
    # Sample data with overlaps
    education = [
        {
            'degree': 'Master of Science',
            'university': 'Stanford',
            'start_date': '2018-08-01',
            'end_date': '2020-05-01'
        }
    ]
    
    experience = [
        {
            'title': 'Software Engineer',
            'company': 'Company A',
            'start_date': '2019-06-01',  # Overlaps with Master's
            'end_date': '2021-03-01'
        },
        {
            'title': 'CTO',  # Unrealistic jump
            'company': 'Company B',
            'start_date': '2021-04-01',
            'end_date': '2023-12-01'
        }
    ]
    
    analyzer = TimelineAnalyzer()
    results = analyzer.analyze_timeline(education, experience)
    
    print("Timeline Analysis Results:")
    print("=" * 80)
    print(f"Total Anomalies: {results['total_anomalies']}")
    print(f"Anomaly Score: {results['anomaly_score']}/100")
    print(f"\nOverlapping Employment: {len(results['overlapping_employment'])}")
    print(f"Education-Work Overlaps: {len(results['education_work_overlap'])}")
    print(f"Career Progression Issues: {len(results['unrealistic_progression'])}")
    
    if results['education_work_overlap']:
        print("\nEducation-Work Overlaps:")
        for overlap in results['education_work_overlap']:
            print(f"  - {overlap}")


if __name__ == "__main__":
    main()
