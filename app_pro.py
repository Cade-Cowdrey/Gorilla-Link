# app_pro.py
# ─────────────────────────────────────────────────────────────────────────────
# Production Flask entrypoint for PittState-Connect
# - Registers all blueprints (incl. careers_bp)
# - Adds safe_url() to prevent Jinja BuildError from breaking pages
# - Sets up CORS, LoginManager, SocketIO, Cache, Mail
# - Robust error handlers that never loop on 500s
# - Basic security headers + health/check endpoints
# - PSU-friendly logging format
# ─────────────────────────────────────────────────────────────────────────────

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, g, jsonify, url_for
from werkzeug.exceptions import NotFound, HTTPException, InternalServerError, BadRequest, Forbidden
from werkzeug.routing import BuildError

# Use your existing extensions module (already present in your repo)
# It should define
