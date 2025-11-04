"""
PSU Connect - AI Career Coach Chatbot
24/7 career assistance using OpenAI GPT-4
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import User
from models_growth_features import ChatMessage
import openai
import os
from datetime import datetime

ai_coach_bp = Blueprint('ai_coach', __name__, url_prefix='/ai-coach')

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_psu_context(user):
    """Build PSU-specific context for the AI"""
    context = f"""You are a career coach for Pittsburg State University (PSU) students and alumni. 
    
User Profile:
- Name: {user.full_name}
- Major: {user.major or 'Not specified'}
- Graduation Year: {user.graduation_year or 'Not specified'}
- Skills: {', '.join(user.skills or ['None listed'])}

Your role:
- Provide career advice specific to PSU and Kansas
- Help with resume writing, interview prep, job search strategies
- Be encouraging and supportive
- Reference PSU resources when relevant
- Keep responses concise (2-3 paragraphs max unless asked for details)

PSU Information:
- Location: Pittsburg, Kansas
- Known for: Education, Technology, Business programs
- Career Services: Located in Overman Student Center
- Strong alumni network in Kansas City, Wichita, and Joplin areas"""
    
    return context


def get_system_prompt():
    """Get system prompt for AI coach"""
    return """You are an expert career coach and advisor. You help students and professionals with:
- Career planning and goal setting
- Resume and cover letter writing
- Interview preparation
- Job search strategies
- Salary negotiation
- Professional networking
- Work-life balance
- Career transitions

Be friendly, encouraging, and actionable. Give specific advice when possible."""


@ai_coach_bp.route('/')
@ai_coach_bp.route('/chat')
@login_required
def chat_interface():
    """Main chat interface"""
    # Get recent chat history
    recent_messages = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(50).all()
    
    recent_messages.reverse()  # Oldest first
    
    return render_template('ai_coach/chat.html',
                         messages=recent_messages)


@ai_coach_bp.route('/api/chat', methods=['POST'])
@login_required
def send_message():
    """Send message to AI coach"""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message required'}), 400
    
    # Check if OpenAI is configured
    if not openai.api_key:
        return jsonify({
            'error': 'AI coach not configured',
            'response': "I'm sorry, but the AI coach feature requires an OpenAI API key. Please contact support."
        }), 500
    
    try:
        # Save user message
        user_msg = ChatMessage(
            user_id=current_user.id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # Get recent conversation history
        recent = ChatMessage.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        recent.reverse()  # Oldest first
        
        # Build conversation for OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt()},
            {"role": "system", "content": get_psu_context(current_user)}
        ]
        
        # Add recent history
        for msg in recent:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # Save assistant response
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=assistant_message
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': assistant_message,
            'message_id': assistant_msg.id
        })
    
    except Exception as e:
        print(f"OpenAI error: {e}")
        # Fallback response if API fails
        fallback = """I'm having trouble connecting right now, but here are some resources that might help:

1. Check out PSU Career Services in Overman Student Center
2. Browse our job board for opportunities
3. Connect with alumni in your field
4. Review our resume templates and guides

Please try again in a moment or contact career.services@pittstate.edu for immediate assistance."""
        
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=fallback,
            metadata={'error': True}
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': fallback,
            'message_id': assistant_msg.id
        })


@ai_coach_bp.route('/api/quick-actions', methods=['POST'])
@login_required
def quick_action():
    """Handle quick action buttons"""
    data = request.json
    action = data.get('action')
    
    prompts = {
        'resume_tips': "Can you give me 5 quick tips to improve my resume?",
        'interview_prep': "I have an interview coming up. What are the most important things to prepare?",
        'job_search': "What's the best strategy for finding a job in my field?",
        'career_advice': f"I'm a {current_user.major} major. What career paths should I consider?",
        'networking': "How can I effectively network to find job opportunities?",
        'salary_negotiation': "How do I negotiate salary for my first job?"
    }
    
    if action not in prompts:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Use the regular chat endpoint with the predefined prompt
    return send_message()


@ai_coach_bp.route('/api/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clear chat history"""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({'success': True})


@ai_coach_bp.route('/history')
@login_required
def view_history():
    """View all chat history"""
    messages = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Group by date
    grouped = {}
    for msg in messages:
        date_key = msg.created_at.strftime('%Y-%m-%d')
        if date_key not in grouped:
            grouped[date_key] = []
        grouped[date_key].append(msg)
    
    return render_template('ai_coach/history.html',
                         grouped_messages=grouped)


# =====================
# SPECIALIZED COACHING
# =====================

@ai_coach_bp.route('/resume-review', methods=['POST'])
@login_required
def resume_review():
    """Get AI feedback on resume"""
    data = request.json
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        return jsonify({'error': 'Resume text required'}), 400
    
    if not openai.api_key:
        return jsonify({
            'error': 'AI not configured',
            'feedback': 'AI resume review requires OpenAI API key.'
        }), 500
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume reviewer. Provide specific, actionable feedback."},
                {"role": "user", "content": f"Please review this resume and provide 5 specific suggestions for improvement:\n\n{resume_text}"}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        feedback = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'feedback': feedback
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'feedback': 'Unable to review resume at this time. Please try again later.'
        }), 500


@ai_coach_bp.route('/cover-letter-help', methods=['POST'])
@login_required
def cover_letter_help():
    """Get help writing cover letter"""
    data = request.json
    job_description = data.get('job_description', '')
    user_background = data.get('background', '')
    
    if not openai.api_key:
        return jsonify({
            'error': 'AI not configured'
        }), 500
    
    try:
        prompt = f"""Help write a cover letter for this job:

Job Description:
{job_description}

Candidate Background:
- Major: {current_user.major}
- Skills: {', '.join(current_user.skills or [])}
{user_background}

Provide a professional cover letter template that the candidate can customize."""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at writing professional cover letters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        cover_letter = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'cover_letter': cover_letter
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@ai_coach_bp.route('/interview-questions', methods=['POST'])
@login_required
def interview_questions():
    """Generate practice interview questions"""
    data = request.json
    job_title = data.get('job_title', '')
    
    if not openai.api_key:
        # Return fallback questions
        return jsonify({
            'success': True,
            'questions': [
                "Tell me about yourself.",
                "Why are you interested in this position?",
                "What are your greatest strengths?",
                "What are your weaknesses?",
                "Where do you see yourself in 5 years?",
                "Why should we hire you?",
                "Tell me about a time you faced a challenge and how you overcame it.",
                "Do you have any questions for us?"
            ]
        })
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate realistic interview questions."},
                {"role": "user", "content": f"Generate 10 interview questions for a {job_title} position. Include behavioral and technical questions."}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        questions_text = response.choices[0].message.content
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and any(c.isalnum() for c in q)]
        
        return jsonify({
            'success': True,
            'questions': questions
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'questions': []
        }), 500
