# File: blueprints/portfolio/routes.py
from flask import Blueprint, render_template_string, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models_portfolio import Portfolio, PortfolioExperience, PortfolioProject, PortfolioAward, PortfolioSkill
from models import User
from datetime import datetime
from sqlalchemy import desc

bp = Blueprint("portfolio", __name__, url_prefix="/portfolio")

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
    <h1 class="mb-4">Edit Your Portfolio</h1>
    <p class="text-muted mb-4">Update your professional information</p>
    
    <div class="alert alert-info">
        <i class="bi bi-info-circle"></i> Your portfolio URL: 
        <a href="{{ url_for('portfolio.view', slug=portfolio.slug) }}" target="_blank">
            {{ request.host_url }}portfolio/{{ portfolio.slug }}
        </a>
    </div>
    
    <p class="text-muted">Portfolio editing coming soon! For now, you can view your portfolio above.</p>
    <a href="{{ url_for('portfolio.view', slug=portfolio.slug) }}" class="btn btn-primary">
        <i class="bi bi-eye"></i> View My Portfolio
    </a>
</div>
{% endblock %}
"""

PORTFOLIO_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user.full_name }} | Professional Portfolio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --text-color: #1f2937;
            --light-bg: #f9fafb;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--text-color);
            line-height: 1.7;
        }
        
        .hero-section {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 5rem 0;
            text-align: center;
        }
        
        .profile-image {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 5px solid white;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            margin-bottom: 1.5rem;
        }
        
        .hero-headline {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        
        .hero-tagline {
            font-size: 1.2rem;
            opacity: 0.95;
            margin-bottom: 2rem;
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
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 2rem;
            position: relative;
            padding-bottom: 0.5rem;
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 60px;
            height: 3px;
            background: var(--primary-color);
        }
        
        .experience-card {
            border-left: 3px solid var(--primary-color);
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
            color: var(--primary-color);
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
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .project-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .project-subtitle {
            color: var(--primary-color);
            font-weight: 500;
            margin-bottom: 0.75rem;
        }
        
        .project-date {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .btn-portfolio {
            background: var(--primary-color);
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 25px;
            text-decoration: none;
            display: inline-block;
            margin-top: 1rem;
            transition: background 0.2s;
        }
        
        .btn-portfolio:hover {
            background: var(--secondary-color);
            color: white;
        }
        
        .award-item {
            background: var(--light-bg);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid var(--primary-color);
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
            right: 20px;
            background: white;
            border: 2px solid var(--primary-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
        }
    </style>
</head>
<body>
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
            
            {% if portfolio.resume_url %}
            <a href="{{ portfolio.resume_url }}" class="btn btn-light btn-lg" target="_blank">
                <i class="bi bi-file-earmark-pdf"></i> View Résumé
            </a>
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
            <p>&copy; {{ now().year }} {{ user.full_name }} | Professional Portfolio</p>
            <p class="text-muted small">Powered by PittState-Connect</p>
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
