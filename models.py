import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY
from extensions import db

# ---------------------------
# USER & AUTH MODELS
# ---------------------------

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    major = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    date_joined = db.Column(db.DateTime, default=func.now())
    last_login = db.Column(db.DateTime, default=func.now())

    # Relationships
    role = db.relationship("Role", back_populates="users", lazy=True)
    posts = db.relationship("Post", back_populates="author", lazy=True)
    connections = db.relationship(
        "Connection",
        foreign_keys="Connection.user_id",
        back_populates="user",
        lazy=True,
    )
    notifications = db.relationship("Notification", back_populates="recipient", lazy=True)
    resumes = db.relationship("Resume", back_populates="user", lazy=True, cascade="all, delete-orphan")
    mock_interviews = db.relationship("MockInterview", back_populates="user", lazy=True)
    career_assessments = db.relationship("CareerAssessment", back_populates="user", lazy=True)
    
    # Extended profile fields for production
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(512))
    github_url = db.Column(db.String(512))
    portfolio_url = db.Column(db.String(512))
    gpa = db.Column(db.Float)
    skills = db.Column(ARRAY(db.String))
    interests = db.Column(ARRAY(db.String))
    resume_url = db.Column(db.String(512))
    transcript_url = db.Column(db.String(512))
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(128))
    onboarding_completed = db.Column(db.Boolean, default=False)
    privacy_settings = db.Column(JSONB)
    notification_preferences = db.Column(JSONB)
    last_active = db.Column(db.DateTime)
    
    # Payment integration
    stripe_customer_id = db.Column(db.String(128))
    
    # OAuth integration fields
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    linkedin_id = db.Column(db.String(128), unique=True, nullable=True)
    microsoft_id = db.Column(db.String(128), unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    profile_image_url = db.Column(db.String(512))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}>"


# ---------------------------
# CONTENT MODELS
# ---------------------------

class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    image_url = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    likes = db.Column(db.Integer, default=0)
    visibility = db.Column(db.String(32), default="public")

    author = db.relationship("User", back_populates="posts", lazy=True)

    def __repr__(self):
        return f"<Post {self.id} by {self.author_id}>"


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    chair_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    scholarships = db.relationship("Scholarship", back_populates="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(255))
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    def __repr__(self):
        return f"<Event {self.title}>"


# ---------------------------
# NETWORK & COMMUNICATION
# ---------------------------

class Connection(db.Model):
    __tablename__ = "connections"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    connected_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="connections",
        lazy=True,
    )
    connected_user = db.relationship(
        "User",
        foreign_keys=[connected_user_id],
        lazy=True,
    )

    def __repr__(self):
        return f"<Connection {self.user_id} → {self.connected_user_id} ({self.status})>"


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), default="info")
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=func.now())

    recipient = db.relationship("User", back_populates="notifications", lazy=True)

    def __repr__(self):
        return f"<Notification to {self.recipient_id}: {self.message[:20]}>"


# ---------------------------
# SCHOLARSHIP & CAREER MODELS
# ---------------------------

class Scholarship(db.Model):
    __tablename__ = "scholarships"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    deadline = db.Column(db.Date)
    eligibility = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=func.now())

    department = db.relationship("Department", back_populates="scholarships", lazy=True)

    def __repr__(self):
        return f"<Scholarship {self.title}>"


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=func.now())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


# ---------------------------
# ANALYTICS & TRACKING
# ---------------------------

class PageView(db.Model):
    __tablename__ = "page_views"
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    def __repr__(self):
        return f"<PageView {self.page_name} by {self.user_id or 'Guest'}>"


class AnalyticsSummary(db.Model):
    __tablename__ = "analytics_summary"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.date.today)
    page_views = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    scholarships_viewed = db.Column(db.Integer, default=0)
    jobs_viewed = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<AnalyticsSummary {self.date}>"


class ApiUsage(db.Model):
    __tablename__ = "api_usage"
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    response_time_ms = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer, default=0)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    def __repr__(self):
        return f"<ApiUsage {self.endpoint} ({self.status_code})>"


# ---------------------------
# RESUME & CAREER DEVELOPMENT MODELS
# ---------------------------

class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("resume_templates.id"))
    status = db.Column(db.String(20), default='draft')  # draft, active, archived
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(64), unique=True)
    views_count = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = db.relationship("User", back_populates="resumes")
    template = db.relationship("ResumeTemplate", back_populates="resumes")
    sections = db.relationship("ResumeSection", back_populates="resume", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume {self.title} by User {self.user_id}>"


class ResumeSection(db.Model):
    __tablename__ = "resume_sections"
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False)
    section_type = db.Column(db.String(50), nullable=False)  # summary, experience, education, skills, etc.
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    resume = db.relationship("Resume", back_populates="sections")
    
    def __repr__(self):
        return f"<ResumeSection {self.section_type} for Resume {self.resume_id}>"


class ResumeTemplate(db.Model):
    __tablename__ = "resume_templates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    preview_image = db.Column(db.String(512))
    category = db.Column(db.String(50))  # modern, classic, creative, academic, technical
    color_scheme = db.Column(db.String(50))
    font_family = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_premium = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    
    # Relationships
    resumes = db.relationship("Resume", back_populates="template")
    
    def __repr__(self):
        return f"<ResumeTemplate {self.name}>"


class MockInterview(db.Model):
    __tablename__ = "mock_interviews"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    interview_type = db.Column(db.String(50))  # behavioral, technical, case, phone
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    questions = db.Column(JSONB)  # Array of questions with suggested answers
    user_responses = db.Column(JSONB)  # User's recorded/written responses
    ai_feedback = db.Column(JSONB)  # AI-generated feedback on responses
    overall_score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship("User", back_populates="mock_interviews")
    
    def __repr__(self):
        return f"<MockInterview {self.interview_type} for User {self.user_id}>"


class CareerAssessment(db.Model):
    __tablename__ = "career_assessments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assessment_type = db.Column(db.String(50))  # personality, skills, interests, values
    results = db.Column(JSONB)  # Assessment results and scores
    recommendations = db.Column(JSONB)  # Career path recommendations
    completed_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    user = db.relationship("User", back_populates="career_assessments")
    
    def __repr__(self):
        return f"<CareerAssessment {self.assessment_type} for User {self.user_id}>"


class SkillEndorsement(db.Model):
    __tablename__ = "skill_endorsements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    endorser_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    proficiency_level = db.Column(db.Integer)  # 1-5 scale
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SkillEndorsement {self.skill_name} for User {self.user_id}>"


class LearningResource(db.Model):
    __tablename__ = "learning_resources"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    resource_type = db.Column(db.String(50))  # course, video, article, book, certification
    url = db.Column(db.String(512))
    provider = db.Column(db.String(100))  # Coursera, Udemy, LinkedIn Learning, etc.
    category = db.Column(db.String(100))  # tech, business, design, etc.
    difficulty = db.Column(db.String(20))  # beginner, intermediate, advanced
    duration_hours = db.Column(db.Float)
    cost = db.Column(db.Float)  # 0 for free
    rating = db.Column(db.Float)
    tags = db.Column(ARRAY(db.String))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<LearningResource {self.title}>"


class UserCourse(db.Model):
    __tablename__ = "user_courses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey("learning_resources.id"), nullable=False)
    status = db.Column(db.String(20))  # enrolled, in_progress, completed, dropped
    progress_percent = db.Column(db.Float, default=0)
    started_at = db.Column(db.DateTime, default=func.now())
    completed_at = db.Column(db.DateTime)
    certificate_url = db.Column(db.String(512))
    
    def __repr__(self):
        return f"<UserCourse User {self.user_id} Resource {self.resource_id}>"


class IndustryInsight(db.Model):
    __tablename__ = "industry_insights"
    id = db.Column(db.Integer, primary_key=True)
    industry = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    insight_type = db.Column(db.String(50))  # trend, advice, salary_data, skills_demand
    data_points = db.Column(JSONB)  # Structured data (salary ranges, growth rates, etc.)
    views_count = db.Column(db.Integer, default=0)
    published_at = db.Column(db.DateTime, default=func.now())
    is_featured = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<IndustryInsight {self.title}>"


class CompanyReview(db.Model):
    __tablename__ = "company_reviews"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    position = db.Column(db.String(200))
    rating_overall = db.Column(db.Float)  # 1-5 scale
    rating_culture = db.Column(db.Float)
    rating_compensation = db.Column(db.Float)
    rating_work_life = db.Column(db.Float)
    rating_management = db.Column(db.Float)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    advice = db.Column(db.Text)
    is_current_employee = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<CompanyReview for Company {self.company_id}>"


class Company(db.Model):
    """Company profiles for job postings and reviews"""
    __tablename__ = "companies"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    size = db.Column(db.String(50))  # 1-10, 11-50, 51-200, 201-500, 501+
    headquarters = db.Column(db.String(200))
    website = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    job_postings = db.relationship('JobPosting', backref='company', lazy='dynamic')
    reviews = db.relationship('CompanyReview', backref='company', lazy='dynamic')
    
    def __repr__(self):
        return f"<Company {self.name}>"


class JobPosting(db.Model):
    """Job postings for student applications"""
    __tablename__ = "job_postings"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    location = db.Column(db.String(200))
    job_type = db.Column(db.String(50))  # full_time, part_time, internship, contract
    experience_level = db.Column(db.String(50))  # entry, mid, senior
    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    skills_required = db.Column(ARRAY(db.String))
    posted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    posted_at = db.Column(db.DateTime, default=func.now())
    expires_at = db.Column(db.DateTime)
    application_url = db.Column(db.String(500))
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy='dynamic')
    posted_by = db.relationship('User', backref=db.backref('posted_jobs', lazy='dynamic'))
    
    def __repr__(self):
        return f"<JobPosting {self.title} at {self.company_id}>"


class Application(db.Model):
    """Student job applications"""
    __tablename__ = "applications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(50), default='submitted')  # submitted, reviewed, interview, offer, rejected
    applied_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('applications', lazy='dynamic'))
    resume = db.relationship('Resume')
    
    def __repr__(self):
        return f"<Application {self.user_id} to Job {self.job_id}>"


class SalaryData(db.Model):
    __tablename__ = "salary_data"
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    industry = db.Column(db.String(100))
    location = db.Column(db.String(200))
    experience_level = db.Column(db.String(50))  # entry, mid, senior, lead
    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    salary_currency = db.Column(db.String(10), default='USD')
    employment_type = db.Column(db.String(50))  # full_time, part_time, contract
    benefits = db.Column(JSONB)  # Healthcare, 401k, PTO, etc.
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SalaryData {self.job_title}>"


# ---------------------------
# HELPER METHODS
# ---------------------------

def track_page_view(page_name, user_id=None, ip_address=None, user_agent=None):
    """Log page views for analytics tracking."""
    view = PageView(
        page_name=page_name,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(view)
    db.session.commit()

