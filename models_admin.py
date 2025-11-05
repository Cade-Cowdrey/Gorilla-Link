"""
Admin-focused models for platform management and moderation
"""

from extensions import db
from datetime import datetime
from sqlalchemy import Index

# ==================== CONTENT MODERATION ====================
class ModerationQueue(db.Model):
    __tablename__ = 'moderation_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Content Information
    content_type = db.Column(db.String(50), nullable=False, index=True)  # textbook, review, event, material, etc.
    content_id = db.Column(db.Integer, nullable=False)
    content_title = db.Column(db.String(300))
    content_preview = db.Column(db.Text)  # First 200 chars of content
    
    # Reporter/Flagging
    reported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    report_reason = db.Column(db.String(100))  # spam, inappropriate, misleading, etc.
    report_details = db.Column(db.Text)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Content Owner
    content_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Moderation Status
    status = db.Column(db.String(20), default='pending', index=True)  # pending, reviewed, approved, removed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Moderation Action
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    action_taken = db.Column(db.String(50))  # approved, removed, warned, banned
    moderator_notes = db.Column(db.Text)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reported_by_id], backref='reports_made')
    content_owner = db.relationship('User', foreign_keys=[content_owner_id], backref='content_reported')
    moderator = db.relationship('User', foreign_keys=[reviewed_by_id], backref='moderation_actions')
    
    __table_args__ = (
        Index('idx_moderation_status_priority', 'status', 'priority'),
        Index('idx_moderation_content', 'content_type', 'content_id'),
    )


class UserWarning(db.Model):
    __tablename__ = 'user_warnings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Warning Details
    warning_type = db.Column(db.String(50), nullable=False)  # spam, inappropriate_content, harassment, etc.
    severity = db.Column(db.String(20), default='minor')  # minor, moderate, severe
    description = db.Column(db.Text, nullable=False)
    
    # Associated Content
    related_content_type = db.Column(db.String(50))
    related_content_id = db.Column(db.Integer)
    
    # Admin Action
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='warnings_received')
    admin = db.relationship('User', foreign_keys=[issued_by_id], backref='warnings_issued')


class UserBan(db.Model):
    __tablename__ = 'user_bans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Ban Details
    reason = db.Column(db.Text, nullable=False)
    ban_type = db.Column(db.String(20), default='temporary')  # temporary, permanent
    
    # Duration
    banned_at = db.Column(db.DateTime, default=datetime.utcnow)
    banned_until = db.Column(db.DateTime)  # NULL for permanent bans
    
    # Admin
    banned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    lifted_at = db.Column(db.DateTime)
    lifted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lift_reason = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='bans')
    admin = db.relationship('User', foreign_keys=[banned_by_id], backref='bans_issued')
    lifted_by = db.relationship('User', foreign_keys=[lifted_by_id], backref='bans_lifted')


# ==================== PLATFORM ANALYTICS ====================
class DailyAnalytics(db.Model):
    __tablename__ = 'daily_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    
    # User Metrics
    total_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)  # Logged in that day
    returning_users = db.Column(db.Integer, default=0)
    
    # Engagement Metrics
    total_logins = db.Column(db.Integer, default=0)
    total_page_views = db.Column(db.Integer, default=0)
    avg_session_duration = db.Column(db.Integer, default=0)  # seconds
    
    # Feature Usage
    textbook_listings_created = db.Column(db.Integer, default=0)
    textbook_views = db.Column(db.Integer, default=0)
    housing_reviews_created = db.Column(db.Integer, default=0)
    professor_reviews_created = db.Column(db.Integer, default=0)
    events_created = db.Column(db.Integer, default=0)
    event_rsvps = db.Column(db.Integer, default=0)
    materials_uploaded = db.Column(db.Integer, default=0)
    materials_downloaded = db.Column(db.Integer, default=0)
    discount_views = db.Column(db.Integer, default=0)
    
    # Job/Career Activity
    job_applications = db.Column(db.Integer, default=0)
    scholarship_applications = db.Column(db.Integer, default=0)
    
    # Moderation
    reports_submitted = db.Column(db.Integer, default=0)
    content_removed = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeatureAnalytics(db.Model):
    __tablename__ = 'feature_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Feature Information
    feature_name = db.Column(db.String(50), nullable=False, index=True)  # textbook_exchange, housing_reviews, etc.
    metric_name = db.Column(db.String(50), nullable=False)  # views, posts, searches, etc.
    
    # Time Period
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer)  # 0-23 for hourly tracking
    
    # Metrics
    count = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_feature_date', 'feature_name', 'date'),
        Index('idx_feature_metric', 'feature_name', 'metric_name', 'date'),
    )


# ==================== ANNOUNCEMENT SYSTEM ====================
class AdminAnnouncement(db.Model):
    __tablename__ = 'admin_announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Announcement Content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(50), default='info')  # info, warning, success, urgent
    
    # Targeting
    target_audience = db.Column(db.String(50), default='all')  # all, students, alumni, faculty
    is_dismissible = db.Column(db.Boolean, default=True)
    
    # Display Settings
    display_on_homepage = db.Column(db.Boolean, default=True)
    display_as_banner = db.Column(db.Boolean, default=False)
    display_as_popup = db.Column(db.Boolean, default=False)
    
    # Scheduling
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Creator
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stats
    view_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    
    # Relationships
    creator = db.relationship('User', backref='announcements_created')


class AnnouncementView(db.Model):
    __tablename__ = 'announcement_views'
    
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('admin_announcements.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    dismissed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        Index('idx_announcement_user', 'announcement_id', 'user_id'),
    )


# ==================== BULK OPERATIONS ====================
class BulkOperation(db.Model):
    __tablename__ = 'bulk_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Operation Details
    operation_type = db.Column(db.String(50), nullable=False)  # bulk_delete, bulk_approve, bulk_email, etc.
    target_type = db.Column(db.String(50), nullable=False)  # users, textbooks, reviews, etc.
    description = db.Column(db.Text)
    
    # Parameters (JSON)
    parameters = db.Column(db.Text)  # Stored as JSON string
    
    # Execution
    status = db.Column(db.String(20), default='pending', index=True)  # pending, running, completed, failed
    initiated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Results
    total_items = db.Column(db.Integer, default=0)
    processed_items = db.Column(db.Integer, default=0)
    successful_items = db.Column(db.Integer, default=0)
    failed_items = db.Column(db.Integer, default=0)
    
    error_log = db.Column(db.Text)
    
    # Relationships
    admin = db.relationship('User', backref='bulk_operations')


# ==================== SYSTEM HEALTH MONITORING ====================
class SystemHealthLog(db.Model):
    __tablename__ = 'system_health_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # System Metrics
    cpu_usage = db.Column(db.Numeric(5, 2))  # Percentage
    memory_usage = db.Column(db.Numeric(5, 2))  # Percentage
    disk_usage = db.Column(db.Numeric(5, 2))  # Percentage
    
    # Database Metrics
    db_connections = db.Column(db.Integer)
    db_query_time_avg = db.Column(db.Integer)  # milliseconds
    db_size_mb = db.Column(db.Integer)
    
    # Application Metrics
    active_sessions = db.Column(db.Integer)
    requests_per_minute = db.Column(db.Integer)
    error_rate = db.Column(db.Numeric(5, 2))  # Percentage
    avg_response_time = db.Column(db.Integer)  # milliseconds
    
    # Status
    overall_status = db.Column(db.String(20), default='healthy')  # healthy, degraded, critical


class ErrorLog(db.Model):
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Error Information
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    error_type = db.Column(db.String(100), nullable=False, index=True)
    error_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)
    
    # Context
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    request_url = db.Column(db.String(500))
    request_method = db.Column(db.String(10))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    # Severity
    severity = db.Column(db.String(20), default='error')  # debug, info, warning, error, critical
    
    # Resolution
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolution_notes = db.Column(db.Text)
    
    __table_args__ = (
        Index('idx_error_type_time', 'error_type', 'timestamp'),
        Index('idx_error_severity', 'severity', 'resolved'),
    )


# ==================== FEATURE FLAGS ====================
class FeatureFlag(db.Model):
    __tablename__ = 'feature_flags'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Feature Information
    feature_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Status
    is_enabled = db.Column(db.Boolean, default=False, index=True)
    
    # Rollout
    rollout_percentage = db.Column(db.Integer, default=0)  # 0-100 for gradual rollout
    target_users = db.Column(db.Text)  # JSON array of user IDs for testing
    
    # Management
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    modifier = db.relationship('User', backref='feature_flags_modified')


# ==================== USER VERIFICATION REQUESTS ====================
class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Request Type
    verification_type = db.Column(db.String(50), nullable=False)  # student, alumni, faculty, employer
    
    # Documentation
    document_url = db.Column(db.String(500))  # Student ID, diploma, etc.
    additional_info = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Review
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='verification_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id], backref='verifications_reviewed')


# ==================== EXPORT REQUESTS ====================
class DataExportRequest(db.Model):
    __tablename__ = 'data_export_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Request Details
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    export_type = db.Column(db.String(50), nullable=False)  # users, analytics, textbooks, all_data
    export_format = db.Column(db.String(20), default='csv')  # csv, excel, json
    
    # Filters (JSON)
    filters = db.Column(db.Text)  # Date ranges, user types, etc.
    
    # Status
    status = db.Column(db.String(20), default='pending', index=True)  # pending, processing, completed, failed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Processing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Result
    file_url = db.Column(db.String(500))  # URL to download
    file_size_mb = db.Column(db.Numeric(10, 2))
    expires_at = db.Column(db.DateTime)  # Auto-delete after 7 days
    
    error_message = db.Column(db.Text)
    
    # Relationships
    requester = db.relationship('User', backref='export_requests')
