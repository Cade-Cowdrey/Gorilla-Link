"""
OpenAI Utilities - AI-Powered Content Generation
Handles resume generation, optimization, cover letters, and more
"""

import openai
import os
from typing import Dict, List, Any, Optional
import json
import re


# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')


def generate_resume_content(section_type: str, context: Dict[str, Any]) -> str:
    """
    Generate resume section content using AI
    
    Args:
        section_type: Type of section (experience, education, skills, summary, etc.)
        context: User context and input data
    
    Returns:
        Generated content string
    """
    
    prompts = {
        'summary': f"""
Write a professional resume summary for a {context.get('user', {}).get('role', 'student')} 
majoring in {context.get('user', {}).get('major', 'their field')}.
Graduation year: {context.get('user', {}).get('graduation_year', 'upcoming')}.

Key points to include:
- {context.get('years_experience', '0')} years of experience
- Skills: {', '.join(context.get('skills', []))}
- Career goals: {context.get('career_goals', 'professional growth')}

Write 3-4 sentences that are compelling, specific, and achievement-focused.
""",
        
        'experience': f"""
Write a professional work experience entry for:

Job Title: {context.get('job_title', '')}
Company: {context.get('company', '')}
Duration: {context.get('duration', '')}
Responsibilities: {context.get('responsibilities', '')}
Achievements: {context.get('achievements', '')}

Format as bullet points. Start each bullet with a strong action verb.
Focus on quantifiable achievements and impact. 3-5 bullet points.
""",
        
        'education': f"""
Write an education section entry for:

Degree: {context.get('degree', '')}
Major: {context.get('major', '')}
Institution: {context.get('institution', 'Pittsburg State University')}
Graduation: {context.get('graduation_date', '')}
GPA: {context.get('gpa', '')}
Honors: {context.get('honors', '')}
Relevant Coursework: {context.get('coursework', '')}

Format professionally. Include relevant details that showcase academic achievement.
""",
        
        'skills': f"""
Organize these skills into professional categories:

Technical Skills: {', '.join(context.get('technical_skills', []))}
Soft Skills: {', '.join(context.get('soft_skills', []))}
Tools/Software: {', '.join(context.get('tools', []))}

Format as categorized bullet points. Prioritize most relevant skills for {context.get('target_role', 'the role')}.
""",
        
        'projects': f"""
Write a project description for:

Project Name: {context.get('project_name', '')}
Description: {context.get('description', '')}
Technologies: {context.get('technologies', '')}
Role: {context.get('role', '')}
Outcome: {context.get('outcome', '')}

Format as 2-3 bullet points highlighting technical skills, challenges solved, and impact.
""",
        
        'certifications': f"""
Format certification entries:

Certifications: {', '.join(context.get('certifications', []))}

Include issuing organization and date if provided: {context.get('details', '')}.
""",
        
        'volunteer': f"""
Write a volunteer experience entry for:

Organization: {context.get('organization', '')}
Role: {context.get('role', '')}
Duration: {context.get('duration', '')}
Activities: {context.get('activities', '')}
Impact: {context.get('impact', '')}

Format as 2-3 achievement-focused bullet points.
"""
    }
    
    prompt = prompts.get(section_type, f"Write professional resume content for the {section_type} section based on: {json.dumps(context)}")
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer and career coach. Write concise, achievement-focused, ATS-friendly resume content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message['content'].strip()
        
    except Exception as e:
        # Fallback to basic template
        return f"[Generated {section_type} content - configure OpenAI API key for AI generation]"


def optimize_resume_for_job(resume_content: Dict[str, Any], job: Any) -> Dict[str, Any]:
    """
    Optimize resume content for a specific job posting using AI
    
    Args:
        resume_content: Current resume content dictionary
        job: Job object with description and requirements
    
    Returns:
        Dictionary with optimized content and suggestions
    """
    
    job_description = f"""
Job Title: {job.title}
Company: {job.company.name if hasattr(job, 'company') else 'Company'}
Description: {job.description}
Requirements: {job.requirements if hasattr(job, 'requirements') else ''}
"""
    
    resume_text = json.dumps(resume_content, indent=2)
    
    prompt = f"""
Analyze this resume against the job posting and provide optimization suggestions.

RESUME:
{resume_text}

JOB POSTING:
{job_description}

Provide:
1. Keyword matches (what keywords from job description are in resume)
2. Missing keywords (important keywords from job that should be added)
3. Specific suggestions to tailor each section
4. Overall keyword match percentage
5. Priority changes to make

Format as JSON with keys: keyword_match, missing_keywords, suggestions, match_percentage, priority_changes
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert ATS optimization specialist and resume consultant. Analyze resumes and provide actionable optimization advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message['content'].strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(result_text)
        except:
            # Fallback to structured response
            result = {
                'keyword_match': 65,
                'content': result_text,
                'suggestions': ['Add more relevant keywords', 'Quantify achievements', 'Tailor experience section']
            }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'keyword_match': 0,
            'suggestions': ['Configure OpenAI API key for optimization features']
        }


def scan_resume_ats(resume_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan resume for ATS (Applicant Tracking System) compatibility
    
    Args:
        resume_content: Resume content dictionary
    
    Returns:
        Dictionary with ATS scan results and recommendations
    """
    
    resume_text = json.dumps(resume_content, indent=2)
    
    prompt = f"""
Perform an ATS (Applicant Tracking System) compatibility scan on this resume:

{resume_text}

Analyze:
1. ATS Score (0-100)
2. Formatting issues (tables, columns, graphics, special characters)
3. Section headers (are they standard?)
4. Contact information (is it parseable?)
5. Keyword optimization
6. File compatibility issues
7. Specific recommendations to improve ATS score

Provide detailed, actionable feedback. Format as JSON with keys:
score, issues, recommendations, keyword_density, formatting_score
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an ATS (Applicant Tracking System) expert. Analyze resumes for ATS compatibility and provide technical optimization advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message['content'].strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(result_text)
        except:
            # Fallback structure
            result = {
                'score': 75,
                'issues': ['Use standard section headers', 'Avoid tables and columns'],
                'recommendations': ['Use simple formatting', 'Include keywords naturally'],
                'keyword_density': 'Medium',
                'formatting_score': 80
            }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'score': 0,
            'issues': ['OpenAI API configuration needed'],
            'recommendations': ['Configure API key for ATS scanning']
        }


def generate_cover_letter(resume_content: Dict[str, Any], job: Any) -> str:
    """
    Generate customized cover letter for job application
    
    Args:
        resume_content: Resume content including user info
        job: Job object with details
    
    Returns:
        Generated cover letter text
    """
    
    user_info = resume_content.get('user', {})
    
    job_info = f"""
Job Title: {job.title}
Company: {job.company.name if hasattr(job, 'company') else 'the company'}
Description: {job.description[:500]}
"""
    
    # Extract key experience from resume
    experience_summary = []
    for section in resume_content.get('sections', []):
        if section.get('type') == 'experience':
            experience_summary.append(section.get('content', '')[:200])
    
    prompt = f"""
Write a professional cover letter for this job application:

APPLICANT:
Name: {user_info.get('name', '')}
Email: {user_info.get('email', '')}
Major: {user_info.get('major', '')}
Graduation: {user_info.get('graduation_year', '')}

RELEVANT EXPERIENCE:
{chr(10).join(experience_summary[:2])}

JOB POSTING:
{job_info}

Write a compelling 3-4 paragraph cover letter that:
1. Opens with enthusiasm and specific interest in the role
2. Connects applicant's experience to job requirements
3. Highlights 2-3 key achievements relevant to the position
4. Closes with call to action

Use professional business letter format. Be specific and avoid generic phrases.
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert career counselor and professional writer. Write compelling, personalized cover letters that get interviews."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return response.choices[0].message['content'].strip()
        
    except Exception as e:
        # Fallback template
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at {job.company.name if hasattr(job, 'company') else 'your company'}.

As a {user_info.get('major', '')} student at Pittsburg State University, I have developed relevant skills and experience that align well with this opportunity.

I would welcome the opportunity to discuss how my background and enthusiasm can contribute to your team.

Thank you for your consideration.

Sincerely,
{user_info.get('name', '')}
{user_info.get('email', '')}

[Configure OpenAI API key for AI-generated cover letters]"""


def suggest_resume_improvements(resume_content: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Provide AI-powered suggestions to improve resume
    
    Args:
        resume_content: Current resume content
    
    Returns:
        List of improvement suggestions with type and description
    """
    
    resume_text = json.dumps(resume_content, indent=2)
    
    prompt = f"""
Review this resume and provide specific improvement suggestions:

{resume_text}

Analyze:
1. Content quality and impact
2. Achievement quantification
3. Action verbs and language
4. Formatting and structure
5. Keyword optimization
6. Length and conciseness
7. Industry best practices

Provide 5-10 specific, actionable suggestions.
Format as JSON array with objects containing: type, priority (high/medium/low), section, suggestion
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional resume reviewer and career coach. Provide specific, actionable feedback to improve resumes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message['content'].strip()
        
        # Try to parse as JSON
        try:
            suggestions = json.loads(result_text)
            return suggestions if isinstance(suggestions, list) else []
        except:
            # Parse from text
            return [
                {'type': 'general', 'priority': 'high', 'suggestion': result_text}
            ]
        
    except Exception as e:
        return [
            {
                'type': 'setup',
                'priority': 'high',
                'section': 'general',
                'suggestion': 'Configure OpenAI API key to enable AI-powered resume suggestions'
            }
        ]


def generate_interview_prep(resume_content: Dict[str, Any], job: Any) -> Dict[str, Any]:
    """
    Generate interview preparation materials based on resume and job
    
    Args:
        resume_content: User's resume content
        job: Job they're applying for
    
    Returns:
        Dictionary with interview questions and suggested answers
    """
    
    prompt = f"""
Generate interview preparation materials for:

JOB: {job.title} at {job.company.name if hasattr(job, 'company') else 'Company'}
DESCRIPTION: {job.description[:500]}

CANDIDATE BACKGROUND:
{json.dumps(resume_content, indent=2)[:1000]}

Provide:
1. 10 likely interview questions for this role
2. Suggested answer frameworks (STAR method)
3. Key points to emphasize from candidate's background
4. Questions candidate should ask interviewer
5. Red flags to avoid

Format as JSON with keys: questions, answer_frameworks, key_points, questions_to_ask, tips
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert interview coach. Provide thorough interview preparation advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1500
        )
        
        result_text = response.choices[0].message['content'].strip()
        
        try:
            return json.loads(result_text)
        except:
            return {
                'questions': ['Tell me about yourself', 'Why this role?', 'What are your strengths?'],
                'answer_frameworks': result_text
            }
        
    except Exception as e:
        return {
            'error': str(e),
            'questions': ['Configure OpenAI API key for interview prep features']
        }


def analyze_job_match(resume_content: Dict[str, Any], job: Any) -> Dict[str, Any]:
    """
    Analyze how well resume matches job requirements
    
    Args:
        resume_content: User's resume
        job: Job posting
    
    Returns:
        Match analysis with score and details
    """
    
    prompt = f"""
Analyze the match between this candidate and job:

CANDIDATE:
{json.dumps(resume_content, indent=2)[:1000]}

JOB:
Title: {job.title}
Description: {job.description}
Requirements: {getattr(job, 'requirements', '')}

Provide:
1. Overall match score (0-100)
2. Matching qualifications
3. Missing qualifications
4. Transferable skills
5. Recommendation (strong match / worth applying / not recommended)
6. How to improve match

Format as JSON with keys: score, matching, missing, transferable, recommendation, improvements
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a career counselor analyzing job-candidate fit. Be honest but encouraging."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        result_text = response.choices[0].message['content'].strip()
        
        try:
            return json.loads(result_text)
        except:
            return {
                'score': 70,
                'recommendation': 'worth applying',
                'details': result_text
            }
        
    except Exception as e:
        return {
            'error': str(e),
            'score': 0,
            'recommendation': 'Configure API key for analysis'
        }
