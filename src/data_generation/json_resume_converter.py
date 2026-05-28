"""
JSON Resume Converter - Converts JSON Resume format to text for training
"""

import json
from pathlib import Path
from typing import Dict, List
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

import config


class JSONResumeConverter:
    """Convert JSON Resume format to plain text"""
    
    def __init__(self, json_resume_dir: Path):
        self.json_resume_dir = Path(json_resume_dir)
        self.output_dir = config.RAW_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_json_to_text(self, json_data: Dict) -> str:
        """Convert JSON resume data to formatted text"""
        
        text_lines = []
        
        # Basics
        if 'basics' in json_data:
            basics = json_data['basics']
            if 'name' in basics:
                text_lines.append(basics['name'])
            if 'email' in basics:
                text_lines.append(f"Email: {basics['email']}")
            if 'phone' in basics:
                text_lines.append(f"Phone: {basics['phone']}")
            if 'website' in basics or 'url' in basics:
                website = basics.get('website') or basics.get('url')
                text_lines.append(f"Website: {website}")
            
            # Location
            if 'location' in basics:
                loc = basics['location']
                location_parts = []
                for key in ['city', 'region', 'countryCode']:
                    if key in loc:
                        location_parts.append(loc[key])
                if location_parts:
                    text_lines.append("Location: " + ", ".join(location_parts))
            
            # Summary
            if 'summary' in basics:
                text_lines.append("\nPROFESSIONAL SUMMARY")
                text_lines.append(basics['summary'])
        
        # Work Experience
        if 'work' in json_data and json_data['work']:
            text_lines.append("\nWORK EXPERIENCE")
            for job in json_data['work']:
                if 'position' in job and 'name' in job:
                    text_lines.append(f"\n{job['position']} - {job['name']}")
                
                # Dates
                if 'startDate' in job:
                    end_date = job.get('endDate', 'Present')
                    text_lines.append(f"{job['startDate']} to {end_date}")
                
                # Summary
                if 'summary' in job:
                    text_lines.append(job['summary'])
                
                # Highlights
                if 'highlights' in job:
                    for highlight in job['highlights']:
                        text_lines.append(f"• {highlight}")
        
        # Education
        if 'education' in json_data and json_data['education']:
            text_lines.append("\nEDUCATION")
            for edu in json_data['education']:
                if 'studyType' in edu and 'area' in edu:
                    text_lines.append(f"\n{edu['studyType']} in {edu['area']}")
                elif 'studyType' in edu:
                    text_lines.append(f"\n{edu['studyType']}")
                
                # Institution
                if 'institution' in edu:
                    text_lines.append(f"{edu['institution']}")
                
                # Dates
                if 'startDate' in edu:
                    end_date = edu.get('endDate', 'Present')
                    text_lines.append(f"({edu['startDate']} - {end_date})")
                
                # GPA
                if 'gpa' in edu:
                    text_lines.append(f"GPA: {edu['gpa']}")
        
        # Skills
        if 'skills' in json_data and json_data['skills']:
            text_lines.append("\nSKILLS")
            all_skills = []
            for skill_group in json_data['skills']:
                if 'keywords' in skill_group:
                    all_skills.extend(skill_group['keywords'])
                elif 'name' in skill_group:
                    all_skills.append(skill_group['name'])
            text_lines.append(", ".join(all_skills))
        
        # Certifications / Awards
        if 'awards' in json_data and json_data['awards']:
            text_lines.append("\nCERTIFICATIONS & AWARDS")
            for award in json_data['awards']:
                if 'title' in award:
                    text_lines.append(f"• {award['title']}")
                    if 'date' in award:
                        text_lines.append(f"  Date: {award['date']}")
        
        # Publications
        if 'publications' in json_data and json_data['publications']:
            text_lines.append("\nPUBLICATIONS")
            for pub in json_data['publications']:
                if 'name' in pub:
                    text_lines.append(f"• {pub['name']}")
        
        # Languages
        if 'languages' in json_data and json_data['languages']:
            text_lines.append("\nLANGUAGES")
            langs = []
            for lang in json_data['languages']:
                if 'language' in lang:
                    fluency = lang.get('fluency', '')
                    langs.append(f"{lang['language']} ({fluency})" if fluency else lang['language'])
            text_lines.append(", ".join(langs))
        
        return "\n".join(text_lines)
    
    def convert_all(self) -> List[str]:
        """Convert all JSON resumes to text files"""
        
        json_files = list(self.json_resume_dir.glob("*.json"))
        converted_files = []
        
        print(f"Found {len(json_files)} JSON resume files")
        print(f"Converting to text format...")
        
        for i, json_file in enumerate(json_files, 1):
            try:
                # Read JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Convert to text
                text = self.convert_json_to_text(json_data)
                
                # Save as text file
                output_file = self.output_dir / f"{json_file.stem}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                converted_files.append(str(output_file))
                
                if i % 50 == 0:
                    print(f"  Converted {i}/{len(json_files)} files...")
            
            except Exception as e:
                print(f"Error converting {json_file.name}: {e}")
                continue
        
        print(f"\n✓ Successfully converted {len(converted_files)} resumes")
        print(f"  Output directory: {self.output_dir}")
        
        return converted_files


def main():
    """Main function"""
    # Path to JSON resumes
    json_resume_dir = Path("c:/Users/mamid/OneDrive/Desktop/resume_fraud/data/jsonresume-fake/resumes")
    
    if not json_resume_dir.exists():
        print(f"Error: Directory not found: {json_resume_dir}")
        print("Please ensure you've cloned the jsonresume-fake repository")
        return
    
    # Convert all resumes
    converter = JSONResumeConverter(json_resume_dir)
    converted_files = converter.convert_all()
    
    print(f"\n✓ Conversion complete!")
    print(f"  {len(converted_files)} real resumes ready for training")
    print(f"\nNext steps:")
    print(f"  1. These are all GENUINE resumes (label: 0)")
    print(f"  2. Run synthetic_resume_generator.py to create FRAUDULENT resumes (label: 1)")
    print(f"  3. Run train_models.py to train ML models on combined dataset")


if __name__ == "__main__":
    main()
