import os
import re
from typing import Dict, List, Optional
# Optional python-docx import
try:
    from docx import Document  # type: ignore[reportMissingImports]
except ImportError:
    Document = None
import PyPDF2
import io

class ResumeParser:
    def __init__(self):
        self.skills_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'fastapi',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'github', 'gitlab', 'jenkins', 'ci/cd',
            'machine learning', 'ai', 'data science', 'pandas', 'numpy', 'tensorflow', 'pytorch',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum'
        ]
        
        self.experience_keywords = [
            'years', 'experience', 'senior', 'junior', 'lead', 'manager', 'director',
            'engineer', 'developer', 'analyst', 'consultant', 'architect'
        ]

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text() or ""
                text += extracted + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        if Document is None:
            raise Exception("python-docx not installed")
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills

    def extract_experience(self, text: str) -> Optional[str]:
        """Extract years of experience from resume text"""
        # Look for patterns like "5 years", "3+ years", etc.
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*in',
            r'(\d+)\+?\s*years?\s*working'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        
        return None

    def extract_education(self, text: str) -> List[str]:
        """Extract education information"""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma',
            'university', 'college', 'institute', 'school'
        ]
        
        education = []
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                education.append(line.strip())
        
        return education

    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information"""
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        return contact

    def parse_resume(self, file_content: bytes, filename: str) -> Dict:
        """Parse resume and extract structured information"""
        try:
            # Extract text based on file type
            if filename.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(file_content)
            elif filename.lower().endswith('.docx'):
                text = self.extract_text_from_docx(file_content)
            else:
                raise Exception("Unsupported file format")
            
            # Extract information
            skills = self.extract_skills(text)
            experience = self.extract_experience(text)
            education = self.extract_education(text)
            contact = self.extract_contact_info(text)
            
            return {
                'filename': filename,
                'skills': skills,
                'experience_years': experience,
                'education': education,
                'contact': contact,
                'text_length': len(text),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'filename': filename,
                'error': str(e),
                'status': 'error'
            }

# Example usage
if __name__ == "__main__":
    parser = ResumeParser()
    print("Resume parser ready!")
