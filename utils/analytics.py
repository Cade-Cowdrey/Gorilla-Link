# utils/analytics.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List
from flask import current_app

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

class AnalyticsService:
    """
    A very lightweight analytics aggregator that stores daily counters in Redis.
    Keys:
      psu:analytics:visits:YYYY-MM-DD -> int
    """

    def __init__(self, app=None):
        self._app = app
        self._redis = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        url = app.config.get("CACHE_REDIS_URL") or app.config.get("SESSION_REDIS")
        if isinstance(url, str) and redis:
            self._redis = redis.from_url(url)
            app.logger.info("✅ AnalyticsService hooked to Redis.")
        else:
            self._redis = None
            app.logger.warning("AnalyticsService using in-memory fallback (no Redis).")
        app.extensions["analytics_service"] = self

    # ------------- public API -------------

    def bump_visit(self) -> None:
        """Increment today's visit counter; safe no-op if no redis."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if not self._redis:
            return
        self._redis.incr(self._key(today))

    def get_summary(self) -> Dict:
        last7 = self.get_timeseries(7)
        total7 = sum(x["visits"] for x in last7)
        return {
            "last_7d_total": total7,
            "avg_per_day": round(total7 / 7, 2),
            "latest": last7[-1] if last7 else {"day": None, "visits": 0},
        }

    def get_timeseries(self, days: int = 7) -> List[Dict]:
        out = []
        for i in range(days, 0, -1):
            day = (datetime.utcnow() - timedelta(days=i-1)).strftime("%Y-%m-%d")
            visits = self._read(day)
            out.append({"day": day, "visits": visits})
        return out

    # ------------- helpers -------------

    def _key(self, day: str) -> str:
        return f"psu:analytics:visits:{day}"

    def _read(self, day: str) -> int:
        if not self._redis:
            return 0
        val = self._redis.get(self._key(day))
        try:
            return int(val or 0)
        except Exception:
            return 0
