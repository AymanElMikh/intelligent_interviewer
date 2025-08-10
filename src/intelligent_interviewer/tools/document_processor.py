import PyPDF2
import docx
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger

class DocumentProcessorTools:
    """Tools for processing resumes, job descriptions, and other HR documents"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def extract_resume_skills(self, file_path: str) -> List[str]:
        """Extract skills from resume documents"""
        try:
            text = await self._extract_text_from_file(file_path)
            skills = self._parse_skills_from_text(text)
            return skills
        except Exception as e:
            self.logger.error(f"Error extracting resume skills: {str(e)}")
            return []
    
    async def analyze_job_description(self, job_desc_text: str) -> Dict[str, Any]:
        """Analyze job description to extract requirements"""
        return {
            "required_skills": self._extract_required_skills(job_desc_text),
            "preferred_skills": self._extract_preferred_skills(job_desc_text),
            "responsibilities": self._extract_responsibilities(job_desc_text),
            "qualifications": self._extract_qualifications(job_desc_text)
        }
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or Word documents"""
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text