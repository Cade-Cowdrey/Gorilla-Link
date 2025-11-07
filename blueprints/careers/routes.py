# File: blueprints/careers/routes.py
from flask import Blueprint, render_template, jsonify, request
from utils.analytics_util import record_page_view
from models import Job
import logging

logger = logging.getLogger(__name__)

# Import blueprint from __init__.py
from . import bp

@bp.get("/health")
def health():
    return jsonify(status="ok", section="careers")

@bp.get("/")
def index():
    record_page_view("careers")
    
    try:
        # Get featured jobs (active jobs, limited to 6)
        featured_jobs = Job.query.filter_by(is_active=True).limit(6).all()
        
        # Get recent grad opportunities (1-3 years experience)
        recent_grad_jobs = Job.query.filter(
            Job.is_active == True,
            Job.years_experience_required.in_(['1-3', '0-1'])
        ).limit(6).all()
    except Exception as e:
        logger.error(f"Error querying jobs: {e}")
        # Return empty lists if database isn't available
        featured_jobs = []
        recent_grad_jobs = []
    
    return render_template(
        "careers/index.html", 
        featured_jobs=featured_jobs, 
        recent_grad_jobs=recent_grad_jobs or [],
        employers=[]
    )

@bp.get("/jobs")
def jobs():
    record_page_view("careers_jobs")
    
    try:
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
    except Exception as e:
        logger.error(f"Error loading jobs list: {e}")
        all_jobs = []
        experience_filter = 'all'
    
    return render_template("careers/jobs.html", jobs=all_jobs, experience_filter=experience_filter)

@bp.get("/upgrade-board")
def upgrade_board():
    """Job Upgrade Board - Higher paying jobs for recent graduates"""
    record_page_view("careers_upgrade_board")
    
    try:
        # Jobs requiring 1-3 years experience with higher salaries
        upgrade_jobs = Job.query.filter(
            Job.is_active == True,
            Job.years_experience_required.in_(['1-3', '3-5']),
            Job.salary_min >= 50000  # $50K+ for upgrade positions
        ).order_by(Job.salary_max.desc()).all()
    except Exception as e:
        logger.error(f"Error loading upgrade board: {e}")
        upgrade_jobs = []
    
    return render_template("careers/upgrade_board.html", jobs=upgrade_jobs)
