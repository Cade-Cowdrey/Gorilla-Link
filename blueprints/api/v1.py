"""
API v1 Blueprint - Production-Grade REST API
Integrates all services: AI, Security, Analytics, Communication, Integration
"""

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from extensions import limiter, cache
from services.ai_service import get_ai_service
from services.security_service import get_security_service
from services.analytics_service import get_analytics_service
from services.communication_service import get_communication_service
from services.integration_service import get_integration_service
from services.monitoring_service import get_monitoring_service
from services.feature_flag_service import get_feature_flag_service
from services.data_governance_service import get_data_governance_service
from services.notification_hub_service import get_notification_hub_service
from services.monetization_service import get_monetization_service
from services.resume_builder_service import get_resume_builder_service
from functools import wraps
import os
import logging

logger = logging.getLogger(__name__)

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# ============================================================
# DECORATORS
# ============================================================

def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.name != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    """Require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        
        # Validate API key (simplified)
        from models_extended import LicenseKey
        license_key = LicenseKey.query.filter_by(key=api_key, active=True).first()
        if not license_key:
            return jsonify({"error": "Invalid API key"}), 401
        
        # Check rate limits
        if license_key.api_calls_used >= license_key.max_api_calls:
            return jsonify({"error": "API rate limit exceeded"}), 429
        
        # Increment usage
        license_key.api_calls_used += 1
        from extensions import db
        db.session.commit()
        
        g.license_key = license_key
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# HEALTH & MONITORING
# ============================================================

@api_v1.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    monitoring = get_monitoring_service()
    return jsonify(monitoring.health_check())


@api_v1.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    monitoring = get_monitoring_service()
    return monitoring.export_metrics(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@api_v1.route('/status', methods=['GET'])
@login_required
@admin_required
def system_status():
    """Comprehensive system status"""
    monitoring = get_monitoring_service()
    return jsonify({
        "health": monitoring.health_check(),
        "performance": monitoring.get_performance_report(),
        "alerts": monitoring.check_alerts()
    })


# ============================================================
# AI ASSISTANT (GorillaGPT)
# ============================================================

@api_v1.route('/ai/chat', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def ai_chat():
    """AI chat assistant"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    message = data.get('message')
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    ai_service = get_ai_service(
        api_key=os.getenv('OPENAI_API_KEY'),
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    )
    
    result = ai_service.chat(
        user_id=current_user.id,
        message=message,
        session_id=session_id
    )
    
    # Record metrics
    monitoring = get_monitoring_service()
    monitoring.record_ai_request(
        model=result.get('model', 'unknown'),
        status='success' if 'error' not in result else 'error',
        tokens=result.get('tokens_used', 0)
    )
    
    return jsonify(result)


@api_v1.route('/ai/resume/generate', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def ai_generate_resume():
    """AI-powered resume generation"""
    data = request.get_json()
    if not data:
        data = {}
    
    ai_service = get_ai_service(
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    user_data = {
        "name": current_user.full_name,
        "email": current_user.email,
        "major": current_user.major,
        "graduation_year": current_user.graduation_year,
        "skills": data.get('skills', []),
        "experience": data.get('experience', ''),
        "education": data.get('education', '')
    }
    
    resume = ai_service.build_resume(current_user.id, user_data)
    
    return jsonify({
        "resume": resume,
        "user_id": current_user.id
    })


@api_v1.route('/ai/essay/improve', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def improve_essay():
    """AI essay improvement suggestions"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    essay_text = data.get('essay')
    prompt = data.get('prompt', '')
    
    if not essay_text:
        return jsonify({"error": "Essay text required"}), 400
    
    ai_service = get_ai_service(api_key=os.getenv('OPENAI_API_KEY'))
    result = ai_service.improve_essay(essay_text, prompt)
    
    return jsonify(result)


# ============================================================
# SECURITY
# ============================================================

@api_v1.route('/security/2fa/enable', methods=['POST'])
@login_required
def enable_2fa():
    """Enable 2FA for user"""
    security = get_security_service()
    result = security.enable_2fa(current_user.id, current_user.email)
    return jsonify(result)


@api_v1.route('/security/2fa/verify', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA token"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    token = data.get('token')
    
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    security = get_security_service()
    valid = security.verify_2fa_token(current_user.id, token)
    
    return jsonify({"valid": valid})


@api_v1.route('/security/audit-logs', methods=['GET'])
@login_required
def get_audit_logs():
    """Get user audit logs"""
    security = get_security_service()
    logs = security.get_audit_logs(user_id=current_user.id, limit=50)
    
    return jsonify({
        "logs": [{
            "action": log.action,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details,
            "severity": log.severity
        } for log in logs]
    })


@api_v1.route('/security/consent', methods=['POST'])
@login_required
def record_consent():
    """Record user consent"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    consent_type = data.get('consent_type')
    granted = data.get('granted', False)
    
    if not consent_type:
        return jsonify({"error": "Consent type required"}), 400
    
    security = get_security_service()
    success = security.record_consent(
        user_id=current_user.id,
        consent_type=consent_type,
        granted=granted,
        ip_address=request.remote_addr
    )
    
    return jsonify({"success": success})


# ============================================================
# ANALYTICS
# ============================================================

@api_v1.route('/analytics/dashboard', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def analytics_dashboard():
    """Get admin analytics dashboard"""
    days = request.args.get('days', 30, type=int)
    
    analytics = get_analytics_service()
    dashboard = analytics.get_admin_dashboard(days=days)
    
    return jsonify(dashboard)


@api_v1.route('/analytics/department/<int:department_id>', methods=['GET'])
@login_required
def department_scorecard(department_id):
    """Get department scorecard"""
    days = request.args.get('days', 30, type=int)
    
    analytics = get_analytics_service()
    scorecard = analytics.get_department_scorecard(department_id, days=days)
    
    return jsonify(scorecard)


@api_v1.route('/analytics/export/<report_type>', methods=['GET'])
@login_required
@admin_required
def export_analytics(report_type):
    """Export analytics data"""
    format_type = request.args.get('format', 'csv')
    
    analytics = get_analytics_service()
    
    if format_type == 'csv':
        buffer = analytics.export_analytics_csv(report_type)
        return buffer.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename={report_type}.csv'
        }
    elif format_type == 'pdf':
        buffer = analytics.export_analytics_pdf(report_type)
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename={report_type}.pdf'
        }
    
    return jsonify({"error": "Invalid format"}), 400


@api_v1.route('/analytics/insights', methods=['GET'])
@login_required
@cache.cached(timeout=3600)  # Cache for 1 hour
def ai_insights():
    """Get AI-generated insights"""
    days = request.args.get('days', 7, type=int)
    
    analytics = get_analytics_service()
    insights = analytics.generate_ai_insights(days=days)
    
    return jsonify({"insights": insights})


@api_v1.route('/analytics/predict/churn/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def predict_churn(user_id):
    """Predict student churn risk"""
    analytics = get_analytics_service()
    prediction = analytics.predict_student_churn(user_id)
    
    return jsonify(prediction)


# ============================================================
# COMMUNICATION
# ============================================================

@api_v1.route('/inbox', methods=['GET'])
@login_required
def unified_inbox():
    """Get unified inbox"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    comm = get_communication_service()
    inbox = comm.get_unified_inbox(current_user.id, page=page, per_page=per_page)
    
    return jsonify(inbox)


@api_v1.route('/messages/send', methods=['POST'])
@login_required
@limiter.limit("30 per hour")
def send_message():
    """Send internal message"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    recipient_id = data.get('recipient_id')
    subject = data.get('subject')
    body = data.get('body')
    
    if not all([recipient_id, subject, body]):
        return jsonify({"error": "Missing required fields"}), 400
    
    comm = get_communication_service()
    result = comm.send_message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        subject=subject,
        body=body
    )
    
    return jsonify(result)


@api_v1.route('/notifications/create', methods=['POST'])
@login_required
@admin_required
def create_notification():
    """Create system notification"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    comm = get_communication_service()
    success = comm.create_notification(
        recipient_id=data.get('recipient_id'),
        message=data.get('message'),
        category=data.get('category', 'info'),
        link=data.get('link')
    )
    
    return jsonify({"success": success})


@api_v1.route('/announcements', methods=['GET'])
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_announcements():
    """Get active announcements"""
    department_id = request.args.get('department_id', type=int)
    
    comm = get_communication_service()
    announcements = comm.get_active_announcements(department_id=department_id)
    
    return jsonify({
        "announcements": [{
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "priority": a.priority,
            "published_at": a.published_at.isoformat()
        } for a in announcements]
    })


# ============================================================
# INTEGRATIONS
# ============================================================

@api_v1.route('/integrations/payment/initialize', methods=['POST'])
@login_required
def initialize_payment():
    """Initialize Stripe payment"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    integration = get_integration_service({
        "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY")
    })
    
    if not integration:
        return jsonify({"error": "Integration service not available"}), 503
    
    result = integration.initialize_stripe_payment(
        user_id=current_user.id,
        amount=data.get('amount'),
        currency=data.get('currency', 'USD'),
        purpose=data.get('purpose', 'donation'),
        metadata=data.get('metadata')
    )
    
    return jsonify(result)


@api_v1.route('/integrations/sms/send', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def send_sms():
    """Send SMS notification"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    integration = get_integration_service({
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER")
    })
    
    if not integration:
        return jsonify({"error": "Integration service not available"}), 503
    
    success = integration.send_sms(
        to_phone=data.get('phone'),
        message=data.get('message')
    )
    
    return jsonify({"success": success})


# ============================================================
# ERROR HANDLERS
# ============================================================

@api_v1.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": str(e)}), 400


@api_v1.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401


@api_v1.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden", "message": "Insufficient permissions"}), 403


@api_v1.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": str(e)}), 404


@api_v1.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Rate limit exceeded", "message": "Too many requests"}), 429


@api_v1.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    monitoring = get_monitoring_service()
    monitoring.record_error("internal_server_error", "critical")
    return jsonify({"error": "Internal server error"}), 500


# ============================================================
# FEATURE FLAGS
# ============================================================

@api_v1.route('/feature-flags', methods=['GET'])
@login_required
def get_feature_flags():
    """Get all feature flags for current user"""
    try:
        service = get_feature_flag_service()
        role = current_user.role.name if current_user.role else None
        flags = service.get_user_flags(current_user.id, role)
        
        return jsonify({
            "user_id": current_user.id,
            "flags": flags
        }), 200
    except Exception as e:
        logger.error(f"Get feature flags error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/feature-flags/check/<flag_name>', methods=['GET'])
@login_required
def check_feature_flag(flag_name):
    """Check if a specific feature is enabled"""
    try:
        service = get_feature_flag_service()
        role = current_user.role.name if current_user.role else None
        enabled = service.is_enabled(flag_name, current_user.id, role)
        
        return jsonify({
            "flag": flag_name,
            "enabled": enabled
        }), 200
    except Exception as e:
        logger.error(f"Check feature flag error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/feature-flags', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def create_feature_flag():
    """Create a new feature flag (admin only)"""
    try:
        data = request.get_json()
        service = get_feature_flag_service()
        
        success = service.create_flag(
            name=data['name'],
            description=data['description'],
            enabled=data.get('enabled', False),
            rollout_percentage=data.get('rollout_percentage', 0.0),
            target_users=data.get('target_users'),
            target_roles=data.get('target_roles')
        )
        
        if success:
            return jsonify({"message": "Feature flag created"}), 201
        else:
            return jsonify({"error": "Feature flag creation failed"}), 400
    except Exception as e:
        logger.error(f"Create feature flag error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/feature-flags/<flag_name>', methods=['PUT'])
@login_required
@admin_required
@limiter.limit("20 per hour")
def update_feature_flag(flag_name):
    """Update feature flag configuration (admin only)"""
    try:
        data = request.get_json()
        service = get_feature_flag_service()
        
        success = service.update_flag(
            name=flag_name,
            enabled=data.get('enabled'),
            rollout_percentage=data.get('rollout_percentage'),
            target_users=data.get('target_users'),
            target_roles=data.get('target_roles')
        )
        
        if success:
            return jsonify({"message": "Feature flag updated"}), 200
        else:
            return jsonify({"error": "Feature flag not found"}), 404
    except Exception as e:
        logger.error(f"Update feature flag error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/feature-flags/<flag_name>', methods=['DELETE'])
@login_required
@admin_required
@limiter.limit("5 per hour")
def delete_feature_flag(flag_name):
    """Delete a feature flag (admin only)"""
    try:
        service = get_feature_flag_service()
        success = service.delete_flag(flag_name)
        
        if success:
            return jsonify({"message": "Feature flag deleted"}), 200
        else:
            return jsonify({"error": "Feature flag not found"}), 404
    except Exception as e:
        logger.error(f"Delete feature flag error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests', methods=['GET'])
@login_required
@admin_required
def get_ab_tests():
    """Get all A/B tests (admin only)"""
    try:
        service = get_feature_flag_service()
        status = request.args.get('status')
        tests = service.get_all_ab_tests(status)
        
        return jsonify({
            "tests": [{
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "status": t.status,
                "traffic_split": t.traffic_split,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "ended_at": t.ended_at.isoformat() if t.ended_at else None,
                "winner": t.winner
            } for t in tests]
        }), 200
    except Exception as e:
        logger.error(f"Get A/B tests error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per hour")
def create_ab_test():
    """Create a new A/B test (admin only)"""
    try:
        data = request.get_json()
        service = get_feature_flag_service()
        
        success = service.create_ab_test(
            name=data['name'],
            description=data['description'],
            variant_a=data['variant_a'],
            variant_b=data['variant_b'],
            traffic_split=data.get('traffic_split', 0.5)
        )
        
        if success:
            return jsonify({"message": "A/B test created"}), 201
        else:
            return jsonify({"error": "A/B test creation failed"}), 400
    except Exception as e:
        logger.error(f"Create A/B test error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests/<int:test_id>/start', methods=['POST'])
@login_required
@admin_required
def start_ab_test(test_id):
    """Start an A/B test (admin only)"""
    try:
        service = get_feature_flag_service()
        success = service.start_ab_test(test_id)
        
        if success:
            return jsonify({"message": "A/B test started"}), 200
        else:
            return jsonify({"error": "A/B test not found"}), 404
    except Exception as e:
        logger.error(f"Start A/B test error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests/<int:test_id>/stop', methods=['POST'])
@login_required
@admin_required
def stop_ab_test(test_id):
    """Stop an A/B test (admin only)"""
    try:
        data = request.get_json()
        service = get_feature_flag_service()
        success = service.stop_ab_test(test_id, data.get('winner'))
        
        if success:
            return jsonify({"message": "A/B test stopped"}), 200
        else:
            return jsonify({"error": "A/B test not found"}), 404
    except Exception as e:
        logger.error(f"Stop A/B test error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests/<int:test_id>/variant', methods=['GET'])
@login_required
def get_ab_variant(test_id):
    """Get A/B test variant for current user"""
    try:
        service = get_feature_flag_service()
        variant = service.get_ab_variant(test_id, current_user.id)
        
        if variant:
            return jsonify({"test_id": test_id, "variant": variant}), 200
        else:
            return jsonify({"error": "Test not found or not running"}), 404
    except Exception as e:
        logger.error(f"Get A/B variant error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/ab-tests/<int:test_id>/results', methods=['GET'])
@login_required
@admin_required
def get_ab_test_results(test_id):
    """Get A/B test results (admin only)"""
    try:
        service = get_feature_flag_service()
        results = service.get_ab_test_results(test_id)
        
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Get A/B test results error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# DATA GOVERNANCE
# ============================================================

@api_v1.route('/governance/lineage/<entity_type>/<int:entity_id>', methods=['GET'])
@login_required
@admin_required
def get_lineage(entity_type, entity_id):
    """Get data lineage chain (admin only)"""
    try:
        service = get_data_governance_service()
        chain = service.get_lineage_chain(entity_type, entity_id)
        
        return jsonify({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "lineage_chain": chain
        }), 200
    except Exception as e:
        logger.error(f"Get lineage error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/lineage-graph/<entity_type>/<int:entity_id>', methods=['GET'])
@login_required
@admin_required
def get_lineage_graph(entity_type, entity_id):
    """Get data lineage as graph (admin only)"""
    try:
        service = get_data_governance_service()
        graph = service.get_lineage_graph(entity_type, entity_id)
        
        return jsonify(graph), 200
    except Exception as e:
        logger.error(f"Get lineage graph error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/bias/<model_name>', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=3600)
def get_bias_comparison(model_name):
    """Compare bias across demographic groups (admin only)"""
    try:
        service = get_data_governance_service()
        comparison = service.compare_bias_across_groups(model_name)
        
        return jsonify(comparison), 200
    except Exception as e:
        logger.error(f"Get bias comparison error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/bias', methods=['POST'])
@login_required
@admin_required
@limiter.limit("100 per hour")
def report_bias_metrics():
    """Report bias metrics for a model (admin only)"""
    try:
        data = request.get_json()
        service = get_data_governance_service()
        
        result = service.detect_bias(
            model_name=data['model_name'],
            prediction_type=data['prediction_type'],
            demographic_group=data['demographic_group'],
            true_positives=data['true_positives'],
            false_positives=data['false_positives'],
            true_negatives=data['true_negatives'],
            false_negatives=data['false_negatives']
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Report bias metrics error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/retention', methods=['GET'])
@login_required
@admin_required
def get_retention_policies():
    """Get all data retention policies (admin only)"""
    try:
        service = get_data_governance_service()
        policies = service.get_all_policies()
        
        return jsonify({
            "policies": [{
                "entity_type": p.entity_type,
                "retention_days": p.retention_days,
                "deletion_method": p.deletion_method,
                "legal_basis": p.legal_basis,
                "created_at": p.created_at.isoformat()
            } for p in policies]
        }), 200
    except Exception as e:
        logger.error(f"Get retention policies error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/retention', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def set_retention_policy():
    """Set data retention policy (admin only)"""
    try:
        data = request.get_json()
        service = get_data_governance_service()
        
        success = service.set_retention_policy(
            entity_type=data['entity_type'],
            retention_days=data['retention_days'],
            deletion_method=data.get('deletion_method', 'soft'),
            legal_basis=data.get('legal_basis')
        )
        
        if success:
            return jsonify({"message": "Retention policy set"}), 201
        else:
            return jsonify({"error": "Policy creation failed"}), 400
    except Exception as e:
        logger.error(f"Set retention policy error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/retention/<entity_type>/check', methods=['GET'])
@login_required
@admin_required
def check_retention_expiration(entity_type):
    """Check expired records (admin only)"""
    try:
        service = get_data_governance_service()
        expired = service.check_expiration(entity_type)
        
        return jsonify({
            "entity_type": entity_type,
            "expired_count": len(expired),
            "records": expired[:20]  # First 20
        }), 200
    except Exception as e:
        logger.error(f"Check expiration error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/governance/quality/<entity_type>', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=1800)
def check_data_quality(entity_type):
    """Run data quality checks (admin only)"""
    try:
        service = get_data_governance_service()
        results = service.check_data_quality(entity_type)
        
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Data quality check error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# NOTIFICATION HUB
# ============================================================

@api_v1.route('/notifications/preferences', methods=['GET'])
@login_required
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        service = get_notification_hub_service()
        preferences = service.get_preferences(current_user.id)
        
        return jsonify(preferences), 200
    except Exception as e:
        logger.error(f"Get notification preferences error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/preferences', methods=['PUT'])
@login_required
@limiter.limit("20 per hour")
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        data = request.get_json()
        service = get_notification_hub_service()
        
        success = service.update_preferences(current_user.id, data['preferences'])
        
        if success:
            return jsonify({"message": "Preferences updated"}), 200
        else:
            return jsonify({"error": "Update failed"}), 400
    except Exception as e:
        logger.error(f"Update notification preferences error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/channel/<channel>/enable', methods=['POST'])
@login_required
def enable_notification_channel(channel):
    """Enable a notification channel for all types"""
    try:
        service = get_notification_hub_service()
        success = service.enable_channel(current_user.id, channel)
        
        if success:
            return jsonify({"message": f"Channel {channel} enabled"}), 200
        else:
            return jsonify({"error": "Enable failed"}), 400
    except Exception as e:
        logger.error(f"Enable channel error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/channel/<channel>/disable', methods=['POST'])
@login_required
def disable_notification_channel(channel):
    """Disable a notification channel for all types"""
    try:
        service = get_notification_hub_service()
        success = service.disable_channel(current_user.id, channel)
        
        if success:
            return jsonify({"message": f"Channel {channel} disabled"}), 200
        else:
            return jsonify({"error": "Disable failed"}), 400
    except Exception as e:
        logger.error(f"Disable channel error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/list', methods=['GET'])
@login_required
def list_user_notifications():
    """Get user notification history"""
    try:
        service = get_notification_hub_service()
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        
        notifications = service.get_user_notifications(
            current_user.id,
            unread_only=unread_only,
            category=category,
            limit=limit
        )
        
        return jsonify({
            "notifications": notifications,
            "unread_count": service.get_unread_count(current_user.id)
        }), 200
    except Exception as e:
        logger.error(f"List notifications error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        service = get_notification_hub_service()
        success = service.mark_as_read(notification_id, current_user.id)
        
        if success:
            return jsonify({"message": "Notification marked as read"}), 200
        else:
            return jsonify({"error": "Notification not found"}), 404
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        service = get_notification_hub_service()
        success = service.mark_all_as_read(current_user.id)
        
        if success:
            return jsonify({"message": "All notifications marked as read"}), 200
        else:
            return jsonify({"error": "Update failed"}), 400
    except Exception as e:
        logger.error(f"Mark all read error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
@limiter.limit("30 per hour")
def send_notification():
    """Send notification (admin only)"""
    try:
        data = request.get_json()
        service = get_notification_hub_service()
        
        result = service.send(
            user_id=data['user_id'],
            notification_type=data['notification_type'],
            title=data['title'],
            message=data['message'],
            data=data.get('data'),
            link=data.get('link')
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/send-bulk', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def send_bulk_notification():
    """Send bulk notification (admin only)"""
    try:
        data = request.get_json()
        service = get_notification_hub_service()
        
        result = service.send_bulk(
            user_ids=data['user_ids'],
            notification_type=data['notification_type'],
            title=data['title'],
            message=data['message'],
            data=data.get('data'),
            link=data.get('link')
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Send bulk notification error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/notifications/stats', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=600)
def get_notification_stats():
    """Get notification statistics (admin only)"""
    try:
        service = get_notification_hub_service()
        days = int(request.args.get('days', 7))
        stats = service.get_notification_stats(days)
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Get notification stats error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# MONETIZATION & SUBSCRIPTIONS
# ============================================================

@api_v1.route('/subscriptions/tiers', methods=['GET'])
@cache.cached(timeout=3600)
def get_subscription_tiers():
    """Get all subscription tiers and pricing"""
    try:
        service = get_monetization_service()
        tiers = service.compare_tiers()
        return jsonify(tiers), 200
    except Exception as e:
        logger.error(f"Get tiers error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions/tiers/<tier_name>', methods=['GET'])
@cache.cached(timeout=3600)
def get_tier_info(tier_name):
    """Get detailed information about a specific tier"""
    try:
        service = get_monetization_service()
        tier = service.get_tier_info(tier_name)
        if not tier:
            return jsonify({"error": "Tier not found"}), 404
        return jsonify(tier), 200
    except Exception as e:
        logger.error(f"Get tier info error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def create_subscription():
    """Create new employer subscription"""
    try:
        data = request.get_json()
        service = get_monetization_service()
        
        subscription, error = service.create_subscription(
            user_id=current_user.id,
            tier_name=data['tier_name'],
            billing_cycle=data.get('billing_cycle', 'annually'),
            payment_method_id=data.get('payment_method_id')
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        if not subscription:
            return jsonify({"error": "Failed to create subscription"}), 500
        
        return jsonify({
            "id": subscription.id,
            "plan_name": subscription.plan_name,
            "billing_cycle": subscription.billing_cycle,
            "amount": subscription.amount,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }), 201
    except Exception as e:
        logger.error(f"Create subscription error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions/my', methods=['GET'])
@login_required
def get_my_subscription():
    """Get current user's active subscription"""
    try:
        service = get_monetization_service()
        subscription = service.get_user_subscription(current_user.id)
        
        if not subscription:
            return jsonify({"message": "No active subscription", "tier": "free"}), 200
        
        return jsonify({
            "id": subscription.id,
            "plan_name": subscription.plan_name,
            "billing_cycle": subscription.billing_cycle,
            "amount": subscription.amount,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }), 200
    except Exception as e:
        logger.error(f"Get my subscription error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions/<int:subscription_id>/upgrade', methods=['PUT'])
@login_required
@limiter.limit("5 per hour")
def upgrade_subscription(subscription_id):
    """Upgrade subscription to higher tier"""
    try:
        data = request.get_json()
        service = get_monetization_service()
        
        success, error = service.upgrade_subscription(
            subscription_id=subscription_id,
            new_tier=data['new_tier']
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({"message": "Subscription upgraded successfully"}), 200
    except Exception as e:
        logger.error(f"Upgrade subscription error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions/<int:subscription_id>/cancel', methods=['DELETE'])
@login_required
@limiter.limit("5 per hour")
def cancel_subscription(subscription_id):
    """Cancel subscription"""
    try:
        service = get_monetization_service()
        immediate = request.args.get('immediate', 'false').lower() == 'true'
        
        success, error = service.cancel_subscription(
            subscription_id=subscription_id,
            immediate=immediate
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({"message": "Subscription cancelled successfully"}), 200
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/subscriptions/benefits/<benefit>', methods=['GET'])
@login_required
def check_subscription_benefit(benefit):
    """Check if user has access to a specific benefit"""
    try:
        service = get_monetization_service()
        has_benefit = service.check_tier_benefits(current_user.id, benefit)
        
        return jsonify({
            "benefit": benefit,
            "has_access": has_benefit
        }), 200
    except Exception as e:
        logger.error(f"Check benefit error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# EVENT SPONSORSHIPS
# ============================================================

@api_v1.route('/sponsorships/packages', methods=['GET'])
@cache.cached(timeout=3600)
def get_sponsorship_packages():
    """Get all event sponsorship packages"""
    try:
        service = get_monetization_service()
        packages = service.get_sponsorship_packages()
        return jsonify(packages), 200
    except Exception as e:
        logger.error(f"Get sponsorship packages error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/sponsorships', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def create_event_sponsorship():
    """Sponsor an event"""
    try:
        data = request.get_json()
        service = get_monetization_service()
        
        sponsor_id, error = service.sponsor_event(
            event_id=data['event_id'],
            user_id=current_user.id,
            package_name=data['package_name'],
            payment_method_id=data.get('payment_method_id')
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({
            "sponsor_id": sponsor_id,
            "message": "Event sponsorship created successfully"
        }), 201
    except Exception as e:
        logger.error(f"Create sponsorship error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/sponsorships/events/<int:event_id>', methods=['GET'])
@cache.cached(timeout=600)
def get_event_sponsors(event_id):
    """Get all sponsors for an event"""
    try:
        service = get_monetization_service()
        sponsors = service.get_event_sponsors(event_id)
        return jsonify(sponsors), 200
    except Exception as e:
        logger.error(f"Get event sponsors error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# MONETIZATION ANALYTICS (ADMIN)
# ============================================================

@api_v1.route('/monetization/revenue', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=3600)
def get_revenue_report():
    """Get revenue report for date range (admin only)"""
    try:
        from datetime import datetime, timedelta
        
        service = get_monetization_service()
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = service.get_revenue_report(start_date, end_date)
        return jsonify(report), 200
    except Exception as e:
        logger.error(f"Get revenue report error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/monetization/subscriptions/stats', methods=['GET'])
@login_required
@admin_required
@cache.cached(timeout=3600)
def get_subscription_statistics():
    """Get subscription statistics (admin only)"""
    try:
        service = get_monetization_service()
        stats = service.get_subscription_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Get subscription stats error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# AI RESUME BUILDER
# ============================================================

@api_v1.route('/resume/generate', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def generate_resume():
    """Generate resume from user profile"""
    try:
        data = request.get_json() or {}
        service = get_resume_builder_service()
        
        result = service.generate_resume(
            user_id=current_user.id,
            format_type=data.get('format_type', 'modern'),
            target_role=data.get('target_role')
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Generate resume error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/resume/analyze-ats', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def analyze_ats():
    """Analyze ATS compatibility of resume"""
    try:
        data = request.get_json()
        service = get_resume_builder_service()
        
        result = service.analyze_ats_score(
            resume_text=data['resume_text'],
            job_description=data.get('job_description')
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"ATS analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/resume/optimize', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def optimize_resume():
    """Optimize resume for specific job"""
    try:
        data = request.get_json()
        service = get_resume_builder_service()
        
        result = service.optimize_for_job(
            user_id=current_user.id,
            job_description=data['job_description'],
            job_title=data['job_title']
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Resume optimization error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/resume/cover-letter', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def generate_cover_letter():
    """Generate cover letter for job application"""
    try:
        data = request.get_json()
        service = get_resume_builder_service()
        
        result = service.generate_cover_letter(
            user_id=current_user.id,
            company_name=data['company_name'],
            job_title=data['job_title'],
            job_description=data.get('job_description')
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Cover letter generation error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# SMS & WHATSAPP COMMUNICATION
# ============================================================

@api_v1.route('/communications/sms', methods=['POST'])
@login_required
@admin_required
@limiter.limit("50 per hour")
def send_sms_message():
    """Send SMS message (admin only)"""
    try:
        data = request.get_json()
        service = get_communication_service()
        
        result = service.send_sms(
            to_phone=data['phone'],
            message=data['message'],
            user_id=data.get('user_id')
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/communications/whatsapp', methods=['POST'])
@login_required
@admin_required
@limiter.limit("50 per hour")
def send_whatsapp_message():
    """Send WhatsApp message (admin only)"""
    try:
        data = request.get_json()
        service = get_communication_service()
        
        result = service.send_whatsapp(
            to_phone=data['phone'],
            message=data['message'],
            user_id=data.get('user_id'),
            media_url=data.get('media_url')
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return jsonify({"error": str(e)}), 500


@api_v1.route('/communications/sms/bulk', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def send_bulk_sms():
    """Send bulk SMS (admin only)"""
    try:
        data = request.get_json()
        service = get_communication_service()
        
        result = service.send_bulk_sms(
            phone_numbers=data['phone_numbers'],
            message=data['message']
        )
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Bulk SMS error: {e}")
        return jsonify({"error": str(e)}), 500


