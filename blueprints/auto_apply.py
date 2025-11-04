"""
PSU Connect - Auto-Apply System
One-click bulk job applications with AI-tailored resumes
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import AutoApplyQueue
from models import JobPosting, Application
from sqlalchemy import desc
from datetime import datetime
import openai
import os

auto_apply_bp = Blueprint('auto_apply', __name__, url_prefix='/auto-apply')

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')


def generate_tailored_resume(user, job):
    """Generate AI-tailored resume for specific job"""
    if not openai.api_key:
        return None
    
    try:
        prompt = f"""Tailor this resume for the job description below.

User Profile:
- Name: {user.full_name}
- Major: {user.major}
- Skills: {', '.join(user.skills or [])}
- Experience: {getattr(user, 'experience_summary', 'Recent graduate')}

Job Title: {job.title}
Company: {job.company}
Description: {job.description[:500]}

Generate a 1-paragraph professional summary that highlights the most relevant qualifications for this specific job. Focus on matching skills and experience."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a resume expert. Write compelling, concise professional summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Resume generation error: {e}")
        return None


def generate_cover_letter(user, job):
    """Generate AI cover letter for job"""
    if not openai.api_key:
        return None
    
    try:
        prompt = f"""Write a professional cover letter.

Applicant:
- Name: {user.full_name}
- Major: {user.major}
- Skills: {', '.join(user.skills or [])}

Job:
- Title: {job.title}
- Company: {job.company}
- Description: {job.description[:500]}

Write a 3-paragraph cover letter (introduction, why I'm a good fit, conclusion). Be enthusiastic but professional."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a career advisor. Write compelling, personalized cover letters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Cover letter generation error: {e}")
        return None


@auto_apply_bp.route('/')
@login_required
def dashboard():
    """Auto-apply dashboard"""
    # Get queued jobs
    queued = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='queued'
    ).order_by(AutoApplyQueue.created_at).all()
    
    # Get processing/completed
    processing = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='processing'
    ).all()
    
    completed = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).order_by(desc(AutoApplyQueue.completed_at)).limit(20).all()
    
    failed = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='failed'
    ).order_by(desc(AutoApplyQueue.completed_at)).limit(10).all()
    
    # Stats
    total_applied = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).count()
    
    return render_template('auto_apply/dashboard.html',
                         queued=queued,
                         processing=processing,
                         completed=completed,
                         failed=failed,
                         total_applied=total_applied)


@auto_apply_bp.route('/add-to-queue/<int:job_id>', methods=['POST'])
@login_required
def add_to_queue(job_id):
    """Add job to auto-apply queue"""
    job = JobPosting.query.get_or_404(job_id)
    
    # Check if already applied
    existing_app = Application.query.filter_by(
        user_id=current_user.id,
        job_id=job_id
    ).first()
    
    if existing_app:
        return jsonify({'error': 'Already applied to this job'}), 400
    
    # Check if already in queue
    existing_queue = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        job_id=job_id,
        status='queued'
    ).first()
    
    if existing_queue:
        return jsonify({'error': 'Job already in queue'}), 400
    
    data = request.json
    
    # Add to queue
    queue_item = AutoApplyQueue(
        user_id=current_user.id,
        job_id=job_id,
        use_ai_resume=data.get('use_ai_resume', True),
        use_ai_cover_letter=data.get('use_ai_cover_letter', True),
        custom_message=data.get('custom_message'),
        status='queued'
    )
    
    db.session.add(queue_item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'queue_id': queue_item.id,
        'message': 'Added to auto-apply queue'
    })


@auto_apply_bp.route('/bulk-add', methods=['POST'])
@login_required
def bulk_add():
    """Add multiple jobs to queue"""
    data = request.json
    job_ids = data.get('job_ids', [])
    
    if not job_ids:
        return jsonify({'error': 'No jobs selected'}), 400
    
    added = 0
    skipped = 0
    
    for job_id in job_ids:
        # Check if already applied
        existing_app = Application.query.filter_by(
            user_id=current_user.id,
            job_id=job_id
        ).first()
        
        if existing_app:
            skipped += 1
            continue
        
        # Check if in queue
        existing_queue = AutoApplyQueue.query.filter_by(
            user_id=current_user.id,
            job_id=job_id,
            status='queued'
        ).first()
        
        if existing_queue:
            skipped += 1
            continue
        
        # Add to queue
        queue_item = AutoApplyQueue(
            user_id=current_user.id,
            job_id=job_id,
            use_ai_resume=data.get('use_ai_resume', True),
            use_ai_cover_letter=data.get('use_ai_cover_letter', True),
            status='queued'
        )
        db.session.add(queue_item)
        added += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'added': added,
        'skipped': skipped,
        'message': f'Added {added} jobs to queue, skipped {skipped}'
    })


@auto_apply_bp.route('/process-queue', methods=['POST'])
@login_required
def process_queue():
    """Process auto-apply queue (triggered manually or by cron)"""
    # Get next items in queue
    queue_items = AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='queued'
    ).order_by(AutoApplyQueue.created_at).limit(5).all()
    
    if not queue_items:
        return jsonify({'message': 'Queue is empty'})
    
    processed = 0
    failed = 0
    
    for item in queue_items:
        try:
            # Mark as processing
            item.status = 'processing'
            db.session.commit()
            
            job = item.job
            
            # Generate AI resume if requested
            tailored_resume = None
            if item.use_ai_resume:
                tailored_resume = generate_tailored_resume(current_user, job)
            
            # Generate AI cover letter if requested
            cover_letter = None
            if item.use_ai_cover_letter:
                cover_letter = generate_cover_letter(current_user, job)
            
            # Create application
            application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume_url=current_user.resume_url,
                cover_letter=cover_letter or item.custom_message,
                status='submitted',
                applied_at=datetime.utcnow()
            )
            
            # Store tailored content
            if tailored_resume:
                application.custom_data = {
                    'ai_tailored_summary': tailored_resume,
                    'auto_applied': True
                }
            
            db.session.add(application)
            
            # Mark queue item as complete
            item.status = 'completed'
            item.completed_at = datetime.utcnow()
            item.application_id = application.id
            
            processed += 1
            
        except Exception as e:
            print(f"Auto-apply error for job {item.job_id}: {e}")
            item.status = 'failed'
            item.error_message = str(e)
            item.completed_at = datetime.utcnow()
            failed += 1
    
    db.session.commit()
    
    # Award points for applications
    if processed > 0:
        from blueprints.gamification import award_points
        award_points(current_user.id, processed * 5, 'auto_applied')
    
    return jsonify({
        'success': True,
        'processed': processed,
        'failed': failed,
        'remaining': AutoApplyQueue.query.filter_by(
            user_id=current_user.id,
            status='queued'
        ).count()
    })


@auto_apply_bp.route('/remove/<int:queue_id>', methods=['POST'])
@login_required
def remove_from_queue(queue_id):
    """Remove job from queue"""
    item = AutoApplyQueue.query.get_or_404(queue_id)
    
    # Verify ownership
    if item.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    if item.status != 'queued':
        return jsonify({'error': 'Can only remove queued items'}), 400
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True})


@auto_apply_bp.route('/clear-queue', methods=['POST'])
@login_required
def clear_queue():
    """Clear all queued items"""
    AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='queued'
    ).delete()
    
    db.session.commit()
    
    return jsonify({'success': True})


@auto_apply_bp.route('/smart-apply')
@login_required
def smart_apply():
    """Show recommended jobs for auto-apply"""
    from blueprints.recommendations import generate_recommendations_for_user
    
    # Get AI recommendations
    recommendations = generate_recommendations_for_user(current_user.id, limit=50)
    
    # Filter out already applied
    applied_ids = [a.job_id for a in Application.query.filter_by(
        user_id=current_user.id
    ).all()]
    
    recommendations = [r for r in recommendations if r.job_id not in applied_ids]
    
    # Filter out in queue
    queued_ids = [q.job_id for q in AutoApplyQueue.query.filter_by(
        user_id=current_user.id,
        status='queued'
    ).all()]
    
    recommendations = [r for r in recommendations if r.job_id not in queued_ids]
    
    # Get top 20
    recommendations = recommendations[:20]
    
    return render_template('auto_apply/smart_apply.html',
                         recommendations=recommendations)


@auto_apply_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Auto-apply settings"""
    if request.method == 'POST':
        data = request.json
        
        # Save user preferences
        # TODO: Add user settings table
        # For now, just return success
        
        return jsonify({'success': True})
    
    return render_template('auto_apply/settings.html')
