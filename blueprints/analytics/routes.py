# File: blueprints/analytics/routes.py
from __future__ import annotations

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from utils.analytics_util import record_page_view, get_page_stats, get_top_pages, get_timeseries

# Analytics blueprint using a standard bp variable and _bp suffix name
bp = Blueprint("analytics_bp", __name__, url_prefix="/analytics")

@bp.get("/health")
def health():
    """Health endpoint for monitoring."""
    return jsonify(status="ok", section="analytics")

@bp.get("/")
@login_required
def index():
    """Render the analytics dashboard page and record a page view."""
    record_page_view("analytics_dashboard", current_user.id if current_user.is_authenticated else None)
    return render_template(
        "analytics/index.html",
        title="Analytics | PittState-Connect",
        user=current_user,
    )

# --- JSON APIs feeding the dashboard ----
@bp.get("/api/summary")
@login_required
def api_summary():
    """Return summary statistics for the analytics dashboard."""
    record_page_view("analytics_api_summary", current_user.id if current_user.is_authenticated else None)
    stats = get_page_stats()
    return jsonify(stats)

@bp.get("/api/top-pages")
@login_required
def api_top_pages():
    """Return top pages viewed over a period (default limit=10)."""
    record_page_view("analytics_api_top_pages", current_user.id if current_user.is_authenticated else None)
    limit = int(request.args.get("limit", 10))
    data = get_top_pages(limit=limit)
    return jsonify({"limit": limit, "items": data})

@bp.get("/api/timeseries")
@login_required
def api_timeseries():
    """Return a time series of page views for the past N days (default 30 days)."""
    record_page_view("analytics_api_timeseries", current_user.id if current_user.is_authenticated else None)
    days = int(request.args.get("days", 30))
    data = get_timeseries(days=days)
    return jsonify({"days": days, "series": data})

@bp.get("/export")
@login_required
def export_data():
    """Export analytics data in CSV, JSON, or PDF format"""
    import csv
    import io
    from flask import make_response
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department = request.args.get('department', '')
    role = request.args.get('role', '')
    format_type = request.args.get('format', 'csv')
    
    # Get data (use existing functions)
    stats = get_page_stats()
    top_pages = get_top_pages(limit=50)
    
    if format_type == 'csv':
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Analytics Export'])
        writer.writerow(['Date Range', f"{date_from} to {date_to}"])
        writer.writerow([])
        
        # Summary
        writer.writerow(['Summary Statistics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Page Views (7d)', stats.get('page_views_7d', 0)])
        writer.writerow(['Unique Users (7d)', stats.get('unique_users_7d', 0)])
        writer.writerow(['Avg per Day (30d)', stats.get('avg_per_day_30d', 0)])
        writer.writerow([])
        
        # Top pages
        writer.writerow(['Top Pages'])
        writer.writerow(['Rank', 'Page', 'Views'])
        for i, page in enumerate(top_pages, 1):
            writer.writerow([i, page.get('page', ''), page.get('views', 0)])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_{date_from}_to_{date_to}.csv'
        return response
        
    elif format_type == 'json':
        # JSON export
        data = {
            'date_range': {'from': date_from, 'to': date_to},
            'filters': {'department': department, 'role': role},
            'summary': stats,
            'top_pages': top_pages
        }
        response = make_response(jsonify(data))
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_{date_from}_to_{date_to}.json'
        return response
        
    elif format_type == 'pdf':
        # PDF export (requires reportlab)
        response = make_response("PDF export feature coming soon. Use CSV or JSON for now.")
        response.headers['Content-Type'] = 'text/plain'
        return response
    
    return jsonify({'error': 'Invalid format'}), 400

