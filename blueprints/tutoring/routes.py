from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import tutoring_bp
from extensions import db
from models_innovative_features import TutorProfile, TutoringSession
from datetime import datetime
import json

@tutoring_bp.route('/')
def index():
    """Browse tutors"""
    subject = request.args.get('subject', '')
    max_rate = request.args.get('max_rate')
    
    query = TutorProfile.query.filter_by(is_active=True)
    
    if subject:
        query = query.filter(TutorProfile.subjects.like(f'%{subject}%'))
    
    if max_rate:
        query = query.filter(TutorProfile.hourly_rate <= float(max_rate))
    
    tutors = query.order_by(TutorProfile.avg_rating.desc()).all()
    
    return render_template('tutoring/index.html', tutors=tutors)


@tutoring_bp.route('/tutor/<int:tutor_id>')
def view_tutor(tutor_id):
    """View tutor profile"""
    profile = TutorProfile.query.get_or_404(tutor_id)
    
    # Get reviews
    sessions = TutoringSession.query.filter_by(
        tutor_id=profile.user_id,
        status='completed'
    ).filter(
        TutoringSession.student_review.isnot(None)
    ).order_by(TutoringSession.reviewed_at.desc()).limit(10).all()
    
    return render_template('tutoring/view_tutor.html', profile=profile, sessions=sessions)


@tutoring_bp.route('/become-tutor', methods=['GET', 'POST'])
@login_required
def become_tutor():
    """Create tutor profile"""
    # Check if already a tutor
    existing = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        if existing:
            profile = existing
        else:
            profile = TutorProfile(user_id=current_user.id)
        
        profile.bio = request.form.get('bio')
        profile.major = request.form.get('major')
        profile.year = request.form.get('year')
        profile.gpa = float(request.form.get('gpa', 0))
        profile.subjects = request.form.get('subjects')  # JSON array from form
        profile.availability = request.form.get('availability')
        profile.preferred_location = request.form.get('preferred_location')
        profile.offers_online = request.form.get('offers_online') == 'on'
        profile.offers_in_person = request.form.get('offers_in_person') == 'on'
        profile.hourly_rate = float(request.form.get('hourly_rate'))
        profile.first_session_free = request.form.get('first_session_free') == 'on'
        profile.tutoring_experience = request.form.get('tutoring_experience')
        
        if not existing:
            db.session.add(profile)
        
        db.session.commit()
        
        flash('Tutor profile created!', 'success')
        return redirect(url_for('tutoring.view_tutor', tutor_id=profile.id))
    
    return render_template('tutoring/become_tutor.html', existing=existing)


@tutoring_bp.route('/book/<int:tutor_id>', methods=['POST'])
@login_required
def book_session(tutor_id):
    """Book tutoring session"""
    profile = TutorProfile.query.filter_by(user_id=tutor_id).first_or_404()
    
    session = TutoringSession(
        tutor_id=tutor_id,
        student_id=current_user.id,
        subject=request.form.get('subject'),
        topic=request.form.get('topic'),
        scheduled_date=datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%dT%H:%M'),
        duration_minutes=int(request.form.get('duration', 60)),
        is_online=request.form.get('is_online') == 'on',
        location=request.form.get('location')
    )
    
    db.session.add(session)
    db.session.commit()
    
    flash('Session booked! The tutor will be notified.', 'success')
    return redirect(url_for('tutoring.my_sessions'))


@tutoring_bp.route('/my-sessions')
@login_required
def my_sessions():
    """View user's tutoring sessions"""
    # Sessions as student
    as_student = TutoringSession.query.filter_by(student_id=current_user.id).order_by(TutoringSession.scheduled_date.desc()).all()
    
    # Sessions as tutor
    as_tutor = TutoringSession.query.filter_by(tutor_id=current_user.id).order_by(TutoringSession.scheduled_date.desc()).all()
    
    return render_template('tutoring/my_sessions.html', as_student=as_student, as_tutor=as_tutor)


@tutoring_bp.route('/review/<int:session_id>', methods=['POST'])
@login_required
def review_session(session_id):
    """Leave review for tutor"""
    session = TutoringSession.query.get_or_404(session_id)
    
    if session.student_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('tutoring.index'))
    
    session.student_rating = int(request.form.get('rating'))
    session.student_review = request.form.get('review')
    session.reviewed_at = datetime.utcnow()
    session.status = 'completed'
    
    # Update tutor profile ratings
    profile = TutorProfile.query.filter_by(user_id=session.tutor_id).first()
    if profile:
        profile.total_sessions += 1
        profile.total_reviews += 1
        
        # Recalculate average rating
        all_ratings = db.session.query(TutoringSession.student_rating).filter_by(
            tutor_id=session.tutor_id
        ).filter(TutoringSession.student_rating.isnot(None)).all()
        
        if all_ratings:
            profile.avg_rating = sum(r[0] for r in all_ratings) / len(all_ratings)
    
    db.session.commit()
    
    flash('Review submitted!', 'success')
    return redirect(url_for('tutoring.my_sessions'))
