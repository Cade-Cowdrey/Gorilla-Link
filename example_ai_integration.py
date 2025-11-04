"""
Complete Integration Example - AI Resume Builder
Shows how to use all AI features in your application
"""

from flask import Flask, jsonify, request
from models import db, User, Resume, Job
from utils.openai_utils import (
    generate_resume_content,
    optimize_resume_for_job,
    scan_resume_ats,
    generate_cover_letter,
    suggest_resume_improvements,
    generate_interview_prep,
    analyze_job_match
)


def example_create_ai_resume(user_id):
    """
    Example: Create a complete resume using AI
    """
    user = User.query.get(user_id)
    
    # Step 1: Generate professional summary
    summary_context = {
        'user': {
            'name': user.full_name,
            'major': user.major,
            'graduation_year': user.graduation_year,
            'role': user.role
        },
        'years_experience': '2',
        'skills': ['Python', 'JavaScript', 'React', 'SQL'],
        'career_goals': 'Software Engineer at a tech company'
    }
    
    summary = generate_resume_content('summary', summary_context)
    
    # Step 2: Generate work experience
    experience_context = {
        'job_title': 'Software Development Intern',
        'company': 'Tech Startup Inc',
        'duration': 'May 2024 - Aug 2024',
        'responsibilities': 'Built web applications, collaborated with team, wrote tests',
        'achievements': 'Increased site performance by 40%, deployed 15 features'
    }
    
    experience = generate_resume_content('experience', experience_context)
    
    # Step 3: Generate skills section
    skills_context = {
        'technical_skills': ['Python', 'JavaScript', 'React', 'Node.js', 'PostgreSQL'],
        'soft_skills': ['Communication', 'Teamwork', 'Problem-solving'],
        'tools': ['Git', 'Docker', 'AWS', 'Jira'],
        'target_role': 'Full Stack Developer'
    }
    
    skills = generate_resume_content('skills', skills_context)
    
    # Step 4: Create resume with all sections
    resume = Resume(
        user_id=user_id,
        title=f"{user.full_name} - Resume",
        template_id=1,  # Use ATS-optimized template
        status='active'
    )
    db.session.add(resume)
    db.session.flush()
    
    # Add sections
    from models import ResumeSection
    
    sections = [
        {'type': 'summary', 'title': 'Professional Summary', 'content': summary, 'order': 1},
        {'type': 'experience', 'title': 'Experience', 'content': experience, 'order': 2},
        {'type': 'skills', 'title': 'Skills', 'content': skills, 'order': 3}
    ]
    
    for section_data in sections:
        section = ResumeSection(resume_id=resume.id, **section_data)
        db.session.add(section)
    
    db.session.commit()
    
    return resume


def example_optimize_for_job(resume_id, job_id):
    """
    Example: Optimize existing resume for specific job
    """
    resume = Resume.query.get(resume_id)
    job = Job.query.get(job_id)
    
    # Get resume content
    resume_content = {
        'title': resume.title,
        'sections': []
    }
    
    for section in resume.sections:
        resume_content['sections'].append({
            'type': section.section_type,
            'title': section.title,
            'content': section.content
        })
    
    # Optimize using AI
    optimization = optimize_resume_for_job(resume_content, job)
    
    return {
        'job_title': job.title,
        'keyword_match': optimization.get('keyword_match', 0),
        'missing_keywords': optimization.get('missing_keywords', []),
        'suggestions': optimization.get('suggestions', []),
        'priority_changes': optimization.get('priority_changes', [])
    }


def example_ats_scan(resume_id):
    """
    Example: Scan resume for ATS compatibility
    """
    resume = Resume.query.get(resume_id)
    
    resume_content = {
        'title': resume.title,
        'sections': [
            {
                'type': s.section_type,
                'title': s.title,
                'content': s.content
            }
            for s in resume.sections
        ]
    }
    
    # Scan with AI
    scan_results = scan_resume_ats(resume_content)
    
    return {
        'ats_score': scan_results.get('score', 0),
        'issues': scan_results.get('issues', []),
        'recommendations': scan_results.get('recommendations', []),
        'formatting_score': scan_results.get('formatting_score', 0)
    }


def example_generate_cover_letter(resume_id, job_id):
    """
    Example: Generate cover letter for job application
    """
    resume = Resume.query.get(resume_id)
    job = Job.query.get(job_id)
    user = resume.user
    
    resume_content = {
        'user': {
            'name': user.full_name,
            'email': user.email,
            'major': user.major,
            'graduation_year': user.graduation_year
        },
        'sections': [
            {
                'type': s.section_type,
                'content': s.content
            }
            for s in resume.sections
        ]
    }
    
    # Generate cover letter
    cover_letter = generate_cover_letter(resume_content, job)
    
    return cover_letter


def example_interview_prep(resume_id, job_id):
    """
    Example: Generate interview preparation materials
    """
    resume = Resume.query.get(resume_id)
    job = Job.query.get(job_id)
    
    resume_content = {
        'user': {
            'name': resume.user.full_name,
            'major': resume.user.major
        },
        'sections': [
            {
                'type': s.section_type,
                'content': s.content
            }
            for s in resume.sections
        ]
    }
    
    # Generate interview prep
    prep = generate_interview_prep(resume_content, job)
    
    return {
        'questions': prep.get('questions', []),
        'answer_frameworks': prep.get('answer_frameworks', ''),
        'key_points': prep.get('key_points', []),
        'questions_to_ask': prep.get('questions_to_ask', [])
    }


def example_job_match_analysis(resume_id, job_id):
    """
    Example: Analyze how well resume matches job
    """
    resume = Resume.query.get(resume_id)
    job = Job.query.get(job_id)
    
    resume_content = {
        'sections': [
            {
                'type': s.section_type,
                'content': s.content
            }
            for s in resume.sections
        ]
    }
    
    # Analyze match
    match = analyze_job_match(resume_content, job)
    
    return {
        'match_score': match.get('score', 0),
        'matching_qualifications': match.get('matching', []),
        'missing_qualifications': match.get('missing', []),
        'transferable_skills': match.get('transferable', []),
        'recommendation': match.get('recommendation', ''),
        'improvements': match.get('improvements', [])
    }


# =============================================================================
# FLASK ROUTE EXAMPLES
# =============================================================================

def setup_example_routes(app):
    """
    Add these routes to your Flask app to enable AI features
    """
    
    @app.route('/api/resume/ai-create', methods=['POST'])
    def api_create_ai_resume():
        """Create resume using AI"""
        user_id = request.json.get('user_id')
        
        try:
            resume = example_create_ai_resume(user_id)
            return jsonify({
                'success': True,
                'resume_id': resume.id,
                'message': 'Resume created with AI assistance'
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/resume/<int:resume_id>/optimize/<int:job_id>', methods=['POST'])
    def api_optimize_resume(resume_id, job_id):
        """Optimize resume for specific job"""
        try:
            result = example_optimize_for_job(resume_id, job_id)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/resume/<int:resume_id>/ats-scan', methods=['GET'])
    def api_ats_scan(resume_id):
        """Scan resume for ATS compatibility"""
        try:
            result = example_ats_scan(resume_id)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/resume/<int:resume_id>/cover-letter/<int:job_id>', methods=['POST'])
    def api_generate_cover_letter(resume_id, job_id):
        """Generate cover letter"""
        try:
            cover_letter = example_generate_cover_letter(resume_id, job_id)
            return jsonify({
                'success': True,
                'cover_letter': cover_letter
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/resume/<int:resume_id>/interview-prep/<int:job_id>', methods=['GET'])
    def api_interview_prep(resume_id, job_id):
        """Get interview preparation materials"""
        try:
            prep = example_interview_prep(resume_id, job_id)
            return jsonify(prep), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/api/resume/<int:resume_id>/match/<int:job_id>', methods=['GET'])
    def api_job_match(resume_id, job_id):
        """Analyze job match"""
        try:
            match = example_job_match_analysis(resume_id, job_id)
            return jsonify(match), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# =============================================================================
# USAGE IN YOUR APPLICATION
# =============================================================================

"""
To use these AI features in your app:

1. Install dependencies:
   pip install openai==1.3.0 pdfkit python-docx

2. Set environment variable:
   OPENAI_API_KEY=sk-your-api-key-here

3. Import and use in your code:
   
   from example_ai_integration import example_create_ai_resume
   
   # In your route
   @app.route('/resume/create-with-ai')
   def create_ai_resume():
       user_id = current_user.id
       resume = example_create_ai_resume(user_id)
       flash('Resume created with AI!', 'success')
       return redirect(url_for('resume.edit', resume_id=resume.id))

4. Or register the example routes:
   
   from example_ai_integration import setup_example_routes
   setup_example_routes(app)

5. Test the endpoints:
   
   POST /api/resume/ai-create
   POST /api/resume/1/optimize/5
   GET  /api/resume/1/ats-scan
   POST /api/resume/1/cover-letter/5
   GET  /api/resume/1/interview-prep/5
   GET  /api/resume/1/match/5
"""


# =============================================================================
# COMMAND LINE TESTING
# =============================================================================

if __name__ == '__main__':
    """
    Test AI features from command line:
    
    python example_ai_integration.py
    """
    from app_pro import app
    
    with app.app_context():
        print("🤖 Testing AI Resume Features\n")
        
        # Test 1: Generate resume content
        print("1️⃣ Testing Resume Content Generation...")
        context = {
            'user': {
                'name': 'Jane Doe',
                'major': 'Computer Science',
                'graduation_year': 2025,
                'role': 'student'
            },
            'years_experience': '1',
            'skills': ['Python', 'Java', 'SQL'],
            'career_goals': 'Software Engineer'
        }
        
        summary = generate_resume_content('summary', context)
        print(f"✅ Generated Summary:\n{summary}\n")
        
        # Test 2: Get improvement suggestions
        print("2️⃣ Testing Improvement Suggestions...")
        resume_content = {
            'title': 'Jane Doe Resume',
            'sections': [
                {'type': 'summary', 'content': summary}
            ]
        }
        
        suggestions = suggest_resume_improvements(resume_content)
        print(f"✅ Got {len(suggestions)} suggestions\n")
        
        print("🎉 All tests complete!")
        print("\nReady to deploy AI features!")
