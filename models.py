# models.py  — PittState-Connect (Gorilla-Link)
# Pure models only: no seeders, no CLI, no app factory code.
# Compatible with: Flask-SQLAlchemy 3.1.x, SQLAlchemy 2.0.x

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Any, Dict

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    func,
    UniqueConstraint,
    Index,
    ForeignKey,
    CheckConstraint,
    JSON,
    text,
)

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Utility mixins
# ---------------------------------------------------------------------------

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), index=True)

class PKMixin:
    id = db.Column(db.Integer, primary_key=True)

# ---------------------------------------------------------------------------
# Identity & org structure
# ---------------------------------------------------------------------------

class Role(PKMixin, db.Model):
    __tablename__ = "roles"
    name = db.Column(db.String(64), unique=True, nullable=False)  # e.g., admin, student, alumni, faculty, employer
    description = db.Column(db.String(255))

    users = db.relationship("User", back_populates="role", lazy="dynamic")

class Department(PKMixin, db.Model):
    __tablename__ = "departments"
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)  # e.g., CSIS
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)

    users = db.relationship("User", back_populates="department", lazy="dynamic")
    jobs = db.relationship("Job", back_populates="department", lazy="dynamic")
    events = db.relationship("Event", back_populates="department", lazy="dynamic")

class User(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    # Core identity
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)

    # Profile
    headline = db.Column(db.String(160))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    banner_url = db.Column(db.String(500))

    # Status/roles
    is_active = db.Column(db.Boolean, nullable=False, server_default=text("true"), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="SET NULL"), index=True)
    dept_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), index=True)

    # Contact
    phone = db.Column(db.String(32))
    location = db.Column(db.String(160))

    # Relationships
    role = db.relationship("Role", back_populates="users")
    department = db.relationship("Department", back_populates="users")

    # Convenience
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

# Student/Faculty/Alumni facets as 1–to–1 “profiles” hanging off User
class Student(PKMixin, db.Model):
    __tablename__ = "students"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    major = db.Column(db.String(120))
    minor = db.Column(db.String(120))
    grad_year = db.Column(db.Integer, index=True)

    user = db.relationship("User", backref=db.backref("student_profile", uselist=False, cascade="all, delete"))

class Faculty(PKMixin, db.Model):
    __tablename__ = "faculty"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = db.Column(db.String(120))  # e.g., Assistant Professor
    office = db.Column(db.String(120))
    research_interests = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("faculty_profile", uselist=False, cascade="all, delete"))

class Alumni(PKMixin, db.Model):
    __tablename__ = "alumni"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    grad_year = db.Column(db.Integer, index=True)
    current_company = db.Column(db.String(160))
    current_title = db.Column(db.String(160))

    user = db.relationship("User", backref=db.backref("alumni_profile", uselist=False, cascade="all, delete"))

# ---------------------------------------------------------------------------
# Careers / Opportunities
# ---------------------------------------------------------------------------

class Employer(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "employers"
    name = db.Column(db.String(160), nullable=False, unique=True)
    website = db.Column(db.String(255))
    logo_url = db.Column(db.String(500))
    description = db.Column(db.Text)

    jobs = db.relationship("Job", back_populates="employer", lazy="dynamic")

class Job(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "jobs"
    title = db.Column(db.String(160), nullable=False, index=True)
    description = db.Column(db.Text)
    job_type = db.Column(db.String(50), index=True)  # e.g., full_time, part_time, internship
    is_remote = db.Column(db.Boolean, nullable=False, server_default=text("false"))
    location = db.Column(db.String(160))

    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id", ondelete="SET NULL"), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), index=True)
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)

    employer = db.relationship("Employer", back_populates="jobs")
    department = db.relationship("Department", back_populates="jobs")
    posted_by = db.relationship("User", backref=db.backref("jobs_posted", lazy="dynamic"))

    applications = db.relationship("Application", back_populates="job", cascade="all, delete-orphan", lazy="dynamic")

class Application(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "applications"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, server_default="submitted", index=True)  # submitted, reviewing, interview, offer, rejected
    resume_url = db.Column(db.String(500))
    cover_letter_url = db.Column(db.String(500))

    user = db.relationship("User", backref=db.backref("applications", lazy="dynamic", cascade="all, delete-orphan"))
    job = db.relationship("Job", back_populates="applications")

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),)

# A generic “opportunity” for non-job postings (competitions, grants, etc.)
class Opportunity(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "opportunities"
    title = db.Column(db.String(200), nullable=False, index=True)
    summary = db.Column(db.Text)
    category = db.Column(db.String(64), index=True)  # e.g., grant, competition, fellowship
    link_url = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), index=True)

    owner = db.relationship("User", backref=db.backref("opportunities", lazy="dynamic"))
    department = db.relationship("Department", backref=db.backref("opportunities", lazy="dynamic"))

# ---------------------------------------------------------------------------
# Social / Feed / Groups / Connections / Mentorship
# ---------------------------------------------------------------------------

class Post(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "posts"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    visibility = db.Column(db.String(32), nullable=False, server_default="public", index=True)  # public, campus, connections, private

    user = db.relationship("User", backref=db.backref("posts", lazy="dynamic", cascade="all, delete-orphan"))
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")
    likes = db.relationship("Like", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")

class Comment(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "comments"
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)

    post = db.relationship("Post", back_populates="comments")
    user = db.relationship("User", backref=db.backref("comments", lazy="dynamic", cascade="all, delete-orphan"))

class Like(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "likes"
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    post = db.relationship("Post", back_populates="likes")
    user = db.relationship("User", backref=db.backref("likes", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),)

class Group(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "groups"
    name = db.Column(db.String(160), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    privacy = db.Column(db.String(32), nullable=False, server_default="public", index=True)  # public, private
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)

    owner = db.relationship("User", backref=db.backref("groups_owned", lazy="dynamic"))
    memberships = db.relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan", lazy="dynamic")
    messages = db.relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan", lazy="dynamic")

class GroupMembership(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "group_memberships"
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(32), nullable=False, server_default="member", index=True)  # member, moderator, owner

    group = db.relationship("Group", back_populates="memberships")
    user = db.relationship("User", backref=db.backref("group_memberships", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

class GroupMessage(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "group_messages"
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)

    group = db.relationship("Group", back_populates="messages")
    user = db.relationship("User", backref=db.backref("group_messages", lazy="dynamic", cascade="all, delete-orphan"))

class Connection(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "connections"
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, server_default="pending", index=True)  # pending, accepted, blocked

    requester = db.relationship("User", foreign_keys=[requester_id], backref=db.backref("connections_sent", lazy="dynamic", cascade="all, delete-orphan"))
    addressee = db.relationship("User", foreign_keys=[addressee_id], backref=db.backref("connections_received", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("requester_id", "addressee_id", name="uq_connection_pair"),)

class Mentorship(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "mentorships"
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, server_default="active", index=True)  # active, paused, ended
    started_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    ended_at = db.Column(db.DateTime)

    mentor = db.relationship("User", foreign_keys=[mentor_id], backref=db.backref("mentees", lazy="dynamic", cascade="all, delete-orphan"))
    mentee = db.relationship("User", foreign_keys=[mentee_id], backref=db.backref("mentors", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("mentor_id", "mentee_id", name="uq_mentorship_pair"),)

# ---------------------------------------------------------------------------
# Events / Calendaring
# ---------------------------------------------------------------------------

class Event(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "events"
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False, index=True)

    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), index=True)

    creator = db.relationship("User", backref=db.backref("events_created", lazy="dynamic"))
    department = db.relationship("Department", back_populates="events")
    attendees = db.relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan", lazy="dynamic")

class EventAttendee(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "event_attendees"
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, server_default="going", index=True)  # going, interested, declined

    event = db.relationship("Event", back_populates="attendees")
    user = db.relationship("User", backref=db.backref("event_attendances", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_user"),)

# ---------------------------------------------------------------------------
# Notifications / Emails / Marketing
# ---------------------------------------------------------------------------

class Notification(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "notifications"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notif_type = db.Column(db.String(64), nullable=False, index=True)  # e.g., new_comment, new_connection, digest
    payload = db.Column(JSON)  # small structured blob
    is_read = db.Column(db.Boolean, nullable=False, server_default=text("false"), index=True)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

class EmailTemplate(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "email_templates"
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)  # e.g., WEEKLY_STUDENT_DIGEST
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)

class MarketingCampaign(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "marketing_campaigns"
    name = db.Column(db.String(160), nullable=False)
    channel = db.Column(db.String(64), nullable=False, index=True)  # email, push, social
    sent_at = db.Column(db.DateTime)
    metrics = db.Column(JSON)  # store open/click/ctr safely here (NOT named 'metadata')

# ---------------------------------------------------------------------------
# Scholarships / Donors
# ---------------------------------------------------------------------------

class Donor(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "donors"
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255))
    organization = db.Column(db.String(160))

    donations = db.relationship("Donation", back_populates="donor", lazy="dynamic")
    scholarships = db.relationship("Scholarship", back_populates="donor", lazy="dynamic")

class Donation(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "donations"
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    note = db.Column(db.String(255))

    donor = db.relationship("Donor", back_populates="donations")

class Scholarship(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "scholarships"
    name = db.Column(db.String(200), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Date, index=True)

    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id", ondelete="SET NULL"), index=True)
    donor = db.relationship("Donor", back_populates="scholarships")

    applications = db.relationship("ScholarshipApplication", back_populates="scholarship", cascade="all, delete-orphan", lazy="dynamic")

class ScholarshipApplication(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "scholarship_applications"
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, server_default="submitted", index=True)  # submitted, under_review, awarded, rejected

    essay_url = db.Column(db.String(500))
    extra = db.Column(JSON)

    scholarship = db.relationship("Scholarship", back_populates="applications")
    user = db.relationship("User", backref=db.backref("scholarship_applications", lazy="dynamic", cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint("scholarship_id", "user_id", name="uq_scholarship_user"),)

# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

class PortfolioProject(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "portfolio_projects"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    tags = db.Column(db.String(255))  # comma-separated for simplicity

    user = db.relationship("User", backref=db.backref("portfolio_projects", lazy="dynamic", cascade="all, delete-orphan"))

# ---------------------------------------------------------------------------
# Badges / Engagement
# ---------------------------------------------------------------------------

class Badge(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "badges"
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)  # e.g., GORILLA_AMBASSADOR
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(500))

    awards = db.relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan", lazy="dynamic")

class UserBadge(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "user_badges"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    user = db.relationship("User", backref=db.backref("badges", lazy="dynamic", cascade="all, delete-orphan"))
    badge = db.relationship("Badge", back_populates="awards")

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

# ---------------------------------------------------------------------------
# Analytics / Admin
# ---------------------------------------------------------------------------

class ActivityLog(PKMixin, db.Model):
    """
    Tracks user/admin actions for analytics & audit.
    NOTE: we intentionally avoid a column named 'metadata' (reserved).
    """
    __tablename__ = "activity_logs"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action = db.Column(db.String(120), nullable=False, index=True)  # e.g., LOGIN, CREATE_POST
    entity_type = db.Column(db.String(120), index=True)            # e.g., Post, Job
    entity_id = db.Column(db.Integer, index=True)
    details = db.Column(JSON)                                      # small structured blob
    ip = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), index=True)

    user = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic"))

    __table_args__ = (
        Index("ix_activity_entity", "entity_type", "entity_id"),
    )

class DailyStats(PKMixin, db.Model):
    __tablename__ = "daily_stats"
    stat_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    users_count = db.Column(db.Integer, nullable=False, server_default=text("0"))
    jobs_posted = db.Column(db.Integer, nullable=False, server_default=text("0"))
    posts_count = db.Column(db.Integer, nullable=False, server_default=text("0"))
    events_count = db.Column(db.Integer, nullable=False, server_default=text("0"))

# ---------------------------------------------------------------------------
# Map / Campus (basic placeholders that some blueprints expect)
# ---------------------------------------------------------------------------

class CampusBuilding(PKMixin, db.Model):
    __tablename__ = "campus_buildings"
    name = db.Column(db.String(160), nullable=False, unique=True)
    code = db.Column(db.String(32), unique=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

class CampusPlace(PKMixin, db.Model):
    __tablename__ = "campus_places"
    building_id = db.Column(db.Integer, db.ForeignKey("campus_buildings.id", ondelete="SET NULL"), index=True)
    name = db.Column(db.String(160), nullable=False)
    floor = db.Column(db.String(32))
    room = db.Column(db.String(32))

    building = db.relationship("CampusBuilding", backref=db.backref("places", lazy="dynamic"))

# ---------------------------------------------------------------------------
# Stories / Marketing content (for feed/stories blueprint)
# ---------------------------------------------------------------------------

class Story(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "stories"
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    cover_image_url = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, nullable=False, server_default=text("false"), index=True)
    published_at = db.Column(db.DateTime)

    author = db.relationship("User", backref=db.backref("stories", lazy="dynamic"))

# ---------------------------------------------------------------------------
# Profiles (extended fields referenced by profile blueprint)
# ---------------------------------------------------------------------------

class ProfileLink(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "profile_links"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = db.Column(db.String(80), nullable=False)  # e.g., LinkedIn, GitHub
    url = db.Column(db.String(500), nullable=False)

    user = db.relationship("User", backref=db.backref("profile_links", lazy="dynamic", cascade="all, delete-orphan"))

class ProfileExperience(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "profile_experiences"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(160))
    location = db.Column(db.String(160))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("experiences", lazy="dynamic", cascade="all, delete-orphan"))

class ProfileEducation(PKMixin, TimestampMixin, db.Model):
    __tablename__ = "profile_education"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school = db.Column(db.String(160), nullable=False)
    degree = db.Column(db.String(160))
    field_of_study = db.Column(db.String(160))
    start_year = db.Column(db.Integer)
    end_year = db.Column(db.Integer)
    description = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("education", lazy="dynamic", cascade="all, delete-orphan"))

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Core
    "db", "User", "Role", "Department", "Student", "Faculty", "Alumni",
    # Careers
    "Employer", "Job", "Application", "Opportunity",
    # Social
    "Post", "Comment", "Like", "Group", "GroupMembership", "GroupMessage",
    "Connection", "Mentorship",
    # Events
    "Event", "EventAttendee",
    # Notifications/Emails/Marketing
    "Notification", "EmailTemplate", "MarketingCampaign",
    # Scholarships/Donors
    "Donor", "Donation", "Scholarship", "ScholarshipApplication",
    # Portfolio
    "PortfolioProject",
    # Badges/Engagement
    "Badge", "UserBadge",
    # Analytics/Admin
    "ActivityLog", "DailyStats",
    # Campus/Map
    "CampusBuilding", "CampusPlace",
    # Stories/Feed
    "Story",
    # Profile
    "ProfileLink", "ProfileExperience", "ProfileEducation",
]
