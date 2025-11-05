"""
Admin Dashboard Routes - Real-time analytics and metrics
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models import db, User, Job, Scholarship
from models_growth_features import (
    DashboardMetric, PlatformEngagement, CareerServicesImpact,
    AdminAlert, OutcomeReport, CareerServiceAppointment,
    AppointmentFeedback
)

bp = Blueprint("admin_dashboard", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            return jsonify(error="Unauthorized"), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.get("/")
@login_required
@admin_required
def dashboard_home():
    """Main admin dashboard with real-time metrics"""
    
    # Get key metrics
    total_users = User.query.count()
    total_jobs = Job.query.filter_by(is_active=True).count()
    total_scholarships = Scholarship.query.filter_by(is_active=True).count()
    
    # Today's engagement
    today = datetime.utcnow().date()
    today_engagement = PlatformEngagement.query.filter_by(date=today).first()
    
    # Recent alerts
    unread_alerts = AdminAlert.query.filter_by(is_read=False).order_by(desc(AdminAlert.created_at)).limit(5).all()
    
    # Latest impact metrics
    latest_impact = CareerServicesImpact.query.order_by(desc(CareerServicesImpact.period_end)).first()
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_jobs=total_jobs,
        total_scholarships=total_scholarships,
        today_engagement=today_engagement,
        alerts=unread_alerts,
        impact=latest_impact
    )


@bp.get("/api/metrics")
@login_required
@admin_required
def get_metrics():
    """API endpoint for real-time metrics"""
    
    # Calculate real-time metrics
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    # User metrics
    total_users = User.query.count()
    active_this_week = User.query.filter(User.last_login >= week_ago).count()
    
    # Engagement metrics
    today_engagement = PlatformEngagement.query.filter_by(date=today).first()
    
    # Career services metrics
    appointments_this_month = CareerServiceAppointment.query.filter(
        func.extract('month', CareerServiceAppointment.scheduled_at) == datetime.utcnow().month,
        func.extract('year', CareerServiceAppointment.scheduled_at) == datetime.utcnow().year
    ).count()
    
    # Outcome metrics
    employment_rate = db.session.query(
        func.count(OutcomeReport.id)
    ).filter(OutcomeReport.outcome_type == 'employed').scalar() or 0
    
    total_outcomes = OutcomeReport.query.count() or 1
    employment_percentage = (employment_rate / total_outcomes) * 100
    
    return jsonify({
        "users": {
            "total": total_users,
            "active_this_week": active_this_week,
            "percentage_active": (active_this_week / total_users * 100) if total_users > 0 else 0
        },
        "engagement": {
            "daily_active_users": today_engagement.daily_active_users if today_engagement else 0,
            "new_registrations": today_engagement.new_registrations if today_engagement else 0,
            "appointments_booked": today_engagement.appointments_booked if today_engagement else 0
        },
        "career_services": {
            "appointments_this_month": appointments_this_month,
            "employment_rate": round(employment_percentage, 1)
        },
        "timestamp": datetime.utcnow().isoformat()
    })


@bp.get("/analytics")
@login_required
@admin_required
def analytics_page():
    """Detailed analytics page with charts and graphs"""
    
    # Get last 30 days of engagement
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    engagement_data = PlatformEngagement.query.filter(
        PlatformEngagement.date >= thirty_days_ago
    ).order_by(PlatformEngagement.date).all()
    
    # Get all dashboard metrics
    metrics = DashboardMetric.query.all()
    
    # Career services impact over time
    impact_reports = CareerServicesImpact.query.order_by(
        desc(CareerServicesImpact.period_end)
    ).limit(12).all()
    
    return render_template(
        "admin/analytics.html",
        engagement_data=engagement_data,
        metrics=metrics,
        impact_reports=impact_reports
    )


@bp.get("/career-services")
@login_required
@admin_required
def career_services_dashboard():
    """Dashboard specifically for career services metrics"""
    
    # Current month stats
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    appointments_this_month = CareerServiceAppointment.query.filter(
        func.extract('month', CareerServiceAppointment.scheduled_at) == current_month,
        func.extract('year', CareerServiceAppointment.scheduled_at) == current_year
    ).all()
    
    # Appointment types breakdown
    appointment_types = db.session.query(
        CareerServiceAppointment.appointment_type,
        func.count(CareerServiceAppointment.id)
    ).group_by(CareerServiceAppointment.appointment_type).all()
    
    # Average ratings
    avg_rating = db.session.query(
        func.avg(AppointmentFeedback.rating)
    ).scalar() or 0
    
    # Outcomes
    students_with_outcomes = db.session.query(
        func.count(OutcomeReport.id)
    ).join(
        CareerServiceAppointment,
        OutcomeReport.user_id == CareerServiceAppointment.student_id
    ).scalar() or 0
    
    return render_template(
        "admin/career_services.html",
        appointments=appointments_this_month,
        appointment_types=appointment_types,
        avg_rating=round(avg_rating, 2),
        students_with_outcomes=students_with_outcomes
    )


@bp.get("/outcomes")
@login_required
@admin_required
def outcomes_dashboard():
    """Graduate outcomes tracking for accreditation"""
    
    # Current academic year
    current_year = datetime.utcnow().year
    
    # Get all outcomes for current year
    outcomes = OutcomeReport.query.filter(
        OutcomeReport.graduation_year == current_year
    ).all()
    
    # Breakdown by outcome type
    outcome_breakdown = db.session.query(
        OutcomeReport.outcome_type,
        func.count(OutcomeReport.id)
    ).filter(
        OutcomeReport.graduation_year == current_year
    ).group_by(OutcomeReport.outcome_type).all()
    
    # Salary ranges
    salary_data = db.session.query(
        OutcomeReport.salary_range,
        func.count(OutcomeReport.id)
    ).filter(
        OutcomeReport.graduation_year == current_year,
        OutcomeReport.outcome_type == 'employed'
    ).group_by(OutcomeReport.salary_range).all()
    
    # Related to major percentage
    related_to_major = db.session.query(
        func.count(OutcomeReport.id)
    ).filter(
        OutcomeReport.graduation_year == current_year,
        OutcomeReport.related_to_major == True
    ).scalar() or 0
    
    total_employed = db.session.query(
        func.count(OutcomeReport.id)
    ).filter(
        OutcomeReport.graduation_year == current_year,
        OutcomeReport.outcome_type == 'employed'
    ).scalar() or 1
    
    related_percentage = (related_to_major / total_employed * 100) if total_employed > 0 else 0
    
    return render_template(
        "admin/outcomes.html",
        outcomes=outcomes,
        outcome_breakdown=outcome_breakdown,
        salary_data=salary_data,
        related_percentage=round(related_percentage, 1)
    )


@bp.get("/alerts")
@login_required
@admin_required
def alerts_page():
    """View and manage system alerts"""
    
    # Get all unresolved alerts
    alerts = AdminAlert.query.filter_by(is_resolved=False).order_by(
        desc(AdminAlert.severity),
        desc(AdminAlert.created_at)
    ).all()
    
    return render_template("admin/alerts.html", alerts=alerts)


@bp.post("/alerts/<int:alert_id>/mark-read")
@login_required
@admin_required
def mark_alert_read(alert_id):
    """Mark an alert as read"""
    alert = AdminAlert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    
    return jsonify(success=True)


@bp.post("/alerts/<int:alert_id>/resolve")
@login_required
@admin_required
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    alert = AdminAlert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success=True)


@bp.get("/reports")
@login_required
@admin_required
def reports_page():
    """View and download pre-generated reports"""
    from models_growth_features import ExportableReport
    
    reports = ExportableReport.query.order_by(
        desc(ExportableReport.created_at)
    ).all()
    
    return render_template("admin/reports.html", reports=reports)


@bp.get("/api/export/outcomes")
@login_required
@admin_required
def export_outcomes():
    """Export outcomes data for accreditation (CSV format)"""
    import csv
    from io import StringIO
    from flask import Response
    
    # Get all outcomes
    outcomes = OutcomeReport.query.all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Student ID', 'Graduation Year', 'Outcome Type', 'Employer',
        'Job Title', 'Salary Range', 'Related to Major', 'Satisfaction Score'
    ])
    
    # Data
    for outcome in outcomes:
        writer.writerow([
            outcome.user_id,
            outcome.graduation_year,
            outcome.outcome_type,
            outcome.employer_name or '',
            outcome.job_title or '',
            outcome.salary_range or '',
            'Yes' if outcome.related_to_major else 'No',
            outcome.satisfaction_score or ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=outcomes_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )


@bp.get("/api/widget/stats")
def public_stats_widget():
    """Public API endpoint for embeddable stats widget"""
    
    # Calculate key public-facing metrics
    total_users = User.query.count()
    total_scholarships = Scholarship.query.filter_by(is_active=True).count()
    total_jobs = Job.query.filter_by(is_active=True).count()
    
    # Get employment rate
    employment_rate = db.session.query(
        func.count(OutcomeReport.id)
    ).filter(OutcomeReport.outcome_type == 'employed').scalar() or 0
    
    total_outcomes = OutcomeReport.query.count() or 1
    employment_percentage = (employment_rate / total_outcomes) * 100
    
    return jsonify({
        "platform": "Gorilla-Link",
        "university": "Pittsburg State University",
        "stats": {
            "active_users": total_users,
            "available_scholarships": total_scholarships,
            "job_postings": total_jobs,
            "employment_rate": f"{round(employment_percentage, 1)}%"
        },
        "updated_at": datetime.utcnow().isoformat()
    })
