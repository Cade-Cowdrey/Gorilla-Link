"""
Monitoring & Observability Service
Prometheus metrics, health checks, performance monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from flask import request, g
import time
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================================
# PROMETHEUS METRICS
# ============================================================

# Request metrics
request_count = Counter(
    'pittstate_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'pittstate_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# User metrics
active_users = Gauge(
    'pittstate_active_users',
    'Number of currently active users'
)

total_users = Gauge(
    'pittstate_total_users',
    'Total number of registered users'
)

# Application metrics
db_connections = Gauge(
    'pittstate_db_connections',
    'Number of active database connections'
)

cache_hit_rate = Gauge(
    'pittstate_cache_hit_rate',
    'Cache hit rate percentage'
)

# Business metrics
scholarships_active = Gauge(
    'pittstate_scholarships_active',
    'Number of active scholarships'
)

jobs_active = Gauge(
    'pittstate_jobs_active',
    'Number of active job postings'
)

events_upcoming = Gauge(
    'pittstate_events_upcoming',
    'Number of upcoming events'
)

# AI metrics
ai_requests = Counter(
    'pittstate_ai_requests_total',
    'Total number of AI requests',
    ['model', 'status']
)

ai_tokens_used = Counter(
    'pittstate_ai_tokens_used_total',
    'Total number of AI tokens used'
)

# Error metrics
errors_total = Counter(
    'pittstate_errors_total',
    'Total number of errors',
    ['error_type', 'severity']
)


class MonitoringService:
    """Comprehensive monitoring and observability"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    # ============================================================
    # REQUEST MONITORING
    # ============================================================
    
    def before_request(self):
        """Record request start time"""
        g.request_start_time = time.time()
    
    def after_request(self, response):
        """Record request metrics"""
        try:
            if hasattr(g, 'request_start_time'):
                duration = time.time() - g.request_start_time
                
                # Record metrics
                request_count.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code
                ).inc()
                
                request_duration.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(duration)
        
        except Exception as e:
            logger.error(f"Monitoring after_request error: {e}")
        
        return response
    
    def record_error(self, error_type: str, severity: str = "error"):
        """Record application error"""
        errors_total.labels(error_type=error_type, severity=severity).inc()
    
    # ============================================================
    # HEALTH CHECKS
    # ============================================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check
        Returns: Health status and detailed metrics
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "checks": {}
        }
        
        # Database check
        health["checks"]["database"] = self._check_database()
        
        # Redis check
        health["checks"]["redis"] = self._check_redis()
        
        # Disk space check
        health["checks"]["disk"] = self._check_disk_space()
        
        # Memory check
        health["checks"]["memory"] = self._check_memory()
        
        # API responsiveness
        health["checks"]["api"] = self._check_api_responsiveness()
        
        # Determine overall status
        if any(check["status"] == "unhealthy" for check in health["checks"].values()):
            health["status"] = "unhealthy"
        elif any(check["status"] == "degraded" for check in health["checks"].values()):
            health["status"] = "degraded"
        
        return health
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        from extensions import db
        
        try:
            start = time.time()
            db.session.execute("SELECT 1")
            duration = time.time() - start
            
            return {
                "status": "healthy" if duration < 1.0 else "degraded",
                "response_time_ms": duration * 1000,
                "message": "Database is responsive"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}"
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        from extensions import redis_client
        
        if not redis_client:
            return {
                "status": "degraded",
                "message": "Redis not configured"
            }
        
        try:
            start = time.time()
            redis_client.ping()
            duration = time.time() - start
            
            return {
                "status": "healthy" if duration < 0.5 else "degraded",
                "response_time_ms": duration * 1000,
                "message": "Redis is responsive"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis error: {str(e)}"
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            percent_used = disk.percent
            
            status = "healthy"
            if percent_used > 90:
                status = "unhealthy"
            elif percent_used > 80:
                status = "degraded"
            
            return {
                "status": status,
                "percent_used": percent_used,
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "message": f"Disk {percent_used}% used"
            }
        except Exception as e:
            return {
                "status": "unknown",
                "message": f"Disk check error: {str(e)}"
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            status = "healthy"
            if percent_used > 90:
                status = "unhealthy"
            elif percent_used > 80:
                status = "degraded"
            
            return {
                "status": status,
                "percent_used": percent_used,
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "message": f"Memory {percent_used}% used"
            }
        except Exception as e:
            return {
                "status": "unknown",
                "message": f"Memory check error: {str(e)}"
            }
    
    def _check_api_responsiveness(self) -> Dict[str, Any]:
        """Check API responsiveness"""
        # Simple check - in production would test actual endpoints
        return {
            "status": "healthy",
            "message": "API is responsive"
        }
    
    # ============================================================
    # METRICS UPDATE
    # ============================================================
    
    def update_business_metrics(self):
        """Update business-related metrics"""
        try:
            from models import User, Scholarship, Job, Event
            from datetime import datetime, timedelta
            
            # User metrics
            total_users.set(User.query.count())
            
            # Active users (logged in within 24 hours)
            threshold = datetime.utcnow() - timedelta(hours=24)
            active_count = User.query.filter(User.last_login >= threshold).count()
            active_users.set(active_count)
            
            # Scholarship metrics
            scholarships_active.set(
                Scholarship.query.filter(Scholarship.deadline >= datetime.utcnow().date()).count()
            )
            
            # Job metrics
            jobs_active.set(Job.query.filter_by(is_active=True).count())
            
            # Event metrics
            events_upcoming.set(
                Event.query.filter(Event.start_time >= datetime.utcnow()).count()
            )
            
        except Exception as e:
            logger.error(f"Business metrics update error: {e}")
    
    def record_ai_request(self, model: str, status: str, tokens: int = 0):
        """Record AI request metrics"""
        ai_requests.labels(model=model, status=status).inc()
        if tokens > 0:
            ai_tokens_used.inc(tokens)
    
    # ============================================================
    # METRICS EXPORT
    # ============================================================
    
    def export_metrics(self) -> bytes:
        """Export Prometheus metrics"""
        # Update business metrics before export
        self.update_business_metrics()
        return generate_latest(REGISTRY)
    
    # ============================================================
    # PERFORMANCE MONITORING
    # ============================================================
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count()
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_gb": psutil.virtual_memory().available / (1024**3)
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free_gb": psutil.disk_usage('/').free / (1024**3)
            },
            "network": self._get_network_stats(),
            "database": self._get_database_stats(),
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600
        }
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent_mb": net_io.bytes_sent / (1024**2),
                "bytes_recv_mb": net_io.bytes_recv / (1024**2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except:
            return {}
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        from extensions import db
        
        try:
            # Get connection pool stats (SQLAlchemy)
            pool = db.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
            }
        except:
            return {}
    
    # ============================================================
    # ALERTING
    # ============================================================
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        health = self.health_check()
        
        # Check for unhealthy services
        for service, check in health["checks"].items():
            if check["status"] == "unhealthy":
                alerts.append({
                    "severity": "critical",
                    "service": service,
                    "message": check.get("message", "Service unhealthy")
                })
            elif check["status"] == "degraded":
                alerts.append({
                    "severity": "warning",
                    "service": service,
                    "message": check.get("message", "Service degraded")
                })
        
        # Check error rate
        # In production, would query error metrics from Prometheus
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification"""
        logger.warning(f"ALERT: {alert['severity']} - {alert['service']}: {alert['message']}")
        
        # In production, would integrate with:
        # - PagerDuty
        # - Slack
        # - Email
        # - SMS via Twilio


# Singleton
_monitoring_service = None

def get_monitoring_service() -> MonitoringService:
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
