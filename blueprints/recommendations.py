"""
PSU Connect - AI Job Recommendations Engine
Personalized "For You" job feed using ML and behavior tracking
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import Recommendation, UserBehavior, UserAnalytics
from models import User, JobPosting, Application
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import json

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')


# =====================
# AI RECOMMENDATION ENGINE
# =====================

def calculate_job_match_score(user, job):
    """Calculate how well a job matches a user (0-1 score)"""
    score = 0.0
    factors = []
    
    # 1. Skills match (30% weight)
    if user.skills and job.required_skills:
        user_skills_lower = [s.lower() for s in (user.skills or [])]
        job_skills_lower = [s.lower() for s in (job.required_skills or [])]
        matching_skills = set(user_skills_lower) & set(job_skills_lower)
        if job_skills_lower:
            skills_score = len(matching_skills) / len(job_skills_lower)
            score += skills_score * 0.3
            factors.append(f"{len(matching_skills)} matching skills")
    
    # 2. Major relevance (25% weight)
    if user.major and job.preferred_majors:
        if user.major.lower() in [m.lower() for m in job.preferred_majors]:
            score += 0.25
            factors.append(f"Matches your {user.major} major")
    
    # 3. Experience level (15% weight)
    if job.experience_level:
        user_grad_year = user.graduation_year or datetime.now().year
        years_since_grad = datetime.now().year - user_grad_year
        
        if job.experience_level == 'entry' and years_since_grad <= 2:
            score += 0.15
            factors.append("Entry level - perfect for you")
        elif job.experience_level == 'mid' and 2 < years_since_grad <= 5:
            score += 0.15
            factors.append("Mid-level matches your experience")
        elif job.experience_level == 'senior' and years_since_grad > 5:
            score += 0.15
            factors.append("Senior role for experienced professional")
    
    # 4. Location preference (10% weight)
    # Assume remote or location in user's state is preferred
    if job.location:
        if 'remote' in job.location.lower():
            score += 0.10
            factors.append("Remote opportunity")
        # Could check against user location if we had it
    
    # 5. Company preference (10% weight)
    # Check if user has viewed this company's other jobs
    from models import Company
    if job.company_id:
        viewed_same_company = UserBehavior.query.filter_by(
            user_id=user.id,
            item_type='job',
            action_type='view'
        ).join(JobPosting, UserBehavior.item_id == JobPosting.id).filter(
            JobPosting.company_id == job.company_id
        ).count()
        
        if viewed_same_company > 0:
            score += 0.10
            factors.append(f"You've viewed {viewed_same_company} jobs at this company")
    
    # 6. Behavioral signals (10% weight)
    # Jobs similar to ones user applied to or saved
    similar_behaviors = UserBehavior.query.filter(
        UserBehavior.user_id == user.id,
        UserBehavior.item_type == 'job',
        UserBehavior.action_type.in_(['apply', 'save'])
    ).count()
    
    if similar_behaviors > 0:
        score += min(0.10, similar_behaviors * 0.02)
        factors.append("Similar to jobs you've applied to")
    
    return min(score, 1.0), factors


def generate_recommendations_for_user(user_id, limit=20):
    """Generate fresh job recommendations for user"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get jobs user hasn't applied to or viewed recently
    viewed_job_ids = db.session.query(UserBehavior.item_id).filter(
        UserBehavior.user_id == user_id,
        UserBehavior.item_type == 'job',
        UserBehavior.timestamp > datetime.utcnow() - timedelta(days=7)
    ).subquery()
    
    applied_job_ids = db.session.query(Application.job_id).filter(
        Application.user_id == user_id
    ).subquery()
    
    # Get active jobs
    candidate_jobs = JobPosting.query.filter(
        JobPosting.is_active == True,
        JobPosting.id.notin_(viewed_job_ids),
        JobPosting.id.notin_(applied_job_ids)
    ).all()
    
    # Score all candidate jobs
    scored_jobs = []
    for job in candidate_jobs:
        score, factors = calculate_job_match_score(user, job)
        if score > 0.3:  # Only recommend if score > 30%
            scored_jobs.append({
                'job': job,
                'score': score,
                'factors': factors
            })
    
    # Sort by score and take top N
    scored_jobs.sort(key=lambda x: x['score'], reverse=True)
    top_jobs = scored_jobs[:limit]
    
    # Save recommendations to database
    for job_data in top_jobs:
        # Check if recommendation already exists
        existing = Recommendation.query.filter_by(
            user_id=user_id,
            item_id=job_data['job'].id,
            item_type='job_posting'
        ).first()
        
        if not existing:
            rec = Recommendation(
                user_id=user_id,
                recommendation_type='job',
                item_id=job_data['job'].id,
                item_type='job_posting',
                score=job_data['score'],
                reasoning='; '.join(job_data['factors']),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(rec)
    
    db.session.commit()
    
    return top_jobs


@recommendations_bp.route('/for-you')
@login_required
def for_you_feed():
    """Show personalized 'For You' job recommendations"""
    # Check if we need to generate fresh recommendations
    recent_recs = Recommendation.query.filter(
        Recommendation.user_id == current_user.id,
        Recommendation.recommendation_type == 'job',
        Recommendation.is_dismissed == False,
        Recommendation.created_at > datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    if recent_recs < 10:
        # Generate fresh recommendations
        generate_recommendations_for_user(current_user.id)
    
    # Get recommendations
    recommendations = Recommendation.query.filter(
        Recommendation.user_id == current_user.id,
        Recommendation.recommendation_type == 'job',
        Recommendation.is_dismissed == False,
        Recommendation.is_viewed == False,
        or_(
            Recommendation.expires_at == None,
            Recommendation.expires_at > datetime.utcnow()
        )
    ).order_by(desc(Recommendation.score)).limit(20).all()
    
    # Get job details
    job_recommendations = []
    for rec in recommendations:
        job = JobPosting.query.get(rec.item_id)
        if job and job.is_active:
            job_recommendations.append({
                'recommendation': rec,
                'job': job,
                'match_score': int(rec.score * 100),
                'reasons': rec.reasoning.split('; ') if rec.reasoning else []
            })
    
    return render_template('recommendations/for_you.html',
                         recommendations=job_recommendations)


@recommendations_bp.route('/api/refresh', methods=['POST'])
@login_required
def refresh_recommendations():
    """Generate fresh recommendations"""
    generate_recommendations_for_user(current_user.id, limit=30)
    return jsonify({'success': True, 'message': 'Recommendations refreshed!'})


@recommendations_bp.route('/api/view/<int:recommendation_id>', methods=['POST'])
@login_required
def mark_viewed(recommendation_id):
    """Mark recommendation as viewed"""
    rec = Recommendation.query.get_or_404(recommendation_id)
    
    if rec.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    rec.is_viewed = True
    db.session.commit()
    
    # Track behavior
    behavior = UserBehavior(
        user_id=current_user.id,
        action_type='view',
        item_type='job',
        item_id=rec.item_id
    )
    db.session.add(behavior)
    db.session.commit()
    
    return jsonify({'success': True})


@recommendations_bp.route('/api/dismiss/<int:recommendation_id>', methods=['POST'])
@login_required
def dismiss_recommendation(recommendation_id):
    """Dismiss a recommendation"""
    rec = Recommendation.query.get_or_404(recommendation_id)
    
    if rec.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    rec.is_dismissed = True
    db.session.commit()
    
    return jsonify({'success': True})


@recommendations_bp.route('/api/act/<int:recommendation_id>', methods=['POST'])
@login_required
def mark_acted(recommendation_id):
    """Mark recommendation as acted upon (applied, saved, etc.)"""
    rec = Recommendation.query.get_or_404(recommendation_id)
    
    if rec.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    rec.is_acted_upon = True
    db.session.commit()
    
    return jsonify({'success': True})


# =====================
# PEOPLE ALSO VIEWED
# =====================

def get_similar_jobs(job_id, limit=5):
    """Get jobs similar to given job"""
    job = JobPosting.query.get(job_id)
    if not job:
        return []
    
    # Find jobs with similar skills or same company
    similar = JobPosting.query.filter(
        JobPosting.id != job_id,
        JobPosting.is_active == True,
        or_(
            JobPosting.company_id == job.company_id,
            # Could add skill matching here
        )
    ).limit(limit).all()
    
    return similar


def get_similar_users(user_id, limit=5):
    """Get users with similar profile (same major, grad year, etc.)"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    similar = User.query.filter(
        User.id != user_id,
        User.major == user.major,
        User.graduation_year.between(user.graduation_year - 2, user.graduation_year + 2)
    ).limit(limit).all()
    
    return similar


@recommendations_bp.route('/api/people-also-viewed/job/<int:job_id>')
def people_also_viewed_job(job_id):
    """Get jobs that people who viewed this job also viewed"""
    # Get users who viewed this job
    viewer_ids = db.session.query(UserBehavior.user_id).filter(
        UserBehavior.item_type == 'job',
        UserBehavior.item_id == job_id,
        UserBehavior.action_type == 'view'
    ).distinct().subquery()
    
    # Get other jobs those users viewed
    also_viewed = db.session.query(
        UserBehavior.item_id,
        func.count(UserBehavior.user_id).label('view_count')
    ).filter(
        UserBehavior.user_id.in_(viewer_ids),
        UserBehavior.item_type == 'job',
        UserBehavior.item_id != job_id,
        UserBehavior.action_type == 'view'
    ).group_by(UserBehavior.item_id).order_by(
        desc('view_count')
    ).limit(5).all()
    
    # Get job details
    jobs = []
    for job_id, count in also_viewed:
        job = JobPosting.query.get(job_id)
        if job and job.is_active:
            jobs.append({
                'job': job.to_dict() if hasattr(job, 'to_dict') else {'id': job.id, 'title': job.title},
                'view_count': count
            })
    
    return jsonify({'jobs': jobs})


@recommendations_bp.route('/api/people-also-viewed/profile/<int:user_id>')
def people_also_viewed_profile(user_id):
    """Get profiles that people who viewed this profile also viewed"""
    # Similar logic for user profiles
    similar_users = get_similar_users(user_id, 5)
    
    return jsonify({
        'users': [{
            'id': u.id,
            'name': u.full_name,
            'major': u.major,
            'graduation_year': u.graduation_year
        } for u in similar_users]
    })


# =====================
# BEHAVIOR TRACKING
# =====================

@recommendations_bp.route('/api/track', methods=['POST'])
@login_required
def track_behavior():
    """Track user behavior for recommendation engine"""
    data = request.json
    
    behavior = UserBehavior(
        user_id=current_user.id,
        action_type=data.get('action'),  # view, click, apply, save, share
        item_type=data.get('item_type'),  # job, profile, course, event
        item_id=data.get('item_id'),
        metadata=data.get('metadata', {}),
        session_id=data.get('session_id')
    )
    
    db.session.add(behavior)
    db.session.commit()
    
    return jsonify({'success': True})


# =====================
# COLLABORATIVE FILTERING
# =====================

def get_collaborative_recommendations(user_id, limit=10):
    """Get recommendations based on similar users' behavior"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Find similar users (same major, similar grad year)
    similar_users = User.query.filter(
        User.id != user_id,
        User.major == user.major,
        User.graduation_year.between(user.graduation_year - 1, user.graduation_year + 1)
    ).limit(20).all()
    
    similar_user_ids = [u.id for u in similar_users]
    
    # Get jobs those users applied to
    popular_jobs = db.session.query(
        Application.job_id,
        func.count(Application.user_id).label('application_count')
    ).filter(
        Application.user_id.in_(similar_user_ids)
    ).group_by(Application.job_id).order_by(
        desc('application_count')
    ).limit(limit).all()
    
    # Filter out jobs user has already applied to
    user_applied_ids = [a.job_id for a in Application.query.filter_by(user_id=user_id).all()]
    
    recommendations = []
    for job_id, count in popular_jobs:
        if job_id not in user_applied_ids:
            job = JobPosting.query.get(job_id)
            if job and job.is_active:
                recommendations.append({
                    'job': job,
                    'application_count': count,
                    'reasoning': f'{count} students with your major applied to this'
                })
    
    return recommendations


@recommendations_bp.route('/collaborative')
@login_required
def collaborative_feed():
    """Show collaborative filtering recommendations"""
    recommendations = get_collaborative_recommendations(current_user.id, 15)
    
    return render_template('recommendations/collaborative.html',
                         recommendations=recommendations)
