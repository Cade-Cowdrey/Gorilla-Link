# models.py
# -------------------------------------------------------------------
# Full PittState-Connect ORM model definitions (finalized)
# Includes all blueprint dependencies + analytics models
# -------------------------------------------------------------------

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


# -------------------------------------------------------------------
# Roles / Users
# -------------------------------------------------------------------

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    password_hash = db.Column(db.String(128))
    verified = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Profile
    bio = db.Column(db.Text)
    major = db.Column(db.String(120))
    grad_year = db.Column(db.String(10))
    linkedin_url = db.Column(db.String(255))
    resume_url = db.Column(db.String(255))
    avatar_url = db.Column(db.String(255))

    role = db.relationship("Role", back_populates="users")
    activity_logs = db.relationship("ActivityLog", back_populates="user", cascade="all,delete")
    badges = db.relationship("UserBadge", back_populates="user", cascade="all,delete")
    scholarship_applications = db.relationship("ScholarshipApplication", back_populates="user", cascade="all,delete")
    essays = db.relationship("Essay", back_populates="user", cascade="all,delete")
    feed_items = db.relationship("FeedItem", back_populates="user", cascade="all,delete")
    mentorships_as_mentor = db.relationship("Mentorship", foreign_keys="Mentorship.mentor_id", back_populates="mentor")
    mentorships_as_mentee = db.relationship("Mentorship", foreign_keys="Mentorship.mentee_id", back_populates="mentee")
    groups = db.relationship("GroupMember", back_populates="user", cascade="all,delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------------------------------------------
# Analytics & Logging
# -------------------------------------------------------------------

class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(100))
    extra_data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action}>"


class DailyStats(db.Model):
    __tablename__ = "daily_stats"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True)
    active_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    scholarships_applied = db.Column(db.Integer, default=0)
    jobs_posted = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<DailyStats {self.date}>"


# -------------------------------------------------------------------
# Department / Faculty / Alumni
# -------------------------------------------------------------------

class Department(db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    building = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(255))

    faculty = db.relationship("Faculty", back_populates="department", cascade="all,delete")
    scholarships = db.relationship("Scholarship", back_populates="department_ref", cascade="all,delete")

    def __repr__(self):
        return f"<Department {self.name}>"


class Faculty(db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    title = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    department = db.relationship("Department", back_populates="faculty")

    def __repr__(self):
        return f"<Faculty {self.name}>"


class Alumni(db.Model):
    __tablename__ = "alumni"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    graduation_year = db.Column(db.String(10))
    employer = db.Column(db.String(120))
    position = db.Column(db.String(120))
    location = db.Column(db.String(120))
    achievements = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def __repr__(self):
        return f"<Alumni {self.user_id} - {self.employer}>"


# -------------------------------------------------------------------
# Scholarships / Essays
# -------------------------------------------------------------------

class Scholarship(db.Model):
    __tablename__ = "scholarship"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    department = db.Column(db.String(120))
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))

    department_ref = db.relationship("Department", back_populates="scholarships")
    applications = db.relationship("ScholarshipApplication", back_populates="scholarship")

    def __repr__(self):
        return f"<Scholarship {self.title}>"


class ScholarshipApplication(db.Model):
    __tablename__ = "scholarship_application"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"))
    status = db.Column(db.String(50), default="draft")
    progress = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="scholarship_applications")
    scholarship = db.relationship("Scholarship", back_populates="applications")

    def __repr__(self):
        return f"<ScholarshipApplication {self.id}:{self.status}>"


class Essay(db.Model):
    __tablename__ = "essay"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(150))
    content = db.Column(db.Text)
    user = db.relationship("User", back_populates="essays")

    def __repr__(self):
        return f"<Essay {self.title}>"


# -------------------------------------------------------------------
# Mentorship / Groups
# -------------------------------------------------------------------

class Mentorship(db.Model):
    __tablename__ = "mentorship"
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mentee_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentor = db.relationship("User", foreign_keys=[mentor_id], back_populates="mentorships_as_mentor")
    mentee = db.relationship("User", foreign_keys=[mentee_id], back_populates="mentorships_as_mentee")

    def __repr__(self):
        return f"<Mentorship {self.mentor_id}->{self.mentee_id}>"


class Group(db.Model):
    __tablename__ = "group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    members = db.relationship("GroupMember", back_populates="group", cascade="all,delete")
    messages = db.relationship("GroupMessage", back_populates="group", cascade="all,delete")

    def __repr__(self):
        return f"<Group {self.name}>"


class GroupMember(db.Model):
    __tablename__ = "group_member"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    role = db.Column(db.String(50), default="member")
    group = db.relationship("Group", back_populates="members")
    user = db.relationship("User", back_populates="groups")

    def __repr__(self):
        return f"<GroupMember {self.user_id}:{self.group_id}>"


class GroupMessage(db.Model):
    __tablename__ = "group_message"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    group = db.relationship("Group", back_populates="messages")
    sender = db.relationship("User")

    def __repr__(self):
        return f"<GroupMessage {self.id}>"


# -------------------------------------------------------------------
# Careers / Jobs / Posts
# -------------------------------------------------------------------

class Job(db.Model):
    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    company = db.Column(db.String(120))
    description = db.Column(db.Text)
    location = db.Column(db.String(120))
    salary = db.Column(db.Float)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title}>"


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.Text)
    category = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")

    def __repr__(self):
        return f"<Post {self.id}:{self.category}>"


# -------------------------------------------------------------------
# Events / RSVPs / Badges / Feed / Donors
# -------------------------------------------------------------------

class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    location = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvps = db.relationship("EventRSVP", back_populates="event", cascade="all,delete")

    def __repr__(self):
        return f"<Event {self.title}>"


class EventRSVP(db.Model):
    __tablename__ = "event_rsvp"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event = db.relationship("Event", back_populates="rsvps")
    user = db.relationship("User")

    def __repr__(self):
        return f"<RSVP {self.user_id}:{self.event_id}>"


class Badge(db.Model):
    __tablename__ = "badge"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(120))
    description = db.Column(db.String(255))
    user_badges = db.relationship("UserBadge", back_populates="badge", cascade="all,delete")

    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(db.Model):
    __tablename__ = "user_badge"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"))
    reason = db.Column(db.String(255))
    user = db.relationship("User", back_populates="badges")
    badge = db.relationship("Badge", back_populates="user_badges")

    def __repr__(self):
        return f"<UserBadge {self.user_id}:{self.badge_id}>"


class Donor(db.Model):
    __tablename__ = "donor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    organization = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    donations = db.relationship("Donation", back_populates="donor", cascade="all,delete")

    def __repr__(self):
        return f"<Donor {self.name}>"


class Donation(db.Model):
    __tablename__ = "donation"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donor.id"))
    amount = db.Column(db.Float)
    note = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    donor = db.relationship("Donor", back_populates="donations")

    def __repr__(self):
        return f"<Donation ${self.amount}>"


class ImpactStory(db.Model):
    __tablename__ = "impact_story"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    body = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ImpactStory {self.title}>"
