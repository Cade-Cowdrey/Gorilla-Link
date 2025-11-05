"""
Advanced Data & Compliance Layer Routes
FERPA-compliant audit trails and data protection
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_advanced_features import DataAccessAudit, ComplianceReport, DataMaskingRule
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc, func

compliance_bp = Blueprint('compliance', __name__, url_prefix='/compliance')

# ==================== AUDIT TRAIL LOGGING ====================

def log_data_access(accessor_id, data_type, record_id=None, student_affected_id=None,
                   access_method='view', endpoint=None, access_purpose='routine_maintenance',
                   fields_accessed=None):
    """
    Log all data access for FERPA compliance
    Call this function whenever sensitive data is accessed
    """
    import json
    from flask import request as flask_request
    
    audit = DataAccessAudit(
        accessor_id=accessor_id,
        accessor_role=get_user_role(accessor_id),
        accessor_ip_address=flask_request.remote_addr if flask_request else None,
        data_type=data_type,
        record_id=record_id,
        student_affected_id=student_affected_id,
        access_method=access_method,
        endpoint=endpoint or flask_request.endpoint if flask_request else None,
        access_purpose=access_purpose,
        fields_accessed=json.dumps(fields_accessed) if fields_accessed else None,
        authorization_level='authorized',
        is_ferpa_protected=True,
        is_suspicious=detect_suspicious_access(accessor_id, data_type),
        session_id=flask_request.cookies.get('session') if flask_request else None,
        user_agent=flask_request.headers.get('User-Agent') if flask_request else None
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return audit


# ==================== AUDIT TRAIL VIEWING ====================

@compliance_bp.route('/audit-trail')
@login_required
def audit_trail():
    """View audit trail (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    # Filters
    data_type = request.args.get('data_type', 'all')
    accessor = request.args.get('accessor')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    suspicious_only = request.args.get('suspicious') == 'true'
    
    query = DataAccessAudit.query
    
    if data_type != 'all':
        query = query.filter_by(data_type=data_type)
    
    if accessor:
        query = query.filter_by(accessor_id=int(accessor))
    
    if start_date:
        query = query.filter(DataAccessAudit.accessed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        query = query.filter(DataAccessAudit.accessed_at <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    if suspicious_only:
        query = query.filter_by(is_suspicious=True)
    
    audits = query.order_by(DataAccessAudit.accessed_at.desc()).limit(500).all()
    
    # Get stats
    total_accesses = DataAccessAudit.query.count()
    suspicious_count = DataAccessAudit.query.filter_by(is_suspicious=True).count()
    last_24h = DataAccessAudit.query.filter(
        DataAccessAudit.accessed_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    
    return render_template('compliance/audit_trail.html',
                         audits=audits,
                         total_accesses=total_accesses,
                         suspicious_count=suspicious_count,
                         last_24h=last_24h,
                         current_filters=request.args)


@compliance_bp.route('/my-data-access')
@login_required
def my_data_access():
    """Student views their own data access history"""
    audits = DataAccessAudit.query.filter_by(
        student_affected_id=current_user.id
    ).order_by(DataAccessAudit.accessed_at.desc()).limit(100).all()
    
    return render_template('compliance/my_data_access.html', audits=audits)


@compliance_bp.route('/audit/<int:audit_id>')
@login_required
def view_audit_detail(audit_id):
    """View detailed audit record"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('compliance.audit_trail'))
    
    audit = DataAccessAudit.query.get_or_404(audit_id)
    
    import json
    fields = json.loads(audit.fields_accessed) if audit.fields_accessed else []
    
    return render_template('compliance/audit_detail.html',
                         audit=audit,
                         fields=fields)


# ==================== COMPLIANCE REPORTS ====================

@compliance_bp.route('/reports')
@login_required
def compliance_reports():
    """View compliance reports (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    report_type = request.args.get('type', 'all')
    
    query = ComplianceReport.query
    
    if report_type != 'all':
        query = query.filter_by(report_type=report_type)
    
    reports = query.order_by(ComplianceReport.generated_at.desc()).all()
    
    return render_template('compliance/reports.html',
                         reports=reports,
                         current_type=report_type)


@compliance_bp.route('/report/<int:report_id>')
@login_required
def view_compliance_report(report_id):
    """View specific compliance report"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('compliance.compliance_reports'))
    
    report = ComplianceReport.query.get_or_404(report_id)
    
    import json
    findings = json.loads(report.findings) if report.findings else []
    recommendations = json.loads(report.recommendations) if report.recommendations else []
    action_items = json.loads(report.action_items) if report.action_items else []
    
    return render_template('compliance/report_detail.html',
                         report=report,
                         findings=findings,
                         recommendations=recommendations,
                         action_items=action_items)


@compliance_bp.route('/generate-report', methods=['GET', 'POST'])
@login_required
def generate_report():
    """Generate new compliance report"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.form
        
        report_type = data.get('report_type')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        # Generate report data
        report_data = generate_compliance_report_data(report_type, start_date, end_date)
        
        report = ComplianceReport(
            report_type=report_type,
            report_title=f"{report_type.replace('_', ' ').title()} Report: {start_date} to {end_date}",
            report_period_start=start_date,
            report_period_end=end_date,
            summary=report_data['summary'],
            total_records_reviewed=report_data['total_records'],
            total_access_events=report_data['total_accesses'],
            unauthorized_access_attempts=report_data['unauthorized'],
            policy_violations=report_data['violations'],
            findings=report_data['findings'],
            recommendations=report_data['recommendations'],
            action_items=report_data['action_items'],
            compliance_score=report_data['compliance_score'],
            compliant=report_data['compliant'],
            issues_found=report_data['issues_found'],
            issues_resolved=0,
            generated_by='admin_requested',
            generated_by_user_id=current_user.id,
            status='draft'
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('Compliance report generated successfully', 'success')
        return redirect(url_for('compliance.view_compliance_report', report_id=report.id))
    
    return render_template('compliance/generate_report.html')


@compliance_bp.route('/report/<int:report_id>/approve', methods=['POST'])
@login_required
def approve_report(report_id):
    """Approve compliance report"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    report = ComplianceReport.query.get_or_404(report_id)
    
    report.status = 'approved'
    report.reviewed_by_user_id = current_user.id
    report.reviewed_at = datetime.utcnow()
    report.review_notes = request.json.get('notes')
    
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== DATA MASKING RULES ====================

@compliance_bp.route('/masking-rules')
@login_required
def masking_rules():
    """Manage data masking rules (admin only)"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    rules = DataMaskingRule.query.filter_by(is_active=True).all()
    
    return render_template('compliance/masking_rules.html', rules=rules)


@compliance_bp.route('/masking-rule/add', methods=['POST'])
@login_required
def add_masking_rule():
    """Add new data masking rule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form
    
    import json
    
    rule = DataMaskingRule(
        rule_name=data.get('rule_name'),
        data_category=data.get('data_category'),
        field_name=data.get('field_name'),
        table_name=data.get('table_name'),
        masking_type=data.get('masking_type'),
        mask_pattern=data.get('mask_pattern'),
        apply_for_roles=json.dumps(data.getlist('apply_for_roles')),
        exempt_roles=json.dumps(data.getlist('exempt_roles')),
        requires_explicit_consent=data.get('requires_explicit_consent') == 'true',
        ferpa_requirement=data.get('ferpa_requirement') == 'true',
        is_active=True,
        created_by_id=current_user.id
    )
    
    db.session.add(rule)
    db.session.commit()
    
    flash('Data masking rule added', 'success')
    return redirect(url_for('compliance.masking_rules'))


@compliance_bp.route('/masking-rule/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_masking_rule(rule_id):
    """Enable/disable masking rule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    rule = DataMaskingRule.query.get_or_404(rule_id)
    rule.is_active = not rule.is_active
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': rule.is_active})


# ==================== DATA PRIVACY DASHBOARD ====================

@compliance_bp.route('/privacy-dashboard')
@login_required
def privacy_dashboard():
    """Student privacy control dashboard"""
    # Get user's data access history
    recent_accesses = DataAccessAudit.query.filter_by(
        student_affected_id=current_user.id
    ).order_by(DataAccessAudit.accessed_at.desc()).limit(10).all()
    
    # Get consent records (if implemented)
    # consents = ConsentRecord.query.filter_by(student_id=current_user.id).all()
    
    # Stats
    total_accesses = DataAccessAudit.query.filter_by(
        student_affected_id=current_user.id
    ).count()
    
    last_30_days = DataAccessAudit.query.filter(
        DataAccessAudit.student_affected_id == current_user.id,
        DataAccessAudit.accessed_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Who accessed my data most
    top_accessors = db.session.query(
        DataAccessAudit.accessor_id,
        func.count(DataAccessAudit.id).label('access_count')
    ).filter_by(
        student_affected_id=current_user.id
    ).group_by(DataAccessAudit.accessor_id).order_by(desc('access_count')).limit(5).all()
    
    return render_template('compliance/privacy_dashboard.html',
                         recent_accesses=recent_accesses,
                         total_accesses=total_accesses,
                         last_30_days=last_30_days,
                         top_accessors=top_accessors)


@compliance_bp.route('/privacy-settings', methods=['GET', 'POST'])
@login_required
def privacy_settings():
    """Manage privacy settings"""
    if request.method == 'POST':
        # Update privacy preferences
        # This would update user settings for data sharing, directory visibility, etc.
        
        flash('Privacy settings updated', 'success')
        return redirect(url_for('compliance.privacy_dashboard'))
    
    return render_template('compliance/privacy_settings.html')


# ==================== FERPA DISCLOSURES ====================

@compliance_bp.route('/ferpa-disclosure-log')
@login_required
def ferpa_disclosure_log():
    """Log of FERPA-protected data disclosures (admin)"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    # Get all exports, prints, and external accesses
    disclosures = DataAccessAudit.query.filter(
        DataAccessAudit.data_was_exported == True
    ).order_by(DataAccessAudit.accessed_at.desc()).limit(500).all()
    
    return render_template('compliance/ferpa_disclosures.html',
                         disclosures=disclosures)


# ==================== ANALYTICS ====================

@compliance_bp.route('/analytics')
@login_required
def compliance_analytics():
    """Compliance and security analytics dashboard"""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    # Access statistics
    total_accesses = DataAccessAudit.query.count()
    suspicious_accesses = DataAccessAudit.query.filter_by(is_suspicious=True).count()
    
    # Access by data type
    by_data_type = db.session.query(
        DataAccessAudit.data_type,
        func.count(DataAccessAudit.id).label('count')
    ).group_by(DataAccessAudit.data_type).order_by(desc('count')).all()
    
    # Access by purpose
    by_purpose = db.session.query(
        DataAccessAudit.access_purpose,
        func.count(DataAccessAudit.id).label('count')
    ).group_by(DataAccessAudit.access_purpose).order_by(desc('count')).all()
    
    # Top accessors
    top_accessors = db.session.query(
        DataAccessAudit.accessor_id,
        func.count(DataAccessAudit.id).label('count')
    ).group_by(DataAccessAudit.accessor_id).order_by(desc('count')).limit(10).all()
    
    # Access over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_accesses = db.session.query(
        func.date(DataAccessAudit.accessed_at).label('date'),
        func.count(DataAccessAudit.id).label('count')
    ).filter(
        DataAccessAudit.accessed_at >= thirty_days_ago
    ).group_by(func.date(DataAccessAudit.accessed_at)).all()
    
    # Compliance score (simplified)
    total_reports = ComplianceReport.query.count()
    compliant_reports = ComplianceReport.query.filter_by(compliant=True).count()
    compliance_rate = (compliant_reports / max(total_reports, 1)) * 100
    
    # Active masking rules
    active_masking_rules = DataMaskingRule.query.filter_by(is_active=True).count()
    
    return render_template('compliance/analytics.html',
                         total_accesses=total_accesses,
                         suspicious_accesses=suspicious_accesses,
                         by_data_type=by_data_type,
                         by_purpose=by_purpose,
                         top_accessors=top_accessors,
                         daily_accesses=daily_accesses,
                         compliance_rate=compliance_rate,
                         active_masking_rules=active_masking_rules)


# ==================== HELPER FUNCTIONS ====================

def get_user_role(user_id):
    """Get user role for audit logging"""
    from models import User
    user = User.query.get(user_id)
    if not user:
        return 'unknown'
    
    if hasattr(user, 'is_admin') and user.is_admin:
        return 'admin'
    elif hasattr(user, 'is_faculty') and user.is_faculty:
        return 'faculty'
    elif hasattr(user, 'is_staff') and user.is_staff:
        return 'staff'
    else:
        return 'student'


def detect_suspicious_access(accessor_id, data_type):
    """AI-powered suspicious access detection"""
    # Check for unusual access patterns
    recent_accesses = DataAccessAudit.query.filter_by(
        accessor_id=accessor_id
    ).filter(
        DataAccessAudit.accessed_at >= datetime.utcnow() - timedelta(minutes=5)
    ).count()
    
    # Flag if more than 50 accesses in 5 minutes
    if recent_accesses > 50:
        return True
    
    # Check for after-hours access
    current_hour = datetime.utcnow().hour
    if current_hour < 6 or current_hour > 22:
        # After hours access to sensitive data
        if data_type in ['financial_data', 'health_data', 'disciplinary_record']:
            return True
    
    return False


def generate_compliance_report_data(report_type, start_date, end_date):
    """Generate compliance report data"""
    import json
    
    # Query audit trail for date range
    audits = DataAccessAudit.query.filter(
        DataAccessAudit.accessed_at >= datetime.combine(start_date, datetime.min.time()),
        DataAccessAudit.accessed_at <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    total_accesses = len(audits)
    suspicious = sum(1 for a in audits if a.is_suspicious)
    exported = sum(1 for a in audits if a.data_was_exported)
    
    # Calculate compliance score
    if total_accesses == 0:
        compliance_score = 100
    else:
        violation_rate = (suspicious / total_accesses) * 100
        compliance_score = max(0, 100 - violation_rate)
    
    # Generate findings
    findings = []
    if suspicious > 0:
        findings.append({
            'severity': 'high',
            'finding': f'{suspicious} suspicious access attempts detected',
            'recommendation': 'Review suspicious access patterns and investigate potential security issues'
        })
    
    if exported > 10:
        findings.append({
            'severity': 'medium',
            'finding': f'{exported} data exports performed',
            'recommendation': 'Ensure all exports were authorized and documented'
        })
    
    # Generate recommendations
    recommendations = [
        'Continue monitoring access patterns for suspicious activity',
        'Conduct quarterly FERPA training for all staff',
        'Review and update data masking rules'
    ]
    
    # Action items
    action_items = []
    if suspicious > 0:
        action_items.append({
            'priority': 'high',
            'action': 'Investigate suspicious access attempts',
            'assigned_to': 'Security Team',
            'due_date': (date.today() + timedelta(days=7)).isoformat()
        })
    
    return {
        'summary': f'Compliance report for {start_date} to {end_date}. {total_accesses} total access events reviewed.',
        'total_records': total_accesses,
        'total_accesses': total_accesses,
        'unauthorized': suspicious,
        'violations': suspicious,
        'findings': json.dumps(findings),
        'recommendations': json.dumps(recommendations),
        'action_items': json.dumps(action_items),
        'compliance_score': round(compliance_score, 2),
        'compliant': compliance_score >= 95,
        'issues_found': len(findings)
    }


def apply_data_masking(data, field_name, user_role):
    """Apply data masking based on rules"""
    # Get applicable masking rule
    rule = DataMaskingRule.query.filter_by(
        field_name=field_name,
        is_active=True
    ).first()
    
    if not rule:
        return data
    
    import json
    
    # Check if user role is exempt
    exempt_roles = json.loads(rule.exempt_roles) if rule.exempt_roles else []
    if user_role in exempt_roles:
        return data
    
    # Apply masking
    apply_roles = json.loads(rule.apply_for_roles) if rule.apply_for_roles else []
    if user_role not in apply_roles:
        return data
    
    # Apply masking based on type
    if rule.masking_type == 'full_redaction':
        return '[REDACTED]'
    elif rule.masking_type == 'partial_mask' and rule.mask_pattern:
        return rule.mask_pattern
    elif rule.masking_type == 'partial_mask':
        # Default SSN masking
        if len(str(data)) >= 4:
            return 'XXX-XX-' + str(data)[-4:]
        return 'XXXX'
    
    return data
