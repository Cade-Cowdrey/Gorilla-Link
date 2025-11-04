"""
PittState-Connect | System Health & Status Monitoring
Provides health check endpoints for monitoring and diagnostics.
"""

from flask import Blueprint, jsonify, current_app
from extensions import db, redis_client, cache
from datetime import datetime
import os
import psutil


bp = Blueprint("health", __name__, url_prefix="/health")


def check_database() -> dict:
    """Check database connectivity"""
    try:
        # Execute simple query
        db.session.execute(db.text("SELECT 1"))
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_redis() -> dict:
    """Check Redis connectivity"""
    try:
        if redis_client:
            redis_client.ping()
            return {"status": "healthy", "message": "Redis connection OK"}
        else:
            return {"status": "disabled", "message": "Redis not configured"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_cache() -> dict:
    """Check cache system"""
    try:
        # Try to set and get a test value
        cache.set('health_check', 'ok', timeout=10)
        value = cache.get('health_check')
        if value == 'ok':
            return {"status": "healthy", "message": "Cache working"}
        return {"status": "unhealthy", "message": "Cache read/write failed"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_disk_space() -> dict:
    """Check disk space availability"""
    try:
        usage = psutil.disk_usage('/')
        percent_used = usage.percent
        
        if percent_used > 90:
            status = "critical"
        elif percent_used > 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "percent_used": percent_used,
            "total_gb": round(usage.total / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2)
        }
    except Exception as e:
        return {"status": "unknown", "message": str(e)}


def check_memory() -> dict:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used > 90:
            status = "critical"
        elif percent_used > 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "percent_used": percent_used,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2)
        }
    except Exception as e:
        return {"status": "unknown", "message": str(e)}


def check_openai() -> dict:
    """Check OpenAI API configuration"""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        # Don't actually call the API, just check if configured
        return {"status": "configured", "message": "OpenAI API key present"}
    return {"status": "not_configured", "message": "OpenAI API key not set"}


@bp.route("/")
def health_check():
    """
    Basic health check endpoint
    Returns 200 if service is up, 503 if critical components are down
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "cache": check_cache(),
    }
    
    # Determine overall status
    critical_failures = [
        name for name, result in checks.items() 
        if result.get("status") == "unhealthy"
    ]
    
    if critical_failures:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "failed_checks": critical_failures
        }), 503
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }), 200


@bp.route("/detailed")
def detailed_health():
    """
    Detailed health check with all system metrics
    Requires authentication in production
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "cache": check_cache(),
        "disk": check_disk_space(),
        "memory": check_memory(),
        "openai": check_openai(),
    }
    
    # System info
    system_info = {
        "python_version": os.sys.version,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
    }
    
    # App config (sanitized)
    app_config = {
        "debug": current_app.debug,
        "testing": current_app.testing,
        "environment": os.getenv('FLASK_ENV', 'production'),
    }
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "system": system_info,
        "app": app_config
    }), 200


@bp.route("/ready")
def readiness_check():
    """
    Kubernetes-style readiness probe
    Returns 200 if service is ready to accept traffic
    """
    db_check = check_database()
    
    if db_check["status"] == "healthy":
        return jsonify({"status": "ready"}), 200
    
    return jsonify({"status": "not ready", "reason": "database unavailable"}), 503


@bp.route("/live")
def liveness_check():
    """
    Kubernetes-style liveness probe
    Returns 200 if service is alive (even if not fully functional)
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@bp.route("/metrics")
def metrics():
    """
    Prometheus-style metrics endpoint
    """
    try:
        # Get database stats
        from models import User, Scholarship, Job
        
        user_count = User.query.count()
        scholarship_count = Scholarship.query.count()
        job_count = Job.query.count()
        
        metrics_text = f"""
# HELP pittstate_users_total Total number of users
# TYPE pittstate_users_total gauge
pittstate_users_total {user_count}

# HELP pittstate_scholarships_total Total number of scholarships
# TYPE pittstate_scholarships_total gauge
pittstate_scholarships_total {scholarship_count}

# HELP pittstate_jobs_total Total number of jobs
# TYPE pittstate_jobs_total gauge
pittstate_jobs_total {job_count}

# HELP pittstate_disk_usage_percent Disk usage percentage
# TYPE pittstate_disk_usage_percent gauge
pittstate_disk_usage_percent {check_disk_space().get('percent_used', 0)}

# HELP pittstate_memory_usage_percent Memory usage percentage
# TYPE pittstate_memory_usage_percent gauge
pittstate_memory_usage_percent {check_memory().get('percent_used', 0)}
"""
        
        return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        current_app.logger.error(f"Metrics error: {str(e)}")
        return "# Error generating metrics\n", 500, {'Content-Type': 'text/plain; charset=utf-8'}
