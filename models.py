# models.py  (root-level, same folder as app_pro.py)

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# -----------------------------------------------------------
# Core / Auth / Admin
# -----------------------------------------------------------

class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    users = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    verified = db.Column(db.Boolean, default=False)

    role = db.relationship("Role", back_populates="users", lazy="joined")

    # Rich relationships for convenience in templates/admin
    posts = db.relationship("Post", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    scholarship_applications = db.relationship("ScholarshipApplication", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    essays = db.relationship("Essay", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    reminders = db.relationship("Reminder", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    cost_to_completion = db.relationship("CostToCompletion", back_populates="user", uselist=False, cascade="all, delete-orphan")
    funding_journey = db.relationship("FundingJourney", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    # Connections & messages
    sent_connections = db.relationship("Connection", foreign_keys="Connection.user_id", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    received_connections = db.relationship("Connection", foreign_keys="Connection.connected_user_id", back_populates="connected_user", cascade="all, delete-orphan", lazy="dynamic")
    direct_messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan", lazy="dynamic")
    direct_messages_received = db.relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan", lazy="dynamic")

    # Groups & group chat
    group_messages = db.relationship("GroupMessage", back_populates="sender", cascade="all, delete-orphan", lazy="dynamic")
    group_memberships = db.relationship("GroupMember", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    # Notifications & preferences
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    notification_preferences = db.relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    email_logs = db.relationship("EmailLog", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    # Mentorship
    mentorships_as_mentor = db.relationship("Mentorship", foreign_keys="Mentorship.mentor_id", back_populates="mentor", cascade="all, delete-orphan", lazy="dynamic")
    mentorships_as_mentee = db.relationship("Mentorship", foreign_keys="Mentorship.mentee_id", back_populates="mentee", cascade="all, delete-orphan", lazy="dynamic")

    # Badges & portfolio & profile
    user_badges = db.relationship("UserBadge", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    portfolio_projects = db.relationship("PortfolioProject", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    portfolio_links = db.relationship("PortfolioLink", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    profile = db.relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Engagement & opportunities
    engagement_actions = db.relationship("EngagementAction", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    opportunity_applications = db.relationship("OpportunityApplication", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    # Audit/activity
    activity_logs = db.relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def __repr__(self):
        return f"<User {self.email}>"


class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(100))
    metadata = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="activity_logs", lazy="joined")

    def __repr__(self):
        return f"<ActivityLog action={self.action} user={self.user_id}>"


# -----------------------------------------------------------
# Mentorship (mentorship blueprint) & PeerMentor legacy
# -----------------------------------------------------------

class Mentorship(db.Model):
    __tablename__ = "mentorship"
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="active")  # active, paused, completed
    notes = db.Column(db.Text)

    mentor = db.relationship("User", foreign_keys=[mentor_id], back_populates="mentorships_as_mentor", lazy="joined")
    mentee = db.relationship("User", foreign_keys=[mentee_id], back_populates="mentorships_as_mentee", lazy="joined")

    def __repr__(self):
        return f"<Mentorship mentor={self.mentor_id} mentee={self.mentee_id} status={self.status}>"


class PeerMentor(db.Model):
    """Legacy/lightweight pairing used in some older routes."""
    __tablename__ = "peer_mentor"
    id = db.Column(db.Integer, primary_key=True)
    mentor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mentee_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    mentor = db.relationship("User", foreign_keys=[mentor_user_id], backref="legacy_peer_mentees", lazy="joined")
    mentee = db.relationship("User", foreign_keys=[mentee_user_id], backref="legacy_peer_mentors", lazy="joined")


# -----------------------------------------------------------
# Scholarships (scholarships blueprint) + Faculty + Departments
# -----------------------------------------------------------

class Scholarship(db.Model):
    __tablename__ = "scholarship"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    deadline = db.Column(db.Date, index=True)
    department = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)

    applications = db.relationship("ScholarshipApplication", back_populates="scholarship", cascade="all, delete-orphan", lazy="dynamic")


class ScholarshipApplication(db.Model):
    __tablename__ = "scholarship_application"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"), index=True)
    status = db.Column(db.String(32), default="draft")  # draft, submitted, reviewed, awarded, rejected
    progress = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="scholarship_applications", lazy="joined")
    scholarship = db.relationship("Scholarship", back_populates="applications", lazy="joined")


class Essay(db.Model):
    __tablename__ = "essay"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="essays", lazy="joined")


class Reminder(db.Model):
    __tablename__ = "reminder"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    scholarship_id = db.Column(db.Integer, nullable=True)
    due_at = db.Column(db.DateTime, index=True)
    note = db.Column(db.String(255))

    user = db.relationship("User", back_populates="reminders", lazy="joined")


class FinancialLiteracyResource(db.Model):
    __tablename__ = "financial_literacy_resource"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    url = db.Column(db.String(300))
    category = db.Column(db.String(100), index=True)


class CostToCompletion(db.Model):
    __tablename__ = "cost_to_completion"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, index=True)
    estimated_tuition_remaining = db.Column(db.Integer, default=0)
    est_graduation_date = db.Column(db.Date)

    user = db.relationship("User", back_populates="cost_to_completion", lazy="joined")


class FundingJourney(db.Model):
    __tablename__ = "funding_journey"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    step = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="funding_journey", lazy="joined")


class FacultyRecommendation(db.Model):
    __tablename__ = "faculty_recommendation"
    id = db.Column(db.Integer, primary_key=True)
    applicant_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    faculty_name = db.Column(db.String(200))
    file_url = db.Column(db.String(400))

    applicant = db.relationship("User", backref="faculty_recommendations", lazy="joined")


class LeaderboardEntry(db.Model):
    __tablename__ = "leaderboard_entry"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    points = db.Column(db.Integer, default=0, index=True)

    user = db.relationship("User", backref="leaderboard_entries", lazy="joined")


# Departments & Faculty (departments blueprint; analytics uses them too)

class Department(db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True)
    building = db.Column(db.String(150))
    phone = db.Column(db.String(100))
    website = db.Column(db.String(200))

    faculty_members = db.relationship("Faculty", back_populates="department", cascade="all, delete-orphan", lazy="dynamic")


class Faculty(db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), index=True)
    email = db.Column(db.String(120))
    title = db.Column(db.String(120))

    department = db.relationship("Department", back_populates="faculty_members", lazy="joined")


# -----------------------------------------------------------
# Donor / Impact (donor, stories)
# -----------------------------------------------------------

class Donor(db.Model):
    __tablename__ = "donor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    organization = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))

    donations = db.relationship("Donation", back_populates="donor", cascade="all, delete-orphan", lazy="dynamic")


class Donation(db.Model):
    __tablename__ = "donation"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donor.id"), index=True)
    amount = db.Column(db.Integer)
    note = db.Column(db.String(255))
    donated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    donor = db.relationship("Donor", back_populates="donations", lazy="joined")


class ImpactStory(db.Model):
    __tablename__ = "impact_story"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    body = db.Column(db.Text)
    photo_url = db.Column(db.String(400))
    published_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Story(db.Model):
    """stories blueprint general content (student/alumni spotlights)"""
    __tablename__ = "story"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    title = db.Column(db.String(200), index=True)
    body = db.Column(db.Text)
    cover_image_url = db.Column(db.String(400))
    published_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_published = db.Column(db.Boolean, default=True)

    author = db.relationship("User", backref="stories", lazy="joined")


# -----------------------------------------------------------
# Alumni / Careers / Analytics
# -----------------------------------------------------------

class Alumni(db.Model):
    __tablename__ = "alumni"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True)
    graduation_year = db.Column(db.Integer, index=True)
    current_employer = db.Column(db.String(200))
    job_title = db.Column(db.String(150))
    email = db.Column(db.String(120))
    location = db.Column(db.String(120), index=True)


class Job(db.Model):
    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    company = db.Column(db.String(200), index=True)
    location = db.Column(db.String(200))
    posted_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    description = db.Column(db.Text)


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    title = db.Column(db.String(200), index=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="posts", lazy="joined")


class DailyStats(db.Model):
    __tablename__ = "daily_stats"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True, index=True)
    total_logins = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    scholarships_submitted = db.Column(db.Integer, default=0)
    donations_made = db.Column(db.Integer, default=0)


# -----------------------------------------------------------
# Connections / Messaging / Notifications / Groups / Events
# -----------------------------------------------------------

class Connection(db.Model):
    __tablename__ = "connection"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    connected_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(50), default="pending")  # pending, accepted, blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="sent_connections", lazy="joined")
    connected_user = db.relationship("User", foreign_keys=[connected_user_id], back_populates="received_connections", lazy="joined")

    def __repr__(self):
        return f"<Connection {self.user_id} ↔ {self.connected_user_id} ({self.status})>"


class Message(db.Model):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="direct_messages_sent", lazy="joined")
    receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="direct_messages_received", lazy="joined")


class Notification(db.Model):
    __tablename__ = "notification"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    message = db.Column(db.String(255))
    link = db.Column(db.String(255))
    read = db.Column(db.Boolean, default=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="notifications", lazy="joined")


class NotificationPreference(db.Model):
    __tablename__ = "notification_preference"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, index=True)
    email_digest_weekly = db.Column(db.Boolean, default=True)
    email_deadline_reminders = db.Column(db.Boolean, default=True)
    push_new_message = db.Column(db.Boolean, default=True)

    user = db.relationship("User", back_populates="notification_preferences", lazy="joined")


# Groups

class Group(db.Model):
    __tablename__ = "group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    messages = db.relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan", lazy="dynamic")
    members = db.relationship("GroupMember", back_populates="group", cascade="all, delete-orphan", lazy="dynamic")


class GroupMember(db.Model):
    __tablename__ = "group_member"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    role = db.Column(db.String(50), default="member")  # member, admin, owner
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    group = db.relationship("Group", back_populates="members", lazy="joined")
    user = db.relationship("User", back_populates="group_memberships", lazy="joined")


class GroupMessage(db.Model):
    __tablename__ = "group_message"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    group = db.relationship("Group", back_populates="messages", lazy="joined")
    sender = db.relationship("User", back_populates="group_messages", lazy="joined")

    def __repr__(self):
        return f"<GroupMessage group={self.group_id} sender={self.sender_id}>"


# Events

class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    date = db.Column(db.Date, index=True)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)

    rsvps = db.relationship("EventRSVP", back_populates="event", cascade="all, delete-orphan", lazy="dynamic")


class EventRSVP(db.Model):
    __tablename__ = "event_rsvp"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    status = db.Column(db.String(20), default="going")  # going, interested, not_going
    responded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    event = db.relationship("Event", back_populates="rsvps", lazy="joined")
    user = db.relationship("User", backref="event_rsvps", lazy="joined")


# Feed / Announcements

class FeedItem(db.Model):
    __tablename__ = "feed_item"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    pinned = db.Column(db.Boolean, default=False, index=True)

    user = db.relationship("User", backref="feed_items", lazy="joined")


class Announcement(db.Model):
    __tablename__ = "announcement"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_public = db.Column(db.Boolean, default=True)


# -----------------------------------------------------------
# Badges (badges blueprint)
# -----------------------------------------------------------

class Badge(db.Model):
    __tablename__ = "badge"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, index=True)  # e.g., "gorilla-scholar"
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    icon_url = db.Column(db.String(300))

    user_badges = db.relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan", lazy="dynamic")


class UserBadge(db.Model):
    __tablename__ = "user_badge"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"), index=True)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reason = db.Column(db.String(255))

    user = db.relationship("User", back_populates="user_badges", lazy="joined")
    badge = db.relationship("Badge", back_populates="user_badges", lazy="joined")


# -----------------------------------------------------------
# Opportunities (opportunities blueprint)
# -----------------------------------------------------------

class Opportunity(db.Model):
    __tablename__ = "opportunity"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    category = db.Column(db.String(100), index=True)  # internship, research, volunteer
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    deadline = db.Column(db.Date)

    applications = db.relationship("OpportunityApplication", back_populates="opportunity", cascade="all, delete-orphan", lazy="dynamic")


class OpportunityApplication(db.Model):
    __tablename__ = "opportunity_application"
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunity.id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    status = db.Column(db.String(32), default="applied")  # applied, interviewing, offered, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    note = db.Column(db.String(255))

    opportunity = db.relationship("Opportunity", back_populates="applications", lazy="joined")
    user = db.relationship("User", back_populates="opportunity_applications", lazy="joined")


# -----------------------------------------------------------
# Engagement (engagement blueprint)
# -----------------------------------------------------------

class EngagementAction(db.Model):
    __tablename__ = "engagement_action"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    action = db.Column(db.String(100), index=True)  # login, post_like, rsvp, scholarship_submit
    object_type = db.Column(db.String(50))
    object_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="engagement_actions", lazy="joined")


# -----------------------------------------------------------
# Students / Profile (students, profile, portfolio blueprints)
# -----------------------------------------------------------

class StudentProfile(db.Model):
    __tablename__ = "student_profile"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, index=True)
    major = db.Column(db.String(120), index=True)
    minor = db.Column(db.String(120))
    grad_year = db.Column(db.Integer, index=True)
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(300))
    website_url = db.Column(db.String(300))
    linkedin_url = db.Column(db.String(300))
    github_url = db.Column(db.String(300))

    user = db.relationship("User", back_populates="profile", lazy="joined")


class PortfolioProject(db.Model):
    __tablename__ = "portfolio_project"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    title = db.Column(db.String(200), index=True)
    description = db.Column(db.Text)
    project_url = db.Column(db.String(300))
    image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="portfolio_projects", lazy="joined")


class PortfolioLink(db.Model):
    __tablename__ = "portfolio_link"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    label = db.Column(db.String(120))
    url = db.Column(db.String(300))

    user = db.relationship("User", back_populates="portfolio_links", lazy="joined")


# -----------------------------------------------------------
# Campus / Map / Marketing / Emails (campus, map, marketing, emails blueprints)
# -----------------------------------------------------------

class CampusLocation(db.Model):
    __tablename__ = "campus_location"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    category = db.Column(db.String(100), index=True)  # building, parking, dining, service
    description = db.Column(db.Text)


class CampusResource(db.Model):
    __tablename__ = "campus_resource"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True)
    url = db.Column(db.String(300))
    category = db.Column(db.String(100), index=True)  # advising, mental_health, financial_aid
    summary = db.Column(db.Text)


class MarketingLead(db.Model):
    __tablename__ = "marketing_lead"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), index=True)
    name = db.Column(db.String(150))
    source = db.Column(db.String(100), index=True)  # landing_page, newsletter, event
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    notes = db.Column(db.Text)


class EmailLog(db.Model):
    __tablename__ = "email_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    subject = db.Column(db.String(255), index=True)
    template = db.Column(db.String(200))
    to_address = db.Column(db.String(255), index=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(50), default="sent")  # sent, failed
    error = db.Column(db.Text)

    user = db.relationship("User", back_populates="email_logs", lazy="joined")


# -----------------------------------------------------------
# Exports for "from models import *"
# -----------------------------------------------------------

__all__ = [
    # core
    "db", "User", "Role", "ActivityLog",
    # mentorship
    "Mentorship", "PeerMentor",
    # scholarships
    "Scholarship", "ScholarshipApplication", "Essay", "Reminder",
    "FinancialLiteracyResource", "CostToCompletion", "FundingJourney",
    "FacultyRecommendation", "LeaderboardEntry",
    # departments/faculty
    "Department", "Faculty",
    # donor/impact/stories
    "Donor", "Donation", "ImpactStory", "Story",
    # alumni/careers/analytics
    "Alumni", "Job", "Post", "DailyStats",
    # connections/messages/notifications/groups/events/feed
    "Connection", "Message", "Notification", "NotificationPreference",
    "Group", "GroupMember", "GroupMessage",
    "Event", "EventRSVP", "FeedItem", "Announcement",
    # badges
    "Badge", "UserBadge",
    # opportunities
    "Opportunity", "OpportunityApplication",
    # engagement
    "EngagementAction",
    # students/profile/portfolio
    "StudentProfile", "PortfolioProject", "PortfolioLink",
    # campus/map/marketing/emails
    "CampusLocation", "CampusResource", "MarketingLead", "EmailLog",
]
