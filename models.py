# =============================================================
# FILE: models.py
# PittState-Connect — Unified Data Models
# Includes: Users, Posts, Departments, Events, Scholarships,
# Mentorship, Analytics, Badges, Notifications, Digests,
# and ContactMessage (Admin Inbox)
# =============================================================

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app_pro import db, login_manager

# -------------------------------------------------------------
# USER MODEL
# -------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default="student")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(250))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    notifications = db.relationship("Notification", backref="recipient", lazy=True)
    badges = db.relationship("UserBadge", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------------------------------------
# DEPARTMENTS MODEL
# -------------------------------------------------------------
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    faculty_contact = db.Column(db.String(120))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Department {self.name}>"


# -------------------------------------------------------------
# POSTS / FEED MODEL
# -------------------------------------------------------------
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(250))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship("Like", backref="post", lazy=True)
    replies = db.relationship("Reply", backref="post", lazy=True)

    def __repr__(self):
        return f"<Post {self.id}>"


# -------------------------------------------------------------
# LIKES / REPLIES MODELS
# -------------------------------------------------------------
class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reply(db.Model):
    __tablename__ = "replies"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# EVENTS MODEL
# -------------------------------------------------------------
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# JOBS / INTERNSHIPS MODEL
# -------------------------------------------------------------
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150))
    description = db.Column(db.Text)
    link = db.Column(db.String(300))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))


# -------------------------------------------------------------
# SCHOLARSHIPS MODEL
# -------------------------------------------------------------
class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(10, 2))
    deadline = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# NOTIFICATIONS MODEL
# -------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.String(250))
    link = db.Column(db.String(250))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# BADGES SYSTEM
# -------------------------------------------------------------
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# DIGESTS / EMAIL LOGS
# -------------------------------------------------------------
class EmailDigestLog(db.Model):
    __tablename__ = "email_digest_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    digest_type = db.Column(db.String(50))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------------------------------------------
# CONTACT MESSAGE MODEL (NEW)
# -------------------------------------------------------------
class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactMessage from {self.email}>"
