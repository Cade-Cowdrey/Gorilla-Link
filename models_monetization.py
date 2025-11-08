# Database Models for Employer Monetization Features
# Add these to your models.py file

from extensions import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class EmployerTier(enum.Enum):
    """Employer subscription tiers"""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    PLATINUM = "platinum"

class SubscriptionStatus(enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"

# Add these fields to your existing User/Employer model:
# If you have a separate Employer model, add to that. If employers are Users, add to User model.

class EmployerSubscription(db.Model):
    """Employer subscription and billing information"""
    __tablename__ = 'employer_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Subscription details
    tier = db.Column(db.Enum(EmployerTier), nullable=False, default=EmployerTier.FREE)
    status = db.Column(db.Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    
    # Billing
    stripe_customer_id = db.Column(db.String(255), unique=True, index=True)
    stripe_subscription_id = db.Column(db.String(255), unique=True, index=True)
    stripe_price_id = db.Column(db.String(255))  # Stripe price ID for the plan
    
    # Dates
    subscription_start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    trial_end_date = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Usage tracking
    jobs_posted_this_month = db.Column(db.Integer, default=0)
    profile_views_this_week = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metrics
    total_jobs_posted = db.Column(db.Integer, default=0)
    total_applications_received = db.Column(db.Integer, default=0)
    total_hires = db.Column(db.Integer, default=0)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    
    def __repr__(self):
        return f'<EmployerSubscription {self.user_id} - {self.tier.value}>'
    
    @property
    def is_active(self):
        """Check if subscription is active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    @property
    def job_limit(self):
        """Get job posting limit based on tier"""
        limits = {
            EmployerTier.FREE: 1,
            EmployerTier.PROFESSIONAL: 5,
            EmployerTier.ENTERPRISE: 999,  # Unlimited
            EmployerTier.PLATINUM: 999  # Unlimited
        }
        return limits.get(self.tier, 0)
    
    @property
    def profile_view_limit(self):
        """Get profile view limit based on tier"""
        limits = {
            EmployerTier.FREE: 5,
            EmployerTier.PROFESSIONAL: 999,  # Unlimited
            EmployerTier.ENTERPRISE: 999,
            EmployerTier.PLATINUM: 999
        }
        return limits.get(self.tier, 999)
    
    @property
    def can_post_job(self):
        """Check if employer can post another job"""
        return self.jobs_posted_this_month < self.job_limit
    
    @property
    def can_view_profile(self):
        """Check if employer can view another profile"""
        return self.profile_views_this_week < self.profile_view_limit
    
    @property
    def has_featured_placement(self):
        """Check if tier includes featured placement"""
        return self.tier in [EmployerTier.PROFESSIONAL, EmployerTier.ENTERPRISE, EmployerTier.PLATINUM]
    
    @property
    def has_premium_placement(self):
        """Check if tier includes premium (top 3) placement"""
        return self.tier in [EmployerTier.ENTERPRISE, EmployerTier.PLATINUM]


class ScholarshipSponsorship(db.Model):
    """Company scholarship sponsorships"""
    __tablename__ = 'scholarship_sponsorships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Scholarship details
    name = db.Column(db.String(200), nullable=False)  # e.g., "ABC Corp Tech Scholarship"
    amount = db.Column(db.Integer, nullable=False)  # Dollar amount
    tier = db.Column(db.String(50))  # Bronze, Silver, Gold, Platinum
    
    # Eligibility
    eligibility_criteria = db.Column(db.Text)
    major_restrictions = db.Column(db.String(500))  # JSON or comma-separated
    gpa_requirement = db.Column(db.Float)
    
    # Timeline
    academic_year = db.Column(db.String(20))  # e.g., "2025-2026"
    application_deadline = db.Column(db.DateTime)
    award_date = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(50), default='active')  # active, awarded, expired
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sponsor = db.relationship('User', foreign_keys=[user_id], backref='sponsored_scholarships')
    recipient = db.relationship('User', foreign_keys=[recipient_user_id], backref='received_scholarships')
    
    def __repr__(self):
        return f'<ScholarshipSponsorship {self.name} - ${self.amount}>'


class CareerFairParticipation(db.Model):
    """Employer participation in career fairs"""
    __tablename__ = 'career_fair_participation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Fair details
    fair_name = db.Column(db.String(200), nullable=False)
    fair_date = db.Column(db.DateTime, nullable=False)
    fair_type = db.Column(db.String(50))  # virtual, in-person, hybrid
    
    # Booth tier
    booth_tier = db.Column(db.String(50))  # basic, premium, title_sponsor
    booth_cost = db.Column(db.Integer)
    
    # Payment
    paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    stripe_payment_intent_id = db.Column(db.String(255))
    
    # Engagement metrics
    students_met = db.Column(db.Integer, default=0)
    resumes_collected = db.Column(db.Integer, default=0)
    interviews_scheduled = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    employer = db.relationship('User', backref='career_fair_participations')
    
    def __repr__(self):
        return f'<CareerFairParticipation {self.fair_name} - {self.employer.name}>'


class JobBoost(db.Model):
    """Job post boosts for increased visibility"""
    __tablename__ = 'job_boosts'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Boost details
    boost_type = db.Column(db.String(50))  # 24hr, 7day, 30day
    boost_cost = db.Column(db.Integer)  # Amount paid
    
    # Timeline
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Payment
    stripe_payment_intent_id = db.Column(db.String(255))
    paid = db.Column(db.Boolean, default=False)
    
    # Metrics
    views_during_boost = db.Column(db.Integer, default=0)
    applications_during_boost = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    job = db.relationship('Job', backref='boosts')
    employer = db.relationship('User', backref='job_boosts')
    
    @property
    def is_active(self):
        """Check if boost is currently active"""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date
    
    def __repr__(self):
        return f'<JobBoost {self.job_id} - {self.boost_type}>'


class EmployerBrandingPackage(db.Model):
    """Employer branding packages (videos, testimonials, content)"""
    __tablename__ = 'employer_branding_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Package details
    package_type = db.Column(db.String(50))  # basic, standard, premium
    package_cost = db.Column(db.Integer)
    
    # Content delivered
    company_video_url = db.Column(db.String(500))
    employee_testimonials = db.Column(db.Text)  # JSON array
    social_media_content = db.Column(db.Text)  # JSON array
    custom_company_page = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    
    # Payment
    paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    stripe_payment_intent_id = db.Column(db.String(255))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    employer = db.relationship('User', backref='branding_packages')
    
    def __repr__(self):
        return f'<EmployerBrandingPackage {self.employer.name} - {self.package_type}>'


class RevenueTransaction(db.Model):
    """Track all revenue transactions for reporting"""
    __tablename__ = 'revenue_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(50), nullable=False)  # subscription, scholarship, fair, boost, branding
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    description = db.Column(db.String(500))
    
    # Payment
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    stripe_invoice_id = db.Column(db.String(255))
    payment_status = db.Column(db.String(50), default='pending')  # pending, succeeded, failed, refunded
    
    # Revenue share
    psu_share_amount = db.Column(db.Integer)  # 20% to PSU
    platform_revenue = db.Column(db.Integer)  # 80% platform
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref='revenue_transactions')
    
    def __repr__(self):
        return f'<RevenueTransaction ${self.amount/100} - {self.transaction_type}>'
    
    @staticmethod
    def calculate_psu_share(amount, share_percentage=0.20):
        """Calculate PSU's revenue share"""
        return int(amount * share_percentage)
