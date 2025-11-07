from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import limiter
from utils.analytics_util import record_page_view
from models import Scholarship
import openai
import os
import logging
import bleach

logger = logging.getLogger(__name__)

# Allowed HTML tags for essay text (very restricted for security)
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u']
ALLOWED_ATTRS = {}

# File upload security settings
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file):
    """Check if file size is within limit"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset file pointer
    return size <= MAX_FILE_SIZE

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Import blueprint from __init__.py
from . import bp

@bp.route("/")
@limiter.limit("20/minute")
def index():
    """Scholarships home page showing hub overview."""
    record_page_view("scholarships_home", current_user.id if current_user.is_authenticated else None)
    return render_template("scholarships/index.html", title="Scholarships Hub | PittState-Connect")

@bp.route("/browse")
def browse():
    """Browse all available scholarships from trusted sources."""
    record_page_view("scholarships_browse", current_user.id if current_user.is_authenticated else None)
    
    try:
        # Get all active scholarships
        query = Scholarship.query.filter_by(is_active=True)
        
        # Apply filters if provided
        category = request.args.get('category')
        if category:
            query = query.filter(Scholarship.category == category)
        
        min_amount = request.args.get('min_amount', type=float)
        if min_amount:
            query = query.filter(Scholarship.amount >= min_amount)
        
        # Order by deadline (closest first)
        scholarships = query.order_by(Scholarship.deadline).all()
        
        # Get unique categories for filtering
        all_categories = [c[0] for c in Scholarship.query.with_entities(Scholarship.category).distinct().all() if c[0]]
    except Exception as e:
        logger.error(f"Error loading scholarships: {e}")
        scholarships = []
        all_categories = []
    
    return render_template(
        "scholarships/browse.html", 
        scholarships=scholarships, 
        categories=all_categories,
        total_count=len(scholarships),
        title="Browse Scholarships | PittState-Connect"
    )


@bp.route("/personal")
def personal_circumstances():
    """Browse scholarships for specific personal circumstances (sensitive categories)"""
    record_page_view("scholarships_personal", current_user.id if current_user.is_authenticated else None)
    
    # Get personal circumstance scholarships (specific categories)
    personal_categories = ['First Generation', 'Military/Veterans', 'General', 'Healthcare', 'Nursing']
    scholarships = Scholarship.query.filter(
        Scholarship.is_active == True,
        Scholarship.category.in_(personal_categories)
    ).all()
    
    # Group by category
    categories = {}
    for scholarship in scholarships:
        category = scholarship.category or 'Other'
        if category not in categories:
            categories[category] = []
        categories[category].append(scholarship)
    
    return render_template(
        "scholarships/personal.html",
        categories=categories,
        total_count=len(scholarships),
        title="Personal Circumstance Scholarships | PittState-Connect"
    )


@bp.route("/api/search")
def api_search():
    """API endpoint for dynamic scholarship search"""
    query_text = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Start with active scholarships
    query = Scholarship.query.filter_by(is_active=True)
    
    # Apply category filter
    if category:
        query = query.filter(Scholarship.category == category)
    
    # Apply text search if provided
    if query_text:
        search_pattern = f'%{query_text}%'
        query = query.filter(
            (Scholarship.title.ilike(search_pattern)) |
            (Scholarship.description.ilike(search_pattern)) |
            (Scholarship.provider.ilike(search_pattern))
        )
    
    scholarships = query.order_by(Scholarship.deadline).limit(50).all()
    
    # Convert to JSON
    results = [{
        'id': s.id,
        'title': s.title,
        'amount': float(s.amount) if s.amount else 0,
        'provider': s.provider,
        'deadline': s.deadline.isoformat() if s.deadline else None,
        'category': s.category,
        'url': s.url
    } for s in scholarships]
    
    return jsonify(results)

@bp.route("/my")
@login_required
def my_scholarships():
    """Display scholarships the current user has saved or applied to."""
    record_page_view("scholarships_my", current_user.id if current_user.is_authenticated else None)
    # In a real application this would query the database for the user's scholarships
    my_sch = []
    return render_template("scholarships/my_scholarships.html", scholarships=my_sch, title="My Scholarships | PittState-Connect")

@bp.route("/apply/<int:scholarship_id>", methods=["GET", "POST"])
@login_required
def apply(scholarship_id: int):
    """Full scholarship application with essay, file upload, and progress tracking"""
    from models import Scholarship, db
    from models_growth_features import ScholarshipApplication
    from datetime import datetime
    from werkzeug.utils import secure_filename
    import os
    
    record_page_view("scholarships_apply", current_user.id if current_user.is_authenticated else None)
    
    # Get scholarship
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    
    # Check if already applied
    existing_app = ScholarshipApplication.query.filter_by(
        user_id=current_user.id,
        scholarship_id=scholarship_id
    ).first()
    
    if request.method == "GET":
        return render_template("scholarships/apply.html", 
                             scholarship=scholarship,
                             application=existing_app)
    
    # POST - Process application
    try:
        essay_text = request.form.get('essay_text', '').strip()
        
        # Sanitize input to prevent XSS attacks
        essay_text = bleach.clean(essay_text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
        
        # Validation
        if not essay_text:
            flash("Essay is required", "danger")
            return redirect(request.url)
        
        if len(essay_text.split()) < 100:
            flash("Essay must be at least 100 characters", "warning")
            return redirect(request.url)
        
        # Create or update application
        if existing_app:
            application = existing_app
            application.essay_text = essay_text
            application.updated_at = datetime.utcnow()
        else:
            application = ScholarshipApplication(
                user_id=current_user.id,
                scholarship_id=scholarship_id,
                essay_text=essay_text,
                status='draft',
                progress_percentage=40
            )
            db.session.add(application)
        
        # Handle file uploads (transcripts, recommendations, etc.)
        uploaded_files = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            upload_folder = os.path.join('static', 'uploads', 'scholarships', str(current_user.id))
            os.makedirs(upload_folder, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    # Security: Check file extension
                    if not allowed_file(file.filename):
                        flash(f"File type not allowed: {file.filename}. Only PDF, DOC, DOCX, JPG, PNG allowed.", "warning")
                        continue
                    
                    # Security: Check file size
                    if not check_file_size(file):
                        flash(f"File too large: {file.filename}. Maximum 5MB per file.", "warning")
                        continue
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    uploaded_files.append(unique_filename)
                    
                    # Update recommendations count if it's a recommendation letter
                    if 'recommendation' in filename.lower() or 'letter' in filename.lower():
                        application.recommendations_uploaded += 1
        
        # Check if user wants to submit
        if request.form.get('action') == 'submit':
            application.status = 'submitted'
            application.submitted_at = datetime.utcnow()
            application.progress_percentage = 100
            
            # Send confirmation email
            try:
                from utils.mail_util import send_email
                send_email(
                    to=current_user.email,
                    subject=f"Scholarship Application Submitted: {scholarship.title}",
                    body=f"""
                    <h2>Application Submitted Successfully!</h2>
                    <p>Dear {current_user.full_name},</p>
                    <p>Your application for <strong>{scholarship.title}</strong> has been successfully submitted.</p>
                    <p><strong>Application Details:</strong></p>
                    <ul>
                        <li>Scholarship: {scholarship.title}</li>
                        <li>Amount: ${scholarship.amount}</li>
                        <li>Deadline: {scholarship.deadline}</li>
                        <li>Submitted: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}</li>
                        <li>Files Uploaded: {len(uploaded_files)}</li>
                    </ul>
                    <p>You will receive an email notification when your application status changes.</p>
                    <p>Good luck!</p>
                    <p><em>- PittState Connect Team</em></p>
                    """
                )
            except Exception as e:
                logger.warning(f"Failed to send confirmation email: {e}")
            
            flash(f"Application submitted successfully for {scholarship.title}! You will receive a confirmation email shortly.", "success")
        else:
            application.status = 'draft'
            application.progress_percentage = min(application.progress_percentage + 20, 80)
            flash("Application saved as draft. You can continue editing later.", "info")
        
        db.session.commit()
        
        # Log the application
        logger.info(f"Scholarship application {application.status} - User: {current_user.id}, Scholarship: {scholarship_id}")
        
        return redirect(url_for("scholarships_bp.my_scholarships"))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing scholarship application: {str(e)}")
        flash("An error occurred while processing your application. Please try again.", "danger")
        return redirect(request.url)


@bp.route("/essay-helper")
@login_required
def essay_helper():
    """AI-powered essay writing assistant"""
    record_page_view("essay_helper", current_user.id if current_user.is_authenticated else None)
    return render_template("scholarships/essay_helper.html", title="Essay Writing Helper | PittState-Connect")


@bp.route("/essay-helper/analyze", methods=["POST"])
@limiter.limit("10/hour")
@login_required
def analyze_essay():
    """
    Analyze scholarship essay using AI and provide suggestions
    
    Returns:
        JSON with analysis results:
        - grammar: Grammar and spelling issues
        - structure: Essay structure recommendations
        - clarity: Clarity and coherence suggestions
        - scholarship_fit: How well it fits scholarship criteria
        - strengths: What's working well
        - improvements: Specific improvement suggestions
        - overall_score: 0-100 score
    """
    try:
        data = request.get_json()
        
        essay_text = data.get('essay', '').strip()
        scholarship_type = data.get('scholarship_type', 'general')
        prompt_question = data.get('prompt', '')
        word_limit = data.get('word_limit', 500)
        
        if not essay_text:
            return jsonify({'success': False, 'error': 'Essay text is required'}), 400
        
        if len(essay_text) < 50:
            return jsonify({'success': False, 'error': 'Essay is too short for meaningful analysis'}), 400
        
        # Count words
        word_count = len(essay_text.split())
        
        # Build AI prompt
        analysis_prompt = f"""You are an expert scholarship essay reviewer. Analyze the following essay and provide detailed, actionable feedback.

Essay Prompt: {prompt_question if prompt_question else 'Not provided'}
Scholarship Type: {scholarship_type}
Word Limit: {word_limit}
Current Word Count: {word_count}

Essay:
{essay_text}

Provide your analysis in the following JSON format:
{{
  "grammar": {{
    "issues_found": [list of specific grammar/spelling issues with line numbers],
    "severity": "low/medium/high"
  }},
  "structure": {{
    "has_clear_intro": true/false,
    "has_body_paragraphs": true/false,
    "has_strong_conclusion": true/false,
    "suggestions": [list of structure improvements]
  }},
  "clarity": {{
    "score": 0-100,
    "issues": [list of clarity problems],
    "suggestions": [list of ways to improve clarity]
  }},
  "scholarship_fit": {{
    "score": 0-100,
    "addresses_prompt": true/false,
    "shows_qualifications": true/false,
    "demonstrates_passion": true/false,
    "feedback": "detailed feedback on fit"
  }},
  "strengths": [list of 3-5 strong points],
  "improvements": [list of 3-5 specific improvements needed],
  "overall_score": 0-100,
  "word_count_feedback": "feedback on length relative to limit",
  "next_steps": [list of 2-3 immediate action items]
}}

Be specific, constructive, and encouraging in your feedback."""

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert scholarship essay reviewer with years of experience helping students improve their applications. Provide detailed, actionable, and encouraging feedback."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse JSON response
        import json
        try:
            # Try to extract JSON from response (in case AI adds extra text)
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis_json = json.loads(ai_response[json_start:json_end])
            else:
                analysis_json = json.loads(ai_response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {ai_response}")
            # Fallback: return raw text
            analysis_json = {
                "grammar": {"issues_found": [], "severity": "unknown"},
                "structure": {
                    "has_clear_intro": True,
                    "has_body_paragraphs": True,
                    "has_strong_conclusion": True,
                    "suggestions": []
                },
                "clarity": {"score": 70, "issues": [], "suggestions": []},
                "scholarship_fit": {
                    "score": 70,
                    "addresses_prompt": True,
                    "shows_qualifications": True,
                    "demonstrates_passion": True,
                    "feedback": ai_response
                },
                "strengths": ["Your essay shows promise"],
                "improvements": ["Continue refining your work"],
                "overall_score": 70,
                "word_count_feedback": f"Your essay is {word_count} words",
                "next_steps": ["Review the feedback", "Make revisions", "Have someone proofread"]
            }
        
        # Add metadata
        analysis_json['word_count'] = word_count
        analysis_json['word_limit'] = word_limit
        analysis_json['is_over_limit'] = word_count > word_limit
        analysis_json['word_count_status'] = 'over' if word_count > word_limit else 'under' if word_count < word_limit * 0.8 else 'good'
        
        logger.info(f"✅ Essay analyzed for user {current_user.id}: score {analysis_json.get('overall_score', 'N/A')}")
        
        return jsonify({
            'success': True,
            'analysis': analysis_json
        })
        
    except openai.error.RateLimitError:
        logger.error("OpenAI rate limit exceeded")
        return jsonify({
            'success': False,
            'error': 'AI service is currently busy. Please try again in a few minutes.'
        }), 429
        
    except openai.error.InvalidRequestError as e:
        logger.error(f"Invalid OpenAI request: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Invalid request to AI service. Please check your essay and try again.'
        }), 400
        
    except openai.error.AuthenticationError:
        logger.error("OpenAI authentication failed")
        return jsonify({
            'success': False,
            'error': 'AI service configuration error. Please contact support.'
        }), 500
        
    except Exception as e:
        logger.error(f"Error analyzing essay: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500


@bp.route("/essay-helper/templates")
@login_required
def essay_templates():
    """Get essay templates and examples"""
    
    templates = {
        'academic': {
            'title': 'Academic Achievement Essay',
            'description': 'Highlight your academic accomplishments and goals',
            'outline': [
                'Opening: Hook with a defining academic moment',
                'Academic journey: Challenges overcome and lessons learned',
                'Current achievements: Specific examples with metrics',
                'Future goals: How this scholarship enables your path',
                'Closing: Connect back to opening and scholarship mission'
            ],
            'tips': [
                'Use specific examples and numbers (GPA, test scores, awards)',
                'Show growth and learning, not just accomplishments',
                'Connect your goals to the scholarship\'s mission',
                'Be authentic - share both successes and struggles'
            ]
        },
        'leadership': {
            'title': 'Leadership Experience Essay',
            'description': 'Demonstrate your leadership skills and impact',
            'outline': [
                'Opening: Describe a leadership challenge you faced',
                'The situation: Set the scene and stakes',
                'Your actions: Specific steps you took to lead',
                'The impact: Measurable results and lessons learned',
                'Closing: How you\'ll apply these skills in the future'
            ],
            'tips': [
                'Focus on one or two strong examples rather than listing many',
                'Emphasize impact on others, not just your role',
                'Show emotional intelligence and adaptability',
                'Include specific metrics of success'
            ]
        },
        'community_service': {
            'title': 'Community Service Essay',
            'description': 'Share your commitment to service and impact',
            'outline': [
                'Opening: What inspired you to serve your community',
                'The need: Problem or issue you addressed',
                'Your involvement: Specific actions and time commitment',
                'The impact: Who benefited and how (with numbers)',
                'Closing: Your continued commitment to service'
            ],
            'tips': [
                'Show passion and personal connection to the cause',
                'Quantify your impact (hours, people served, funds raised)',
                'Reflect on what you learned from those you served',
                'Connect service to your future career or goals'
            ]
        },
        'overcoming_adversity': {
            'title': 'Overcoming Challenges Essay',
            'description': 'Share how you\'ve grown through difficulties',
            'outline': [
                'Opening: Introduce the challenge (without being too dramatic)',
                'The struggle: What made this difficult for you',
                'Turning point: What changed or what you realized',
                'Growth: Specific skills or insights you gained',
                'Closing: How this experience shaped who you are today'
            ],
            'tips': [
                'Be honest but maintain appropriate boundaries',
                'Focus more on growth than on the hardship itself',
                'Show resilience and problem-solving skills',
                'Connect the experience to your future goals'
            ]
        },
        'career_goals': {
            'title': 'Career Goals Essay',
            'description': 'Articulate your professional aspirations',
            'outline': [
                'Opening: What sparked your interest in this field',
                'Current preparation: Relevant coursework, experiences, skills',
                'Short-term goals: What you plan to achieve in 2-5 years',
                'Long-term vision: Your ultimate career aspirations',
                'Closing: How this scholarship is crucial to your path'
            ],
            'tips': [
                'Be specific about your chosen field and why',
                'Show you\'ve researched career paths and opportunities',
                'Connect your goals to a larger purpose or impact',
                'Demonstrate realistic planning and commitment'
            ]
        }
    }
    
    return jsonify({
        'success': True,
        'templates': templates
    })


# ========================================
# ADMIN: Federal Grants Integration
# ========================================

@bp.route("/admin/add-federal-grants", methods=["POST"])
@login_required
def admin_add_federal_grants():
    """
    Admin route to add federal grants from Student Aid API
    FREE government scholarships - No API key required!
    """
    # Check if user is admin
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash("⛔ Unauthorized access", "danger")
        return redirect(url_for("scholarships_bp.browse"))
    
    try:
        from federal_aid_api import add_federal_grants
        
        count = add_federal_grants()
        
        if count > 0:
            flash(f"✅ Successfully added {count} federal grants! (Pell, FSEOG, TEACH, etc.)", "success")
        else:
            flash("ℹ️ Federal grants already exist in database", "info")
            
    except Exception as e:
        logger.error(f"Error adding federal grants: {e}")
        flash(f"❌ Error adding federal grants: {str(e)}", "danger")
    
    return redirect(url_for("scholarships_bp.browse"))
