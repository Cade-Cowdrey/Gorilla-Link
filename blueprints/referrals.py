"""
PSU Connect - Referral Program System
Viral growth engine with tracking and rewards
"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import Referral, UserPoints
from models import User
import string
import random
from datetime import datetime
from sqlalchemy import func

referral_bp = Blueprint('referrals', __name__, url_prefix='/referrals')


def generate_referral_code():
    """Generate unique referral code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        existing = Referral.query.filter_by(referral_code=code).first()
        if not existing:
            return code


@referral_bp.route('/dashboard')
@login_required
def dashboard():
    """Referral dashboard showing stats and code"""
    # Get or create user's referral code
    user_referral = Referral.query.filter_by(
        referrer_id=current_user.id,
        referred_user_id=None
    ).first()
    
    if not user_referral:
        user_referral = Referral(
            referrer_id=current_user.id,
            referral_code=generate_referral_code()
        )
        db.session.add(user_referral)
        db.session.commit()
    
    # Get referral stats
    total_referrals = Referral.query.filter_by(referrer_id=current_user.id).count()
    completed_referrals = Referral.query.filter_by(
        referrer_id=current_user.id,
        status='completed'
    ).count()
    pending_referrals = Referral.query.filter_by(
        referrer_id=current_user.id,
        status='pending'
    ).count()
    
    # Get recent referrals
    recent = Referral.query.filter_by(
        referrer_id=current_user.id
    ).order_by(Referral.referred_at.desc()).limit(10).all()
    
    # Get leaderboard
    top_referrers = db.session.query(
        User,
        func.count(Referral.id).label('referral_count')
    ).join(Referral, User.id == Referral.referrer_id).filter(
        Referral.status == 'completed'
    ).group_by(User.id).order_by(func.count(Referral.id).desc()).limit(10).all()
    
    return render_template('referrals/dashboard.html',
                         referral_code=user_referral.referral_code,
                         total_referrals=total_referrals,
                         completed_referrals=completed_referrals,
                         pending_referrals=pending_referrals,
                         recent_referrals=recent,
                         leaderboard=top_referrers)


@referral_bp.route('/send-invite', methods=['POST'])
@login_required
def send_invite():
    """Send referral invitation via email"""
    email = request.form.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email required'}), 400
    
    # Check if already referred
    existing = Referral.query.filter_by(
        referrer_id=current_user.id,
        referred_email=email
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Already invited this email'}), 400
    
    # Get user's referral code
    user_referral = Referral.query.filter_by(
        referrer_id=current_user.id,
        referred_user_id=None
    ).first()
    
    if not user_referral:
        user_referral = Referral(
            referrer_id=current_user.id,
            referral_code=generate_referral_code()
        )
        db.session.add(user_referral)
        db.session.commit()
    
    # Create referral record
    referral = Referral(
        referrer_id=current_user.id,
        referral_code=user_referral.referral_code,
        referred_email=email,
        status='pending'
    )
    db.session.add(referral)
    db.session.commit()
    
    # TODO: Send email with referral link
    # For now, return success
    referral_link = url_for('auth.register', ref=user_referral.referral_code, _external=True)
    
    return jsonify({
        'success': True,
        'message': 'Invitation sent!',
        'referral_link': referral_link
    })


@referral_bp.route('/process/<code>')
def process_referral(code):
    """Process referral when new user signs up"""
    # Find referral by code
    referral = Referral.query.filter_by(referral_code=code).first()
    
    if not referral:
        flash('Invalid referral code', 'error')
        return redirect(url_for('auth.register'))
    
    # Store in session to complete after registration
    from flask import session
    session['referral_code'] = code
    
    flash(f'You were referred by {referral.referrer.full_name}! Complete signup to get bonus features.', 'info')
    return redirect(url_for('auth.register'))


def complete_referral(new_user_id, referral_code):
    """Complete referral after user signs up"""
    # Find all pending referrals with this code
    referrals = Referral.query.filter_by(
        referral_code=referral_code,
        status='pending'
    ).all()
    
    for referral in referrals:
        referral.referred_user_id = new_user_id
        referral.status = 'completed'
        referral.completed_at = datetime.utcnow()
        
        # Award rewards
        award_referral_rewards(referral.referrer_id, new_user_id)
        
        referral.status = 'rewarded'
        referral.rewarded_at = datetime.utcnow()
    
    db.session.commit()


def award_referral_rewards(referrer_id, referred_user_id):
    """Award rewards to both referrer and referred user"""
    # Reward referrer: 1 month free premium + 100 points
    referrer_points = UserPoints.query.filter_by(user_id=referrer_id).first()
    if not referrer_points:
        referrer_points = UserPoints(user_id=referrer_id)
        db.session.add(referrer_points)
    
    referrer_points.add_points(100, 'Successful referral')
    
    # Reward referred user: 50% off first year + 50 points
    referred_points = UserPoints.query.filter_by(user_id=referred_user_id).first()
    if not referred_points:
        referred_points = UserPoints(user_id=referred_user_id)
        db.session.add(referred_points)
    
    referred_points.add_points(50, 'Signed up via referral')
    
    db.session.commit()


@referral_bp.route('/api/stats')
@login_required
def get_stats():
    """Get referral statistics"""
    stats = {
        'total': Referral.query.filter_by(referrer_id=current_user.id).count(),
        'completed': Referral.query.filter_by(referrer_id=current_user.id, status='completed').count(),
        'pending': Referral.query.filter_by(referrer_id=current_user.id, status='pending').count(),
        'rewarded': Referral.query.filter_by(referrer_id=current_user.id, status='rewarded').count()
    }
    
    return jsonify(stats)


@referral_bp.route('/leaderboard')
def leaderboard():
    """Public referral leaderboard"""
    top_referrers = db.session.query(
        User,
        func.count(Referral.id).label('referral_count')
    ).join(Referral, User.id == Referral.referrer_id).filter(
        Referral.status.in_(['completed', 'rewarded'])
    ).group_by(User.id).order_by(func.count(Referral.id).desc()).limit(50).all()
    
    return render_template('referrals/leaderboard.html', leaderboard=top_referrers)
