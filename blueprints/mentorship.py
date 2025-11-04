"""
PSU Connect - Mentorship Matching System
AI-powered matching of mentors and mentees
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import MentorshipProgram, MentorProfile, MenteeProfile, MentorshipMatch, MentorshipSession
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import random

mentorship_bp = Blueprint('mentorship', __name__, url_prefix='/mentorship')


def calculate_match_score(mentor_profile, mentee_profile):
    """Calculate match score between mentor and mentee using AI-like algorithm"""
    score = 0
    factors = []
    
    # Major match (30%)
    if mentor_profile.expertise_areas and mentee_profile.career_interests:
        expertise = set([e.lower() for e in mentor_profile.expertise_areas])
        interests = set([i.lower() for i in mentee_profile.career_interests])
        overlap = len(expertise.intersection(interests))
        if overlap > 0:
            score += 30 * (overlap / max(len(expertise), len(interests)))
            factors.append(f"{overlap} matching interests")
    
    # Industry match (25%)
    if mentor_profile.industry and mentee_profile.target_industry:
        if mentor_profile.industry.lower() == mentee_profile.target_industry.lower():
            score += 25
            factors.append("Same industry")
    
    # Skills match (20%)
    if mentor_profile.skills and mentee_profile.skills_to_develop:
        mentor_skills = set([s.lower() for s in mentor_profile.skills])
        needed_skills = set([s.lower() for s in mentee_profile.skills_to_develop])
        overlap = len(mentor_skills.intersection(needed_skills))
        if overlap > 0:
            score += 20 * (overlap / len(needed_skills))
            factors.append(f"Can teach {overlap} skills you want")
    
    # Location compatibility (10%)
    if mentor_profile.availability_mode and mentee_profile.preferred_meeting_mode:
        if mentor_profile.availability_mode == mentee_profile.preferred_meeting_mode:
            score += 10
            factors.append("Meeting mode match")
        elif mentor_profile.availability_mode == 'both' or mentee_profile.preferred_meeting_mode == 'both':
            score += 5
    
    # Experience level (10%)
    if mentor_profile.years_experience:
        if mentor_profile.years_experience >= 5:
            score += 10
            factors.append(f"{mentor_profile.years_experience} years experience")
        elif mentor_profile.years_experience >= 3:
            score += 7
        elif mentor_profile.years_experience >= 1:
            score += 5
    
    # Availability (5%)
    if mentor_profile.max_mentees and mentor_profile.current_mentees < mentor_profile.max_mentees:
        score += 5
        factors.append("Available now")
    
    return round(score), factors


@mentorship_bp.route('/')
def index():
    """Mentorship program overview"""
    programs = MentorshipProgram.query.filter_by(is_active=True).all()
    
    # Get stats
    total_mentors = MentorProfile.query.filter_by(is_active=True).count()
    total_mentees = MenteeProfile.query.filter_by(is_active=True).count()
    active_matches = MentorshipMatch.query.filter_by(status='active').count()
    
    return render_template('mentorship/index.html',
                         programs=programs,
                         total_mentors=total_mentors,
                         total_mentees=total_mentees,
                         active_matches=active_matches)


@mentorship_bp.route('/become-mentor', methods=['GET', 'POST'])
@login_required
def become_mentor():
    """Sign up as a mentor"""
    # Check if already a mentor
    existing = MentorProfile.query.filter_by(user_id=current_user.id).first()
    if existing:
        return redirect(url_for('mentorship.mentor_dashboard'))
    
    if request.method == 'POST':
        data = request.form
        
        profile = MentorProfile(
            user_id=current_user.id,
            program_id=data.get('program_id', type=int),
            bio=data.get('bio'),
            expertise_areas=data.getlist('expertise_areas'),
            skills=data.getlist('skills'),
            industry=data.get('industry'),
            company=data.get('company'),
            job_title=data.get('job_title'),
            years_experience=data.get('years_experience', type=int),
            max_mentees=data.get('max_mentees', type=int, default=2),
            availability_mode=data.get('availability_mode'),
            availability_hours=data.get('availability_hours', type=int),
            is_active=True
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return redirect(url_for('mentorship.mentor_dashboard'))
    
    programs = MentorshipProgram.query.filter_by(is_active=True).all()
    return render_template('mentorship/become_mentor.html', programs=programs)


@mentorship_bp.route('/find-mentor', methods=['GET', 'POST'])
@login_required
def find_mentor():
    """Sign up as a mentee"""
    # Check if already a mentee
    existing = MenteeProfile.query.filter_by(user_id=current_user.id).first()
    if existing:
        return redirect(url_for('mentorship.mentee_dashboard'))
    
    if request.method == 'POST':
        data = request.form
        
        profile = MenteeProfile(
            user_id=current_user.id,
            program_id=data.get('program_id', type=int),
            bio=data.get('bio'),
            career_interests=data.getlist('career_interests'),
            skills_to_develop=data.getlist('skills_to_develop'),
            target_industry=data.get('target_industry'),
            current_challenges=data.get('current_challenges'),
            goals=data.get('goals'),
            preferred_meeting_mode=data.get('preferred_meeting_mode'),
            is_active=True
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return redirect(url_for('mentorship.mentee_dashboard'))
    
    programs = MentorshipProgram.query.filter_by(is_active=True).all()
    return render_template('mentorship/find_mentor.html', programs=programs)


@mentorship_bp.route('/mentor/dashboard')
@login_required
def mentor_dashboard():
    """Mentor dashboard"""
    profile = MentorProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get matches
    matches = MentorshipMatch.query.filter_by(
        mentor_id=profile.id
    ).order_by(desc(MentorshipMatch.created_at)).all()
    
    # Get upcoming sessions
    upcoming = MentorshipSession.query.join(MentorshipMatch).filter(
        MentorshipMatch.mentor_id == profile.id,
        MentorshipSession.scheduled_time > datetime.utcnow(),
        MentorshipSession.status == 'scheduled'
    ).order_by(MentorshipSession.scheduled_time).limit(5).all()
    
    # Get stats
    total_sessions = MentorshipSession.query.join(MentorshipMatch).filter(
        MentorshipMatch.mentor_id == profile.id,
        MentorshipSession.status == 'completed'
    ).count()
    
    return render_template('mentorship/mentor_dashboard.html',
                         profile=profile,
                         matches=matches,
                         upcoming=upcoming,
                         total_sessions=total_sessions)


@mentorship_bp.route('/mentee/dashboard')
@login_required
def mentee_dashboard():
    """Mentee dashboard"""
    profile = MenteeProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get match
    match = MentorshipMatch.query.filter_by(
        mentee_id=profile.id,
        status='active'
    ).first()
    
    # Get upcoming sessions
    upcoming = []
    if match:
        upcoming = MentorshipSession.query.filter_by(
            match_id=match.id,
            status='scheduled'
        ).filter(
            MentorshipSession.scheduled_time > datetime.utcnow()
        ).order_by(MentorshipSession.scheduled_time).all()
    
    # Get recommended mentors
    recommendations = []
    if not match:
        mentors = MentorProfile.query.filter_by(is_active=True).filter(
            MentorProfile.current_mentees < MentorProfile.max_mentees
        ).all()
        
        scored = []
        for mentor in mentors:
            score, factors = calculate_match_score(mentor, profile)
            if score >= 30:  # Minimum 30% match
                scored.append({
                    'mentor': mentor,
                    'score': score,
                    'factors': factors
                })
        
        # Sort by score
        recommendations = sorted(scored, key=lambda x: x['score'], reverse=True)[:10]
    
    return render_template('mentorship/mentee_dashboard.html',
                         profile=profile,
                         match=match,
                         upcoming=upcoming,
                         recommendations=recommendations)


@mentorship_bp.route('/request-mentor/<int:mentor_id>', methods=['POST'])
@login_required
def request_mentor(mentor_id):
    """Request a specific mentor"""
    mentee_profile = MenteeProfile.query.filter_by(user_id=current_user.id).first()
    if not mentee_profile:
        return jsonify({'error': 'Create mentee profile first'}), 400
    
    # Check if already has active match
    existing_match = MentorshipMatch.query.filter_by(
        mentee_id=mentee_profile.id,
        status='active'
    ).first()
    
    if existing_match:
        return jsonify({'error': 'You already have an active mentor'}), 400
    
    mentor_profile = MentorProfile.query.get_or_404(mentor_id)
    
    # Check mentor availability
    if mentor_profile.current_mentees >= mentor_profile.max_mentees:
        return jsonify({'error': 'Mentor has reached maximum mentees'}), 400
    
    data = request.json
    message = data.get('message', '')
    
    # Create match request
    match = MentorshipMatch(
        mentor_id=mentor_id,
        mentee_id=mentee_profile.id,
        status='pending',
        mentee_message=message
    )
    
    db.session.add(match)
    db.session.commit()
    
    # TODO: Send notification to mentor
    
    return jsonify({'success': True, 'match_id': match.id})


@mentorship_bp.route('/match/<int:match_id>/respond', methods=['POST'])
@login_required
def respond_to_match(match_id):
    """Mentor responds to match request"""
    match = MentorshipMatch.query.get_or_404(match_id)
    
    # Verify is mentor
    if match.mentor.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.json
    action = data.get('action')  # accept or decline
    
    if action == 'accept':
        match.status = 'active'
        match.matched_at = datetime.utcnow()
        
        # Update mentor mentee count
        match.mentor.current_mentees += 1
        
        # Award points
        from blueprints.gamification import award_points
        award_points(current_user.id, 50, 'mentor_accepted')
        award_points(match.mentee.user_id, 25, 'mentor_matched')
        
    else:  # decline
        match.status = 'declined'
    
    db.session.commit()
    
    return jsonify({'success': True})


@mentorship_bp.route('/match/<int:match_id>/schedule', methods=['POST'])
@login_required
def schedule_session(match_id):
    """Schedule a mentorship session"""
    match = MentorshipMatch.query.get_or_404(match_id)
    
    # Verify access
    if match.mentor.user_id != current_user.id and match.mentee.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.json
    
    session = MentorshipSession(
        match_id=match_id,
        scheduled_time=datetime.fromisoformat(data.get('datetime')),
        duration_minutes=data.get('duration', 60),
        meeting_link=data.get('meeting_link'),
        agenda=data.get('agenda'),
        status='scheduled'
    )
    
    db.session.add(session)
    db.session.commit()
    
    # TODO: Send calendar invites
    
    return jsonify({'success': True, 'session_id': session.id})


@mentorship_bp.route('/session/<int:session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    """Mark session as complete and add notes"""
    session = MentorshipSession.query.get_or_404(session_id)
    
    # Verify access
    if session.match.mentor.user_id != current_user.id and session.match.mentee.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.json
    
    session.status = 'completed'
    session.notes = data.get('notes')
    session.mentor_rating = data.get('mentor_rating')
    session.mentee_rating = data.get('mentee_rating')
    
    # Update match total hours
    session.match.total_hours += session.duration_minutes / 60
    
    db.session.commit()
    
    # Award points
    from blueprints.gamification import award_points
    if current_user.id == session.match.mentor.user_id:
        award_points(current_user.id, 15, 'mentorship_session')
    
    return jsonify({'success': True})


@mentorship_bp.route('/browse-mentors')
def browse_mentors():
    """Browse all mentors"""
    industry = request.args.get('industry')
    expertise = request.args.get('expertise')
    page = request.args.get('page', 1, type=int)
    
    query = MentorProfile.query.filter_by(is_active=True)
    
    if industry:
        query = query.filter_by(industry=industry)
    
    if expertise:
        query = query.filter(MentorProfile.expertise_areas.contains([expertise]))
    
    mentors = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get unique industries and expertise for filters
    industries = db.session.query(
        func.distinct(MentorProfile.industry)
    ).filter(MentorProfile.is_active == True).all()
    industries = [i[0] for i in industries if i[0]]
    
    return render_template('mentorship/browse_mentors.html',
                         mentors=mentors,
                         industries=industries,
                         selected_industry=industry,
                         selected_expertise=expertise)
