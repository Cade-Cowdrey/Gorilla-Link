"""
Extended Models for Production-Grade PittState-Connect
Includes: Security, Scholarships Phase 2, Alumni, Analytics, AI, Communication, Monetization
"""

import datetime
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY
from extensions import db
import secrets


# ================================================================
# SECURITY & AUTHENTICATION MODELS
# ================================================================

class TwoFactorAuth(db.Model):
    """Two-Factor Authentication (TOTP)"""
    __tablename__ = "two_factor_auth"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    secret = db.Column(db.String(32), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=func.now())
    last_used = db.Column(db.DateTime)
    
    user = db.relationship("User", backref=db.backref("two_factor", uselist=False))


class WebAuthnCredential(db.Model):
    """WebAuthn/FIDO2 Credentials"""
    __tablename__ = "webauthn_credentials"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    credential_id = db.Column(db.String(255), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    sign_count = db.Column(db.Integer, default=0)
    device_name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=func.now())
    last_used = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="webauthn_credentials")


class AuditLog(db.Model):
    """Comprehensive audit trail for compliance"""
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(128), nullable=False)
    resource_type = db.Column(db.String(64))
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(512))
    details = db.Column(JSONB)
    timestamp = db.Column(db.DateTime, default=func.now(), index=True)
    severity = db.Column(db.String(20), default="info")  # info, warning, critical
    
    user = db.relationship("User", backref="audit_logs")


class ConsentRecord(db.Model):
    """FERPA/GDPR Consent Management"""
    __tablename__ = "consent_records"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    consent_type = db.Column(db.String(64), nullable=False)  # ferpa, gdpr, marketing, etc.
    granted = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(20))
    granted_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    
    user = db.relationship("User", backref="consents")


class SecretVault(db.Model):
    """Encrypted secrets management"""
    __tablename__ = "secret_vault"
    
    id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    encrypted_value = db.Column(db.Text, nullable=False)
    rotation_date = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())


# ================================================================
# SCHOLARSHIP HUB PHASE 2
# ================================================================

class ScholarshipExtended(db.Model):
    """Extended scholarship model with AI matching"""
    __tablename__ = "scholarships_extended"
    
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), unique=True)
    ai_tags = db.Column(ARRAY(db.String), default=[])
    match_criteria = db.Column(JSONB)  # GPA, major, year, demographics
    essay_required = db.Column(db.Boolean, default=False)
    essay_prompts = db.Column(JSONB)
    num_recommendations = db.Column(db.Integer, default=0)
    renewable = db.Column(db.Boolean, default=False)
    award_notification_date = db.Column(db.Date)
    funding_source = db.Column(db.String(128))  # donor, department, endowment
    impact_story = db.Column(db.Text)
    
    scholarship = db.relationship("Scholarship", backref=db.backref("extended", uselist=False))


class ScholarshipApplication(db.Model):
    """Track scholarship applications"""
    __tablename__ = "scholarship_applications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)
    status = db.Column(db.String(32), default="draft")  # draft, submitted, under_review, awarded, denied
    submitted_at = db.Column(db.DateTime)
    essay_text = db.Column(db.Text)
    ai_match_score = db.Column(db.Float)
    progress_percentage = db.Column(db.Integer, default=0)
    recommendations_uploaded = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    user = db.relationship("User", backref="scholarship_applications")
    scholarship = db.relationship("Scholarship", backref="applications")


class EssayLibrary(db.Model):
    """Shared essay repository with AI assistance"""
    __tablename__ = "essay_library"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    prompt = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    ai_suggestions = db.Column(JSONB)
    word_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    user = db.relationship("User", backref="essays")


class FinancialLiteracy(db.Model):
    """Financial literacy content & progress tracking"""
    __tablename__ = "financial_literacy"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64))  # budgeting, loans, investing, etc.
    content = db.Column(db.Text)
    video_url = db.Column(db.String(512))
    quiz_data = db.Column(JSONB)
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    created_at = db.Column(db.DateTime, default=func.now())


class UserFinancialProgress(db.Model):
    """Track user financial literacy completion"""
    __tablename__ = "user_financial_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("financial_literacy.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="financial_progress")
    module = db.relationship("FinancialLiteracy", backref="user_progress")


class DonorPortal(db.Model):
    """Donor management and tracking"""
    __tablename__ = "donor_portal"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    donor_name = db.Column(db.String(255), nullable=False)
    donor_type = db.Column(db.String(64))  # individual, corporate, foundation
    total_donated = db.Column(db.Float, default=0.0)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"))
    impact_stories_enabled = db.Column(db.Boolean, default=True)
    recognition_level = db.Column(db.String(64))  # bronze, silver, gold, platinum
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="donor_profile")
    scholarship = db.relationship("Scholarship", backref="donors")


# ================================================================
# ALUMNI & EMPLOYER ENGAGEMENT
# ================================================================

class AlumniProfile(db.Model):
    """Extended alumni profiles"""
    __tablename__ = "alumni_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    graduation_year = db.Column(db.Integer)
    degree = db.Column(db.String(128))
    current_company = db.Column(db.String(255))
    current_position = db.Column(db.String(255))
    industry = db.Column(db.String(128))
    linkedin_url = db.Column(db.String(512))
    is_mentor = db.Column(db.Boolean, default=False)
    mentorship_areas = db.Column(ARRAY(db.String))
    availability = db.Column(JSONB)  # calendar availability
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref=db.backref("alumni_profile", uselist=False))


class MentorshipSession(db.Model):
    """Track mentorship sessions"""
    __tablename__ = "mentorship_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer)
    topic = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status = db.Column(db.String(32), default="scheduled")  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=func.now())
    
    mentor = db.relationship("User", foreign_keys=[mentor_id], backref="mentoring_sessions")
    mentee = db.relationship("User", foreign_keys=[mentee_id], backref="mentee_sessions")


class EmployerPortal(db.Model):
    """Employer analytics and engagement"""
    __tablename__ = "employer_portal"
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False, unique=True)
    industry = db.Column(db.String(128))
    contact_email = db.Column(db.String(255))
    contact_name = db.Column(db.String(255))
    sponsorship_tier = db.Column(db.String(32))  # free, bronze, silver, gold, platinum
    logo_url = db.Column(db.String(512))
    description = db.Column(db.Text)
    jobs_posted = db.Column(db.Integer, default=0)
    active_since = db.Column(db.DateTime, default=func.now())
    premium_until = db.Column(db.DateTime)
    
    # Analytics access
    analytics_enabled = db.Column(db.Boolean, default=False)
    monthly_fee = db.Column(db.Float, default=0.0)


class SponsorshipTier(db.Model):
    """Sponsorship tier definitions"""
    __tablename__ = "sponsorship_tiers"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    annual_cost = db.Column(db.Float, nullable=False)
    benefits = db.Column(JSONB)
    max_job_postings = db.Column(db.Integer)
    analytics_access = db.Column(db.Boolean, default=False)
    featured_placement = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)


class EventSponsor(db.Model):
    """Event sponsorship records"""
    __tablename__ = "event_sponsors"
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    sponsor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sponsorship_level = db.Column(db.String(32), nullable=False)  # presenting, platinum, gold, silver, bronze
    amount_paid = db.Column(db.Float, nullable=False)
    benefits = db.Column(JSONB)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    event = db.relationship("Event", backref="sponsors")
    sponsor = db.relationship("User", backref="event_sponsorships")


# ================================================================
# AI & AUTOMATION
# ================================================================

class AIConversation(db.Model):
    """Store AI chat conversations"""
    __tablename__ = "ai_conversations"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    context = db.Column(JSONB)
    model_used = db.Column(db.String(64))
    tokens_used = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="ai_conversations")


class PredictiveModel(db.Model):
    """Store predictive analytics models"""
    __tablename__ = "predictive_models"
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(128), unique=True, nullable=False)
    model_type = db.Column(db.String(64))  # success_prediction, churn, engagement
    model_data = db.Column(JSONB)
    accuracy_score = db.Column(db.Float)
    last_trained = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())


class UserPrediction(db.Model):
    """Store user-specific predictions"""
    __tablename__ = "user_predictions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    prediction_type = db.Column(db.String(64))
    score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    factors = db.Column(JSONB)
    generated_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="predictions")


class AutomatedTag(db.Model):
    """AI-generated tags for content"""
    __tablename__ = "automated_tags"
    
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(64), nullable=False)  # post, scholarship, event
    resource_id = db.Column(db.Integer, nullable=False)
    tag = db.Column(db.String(64), nullable=False)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=func.now())


# ================================================================
# COMMUNICATION SUITE
# ================================================================

class Message(db.Model):
    """Unified messaging system"""
    __tablename__ = "messages"
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    thread_id = db.Column(db.String(64), index=True)
    attachments = db.Column(JSONB)
    encrypted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_messages")


class CalendarSync(db.Model):
    """Calendar integration tracking"""
    __tablename__ = "calendar_sync"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provider = db.Column(db.String(32), nullable=False)  # google, outlook, ical
    external_calendar_id = db.Column(db.String(255))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    sync_enabled = db.Column(db.Boolean, default=True)
    last_synced = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="calendar_syncs")


class Announcement(db.Model):
    """Department/system announcements"""
    __tablename__ = "announcements"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    priority = db.Column(db.String(20), default="normal")  # low, normal, high, urgent
    target_audience = db.Column(ARRAY(db.String))  # students, faculty, alumni, all
    published_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    author = db.relationship("User", backref="announcements")
    department = db.relationship("Department", backref="announcements")


class Forum(db.Model):
    """Community forums"""
    __tablename__ = "forums"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64))
    is_private = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=func.now())
    
    creator = db.relationship("User", backref="created_forums")


class ForumThread(db.Model):
    """Forum discussion threads"""
    __tablename__ = "forum_threads"
    
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    forum = db.relationship("Forum", backref="threads")
    author = db.relationship("User", backref="forum_threads")


class ForumPost(db.Model):
    """Forum thread replies"""
    __tablename__ = "forum_posts"
    
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("forum_threads.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_post_id = db.Column(db.Integer, db.ForeignKey("forum_posts.id"))
    upvotes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    
    thread = db.relationship("ForumThread", backref="posts")
    author = db.relationship("User", backref="forum_posts")


class Webinar(db.Model):
    """Webinar management"""
    __tablename__ = "webinars"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer)
    meeting_url = db.Column(db.String(512))
    recording_url = db.Column(db.String(512))
    max_participants = db.Column(db.Integer)
    registration_required = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    host = db.relationship("User", backref="hosted_webinars")


class WebinarRegistration(db.Model):
    """Webinar attendee tracking"""
    __tablename__ = "webinar_registrations"
    
    id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey("webinars.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    attended = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=func.now())
    
    webinar = db.relationship("Webinar", backref="registrations")
    user = db.relationship("User", backref="webinar_registrations")


# ================================================================
# SYSTEM ARCHITECTURE
# ================================================================

class FeatureFlag(db.Model):
    """Feature flag management"""
    __tablename__ = "feature_flags"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    rollout_percentage = db.Column(db.Float, default=0.0)
    target_users = db.Column(ARRAY(db.Integer))
    target_roles = db.Column(ARRAY(db.String))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())


class ABTest(db.Model):
    """A/B testing experiments"""
    __tablename__ = "ab_tests"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    variant_a = db.Column(JSONB)
    variant_b = db.Column(JSONB)
    traffic_split = db.Column(db.Float, default=0.5)
    status = db.Column(db.String(32), default="draft")  # draft, running, completed
    winner = db.Column(db.String(1))  # A or B
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())


class ABTestAssignment(db.Model):
    """Track user A/B test assignments"""
    __tablename__ = "ab_test_assignments"
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("ab_tests.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    variant = db.Column(db.String(1), nullable=False)  # A or B
    assigned_at = db.Column(db.DateTime, default=func.now())
    
    test = db.relationship("ABTest", backref="assignments")
    user = db.relationship("User", backref="ab_test_assignments")


class EventLog(db.Model):
    """Event sourcing log"""
    __tablename__ = "event_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(128), nullable=False, index=True)
    aggregate_id = db.Column(db.String(64), index=True)
    aggregate_type = db.Column(db.String(64))
    event_data = db.Column(JSONB, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=func.now(), index=True)
    version = db.Column(db.Integer, default=1)
    
    user = db.relationship("User", backref="event_logs")


class TenantConfig(db.Model):
    """Multi-campus tenancy configuration"""
    __tablename__ = "tenant_configs"
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), unique=True, nullable=False)
    tenant_name = db.Column(db.String(255), nullable=False)
    subdomain = db.Column(db.String(128), unique=True)
    branding = db.Column(JSONB)  # colors, logos, etc.
    features_enabled = db.Column(JSONB)
    database_uri = db.Column(db.String(512))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())


# ================================================================
# INTEGRATIONS
# ================================================================

class ExternalIntegration(db.Model):
    """Track external service integrations"""
    __tablename__ = "external_integrations"
    
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(128), nullable=False)  # Canvas, LinkedIn, etc.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    config = db.Column(JSONB)
    enabled = db.Column(db.Boolean, default=True)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="integrations")


class PaymentTransaction(db.Model):
    """Payment and donation tracking"""
    __tablename__ = "payment_transactions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    transaction_id = db.Column(db.String(128), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="USD")
    payment_method = db.Column(db.String(32))  # stripe, paypal, etc.
    purpose = db.Column(db.String(128))  # donation, sponsorship, premium_subscription
    status = db.Column(db.String(32), default="pending")  # pending, completed, failed, refunded
    meta_data = db.Column(JSONB)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="transactions")


class PushNotificationToken(db.Model):
    """Store push notification tokens"""
    __tablename__ = "push_notification_tokens"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(512), unique=True, nullable=False)
    platform = db.Column(db.String(32))  # ios, android, web
    device_info = db.Column(JSONB)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="push_tokens")


# ================================================================
# DATA GOVERNANCE
# ================================================================

class DataLineage(db.Model):
    """Track data lineage for governance"""
    __tablename__ = "data_lineage"
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_name = db.Column(db.String(128), nullable=False)
    source_system = db.Column(db.String(128))
    transformation_applied = db.Column(db.Text)
    version = db.Column(db.String(32))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=func.now())
    schema_snapshot = db.Column(JSONB)
    
    creator = db.relationship("User", backref="created_datasets")


class BiasMonitoring(db.Model):
    """Monitor for algorithmic bias"""
    __tablename__ = "bias_monitoring"
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(128), nullable=False)
    metric_name = db.Column(db.String(64))
    demographic_group = db.Column(db.String(64))
    metric_value = db.Column(db.Float)
    threshold = db.Column(db.Float)
    alert_triggered = db.Column(db.Boolean, default=False)
    measured_at = db.Column(db.DateTime, default=func.now())


class DataRetention(db.Model):
    """Data retention policy management"""
    __tablename__ = "data_retention"
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(128), nullable=False)
    retention_days = db.Column(db.Integer, nullable=False)
    archive_location = db.Column(db.String(255))  # hot, warm, cold storage
    last_cleanup = db.Column(db.DateTime)
    policy_active = db.Column(db.Boolean, default=True)


# ================================================================
# COMMUNITY & ENGAGEMENT
# ================================================================

class LocalBusiness(db.Model):
    """Local business partners"""
    __tablename__ = "local_businesses"
    
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64))
    description = db.Column(db.Text)
    address = db.Column(db.String(512))
    contact_email = db.Column(db.String(255))
    discount_offered = db.Column(db.String(255))
    logo_url = db.Column(db.String(512))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())


class Badge(db.Model):
    """Gamification badges"""
    __tablename__ = "badges"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(512))
    criteria = db.Column(JSONB)
    points = db.Column(db.Integer, default=0)
    rarity = db.Column(db.String(32))  # common, rare, epic, legendary
    created_at = db.Column(db.DateTime, default=func.now())


class UserBadge(db.Model):
    """User badge awards"""
    __tablename__ = "user_badges"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    awarded_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="earned_badges")
    badge = db.relationship("Badge", backref="user_awards")


class Survey(db.Model):
    """Survey engine"""
    __tablename__ = "surveys"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(JSONB, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    active = db.Column(db.Boolean, default=True)
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now())
    closes_at = db.Column(db.DateTime)
    
    creator = db.relationship("User", backref="created_surveys")


class SurveyResponse(db.Model):
    """Survey responses"""
    __tablename__ = "survey_responses"
    
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    responses = db.Column(JSONB, nullable=False)
    submitted_at = db.Column(db.DateTime, default=func.now())
    
    survey = db.relationship("Survey", backref="responses")
    user = db.relationship("User", backref="survey_responses")


# ================================================================
# MONETIZATION
# ================================================================

class LicenseKey(db.Model):
    """API/Platform license management"""
    __tablename__ = "license_keys"
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    organization = db.Column(db.String(255))
    tier = db.Column(db.String(32))  # free, basic, pro, enterprise
    max_api_calls = db.Column(db.Integer)
    api_calls_used = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())


class Subscription(db.Model):
    """User/organization subscriptions"""
    __tablename__ = "subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    organization_id = db.Column(db.Integer)
    plan_name = db.Column(db.String(64), nullable=False)
    billing_cycle = db.Column(db.String(32))  # monthly, annually
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="USD")
    status = db.Column(db.String(32), default="active")  # active, cancelled, expired
    stripe_subscription_id = db.Column(db.String(128))
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="subscriptions")


# ================================================================
# EDUCATION & RESEARCH
# ================================================================

class MicroCredential(db.Model):
    """Digital micro-credentials"""
    __tablename__ = "micro_credentials"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    issuing_department = db.Column(db.Integer, db.ForeignKey("departments.id"))
    criteria = db.Column(JSONB)
    badge_image_url = db.Column(db.String(512))
    blockchain_verified = db.Column(db.Boolean, default=False)
    blockchain_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=func.now())
    
    department = db.relationship("Department", backref="micro_credentials")


class UserCredential(db.Model):
    """User-earned micro-credentials"""
    __tablename__ = "user_credentials"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    credential_id = db.Column(db.Integer, db.ForeignKey("micro_credentials.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=func.now())
    verification_url = db.Column(db.String(512))
    
    user = db.relationship("User", backref="credentials")
    credential = db.relationship("MicroCredential", backref="user_awards")


class ResearchFunding(db.Model):
    """Research funding opportunities"""
    __tablename__ = "research_funding"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    funding_agency = db.Column(db.String(255))
    amount_available = db.Column(db.Float)
    deadline = db.Column(db.Date)
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    research_areas = db.Column(ARRAY(db.String))
    created_at = db.Column(db.DateTime, default=func.now())


# ================================================================
# MOBILE & ON-SITE
# ================================================================

class QRCheckIn(db.Model):
    """QR code check-in tracking"""
    __tablename__ = "qr_checkins"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    check_in_time = db.Column(db.DateTime, default=func.now())
    location = db.Column(db.String(255))
    geolocation = db.Column(JSONB)  # lat, lng
    
    event = db.relationship("Event", backref="checkins")
    user = db.relationship("User", backref="checkins")


class KioskSession(db.Model):
    """Track kiosk mode sessions"""
    __tablename__ = "kiosk_sessions"
    
    id = db.Column(db.Integer, primary_key=True)
    kiosk_id = db.Column(db.String(64), nullable=False)
    location = db.Column(db.String(255))
    session_start = db.Column(db.DateTime, default=func.now())
    session_end = db.Column(db.DateTime)
    users_served = db.Column(db.Integer, default=0)
    activities = db.Column(JSONB)


# ================================================================
# FUTURE VISION
# ================================================================

class ARContent(db.Model):
    """Augmented Reality campus content"""
    __tablename__ = "ar_content"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    ar_model_url = db.Column(db.String(512))
    media_type = db.Column(db.String(32))  # 3d_model, video, image
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    creator = db.relationship("User", backref="ar_content")


class VoiceCommand(db.Model):
    """Voice assistant command logging"""
    __tablename__ = "voice_commands"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    command_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    intent = db.Column(db.String(64))
    success = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="voice_commands")


class BlockchainCredential(db.Model):
    """Blockchain-verified credentials"""
    __tablename__ = "blockchain_credentials"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    credential_type = db.Column(db.String(64), nullable=False)
    credential_data = db.Column(JSONB)
    blockchain_hash = db.Column(db.String(128), unique=True)
    blockchain_network = db.Column(db.String(32))  # ethereum, polygon, etc.
    transaction_id = db.Column(db.String(128))
    issued_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="blockchain_credentials")


# ================================================================
# SEARCH & DISCOVERY MODELS
# ================================================================

class SearchHistory(db.Model):
    """Track user search history for analytics and suggestions"""
    __tablename__ = "search_history"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    query = db.Column(db.String(512), nullable=False)
    entity_types = db.Column(db.Text)  # JSON array of entity types searched
    result_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=func.now())
    clicked_result_id = db.Column(db.Integer)  # Track which result was clicked
    clicked_result_type = db.Column(db.String(32))  # job, scholarship, event, etc.
    
    user = db.relationship("User", backref="search_history")


class SavedSearch(db.Model):
    """Saved searches with email alerts"""
    __tablename__ = "saved_searches"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    query = db.Column(db.String(512), nullable=False)
    entity_types = db.Column(db.Text)  # JSON array
    filters = db.Column(JSONB)  # Saved filter criteria
    email_alerts = db.Column(db.Boolean, default=False)
    alert_frequency = db.Column(db.String(32), default='daily')  # daily, weekly
    last_alerted = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=func.now())
    
    user = db.relationship("User", backref="saved_searches")


class SearchSuggestion(db.Model):
    """Popular search suggestions"""
    __tablename__ = "search_suggestions"
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(256), unique=True, nullable=False)
    entity_type = db.Column(db.String(32))
    search_count = db.Column(db.Integer, default=1)
    last_searched = db.Column(db.DateTime, default=func.now())


# ================================================================
# VIDEO INTERVIEW MODELS
# ================================================================

class VideoInterview(db.Model):
    """Video interview sessions via Twilio Video"""
    __tablename__ = "video_interviews"
    
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.String(64), unique=True, nullable=False)
    room_sid = db.Column(db.String(128))
    room_name = db.Column(db.String(256), nullable=False)
    
    employer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    candidate_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    scheduled_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    actual_duration_minutes = db.Column(db.Integer)
    
    status = db.Column(db.String(32), default='scheduled')  # scheduled, in_progress, completed, cancelled
    
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    employer_joined_at = db.Column(db.DateTime)
    candidate_joined_at = db.Column(db.DateTime)
    
    recording_url = db.Column(db.String(512))
    recording_duration_seconds = db.Column(db.Integer)
    
    cancelled_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    cancellation_reason = db.Column(db.Text)
    cancelled_at = db.Column(db.DateTime)
    
    rescheduled_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=func.now())
    
    employer = db.relationship("User", foreign_keys=[employer_user_id], backref="employer_interviews")
    candidate = db.relationship("User", foreign_keys=[candidate_user_id], backref="candidate_interviews")


# ================================================================
# LIVE CHAT MODELS
# ================================================================

class ChatRoom(db.Model):
    """Chat rooms for real-time messaging"""
    __tablename__ = "chat_rooms"
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(128), unique=True, nullable=False)
    room_type = db.Column(db.String(32), nullable=False)  # direct, group, support
    room_name = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=func.now())
    is_active = db.Column(db.Boolean, default=True)
    
    messages = db.relationship("ChatMessage", backref="room", lazy=True)
    participants = db.relationship("ChatParticipant", backref="room", lazy=True)


class ChatMessage(db.Model):
    """Chat messages"""
    __tablename__ = "chat_messages"
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(128), db.ForeignKey("chat_rooms.room_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(32), default='text')  # text, image, file, system
    meta_data = db.Column(JSONB)  # For file URLs, image URLs, etc. - Renamed from metadata
    timestamp = db.Column(db.DateTime, default=func.now())
    edited_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="chat_messages")


class ChatParticipant(db.Model):
    """Chat room participants"""
    __tablename__ = "chat_participants"
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=func.now())
    left_at = db.Column(db.DateTime)
    last_read_at = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="chat_participations")



