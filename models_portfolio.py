"""
Portfolio Models - Professional Portfolio System
Stores user portfolios, experiences, projects, awards, and skills
"""

# Determine if we're using PostgreSQL or SQLite
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///pittstate_connect_local.db')
USE_POSTGRES = DATABASE_URL.startswith('postgresql')

from extensions import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy import Text


class Portfolio(db.Model):
    """User portfolio profile"""
    __tablename__ = "portfolios"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)  # URL-friendly username
    
    # Profile Information
    headline = db.Column(db.String(255))  # e.g., "Turning Strategy into Impact"
    about = db.Column(db.Text)
    profile_image = db.Column(db.String(512))
    
    # Contact & Social
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(512))
    github_url = db.Column(db.String(512))
    twitter_url = db.Column(db.String(512))
    website_url = db.Column(db.String(512))
    
    # Resume
    resume_url = db.Column(db.String(512))
    
    # Settings
    is_public = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(50), default="light")  # light/dark
    custom_css = db.Column(db.Text)
    
    # Metadata
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    experiences = db.relationship("PortfolioExperience", back_populates="portfolio", lazy=True, cascade="all, delete-orphan", order_by="PortfolioExperience.start_date.desc()")
    projects = db.relationship("PortfolioProject", back_populates="portfolio", lazy=True, cascade="all, delete-orphan", order_by="PortfolioProject.date.desc()")
    awards = db.relationship("PortfolioAward", back_populates="portfolio", lazy=True, cascade="all, delete-orphan", order_by="PortfolioAward.date.desc()")
    skills = db.relationship("PortfolioSkill", back_populates="portfolio", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio {self.slug}>"


class PortfolioExperience(db.Model):
    """Work experience entries"""
    __tablename__ = "portfolio_experiences"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id"), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)  # e.g., "Sales & Supply Chain Intern"
    company = db.Column(db.String(255), nullable=False)  # e.g., "Jake's Fireworks"
    location = db.Column(db.String(255))  # e.g., "Pittsburg, KS"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL = present
    description = db.Column(db.Text)
    bullets = db.Column(db.Text)  # JSON string of bullet points
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    portfolio = db.relationship("Portfolio", back_populates="experiences")
    
    def __repr__(self):
        return f"<Experience {self.title} at {self.company}>"


class PortfolioProject(db.Model):
    """Portfolio projects"""
    __tablename__ = "portfolio_projects"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id"), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255))  # e.g., "Strategic Marketing & Planning Analysis"
    description = db.Column(db.Text)
    date = db.Column(db.String(100))  # e.g., "April 2025" or "2025 – Present"
    impact = db.Column(db.Text)  # Results/impact section
    
    # Links
    project_url = db.Column(db.String(512))  # Link to PDF or external site
    github_url = db.Column(db.String(512))
    demo_url = db.Column(db.String(512))
    
    # Media
    image_url = db.Column(db.String(512))
    tags = db.Column(db.Text)  # JSON string of tags
    
    # Display order
    display_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    portfolio = db.relationship("Portfolio", back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.title}>"


class PortfolioAward(db.Model):
    """Awards and honors"""
    __tablename__ = "portfolio_awards"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id"), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)  # e.g., "Golden Gorilla Award"
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    issuer = db.Column(db.String(255))  # e.g., "Pittsburg State University"
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    portfolio = db.relationship("Portfolio", back_populates="awards")
    
    def __repr__(self):
        return f"<Award {self.title}>"


class PortfolioSkill(db.Model):
    """Skills and competencies"""
    __tablename__ = "portfolio_skills"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))  # e.g., "Technical", "Leadership", "Marketing"
    proficiency = db.Column(db.Integer)  # 1-5 rating
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    portfolio = db.relationship("Portfolio", back_populates="skills")
    
    def __repr__(self):
        return f"<Skill {self.name}>"
