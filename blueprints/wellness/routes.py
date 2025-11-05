from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from . import wellness_bp
from extensions import db
from models_innovative_features import WellnessCheckIn, WellnessResource
from datetime import datetime, timedelta
from sqlalchemy import func

@wellness_bp.route('/')
@login_required
def index():
    """Wellness dashboard"""
    # Get recent check-ins
    recent_checkins = WellnessCheckIn.query.filter_by(
        user_id=current_user.id
    ).order_by(WellnessCheckIn.checkin_date.desc()).limit(30).all()
    
    # Calculate averages for last 7 days
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    week_checkins = [c for c in recent_checkins if c.checkin_date >= week_ago]
    
    avg_mood = sum(c.mood_rating for c in week_checkins if c.mood_rating) / len(week_checkins) if week_checkins else 0
    avg_stress = sum(c.stress_level for c in week_checkins if c.stress_level) / len(week_checkins) if week_checkins else 0
    avg_sleep = sum(float(c.hours_slept) for c in week_checkins if c.hours_slept) / len(week_checkins) if week_checkins else 0
    
    # Check if checked in today
    today = datetime.utcnow().date()
    checked_in_today = any(c.checkin_date == today for c in recent_checkins)
    
    return render_template('wellness/index.html',
                         recent_checkins=recent_checkins,
                         avg_mood=round(avg_mood, 1),
                         avg_stress=round(avg_stress, 1),
                         avg_sleep=round(avg_sleep, 1),
                         checked_in_today=checked_in_today)


@wellness_bp.route('/check-in', methods=['GET', 'POST'])
@login_required
def check_in():
    """Daily wellness check-in"""
    today = datetime.utcnow().date()
    
    # Check if already checked in today
    existing = WellnessCheckIn.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()
    
    if request.method == 'POST':
        if existing:
            # Update existing check-in
            checkin = existing
        else:
            # Create new check-in
            checkin = WellnessCheckIn(
                user_id=current_user.id,
                checkin_date=today
            )
        
        # Update fields
        checkin.mood_rating = int(request.form.get('mood_rating', 5))
        checkin.stress_level = int(request.form.get('stress_level', 5))
        checkin.energy_level = int(request.form.get('energy_level', 5))
        checkin.sleep_quality = int(request.form.get('sleep_quality', 5))
        checkin.hours_slept = float(request.form.get('hours_slept', 7))
        
        # Stress factors
        checkin.exam_stress = request.form.get('exam_stress') == 'on'
        checkin.assignment_stress = request.form.get('assignment_stress') == 'on'
        checkin.financial_stress = request.form.get('financial_stress') == 'on'
        checkin.social_stress = request.form.get('social_stress') == 'on'
        
        # Self-care activities
        checkin.exercised_today = request.form.get('exercised_today') == 'on'
        checkin.ate_healthy = request.form.get('ate_healthy') == 'on'
        checkin.socialized = request.form.get('socialized') == 'on'
        checkin.practiced_selfcare = request.form.get('practiced_selfcare') == 'on'
        
        # Notes and needs
        checkin.notes = request.form.get('notes')
        checkin.needs_counseling = request.form.get('needs_counseling') == 'on'
        checkin.needs_academic_help = request.form.get('needs_academic_help') == 'on'
        checkin.needs_financial_help = request.form.get('needs_financial_help') == 'on'
        
        if not existing:
            db.session.add(checkin)
        
        db.session.commit()
        
        # Show encouragement message based on check-in
        if checkin.mood_rating <= 3 or checkin.stress_level >= 8:
            flash('We noticed you might be struggling. Please check out our resources below.', 'warning')
        else:
            flash('Check-in complete! Keep up the great work taking care of yourself! 💚', 'success')
        
        return redirect(url_for('wellness.index'))
    
    return render_template('wellness/check_in.html', existing_checkin=existing)


@wellness_bp.route('/resources')
def resources():
    """View wellness resources"""
    category = request.args.get('category', 'all')
    
    query = WellnessResource.query.filter_by(is_active=True)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    resources = query.order_by(WellnessResource.priority.desc()).all()
    
    # Separate emergency resources
    emergency_resources = [r for r in resources if r.is_emergency]
    regular_resources = [r for r in resources if not r.is_emergency]
    
    return render_template('wellness/resources.html',
                         emergency_resources=emergency_resources,
                         regular_resources=regular_resources,
                         category=category)


@wellness_bp.route('/trends')
@login_required
def trends():
    """View wellness trends over time"""
    # Get last 30 days of check-ins
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    
    checkins = WellnessCheckIn.query.filter(
        WellnessCheckIn.user_id == current_user.id,
        WellnessCheckIn.checkin_date >= thirty_days_ago
    ).order_by(WellnessCheckIn.checkin_date.asc()).all()
    
    # Prepare data for charts
    chart_data = {
        'dates': [c.checkin_date.strftime('%m/%d') for c in checkins],
        'mood': [c.mood_rating for c in checkins],
        'stress': [c.stress_level for c in checkins],
        'sleep': [float(c.hours_slept) if c.hours_slept else 0 for c in checkins],
        'energy': [c.energy_level for c in checkins]
    }
    
    # Calculate statistics
    total_checkins = len(checkins)
    avg_mood = sum(c.mood_rating for c in checkins if c.mood_rating) / total_checkins if total_checkins else 0
    avg_stress = sum(c.stress_level for c in checkins if c.stress_level) / total_checkins if total_checkins else 0
    
    # Count stress factors
    stress_factors = {
        'Exams': sum(1 for c in checkins if c.exam_stress),
        'Assignments': sum(1 for c in checkins if c.assignment_stress),
        'Financial': sum(1 for c in checkins if c.financial_stress),
        'Social': sum(1 for c in checkins if c.social_stress)
    }
    
    # Self-care frequency
    selfcare_stats = {
        'Exercised': sum(1 for c in checkins if c.exercised_today),
        'Healthy Eating': sum(1 for c in checkins if c.ate_healthy),
        'Socialized': sum(1 for c in checkins if c.socialized),
        'Self-Care': sum(1 for c in checkins if c.practiced_selfcare)
    }
    
    return render_template('wellness/trends.html',
                         chart_data=chart_data,
                         avg_mood=round(avg_mood, 1),
                         avg_stress=round(avg_stress, 1),
                         stress_factors=stress_factors,
                         selfcare_stats=selfcare_stats,
                         total_checkins=total_checkins)


@wellness_bp.route('/crisis')
def crisis():
    """Crisis resources page"""
    return render_template('wellness/crisis.html')


@wellness_bp.route('/api/quick-checkin', methods=['POST'])
@login_required
def quick_checkin():
    """Quick mood check-in via AJAX"""
    today = datetime.utcnow().date()
    
    checkin = WellnessCheckIn.query.filter_by(
        user_id=current_user.id,
        checkin_date=today
    ).first()
    
    if not checkin:
        checkin = WellnessCheckIn(
            user_id=current_user.id,
            checkin_date=today
        )
        db.session.add(checkin)
    
    checkin.mood_rating = int(request.json.get('mood'))
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Mood logged!'})
