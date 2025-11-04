"""
PSU Connect - User Analytics Dashboard
Personal metrics and insights with Chart.js visualizations
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import UserAnalytics
from models import Application, JobPosting, User
from sqlalchemy import func, desc, extract
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


def get_or_create_analytics(user_id):
    """Get or create analytics record for user"""
    analytics = UserAnalytics.query.filter_by(user_id=user_id).first()
    
    if not analytics:
        analytics = UserAnalytics(user_id=user_id)
        db.session.add(analytics)
        db.session.commit()
    
    return analytics


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """Main analytics dashboard"""
    analytics = get_or_create_analytics(current_user.id)
    
    # Calculate additional metrics
    total_applications = Application.query.filter_by(user_id=current_user.id).count()
    
    response_rate = 0
    if total_applications > 0:
        responses = Application.query.filter(
            Application.user_id == current_user.id,
            Application.status.in_(['interview', 'offer', 'accepted'])
        ).count()
        response_rate = round((responses / total_applications) * 100, 1)
    
    # Get recent activity
    recent_applications = Application.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(Application.applied_at)).limit(5).all()
    
    # Calculate percentile ranking
    all_profile_views = db.session.query(func.avg(UserAnalytics.profile_views)).scalar() or 0
    percentile = 50
    if all_profile_views > 0:
        better_than = db.session.query(func.count(UserAnalytics.id)).filter(
            UserAnalytics.profile_views < analytics.profile_views
        ).scalar()
        total_users = db.session.query(func.count(UserAnalytics.id)).scalar()
        if total_users > 0:
            percentile = round((better_than / total_users) * 100)
    
    return render_template('analytics/dashboard.html',
                         analytics=analytics,
                         total_applications=total_applications,
                         response_rate=response_rate,
                         recent_applications=recent_applications,
                         percentile=percentile)


@analytics_bp.route('/api/profile-views')
@login_required
def profile_views_data():
    """Get profile views over time (for Chart.js)"""
    analytics = get_or_create_analytics(current_user.id)
    
    # Get last 30 days
    views_by_day = analytics.views_by_day or {}
    
    # Generate last 30 days
    labels = []
    data = []
    
    for i in range(29, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append((datetime.utcnow() - timedelta(days=i)).strftime('%b %d'))
        data.append(views_by_day.get(date, 0))
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@analytics_bp.route('/api/resume-downloads')
@login_required
def resume_downloads_data():
    """Get resume downloads over time"""
    analytics = get_or_create_analytics(current_user.id)
    
    downloads_by_day = analytics.downloads_by_day or {}
    
    labels = []
    data = []
    
    for i in range(29, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        labels.append((datetime.utcnow() - timedelta(days=i)).strftime('%b %d'))
        data.append(downloads_by_day.get(date, 0))
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@analytics_bp.route('/api/application-funnel')
@login_required
def application_funnel_data():
    """Get application funnel data"""
    submitted = Application.query.filter_by(
        user_id=current_user.id,
        status='submitted'
    ).count()
    
    viewed = Application.query.filter_by(
        user_id=current_user.id,
        status='viewed'
    ).count()
    
    interview = Application.query.filter_by(
        user_id=current_user.id,
        status='interview'
    ).count()
    
    offer = Application.query.filter(
        Application.user_id == current_user.id,
        Application.status.in_(['offer', 'accepted'])
    ).count()
    
    return jsonify({
        'labels': ['Submitted', 'Viewed', 'Interview', 'Offer'],
        'data': [submitted, viewed, interview, offer]
    })


@analytics_bp.route('/api/application-timeline')
@login_required
def application_timeline_data():
    """Get applications over time"""
    # Get applications by month for last 6 months
    applications = Application.query.filter(
        Application.user_id == current_user.id,
        Application.applied_at >= datetime.utcnow() - timedelta(days=180)
    ).all()
    
    # Group by month
    by_month = {}
    for app in applications:
        month = app.applied_at.strftime('%Y-%m')
        by_month[month] = by_month.get(month, 0) + 1
    
    # Generate last 6 months
    labels = []
    data = []
    
    for i in range(5, -1, -1):
        date = datetime.utcnow() - timedelta(days=i*30)
        month = date.strftime('%Y-%m')
        labels.append(date.strftime('%b %Y'))
        data.append(by_month.get(month, 0))
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@analytics_bp.route('/api/top-skills')
@login_required
def top_skills_data():
    """Get most viewed skills on profile"""
    analytics = get_or_create_analytics(current_user.id)
    
    skill_views = analytics.skill_views or {}
    
    # Sort by views
    sorted_skills = sorted(skill_views.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        'labels': [s[0] for s in sorted_skills],
        'data': [s[1] for s in sorted_skills]
    })


@analytics_bp.route('/api/search-appearances')
@login_required
def search_appearances_data():
    """Get search appearances by keyword"""
    analytics = get_or_create_analytics(current_user.id)
    
    search_keywords = analytics.search_keywords or {}
    
    # Sort by frequency
    sorted_keywords = sorted(search_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        'labels': [k[0] for k in sorted_keywords],
        'data': [k[1] for k in sorted_keywords]
    })


@analytics_bp.route('/track/profile-view', methods=['POST'])
def track_profile_view():
    """Track profile view (called when someone views a profile)"""
    data = request.json
    user_id = data.get('user_id', type=int)
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    analytics = get_or_create_analytics(user_id)
    analytics.profile_views += 1
    analytics.last_profile_view = datetime.utcnow()
    
    # Update daily views
    today = datetime.utcnow().strftime('%Y-%m-%d')
    views_by_day = analytics.views_by_day or {}
    views_by_day[today] = views_by_day.get(today, 0) + 1
    analytics.views_by_day = views_by_day
    
    db.session.commit()
    
    return jsonify({'success': True})


@analytics_bp.route('/track/resume-download', methods=['POST'])
@login_required
def track_resume_download():
    """Track resume download"""
    analytics = get_or_create_analytics(current_user.id)
    analytics.resume_downloads += 1
    
    # Update daily downloads
    today = datetime.utcnow().strftime('%Y-%m-%d')
    downloads_by_day = analytics.downloads_by_day or {}
    downloads_by_day[today] = downloads_by_day.get(today, 0) + 1
    analytics.downloads_by_day = downloads_by_day
    
    db.session.commit()
    
    return jsonify({'success': True})


@analytics_bp.route('/track/skill-view', methods=['POST'])
def track_skill_view():
    """Track when someone views a specific skill"""
    data = request.json
    user_id = data.get('user_id', type=int)
    skill = data.get('skill', '')
    
    if not user_id or not skill:
        return jsonify({'error': 'User ID and skill required'}), 400
    
    analytics = get_or_create_analytics(user_id)
    
    skill_views = analytics.skill_views or {}
    skill_views[skill] = skill_views.get(skill, 0) + 1
    analytics.skill_views = skill_views
    
    db.session.commit()
    
    return jsonify({'success': True})


@analytics_bp.route('/track/search-appearance', methods=['POST'])
def track_search_appearance():
    """Track when user appears in search results"""
    data = request.json
    user_id = data.get('user_id', type=int)
    keyword = data.get('keyword', '')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    analytics = get_or_create_analytics(user_id)
    analytics.search_appearances += 1
    
    if keyword:
        search_keywords = analytics.search_keywords or {}
        search_keywords[keyword] = search_keywords.get(keyword, 0) + 1
        analytics.search_keywords = search_keywords
    
    db.session.commit()
    
    return jsonify({'success': True})


@analytics_bp.route('/insights')
@login_required
def insights():
    """AI-powered insights and recommendations"""
    analytics = get_or_create_analytics(current_user.id)
    
    insights = []
    
    # Profile views insight
    if analytics.profile_views > 0:
        avg_views = db.session.query(func.avg(UserAnalytics.profile_views)).scalar() or 0
        if analytics.profile_views > avg_views * 1.5:
            insights.append({
                'type': 'positive',
                'title': 'High Profile Visibility',
                'message': f'Your profile has {analytics.profile_views} views, which is 50% above average. Great job!',
                'action': None
            })
        elif analytics.profile_views < avg_views * 0.5:
            insights.append({
                'type': 'warning',
                'title': 'Low Profile Visibility',
                'message': 'Your profile views are below average. Try updating your profile photo and skills.',
                'action': {'text': 'Update Profile', 'url': '/profile/edit'}
            })
    
    # Resume downloads insight
    if analytics.resume_downloads == 0 and analytics.profile_views > 10:
        insights.append({
            'type': 'warning',
            'title': 'Resume Not Downloaded',
            'message': 'Your profile is being viewed but your resume isn\'t being downloaded. Consider improving your resume.',
            'action': {'text': 'Improve Resume', 'url': '/resume-builder'}
        })
    
    # Application response rate
    total_apps = Application.query.filter_by(user_id=current_user.id).count()
    if total_apps > 5:
        responses = Application.query.filter(
            Application.user_id == current_user.id,
            Application.status.in_(['interview', 'offer'])
        ).count()
        rate = (responses / total_apps) * 100
        
        if rate < 10:
            insights.append({
                'type': 'warning',
                'title': 'Low Response Rate',
                'message': f'Only {rate:.0f}% of your applications get responses. Try tailoring your resume more.',
                'action': {'text': 'Use Auto-Apply', 'url': '/auto-apply'}
            })
    
    # Skills insight
    if analytics.skill_views:
        top_skill = max(analytics.skill_views.items(), key=lambda x: x[1])
        insights.append({
            'type': 'info',
            'title': 'Most Viewed Skill',
            'message': f'"{top_skill[0]}" is your most viewed skill with {top_skill[1]} views. Highlight it more!',
            'action': None
        })
    
    # Engagement insight
    last_view = analytics.last_profile_view
    if last_view and last_view < datetime.utcnow() - timedelta(days=7):
        insights.append({
            'type': 'warning',
            'title': 'Profile Inactive',
            'message': 'Your profile hasn\'t been viewed in 7+ days. Share it on social media!',
            'action': {'text': 'Share Profile', 'url': '/profile/share'}
        })
    
    return render_template('analytics/insights.html',
                         insights=insights,
                         analytics=analytics)


@analytics_bp.route('/export')
@login_required
def export_data():
    """Export analytics data as JSON"""
    analytics = get_or_create_analytics(current_user.id)
    
    data = {
        'profile_views': analytics.profile_views,
        'resume_downloads': analytics.resume_downloads,
        'search_appearances': analytics.search_appearances,
        'connection_clicks': analytics.connection_clicks,
        'last_profile_view': analytics.last_profile_view.isoformat() if analytics.last_profile_view else None,
        'views_by_day': analytics.views_by_day,
        'downloads_by_day': analytics.downloads_by_day,
        'skill_views': analytics.skill_views,
        'search_keywords': analytics.search_keywords
    }
    
    return jsonify(data)
