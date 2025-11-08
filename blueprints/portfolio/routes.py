# File: blueprints/portfolio/routes.py
from flask import Blueprint, render_template_string, jsonify, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from extensions import db
from models_portfolio import Portfolio, PortfolioExperience, PortfolioProject, PortfolioAward, PortfolioSkill
from models import User
from datetime import datetime
from sqlalchemy import desc
import json
import os
from werkzeug.utils import secure_filename
import pdfkit
from io import BytesIO

bp = Blueprint("portfolio", __name__, url_prefix="/portfolio")

# Configuration
UPLOAD_FOLDER = 'static/uploads/portfolios'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ======================================================
# TEMPLATES
# ======================================================

PORTFOLIO_INDEX_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Professional Portfolios | PittState-Connect{% endblock %}
{% block content %}
<div class="container py-5">
    <div class="text-center mb-5">
        <h1 class="display-4 fw-bold">Student Portfolios</h1>
        <p class="lead text-muted">Showcase your professional journey with a stunning portfolio</p>
        {% if current_user.is_authenticated %}
        <a href="{{ url_for('portfolio.create_form') }}" class="btn btn-primary btn-lg mt-3">
            <i class="bi bi-plus-circle"></i> Create Your Portfolio
        </a>
        {% endif %}
    </div>
    
    <div class="row g-4">
        {% for p in portfolios %}
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 shadow-sm hover-shadow">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        {% if p.profile_image %}
                        <img src="{{ p.profile_image }}" class="rounded-circle me-3" width="60" height="60" alt="Profile">
                        {% else %}
                        <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                            <span class="fs-4 fw-bold">{{ p.slug[0]|upper }}</span>
                        </div>
                        {% endif %}
                        <div>
                            <h5 class="card-title mb-0">{{ p.slug.replace('-', ' ')|title }}</h5>
                            {% if p.headline %}
                            <small class="text-muted">{{ p.headline[:50] }}...</small>
                            {% endif %}
                        </div>
                    </div>
                    {% if p.about %}
                    <p class="card-text text-muted small">{{ p.about[:120] }}...</p>
                    {% endif %}
                    <div class="d-flex justify-content-between align-items-center">
                        <a href="{{ url_for('portfolio.view', slug=p.slug) }}" class="btn btn-sm btn-outline-primary">
                            View Portfolio <i class="bi bi-arrow-right"></i>
                        </a>
                        <small class="text-muted"><i class="bi bi-eye"></i> {{ p.views }}</small>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<style>
.hover-shadow {
    transition: box-shadow 0.3s ease;
}
.hover-shadow:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}
</style>
{% endblock %}
"""

PORTFOLIO_CREATE_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Create Portfolio | PittState-Connect{% endblock %}
{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="mb-4">Create Your Professional Portfolio</h1>
            <p class="lead text-muted mb-4">Build a stunning portfolio to showcase your work and achievements</p>
            
            <form method="POST" action="{{ url_for('portfolio.create') }}" class="needs-validation">
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-person-circle"></i> Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="headline" class="form-label">Professional Headline</label>
                            <input type="text" class="form-control" id="headline" name="headline" 
                                   placeholder="e.g., Turning Strategy into Impact through Leadership">
                            <small class="text-muted">A catchy tagline that describes you</small>
                        </div>
                        
                        <div class="mb-3">
                            <label for="about" class="form-label">About Me</label>
                            <textarea class="form-control" id="about" name="about" rows="5"
                                      placeholder="Tell your story..."></textarea>
                        </div>
                    </div>
                </div>
                
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-link-45deg"></i> Contact & Social</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="phone" class="form-label">Phone</label>
                            <input type="tel" class="form-control" id="phone" name="phone" placeholder="(123) 456-7890">
                        </div>
                        
                        <div class="mb-3">
                            <label for="linkedin_url" class="form-label">LinkedIn</label>
                            <input type="url" class="form-control" id="linkedin_url" name="linkedin_url" 
                                   placeholder="https://linkedin.com/in/yourname">
                        </div>
                        
                        <div class="mb-3">
                            <label for="github_url" class="form-label">GitHub</label>
                            <input type="url" class="form-control" id="github_url" name="github_url" 
                                   placeholder="https://github.com/yourname">
                        </div>
                        
                        <div class="mb-3">
                            <label for="twitter_url" class="form-label">Twitter/X</label>
                            <input type="url" class="form-control" id="twitter_url" name="twitter_url" 
                                   placeholder="https://x.com/yourhandle">
                        </div>
                    </div>
                </div>
                
                <div class="card shadow-sm mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-gear"></i> Settings</h5>
                    </div>
                    <div class="card-body">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="is_public" name="is_public" value="true" checked>
                            <label class="form-check-label" for="is_public">
                                Make portfolio public
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="bi bi-check-circle"></i> Create Portfolio
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""

PORTFOLIO_EDIT_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Edit Portfolio | PittState-Connect{% endblock %}
{% block content %}
<div class="container py-5">
    <div class="row">
        <div class="col-lg-3">
            <!-- Sidebar Navigation -->
            <div class="card shadow-sm mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="bi bi-gear"></i> Portfolio Manager</h5>
                </div>
                <div class="list-group list-group-flush">
                    <a href="#basic-info" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-person"></i> Basic Info
                    </a>
                    <a href="#experiences" class="list-group-item list-group-item-action active" data-bs-toggle="tab">
                        <i class="bi bi-briefcase"></i> Experiences
                    </a>
                    <a href="#projects" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-folder"></i> Projects
                    </a>
                    <a href="#awards" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-trophy"></i> Awards
                    </a>
                    <a href="#skills" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-star"></i> Skills
                    </a>
                    <a href="#media" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-image"></i> Media
                    </a>
                    <a href="#theme" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-palette"></i> Theme
                    </a>
                    <a href="#analytics" class="list-group-item list-group-item-action" data-bs-toggle="tab">
                        <i class="bi bi-graph-up"></i> Analytics
                    </a>
                </div>
            </div>
            
            <div class="card shadow-sm">
                <div class="card-body text-center">
                    <a href="{{ url_for('portfolio.view', slug=portfolio.slug) }}" class="btn btn-success w-100 mb-2" target="_blank">
                        <i class="bi bi-eye"></i> View Portfolio
                    </a>
                    <a href="{{ url_for('portfolio.export_pdf', slug=portfolio.slug) }}" class="btn btn-outline-primary w-100">
                        <i class="bi bi-download"></i> Download PDF
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-lg-9">
            <div class="tab-content">
                <!-- Basic Info Tab -->
                <div class="tab-pane fade" id="basic-info">
                    <div class="card shadow-sm">
                        <div class="card-header">
                            <h4><i class="bi bi-person-circle"></i> Basic Information</h4>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="{{ url_for('portfolio.update_basic') }}" class="needs-validation">
                                <div class="mb-3">
                                    <label class="form-label">Portfolio URL</label>
                                    <div class="input-group">
                                        <span class="input-group-text">{{ request.host_url }}portfolio/</span>
                                        <input type="text" class="form-control" value="{{ portfolio.slug }}" readonly>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="headline" class="form-label">Professional Headline</label>
                                    <input type="text" class="form-control" id="headline" name="headline" 
                                           value="{{ portfolio.headline or '' }}" 
                                           placeholder="e.g., Turning Strategy into Impact through Leadership">
                                </div>
                                
                                <div class="mb-3">
                                    <label for="about" class="form-label">About Me</label>
                                    <textarea class="form-control" id="about" name="about" rows="6">{{ portfolio.about or '' }}</textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label for="phone" class="form-label">Phone</label>
                                        <input type="tel" class="form-control" id="phone" name="phone" value="{{ portfolio.phone or '' }}">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label for="website_url" class="form-label">Website</label>
                                        <input type="url" class="form-control" id="website_url" name="website_url" value="{{ portfolio.website_url or '' }}">
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="linkedin_url" class="form-label">LinkedIn URL</label>
                                    <input type="url" class="form-control" id="linkedin_url" name="linkedin_url" value="{{ portfolio.linkedin_url or '' }}">
                                </div>
                                
                                <div class="mb-3">
                                    <label for="github_url" class="form-label">GitHub URL</label>
                                    <input type="url" class="form-control" id="github_url" name="github_url" value="{{ portfolio.github_url or '' }}">
                                </div>
                                
                                <div class="mb-3">
                                    <label for="twitter_url" class="form-label">Twitter/X URL</label>
                                    <input type="url" class="form-control" id="twitter_url" name="twitter_url" value="{{ portfolio.twitter_url or '' }}">
                                </div>
                                
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="is_public" name="is_public" value="true" {% if portfolio.is_public %}checked{% endif %}>
                                    <label class="form-check-label" for="is_public">Make portfolio public</label>
                                </div>
                                
                                <button type="submit" class="btn btn-primary">
                                    <i class="bi bi-save"></i> Save Changes
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <!-- Experiences Tab -->
                <div class="tab-pane fade show active" id="experiences">
                    <div class="card shadow-sm">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h4><i class="bi bi-briefcase"></i> Work Experience</h4>
                            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addExperienceModal">
                                <i class="bi bi-plus-circle"></i> Add Experience
                            </button>
                        </div>
                        <div class="card-body">
                            {% if portfolio.experiences %}
                            <div class="list-group">
                                {% for exp in portfolio.experiences %}
                                <div class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h5 class="mb-1">{{ exp.title }}</h5>
                                            <p class="mb-1 text-primary">{{ exp.company }}</p>
                                            <small class="text-muted">
                                                {{ exp.start_date.strftime('%b %Y') }} - {% if exp.end_date %}{{ exp.end_date.strftime('%b %Y') }}{% else %}Present{% endif %}
                                                {% if exp.location %}| {{ exp.location }}{% endif %}
                                            </small>
                                        </div>
                                        <div class="btn-group">
                                            <button class="btn btn-sm btn-outline-primary" onclick="editExperience({{ exp.id }})">
                                                <i class="bi bi-pencil"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteExperience({{ exp.id }})">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </div>
                                    </div>
                                    {% if exp.description %}
                                    <p class="mt-2 mb-0">{{ exp.description }}</p>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <p class="text-muted text-center py-4">No experiences added yet. Click "Add Experience" to get started!</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- Projects Tab -->
                <div class="tab-pane fade" id="projects">
                    <div class="card shadow-sm">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h4><i class="bi bi-folder"></i> Projects</h4>
                            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addProjectModal">
                                <i class="bi bi-plus-circle"></i> Add Project
                            </button>
                        </div>
                        <div class="card-body">
                            {% if portfolio.projects %}
                            <div class="row">
                                {% for project in portfolio.projects %}
                                <div class="col-md-6 mb-3">
                                    <div class="card h-100">
                                        {% if project.image_url %}
                                        <img src="{{ project.image_url }}" class="card-img-top" alt="{{ project.title }}">
                                        {% endif %}
                                        <div class="card-body">
                                            <h5 class="card-title">{{ project.title }}</h5>
                                            {% if project.subtitle %}
                                            <p class="card-subtitle text-muted mb-2">{{ project.subtitle }}</p>
                                            {% endif %}
                                            {% if project.description %}
                                            <p class="card-text small">{{ project.description[:100] }}...</p>
                                            {% endif %}
                                        </div>
                                        <div class="card-footer bg-transparent">
                                            <button class="btn btn-sm btn-outline-primary" onclick="editProject({{ project.id }})">
                                                <i class="bi bi-pencil"></i> Edit
                                            </button>
                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteProject({{ project.id }})">
                                                <i class="bi bi-trash"></i> Delete
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <p class="text-muted text-center py-4">No projects added yet. Click "Add Project" to showcase your work!</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- Awards Tab -->
                <div class="tab-pane fade" id="awards">
                    <div class="card shadow-sm">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h4><i class="bi bi-trophy"></i> Awards & Honors</h4>
                            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addAwardModal">
                                <i class="bi bi-plus-circle"></i> Add Award
                            </button>
                        </div>
                        <div class="card-body">
                            {% if portfolio.awards %}
                            <div class="list-group">
                                {% for award in portfolio.awards %}
                                <div class="list-group-item d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 class="mb-1">{{ award.title }}</h6>
                                        {% if award.issuer %}<p class="mb-1 text-muted small">{{ award.issuer }}</p>{% endif %}
                                        {% if award.date %}<small class="text-muted">{{ award.date.strftime('%B %Y') }}</small>{% endif %}
                                    </div>
                                    <div class="btn-group">
                                        <button class="btn btn-sm btn-outline-primary" onclick="editAward({{ award.id }})">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" onclick="deleteAward({{ award.id }})">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <p class="text-muted text-center py-4">No awards added yet. Add your achievements!</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- Skills Tab -->
                <div class="tab-pane fade" id="skills">
                    <div class="card shadow-sm">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h4><i class="bi bi-star"></i> Skills</h4>
                            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addSkillModal">
                                <i class="bi bi-plus-circle"></i> Add Skill
                            </button>
                        </div>
                        <div class="card-body">
                            {% if portfolio.skills %}
                            {% set skills_by_category = {} %}
                            {% for skill in portfolio.skills %}
                                {% set category = skill.category or 'Other' %}
                                {% if category not in skills_by_category %}
                                    {% set _ = skills_by_category.update({category: []}) %}
                                {% endif %}
                                {% set _ = skills_by_category[category].append(skill) %}
                            {% endfor %}
                            
                            {% for category, skills in skills_by_category.items() %}
                            <div class="mb-4">
                                <h6 class="text-primary mb-3">{{ category }}</h6>
                                <div class="row g-2">
                                    {% for skill in skills %}
                                    <div class="col-md-4">
                                        <div class="d-flex justify-content-between align-items-center border rounded p-2">
                                            <div>
                                                <span class="fw-bold">{{ skill.name }}</span>
                                                {% if skill.proficiency %}
                                                <div class="progress mt-1" style="height: 5px;">
                                                    <div class="progress-bar" style="width: {{ skill.proficiency * 20 }}%"></div>
                                                </div>
                                                {% endif %}
                                            </div>
                                            <div class="btn-group btn-group-sm">
                                                <button class="btn btn-outline-danger" onclick="deleteSkill({{ skill.id }})">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                    {% endfor %}
                                </div>
                            </div>
                            {% endfor %}
                            {% else %}
                            <p class="text-muted text-center py-4">No skills added yet. Add your skills to showcase your expertise!</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <!-- Media Tab -->
                <div class="tab-pane fade" id="media">
                    <div class="card shadow-sm mb-4">
                        <div class="card-header">
                            <h5><i class="bi bi-image"></i> Profile Image</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="{{ url_for('portfolio.upload_profile_image') }}" enctype="multipart/form-data">
                                <div class="mb-3">
                                    {% if portfolio.profile_image %}
                                    <img src="{{ portfolio.profile_image }}" class="img-thumbnail mb-3" style="max-width: 200px;">
                                    {% endif %}
                                    <input type="file" class="form-control" name="profile_image" accept="image/*" required>
                                    <small class="text-muted">Recommended: Square image, at least 400x400px</small>
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    <i class="bi bi-upload"></i> Upload Image
                                </button>
                            </form>
                        </div>
                    </div>
                    
                    <div class="card shadow-sm">
                        <div class="card-header">
                            <h5><i class="bi bi-file-pdf"></i> Resume</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="{{ url_for('portfolio.upload_resume') }}" enctype="multipart/form-data">
                                <div class="mb-3">
                                    {% if portfolio.resume_url %}
                                    <a href="{{ portfolio.resume_url }}" class="btn btn-sm btn-outline-primary mb-3" target="_blank">
                                        <i class="bi bi-file-pdf"></i> View Current Resume
                                    </a>
                                    {% endif %}
                                    <input type="file" class="form-control" name="resume" accept=".pdf" required>
                                    <small class="text-muted">PDF format only</small>
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    <i class="bi bi-upload"></i> Upload Resume
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <!-- Theme Tab -->
                <div class="tab-pane fade" id="theme">
                    <div class="card shadow-sm">
                        <div class="card-header">
                            <h4><i class="bi bi-palette"></i> Theme Customization</h4>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="{{ url_for('portfolio.update_theme') }}">
                                <div class="mb-4">
                                    <label class="form-label fw-bold">Choose Your Industry Theme</label>
                                    <p class="text-muted small">Select a professionally designed theme tailored to your field</p>
                                    <div class="row g-3">
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="psu-theme" value="psu" {% if not portfolio.theme or portfolio.theme == 'psu' %}checked{% endif %}>
                                            <label class="btn btn-outline-danger w-100 h-100" for="psu-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #BE1E2D 0%, #FFB81C 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>PSU Crimson & Gold</strong>
                                                    <small class="d-block text-muted">University Pride</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="modern-dark-theme" value="modern-dark" {% if portfolio.theme == 'modern-dark' %}checked{% endif %}>
                                            <label class="btn btn-outline-dark w-100 h-100" for="modern-dark-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #1a1f36 0%, #00d4ff 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Modern Dark</strong>
                                                    <small class="d-block text-muted">Tech & Design</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="healthcare-theme" value="healthcare" {% if portfolio.theme == 'healthcare' %}checked{% endif %}>
                                            <label class="btn btn-outline-info w-100 h-100" for="healthcare-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #0077c8 0%, #00a3e0 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Healthcare Blue</strong>
                                                    <small class="d-block text-muted">Medical & Nursing</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="business-theme" value="business" {% if portfolio.theme == 'business' %}checked{% endif %}>
                                            <label class="btn btn-outline-secondary w-100 h-100" for="business-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #1a1a2e 0%, #d4af37 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Executive Business</strong>
                                                    <small class="d-block text-muted">Corporate & Finance</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="construction-theme" value="construction" {% if portfolio.theme == 'construction' %}checked{% endif %}>
                                            <label class="btn btn-outline-warning w-100 h-100" for="construction-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #ff6b35 0%, #ffa500 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Construction Bold</strong>
                                                    <small class="d-block text-muted">Engineering & Trades</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="creative-theme" value="creative" {% if portfolio.theme == 'creative' %}checked{% endif %}>
                                            <label class="btn btn-outline-primary w-100 h-100" for="creative-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Creative Arts</strong>
                                                    <small class="d-block text-muted">Design & Media</small>
                                                </div>
                                            </label>
                                        </div>
                                        <div class="col-md-4">
                                            <input type="radio" class="btn-check" name="theme_preset" id="tech-theme" value="tech" {% if portfolio.theme == 'tech' %}checked{% endif %}>
                                            <label class="btn btn-outline-success w-100 h-100" for="tech-theme">
                                                <div class="py-3">
                                                    <div class="mb-2" style="background: linear-gradient(135deg, #0a192f 0%, #00ff88 100%); height: 50px; border-radius: 8px;"></div>
                                                    <strong>Technology</strong>
                                                    <small class="d-block text-muted">Software & IT</small>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="custom_css" class="form-label">Custom CSS <small class="text-muted">(Advanced)</small></label>
                                    <textarea class="form-control font-monospace" id="custom_css" name="custom_css" rows="8" placeholder="/* Add your custom CSS here */">{{ portfolio.custom_css or '' }}</textarea>
                                    <small class="text-muted">You can override theme styles with custom CSS</small>
                                </div>
                                
                                <button type="submit" class="btn btn-primary">
                                    <i class="bi bi-save"></i> Save Theme
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                
                <!-- Analytics Tab -->
                <div class="tab-pane fade" id="analytics">
                    <div class="card shadow-sm">
                        <div class="card-header">
                            <h4><i class="bi bi-graph-up"></i> Portfolio Analytics</h4>
                        </div>
                        <div class="card-body">
                            <div class="row g-4">
                                <div class="col-md-3">
                                    <div class="card bg-primary text-white">
                                        <div class="card-body text-center">
                                            <h2 class="display-4">{{ portfolio.views }}</h2>
                                            <p class="mb-0">Total Views</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-success text-white">
                                        <div class="card-body text-center">
                                            <h2 class="display-4">{{ portfolio.experiences|length }}</h2>
                                            <p class="mb-0">Experiences</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-info text-white">
                                        <div class="card-body text-center">
                                            <h2 class="display-4">{{ portfolio.projects|length }}</h2>
                                            <p class="mb-0">Projects</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-warning text-white">
                                        <div class="card-body text-center">
                                            <h2 class="display-4">{{ portfolio.awards|length }}</h2>
                                            <p class="mb-0">Awards</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <h5>Profile Completeness</h5>
                                {% set completeness = 0 %}
                                {% if portfolio.headline %}{% set completeness = completeness + 15 %}{% endif %}
                                {% if portfolio.about %}{% set completeness = completeness + 15 %}{% endif %}
                                {% if portfolio.profile_image %}{% set completeness = completeness + 10 %}{% endif %}
                                {% if portfolio.resume_url %}{% set completeness = completeness + 10 %}{% endif %}
                                {% if portfolio.experiences %}{% set completeness = completeness + 20 %}{% endif %}
                                {% if portfolio.projects %}{% set completeness = completeness + 15 %}{% endif %}
                                {% if portfolio.awards %}{% set completeness = completeness + 10 %}{% endif %}
                                {% if portfolio.skills %}{% set completeness = completeness + 5 %}{% endif %}
                                
                                <div class="progress" style="height: 30px;">
                                    <div class="progress-bar bg-success" style="width: {{ completeness }}%">
                                        {{ completeness }}%
                                    </div>
                                </div>
                                
                                <div class="mt-3">
                                    {% if completeness < 100 %}
                                    <p class="text-muted">Improve your portfolio:</p>
                                    <ul class="list-unstyled">
                                        {% if not portfolio.headline %}<li><i class="bi bi-circle text-warning"></i> Add a professional headline (15%)</li>{% endif %}
                                        {% if not portfolio.about %}<li><i class="bi bi-circle text-warning"></i> Write your about section (15%)</li>{% endif %}
                                        {% if not portfolio.profile_image %}<li><i class="bi bi-circle text-warning"></i> Upload a profile image (10%)</li>{% endif %}
                                        {% if not portfolio.resume_url %}<li><i class="bi bi-circle text-warning"></i> Upload your resume (10%)</li>{% endif %}
                                        {% if not portfolio.experiences %}<li><i class="bi bi-circle text-warning"></i> Add work experience (20%)</li>{% endif %}
                                        {% if not portfolio.projects %}<li><i class="bi bi-circle text-warning"></i> Showcase your projects (15%)</li>{% endif %}
                                        {% if not portfolio.awards %}<li><i class="bi bi-circle text-warning"></i> Add awards and honors (10%)</li>{% endif %}
                                        {% if not portfolio.skills %}<li><i class="bi bi-circle text-warning"></i> List your skills (5%)</li>{% endif %}
                                    </ul>
                                    {% else %}
                                    <p class="text-success"><i class="bi bi-check-circle-fill"></i> Your portfolio is complete! Great job!</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Add Experience Modal -->
<div class="modal fade" id="addExperienceModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Experience</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="{{ url_for('portfolio.add_experience') }}">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="exp_title" class="form-label">Job Title *</label>
                        <input type="text" class="form-control" id="exp_title" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label for="exp_company" class="form-label">Company *</label>
                        <input type="text" class="form-control" id="exp_company" name="company" required>
                    </div>
                    <div class="mb-3">
                        <label for="exp_location" class="form-label">Location</label>
                        <input type="text" class="form-control" id="exp_location" name="location" placeholder="e.g., Pittsburg, KS">
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="exp_start_date" class="form-label">Start Date *</label>
                            <input type="month" class="form-control" id="exp_start_date" name="start_date" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="exp_end_date" class="form-label">End Date</label>
                            <input type="month" class="form-control" id="exp_end_date" name="end_date">
                            <small class="text-muted">Leave blank if current position</small>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="exp_description" class="form-label">Description</label>
                        <textarea class="form-control" id="exp_description" name="description" rows="4"></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="exp_bullets" class="form-label">Key Achievements (one per line)</label>
                        <textarea class="form-control" id="exp_bullets" name="bullets" rows="4" placeholder="- Led team of 5 people&#10;- Increased sales by 25%&#10;- Implemented new process"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Experience</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Add Project Modal -->
<div class="modal fade" id="addProjectModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Project</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="{{ url_for('portfolio.add_project') }}" enctype="multipart/form-data">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="proj_title" class="form-label">Project Title *</label>
                        <input type="text" class="form-control" id="proj_title" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label for="proj_subtitle" class="form-label">Subtitle</label>
                        <input type="text" class="form-control" id="proj_subtitle" name="subtitle" placeholder="e.g., Strategic Marketing & Planning Analysis">
                    </div>
                    <div class="mb-3">
                        <label for="proj_description" class="form-label">Description</label>
                        <textarea class="form-control" id="proj_description" name="description" rows="4"></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="proj_date" class="form-label">Date/Period</label>
                        <input type="text" class="form-control" id="proj_date" name="date" placeholder="e.g., April 2025 or 2024-2025">
                    </div>
                    <div class="mb-3">
                        <label for="proj_impact" class="form-label">Impact/Results</label>
                        <textarea class="form-control" id="proj_impact" name="impact" rows="3" placeholder="Describe the impact or results of this project"></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="proj_url" class="form-label">Project URL</label>
                        <input type="url" class="form-control" id="proj_url" name="project_url" placeholder="https://...">
                    </div>
                    <div class="mb-3">
                        <label for="proj_github" class="form-label">GitHub URL</label>
                        <input type="url" class="form-control" id="proj_github" name="github_url" placeholder="https://github.com/...">
                    </div>
                    <div class="mb-3">
                        <label for="proj_tags" class="form-label">Tags (comma separated)</label>
                        <input type="text" class="form-control" id="proj_tags" name="tags" placeholder="Python, Web Development, Data Analysis">
                    </div>
                    <div class="mb-3">
                        <label for="proj_image" class="form-label">Project Image</label>
                        <input type="file" class="form-control" id="proj_image" name="image" accept="image/*">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Project</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Add Award Modal -->
<div class="modal fade" id="addAwardModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Award</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="{{ url_for('portfolio.add_award') }}">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="award_title" class="form-label">Award Title *</label>
                        <input type="text" class="form-control" id="award_title" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label for="award_issuer" class="form-label">Issuing Organization</label>
                        <input type="text" class="form-control" id="award_issuer" name="issuer" placeholder="e.g., Pittsburg State University">
                    </div>
                    <div class="mb-3">
                        <label for="award_description" class="form-label">Description</label>
                        <textarea class="form-control" id="award_description" name="description" rows="3"></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="award_date" class="form-label">Date</label>
                        <input type="month" class="form-control" id="award_date" name="date">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Award</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Add Skill Modal -->
<div class="modal fade" id="addSkillModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Skill</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="{{ url_for('portfolio.add_skill') }}">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="skill_name" class="form-label">Skill Name *</label>
                        <input type="text" class="form-control" id="skill_name" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label for="skill_category" class="form-label">Category</label>
                        <select class="form-select" id="skill_category" name="category">
                            <option value="Technical">Technical</option>
                            <option value="Leadership">Leadership</option>
                            <option value="Communication">Communication</option>
                            <option value="Marketing">Marketing</option>
                            <option value="Design">Design</option>
                            <option value="Data Analysis">Data Analysis</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="skill_proficiency" class="form-label">Proficiency Level</label>
                        <input type="range" class="form-range" id="skill_proficiency" name="proficiency" min="1" max="5" step="1" value="3" oninput="this.nextElementSibling.textContent = this.value">
                        <div class="text-center"><span>3</span>/5</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Skill</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function deleteExperience(id) {
    if (confirm('Are you sure you want to delete this experience?')) {
        fetch(`{{ url_for('portfolio.delete_experience', id=0) }}`.replace('0', id), { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
    }
}

function deleteProject(id) {
    if (confirm('Are you sure you want to delete this project?')) {
        fetch(`{{ url_for('portfolio.delete_project', id=0) }}`.replace('0', id), { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
    }
}

function deleteAward(id) {
    if (confirm('Are you sure you want to delete this award?')) {
        fetch(`{{ url_for('portfolio.delete_award', id=0) }}`.replace('0', id), { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
    }
}

function deleteSkill(id) {
    if (confirm('Are you sure you want to delete this skill?')) {
        fetch(`{{ url_for('portfolio.delete_skill', id=0) }}`.replace('0', id), { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
    }
}
</script>
{% endblock %}
"""

PORTFOLIO_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user.full_name }} | Professional Portfolio</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="{% if portfolio.headline %}{{ portfolio.headline }}{% else %}Professional portfolio of {{ user.full_name }}{% endif %}">
    <meta name="author" content="{{ user.full_name }}">
    <meta name="keywords" content="{{ user.full_name }}, portfolio, Pittsburg State University, {{ user.major if user.major }}">
    
    <!-- Open Graph Meta Tags for Social Sharing -->
    <meta property="og:title" content="{{ user.full_name }} | Professional Portfolio">
    <meta property="og:description" content="{% if portfolio.headline %}{{ portfolio.headline }}{% else %}Professional portfolio showcasing work and achievements{% endif %}">
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{{ request.url }}">
    {% if portfolio.profile_image %}
    <meta property="og:image" content="{{ request.host_url }}{{ portfolio.profile_image[1:] }}">
    {% endif %}
    <meta property="og:site_name" content="PittState-Connect">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ user.full_name }} | Professional Portfolio">
    <meta name="twitter:description" content="{% if portfolio.headline %}{{ portfolio.headline }}{% else %}Professional portfolio showcasing work and achievements{% endif %}">
    {% if portfolio.profile_image %}
    <meta name="twitter:image" content="{{ request.host_url }}{{ portfolio.profile_image[1:] }}">
    {% endif %}
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        {% if portfolio.theme == 'modern-dark' %}
        /* Modern Dark Theme - Inspired by contemporary portfolio design */
        :root {
            --primary-color: #1a1f36;
            --secondary-color: #0f1419;
            --accent-color: #00d4ff;
            --psu-crimson: #00d4ff;
            --psu-gold: #ffd700;
            --text-color: #e2e8f0;
            --light-bg: #1e2433;
            --card-bg: #242b3d;
        }
        body {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f36 100%);
            color: var(--text-color);
        }
        .card, .section {
            background: var(--card-bg);
            border: 1px solid rgba(0, 212, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        .hero-section {
            background: linear-gradient(135deg, #1a1f36 0%, #0f1419 100%);
        }
        
        {% elif portfolio.theme == 'healthcare' %}
        /* Healthcare/Medical Theme - Professional, clean, trustworthy */
        :root {
            --primary-color: #0077c8;
            --secondary-color: #004e8c;
            --accent-color: #00a3e0;
            --psu-crimson: #0077c8;
            --psu-gold: #00a3e0;
            --text-color: #2c3e50;
            --light-bg: #f0f8ff;
            --card-bg: #ffffff;
        }
        body {
            background: linear-gradient(to bottom, #f0f8ff 0%, #e6f4ff 100%);
        }
        .card {
            border-left: 4px solid var(--accent-color);
            box-shadow: 0 4px 16px rgba(0, 119, 200, 0.1);
        }
        .hero-section {
            background: linear-gradient(135deg, #0077c8 0%, #005a9c 100%);
        }
        
        {% elif portfolio.theme == 'business' %}
        /* Business/Corporate Theme - Executive, sophisticated */
        :root {
            --primary-color: #1a1a2e;
            --secondary-color: #16213e;
            --accent-color: #d4af37;
            --psu-crimson: #1a1a2e;
            --psu-gold: #d4af37;
            --text-color: #2d3436;
            --light-bg: #f8f9fa;
            --card-bg: #ffffff;
        }
        body {
            background: #f8f9fa;
        }
        .card {
            border-top: 3px solid var(--accent-color);
            box-shadow: 0 10px 30px rgba(26, 26, 46, 0.15);
        }
        .hero-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        }
        h2 {
            border-left: 5px solid var(--accent-color);
            padding-left: 1rem;
        }
        
        {% elif portfolio.theme == 'construction' %}
        /* Construction/Engineering Theme - Bold, industrial, strong */
        :root {
            --primary-color: #ff6b35;
            --secondary-color: #d84315;
            --accent-color: #ffa500;
            --psu-crimson: #ff6b35;
            --psu-gold: #ffa500;
            --text-color: #1a1a1a;
            --light-bg: #f5f5f0;
            --card-bg: #ffffff;
        }
        body {
            background: linear-gradient(to bottom, #f5f5f0 0%, #e8e8e0 100%);
        }
        .card {
            border: 2px solid #ddd;
            border-left: 6px solid var(--primary-color);
            box-shadow: 0 6px 20px rgba(255, 107, 53, 0.2);
        }
        .hero-section {
            background: linear-gradient(135deg, #ff6b35 0%, #d84315 100%);
        }
        h1, h2, h3 {
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        {% elif portfolio.theme == 'creative' %}
        /* Creative/Design Theme - Artistic, vibrant, expressive */
        :root {
            --primary-color: #6366f1;
            --secondary-color: #4f46e5;
            --accent-color: #ec4899;
            --psu-crimson: #6366f1;
            --psu-gold: #ec4899;
            --text-color: #1e293b;
            --light-bg: #faf5ff;
            --card-bg: #ffffff;
        }
        body {
            background: linear-gradient(135deg, #faf5ff 0%, #f0e7ff 100%);
        }
        .card {
            border-radius: 20px;
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
            border: 2px solid rgba(99, 102, 241, 0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.25);
        }
        .hero-section {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        }
        
        {% elif portfolio.theme == 'tech' %}
        /* Technology/Software Theme - Sleek, modern, innovative */
        :root {
            --primary-color: #00ff88;
            --secondary-color: #00cc6a;
            --accent-color: #00ffaa;
            --psu-crimson: #00ff88;
            --psu-gold: #00ffaa;
            --text-color: #0a0e27;
            --light-bg: #f0fff4;
            --card-bg: #ffffff;
        }
        body {
            background: linear-gradient(to bottom, #f0fff4 0%, #e6ffed 100%);
        }
        .card {
            border: 1px solid rgba(0, 255, 136, 0.2);
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.1);
            border-radius: 12px;
        }
        .hero-section {
            background: linear-gradient(135deg, #0a192f 0%, #0f2847 100%);
        }
        code, .monospace {
            font-family: 'Courier New', monospace;
            background: rgba(0, 255, 136, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        {% else %}
        /* Default PSU Theme */
        :root {
            --primary-color: #BE1E2D;
            --secondary-color: #8B1520;
            --accent-color: #FFB81C;
            --psu-crimson: #BE1E2D;
            --psu-gold: #FFB81C;
            --text-color: #1f2937;
            --light-bg: #f9fafb;
            --card-bg: #ffffff;
        }
        body {
            background: #f9fafb;
        }
        .card {
            box-shadow: 0 4px 16px rgba(190, 30, 45, 0.1);
        }
        .hero-section {
            background: linear-gradient(135deg, #BE1E2D 0%, #8B1520 100%);
        }
        {% endif %}
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
        }
        
        /* Pitt State Branding Header */
        .psu-branding {
            background: var(--psu-crimson);
            color: white;
            padding: 0.5rem 0;
            text-align: center;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .psu-logo {
            position: fixed;
            top: 70px;
            right: 20px;
            background: white;
            padding: 10px;
            border-radius: 50%;
            box-shadow: 0 4px 12px rgba(190, 30, 45, 0.3);
            z-index: 1000;
            width: 80px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid var(--psu-crimson);
        }
        
        .psu-logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .hero-section {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 5rem 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" font-size="80" opacity="0.05">🦍</text></svg>') repeat;
            opacity: 0.1;
        }
        
        .profile-image {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 5px solid white;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
        }
        
        .hero-headline {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .hero-tagline {
            font-size: 1.2rem;
            opacity: 0.95;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .psu-badge {
            background: var(--psu-gold);
            color: #333;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            display: inline-block;
            font-weight: 600;
            margin-top: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .social-links a {
            color: white;
            font-size: 1.5rem;
            margin: 0 0.75rem;
            transition: transform 0.2s;
            display: inline-block;
        }
        
        .social-links a:hover {
            transform: scale(1.2);
            color: var(--psu-gold);
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 2rem;
            position: relative;
            padding-bottom: 0.5rem;
            color: var(--psu-crimson);
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 60px;
            height: 3px;
            background: var(--psu-gold);
        }
        
        .experience-card {
            border-left: 3px solid var(--psu-crimson);
            padding-left: 1.5rem;
            margin-bottom: 2.5rem;
        }
        
        .experience-header {
            margin-bottom: 0.5rem;
        }
        
        .experience-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--text-color);
        }
        
        .experience-company {
            font-size: 1.1rem;
            color: var(--psu-crimson);
            font-weight: 500;
        }
        
        .experience-meta {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }
        
        .project-card {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            transition: transform 0.2s, box-shadow 0.2s;
            border-top: 4px solid var(--psu-crimson);
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(190, 30, 45, 0.15);
        }
        
        .project-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--psu-crimson);
        }
        
        .project-subtitle {
            color: var(--text-color);
            font-weight: 500;
            margin-bottom: 0.75rem;
        }
        
        .project-date {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .btn-portfolio {
            background: var(--psu-crimson);
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            text-decoration: none;
            display: inline-block;
            margin-top: 1rem;
            transition: background 0.2s;
        }
        
        .btn-portfolio:hover {
            background: #8B1520;
            color: white;
        }
        
        .award-item {
            background: var(--light-bg);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid var(--psu-gold);
        }
        
        .award-title {
            font-weight: 600;
            color: var(--text-color);
        }
        
        footer {
            background: #1f2937;
            color: white;
            padding: 2rem 0;
            margin-top: 4rem;
            text-align: center;
        }
        
        .psu-footer-logo {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .contact-info {
            margin: 2rem 0;
        }
        
        .contact-item {
            display: inline-block;
            margin: 0 1rem;
        }
        
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 120px;
            background: white;
            border: 2px solid var(--psu-crimson);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            z-index: 999;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
        }
        
        @media (max-width: 768px) {
            .psu-logo {
                width: 60px;
                height: 60px;
                font-size: 2rem;
                top: 60px;
                right: 10px;
            }
            
            .theme-toggle {
                right: 80px;
            }
        }
        
        /* Custom CSS from user */
        {% if portfolio.custom_css %}
        {{ portfolio.custom_css | safe }}
        {% endif %}
    </style>
</head>
<body>
    <!-- Pitt State Branding Bar -->
    {% if portfolio.theme == 'psu' or not portfolio.theme %}
    <div class="psu-branding">
        PITTSBURG STATE UNIVERSITY | PROFESSIONAL PORTFOLIO
    </div>
    
    <!-- Pitt State Logo Badge -->
    <div class="psu-logo" title="Pittsburg State University">
        <img src="/static/images/pittstate-logo.png" alt="PSU Logo" onerror="this.style.display='none'">
    </div>
    {% endif %}
    
    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            {% if portfolio.profile_image %}
            <img src="{{ portfolio.profile_image }}" alt="{{ user.full_name }}" class="profile-image">
            {% else %}
            <div class="profile-image d-inline-block" style="background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 3rem; font-weight: 700;">{{ user.first_name[0] }}{{ user.last_name[0] }}</span>
            </div>
            {% endif %}
            
            <h1 class="hero-headline">{{ user.full_name }}</h1>
            {% if portfolio.headline %}
            <p class="hero-tagline">{{ portfolio.headline }}</p>
            {% endif %}
            
            <div class="psu-badge">
                🎓 Pittsburg State University
                {% if user.graduation_year %}| Class of {{ user.graduation_year }}{% endif %}
            </div>
            
            {% if portfolio.resume_url %}
            <div class="mt-3">
                <a href="{{ portfolio.resume_url }}" class="btn btn-light btn-lg" target="_blank">
                    <i class="bi bi-file-earmark-pdf"></i> View Résumé
                </a>
            </div>
            {% endif %}
            
            <div class="social-links mt-4">
                {% if portfolio.email %}
                <a href="mailto:{{ portfolio.email }}" title="Email"><i class="bi bi-envelope-fill"></i></a>
                {% endif %}
                {% if portfolio.phone %}
                <a href="tel:{{ portfolio.phone }}" title="Phone"><i class="bi bi-telephone-fill"></i></a>
                {% endif %}
                {% if portfolio.linkedin_url %}
                <a href="{{ portfolio.linkedin_url }}" target="_blank" title="LinkedIn"><i class="bi bi-linkedin"></i></a>
                {% endif %}
                {% if portfolio.github_url %}
                <a href="{{ portfolio.github_url }}" target="_blank" title="GitHub"><i class="bi bi-github"></i></a>
                {% endif %}
                {% if portfolio.twitter_url %}
                <a href="{{ portfolio.twitter_url }}" target="_blank" title="Twitter"><i class="bi bi-twitter"></i></a>
                {% endif %}
            </div>
        </div>
    </section>
    
    <!-- About Section -->
    {% if portfolio.about %}
    <section class="py-5">
        <div class="container">
            <h2 class="section-title">About</h2>
            <p class="lead">{{ portfolio.about }}</p>
        </div>
    </section>
    {% endif %}
    
    <!-- Experience Section -->
    {% if portfolio.experiences %}
    <section class="py-5" style="background: var(--light-bg);">
        <div class="container">
            <h2 class="section-title">Experience</h2>
            {% for exp in portfolio.experiences %}
            <div class="experience-card">
                <div class="experience-header">
                    <div class="experience-title">{{ exp.title }}</div>
                    <div class="experience-company">{{ exp.company }}</div>
                </div>
                <div class="experience-meta">
                    {{ exp.start_date.strftime('%b %Y') }} – {% if exp.end_date %}{{ exp.end_date.strftime('%b %Y') }}{% else %}Present{% endif %}
                    {% if exp.location %} | {{ exp.location }}{% endif %}
                </div>
                {% if exp.description %}
                <p>{{ exp.description }}</p>
                {% endif %}
                {% if exp.bullets %}
                <ul>
                    {% for bullet in exp.bullets %}
                    <li>{{ bullet }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    <!-- Projects Section -->
    {% if portfolio.projects %}
    <section class="py-5">
        <div class="container">
            <h2 class="section-title">Projects</h2>
            <div class="row">
                {% for project in portfolio.projects %}
                <div class="col-md-6 mb-4">
                    <div class="project-card">
                        <h3 class="project-title">{{ project.title }}</h3>
                        {% if project.subtitle %}
                        <div class="project-subtitle">{{ project.subtitle }}</div>
                        {% endif %}
                        {% if project.date %}
                        <div class="project-date">{{ project.date }}</div>
                        {% endif %}
                        {% if project.description %}
                        <p>{{ project.description }}</p>
                        {% endif %}
                        {% if project.impact %}
                        <p><strong>Impact:</strong> {{ project.impact }}</p>
                        {% endif %}
                        {% if project.project_url %}
                        <a href="{{ project.project_url }}" class="btn-portfolio" target="_blank">
                            View Project <i class="bi bi-arrow-right"></i>
                        </a>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}
    
    <!-- Awards Section -->
    {% if portfolio.awards %}
    <section class="py-5" style="background: var(--light-bg);">
        <div class="container">
            <h2 class="section-title">🏆 Awards & Honors</h2>
            {% for award in portfolio.awards %}
            <div class="award-item">
                <div class="award-title">{{ award.title }}</div>
                {% if award.description %}
                <div class="text-muted">{{ award.description }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    <!-- Contact Section -->
    <section class="py-5">
        <div class="container text-center">
            <h2 class="section-title" style="text-align: center;">📬 Contact</h2>
            <p class="lead mb-4">Connect with {{ user.first_name }} on professional platforms:</p>
            <div class="contact-info">
                {% if portfolio.email %}
                <div class="contact-item">
                    <a href="mailto:{{ portfolio.email }}" class="btn btn-outline-primary">
                        <i class="bi bi-envelope"></i> {{ portfolio.email }}
                    </a>
                </div>
                {% endif %}
                {% if portfolio.phone %}
                <div class="contact-item">
                    <a href="tel:{{ portfolio.phone }}" class="btn btn-outline-primary">
                        <i class="bi bi-telephone"></i> {{ portfolio.phone }}
                    </a>
                </div>
                {% endif %}
            </div>
        </div>
    </section>
    
    <!-- Footer -->
    <footer>
        <div class="container">
            {% if portfolio.theme == 'psu' or not portfolio.theme %}
            <div class="psu-footer-logo">
                <img src="/static/images/pittstate-logo.png" alt="PSU" style="max-height: 40px;" onerror="this.style.display='none'">
            </div>
            <p style="font-weight: 600; color: var(--psu-gold);">PITTSBURG STATE UNIVERSITY</p>
            {% endif %}
            <p>&copy; {{ now().year }} {{ user.full_name }} | Professional Portfolio</p>
        </div>
    </footer>
    
    <!-- Theme Toggle -->
    <div class="theme-toggle" id="themeToggle" title="Toggle theme">
        <i class="bi bi-moon-fill" id="themeIcon"></i>
    </div>
    
    <script>
        // Simple theme toggle
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            themeIcon.classList.toggle('bi-moon-fill');
            themeIcon.classList.toggle('bi-sun-fill');
        });
    </script>
</body>
</html>
"""

# ======================================================
# ROUTES
# ======================================================

@bp.get("/health")
def health():
    return jsonify(status="ok", section="portfolio")

@bp.get("/")
def index():
    """Browse all public portfolios"""
    portfolios = db.session.query(Portfolio).filter_by(is_public=True).order_by(desc(Portfolio.updated_at)).limit(50).all()
    
    return render_template_string(PORTFOLIO_INDEX_TEMPLATE, portfolios=portfolios)

@bp.get("/create")
@login_required
def create_form():
    """Show portfolio creation form"""
    # Check if user already has a portfolio
    existing = Portfolio.query.filter_by(user_id=current_user.id).first()
    if existing:
        return redirect(url_for('portfolio.edit'))
    
    return render_template_string(PORTFOLIO_CREATE_TEMPLATE)

@bp.post("/create")
@login_required
def create():
    """Create a new portfolio"""
    # Check if user already has a portfolio
    existing = Portfolio.query.filter_by(user_id=current_user.id).first()
    if existing:
        flash("You already have a portfolio!", "warning")
        return redirect(url_for('portfolio.edit'))
    
    # Create slug from user's name
    slug = f"{current_user.first_name.lower()}-{current_user.last_name.lower()}"
    
    # Ensure slug is unique
    base_slug = slug
    counter = 1
    while Portfolio.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    portfolio = Portfolio(
        user_id=current_user.id,
        slug=slug,
        email=current_user.email,
        headline=request.form.get('headline', ''),
        about=request.form.get('about', ''),
        phone=request.form.get('phone', ''),
        linkedin_url=request.form.get('linkedin_url', ''),
        github_url=request.form.get('github_url', ''),
        twitter_url=request.form.get('twitter_url', ''),
        is_public=request.form.get('is_public', 'true') == 'true'
    )
    
    db.session.add(portfolio)
    db.session.commit()
    
    flash("Portfolio created successfully!", "success")
    return redirect(url_for('portfolio.view', slug=portfolio.slug))

@bp.get("/edit")
@login_required
def edit():
    """Edit portfolio"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        return redirect(url_for('portfolio.create_form'))
    
    return render_template_string(PORTFOLIO_EDIT_TEMPLATE, portfolio=portfolio)

@bp.get("/<slug>")
def view(slug):
    """View a public portfolio"""
    portfolio = Portfolio.query.filter_by(slug=slug).first_or_404()
    
    if not portfolio.is_public and (not current_user.is_authenticated or current_user.id != portfolio.user_id):
        return jsonify({"error": "Portfolio is private"}), 403
    
    # Increment view count
    portfolio.views += 1
    db.session.commit()
    
    # Get user info
    user = User.query.get(portfolio.user_id)
    
    return render_template_string(PORTFOLIO_VIEW_TEMPLATE, portfolio=portfolio, user=user)

# ======================================================
# CONTENT MANAGEMENT ROUTES
# ======================================================

@bp.post("/update-basic")
@login_required
def update_basic():
    """Update basic portfolio information"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    portfolio.headline = request.form.get('headline', '')
    portfolio.about = request.form.get('about', '')
    portfolio.phone = request.form.get('phone', '')
    portfolio.website_url = request.form.get('website_url', '')
    portfolio.linkedin_url = request.form.get('linkedin_url', '')
    portfolio.github_url = request.form.get('github_url', '')
    portfolio.twitter_url = request.form.get('twitter_url', '')
    portfolio.is_public = request.form.get('is_public', 'false') == 'true'
    
    db.session.commit()
    flash("Portfolio updated successfully!", "success")
    return redirect(url_for('portfolio.edit'))

@bp.post("/add-experience")
@login_required
def add_experience():
    """Add new work experience"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Parse dates
    start_date_str = request.form.get('start_date')
    if not start_date_str:
        flash("Start date is required", "error")
        return redirect(url_for('portfolio.edit'))
    
    start_date = datetime.strptime(start_date_str + '-01', '%Y-%m-%d').date()
    end_date_str = request.form.get('end_date')
    end_date = datetime.strptime(end_date_str + '-01', '%Y-%m-%d').date() if end_date_str else None
    
    # Process bullets
    bullets_text = request.form.get('bullets', '')
    bullets = [line.strip('- ').strip() for line in bullets_text.split('\n') if line.strip()]
    
    experience = PortfolioExperience(
        portfolio_id=portfolio.id,
        title=request.form.get('title'),
        company=request.form.get('company'),
        location=request.form.get('location', ''),
        start_date=start_date,
        end_date=end_date,
        description=request.form.get('description', ''),
        bullets=json.dumps(bullets) if bullets else None
    )
    
    db.session.add(experience)
    db.session.commit()
    
    flash("Experience added successfully!", "success")
    return redirect(url_for('portfolio.edit'))

@bp.delete("/experience/<int:id>")
@login_required
def delete_experience(id):
    """Delete work experience"""
    experience = PortfolioExperience.query.get_or_404(id)
    
    # Verify ownership
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio or experience.portfolio_id != portfolio.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(experience)
    db.session.commit()
    
    return jsonify({"success": True})

@bp.post("/add-project")
@login_required
def add_project():
    """Add new project"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Handle image upload
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            filename = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_url = f"/static/uploads/portfolios/{filename}"
    
    # Process tags
    tags_text = request.form.get('tags', '')
    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    
    project = PortfolioProject(
        portfolio_id=portfolio.id,
        title=request.form.get('title'),
        subtitle=request.form.get('subtitle', ''),
        description=request.form.get('description', ''),
        date=request.form.get('date', ''),
        impact=request.form.get('impact', ''),
        project_url=request.form.get('project_url', ''),
        github_url=request.form.get('github_url', ''),
        image_url=image_url,
        tags=json.dumps(tags) if tags else None
    )
    
    db.session.add(project)
    db.session.commit()
    
    flash("Project added successfully!", "success")
    return redirect(url_for('portfolio.edit'))

@bp.delete("/project/<int:id>")
@login_required
def delete_project(id):
    """Delete project"""
    project = PortfolioProject.query.get_or_404(id)
    
    # Verify ownership
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio or project.portfolio_id != portfolio.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Delete image file if exists
    if project.image_url:
        try:
            filepath = project.image_url.replace('/static/', 'static/')
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({"success": True})

@bp.post("/add-award")
@login_required
def add_award():
    """Add new award"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Parse date
    date_str = request.form.get('date')
    award_date = datetime.strptime(date_str + '-01', '%Y-%m-%d').date() if date_str else None
    
    award = PortfolioAward(
        portfolio_id=portfolio.id,
        title=request.form.get('title'),
        issuer=request.form.get('issuer', ''),
        description=request.form.get('description', ''),
        date=award_date
    )
    
    db.session.add(award)
    db.session.commit()
    
    flash("Award added successfully!", "success")
    return redirect(url_for('portfolio.edit'))

@bp.delete("/award/<int:id>")
@login_required
def delete_award(id):
    """Delete award"""
    award = PortfolioAward.query.get_or_404(id)
    
    # Verify ownership
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio or award.portfolio_id != portfolio.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(award)
    db.session.commit()
    
    return jsonify({"success": True})

@bp.post("/add-skill")
@login_required
def add_skill():
    """Add new skill"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    skill = PortfolioSkill(
        portfolio_id=portfolio.id,
        name=request.form.get('name'),
        category=request.form.get('category', 'Other'),
        proficiency=int(request.form.get('proficiency', 3))
    )
    
    db.session.add(skill)
    db.session.commit()
    
    flash("Skill added successfully!", "success")
    return redirect(url_for('portfolio.edit'))

@bp.delete("/skill/<int:id>")
@login_required
def delete_skill(id):
    """Delete skill"""
    skill = PortfolioSkill.query.get_or_404(id)
    
    # Verify ownership
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio or skill.portfolio_id != portfolio.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(skill)
    db.session.commit()
    
    return jsonify({"success": True})

# ======================================================
# MEDIA UPLOAD ROUTES
# ======================================================

@bp.post("/upload-profile-image")
@login_required
def upload_profile_image():
    """Upload profile image"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    if 'profile_image' not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for('portfolio.edit'))
    
    file = request.files['profile_image']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('portfolio.edit'))
    
    if file and allowed_file(file.filename):
        # Create upload directory
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Delete old image if exists
        if portfolio.profile_image:
            try:
                old_path = portfolio.profile_image.replace('/static/', 'static/')
                if os.path.exists(old_path):
                    os.remove(old_path)
            except:
                pass
        
        # Save new image
        filename = secure_filename(f"profile_{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        portfolio.profile_image = f"/static/uploads/portfolios/{filename}"
        db.session.commit()
        
        flash("Profile image uploaded successfully!", "success")
    else:
        flash("Invalid file type. Please upload an image file.", "error")
    
    return redirect(url_for('portfolio.edit'))

@bp.post("/upload-resume")
@login_required
def upload_resume():
    """Upload resume PDF"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    if 'resume' not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for('portfolio.edit'))
    
    file = request.files['resume']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('portfolio.edit'))
    
    if file and file.filename and file.filename.endswith('.pdf'):
        # Create upload directory
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Delete old resume if exists
        if portfolio.resume_url:
            try:
                old_path = portfolio.resume_url.replace('/static/', 'static/')
                if os.path.exists(old_path):
                    os.remove(old_path)
            except:
                pass
        
        # Save new resume
        filename = secure_filename(f"resume_{current_user.id}_{datetime.now().timestamp()}.pdf")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        portfolio.resume_url = f"/static/uploads/portfolios/{filename}"
        db.session.commit()
        
        flash("Resume uploaded successfully!", "success")
    else:
        flash("Please upload a PDF file.", "error")
    
    return redirect(url_for('portfolio.edit'))

# ======================================================
# THEME CUSTOMIZATION ROUTES
# ======================================================

@bp.post("/update-theme")
@login_required
def update_theme():
    """Update portfolio theme"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first_or_404()
    
    portfolio.theme = request.form.get('theme_preset', 'psu')
    portfolio.custom_css = request.form.get('custom_css', '')
    
    db.session.commit()
    
    flash("Theme updated successfully!", "success")
    return redirect(url_for('portfolio.edit'))

# ======================================================
# EXPORT ROUTES
# ======================================================

@bp.get("/export/<slug>/pdf")
def export_pdf(slug):
    """Export portfolio as PDF"""
    portfolio = Portfolio.query.filter_by(slug=slug).first_or_404()
    
    # Check permissions
    if not portfolio.is_public and (not current_user.is_authenticated or current_user.id != portfolio.user_id):
        return jsonify({"error": "Portfolio is private"}), 403
    
    # Get user info
    user = User.query.get(portfolio.user_id)
    
    # Render portfolio HTML
    html_content = render_template_string(PORTFOLIO_VIEW_TEMPLATE, portfolio=portfolio, user=user)
    
    try:
        # Generate PDF using pdfkit
        pdf = pdfkit.from_string(html_content, False, options={
            'page-size': 'Letter',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        })
        
        # Create response
        response = send_file(
            BytesIO(pdf),
            as_attachment=True,
            download_name=f"{slug}_portfolio.pdf",
            mimetype='application/pdf'
        )
        
        return response
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for('portfolio.view', slug=slug))
