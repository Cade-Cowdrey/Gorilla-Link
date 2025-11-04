"""
PittState-Connect | Performance Monitoring Routes
Real-time performance metrics and query analytics dashboard.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db, redis_client, cache
from utils.query_optimizer import _tracker, get_query_plan, find_missing_indexes
from utils.advanced_rate_limiting import get_abuse_alerts
from datetime import datetime, timedelta
import psutil
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("performance", __name__, url_prefix="/admin/performance")


def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapped


@bp.route("/")
@login_required
@admin_required
def dashboard():
    """Performance monitoring dashboard"""
    return render_template("admin/performance_dashboard.html",
                         title="Performance Monitoring | PittState-Connect")


@bp.route("/api/metrics")
@login_required
@admin_required
def get_metrics():
    """Get current system metrics"""
    try:
        metrics = {
            # System metrics
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            
            # Database metrics
            "db_connections": _get_db_connection_count(),
            "db_pool_size": db.engine.pool.size(),
            "db_pool_checked_out": db.engine.pool.checkedout(),
            
            # Cache metrics
            "cache_hit_rate": _get_cache_hit_rate(),
            "redis_memory": _get_redis_memory(),
            
            # Application metrics
            "active_sessions": _get_active_session_count(),
            "request_rate": _get_request_rate(),
            
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/slow-queries")
@login_required
@admin_required
@cache.cached(timeout=60)
def get_slow_queries():
    """Get recent slow queries"""
    try:
        # This would integrate with your query tracking
        slow_queries = _tracker.get_stats()
        
        return jsonify({
            "queries": slow_queries.get('queries', [])[:50],  # Last 50 queries
            "stats": {
                "total": slow_queries.get('total_queries', 0),
                "avg_time": slow_queries.get('avg_time', 0),
                "total_time": slow_queries.get('total_time', 0)
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting slow queries: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/rate-limits")
@login_required
@admin_required
def get_rate_limit_status():
    """Get rate limit violations"""
    try:
        abuse_alerts = get_abuse_alerts(limit=100)
        
        return jsonify({
            "alerts": abuse_alerts,
            "total": len(abuse_alerts)
        }), 200
    except Exception as e:
        logger.error(f"Error getting rate limits: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/recommendations")
@login_required
@admin_required
@cache.cached(timeout=3600)
def get_recommendations():
    """Get performance optimization recommendations"""
    try:
        from models import User, Scholarship, Job, Event
        
        recommendations = []
        
        # Check for missing indexes
        for model in [User, Scholarship, Job, Event]:
            missing = find_missing_indexes(model)
            recommendations.extend(missing)
        
        # Check cache hit rate
        hit_rate = _get_cache_hit_rate()
        if hit_rate < 70:
            recommendations.append(
                f"Low cache hit rate ({hit_rate}%). Consider caching more frequently accessed data."
            )
        
        # Check database pool
        pool_usage = (db.engine.pool.checkedout() / db.engine.pool.size()) * 100
        if pool_usage > 80:
            recommendations.append(
                f"High database connection pool usage ({pool_usage:.1f}%). Consider increasing pool size."
            )
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            recommendations.append(
                f"High memory usage ({memory.percent}%). Consider optimizing queries or adding more RAM."
            )
        
        return jsonify({
            "recommendations": recommendations,
            "total": len(recommendations),
            "priority": "high" if len(recommendations) > 5 else "medium" if len(recommendations) > 2 else "low"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/endpoints")
@login_required
@admin_required
def get_endpoint_stats():
    """Get per-endpoint performance statistics"""
    try:
        # This would integrate with your API usage tracking
        from models import ApiUsage
        from sqlalchemy import func
        
        # Get stats for last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        
        stats = db.session.query(
            ApiUsage.endpoint,
            func.count(ApiUsage.id).label('requests'),
            func.avg(ApiUsage.response_time_ms).label('avg_time'),
            func.max(ApiUsage.response_time_ms).label('max_time'),
            func.sum(
                db.case(
                    (ApiUsage.status_code >= 500, 1),
                    else_=0
                )
            ).label('errors')
        ).filter(
            ApiUsage.timestamp >= since
        ).group_by(
            ApiUsage.endpoint
        ).order_by(
            func.avg(ApiUsage.response_time_ms).desc()
        ).limit(50).all()
        
        results = [
            {
                "endpoint": stat.endpoint,
                "requests": stat.requests,
                "avg_time": round(stat.avg_time, 2) if stat.avg_time else 0,
                "max_time": round(stat.max_time, 2) if stat.max_time else 0,
                "errors": stat.errors or 0,
                "error_rate": round((stat.errors / stat.requests * 100), 2) if stat.requests else 0
            }
            for stat in stats
        ]
        
        return jsonify({"endpoints": results}), 200
        
    except Exception as e:
        logger.error(f"Error getting endpoint stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Helper functions

def _get_db_connection_count():
    """Get current database connection count"""
    try:
        result = db.session.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
        )
        return result.scalar()
    except:
        return 0


def _get_cache_hit_rate():
    """Calculate cache hit rate (simplified)"""
    if not redis_client:
        return 0
    
    try:
        info = redis_client.info('stats')
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        
        if hits + misses == 0:
            return 0
        
        return round((hits / (hits + misses)) * 100, 2)
    except:
        return 0


def _get_redis_memory():
    """Get Redis memory usage in MB"""
    if not redis_client:
        return 0
    
    try:
        info = redis_client.info('memory')
        return round(info.get('used_memory', 0) / (1024 * 1024), 2)
    except:
        return 0


def _get_active_session_count():
    """Get count of active sessions"""
    try:
        from models import User
        # Count users active in last 15 minutes
        since = datetime.utcnow() - timedelta(minutes=15)
        return User.query.filter(User.last_seen >= since).count()
    except:
        return 0


def _get_request_rate():
    """Get requests per minute (last 5 minutes)"""
    try:
        from models import ApiUsage
        since = datetime.utcnow() - timedelta(minutes=5)
        count = ApiUsage.query.filter(ApiUsage.timestamp >= since).count()
        return round(count / 5, 2)  # Per minute
    except:
        return 0
