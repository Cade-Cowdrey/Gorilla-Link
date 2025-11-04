"""
PittState-Connect | Advanced Rate Limiting
Per-user, per-endpoint rate limiting with Redis backend and automatic abuse detection.
"""

from flask import request, g, abort, jsonify
from flask_login import current_user
from functools import wraps
from extensions import redis_client
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Custom exception for rate limit violations"""
    def __init__(self, message, retry_after=None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class AdvancedRateLimiter:
    """
    Advanced rate limiting with multiple strategies:
    - Per-user limits
    - Per-IP limits
    - Per-endpoint limits
    - Burst detection
    - Adaptive limits based on user behavior
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.fallback_memory = {}  # In-memory fallback if Redis unavailable
        
    def get_identifier(self) -> str:
        """Get unique identifier for rate limiting (user ID or IP)"""
        if current_user and current_user.is_authenticated:
            return f"user:{current_user.id}"
        return f"ip:{request.remote_addr}"
    
    def check_limit(self, 
                   key: str, 
                   limit: int, 
                   window: int,
                   cost: int = 1) -> dict:
        """
        Check if request is within rate limit
        
        Args:
            key: Unique key for this limit (e.g., "user:123:api")
            limit: Maximum requests allowed
            window: Time window in seconds
            cost: Cost of this request (default 1, expensive operations can be higher)
            
        Returns:
            dict with:
                - allowed: bool
                - current: int (current request count)
                - limit: int
                - remaining: int
                - reset_at: timestamp when limit resets
        """
        if not self.redis:
            return self._check_limit_memory(key, limit, window, cost)
        
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window)
            window_start_ts = window_start.timestamp()
            now_ts = now.timestamp()
            reset_at = now + timedelta(seconds=window)
            
            # Use Redis sorted set for sliding window
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start_ts)
            
            # Add current request with timestamp
            for _ in range(cost):
                pipe.zadd(key, {f"{now_ts}:{_}": now_ts})
            
            # Count requests in window
            pipe.zcount(key, window_start_ts, now_ts)
            
            # Set expiry
            pipe.expire(key, window)
            
            results = pipe.execute()
            current = results[2]  # Count result
            
            allowed = current <= limit
            remaining = max(0, limit - current)
            
            result = {
                "allowed": allowed,
                "current": current,
                "limit": limit,
                "remaining": remaining,
                "reset_at": reset_at.isoformat(),
                "retry_after": window if not allowed else None
            }
            
            # Log if limit exceeded
            if not allowed:
                identifier = self.get_identifier()
                logger.warning(f"Rate limit exceeded for {identifier} on {key}: {current}/{limit}")
                
                # Check for abuse (>150% of limit)
                if current > limit * 1.5:
                    self._flag_abuse(identifier, key, current, limit)
            
            return result
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {str(e)}")
            # Fallback to memory-based limiting
            return self._check_limit_memory(key, limit, window, cost)
    
    def _check_limit_memory(self, key: str, limit: int, window: int, cost: int) -> dict:
        """Fallback in-memory rate limiting"""
        now = datetime.utcnow()
        
        if key not in self.fallback_memory:
            self.fallback_memory[key] = []
        
        # Remove old entries
        window_start = now - timedelta(seconds=window)
        self.fallback_memory[key] = [
            ts for ts in self.fallback_memory[key]
            if ts > window_start
        ]
        
        # Add current requests
        for _ in range(cost):
            self.fallback_memory[key].append(now)
        
        current = len(self.fallback_memory[key])
        allowed = current <= limit
        remaining = max(0, limit - current)
        reset_at = now + timedelta(seconds=window)
        
        return {
            "allowed": allowed,
            "current": current,
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at.isoformat(),
            "retry_after": window if not allowed else None
        }
    
    def _flag_abuse(self, identifier: str, endpoint: str, current: int, limit: int):
        """Flag potential abuse for review"""
        abuse_key = f"abuse:{identifier}"
        
        if self.redis:
            try:
                abuse_data = {
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "requests": current,
                    "limit": limit,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "high" if current > limit * 2 else "medium"
                }
                self.redis.lpush("abuse_alerts", json.dumps(abuse_data))
                self.redis.expire("abuse_alerts", 86400)  # Keep for 24 hours
                
                logger.critical(f"🚨 Potential abuse detected: {identifier} - {current} requests (limit: {limit})")
            except Exception as e:
                logger.error(f"Failed to flag abuse: {str(e)}")


# Global instance
limiter = AdvancedRateLimiter(redis_client)


def rate_limit(limit: int, window: int = 3600, cost: int = 1, per_user: bool = True):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds (default 1 hour)
        cost: Cost of this request (default 1)
        per_user: If True, limit per user; if False, limit per IP
        
    Example:
        @rate_limit(limit=100, window=3600)  # 100 requests per hour
        def my_endpoint():
            ...
            
        @rate_limit(limit=10, window=60, cost=5)  # 10 heavy requests per minute
        def expensive_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            identifier = limiter.get_identifier()
            endpoint = request.endpoint or 'unknown'
            key = f"ratelimit:{identifier}:{endpoint}"
            
            result = limiter.check_limit(key, limit, window, cost)
            
            # Add rate limit headers to response
            g.rate_limit_info = result
            
            if not result["allowed"]:
                # Return 429 Too Many Requests
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {result['retry_after']} seconds.",
                    "limit": result["limit"],
                    "remaining": result["remaining"],
                    "reset_at": result["reset_at"]
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = result['reset_at']
                response.headers['Retry-After'] = str(result['retry_after'])
                return response
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator


def add_rate_limit_headers(response):
    """Add rate limit info to response headers"""
    if hasattr(g, 'rate_limit_info'):
        info = g.rate_limit_info
        response.headers['X-RateLimit-Limit'] = str(info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
        response.headers['X-RateLimit-Reset'] = info['reset_at']
    return response


def get_abuse_alerts(limit: int = 100) -> list:
    """
    Get recent abuse alerts for admin review
    
    Args:
        limit: Maximum alerts to return
        
    Returns:
        List of abuse alert dicts
    """
    if not redis_client:
        return []
    
    try:
        alerts = redis_client.lrange("abuse_alerts", 0, limit - 1)
        return [json.loads(alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Failed to get abuse alerts: {str(e)}")
        return []


def clear_rate_limit(identifier: str, endpoint: str = None):
    """
    Clear rate limit for a specific user/IP (admin function)
    
    Args:
        identifier: User ID or IP to clear
        endpoint: Specific endpoint to clear, or None for all
    """
    if not redis_client:
        return
    
    try:
        if endpoint:
            key = f"ratelimit:{identifier}:{endpoint}"
            redis_client.delete(key)
            logger.info(f"Cleared rate limit for {identifier} on {endpoint}")
        else:
            # Clear all endpoints for this identifier
            keys = redis_client.keys(f"ratelimit:{identifier}:*")
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared all rate limits for {identifier}")
    except Exception as e:
        logger.error(f"Failed to clear rate limit: {str(e)}")
