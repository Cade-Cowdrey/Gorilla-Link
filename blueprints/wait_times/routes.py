from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models_student_features import CampusService, ServiceWaitReport
from sqlalchemy import func
from datetime import datetime, timedelta

wait_times_bp = Blueprint('wait_times', __name__, url_prefix='/wait-times')

@wait_times_bp.route('/')
def index():
    """Campus service wait times homepage"""
    category = request.args.get('category', '')
    
    query = CampusService.query
    
    if category:
        query = query.filter_by(category=category)
    
    services = query.order_by(CampusService.name).all()
    
    # Get categories
    categories = db.session.query(
        CampusService.category
    ).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('wait_times/index.html',
                         services=services,
                         categories=categories,
                         category=category)


@wait_times_bp.route('/service/<int:service_id>')
def view_service(service_id):
    """View service details and recent reports"""
    service = CampusService.query.get_or_404(service_id)
    
    # Get recent reports (last 24 hours)
    recent_time = datetime.utcnow() - timedelta(hours=24)
    recent_reports = ServiceWaitReport.query.filter(
        ServiceWaitReport.service_id == service_id,
        ServiceWaitReport.reported_at >= recent_time
    ).order_by(ServiceWaitReport.reported_at.desc()).limit(20).all()
    
    # Calculate stats for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_reports = ServiceWaitReport.query.filter(
        ServiceWaitReport.service_id == service_id,
        ServiceWaitReport.reported_at >= today_start
    ).all()
    
    today_stats = None
    if today_reports:
        avg_wait = sum(r.wait_time for r in today_reports if r.wait_time) / len([r for r in today_reports if r.wait_time]) if any(r.wait_time for r in today_reports) else 0
        today_stats = {
            'avg_wait': round(avg_wait, 1),
            'report_count': len(today_reports),
            'capacity_distribution': {}
        }
        
        for report in today_reports:
            if report.capacity_level:
                today_stats['capacity_distribution'][report.capacity_level] = \
                    today_stats['capacity_distribution'].get(report.capacity_level, 0) + 1
    
    return render_template('wait_times/service.html',
                         service=service,
                         recent_reports=recent_reports,
                         today_stats=today_stats)


@wait_times_bp.route('/report/<int:service_id>', methods=['POST'])
@login_required
def report_wait_time(service_id):
    """Report wait time for a service"""
    service = CampusService.query.get_or_404(service_id)
    
    wait_time = int(request.form.get('wait_time', 0)) if request.form.get('wait_time') else None
    capacity_level = request.form.get('capacity_level')
    
    report = ServiceWaitReport(
        service_id=service_id,
        user_id=current_user.id,
        wait_time=wait_time,
        capacity_level=capacity_level
    )
    
    db.session.add(report)
    
    # Update service current status
    service.current_wait_time = wait_time if wait_time else service.current_wait_time
    service.current_capacity = capacity_level if capacity_level else service.current_capacity
    service.last_updated = datetime.utcnow()
    
    # Recalculate average wait time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_reports = ServiceWaitReport.query.filter(
        ServiceWaitReport.service_id == service_id,
        ServiceWaitReport.reported_at >= thirty_days_ago,
        ServiceWaitReport.wait_time != None
    ).all()
    
    if recent_reports:
        service.avg_wait_time = round(
            sum(r.wait_time for r in recent_reports) / len(recent_reports)
        )
    
    db.session.commit()
    
    flash('Thank you for your report!', 'success')
    return redirect(url_for('wait_times.view_service', service_id=service_id))


@wait_times_bp.route('/quick-report', methods=['POST'])
@login_required
def quick_report():
    """Quick AJAX report for wait time"""
    service_id = request.json.get('service_id')
    capacity_level = request.json.get('capacity_level')
    
    service = CampusService.query.get_or_404(service_id)
    
    report = ServiceWaitReport(
        service_id=service_id,
        user_id=current_user.id,
        capacity_level=capacity_level
    )
    
    db.session.add(report)
    
    service.current_capacity = capacity_level
    service.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Report submitted',
        'current_capacity': service.current_capacity,
        'last_updated': service.last_updated.strftime('%I:%M %p')
    })


@wait_times_bp.route('/api/current-status')
def api_current_status():
    """API endpoint for current wait times"""
    services = CampusService.query.all()
    
    result = []
    for service in services:
        result.append({
            'id': service.id,
            'name': service.name,
            'category': service.category,
            'current_wait_time': service.current_wait_time,
            'current_capacity': service.current_capacity,
            'last_updated': service.last_updated.isoformat() if service.last_updated else None
        })
    
    return jsonify(result)
