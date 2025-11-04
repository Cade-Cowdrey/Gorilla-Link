"""
Routes for institutional administrative functions
"""

from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import (
    UniversityVerification, ComplianceLog, InstitutionalAnnouncement,
    AdministratorRole, OutcomeReport, EmployerPartnership, SystemHealthMetric
)
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func

from . import bp


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if user has any admin role
        admin_role = AdministratorRole.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not admin_role:
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('core_bp.home'))
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Main institutional admin dashboard"""
    
    # Get verification queue count
    pending_verifications = UniversityVerification.query.filter_by(
        verification_status='pending'
    ).count()
    
    # Get active partnerships
    active_partnerships = EmployerPartnership.query.filter_by(
        is_active=True
    ).count()
    
    # Get recent outcome reports
    recent_outcomes = OutcomeReport.query.order_by(
        OutcomeReport.created_at.desc()
    ).limit(10).all()
    
    # Get system health status
    system_health = SystemHealthMetric.query.order_by(
        SystemHealthMetric.timestamp.desc()
    ).limit(5).all()
    
    return render_template('institutional_admin/dashboard.html',
                         pending_verifications=pending_verifications,
                         active_partnerships=active_partnerships,
                         recent_outcomes=recent_outcomes,
                         system_health=system_health)


@bp.route('/verifications')
@login_required
@admin_required
def verification_queue():
    """Student/alumni verification queue"""
    
    pending = UniversityVerification.query.filter_by(
        verification_status='pending'
    ).order_by(UniversityVerification.created_at).all()
    
    return render_template('institutional_admin/verifications.html',
                         verifications=pending)


@bp.route('/verifications/<int:verification_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_verification(verification_id):
    """Approve a verification request"""
    
    verification = UniversityVerification.query.get_or_404(verification_id)
    
    verification.is_verified = True
    verification.verification_status = 'approved'
    verification.verified_by = current_user.id
    verification.verified_at = datetime.utcnow()
    
    # Log compliance action
    log = ComplianceLog(
        user_id=verification.user_id,
        admin_id=current_user.id,
        action_type='verification_approved',
        resource_type='university_verification',
        resource_id=verification_id,
        justification='Manual verification approval',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    
    db.session.commit()
    
    flash(f'Verification approved for user {verification.user_id}', 'success')
    return redirect(url_for('institutional_admin.verification_queue'))


@bp.route('/verifications/<int:verification_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_verification(verification_id):
    """Reject a verification request"""
    
    verification = UniversityVerification.query.get_or_404(verification_id)
    rejection_reason = request.form.get('reason', 'No reason provided')
    
    verification.is_verified = False
    verification.verification_status = 'rejected'
    verification.rejection_reason = rejection_reason
    verification.verified_by = current_user.id
    verification.verified_at = datetime.utcnow()
    
    # Log compliance action
    log = ComplianceLog(
        user_id=verification.user_id,
        admin_id=current_user.id,
        action_type='verification_rejected',
        resource_type='university_verification',
        resource_id=verification_id,
        justification=f'Rejected: {rejection_reason}',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    
    db.session.commit()
    
    flash(f'Verification rejected for user {verification.user_id}', 'warning')
    return redirect(url_for('institutional_admin.verification_queue'))


@bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """Manage institutional announcements"""
    
    announcements = InstitutionalAnnouncement.query.filter_by(
        is_active=True
    ).order_by(InstitutionalAnnouncement.created_at.desc()).all()
    
    return render_template('institutional_admin/announcements.html',
                         announcements=announcements)


@bp.route('/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_announcement():
    """Create a new institutional announcement"""
    
    if request.method == 'POST':
        announcement = InstitutionalAnnouncement(
            title=request.form.get('title'),
            content=request.form.get('content'),
            announcement_type=request.form.get('announcement_type', 'general'),
            priority=request.form.get('priority', 'normal'),
            target_audience=request.form.getlist('target_audience'),
            posted_by=current_user.id,
            show_as_banner=request.form.get('show_as_banner') == 'on',
            banner_color=request.form.get('banner_color', 'blue')
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('institutional_admin.announcements'))
    
    return render_template('institutional_admin/create_announcement.html')


@bp.route('/reports/outcomes')
@login_required
@admin_required
def outcome_reports():
    """Graduate outcome reporting dashboard"""
    
    current_year = datetime.now().year
    
    # Get outcome statistics
    total_graduates = OutcomeReport.query.filter_by(
        graduation_year=current_year
    ).count()
    
    employed = OutcomeReport.query.filter_by(
        graduation_year=current_year,
        outcome_type='employed'
    ).count()
    
    continuing_ed = OutcomeReport.query.filter_by(
        graduation_year=current_year,
        outcome_type='continuing_education'
    ).count()
    
    # Calculate employment rate
    employment_rate = (employed / total_graduates * 100) if total_graduates > 0 else 0
    
    # Get salary distribution
    salary_data = db.session.query(
        OutcomeReport.salary_range,
        func.count(OutcomeReport.id)
    ).filter_by(
        graduation_year=current_year,
        outcome_type='employed'
    ).group_by(OutcomeReport.salary_range).all()
    
    return render_template('institutional_admin/outcome_reports.html',
                         total_graduates=total_graduates,
                         employed=employed,
                         continuing_ed=continuing_ed,
                         employment_rate=employment_rate,
                         salary_data=salary_data,
                         current_year=current_year)


@bp.route('/compliance/audit-log')
@login_required
@admin_required
def audit_log():
    """View compliance audit log"""
    
    page = request.args.get('page', 1, type=int)
    logs = ComplianceLog.query.order_by(
        ComplianceLog.timestamp.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('institutional_admin/audit_log.html',
                         logs=logs)


@bp.route('/partnerships')
@login_required
@admin_required
def partnerships():
    """Manage employer partnerships"""
    
    partnerships = EmployerPartnership.query.filter_by(
        is_active=True
    ).order_by(EmployerPartnership.partnership_level).all()
    
    return render_template('institutional_admin/partnerships.html',
                         partnerships=partnerships)


@bp.route('/partnerships/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_partnership():
    """Create a new employer partnership"""
    
    if request.method == 'POST':
        partnership = EmployerPartnership(
            company_name=request.form.get('company_name'),
            partnership_type=request.form.get('partnership_type'),
            contact_name=request.form.get('contact_name'),
            contact_email=request.form.get('contact_email'),
            contact_phone=request.form.get('contact_phone'),
            partnership_level=request.form.get('partnership_level', 'bronze'),
            website=request.form.get('website'),
            industries=request.form.getlist('industries')
        )
        
        db.session.add(partnership)
        db.session.commit()
        
        flash(f'Partnership with {partnership.company_name} created successfully!', 'success')
        return redirect(url_for('institutional_admin.partnerships'))
    
    return render_template('institutional_admin/create_partnership.html')


@bp.route('/system-health')
@login_required
@admin_required
def system_health():
    """System health monitoring dashboard"""
    
    # Get last 24 hours of metrics
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    metrics = SystemHealthMetric.query.filter(
        SystemHealthMetric.timestamp >= yesterday
    ).order_by(SystemHealthMetric.timestamp.desc()).all()
    
    # Group by metric type
    grouped_metrics = {}
    for metric in metrics:
        if metric.metric_type not in grouped_metrics:
            grouped_metrics[metric.metric_type] = []
        grouped_metrics[metric.metric_type].append(metric)
    
    return render_template('institutional_admin/system_health.html',
                         grouped_metrics=grouped_metrics)


@bp.route('/api/metrics', methods=['POST'])
def record_metric():
    """API endpoint to record system health metrics (called by monitoring service)"""
    
    data = request.get_json()
    
    metric = SystemHealthMetric(
        metric_type=data.get('metric_type'),
        metric_value=data.get('metric_value'),
        threshold_warning=data.get('threshold_warning'),
        threshold_critical=data.get('threshold_critical'),
        status=data.get('status', 'healthy'),
        details=data.get('details')
    )
    
    db.session.add(metric)
    db.session.commit()
    
    return jsonify({'success': True, 'id': metric.id}), 201
