# models.py
"""
PittState-Connect | Unified SQLAlchemy models
---------------------------------------------

This module centralizes ALL database models used across blueprints:
admin, alumni, analytics, api, auth, badges, campus, careers, connections,
core, departments, digests, donor, emails, engagement, events, feed, groups,
map, marketing, mentorship, notifications, opportunities, portfolio, profile,
scholarships, stories, students.

Key choices:
- Role table (Option B): normalized roles/permissions via Role model.
- LinkedIn-style mutual connections:
    * A 'Connection' is a single row representing a request from requester -> addressee.
    * status in {'pending','accepted','blocked'}.
    * Uniqueness enforced on (requester_id, addressee_id). For symmetry, app logic
      should also check the reverse direction before insert/update.
- All foreign keys/relations set with sensible cascade rules.
- Timestamps and soft-boolean flags where useful.
- Avoids SQLAlchemy reserved names (e.g., use 'extra_json' instead of 'metadata').

Import pattern expected by blueprints:
    from models import db, User, Connection, ...
"""

from __future__ import annotations
import enum
from datetime import datetime, date
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Index,
    UniqueConstraint,
    CheckConstraint,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

# Global database handle for app factories to initialize.
db = SQLAlchemy()


# ---------- Mixins & Enums ----------

class TimestampMixin:
    """Adds created_at / updated_at columns."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)


class VisibilityEnum(enum.Enum):
    public = "public"
    campus = "campus"
    private = "private"


class ConnectionStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    blocked = "blocked"


# ---------- Roles & Users ----------

class Role(db.Model, TimestampMixin):
    """
    Normalized role table (Option B).
    Example rows: 'student', 'alumni', 'faculty', 'admin', 'moderator'.
    """
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(32), unique=True, nullable=False)  # machine key (e.g., 'student')
    name = db.Column(db.String(64), nullable=False)               # human label (e.g., 'Student')
    description = db.Column(db.String(255))
    # Optional permissions blob for quick feature flags.
    permissions = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Role {self.slug}>"


class Department(db.Model, TimestampMixin):
    """
    Academic departments (e.g., Kelce College of Business, Tech & Workforce Learning).
    """
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)  # e.g., 'KELCE'
    name = db.Column(db.String(128), unique=True, nullable=False)
    college = db.Column(db.String(128))  # optional college/school
    website = db.Column(db.String(255))
    extra_json = db.Column(JSONB, default=dict)

    faculty = db.relationship("Faculty", back_populates="department", cascade="all,delete")
    students = db.relationship("Student", back_populates="department", cascade="all,delete")
    alumni = db.relationship("Alumni", back_populates="department", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<Department {self.code}>"


class User(db.Model, TimestampMixin):
    """
    Base user account. Roles and person-type models (Student/Alumni/Faculty) hang off this.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    headline = db.Column(db.String(140))       # profile tagline
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="SET NULL"))
    role = db.relationship("Role", backref=db.backref("users", lazy="dynamic"))

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    department = db.relationship("Department", backref=db.backref("users", lazy="dynamic"))

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    extra_json = db.Column(JSONB, default=dict)

    # Relationships commonly used across blueprints
    posts = db.relationship("Post", back_populates="author", cascade="all,delete")
    jobs = db.relationship("Job", back_populates="poster", cascade="all,delete")
    notifications = db.relationship("Notification", back_populates="user", cascade="all,delete")
    activities = db.relationship("ActivityLog", back_populates="user", cascade="all,delete")
    analytics = db.relationship("UserAnalytics", uselist=False, back_populates="user", cascade="all,delete")

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ---------- Person-Type Models ----------

class Student(db.Model, TimestampMixin):
    """
    Student profile (linked to User).
    """
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False, cascade="all,delete"))

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    department = db.relationship("Department", back_populates="students")

    grad_year = db.Column(db.Integer, index=True)
    major = db.Column(db.String(128))
    minor = db.Column(db.String(128))
    gpa = db.Column(db.Numeric(3, 2))
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Student {self.user_id}>"


class Alumni(db.Model, TimestampMixin):
    """
    Alumni profile with employment history.
    """
    __tablename__ = "alumni"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = db.relationship("User", backref=db.backref("alumni_profile", uselist=False, cascade="all,delete"))

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    department = db.relationship("Department", back_populates="alumni")

    grad_year = db.Column(db.Integer, index=True)
    degree = db.Column(db.String(128))
    current_title = db.Column(db.String(128))
    current_company = db.Column(db.String(128))
    extra_json = db.Column(JSONB, default=dict)

    employments = db.relationship("AlumniEmployment", back_populates="alumni", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<Alumni {self.user_id}>"


class Faculty(db.Model, TimestampMixin):
    """
    Faculty profile.
    """
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = db.relationship("User", backref=db.backref("faculty_profile", uselist=False, cascade="all,delete"))

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    department = db.relationship("Department", back_populates="faculty")

    title = db.Column(db.String(128))  # e.g., Associate Professor
    office = db.Column(db.String(128))
    research_interests = db.Column(db.Text)
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Faculty {self.user_id}>"


# ---------- Employment ----------

class Company(db.Model, TimestampMixin):
    """
    Company catalog record for jobs and alumni employment.
    """
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False, index=True)
    website = db.Column(db.String(255))
    hq_city = db.Column(db.String(120))
    hq_state = db.Column(db.String(120))
    extra_json = db.Column(JSONB, default=dict)

    employments = db.relationship("AlumniEmployment", back_populates="company", cascade="all,delete")
    jobs = db.relationship("Job", back_populates="company", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


class AlumniEmployment(db.Model, TimestampMixin):
    """
    Alumni employment history.
    """
    __tablename__ = "alumni_employments"

    id = db.Column(db.Integer, primary_key=True)
    alumni_id = db.Column(db.Integer, db.ForeignKey("alumni.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="SET NULL"))
    company = db.relationship("Company", back_populates="employments")
    alumni = db.relationship("Alumni", back_populates="employments")

    title = db.Column(db.String(160))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_current = db.Column(db.Boolean, default=False, nullable=False)
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<AlumniEmployment alumni={self.alumni_id} company={self.company_id}>"


# ---------- Social / Content ----------

class Post(db.Model, TimestampMixin):
    """
    User posts (feed).
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    author = db.relationship("User", back_populates="posts")

    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.Enum(VisibilityEnum), default=VisibilityEnum.campus, nullable=False)
    like_count = db.Column(db.Integer, default=0, nullable=False)
    comment_count = db.Column(db.Integer, default=0, nullable=False)
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Post {self.id}>"


class Event(db.Model, TimestampMixin):
    """
    Campus & alumni events.
    """
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(255))
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    organizer = db.relationship("User", backref=db.backref("organized_events", lazy="dynamic"))
    visibility = db.Column(db.Enum(VisibilityEnum), default=VisibilityEnum.campus, nullable=False)
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Event {self.title}>"


class Group(db.Model, TimestampMixin):
    """
    Interest or department-based group.
    """
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    owner = db.relationship("User", backref=db.backref("owned_groups", lazy="dynamic"))
    extra_json = db.Column(JSONB, default=dict)

    members = db.relationship(
        "User",
        secondary="group_members",
        backref=db.backref("groups", lazy="dynamic"),
        passive_deletes=True,
    )
    messages = db.relationship("GroupMessage", back_populates="group", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


group_members = db.Table(
    "group_members",
    db.Column("group_id", db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("joined_at", db.DateTime, default=datetime.utcnow, nullable=False),
    db.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
)


class GroupMessage(db.Model, TimestampMixin):
    """
    Messages inside a Group (simple text chat).
    """
    __tablename__ = "group_messages"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    group = db.relationship("Group", back_populates="messages")
    sender = db.relationship("User")

    body = db.Column(db.Text, nullable=False)

    def __repr__(self) -> str:
        return f"<GroupMessage g={self.group_id} id={self.id}>"


# ---------- Careers ----------

class Job(db.Model, TimestampMixin):
    """
    Jobs & internships.
    """
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="SET NULL"))
    company = db.relationship("Company", back_populates="jobs")

    poster_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    poster = db.relationship("User", back_populates="jobs")

    location = db.Column(db.String(160))
    is_remote = db.Column(db.Boolean, default=False, nullable=False)
    apply_url = db.Column(db.String(255))
    extra_json = db.Column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Job {self.title}>"


# ---------- Scholarships ----------

class Scholarship(db.Model, TimestampMixin):
    """
    Scholarships with simple lifecycle & visibility.
    """
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)  # in USD
    opens_on = db.Column(db.Date)
    closes_on = db.Column(db.Date)
    visibility = db.Column(db.Enum(VisibilityEnum), default=VisibilityEnum.campus, nullable=False)
    extra_json = db.Column(JSONB, default=dict)

    applications = db.relationship("ScholarshipApplication", back_populates="scholarship", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<Scholarship {self.title}>"


class ScholarshipApplication(db.Model, TimestampMixin):
    """
    Student applications for scholarships.
    """
    __tablename__ = "scholarship_applications"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    scholarship = db.relationship("Scholarship", back_populates="applications")
    applicant = db.relationship("User")

    status = db.Column(db.String(32), default="submitted", nullable=False)  # submitted, shortlisted, awarded, rejected
    essay_text = db.Column(db.Text)
    extra_json = db.Column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("scholarship_id", "applicant_id", name="uq_scholarship_applicant"),
    )

    def __repr__(self) -> str:
        return f"<ScholarshipApplication {self.id}>"


# ---------- Storytelling / Badges / Opportunities ----------

class Story(db.Model, TimestampMixin):
    """
    Success stories and impact narratives.
    """
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    author = db.relationship("User", backref=db.backref("stories", lazy="dynamic"))
    cover_image_url = db.Column(db.String(255))
    extra_json = db.Column(JSONB, default=dict)


class Badge(db.Model, TimestampMixin):
    """
    Recognition badges (e.g., 'Mentor', 'Donor', 'Dean's List').
    """
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    icon_url = db.Column(db.String(255))


user_badges = db.Table(
    "user_badges",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("badge_id", db.Integer, db.ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True),
    db.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
)


class Opportunity(db.Model, TimestampMixin):
    """
    Misc opportunities: research, volunteering, campus projects.
    """
    __tablename__ = "opportunities"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    posted_by = db.relationship("User", backref=db.backref("opportunities", lazy="dynamic"))
    extra_json = db.Column(JSONB, default=dict)


# ---------- Donor & Giving ----------

class Donor(db.Model, TimestampMixin):
    """
    Donor profile (individual or organization).
    """
    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    email = db.Column(db.String(255))
    organization = db.Column(db.String(160))
    website = db.Column(db.String(255))
    extra_json = db.Column(JSONB, default=dict)

    donations = db.relationship("Donation", back_populates="donor", cascade="all,delete")


class Donation(db.Model, TimestampMixin):
    """
    Donation record (optionally linked to scholarship).
    """
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, index=True)
    donor = db.relationship("Donor", back_populates="donations")

    amount = db.Column(db.Integer, nullable=False)  # in USD
    designated_scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="SET NULL"))
    designated_scholarship = db.relationship("Scholarship")

    message = db.Column(db.Text)
    extra_json = db.Column(JSONB, default=dict)


class FundingJourney(db.Model, TimestampMixin):
    """
    Tracks scholarship funding progress (sum of donations, commitments).
    """
    __tablename__ = "funding_journeys"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False)
    scholarship = db.relationship("Scholarship")

    target_amount = db.Column(db.Integer, nullable=False)
    raised_amount = db.Column(db.Integer, default=0, nullable=False)
    extra_json = db.Column(JSONB, default=dict)


# ---------- Connections (LinkedIn-style mutual) ----------

class Connection(db.Model, TimestampMixin):
    """
    LinkedIn-style mutual connections.

    A single row represents a request from requester -> addressee.
    - pending: sent but not accepted
    - accepted: both users are now 'connected'
    - blocked: blocked by one side

    Uniqueness is enforced on (requester_id, addressee_id).
    App logic should also avoid creating the reverse duplicate.
    """
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)

    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    requester = db.relationship("User", foreign_keys=[requester_id], backref=db.backref("sent_connections", cascade="all,delete"))
    addressee = db.relationship("User", foreign_keys=[addressee_id], backref=db.backref("received_connections", cascade="all,delete"))

    status = db.Column(db.Enum(ConnectionStatus), nullable=False, default=ConnectionStatus.pending)
    responded_at = db.Column(db.DateTime)
    message = db.Column(db.String(280))  # optional note attached to the invite
    extra_json = db.Column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_connection_pair"),
        CheckConstraint("requester_id <> addressee_id", name="ck_connection_self"),
        Index("ix_connections_unique_pair", "requester_id", "addressee_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Connection {self.requester_id}->{self.addressee_id} {self.status.value}>"


# ---------- Mentorship ----------

class Mentorship(db.Model, TimestampMixin):
    """
    Formal mentorship relationships (mentor -> mentee).
    Separate from general connections; can exist with or without a Connection.
    """
    __tablename__ = "mentorships"

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    mentor = db.relationship("User", foreign_keys=[mentor_id], backref=db.backref("mentees", cascade="all,delete"))
    mentee = db.relationship("User", foreign_keys=[mentee_id], backref=db.backref("mentors", cascade="all,delete"))

    status = db.Column(db.String(32), default="active")  # active, paused, ended
    goals = db.Column(db.Text)
    extra_json = db.Column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("mentor_id", "mentee_id", name="uq_mentorship_pair"),
        CheckConstraint("mentor_id <> mentee_id", name="ck_mentorship_self"),
    )


# ---------- Notifications / Activity / Analytics ----------

class Notification(db.Model, TimestampMixin):
    """
    User notifications (connection invites, comments, mentions, awards, etc.)
    """
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = db.relationship("User", back_populates="notifications")

    category = db.Column(db.String(64), nullable=False, index=True)  # e.g., 'connection', 'comment', 'award'
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    extra_json = db.Column(JSONB, default=dict)


class ActivityLog(db.Model, TimestampMixin):
    """
    High-level activity trail for analytics and admin audits.
    """
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    user = db.relationship("User", back_populates="activities")
    action = db.Column(db.String(128), nullable=False, index=True)   # e.g., 'login', 'post_create', 'connection_request'
    context = db.Column(JSONB, default=dict)                         # arbitrary payload (safe)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))


class UserAnalytics(db.Model, TimestampMixin):
    """
    Per-user aggregate counters for cheap dashboards.
    """
    __tablename__ = "user_analytics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = db.relationship("User", back_populates="analytics")

    connections_count = db.Column(db.Integer, default=0, nullable=False)
    posts_count = db.Column(db.Integer, default=0, nullable=False)
    events_count = db.Column(db.Integer, default=0, nullable=False)
    badges_count = db.Column(db.Integer, default=0, nullable=False)
    last_active_at = db.Column(db.DateTime)

    extra_json = db.Column(JSONB, default=dict)


class DailyStats(db.Model, TimestampMixin):
    """
    Platform-wide daily aggregates for analytics dashboards.
    """
    __tablename__ = "daily_stats"

    id = db.Column(db.Integer, primary_key=True)
    stats_date = db.Column(db.Date, unique=True, default=date.today, nullable=False, index=True)

    new_users = db.Column(db.Integer, default=0, nullable=False)
    new_connections = db.Column(db.Integer, default=0, nullable=False)
    new_posts = db.Column(db.Integer, default=0, nullable=False)
    new_events = db.Column(db.Integer, default=0, nullable=False)
    extra_json = db.Column(JSONB, default=dict)


# ---------- Helpful compound indexes ----------

Index("ix_users_name", User.last_name, User.first_name)
Index("ix_posts_author_created", Post.author_id, Post.created_at.desc())
Index("ix_jobs_company_title", Job.company_id, Job.title)
Index("ix_group_message_group_created", GroupMessage.group_id, GroupMessage.created_at.desc())
Index("ix_notifications_user_read", Notification.user_id, Notification.is_read)
