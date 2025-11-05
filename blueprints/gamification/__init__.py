"""
PSU Connect - Gamification Blueprint
Handles badges, streaks, profile completion, and points system
"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models_growth_features import (
    Badge, UserBadge, UserStreak, ProfileCompletionProgress,
    UserPoints, PointTransaction
)
from datetime import datetime, timedelta, date
import random
import string

gamification_bp = Blueprint('gamification', __name__, url_prefix='/gamification')


# =====================
# BADGE SYSTEM
# =====================

@gamification_bp.route('/badges')
@login_required
def badge_showcase():
    """Display all badges and user's progress"""
    all_badges = Badge.query.filter_by(is_active=True).order_by(Badge.points.desc()).all()
    user_earned_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    earned_badge_ids = [ub.badge_id for ub in user_earned_badges]
    
    # Group badges by category
    badges_by_category = {}
    for badge in all_badges:
        category = badge.category or 'general'
        if category not in badges_by_category:
            badges_by_category[category] = []
        badges_by_category[category].append({
            'badge': badge,
            'earned': badge.id in earned_badge_ids,
            'earned_at': next((ub.earned_at for ub in user_earned_badges if ub.badge_id == badge.id), None)
        })
    
    # Calculate completion percentage
    total_badges = len(all_badges)
    earned_count = len(user_earned_badges)
    completion_percentage = int((earned_count / total_badges * 100)) if total_badges > 0 else 0
    
    return render_template('gamification/badges.html',
                         badges_by_category=badges_by_category,
                         earned_count=earned_count,
                         total_badges=total_badges,
                         completion_percentage=completion_percentage)


@gamification_bp.route('/api/check-badges', methods=['POST'])
@login_required
def check_badges():
    """Check if user earned any new badges"""
    newly_earned = []
    
    # Check all badge criteria
    badges = Badge.query.filter_by(is_active=True).all()
    
    for badge in badges:
        # Skip if already earned
        existing = UserBadge.query.filter_by(
            user_id=current_user.id,
            badge_id=badge.id
        ).first()
        
        if existing:
            continue
        
        # Check if criteria met
        if check_badge_criteria(current_user, badge):
            user_badge = UserBadge(
                user_id=current_user.id,
                badge_id=badge.id,
                earned_at=datetime.utcnow()
            )
            db.session.add(user_badge)
            
            # Award points
            user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
            if not user_points:
                user_points = UserPoints(user_id=current_user.id)
                db.session.add(user_points)
            
            user_points.add_points(badge.points, f"Earned badge: {badge.name}")
            
            newly_earned.append({
                'id': badge.id,
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'points': badge.points
            })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'newly_earned': newly_earned,
        'count': len(newly_earned)
    })


def check_badge_criteria(user, badge):
    """Check if user meets criteria for a badge"""
    criteria = badge.criteria or {}
    
    # Resume Master - ATS score 90+
    if badge.slug == 'resume-master':
        from models import Resume
        best_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
        if best_resume and best_resume.ats_score and best_resume.ats_score >= 90:
            return True
    
    # Super Connector - 25+ connections
    elif badge.slug == 'super-connector':
        from models import Connection
        connection_count = Connection.query.filter_by(user_id=user.id, status='accepted').count()
        if connection_count >= 25:
            return True
    
    # Job Hunter - Applied to 10+ jobs
    elif badge.slug == 'job-hunter':
        from models import Application
        application_count = Application.query.filter_by(user_id=user.id).count()
        if application_count >= 10:
            return True
    
    # Interview Pro - Completed 5+ mock interviews
    elif badge.slug == 'interview-pro':
        from models_growth_features import MockInterview
        interview_count = MockInterview.query.filter_by(user_id=user.id, completed=True).count()
        if interview_count >= 5:
            return True
    
    # Lifelong Learner - Completed 3+ courses
    elif badge.slug == 'lifelong-learner':
        from models import UserCourse
        completed_count = UserCourse.query.filter_by(user_id=user.id, status='completed').count()
        if completed_count >= 3:
            return True
    
    # Skill Validator - Received 5+ endorsements
    elif badge.slug == 'skill-validator':
        from models import SkillEndorsement
        endorsement_count = SkillEndorsement.query.filter_by(endorsed_user_id=user.id).count()
        if endorsement_count >= 5:
            return True
    
    # Career Explorer - Completed all career assessments
    elif badge.slug == 'career-explorer':
        from models import CareerAssessment
        assessment_types = ['personality', 'skills', 'interests', 'values']
        completed_types = db.session.query(CareerAssessment.assessment_type).filter_by(
            user_id=user.id
        ).distinct().all()
        if len(completed_types) >= len(assessment_types):
            return True
    
    # Community Helper - Mentored 3+ students
    elif badge.slug == 'community-helper':
        from models_growth_features import MentorshipMatch, MentorProfile
        mentorship_count = MentorshipMatch.query.join(MentorProfile).filter(
            MentorProfile.user_id == user.id,
            MentorshipMatch.status == 'completed'
        ).count()
        if mentorship_count >= 3:
            return True
    
    # 7-Day Streak
    elif badge.slug == '7-day-streak':
        streak = UserStreak.query.filter_by(user_id=user.id, streak_type='login').first()
        if streak and streak.current_streak >= 7:
            return True
    
    # Profile Complete - 100% profile completion
    elif badge.slug == 'profile-complete':
        progress = ProfileCompletionProgress.query.filter_by(user_id=user.id).first()
        if progress and progress.completion_percentage == 100:
            return True
    
    return False


# =====================
# STREAK SYSTEM
# =====================

@gamification_bp.route('/streaks')
@login_required
def view_streaks():
    """View user's current streaks"""
    streaks = UserStreak.query.filter_by(user_id=current_user.id).all()
    
    streak_data = []
    for streak in streaks:
        days_since_last = (date.today() - streak.last_activity_date).days
        is_active = days_since_last <= 1
        
        streak_data.append({
            'type': streak.streak_type,
            'current': streak.current_streak,
            'longest': streak.longest_streak,
            'is_active': is_active,
            'last_activity': streak.last_activity_date,
            'freezes_available': streak.streak_freezes_available
        })
    
    return render_template('gamification/streaks.html', streaks=streak_data)


@gamification_bp.route('/api/update-streak', methods=['POST'])
@login_required
def update_streak():
    """Update user's streak"""
    data = request.json
    streak_type = data.get('type', 'login')
    
    streak = UserStreak.query.filter_by(
        user_id=current_user.id,
        streak_type=streak_type
    ).first()
    
    today = date.today()
    
    if not streak:
        # Create new streak
        streak = UserStreak(
            user_id=current_user.id,
            streak_type=streak_type,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today
        )
        db.session.add(streak)
    else:
        days_since_last = (today - streak.last_activity_date).days
        
        if days_since_last == 0:
            # Already counted today
            pass
        elif days_since_last == 1:
            # Consecutive day - increment streak
            streak.current_streak += 1
            streak.last_activity_date = today
            
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
                
                # Award points for milestones
                if streak.current_streak in [7, 30, 100, 365]:
                    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
                    if not user_points:
                        user_points = UserPoints(user_id=current_user.id)
                        db.session.add(user_points)
                    
                    points_award = {7: 50, 30: 200, 100: 500, 365: 2000}
                    user_points.add_points(
                        points_award[streak.current_streak],
                        f"{streak.current_streak}-day streak milestone!"
                    )
        elif days_since_last == 2 and streak.streak_freezes_available > 0:
            # Use streak freeze
            streak.streak_freezes_available -= 1
            streak.last_activity_date = today
        else:
            # Streak broken
            streak.current_streak = 1
            streak.last_activity_date = today
            streak.streak_freezes_available = 2  # Reset freezes
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak,
        'freezes_available': streak.streak_freezes_available
    })


# =====================
# PROFILE COMPLETION
# =====================

@gamification_bp.route('/profile-progress')
@login_required
def profile_progress():
    """View profile completion progress"""
    progress = ProfileCompletionProgress.query.filter_by(user_id=current_user.id).first()
    
    if not progress:
        progress = ProfileCompletionProgress(user_id=current_user.id)
        db.session.add(progress)
        db.session.commit()
        update_profile_progress(current_user)
        db.session.refresh(progress)
    
    tasks = [
        {'name': 'Add profile photo', 'completed': progress.has_profile_photo, 'points': 10},
        {'name': 'Write bio', 'completed': progress.has_bio, 'points': 15},
        {'name': 'Create resume', 'completed': progress.has_resume, 'points': 25},
        {'name': 'Add 3+ skills', 'completed': progress.has_skills, 'points': 15},
        {'name': 'Get 2+ endorsements', 'completed': progress.has_endorsements, 'points': 20},
        {'name': 'Make 5+ connections', 'completed': progress.has_connections, 'points': 20},
        {'name': 'Complete career assessment', 'completed': progress.has_career_assessment, 'points': 30},
        {'name': 'Apply to first job', 'completed': progress.has_applied_to_job, 'points': 25},
    ]
    
    return render_template('gamification/profile_progress.html',
                         progress=progress,
                         tasks=tasks)


def update_profile_progress(user):
    """Update user's profile completion progress"""
    progress = ProfileCompletionProgress.query.filter_by(user_id=user.id).first()
    
    if not progress:
        progress = ProfileCompletionProgress(user_id=user.id)
        db.session.add(progress)
    
    # Check each task
    progress.has_profile_photo = bool(user.profile_image or user.profile_image_url)
    progress.has_bio = bool(user.bio and len(user.bio) >= 50)
    
    from models import Resume, SkillEndorsement, Connection, CareerAssessment, Application
    
    progress.has_resume = Resume.query.filter_by(user_id=user.id).count() > 0
    progress.has_skills = len(user.skills or []) >= 3
    progress.has_endorsements = SkillEndorsement.query.filter_by(endorsed_user_id=user.id).count() >= 2
    progress.has_connections = Connection.query.filter_by(user_id=user.id, status='accepted').count() >= 5
    progress.has_career_assessment = CareerAssessment.query.filter_by(user_id=user.id).count() > 0
    progress.has_applied_to_job = Application.query.filter_by(user_id=user.id).count() > 0
    
    progress.calculate_percentage()
    progress.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    # Check if unlocked Profile Complete badge
    if progress.completion_percentage == 100:
        check_badges()


# =====================
# POINTS & LEVELS
# =====================

@gamification_bp.route('/leaderboard')
def leaderboard():
    """Display points leaderboard"""
    # Get top users by points
    top_users = db.session.query(UserPoints, User).join(User).order_by(
        UserPoints.total_points.desc()
    ).limit(100).all()
    
    leaderboard_data = []
    for idx, (points, user) in enumerate(top_users, 1):
        leaderboard_data.append({
            'rank': idx,
            'user': user,
            'points': points.total_points,
            'level': points.level,
            'rank_title': points.rank
        })
    
    # Find current user's rank
    current_user_rank = None
    if current_user.is_authenticated:
        user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
        if user_points:
            higher_ranked = UserPoints.query.filter(
                UserPoints.total_points > user_points.total_points
            ).count()
            current_user_rank = higher_ranked + 1
    
    return render_template('gamification/leaderboard.html',
                         leaderboard=leaderboard_data,
                         current_user_rank=current_user_rank)


@gamification_bp.route('/api/award-points', methods=['POST'])
@login_required
def award_points():
    """Award points to user for an action"""
    data = request.json
    amount = data.get('amount', 0)
    reason = data.get('reason', 'Action completed')
    
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    
    if not user_points:
        user_points = UserPoints(user_id=current_user.id)
        db.session.add(user_points)
    
    old_level = user_points.level
    user_points.add_points(amount, reason)
    db.session.commit()
    
    level_up = user_points.level > old_level
    
    return jsonify({
        'success': True,
        'total_points': user_points.total_points,
        'level': user_points.level,
        'level_up': level_up,
        'rank': user_points.rank,
        'points_to_next_level': user_points.points_to_next_level
    })


@gamification_bp.route('/api/points-history')
@login_required
def points_history():
    """Get user's points transaction history"""
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    
    if not user_points:
        return jsonify({'transactions': []})
    
    transactions = PointTransaction.query.filter_by(
        user_points_id=user_points.id
    ).order_by(PointTransaction.created_at.desc()).limit(50).all()
    
    return jsonify({
        'transactions': [{
            'amount': t.amount,
            'reason': t.reason,
            'balance_after': t.balance_after,
            'created_at': t.created_at.isoformat()
        } for t in transactions]
    })


# =====================
# UTILITY FUNCTIONS
# =====================

def initialize_user_gamification(user_id):
    """Initialize gamification records for new user"""
    # Create points record
    if not UserPoints.query.filter_by(user_id=user_id).first():
        points = UserPoints(user_id=user_id)
        db.session.add(points)
    
    # Create profile progress
    if not ProfileCompletionProgress.query.filter_by(user_id=user_id).first():
        progress = ProfileCompletionProgress(user_id=user_id)
        db.session.add(progress)
    
    # Create login streak
    if not UserStreak.query.filter_by(user_id=user_id, streak_type='login').first():
        streak = UserStreak(
            user_id=user_id,
            streak_type='login',
            current_streak=1,
            longest_streak=1,
            last_activity_date=date.today()
        )
        db.session.add(streak)
    
    db.session.commit()


# Register this function to be called when new users sign up
from models import User

@db.event.listens_for(User, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """Automatically initialize gamification for new users"""
    # This will be called after user is created
    pass  # Will be initialized on first login instead
