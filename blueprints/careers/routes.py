# File: blueprints/careers/routes.py
from flask import Blueprint, render_template, jsonify, request
from utils.analytics_util import record_page_view
from models import Job

# Import blueprint from __init__.py
from . import bp

@bp.get("/health")
def health():
    return jsonify(status="ok", section="careers")

@bp.get("/")
def index():
    record_page_view("careers")
    # Get featured jobs (active jobs, limited to 6)
    featured_jobs = Job.query.filter_by(is_active=True).limit(6).all()
    
    # Get recent grad opportunities (1-3 years experience)
    recent_grad_jobs = Job.query.filter(
        Job.is_active == True,
        Job.years_experience_required.in_(['1-3', '0-1'])
    ).limit(6).all()
    
    return render_template(
        "careers/index.html", 
        featured_jobs=featured_jobs, 
        recent_grad_jobs=recent_grad_jobs or [],
        employers=[]
    )

@bp.get("/jobs")
def jobs():
    record_page_view("careers_jobs")
    
    # Get filter parameters
    experience_filter = request.args.get('experience', 'all')
    
    # Base query
    query = Job.query.filter_by(is_active=True)
    
    # Apply experience filter
    if experience_filter == 'recent-grad':
        query = query.filter(Job.years_experience_required.in_(['0-1', '1-3']))
    elif experience_filter == 'mid-level':
        query = query.filter(Job.years_experience_required.in_(['3-5', '5-10']))
    elif experience_filter == 'senior':
        query = query.filter(Job.years_experience_required == '10+')
    
    all_jobs = query.order_by(Job.posted_at.desc()).all()
    return render_template("careers/jobs.html", jobs=all_jobs, experience_filter=experience_filter)

@bp.get("/upgrade-board")
def upgrade_board():
    """Job Upgrade Board - Higher paying jobs for recent graduates"""
    record_page_view("careers_upgrade_board")
    
    # Jobs requiring 1-3 years experience with higher salaries
    upgrade_jobs = Job.query.filter(
        Job.is_active == True,
        Job.years_experience_required.in_(['1-3', '3-5']),
        Job.salary_min >= 50000  # $50K+ for upgrade positions
    ).order_by(Job.salary_max.desc()).all()
    
    return render_template("careers/upgrade_board.html", jobs=upgrade_jobs)
