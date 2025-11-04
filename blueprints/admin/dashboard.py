"""
PSU Connect - Admin Dashboard
User management, content moderation, analytics, and system health
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, JobPosting, Application
from models_growth_features import (
    SuccessStory, ForumTopic, ForumPost, MentorshipMatch,
    DirectMessage, UserAnalytics, Badge, UserBadge
)
from sqlalchemy import func, desc, extract
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin_growth', __name__, url_prefix='/admin/growth')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Main admin dashboard"""
    # User stats
    total_users = User.query.count()
    new_users_week = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    active_users = User.query.filter(
        User.last_login >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Content stats
    total_jobs = JobPosting.query.count()
    total_applications = Application.query.count()
    total_stories = SuccessStory.query.count()
    total_forum_posts = ForumPost.query.count()
    
    # Engagement stats
    avg_profile_views = db.session.query(func.avg(UserAnalytics.profile_views)).scalar() or 0
    total_messages = DirectMessage.query.count()
    active_mentorships = MentorshipMatch.query.filter_by(status='active').count()
    
    # Growth data (last 30 days)
    growth_data = []
    for i in range(29, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        users_on_date = User.query.filter(
            func.date(User.created_at) == date.date()
        ).count()
        
        growth_data.append({
            'date': date.strftime('%b %d'),
            'users': users_on_date
        })
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         new_users_week=new_users_week,
                         active_users=active_users,
                         total_jobs=total_jobs,
                         total_applications=total_applications,
                         total_stories=total_stories,
                         total_forum_posts=total_forum_posts,
                         avg_profile_views=round(avg_profile_views, 1),
                         total_messages=total_messages,
                         active_mentorships=active_mentorships,
                         growth_data=growth_data)


@admin_bp.route('/users')
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=users,
                         search=search)


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    
    # Get user analytics
    analytics = UserAnalytics.query.filter_by(user_id=user_id).first()
    
    # Get user activity
    applications = Application.query.filter_by(user_id=user_id).count()
    forum_posts = ForumPost.query.filter_by(created_by=user_id).count()
    messages_sent = DirectMessage.query.filter_by(sender_id=user_id).count()
    
    # Get badges
    badges = UserBadge.query.filter_by(user_id=user_id).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         analytics=analytics,
                         applications=applications,
                         forum_posts=forum_posts,
                         messages_sent=messages_sent,
                         badges=badges)


@admin_bp.route('/users/<int:user_id>/disable', methods=['POST'])
@admin_required
def disable_user(user_id):
    """Disable user account"""
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})


@admin_bp.route('/users/<int:user_id>/enable', methods=['POST'])
@admin_required
def enable_user(user_id):
    """Enable user account"""
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    return jsonify({'success': True})


@admin_bp.route('/content/moderation')
@admin_required
def content_moderation():
    """Content moderation queue"""
    # Get flagged/reported content
    recent_stories = SuccessStory.query.order_by(
        desc(SuccessStory.created_at)
    ).limit(20).all()
    
    recent_posts = ForumPost.query.order_by(
        desc(ForumPost.created_at)
    ).limit(20).all()
    
    return render_template('admin/moderation.html',
                         stories=recent_stories,
                         posts=recent_posts)


@admin_bp.route('/content/story/<int:story_id>/delete', methods=['POST'])
@admin_required
def delete_story(story_id):
    """Delete success story"""
    story = SuccessStory.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    
    return jsonify({'success': True})


@admin_bp.route('/content/post/<int:post_id>/delete', methods=['POST'])
@admin_required
def delete_post(post_id):
    """Delete forum post"""
    post = ForumPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'success': True})


@admin_bp.route('/analytics')
@admin_required
def analytics():
    """System analytics"""
    # User growth by month
    monthly_growth = db.session.query(
        extract('year', User.created_at).label('year'),
        extract('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    # Application success rate
    total_apps = Application.query.count()
    successful_apps = Application.query.filter(
        Application.status.in_(['offer', 'accepted'])
    ).count()
    success_rate = (successful_apps / total_apps * 100) if total_apps > 0 else 0
    
    # Most active users
    top_users = db.session.query(
        User,
        func.count(Application.id).label('app_count')
    ).join(Application).group_by(User.id).order_by(
        desc('app_count')
    ).limit(10).all()
    
    # Most popular badges
    top_badges = db.session.query(
        Badge,
        func.count(UserBadge.id).label('earned_count')
    ).join(UserBadge).group_by(Badge.id).order_by(
        desc('earned_count')
    ).limit(10).all()
    
    return render_template('admin/analytics.html',
                         monthly_growth=monthly_growth,
                         success_rate=round(success_rate, 1),
                         top_users=top_users,
                         top_badges=top_badges)


@admin_bp.route('/badges')
@admin_required
def badges():
    """Badge management"""
    all_badges = Badge.query.all()
    
    # Get earning stats for each badge
    for badge in all_badges:
        badge.earned_count = UserBadge.query.filter_by(badge_id=badge.id).count()
    
    return render_template('admin/badges.html', badges=all_badges)


@admin_bp.route('/badges/create', methods=['POST'])
@admin_required
def create_badge():
    """Create new badge"""
    data = request.json
    
    badge = Badge(
        name=data.get('name'),
        description=data.get('description'),
        icon=data.get('icon'),
        points=data.get('points', type=int),
        criteria=data.get('criteria', {})
    )
    
    db.session.add(badge)
    db.session.commit()
    
    return jsonify({'success': True, 'badge_id': badge.id})


@admin_bp.route('/badges/<int:badge_id>/award', methods=['POST'])
@admin_required
def award_badge(badge_id):
    """Manually award badge to user"""
    data = request.json
    user_id = data.get('user_id', type=int)
    
    badge = Badge.query.get_or_404(badge_id)
    user = User.query.get_or_404(user_id)
    
    # Check if already has badge
    existing = UserBadge.query.filter_by(
        user_id=user_id,
        badge_id=badge_id
    ).first()
    
    if existing:
        return jsonify({'error': 'User already has this badge'}), 400
    
    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge_id
    )
    db.session.add(user_badge)
    
    # Award points
    from blueprints.gamification import award_points
    award_points(user_id, badge.points, f'badge_{badge.name}')
    
    db.session.commit()
    
    return jsonify({'success': True})


@admin_bp.route('/system/health')
@admin_required
def system_health():
    """System health monitoring"""
    # Database connection
    try:
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'error'
    
    # Count records in key tables
    table_counts = {
        'users': User.query.count(),
        'jobs': JobPosting.query.count(),
        'applications': Application.query.count(),
        'success_stories': SuccessStory.query.count(),
        'forum_posts': ForumPost.query.count(),
        'messages': DirectMessage.query.count()
    }
    
    # Recent errors (would need error logging table)
    recent_errors = []
    
    return render_template('admin/system_health.html',
                         db_status=db_status,
                         table_counts=table_counts,
                         recent_errors=recent_errors)


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard stats"""
    stats = {
        'total_users': User.query.count(),
        'active_users_month': User.query.filter(
            User.last_login >= datetime.utcnow() - timedelta(days=30)
        ).count(),
        'total_applications': Application.query.count(),
        'successful_applications': Application.query.filter(
            Application.status.in_(['offer', 'accepted'])
        ).count()
    }
    
    return jsonify(stats)


@admin_bp.route('/export/users')
@admin_required
def export_users():
    """Export user data as CSV"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Major', 'Grad Year', 'Created', 'Last Login'])
    
    # Data
    users = User.query.all()
    for user in users:
        writer.writerow([
            user.id,
            user.full_name,
            user.email,
            user.major,
            user.graduation_year,
            user.created_at.strftime('%Y-%m-%d'),
            user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
        ])
    
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=users_export.csv'
    }
