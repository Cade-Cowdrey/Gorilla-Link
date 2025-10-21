import json
import logging
import uuid
from datetime import datetime
from functools import wraps
from typing import Callable

from flask import g, request, current_app, render_template


def init_template_filters(app):
    @app.template_filter("currency")
    def currency(v):
        try:
            return "${:,.0f}".format(float(v or 0))
        except Exception:
            return "$0"

    @app.template_filter("dt")
    def dt(v, fmt="%b %d, %Y"):
        if hasattr(v, "strftime"):
            return v.strftime(fmt)
        return v


def init_error_pages(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500


def init_request_id_and_security_headers(app):
    @app.before_request
    def add_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def add_headers(resp):
        # Request tracing
        resp.headers["X-Request-ID"] = getattr(g, "request_id", "")

        # Security headers (compatible with Tailwind + inline styles for keyframes)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("X-XSS-Protection", "0")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # CSP is app-specific. Keep relaxed enough for current templates; tighten later if desired.
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; font-src 'self' https: data:;"
        )
        return resp


class RequestIDJsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = getattr(g, "request_id", None)
        if rid:
            base["request_id"] = rid
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base)


def init_logging(app):
    app.logger.setLevel(app.config["LOG_LEVEL"])
    # Replace default handler with JSON console
    app.logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(RequestIDJsonFormatter())
    app.logger.addHandler(handler)
    app.logger.propagate = False


def init_all(app):
    init_template_filters(app)
    init_error_pages(app)
    init_request_id_and_security_headers(app)
    init_logging(app)
