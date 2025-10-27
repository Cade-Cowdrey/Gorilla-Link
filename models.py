"""
PittState-Connect | Models
Unified database schema for all user, post, event, scholarship, and analytics entities.
"""

from datetime import datetime
from extensions import db
from flask_login import UserMixin


# ======================================================
# 👤 USER MODEL
# ======================================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(50), default="student")
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", backref="author", lazy=True)
    events = db.relationship("Event", backref="organizer", lazy=True)

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


# ======================================================
# 🏫 DEPARTMENTS & FACULTY
# ======================================================
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    description = db.Column(db.Text)
    faculty = db.relationship("Faculty", backref="department", lazy=True)
    users = db.relationship("User", backref="department", lazy=True)


class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    title = db.Column(db.String(120))
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    email = db.Column(db.String(120))


# ======================================================
# 🗓️ EVENTS
# ======================================================
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    date = db.Column(db.DateTime)
    organizer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    is_public = db.Column(db.Boolean, default=True)


# ======================================================
# 💬 POSTS (FEED)
# ======================================================
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship("Like", backref="post", lazy=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# ======================================================
# 🫱 CONNECTIONS (NETWORK)
# ======================================================
class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    connected_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ======================================================
# 🧑‍🎓 SCHOLARSHIPS
# ======================================================
class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)


# ======================================================
# 🏆 STORIES / SUCCESS POSTS
# ======================================================
class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    content = db.Column(db.Text)
    author_name = db.Column(db.String(120))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)


# ======================================================
# 📊 ANALYTICS LOGGING
# ======================================================
class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ApiUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
