# ============================================================
# FILE: models.py
# SQLAlchemy models for PittState-Connect
# ============================================================

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app_pro import db, login_manager


# ============================================================
# LOGIN MANAGER USER LOADER
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================
# USER MODEL
# ============================================================
class User(db.Model, UserMixin):
    """Main user table: students, alumni, faculty, and employers."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.String(30),
        default="student",
        nullable=False,
        doc="student, alumni, faculty, employer, admin",
    )
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    major = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255), default="default.png")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="sender", lazy=True
    )
    messages_received = db.relationship(
        "Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True
    )
    applications = db.relationship("ScholarshipApplication", backref="applicant", lazy=True)
    mentor_sessions = db.relationship("MentorshipSession", backref="mentor", lazy=True)

    # Optional Enhancements
    points = db.Column(db.Integer, default=0, doc="Leaderboard points")
    badges = db.relationship("UserBadge", backref="user", lazy=True)

    # Authentication
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ============================================================
# DEPARTMENT MODEL
# ============================================================
class Department(db.Model):
    """Academic departments for PSU (used for filtering, scholarships, etc.)."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    chair = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship("User", backref="department", lazy=True)
    scholarships = db.relationship("Scholarship", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# ============================================================
# POST MODEL (Feed / News / Announcements)
# ============================================================
class Post(db.Model):
    """Core feed posts (news, updates, or events)."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    category = db.Column(db.String(50), default="general")
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Post {self.title[:25]}>"


# ============================================================
# MESSAGE MODEL
# ============================================================
class Message(db.Model):
    """Private messages between users (stub for chat system)."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}>"


# ============================================================
# EVENT MODEL
# ============================================================
class Event(db.Model):
    """Campus or alumni events."""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    is_public = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Event {self.title}>"


# ============================================================
# SCHOLARSHIP MODEL
# ============================================================
class Scholarship(db.Model):
    """Scholarship database with Smart-Match compatibility."""

    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id"))
    tags = db.Column(db.String(255), doc="Comma-separated keywords for AI Smart Match")
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    applications = db.relationship("ScholarshipApplication", backref="scholarship", lazy=True)

    def __repr__(self):
        return f"<Scholarship {self.title}>"


# ============================================================
# SCHOLARSHIP APPLICATION MODEL
# ============================================================
class ScholarshipApplication(db.Model):
    """Student scholarship submissions."""

    __tablename__ = "scholarship_applications"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    essay_text = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")  # pending, accepted, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_score = db.Column(db.Float, default=0.0, doc="Smart-Match AI confidence score (0-100)")

    def __repr__(self):
        return f"<Application {self.id} - {self.status}>"


# ============================================================
# DONOR MODEL
# ============================================================
class Donor(db.Model):
    """Donor profiles for scholarships and impact stories."""

    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(255))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)
    total_contributed = db.Column(db.Float, default=0.0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    featured = db.Column(db.Boolean, default=False)

    scholarships = db.relationship("Scholarship", backref="donor", lazy=True)

    def __repr__(self):
        return f"<Donor {self.name}>"


# ============================================================
# MENTORSHIP SESSION MODEL
# ============================================================
class MentorshipSession(db.Model):
    """Peer or alumni mentorship sessions."""

    __tablename__ = "mentorship_sessions"

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    mentee_id = db.Column(db.Integer)
    topic = db.Column(db.String(255))
    notes = db.Column(db.Text)
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<MentorshipSession mentor={self.mentor_id} mentee={self.mentee_id}>"


# ============================================================
# USER BADGES MODEL
# ============================================================
class UserBadge(db.Model):
    """Tracks earned achievements and leaderboards."""

    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Badge {self.name} for User {self.user_id}>"


# ============================================================
# ANALYTICS MODEL (STUB)
# ============================================================
class UserAnalytics(db.Model):
    """Optional model for tracking user engagement metrics."""

    __tablename__ = "user_analytics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    last_login = db.Column(db.DateTime)
    total_logins = db.Column(db.Integer, default=0)
    scholarships_applied = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    mentorship_sessions = db.Column(db.Integer, default=0)
    leaderboard_score = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<UserAnalytics {self.user_id}>"


# ============================================================
# SYSTEM NOTIFICATION MODEL
# ============================================================
class Notification(db.Model):
    """System and email notification queue."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    category = db.Column(db.String(50), default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    delivery_status = db.Column(db.String(50), default="queued")

    def __repr__(self):
        return f"<Notification {self.title[:30]}>"


# ============================================================
# OPTIONAL AI LOGGING MODEL
# ============================================================
class AIInteraction(db.Model):
    """Logs AI helper prompts/responses (for essay helper or analytics)."""

    __tablename__ = "ai_interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    feature = db.Column(db.String(50))  # essay_helper, smart_match, etc.
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<AIInteraction {self.feature} by {self.user_id}>"
