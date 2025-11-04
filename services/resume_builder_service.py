"""
AI Resume Builder & Optimizer Service
Auto-generates optimized resumes with ATS scoring and job matching
"""

import openai
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from extensions import db
from models import User
from models_extended import AIConversation
import json
import re

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')


class ResumeBuilderService:
    """AI-powered resume generation and optimization"""
    
    def __init__(self):
        self.model = "gpt-4"
    
    # ============================================================
    # RESUME GENERATION
    # ============================================================
    
    def generate_resume(
        self,
        user_id: int,
        format_type: str = "modern",
        target_role: Optional[str] = None
    ) -> Dict:
        """
        Generate complete resume from user profile
        
        Args:
            user_id: User ID
            format_type: modern, classic, technical, creative
            target_role: Optional job role to tailor resume
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            # Gather user data
            profile_data = self._extract_profile_data(user)
            
            # Generate resume content with AI
            prompt = self._build_resume_prompt(profile_data, format_type, target_role)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer specializing in ATS-optimized resumes for university students and recent graduates."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            resume_content = response.choices[0].message['content']
            
            # Parse and structure
            structured_resume = self._parse_resume_content(resume_content, profile_data)
            
            # Generate HTML
            html_resume = self._generate_html_resume(structured_resume, format_type)
            
            logger.info(f"Generated resume for user {user_id}")
            
            return {
                "success": True,
                "structured_resume": structured_resume,
                "html": html_resume,
                "pdf_ready": True,
                "format": format_type
            }
            
        except Exception as e:
            logger.error(f"Resume generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_profile_data(self, user: User) -> Dict:
        """Extract all relevant data from user profile"""
        return {
            "personal": {
                "name": user.full_name,
                "email": user.email,
                "phone": user.phone or "",
                "linkedin": user.linkedin_url or "",
                "github": user.github_url or "",
                "portfolio": user.portfolio_url or "",
                "location": "Pittsburg, KS"  # Default
            },
            "education": {
                "school": "Pittsburg State University",
                "major": user.major or "",
                "graduation_year": user.graduation_year or "",
                "gpa": user.gpa or ""
            },
            "summary": user.bio or "",
            "skills": user.skills or [],
            "interests": user.interests or [],
            "experience": [],  # Would pull from separate Experience model if exists
            "projects": [],     # Would pull from Portfolio model if exists
            "certifications": []  # Would pull from UserCredential model
        }
    
    def _build_resume_prompt(
        self,
        profile_data: Dict,
        format_type: str,
        target_role: Optional[str]
    ) -> str:
        """Build AI prompt for resume generation"""
        
        target_text = f" tailored for a {target_role} position" if target_role else ""
        
        return f"""
Generate a professional resume{target_text} for this candidate:

PERSONAL INFO:
- Name: {profile_data['personal']['name']}
- Email: {profile_data['personal']['email']}
- Phone: {profile_data['personal']['phone']}
- LinkedIn: {profile_data['personal']['linkedin']}
- GitHub: {profile_data['personal']['github']}

EDUCATION:
- {profile_data['education']['school']}
- Major: {profile_data['education']['major']}
- Graduation: {profile_data['education']['graduation_year']}
- GPA: {profile_data['education']['gpa']}

SKILLS: {', '.join(profile_data['skills'])}

CURRENT BIO: {profile_data['summary']}

Please generate:
1. A compelling professional summary (2-3 sentences)
2. Organized skills section grouped by category
3. Suggested experience descriptions (if any work history mentioned in bio)
4. Projects section (if applicable)
5. Additional sections as relevant

Format as structured JSON with sections: summary, skills, experience, education, projects.
Make it ATS-friendly and keyword-rich.
"""
    
    def _parse_resume_content(self, content: str, profile_data: Dict) -> Dict:
        """Parse AI-generated content into structured format"""
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                parsed = json.loads(content)
            else:
                # Fallback: extract sections manually
                parsed = {
                    "summary": self._extract_section(content, "summary", "professional summary"),
                    "skills": profile_data['skills'],
                    "experience": [],
                    "education": [profile_data['education']],
                    "projects": []
                }
            
            # Ensure required fields
            parsed['personal'] = profile_data['personal']
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Resume parsing fallback: {e}")
            return {
                "personal": profile_data['personal'],
                "summary": profile_data['summary'],
                "skills": profile_data['skills'],
                "education": [profile_data['education']],
                "experience": [],
                "projects": []
            }
    
    def _extract_section(self, content: str, *headers: str) -> str:
        """Extract section by header"""
        for header in headers:
            pattern = re.compile(f"{header}:?\\s*(.+?)(?=\\n[A-Z]|$)", re.IGNORECASE | re.DOTALL)
            match = pattern.search(content)
            if match:
                return match.group(1).strip()
        return ""
    
    # ============================================================
    # ATS OPTIMIZATION
    # ============================================================
    
    def analyze_ats_score(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict:
        """
        Analyze ATS compatibility and provide score
        
        Returns score 0-100 with recommendations
        """
        try:
            score = 0
            recommendations = []
            keyword_analysis = {}
            
            # Basic ATS checks
            checks = {
                "has_contact_info": bool(re.search(r'[\w\.-]+@[\w\.-]+', resume_text)),
                "no_tables": '<table>' not in resume_text.lower(),
                "no_images": '<img' not in resume_text.lower(),
                "has_skills": 'skill' in resume_text.lower(),
                "has_experience": any(word in resume_text.lower() for word in ['experience', 'worked', 'developed']),
                "proper_formatting": len(resume_text.split('\n')) > 5,
                "keyword_density": len(resume_text.split()) > 200
            }
            
            # Calculate base score
            score = sum(1 for passed in checks.values() if passed) * 100 / len(checks)
            
            # Job description matching
            if job_description:
                keyword_match = self._analyze_keywords(resume_text, job_description)
                keyword_analysis = keyword_match
                score = (score + keyword_match['match_percentage']) / 2
            
            # Generate recommendations
            if not checks['has_contact_info']:
                recommendations.append("Add clear contact information (email, phone)")
            if not checks['no_tables']:
                recommendations.append("Avoid tables - use simple text formatting")
            if not checks['has_skills']:
                recommendations.append("Add a dedicated skills section")
            if score < 60:
                recommendations.append("Increase keyword density with relevant industry terms")
            
            return {
                "score": round(score, 1),
                "checks": checks,
                "recommendations": recommendations,
                "keyword_analysis": keyword_analysis,
                "ats_friendly": score >= 70
            }
            
        except Exception as e:
            logger.error(f"ATS analysis error: {e}")
            return {"score": 0, "error": str(e)}
    
    def _analyze_keywords(self, resume: str, job_description: str) -> Dict:
        """Compare resume keywords with job description"""
        
        # Extract keywords (simple approach - could use NLP)
        def extract_keywords(text):
            # Remove common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                          'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 
                          'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
                          'would', 'could', 'should', 'may', 'might', 'must', 'can'}
            
            words = re.findall(r'\b[a-z]{3,}\b', text.lower())
            return [w for w in words if w not in common_words]
        
        resume_keywords = set(extract_keywords(resume))
        job_keywords = set(extract_keywords(job_description))
        
        matched = resume_keywords & job_keywords
        missing = job_keywords - resume_keywords
        
        match_percentage = (len(matched) / len(job_keywords) * 100) if job_keywords else 0
        
        return {
            "matched_keywords": list(matched)[:20],
            "missing_keywords": list(missing)[:20],
            "match_percentage": round(match_percentage, 1),
            "total_job_keywords": len(job_keywords),
            "matched_count": len(matched)
        }
    
    def optimize_for_job(
        self,
        user_id: int,
        job_description: str,
        job_title: str
    ) -> Dict:
        """
        Generate resume optimized for specific job
        
        Uses AI to tailor resume to job requirements
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            profile_data = self._extract_profile_data(user)
            
            # AI optimization prompt
            prompt = f"""
Given this candidate profile and job description, generate an optimized resume that:
1. Highlights relevant skills matching the job requirements
2. Rewords experience to align with job keywords
3. Adds relevant achievements
4. Maintains truthfulness while emphasizing relevant aspects

CANDIDATE PROFILE:
{json.dumps(profile_data, indent=2)}

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

Generate an optimized resume in JSON format with sections: summary, skills, experience, education, achievements.
Focus on ATS keywords and quantifiable results.
"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume optimizer specializing in ATS optimization and keyword matching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            optimized_content = response.choices[0].message['content']
            structured_resume = self._parse_resume_content(optimized_content, profile_data)
            
            # Generate optimized HTML
            html_resume = self._generate_html_resume(structured_resume, "modern")
            
            # Score it
            ats_score = self.analyze_ats_score(
                str(structured_resume),
                job_description
            )
            
            logger.info(f"Generated optimized resume for user {user_id}, job: {job_title}")
            
            return {
                "success": True,
                "structured_resume": structured_resume,
                "html": html_resume,
                "ats_score": ats_score,
                "optimized_for": job_title
            }
            
        except Exception as e:
            logger.error(f"Resume optimization error: {e}")
            return {"success": False, "error": str(e)}
    
    # ============================================================
    # RESUME FORMATTING
    # ============================================================
    
    def _generate_html_resume(self, resume_data: Dict, format_type: str) -> str:
        """Generate HTML resume from structured data"""
        
        personal = resume_data.get('personal', {})
        education = resume_data.get('education', [{}])[0] if resume_data.get('education') else {}
        
        # Modern format template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Resume - {personal.get('name', 'Resume')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 850px; margin: 0 auto; padding: 40px; background: white; }}
        .header {{ border-bottom: 3px solid #8B0000; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #8B0000; font-size: 32px; margin-bottom: 10px; }}
        .contact {{ display: flex; flex-wrap: wrap; gap: 15px; color: #666; font-size: 14px; }}
        .contact a {{ color: #8B0000; text-decoration: none; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{ color: #8B0000; font-size: 20px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid #FFD700; padding-bottom: 5px; }}
        .summary {{ font-size: 15px; line-height: 1.8; color: #555; }}
        .skills {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .skill-tag {{ background: #8B0000; color: white; padding: 6px 12px; border-radius: 4px; font-size: 13px; }}
        .experience-item {{ margin-bottom: 20px; }}
        .experience-title {{ font-weight: bold; font-size: 16px; color: #333; }}
        .experience-details {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .experience-description {{ margin-left: 20px; }}
        ul {{ margin-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        @media print {{ body {{ padding: 0; }} .container {{ padding: 20px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{personal.get('name', 'Your Name')}</h1>
            <div class="contact">
                <span>📧 {personal.get('email', '')}</span>
                <span>📱 {personal.get('phone', '')}</span>
                {f'<a href="{personal.get("linkedin", "")}">🔗 LinkedIn</a>' if personal.get('linkedin') else ''}
                {f'<a href="{personal.get("github", "")}">💻 GitHub</a>' if personal.get('github') else ''}
            </div>
        </div>
        
        {f'''
        <div class="section">
            <div class="section-title">Professional Summary</div>
            <div class="summary">{resume_data.get('summary', '')}</div>
        </div>
        ''' if resume_data.get('summary') else ''}
        
        {f'''
        <div class="section">
            <div class="section-title">Skills</div>
            <div class="skills">
                {''.join(f'<span class="skill-tag">{skill}</span>' for skill in resume_data.get('skills', []))}
            </div>
        </div>
        ''' if resume_data.get('skills') else ''}
        
        <div class="section">
            <div class="section-title">Education</div>
            <div class="experience-item">
                <div class="experience-title">{education.get('school', 'Pittsburg State University')}</div>
                <div class="experience-details">
                    {education.get('major', '')} | Graduation: {education.get('graduation_year', '')} | GPA: {education.get('gpa', '')}
                </div>
            </div>
        </div>
        
        {f'''
        <div class="section">
            <div class="section-title">Experience</div>
            {''.join(self._format_experience_item(exp) for exp in resume_data.get('experience', []))}
        </div>
        ''' if resume_data.get('experience') else ''}
        
        {f'''
        <div class="section">
            <div class="section-title">Projects</div>
            {''.join(self._format_project_item(proj) for proj in resume_data.get('projects', []))}
        </div>
        ''' if resume_data.get('projects') else ''}
    </div>
</body>
</html>
"""
        
        return html
    
    def _format_experience_item(self, exp: Dict) -> str:
        """Format single experience item"""
        return f"""
        <div class="experience-item">
            <div class="experience-title">{exp.get('title', '')}</div>
            <div class="experience-details">{exp.get('company', '')} | {exp.get('dates', '')}</div>
            <div class="experience-description">
                <ul>
                    {''.join(f'<li>{item}</li>' for item in exp.get('bullets', []))}
                </ul>
            </div>
        </div>
        """
    
    def _format_project_item(self, proj: Dict) -> str:
        """Format single project item"""
        return f"""
        <div class="experience-item">
            <div class="experience-title">{proj.get('name', '')}</div>
            <div class="experience-description">{proj.get('description', '')}</div>
        </div>
        """
    
    # ============================================================
    # COVER LETTER GENERATION
    # ============================================================
    
    def generate_cover_letter(
        self,
        user_id: int,
        company_name: str,
        job_title: str,
        job_description: Optional[str] = None
    ) -> Dict:
        """Generate personalized cover letter"""
        
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}
            
            profile_data = self._extract_profile_data(user)
            
            prompt = f"""
Write a professional cover letter for:

CANDIDATE: {profile_data['personal']['name']}
MAJOR: {profile_data['education']['major']}
SCHOOL: {profile_data['education']['school']}
SKILLS: {', '.join(profile_data['skills'][:10])}

APPLYING TO:
Company: {company_name}
Position: {job_title}
{f"Job Description: {job_description[:500]}" if job_description else ""}

Write a compelling 3-paragraph cover letter that:
1. Shows enthusiasm for the role and company
2. Highlights relevant skills and experiences
3. Explains why they're a great fit
4. Closes with a call to action

Keep it professional, concise, and personalized.
"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert career coach specializing in cover letters."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            cover_letter = response.choices[0].message['content']
            
            logger.info(f"Generated cover letter for user {user_id}, company: {company_name}")
            
            return {
                "success": True,
                "cover_letter": cover_letter,
                "company": company_name,
                "position": job_title
            }
            
        except Exception as e:
            logger.error(f"Cover letter generation error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_resume_builder_service = None

def get_resume_builder_service() -> ResumeBuilderService:
    """Get or create ResumeBuilderService singleton"""
    global _resume_builder_service
    if _resume_builder_service is None:
        _resume_builder_service = ResumeBuilderService()
    return _resume_builder_service
