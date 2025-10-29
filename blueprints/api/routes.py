# File: blueprints/api/routes.py
from flask import Blueprint, jsonify, request
from utils.analytics_util import track_page_view

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.get("/health")
def health():
    return jsonify(status="ok", version="v1")

@bp.get("/v1/ping")
def ping():
    track_page_view("api_ping")
    return jsonify(ping="pong", ip=request.headers.get("X-Forwarded-For") or request.remote_addr)
